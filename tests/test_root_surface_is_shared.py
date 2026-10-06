# coding=UTF-8
"""Whatever the app calls on `program.tk_root` must exist on BOTH backends.

WHY. `main.py::_leave_to_successor` calls `tk_root.quit()`. The tkinter Root
inherits `tkinter.Tk`, so it had `quit()` for free; the webview Root did not,
and `RootInterface` never named it. Nothing noticed until the restart handover
ran under `--webview` and died (2026-09-28):

    File "main.py", line 1503, in _leave_to_successor
        self.tk_root.quit()
    AttributeError: 'Root' object has no attribute 'quit'

That path is rare — it only runs when a restarting copy hands the machine to
its successor — so the gap survived every ordinary run. And the failure mode
is the worst one available: the predecessor does not leave, which is how two
live copies end up on one project, the exact thing the handshake prevents.

The general rule this pins: a method used through `tk_root` is part of a
CONTRACT between two independent implementations, and the way that contract
breaks is silently, on whichever backend nobody ran that path on. So derive
the list from the calls rather than maintaining it by hand.
"""
import re
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

# Set on the instance in __init__, so a class-level lookup cannot see them.
# RootInterface's own trailing comment is the source of this list: "Attributes:
# program, theme, renderer, exitFlag, wraplength, photo".
INSTANCE_ATTRS = {'program', 'theme', 'renderer', 'exitFlag', 'wraplength',
                  'photo'}

# `tk_root.exitFlag` must match as ONE name. An earlier sweep used [a-z_]+ and
# truncated it to `exit`, which looked like two modules calling a method that
# exists nowhere — a false alarm that cost a search. Names are not lowercase.
CALL = re.compile(r'\btk_root\.([A-Za-z_][A-Za-z0-9_]*)')

SKIP_DIRS = {'.git', 'env', 'tests', '.buildozer', 'modulestoinstall',
             '.pytest_cache', 'images', 'images_CAWL'}


def names_used():
    """Every `tk_root.<name>` in the app's own source."""
    found = {}
    for path in APP.rglob('*.py'):
        if any(part in SKIP_DIRS for part in path.relative_to(APP).parts):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except OSError:
            continue
        for line in text.splitlines():
            code = line.split('#', 1)[0]
            for name in CALL.findall(code):
                found.setdefault(name, set()).add(
                    str(path.relative_to(APP)))
    return found


def root_class(module_name):
    try:
        module = __import__('frontend.' + module_name, fromlist=['Root'])
    except Exception as e:                       # optional backend deps
        pytest.skip('{} not importable here ({})'.format(module_name, e))
    root = getattr(module, 'Root', None)
    if root is None:
        pytest.skip('{} has no Root'.format(module_name))
    return root


def test_the_sweep_finds_something():
    """A regex that matches nothing would make every test below pass."""
    used = names_used()
    assert len(used) > 5, 'found almost no tk_root calls; the sweep is broken'
    assert 'quit' in used, 'quit is the call this whole file exists for'
    assert 'exitFlag' in used, \
        'exitFlag must survive as one name, not be truncated to "exit"'


@pytest.mark.parametrize('backend', ['ui_tkinter', 'ui_webview'])
def test_every_tk_root_call_exists_on_this_backend(backend):
    root = root_class(backend)
    missing = {}
    for name, where in sorted(names_used().items()):
        if name in INSTANCE_ATTRS or name.startswith('_'):
            continue
        if not hasattr(root, name):
            missing[name] = sorted(where)
    assert not missing, (
        '{}.Root is missing {}; the app calls these through tk_root, so '
        'whichever code path uses one will die on this backend only. Called '
        'from: {}'.format(backend, ', '.join(sorted(missing)),
                          '; '.join('{} ({})'.format(n, ', '.join(w))
                                    for n, w in sorted(missing.items()))))


def test_quit_is_in_the_interface():
    """The contract, not just the two implementations. `quit` was used across
    the app while named in neither `RootInterface` nor the webview Root, which
    is precisely how it went missing."""
    from frontend import ui_interface
    assert hasattr(ui_interface.RootInterface, 'quit'), \
        'RootInterface must declare quit()'


# The interface is the ONE list; these tests read it rather than keeping a
# second copy. `ui_interface.py` exists to say what both backends must do, so
# adding a method there is what makes it checked here.
INTERFACES = [('RootInterface', ['Root']),
              ('ToplevelInterface', ['Toplevel', 'Window'])]


@pytest.mark.parametrize('backend', ['ui_tkinter', 'ui_webview'])
@pytest.mark.parametrize('iface,classes', INTERFACES)
def test_backend_provides_what_the_interface_declares(backend, iface, classes):
    """Every abstract name on an interface must exist on both backends' classes.

    THE SECOND ONE OF THESE IN A DAY is what earned this test. `Root.quit` and
    `Toplevel.state` were both used across the app, both free on tkinter by
    inheriting from Tk, both absent on webview, and both found only when a
    rarely-run path hit them — the restart handover, and the word page's
    return-key binding. Inheriting a method is not the same as promising one,
    and only the promise can be checked."""
    from frontend import ui_interface
    interface = getattr(ui_interface, iface)
    # THIS INTERFACE'S OWN DECLARATIONS, not everything it inherits.
    #
    # The first version swept `dir()`, which pulls in `WidgetInterface`'s
    # abstract methods too, and reported that `ui_tkinter.Root` and
    # `ui_tkinter.Toplevel` lack `grid_info` and `grid_remove`. True, and NOT a
    # defect: a toplevel is not gridded into a parent, so tkinter gives its
    # windows no grid methods either, and neither backend should.
    #   The inheritance `RootInterface(WidgetInterface)` therefore promises
    # more than a window can keep. Left alone — restructuring the interface is
    # a bigger decision than this test — but worth knowing before reading the
    # hierarchy as a contract.
    required = {n for n, v in vars(interface).items()
                if not n.startswith('_')
                and getattr(v, '__isabstractmethod__', False)}
    assert required, '{} declares no abstract methods of its own'.format(iface)
    module = None
    try:
        module = __import__('frontend.' + backend, fromlist=classes)
    except Exception as e:
        pytest.skip('{} not importable here ({})'.format(backend, e))
    # COLLECT ACROSS ALL THE CLASSES, and insist each one is really there.
    # Asserting inside the loop stopped at the first offender, so a second
    # class's gaps stayed hidden until the first was fixed; and `if cls is
    # None: continue` meant a renamed or missing class made this test pass by
    # checking nothing, which is the one result a guard must never give.
    absent = [c for c in classes if getattr(module, c, None) is None]
    assert not absent, \
        '{} defines no {}; this test would otherwise check nothing'.format(
            backend, ', '.join(absent))
    missing = {}
    for cls_name in classes:
        cls = getattr(module, cls_name)
        gaps = sorted(n for n in required if not hasattr(cls, n))
        if gaps:
            missing[cls_name] = gaps
    assert not missing, (
        '{} does not provide what {} declares — {}. The app calls these '
        'through the task/window bridge, so the gap appears only on whichever '
        'backend nobody ran that path on.'
        .format(backend, iface,
                '; '.join('{}: {}'.format(c, ', '.join(g))
                          for c, g in sorted(missing.items()))))
