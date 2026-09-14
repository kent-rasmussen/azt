# coding=UTF-8
"""Find the "rescanning where a grouping or a set was wanted" shape.

    ../env/bin/python -m tests.manual.rescan_sweep            # whole repo
    ../env/bin/python -m tests.manual.rescan_sweep io_put backend/core
    ../env/bin/python -m tests.manual.rescan_sweep --all      # loose forms too

`agenda/rescan_instead_of_grouping.md` plan steps 2 and 3. Three instances
found by hand in one session cost 42 seconds of boot between them, and the
item's own conclusion was that three by hand implies more — but they are
invisible to every other tool we have. They do not raise, they do not log,
and they are CORRECT, so tests pass and the only symptom is that the app is
slow. Only the shape is findable, and only in the AST.

**This prints candidates, not verdicts.** A quadratic comprehension over
four items is fine and one over 9,582 is 92 million iterations; the source
cannot tell you which you have. The item's own rule stands — the three that
were fixed were found by TIMING, and two attempts to find the third by
reading guessed wrong first. Use this to know WHERE to look, then time it.

## The rules, and what the first version got wrong

The first run printed 207 candidates, which is a broken tool rather than a
broken codebase: a list of 207 is read as noise and nobody looks at it. Each
rule below says what it now requires, and what it used to flag.

    R1  a comprehension whose inner generator rescans the SAME collection
        the outer one walks, including when the rescan hides in the element
        expression (the `dict_by` shape).
        FIXED: it compared only the BASE name, so `self.models_that_give_tone`
        and `self.models_that_give_IPA` both read as "self" and matched each
        other. It compares the full dotted path now. The flatten idiom
        `[i for j in X for i in j]` was already excluded, by checking what
        each generator BINDS.
    R2  membership (`in` / `not in`) against a COMPUTED sequence — a
        comprehension, or a call that builds one. The whole collection is
        constructed to answer one question and then scanned.
        FIXED: it flagged every `x in ['NA']`. A literal of a few items is
        not a rescan; a literal is only reported past --big items.
    R3  membership against a name that was assigned a COMPUTED sequence in
        the same function, inside a loop — `getcawlmissing`'s shape, where a
        set would be O(1).
        FIXED: it ignored comprehension scope, so a comprehension's own
        target could be mistaken for a list assigned elsewhere.
    R5  grouping by rescanning — an inner comprehension over some
        collection, filtered by the OUTER comprehension's key:
        `{k: [i for i in things if i.attr() == k] for k in …}` walks
        `things` once per key. THIS IS THE SHAPE THE ITEM IS ABOUT
        (`langtags.dict_by` is exactly it), and tightening R1 to an exact
        path would otherwise have hidden every instance where the two
        collections merely differ. Cheap when the keys are few (parts of
        speech), quadratic when they are not (every lexeme) — reported,
        never judged, because only a measurement knows which.
    R4  `.index()` / `.count()` on the collection the loop is walking, or
        with the loop's own variable as the argument — `for s in xs:
        xs.index(s)`, which is quadratic.
        FIXED: it flagged any `.index()`/`.count()` anywhere inside any
        loop, including `content.count('\\n', 0, match.start())`.

R2 and R3 are one fault wearing two faces; R1 is the other one. `--all`
restores the loose forms if you want to grep the long list yourself.
"""
import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent.parent
SKIP = {'env', '.git', '.buildozer', 'build', 'dist', 'userlogs', 'images',
        'images_CAWL', '__pycache__', 'translations'}

COMPS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
# Calls that hand back a whole fresh sequence. `keys()`/`values()` are views
# and `set()`/`frozenset()` are O(1) to test, so none of them belongs here.
BUILDERS = {'list', 'sorted', 'tuple', 'split', 'splitlines', 'readlines',
            'findall', 'flatten'}
BIG_LITERAL = 8         # a literal list longer than this is worth a look


def _path(node):
    """The dotted path a `for … in X` walks: `self.a.b[0]` → 'self.a.b'.

    THE FULL PATH, not the base name — comparing bases made every pair of
    `self.<anything>` comprehensions look like a rescan of each other, which
    was most of the first run's false positives.
    """
    parts = []
    while True:
        if isinstance(node, ast.Name):
            parts.append(node.id)
            break
        if isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        elif isinstance(node, (ast.Subscript, ast.Starred)):
            node = node.value
        elif isinstance(node, ast.Call):
            node = node.func
        else:
            return None
    return '.'.join(reversed(parts))


