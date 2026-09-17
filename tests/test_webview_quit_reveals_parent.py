# coding=UTF-8
"""Closing a child window puts its parent back.

WHY. `ui_tkinter.Toplevel.on_quit` has an `else:` branch that reveals the
parent (:1425-1495); the webview one had only the `to_root` half, so closing
a child window hid that window and put NOTHING in its place. Since
`getrunwindow` withdraws the task window before handing over the run window
(`ui_shell.py:3159`), the parent is always hidden by then — so Exit on a run
window left an empty screen with the app still running.

Kent reported that as "I thnk the runwindow is closing the app on exit", and
the log agreed about the symptom and not the cause: no `PROGRAM QUIT` line
anywhere (so `Root.on_quit` never ran), just

    Toplevel 237 hidden rather than destroyed, by ui_webview.py:… in <lambda>()

— the Exit button's own command, closing one window and revealing nothing.

THE THREE-WAY DECISION IS THE POINT, not the deiconify. Revealing
unconditionally is a known fault of its own: a task on its way out
re-revealed a parent whose frame had just been emptied, and the user got a
fullscreen kiosk page whose only control was Exit — "the very reason to NEVER
have that kind of page visible". So a wait already covering the screen is
left to do the revealing, an empty parent is reported and left hidden, and
only a parent with content is revealed. Those are tkinter's predicates, via
the same `visibility` helpers, so the two backends cannot drift.

Real method against a stand-in `self`, per tests/README.md.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')
visibility = pytest.importorskip('frontend.visibility',
                                 reason='needs frontend.visibility importable')

_reveal = ui_webview.Toplevel._reveal_parent_on_quit


class FakeParent:
    _exists = True
    _wid = 12

    def __init__(self, waiting=False):
        self._waiting = waiting
        self.revealed = 0

    def iswaiting(self):
        return self._waiting

    def deiconify(self):
        self.revealed += 1


class FakeChild:
    _wid = 237

    def __init__(self, parent, modal_on=None):
        self.parent = parent
        if modal_on is not None:
            self._modal_on = modal_on
        self.fell_back = 0

    def _nothing_behind_me(self):
        """THE CLOSE PATH OWNS WHAT COMES NEXT. Every branch that declines
        to reveal must reach this instead of returning into an empty
        screen — that is the whole of `_nothing_behind_me`, and these three
        tests were written when the branches just returned."""
        self.fell_back += 1


@pytest.fixture(autouse=True)
def _quiet_reports(monkeypatch):
    """`report_empty_page` notifies the user; record instead."""
    seen = []
    monkeypatch.setattr(visibility, 'report_empty_page',
                        lambda *a, **k: seen.append((a, k)))
    return seen


def _with_content(monkeypatch, answer):
    monkeypatch.setattr(visibility, 'has_content', lambda w: answer)


def test_a_parent_with_content_is_revealed(monkeypatch):
    _with_content(monkeypatch, True)
    parent = FakeParent()
    _reveal(FakeChild(parent))
    assert parent.revealed == 1


def test_an_empty_parent_is_reported_and_left_hidden(monkeypatch,
                                                     _quiet_reports):
    """Kent's rule: "we shouldn't be making pages visible, counting on them
    having meaning later." Either it has content, or it does not take the
    screen — but it IS reported, so an empty page is never merely silent."""
    _with_content(monkeypatch, False)
    parent = FakeParent()
    _reveal(FakeChild(parent))
    assert parent.revealed == 0
    assert _quiet_reports, 'an empty parent was left hidden without a word'
    assert _quiet_reports[0][0][0] == 'on_quit'


def test_a_parent_under_a_wait_is_left_to_the_wait(monkeypatch):
    """The wait is covering the screen and will reveal what it covers.
    Revealing underneath it would fight it."""
    _with_content(monkeypatch, True)
    parent = FakeParent(waiting=True)
    _reveal(FakeChild(parent))
    assert parent.revealed == 0


def test_no_parent_falls_back_to_the_task_list(monkeypatch):
    """Nothing behind it is not "do nothing" — it is the case that used to
    leave the screen empty and let two watchdogs notice 15 and 25 seconds
    later."""
    _with_content(monkeypatch, True)
    child = FakeChild(None)
    _reveal(child)
    assert child.fell_back == 1


def test_a_gone_parent_falls_back_too(monkeypatch):
    _with_content(monkeypatch, True)
    parent = FakeParent()
    parent._exists = False
    child = FakeChild(parent)
    _reveal(child)
    assert parent.revealed == 0
    assert child.fell_back == 1


def test_what_it_covers_beats_what_owns_it(monkeypatch):
    """OWNER AND MODAL-ON ARE DIFFERENT RELATIONSHIPS. A task owned by the
    root is modal on the chooser, and closing it must return to the chooser
    — the thing it covered — not to its owner. See
    agenda/modal_window_stack.md."""
    _with_content(monkeypatch, True)
    owner = FakeParent()
    covered = FakeParent()
    child = FakeChild(owner, modal_on=covered)
    _reveal(child)
    assert covered.revealed == 1
    assert owner.revealed == 0
    assert child.fell_back == 0


def test_the_root_is_never_revealed(monkeypatch):
    """The root has no page of its own worth showing, and tkinter excludes
    it for the same reason (`not isinstance(self.parent, Root)`)."""
    _with_content(monkeypatch, True)
    # Built without __init__ on purpose: this needs a real Root for the
    # isinstance test and none of its construction.
    root = object.__new__(ui_webview.Root)
    root._exists = True
    root._wid = 0
    root.revealed = 0
    root.deiconify = lambda: setattr(root, 'revealed', root.revealed + 1)
    child = FakeChild(root)
    _reveal(child)
    assert root.revealed == 0
    # But something still has to come next — the root has no page to show.
    assert child.fell_back == 1


def test_a_deiconify_that_raises_does_not_break_the_close(monkeypatch):
    """This runs during teardown. A failed reveal must not also break the
    window it is closing."""
    _with_content(monkeypatch, True)

    class Angry(FakeParent):
        def deiconify(self):
            raise RuntimeError('surface is gone')

    _reveal(FakeChild(Angry()))          # must not raise


def test_an_unanswerable_predicate_still_reveals(monkeypatch):
    """`has_content` swallows its own errors and answers False, so a broken
    probe would silently stop every reveal. If the DECISION cannot be made
    at all, revealing is the better failure: a window in the wrong state is
    reportable, an absent one looks like a crash."""
    def boom(w):
        raise RuntimeError('cannot tell')

    monkeypatch.setattr(visibility, 'has_content', boom)
    parent = FakeParent()
    _reveal(FakeChild(parent))
    assert parent.revealed == 1


def test_quit_asks_for_the_reveal_only_when_it_is_not_escalating():
    """`to_root` means the program is going down; there is nothing to
    reveal. Read from the source, because exercising on_quit needs a page."""
    src = (Path(__file__).resolve().parents[1]
           / 'frontend' / 'ui_webview.py').read_text(encoding='utf-8')
    body = src.split('    def on_quit(self, to_root=False, event=None):', 1)[1]
    body = body.split('\n    def ', 1)[0]
    assert 'self.parent.on_quit(to_root=True)' in body
    assert 'else:' in body
    assert '_reveal_parent_on_quit()' in body
    assert body.index('self.parent.on_quit(to_root=True)') \
           < body.index('_reveal_parent_on_quit()')
