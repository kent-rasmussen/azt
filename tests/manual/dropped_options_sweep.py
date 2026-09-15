# coding=UTF-8
"""Find widget options that are ACCEPTED AND THROWN AWAY.

    ../env/bin/python -m tests.manual.dropped_options_sweep
    ../env/bin/python -m tests.manual.dropped_options_sweep frontend/ui_webview.py

`agenda/webview_discards_widget_options.md`, plan step 5: "make the class
impossible to reintroduce — every deliberate drop gets a comment… A drop
with no comment then reads as a bug, which is the only way this stops
recurring."

## Why a tool at all

Eleven of these were found in one week, every one of them by a person
noticing that a PAGE looked wrong — never by a test, a log line or an
exception, because the shape raises nothing and logs nothing:

    kwargs.pop('anchor', None)          # the caller asked; nothing happens

The options are declared in `ui_interface.py`, the call sites pass them, the
widget accepts them, and the page ignores them. The only durable defence is
to make the SILENT drop visible, which is what this prints.

## The two rules

    D1  a `kwargs.pop('x', …)` whose value is DISCARDED — a bare statement,
        not an assignment and not put back into kwargs — with no comment
        within six lines above it. With a comment it is a decision; without
        one it is indistinguishable from an oversight, and every one of the
        eleven looked exactly like this.

    D2  `self.x = kwargs.pop('x', …)` where `self.x` is never READ anywhere
        in the file. This is the shape that hid tkinter's `anchor` for years:
        `TextBase.__init__` stored it on the instance, `restore_kwargs` did
        not carry it back, and nothing ever read the attribute — so 91 call
        sites in 14 files passed an option that could not do anything, and
        it took building a nine-cell anchor grid to notice (2026-09-14).

D2 reports CANDIDATES, not faults: an attribute this file never reads may
still be read by another module, and the tool says so rather than guessing.
Check with a grep before believing it.

## What it deliberately does not do

It does not compare against `ui_interface.py`. That comparison is step 6(a)
of `webview_when_to_finish.md` — the full audit of what the app CALLS
against what each backend implements — and it needs the call sites, not just
the backends. This is the cheap half, and the half that stops the class from
coming back.
"""
import ast
import io
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent
DEFAULTS = ['frontend/ui_webview.py', 'frontend/ui_tkinter.py']
COMMENT_WINDOW = 6      # lines above a drop that may explain it


def _comment_lines(src):
    """Line numbers carrying a comment, from the tokenizer (ast drops them)."""
    out = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                out.add(tok.start[0])
    except (tokenize.TokenError, IndentationError):
        pass
    return out


def _is_kwargs_pop(node):
    """`<something>.pop('name', …)` → the popped name, or None."""
    if not isinstance(node, ast.Call):
        return None
    f = node.func
    if not (isinstance(f, ast.Attribute) and f.attr == 'pop'):
        return None
    if not (isinstance(f.value, ast.Name) and 'kwarg' in f.value.id.lower()):
        return None
    if node.args and isinstance(node.args[0], ast.Constant) \
            and isinstance(node.args[0].value, str):
        return node.args[0].value
    return '<computed>'