def _bound(target):
    """Every name a generator's target binds (tuples included)."""
    return {n.id for n in ast.walk(target) if isinstance(n, ast.Name)}


def _computed(node, loose=False):
    """What kind of fresh sequence this expression builds, or None."""
    if isinstance(node, COMPS):
        return 'a comprehension'
    if isinstance(node, ast.Call):
        name = node.func.attr if isinstance(node.func, ast.Attribute) \
               else getattr(node.func, 'id', None)
        if name in BUILDERS:
            return '{}()'.format(name)
        return None
    if isinstance(node, ast.List):
        n = len(node.elts)
        if n > BIG_LITERAL:
            return 'a {}-item literal'.format(n)
        if loose and n:
            return 'a {}-item literal'.format(n)
    return None


class Sweep(ast.NodeVisitor):
    def __init__(self, loose=False):
        self.loose = loose
        self.hits = []
        self.loops = []      # [(iterable path, {target names})] innermost last
        self.compnames = []  # names bound by enclosing comprehensions
        self.listy = {}      # name -> line where it was given a sequence

    # ── context ──────────────────────────────────────────────────────
    def visit_For(self, node):
        self.loops.append((_path(node.iter), _bound(node.target)))
        self.generic_visit(node)
        self.loops.pop()

    visit_AsyncFor = visit_For

    def visit_While(self, node):
        self.loops.append((None, set()))
        self.generic_visit(node)
        self.loops.pop()

    def visit_FunctionDef(self, node):
        # A fresh scope: a name that held a list in one function says nothing
        # about another.
        outer, self.listy = self.listy, {}
        for sub in ast.walk(node):
            if isinstance(sub, ast.Assign) and _computed(sub.value):
                for t in sub.targets:
                    if isinstance(t, ast.Name):
                        self.listy[t.id] = sub.lineno
        self.generic_visit(node)
        self.listy = outer

    visit_AsyncFunctionDef = visit_FunctionDef

    @property
    def inloop(self):
        return bool(self.loops)

    # ── R1 ───────────────────────────────────────────────────────────
    def _check_comp(self, node):
        gens = node.generators
        if not gens:
            return
        outer_path = _path(gens[0].iter)
        bound = _bound(gens[0].target)
        for gen in gens[1:]:
            path = _path(gen.iter)
            base = (path or '').split('.')[0]
            if base and base in bound:
                pass                       # the flatten idiom: linear
            elif path and outer_path and path == outer_path:
                self._hit(node, 'R1', "inner generator rescans {!r}, which "
                                      "the outer one already walks"
                                      "".format(path))
            bound |= _bound(gen.target)
        # The `dict_by` shape: the rescan is in the VALUE, not in a generator.
        outer_paths = {p for p in (_path(n) for n in ast.walk(gens[0].iter)
                                   if isinstance(n, (ast.Name, ast.Attribute)))
                       if p}
        first_bound = _bound(gens[0].target)
        parts = [node.value, node.key] if isinstance(node, ast.DictComp) \
                else [node.elt]
        for part in parts:
            if part is None:
                continue
            for sub in ast.walk(part):
                if not isinstance(sub, COMPS):
                    continue
                for gen in sub.generators:
                    p = _path(gen.iter)
                    if (p and p in outer_paths
                            and p.split('.')[0] not in first_bound):
                        self._hit(node, 'R1',
                                  "the element rebuilds from {!r}, which the "
                                  "outer loop already walks".format(p))
                        continue
                    # R5 — GROUPING BY RESCANNING, which is the shape this
                    # item is actually about, and the one the tightened R1
                    # would otherwise hide. Its signature is not "the same
                    # collection twice": it is an inner comprehension over
                    # SOME collection, filtered by the OUTER key —
                    #     {k: [i for i in things if i.attr() == k] for k in …}
                    # — which walks `things` once per key. That is
                    # `langtags.dict_by`, and it is `sensesbyps`,
                    # `entriesbylx` and `sensesbygroup` too. Cheap when the
                    # keys are few (parts of speech) and quadratic when they
                    # are not (every lexeme), and only a measurement can tell
                    # which — so it is reported, not judged.
                    if not first_bound or not p:
                        continue
                    refs = {n.id for cond in gen.ifs
                            for n in ast.walk(cond)
                            if isinstance(n, ast.Name)}
                    if refs & first_bound:
                        self._hit(node, 'R5',
                                  "groups by rescanning {!r} once per {}"
                                  "".format(p, '/'.join(sorted(
                                      refs & first_bound))))

    def visit_ListComp(self, node):
        self._check_comp(node)
        # Comprehension targets shadow function locals; remember them so a
        # membership test inside is not blamed on a same-named list outside.
        names = set()
        for gen in node.generators:
            names |= _bound(gen.target)
        self.compnames.append(names)
        self.generic_visit(node)
        self.compnames.pop()

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    # ── R2, R3 ───────────────────────────────────────────────────────
    def visit_Compare(self, node):
        for op, right in zip(node.ops, node.comparators):
            if not isinstance(op, (ast.In, ast.NotIn)):
                continue
            where = " INSIDE A LOOP" if self.inloop else ""
            kind = _computed(right, self.loose)
            if kind:
                self._hit(node, 'R2', "membership against {}{}".format(
                                          kind, where))
            elif isinstance(right, ast.Name) and self.inloop:
                shadowed = any(right.id in s for s in self.compnames)
                if right.id in self.listy and not shadowed:
                    self._hit(node, 'R3',
                              "membership against {!r}, a sequence built at "
                              "line {} — a set is O(1)".format(
                                  right.id, self.listy[right.id]))
        self.generic_visit(node)

    # ── R4 ───────────────────────────────────────────────────────────
    def visit_Call(self, node):
        if (self.inloop and isinstance(node.func, ast.Attribute)
                and node.func.attr in ('index', 'count')):
            # QUADRATIC ONLY IF IT SCANS WHAT THE LOOP IS WALKING. Either the
            # receiver is the loop's own iterable, or the argument is the
            # loop's own variable — `for s in xs: xs.index(s)`. Anything else
            # is a linear call that happens to sit in a loop, which is
            # ordinary code (`content.count('\n', 0, match.start())`).
            recv = _path(node.func.value)
            args = {a.id for a in node.args if isinstance(a, ast.Name)}
            for path, targets in self.loops:
                if (recv and path and recv == path) or (args & targets):
                    self._hit(node, 'R4',
                              ".{}() scans {!r}, the collection this loop is "
                              "walking".format(node.func.attr, recv or '?'))
                    break
        self.generic_visit(node)

    def _hit(self, node, rule, why):
        self.hits.append((node.lineno, rule, why))


