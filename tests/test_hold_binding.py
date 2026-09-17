# coding=UTF-8
"""`composites.hold`: a press-and-hold control ends ONCE, on lift OR slide-off.

Kent, 2026-09-17, on the record button under webview, where a release off the
button never arrived and the recording did not end: "the metaphor is 'finger
off the button', which includes off=up and off=sideof."

The other half of the contract is the double stop this creates under tkinter,
whose pointer grab still delivers `<ButtonRelease-1>` after a slide-off:
`RecordButtonFrame._stop` destroys the button and builds the play/delete pair,
so a second `_stop` builds a second pair. Hence "once, and never without a
press".

A stand-in widget records what `hold` binds and lets the test fire it, which
is the suite's idiom for the composites (see `test_second_form_field_placeholder.py`).
"""
from frontend import composites


class Widget:
    def __init__(self):
        self.bound = {}

    def bind(self, event, fn, add=None):
        assert add == '+', ('hold must ADD its bindings: the tooltip binds '
                            '<Leave> on the same button, and a bare bind '
                            'replaces')
        self.bound.setdefault(event, []).append(fn)

    def fire(self, event):
        for fn in self.bound.get(event, []):
            fn(None)


def _held():
    w = Widget()
    calls = []
    state = composites.hold(w,
                            lambda e: calls.append('start'),
                            lambda e: calls.append('stop'))
    return w, calls, state


def test_it_binds_press_release_and_leave():
    w, _, _ = _held()
    assert set(w.bound) == {'<ButtonPress-1>', '<ButtonRelease-1>', '<Leave>'}


def test_press_then_lift_starts_and_stops_once():
    w, calls, state = _held()
    w.fire('<ButtonPress-1>')
    assert state.held is True
    w.fire('<ButtonRelease-1>')
    assert calls == ['start', 'stop']
    assert state.held is False


def test_slide_off_stops_and_the_grabbed_release_does_not_stop_again():
    """tkinter: <Leave> on the way out, then the grab delivers the release."""
    w, calls, _ = _held()
    w.fire('<ButtonPress-1>')
    w.fire('<Leave>')
    w.fire('<ButtonRelease-1>')
    assert calls == ['start', 'stop']


def test_slide_off_stops_when_no_release_ever_arrives():
    """webview: release is `click`, which never fires off the element."""
    w, calls, _ = _held()
    w.fire('<ButtonPress-1>')
    w.fire('<Leave>')
    assert calls == ['start', 'stop']


def test_passing_over_without_pressing_does_nothing():
    w, calls, _ = _held()
    w.fire('<Leave>')
    w.fire('<ButtonRelease-1>')
    assert calls == []


def test_a_second_hold_works_after_the_first():
    w, calls, _ = _held()
    w.fire('<ButtonPress-1>')
    w.fire('<ButtonRelease-1>')
    w.fire('<ButtonPress-1>')
    w.fire('<Leave>')
    assert calls == ['start', 'stop', 'start', 'stop']
