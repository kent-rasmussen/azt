# coding=UTF-8
"""What does tkinter offer that webview does not?

WHY THIS AND NOT THE ABC. `frontend/ui_interface.py` exists to say what both
backends must implement, and `webview_when_to_finish.md` proposed checking
each backend against it. **That check would have passed the worst gap found so
far.** `ui_webview.ContextMenu` implemented exactly the three members
`ContextMenuInterface` declares — `menuinit`, `updatebindings`, `undo_popup` —
and none of the three that make a menu happen: `menuitem`, `do_popup`, and
registering itself as `parent.context`. The contract did not describe the
working implementation either: `ui_tkinter.ContextMenu` has no
`updatebindings` at all.

So the reference is the BACKEND THAT WORKS. tkinter runs the app; anything
public it offers and webview does not is a port gap, whatever any interface
file says. That is mechanical, needs no inference about which expressions are
widgets, and would have caught every gap in the running inventory:
`takekioskscreen`, `after_idle`, `cget`, `wait_window`, `Window.lift`,
`EntryField.delete`/`insert`/`focus_set`, `bind_all`, and `ContextMenu`'s
three.

TWO FAILURE MODES, and only the first is visible today:

  * MISSING — the attribute is not there, so the call raises. Loud, unless it
    is raised inside a pywebview callback, where `on_event` logs and carries
    on (five of the gaps above presented as "nothing happened").
  * PRESENT AND INERT — a stub returning None. Silent everywhere: nothing
    raises, so nothing is logged, and the caller reports success. This is what
    `ContextMenu` was, and no runtime evidence can find it.

This module covers the first. The second needs stubs to declare themselves —
`NotImplementedError` for "not written yet", silence for a deliberate no-op
like `ScrollingFrame.windowsize` — which is the other half of Step 6.

READS SOURCE, IMPORTS NOTHING. `ui_tkinter` needs a display-capable tkinter
and `ui_webview` needs pywebview; this has to run on a machine with neither,
so it compares ASTs.
"""
import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FRONTEND = ROOT / 'frontend'