class Sweep(ast.NodeVisitor):
    def __init__(self, src):
        self.hits = []
        self.comments = _comment_lines(src)
        self.selfstores = {}    # attr -> [lines] assigned on self
        self.selfloads = set()  # attr names read anywhere in the file
        # Names that are ELEMENTS OF A COLLECTION LITERAL — `{'image',
        # 'compound','wraplength'}` — because that is what a getattr()
        # restore iterates. Any string anywhere would be too broad: 'anchor'
        # appears in ui_tkinter as a plain comparison (`kwargs['anchor'] in
        # [E,"e"]`) and was still never restored.
        self.strings = set()
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, (ast.Set, ast.List, ast.Tuple)):
                self.strings |= {e.value for e in n.elts
                                 if isinstance(e, ast.Constant)
                                 and isinstance(e.value, str)}

    # ── D1 ───────────────────────────────────────────────────────────
    def visit_Expr(self, node):
        name = _is_kwargs_pop(node.value)
        if name:
            explained = any(n in self.comments
                            for n in range(node.lineno - COMMENT_WINDOW,
                                           node.lineno + 1))
            if not explained:
                self.hits.append((node.lineno, 'D1', name,
                                  "{!r} is popped and discarded, with nothing "
                                  "saying why".format(name)))
        self.generic_visit(node)

    # ── D2, part one: what is stored, and what is read ───────────────
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            if isinstance(node.ctx, ast.Load):
                self.selfloads.add(node.attr)
        self.generic_visit(node)

    def visit_Assign(self, node):
        name = _is_kwargs_pop(node.value)
        if name:
            for t in node.targets:
                if (isinstance(t, ast.Attribute)
                        and isinstance(t.value, ast.Name)
                        and t.value.id == 'self'):
                    self.selfstores.setdefault(t.attr, []).append(
                        (node.lineno, name))
        self.generic_visit(node)

    def finish(self):
        for attr, places in sorted(self.selfstores.items()):
            if attr in self.selfloads:
                continue
            # NOT EVERY READ IS AN ATTRIBUTE ACCESS. `ui_tkinter` restores
            # reserved kwargs with `getattr(self, k)` over a SET OF NAMES
            # (`Text.tk_textkwargs` and friends), so an attribute nothing
            # names directly may still be read every time the widget is
            # built. That distinction is the whole reason `anchor` was a bug
            # and `compound` is not: 'compound' is in `tk_textkwargs` and
            # comes back; 'anchor' is in none of those sets, so it never did
            # (2026-09-14 — this tool's first run flagged both, and only one
            # of them was real).
            dynamic = attr in self.strings
            self.hits.append((places[0][0], 'D2', attr,
                              "{!r} is popped into self.{}, which this file "
                              "never reads{}".format(
                                  places[0][1], attr,
                                  " — but the NAME appears in a collection "
                                  "here, so a getattr() restore may read it; "
                                  "check that before believing this"
                                  if dynamic else
                                  ", and the name appears nowhere else in "
                                  "the file either")))
        return sorted(set(self.hits))


def findings(paths=None):
    """[(file, rule, option name, line, why)] — the machine-readable form.

    KEYED ON NAMES, NOT LINE NUMBERS, because `tests/test_dropped_options.py`
    gates on this and a baseline keyed on line numbers would go stale on the
    next edit above it — a guard that cries wolf is turned off, and then the
    class it guards against comes back.
    """
    files = []
    for p in (paths or DEFAULTS):
        p = Path(p)
        if not p.is_absolute():
            p = HERE / p
        files += [p] if p.is_file() else sorted(p.rglob('*.py'))
    out = []
    for f in files:
        try:
            src = f.read_text(encoding='utf-8')
            tree = ast.parse(src)
        except Exception as e:
            print("{}: could not parse ({})".format(f, e))
            continue
        s = Sweep(src)
        s.visit(tree)
        rel = str(f.relative_to(HERE)) if HERE in f.parents else str(f)
        lines = src.splitlines()
        for lineno, rule, name, why in s.finish():
            text = lines[lineno - 1].strip() if lineno <= len(lines) else ''
            out.append((rel, rule, name, lineno, why, text))
    return out


def sweep(paths=None):
    found = findings(paths)
    for rel, rule, name, lineno, why, text in found:
        print("{}:{}: [{}] {}".format(rel, lineno, rule, why))
        print("        {}".format(text[:150]))
    print("\n{} unexplained drop(s). A drop WITH a comment is a decision; "
          "one without is indistinguishable from an oversight.".format(
              len(found)))
    return len(found)


if __name__ == '__main__':
    sys.exit(0 if sweep(sys.argv[1:] or DEFAULTS) >= 0 else 1)