ORDER = {'R5': 0, 'R1': 1, 'R3': 2, 'R4': 3, 'R2': 4}


def sweep(paths, loose=False):
    files = []
    for p in paths:
        p = Path(p)
        if not p.is_absolute():
            p = HERE / p
        if p.is_file():
            files.append(p)
        else:
            files += [f for f in sorted(p.rglob('*.py'))
                      if not SKIP & set(f.parts)]
    found = []
    for f in files:
        try:
            src = f.read_text(encoding='utf-8')
            tree = ast.parse(src)
        except Exception as e:
            print("{}: could not parse ({})".format(f, e))
            continue
        s = Sweep(loose)
        s.visit(tree)
        if not s.hits:
            continue
        lines = src.splitlines()
        rel = f.relative_to(HERE) if HERE in f.parents else f
        for lineno, rule, why in sorted(set(s.hits)):
            text = lines[lineno - 1].strip() if lineno <= len(lines) else ''
            found.append((rule, str(rel), lineno, why, text))
    # Structural first (R1), then the two membership shapes, then the rest —
    # a list is only useful if the top of it is the part worth reading.
    found.sort(key=lambda h: (ORDER.get(h[0], 9), h[1], h[2]))
    counts = {}
    for rule, rel, lineno, why, text in found:
        counts[rule] = counts.get(rule, 0) + 1
        print("{}:{}: [{}] {}".format(rel, lineno, rule, why))
        print("        {}".format(text[:150]))
    print("\n{} candidate(s): {}".format(
            len(found), ', '.join("{} {}".format(v, k)
                                  for k, v in sorted(counts.items()))
            or 'none'))
    print("Time before you change any of them — a quadratic over four items "
          "is fine.")
    return len(found)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--all']
    sys.exit(0 if sweep(args or [HERE], '--all' in sys.argv) >= 0 else 1)