def _classes(path):
    """{class name: ({public members}, [base names])} from a module's source.

    BASES MATTER. The two backends organise their hierarchies differently —
    webview declares `takekioskscreen` and `deiconify` on `Toplevel` and has
    `Window` inherit them, tkinter the other way about — so comparing what
    each class declares IN ITSELF reports gaps that are not gaps. The first
    run of this file said `Window` was missing four members it has.
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
        # INSTANCE ATTRIBUTES COUNT. `self.buttons = {}` in __init__ is as
        # much a member as a class-level one, and reading only the class body
        # reported `buttons` as missing from webview when it is set at
        # `ui_webview.py:2651`. A false positive in an audit is expensive:
        # it costs the reader's trust in the whole list.
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


def _inherited(name, table, seen=None):
    """Everything `name` has in its own module, bases included."""
    if name not in table:
        return set()
    seen = seen or set()
    if name in seen:
        return set()                    # a cycle; nothing more to add
    seen.add(name)
    members, bases = table[name]
    out = set(members)
    for base in bases:
        out |= _inherited(base, table, seen)
    return out


_TK_RAW = _classes(FRONTEND / 'ui_tkinter.py')
_WV_RAW = _classes(FRONTEND / 'ui_webview.py')

# DECLARED, not inherited — for asking "does THIS class implement it".
# Resolving inheritance here made every widget report the same dozen names
# (`gridkwargs`, `pads`, `workarea`, `AUTOSCROLL_*`), because tkinter shares
# them through Gridded/UI/Childof mixins and webview does not mirror that
# hierarchy. 27 of 30 classes "had gaps" and almost none were real.
TK = {c: members for c, (members, _b) in _TK_RAW.items()}
WV = {c: members for c, (members, _b) in _WV_RAW.items()}

# MODULE-WIDE — for asking "does this backend have it ANYWHERE". The two
# organise their hierarchies differently (`takekioskscreen` on tkinter's
# Window, webview's Toplevel), so a name present somewhere is implemented;
# only a name present nowhere is a gap.
TK_ANY = set().union(*TK.values()) if TK else set()
WV_ANY = set().union(*WV.values()) if WV else set()
# MODULE LEVEL COUNTS TOO. webview declares some things as module constants
# where tkinter has them on a class — `WAIT_DELAY_MS` is one — and counting
# only class members reported those as missing when they were right there.
_wv_tree = ast.parse((FRONTEND / 'ui_webview.py').read_text())
for _node in _wv_tree.body:
    if isinstance(_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        WV_ANY.add(_node.name)
    elif isinstance(_node, ast.Assign):
        for _t in _node.targets:
            if isinstance(_t, ast.Name):
                WV_ANY.add(_t.id)


# Members tkinter has that webview is NOT expected to supply, with the reason.
# Anything not listed here and not implemented is a gap. Keep this SHORT and
# argued: a long allowlist is how a port stops being measured.
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
    #
    # Thirteen names is a long exemption, and long exemptions are how a port
    # stops being measured — but they are ONE decision, not thirteen: the
    # hover implementation is the engine's. Nothing outside the class names
    # any of them in either backend.
    'ToolTip': {'enter', 'entertip', 'leave', 'schedule', 'unschedule',
                'waittime', 'showtime', 'tw', 'id', 'event',
                'dispx', 'dispy', 'wraplength'},
}


def _gaps(cls):
    """Public members tkinter's `cls` has and webview's does not."""
    if cls not in TK or cls not in WV:
        return set()
    allowed = EXPECTED_ABSENT | DIFFERENT_BY_DESIGN.get(cls, set())
    return {m for m in TK[cls] - WV[cls] if m not in allowed}


def test_both_backends_define_the_same_widget_classes():
    """A class missing outright is the bluntest gap: every call site for it
    fails, and usually at import or construction rather than in a callback."""
    shared_worth_having = {
        'Window', 'Toplevel', 'Frame', 'Label', 'Button', 'Entry',
        'EntryField', 'CheckButton', 'RadioButton', 'ListBox', 'Combobox',
        'Progressbar', 'ScrollingFrame', 'Menu', 'ContextMenu', 'ToolTip',
        'Theme', 'Style', 'Image', 'Notebook', 'ButtonFrame',
    }
    missing = sorted(c for c in shared_worth_having
                     if c in TK and c not in WV)
    assert not missing, \
        "webview has no class for: {}".format(missing)


@pytest.mark.parametrize('cls', ['ContextMenu', 'Menu', 'ToolTip'])
def test_the_classes_that_bit_us_are_complete(cls):
    """The three from the 2026-09-11 session, pinned so they cannot regress.

    `ContextMenu` is the reason this file exists: a stub that satisfied its
    ABC completely while implementing none of the members the app calls.
    """
    gaps = _gaps(cls)
    assert not gaps, \
        "webview {} is missing: {}".format(cls, sorted(gaps))


def _module_gaps(called_only=True):
    """Names ui_tkinter declares somewhere and ui_webview declares nowhere.

    FILTERED BY WHETHER THE APP CALLS THEM, because the unfiltered list is 53
    names and mostly noise: kwarg tables (`bf_kwargs`, `my_tk_kwargs`),
    layout constants (`AUTOSCROLL_MS`, `MIN_AVAILABLE`), and helpers tkinter
    needs to talk to Tk. A member nothing outside `ui_tkinter` names is that
    backend's private business, and webview is entitled to do it differently
    or not at all.

    What survives is the question worth asking: the app calls this, and the
    webview backend has nowhere for the call to land.
    """
    allowed = set(EXPECTED_ABSENT)
    for names in DIFFERENT_BY_DESIGN.values():
        allowed |= names
    gaps = {n for n in TK_ANY - WV_ANY if n not in allowed}
    if called_only:
        gaps &= _app_attribute_names()
    return sorted(gaps)


def test_declared_surfaces_match():
    """ONE list, module-wide. Per-class was the wrong question: the two
    backends group their members differently, so the same name appearing on a
    different class is not a gap — only a name appearing on NO class is."""
    missing = _module_gaps()
    if missing:
        pytest.xfail('{} names ui_tkinter declares and ui_webview does '
                     'not:\n  {}'.format(len(missing), '\n  '.join(missing)))


# ── The inventory that matters: INHERITED tkinter API the app calls ─────────
# Every gap found the hard way so far — `lift`, `cget`, `after_idle`,
# `wait_window`, `takekioskscreen`, `bind_all` — is a member of tkinter's own
# Misc/Wm, not of a class this project declares. So comparing our two modules
# to each other could never have seen them: tkinter gets them for free and
# webview has to write each one.
#
# The question this answers: WHICH tkinter API does the app actually rely on,
# and does the webview backend supply it? Both halves are obtainable without a
# display — `dir(tkinter.Misc)` needs no Tk instance, and the app's own calls
# are in its source.

def _app_attribute_names():
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


def _webview_surface():
    """Every public name ui_webview declares, anywhere in the module."""
    surface = set()
    for members in WV.values():
        surface |= members
    tree = ast.parse((FRONTEND / 'ui_webview.py').read_text())
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            surface.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    surface.add(t.id)
    return surface


def test_the_tkinter_api_the_app_calls_is_implemented():
    """THE POINT OF THIS FILE. Expected to FAIL while gaps remain, and the
    list it prints is the remaining work — the alternative being to find each
    one when a user hits it, which is how all ten so far were found.

    Noisy by nature: an attribute name the app uses on some non-widget object
    will appear here if tkinter happens to define it too. Read it as a list to
    triage, not a list of bugs.
    """
    tkinter = pytest.importorskip('tkinter',
                                  reason='needs tkinter importable (no '
                                         'display required)')
    tk_api = set()
    for base in (tkinter.Misc, tkinter.Wm, tkinter.Widget):
        tk_api |= {n for n in dir(base) if not n.startswith('_')}
    called = _app_attribute_names() & tk_api
    missing = sorted(called - _webview_surface())
    if missing:
        pytest.xfail('{} tkinter members the app calls are not implemented '
                     'in ui_webview:\n  {}'.format(len(missing),
                                                   '\n  '.join(missing)))


def _tkinter_gaps():
    """The inventory, without pytest. Returns a sorted list of names."""
    import tkinter
    tk_api = set()
    for base in (tkinter.Misc, tkinter.Wm, tkinter.Widget):
        tk_api |= {n for n in dir(base) if not n.startswith('_')}
    return sorted((_app_attribute_names() & tk_api) - _webview_surface())


if __name__ == '__main__':
    # RUNNABLE WITHOUT PYTEST, because the output here is a REPORT rather than
    # a verdict, and a report should not need the dev requirements installed.
    # Kent tried `python -um tests.test_backend_surface_parity` — the habit
    # the manual scripts teach — and got nothing, because a pytest module has
    # no entry point (2026-09-11).
    #
    #     ../env/bin/python -um tests.test_backend_surface_parity
    #
    # The pytest form still works and is what CI reads; this is for looking.
    print('=' * 70)
    print("ui_tkinter members the app CALLS that ui_webview does not have")
    print('=' * 70)
    missing = _module_gaps()
    for name in missing:
        print('  ' + name)
    print('\n  {} name(s)'.format(len(missing)) if missing else '  none')

    rest = sorted(set(_module_gaps(called_only=False)) - set(missing))
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
        missing = _tkinter_gaps()
    except ImportError as e:
        print('  cannot check: {}'.format(e))
    else:
        for name in missing:
            print('  ' + name)
        print('\n  {} name(s)'.format(len(missing)))
