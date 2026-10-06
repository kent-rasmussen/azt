# coding=UTF-8
"""Backend code calling a TKINTER method through the task↔window bridge.

THE BUG CLASS, found twice in one day (2026-09-28) and both times by crashing:

    AttributeError: 'Root' object has no attribute 'quit'
    AttributeError: 'WordCollectnParsewRecordings' object has no attribute
                    'state'

Neither was a typo or a regression in the usual sense. Both were methods the
app calls freely, present on the tkinter backend by INHERITANCE from
`tkinter.Tk`/`Wm`/`Misc` rather than by anyone's decision, absent on the
webview backend, and reached only on a path nobody had run there — the restart
handover, and the word page's Return binding. Kent: *"perhaps we should be
watching for other tkinter-specific methods in disguise."*

In disguise is the right word. `self.state()` inside a backend mixin looks
like the task's own method. It is `tkinter.Wm.state`, arriving through
`TaskBase.__getattr__` → `TaskWindow.__getattr__`, and the bridge is what
makes it invisible: nothing in `backend/` or `tasks/` says tkinter anywhere.

WHAT THIS CHECKS. Every `self.X(...)`, `self.ui.X(...)` and `runwindow.X(...)`
in backend-facing code, where X is a name tkinter defines and the webview
backend does not. Those three receivers are the bridge itself, which is why
the filter is tight enough to be worth reading.

FIRST RUN IS AN AUDIT, NOT A VERDICT. The list is derived, so it will include
collisions — a name can be tkinter's AND ours. Each false positive earns an
entry in EXEMPT **with a reason that will still be true later**; the same rule
the import smoke test's exemption list carries, and for the same reason: an
entry here stops something being checked.
"""
import re
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

# Receivers that reach a WINDOW rather than a plain object. `self` is here
# because the bridge makes `self.<window method>` work inside every task.
CALLS = [re.compile(r'\bself\.([A-Za-z_]\w*)\s*\('),
         re.compile(r'\bself\.ui\.([A-Za-z_]\w*)\s*\('),
         re.compile(r'\brunwindow\.([A-Za-z_]\w*)\s*\(')]

# Where backend-facing code lives. `ui_tkinter.py` is EXCLUDED on purpose: it
# is the tkinter backend and may use anything tkinter offers.
SCAN = ['backend', 'tasks', 'frontend', 'settings', 'io_put', 'utilities']
SKIP_FILES = {'ui_tkinter.py', 'ui_webview.py', 'ui_interface.py',
              'tkintermod.py'}

# Names that are tkinter's AND legitimately ours, or otherwise not the bug.
# EVERY ENTRY NEEDS A REASON THAT OUTLIVES TODAY.
EXEMPT = {
    # Python builtins on dicts/objects that happen to collide with Misc.
    'keys':   'dict.keys, everywhere; Misc.keys is never what is meant',
    'update': 'dict.update and our own update(); Misc.update is a Tk idle pump',
    'get':    'dict.get, StringVar.get, ConfigManager.get — rarely Misc',
    'config': 'our own config(); widgets implement configure/config on both',
    'configure': 'implemented on both backends as the widget API',
    'destroy':   'implemented on both backends',
    'after':     'implemented on both backends',
    'bind':      'implemented on both backends',
    'bind_all':  'implemented on both backends',
    'unbind_all': 'implemented on both backends',
    'focus_set': 'implemented on both backends',
    'grid':      'implemented on both backends',
    'grid_remove': 'implemented on both backends',
    'lift':      'implemented on both backends',
    'wait_window': 'implemented on both backends',
    'update_idletasks': 'implemented on both backends',
    # ── Triaged from this test's FIRST RUN, 2026-09-28 ───────────────────
    # Both are OUR names that tkinter happens to share. The collision is
    # permanent, so these entries stay valid as long as the methods do.
    'command': 'ui_shell.Menus.command(parent,label,cmd) adds a menu entry. '
               'tkinter\'s is Wm.command, an alias of wm_command, which sets '
               'the X11 WM_COMMAND property and is never wanted here',
    'group':   'analysis.Analysis.group() and lexicon.Senses.group() are the '
               'sort-group accessor, a core domain concept in this app. '
               'tkinter\'s is Wm.group, the window-group leader',
}


def tkinter_names():
    """Public names tkinter puts on a window, from the real module."""
    try:
        import tkinter
    except Exception as e:                       # no Tk in this environment
        pytest.skip('tkinter not importable ({})'.format(e))
    names = set()
    for cls in (tkinter.Misc, tkinter.Wm, tkinter.Tk, tkinter.Toplevel):
        names |= {n for n in dir(cls) if not n.startswith('_')}
    return names


def webview_defines():
    """Every name the webview backend defines, on any class.

    Deliberately permissive — a name defined anywhere in that file counts as
    provided. A guard that cries wolf gets switched off, so this errs towards
    silence and still caught both of the real ones."""
    text = (APP / 'frontend' / 'ui_webview.py').read_text(encoding='utf-8')
    return set(re.findall(r'^\s*def\s+([A-Za-z_]\w*)', text, re.M))


def bridge_calls():
    """{name: {files}} for every window-ish call in backend-facing code."""
    found = {}
    for top in SCAN:
        root = APP / top
        if not root.is_dir():
            continue
        for path in root.rglob('*.py'):
            if path.name in SKIP_FILES:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except OSError:
                continue
            for line in text.splitlines():
                code = line.split('#', 1)[0]
                for pattern in CALLS:
                    for name in pattern.findall(code):
                        found.setdefault(name, set()).add(
                            str(path.relative_to(APP)))
    return found


def test_the_sweep_finds_something():
    """A pattern that matches nothing would make the audit below vacuous."""
    calls = bridge_calls()
    assert len(calls) > 50, 'almost no bridge calls found; the sweep is broken'
    assert webview_defines(), 'no defs found in ui_webview.py'
    assert 'state' in tkinter_names(), 'tkinter should define state'


def test_no_tkinter_only_method_is_called_through_the_bridge():
    calls = bridge_calls()
    tk = tkinter_names()
    wv = webview_defines()
    suspects = {}
    for name, where in calls.items():
        if name in EXEMPT or name in wv or name not in tk:
            continue
        suspects[name] = sorted(where)
    assert not suspects, (
        'these are tkinter methods reached through the bridge that the '
        'webview backend does not define, so they raise AttributeError there '
        'on whichever path uses them:\n' +
        '\n'.join('  {:<24} {}'.format(n, ', '.join(w))
                  for n, w in sorted(suspects.items())) +
        '\n\nEach is either a real gap (implement it on the webview backend, '
        'and declare it in ui_interface.py) or a collision (add it to EXEMPT '
        'with a reason that will still be true later).')
