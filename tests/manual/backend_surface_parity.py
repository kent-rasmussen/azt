# coding=UTF-8
"""What does tkinter offer that webview does not? A REPORT, run by hand.

    ../env/bin/python -um tests.manual.backend_surface_parity

WHY IT IS HERE AND NOT IN THE SUITE. Kent, 2026-09-11: "more of a manual test
than a regression protection, right?" Quite — and worse than that, the two
inventories were `xfail`, so they could never fail the suite and protected
nothing at all. They are lists for a person to read and triage. The two
checks that genuinely assert something stayed behind in
`tests/test_backend_surface_parity.py`, which imports the machinery from
here.

WHY THIS AND NOT THE ABC. `frontend/ui_interface.py` exists to say what both
backends must implement, and the webview port item proposed checking each
backend against it. **That check would have passed the worst gap found so
far.** `ui_webview.ContextMenu` implemented exactly the three members
`ContextMenuInterface` declares — `menuinit`, `updatebindings`, `undo_popup`
— and none of the three that make a menu happen: `menuitem`, `do_popup`, and
registering itself as `parent.context`. The contract did not describe the
working implementation either: `ui_tkinter.ContextMenu` has no
`updatebindings` at all.

So the reference is the BACKEND THAT WORKS. tkinter runs the app; anything
public it offers and webview does not is a port gap, whatever any interface
file says. That needs no inference about which expressions are widgets, and
it would have caught every gap in the running inventory: `takekioskscreen`,
`after_idle`, `cget`, `wait_window`, `Window.lift`, `EntryField.delete` /
`insert` / `focus_set`, `bind_all`, and `ContextMenu`'s three.

TWO FAILURE MODES, and this finds only the first:

  * MISSING — the attribute is not there, so the call raises. Loud, unless it
    is raised inside a pywebview callback, where `on_event` logs and carries
    on (five of the gaps above presented as "nothing happened"; `on_event`
    now marks that case PORT GAP).
  * PRESENT AND INERT — a stub returning None. Silent everywhere: nothing
    raises, so nothing is logged, and the caller reports success. This is
    what `ContextMenu` was, and no report can find it. That one is swept by
    hand; the result is in agenda/webview_when_to_finish.md, Step 6(b).

READS SOURCE, IMPORTS NOTHING HEAVY. `ui_tkinter` needs tkinter and
`ui_webview` needs pywebview; this has to run where neither is installed, so
it compares ASTs.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / 'frontend'


def _classes(path):
    """{class name: ({public members}, [base names])} from a module's source.

    BASES MATTER for one question and not the other — see `TK`/`TK_ANY`.

    INSTANCE ATTRIBUTES COUNT. `self.buttons = {}` in __init__ is as much a
    member as a class-level one, and reading only the class body reported
    `buttons` as missing from webview when it is set at `ui_webview.py:2651`.
    A false positive in a report is expensive: it costs the reader's trust in
    the whole list.
    """
    tree = ast.parse(path.read_text())
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        members = set()
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                members.add(item.name)
            elif isinstance(item, ast.Assign):
                for t in item.targets:
                    if isinstance(t, ast.Name):
                        members.add(t.id)
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Assign):
                continue
            for t in sub.targets:
                if (isinstance(t, ast.Attribute)
                        and isinstance(t.value, ast.Name)
                        and t.value.id == 'self'):
                    members.add(t.attr)
        bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
        out[node.name] = ({m for m in members if not m.startswith('_')},
                          bases)
    return out


_TK_RAW = _classes(FRONTEND / 'ui_tkinter.py')
_WV_RAW = _classes(FRONTEND / 'ui_webview.py')

# DECLARED, not inherited — for asking "does THIS class implement it".
# Resolving inheritance here made every widget report the same dozen names
# (`gridkwargs`, `pads`, `workarea`, `AUTOSCROLL_*`), because tkinter shares
# them through Gridded/UI/Childof mixins and webview does not mirror that
# hierarchy: 27 of 30 classes "had gaps" and almost none were real.
TK = {c: members for c, (members, _b) in _TK_RAW.items()}
WV = {c: members for c, (members, _b) in _WV_RAW.items()}

# MODULE-WIDE — for asking "does this backend have it ANYWHERE". The two
# organise their hierarchies differently (`takekioskscreen` on tkinter's
# Window, webview's Toplevel), so a name present somewhere is implemented;
# only a name present nowhere is a gap.
TK_ANY = set().union(*TK.values()) if TK else set()
WV_ANY = set().union(*WV.values()) if WV else set()
# Module level counts too: webview declares some things as module constants
# where tkinter has them on a class (`WAIT_DELAY_MS`), and counting only class
# members reported those as missing when they were right there.
_wv_tree = ast.parse((FRONTEND / 'ui_webview.py').read_text())
for _node in _wv_tree.body:
    if isinstance(_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        WV_ANY.add(_node.name)
    elif isinstance(_node, ast.Assign):
        for _t in _node.targets:
            if isinstance(_t, ast.Name):
                WV_ANY.add(_t.id)


EXPECTED_ABSENT = {
    # tkinter internals that mean nothing in a browser
    'pre_tk_init', 'post_tk_init', 'reserve_kwargs', 'restore_kwargs',
    'super_kwargs', 'tk_textkwargs', 'tk_kwargs',
}

# Members webview deliberately does NOT have, because it does the job another
# way. Each needs a reason: an allowlist without one is how a port stops being
# measured, and "we meant to do that" is exactly what a hollow stub says too.
DIFFERENT_BY_DESIGN = {
    # THE BROWSER DOES HOVER. tkinter schedules the tooltip's appearance
    # itself and carries the state to do it — `schedule`/`unschedule` around
    # `enter`/`leave`, with `waittime`/`showtime` for the delays, `tw` for the
    # popup window, `id` for the pending callback, `dispx`/`dispy` for
    # placement. webview sets a CSS tooltip and the engine handles all of it.
    # Thirteen names is a long exemption, but they are ONE decision.
    'ToolTip': {'enter', 'entertip', 'leave', 'schedule', 'unschedule',
                'waittime', 'showtime', 'tw', 'id', 'event',
                'dispx', 'dispy', 'wraplength'},
}


def gaps(cls):
    """Public members tkinter's `cls` declares and webview's does not."""
    if cls not in TK or cls not in WV:
        return set()
    allowed = EXPECTED_ABSENT | DIFFERENT_BY_DESIGN.get(cls, set())
    return {m for m in TK[cls] - WV[cls] if m not in allowed}


def app_attribute_names():
    """Every attribute name the app's own code touches."""
    names = set()
    skip = {'ui_tkinter.py', 'ui_webview.py'}
    for path in ROOT.rglob('*.py'):
        rel = path.relative_to(ROOT).parts
        if rel[0] in ('tests', 'env', '.git', 'translations', 'xlptransforms'):
            continue
        if path.name in skip:
            continue
        try:
            tree = ast.parse(path.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                names.add(node.attr)
    return names


def module_gaps(called_only=True):
    """Names ui_tkinter declares somewhere and ui_webview declares nowhere.

    FILTERED BY WHETHER THE APP CALLS THEM, because the unfiltered list is 53
    names and mostly noise: kwarg tables (`bf_kwargs`, `my_tk_kwargs`),
    layout constants (`AUTOSCROLL_MS`, `MIN_AVAILABLE`), and helpers tkinter
    needs to talk to Tk. A member nothing outside `ui_tkinter` names is that
    backend's private business.
    """
    allowed = set(EXPECTED_ABSENT)
    for names in DIFFERENT_BY_DESIGN.values():
        allowed |= names
    out = {n for n in TK_ANY - WV_ANY if n not in allowed}
    if called_only:
        out &= app_attribute_names()
    return sorted(out)


def tkinter_gaps():
    """tkinter's OWN api that the app calls and webview does not implement.

    Every gap found the hard way — `lift`, `cget`, `after_idle`,
    `wait_window`, `takekioskscreen`, `bind_all` — is a member of tkinter's
    Misc/Wm, not of a class this project declares. So comparing our two
    modules to each other could never have seen them: tkinter gets them free
    and webview has to write each one.
    """
    import tkinter
    api = set()
    for base in (tkinter.Misc, tkinter.Wm, tkinter.Widget):
        api |= {n for n in dir(base) if not n.startswith('_')}
    return sorted((app_attribute_names() & api) - WV_ANY)


if __name__ == '__main__':
    print('=' * 70)
    print("ui_tkinter members the app CALLS that ui_webview does not have")
    print('=' * 70)
    missing = module_gaps()
    for name in missing:
        print('  ' + name)
    print('\n  {} name(s)'.format(len(missing)) if missing else '  none')

    rest = sorted(set(module_gaps(called_only=False)) - set(missing))
    print('\n  ({} more that nothing outside ui_tkinter names — its own '
          'business:'.format(len(rest)))
    print('   ' + ', '.join(rest) + ')')

    print()
    print('=' * 70)
    print('tkinter API the app CALLS that ui_webview does not implement')
    print('  (noisy: a name the app uses on a non-widget shows up here if')
    print('   tkinter happens to define it too — triage, not a bug list)')
    print('=' * 70)
    try:
        tkgaps = tkinter_gaps()
    except ImportError as e:
        print('  cannot check: {}'.format(e))
    else:
        for name in tkgaps:
            print('  ' + name)
        print('\n  {} name(s)'.format(len(tkgaps)))
