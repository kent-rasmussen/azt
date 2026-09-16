# coding=UTF-8
"""Quitting a window frees what is waiting INSIDE it.

WHY. Around thirty call sites wait on a CANARY WIDGET inside a window rather
than on the window itself — the widget's destruction is the signal that a
page is finished (`sort_ui.py:762`, `ui_shell.py:2485`, …). `destroy()`
handles that: it recurses into `_children` and releases each waiter.
`Toplevel.on_quit` did not. It released waiters on the window's own wid and
HID the window, which is not a destruction, so every canary inside stayed
alive and every thread parked on one stayed parked.

Kent's faulthandler dump, 2026-09-16, with the sort run window closed by its
Exit button — `widget 237: waiting on widget 764`, window 237 hidden,
waiters on 237 released, and:

    ui_webview.py:1844 in wait_window        <- parked on an Event
    sorting_engine.py:1434 in presenttosort
    … sort -> maybesort -> after_presort -> drive_work -> runcheck
    ui_webview.py:3325 in <lambda>           <- the button that started it

The app's task flow runs on a pywebview API thread; parked there with
nothing on screen, the app is indistinguishable from closed. Which is what
Kent reported: "I thnk the runwindow is closing the app on exit". It was not
closing — it was hanging, and no `PROGRAM QUIT` line was ever written.

tkinter never had this: destroying a Toplevel destroys every descendant, and
`wait_window` returns on the target's destruction.
"""
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')


class Node:
    """A widget-shaped node: a wid, children, and optionally a window's flag."""

    is_window = False

    def __init__(self, wid, children=(), parent=None, flag=None):
        self._wid = wid
        self._children = list(children)
        self._exists = True
        self.parent = parent
        if flag is not None:
            self.exitFlag = flag
        for child in self._children:
            child.parent = self


class WindowNode(Node):
    is_window = True


@pytest.fixture(autouse=True)
def _clean_waiters():
    """The waiter table is module state; don't leak between tests."""
    with ui_webview._waiter_lock:
        ui_webview._waiters.clear()
    yield
    with ui_webview._waiter_lock:
        ui_webview._waiters.clear()


# ── Releasing the subtree ────────────────────────────────────────────

def test_a_waiter_on_a_descendant_is_released():
    """THE BUG. 764 is a canary two levels inside window 237."""
    canary = Node(764)
    window = WindowNode(237, [Node(300, [canary])])
    event = ui_webview._waiter_for(764)
    assert not event.is_set()
    ui_webview._release_waiters_below(window, 'quit')
    assert event.is_set()


def test_a_waiter_on_the_window_itself_is_still_released():
    window = WindowNode(237)
    event = ui_webview._waiter_for(237)
    ui_webview._release_waiters_below(window, 'quit')
    assert event.is_set()


def test_every_waiter_in_the_subtree_is_released():
    a, b, c = Node(1), Node(2), Node(3)
    window = WindowNode(9, [a, Node(4, [b, c])])
    events = [ui_webview._waiter_for(w) for w in (1, 2, 3, 4, 9)]
    ui_webview._release_waiters_below(window, 'quit')
    assert all(e.is_set() for e in events)


def test_a_cycle_in_the_children_does_not_loop_forever():
    """Runs during teardown, where a cycle must not become a hang of its
    own — which would be the same fault wearing the fix's clothes."""
    a = Node(1)
    b = Node(2, [a])
    a._children.append(b)
    event = ui_webview._waiter_for(1)
    ui_webview._release_waiters_below(b, 'quit')
    assert event.is_set()


class Hostile:
    """A node whose child list cannot be read — a widget part-way through
    teardown. Not a `Node`, so its constructor never touches `_children`."""

    is_window = False
    _wid = 2
    _exists = True
    parent = None

    @property
    def _children(self):
        raise RuntimeError('children are gone')


def test_a_child_list_that_raises_does_not_stop_the_walk():
    window = WindowNode(9, [Node(1), Hostile()])
    event = ui_webview._waiter_for(1)
    ui_webview._release_waiters_below(window, 'quit')
    assert event.is_set()


def test_a_node_with_no_wid_is_skipped():
    ui_webview._release_waiters_below(object(), 'quit')     # must not raise


# ── Knowing a window has quit ────────────────────────────────────────

def test_a_quit_window_above_is_found():
    flag = ui_webview.ExitFlag()
    flag.true()
    window = WindowNode(237, flag=flag)
    inner = Node(764, parent=window)
    assert ui_webview._quit_window_over(inner) == 237


def test_a_live_window_is_not_reported():
    window = WindowNode(237, flag=ui_webview.ExitFlag())
    inner = Node(764, parent=window)
    assert ui_webview._quit_window_over(inner) is None


def test_a_plain_widget_holding_the_flag_is_not_mistaken_for_the_window():
    """Ordinary widgets INHERIT the window's `exitFlag` object at
    construction, so the flag alone does not identify a window. Without the
    `is_window` test this would report a frame's wid as the window's."""
    flag = ui_webview.ExitFlag()
    flag.true()
    frame = Node(300, flag=flag)
    assert ui_webview._quit_window_over(frame) is None


def test_a_parent_chain_that_never_ends_is_bounded():
    node = Node(1)
    node.parent = node
    assert ui_webview._quit_window_over(node) is None


# ── wait_window's own guard ──────────────────────────────────────────

class FakeWaiter:
    """A widget-shaped `self` for wait_window."""

    _wid = 500
    wait_window = ui_webview._WebviewWidget.wait_window
    is_window = False

    def __init__(self, parent=None):
        self.parent = parent


def test_wait_window_does_not_park_in_a_window_that_has_quit(monkeypatch):
    """`on_quit` releases the waits that exist WHEN it runs. A flow that
    reaches here afterwards would park on a fresh Event that nothing will
    ever set — the same hang one turn later."""
    parked = []
    monkeypatch.setattr(ui_webview, '_waiter_for',
                        lambda wid: parked.append(wid) or threading.Event())
    flag = ui_webview.ExitFlag()
    flag.true()
    window = WindowNode(237, flag=flag)
    target = Node(764, parent=window)
    FakeWaiter(parent=window).wait_window(window=target)
    assert parked == [], 'parked in a window that had already quit'


def test_wait_window_still_parks_when_the_window_is_alive(monkeypatch):
    asked = []

    class Ready(threading.Event):
        def wait(self, timeout=None):
            asked.append(True)
            return True

    monkeypatch.setattr(ui_webview, '_waiter_for', lambda wid: Ready())
    window = WindowNode(237, flag=ui_webview.ExitFlag())
    target = Node(764, parent=window)
    FakeWaiter(parent=window).wait_window(window=target)
    assert asked == [True]


def test_wait_window_returns_at_once_for_a_target_already_gone(monkeypatch):
    """The other half of the deadlock, and already the case — pinned so it
    stays that way."""
    monkeypatch.setattr(ui_webview, '_waiter_for',
                        lambda wid: pytest.fail('should not have waited'))
    target = Node(764)
    target._exists = False
    FakeWaiter().wait_window(window=target)


def test_on_quit_releases_the_whole_subtree():
    """Read from the source: exercising on_quit needs a real window."""
    src = (Path(__file__).resolve().parents[1]
           / 'frontend' / 'ui_webview.py').read_text(encoding='utf-8')
    body = src.split('    def on_quit(self, to_root=False, event=None):', 1)[1]
    body = body.split('\n    def ', 1)[0]
    assert '_release_waiters_below(self' in body, \
        'on_quit releases only the window, not the canaries inside it'
