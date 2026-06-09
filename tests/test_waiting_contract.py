"""Contract tests for the `waiting()` context manager (added in v1.2.0).

`waiting()` is the fix for the stuck-progress-dialog class of bug: it must call
`waitdone()` on the way out of the `with` block whether the body returns
normally OR raises. We test the *real* implementation by invoking the unbound
method with a fake `self` that only records `wait`/`waitdone` calls — the method
touches nothing else, so this exercises the actual code path on each backend.
"""
import inspect

import pytest


class _FakeWaitable:
    def __init__(self):
        self.events = []

    def wait(self, msg=None, **kwargs):
        self.events.append("wait")

    def waitdone(self):
        self.events.append("waitdone")


def _waitable_classes():
    """Find each backend's class that defines `waiting` (skip if unimportable)."""
    classes = []
    try:
        from frontend import ui_tkinter
        classes.append(pytest.param(ui_tkinter.Waitable, id="tkinter"))
    except ImportError as e:  # pragma: no cover - env dependent
        classes.append(pytest.param(None, id="tkinter",
                                    marks=pytest.mark.skip(f"ui_tkinter import failed: {e}")))
    try:
        from frontend import ui_webview
        cls = next(
            (obj for _, obj in inspect.getmembers(ui_webview, inspect.isclass)
             if "waiting" in obj.__dict__ and hasattr(obj, "wait") and hasattr(obj, "waitdone")),
            None,
        )
        if cls is not None:
            classes.append(pytest.param(cls, id="webview"))
    except ImportError:
        pass  # webview backend deps not installed — fine
    return classes


@pytest.mark.parametrize("cls", _waitable_classes())
def test_waiting_calls_waitdone_on_normal_exit(cls):
    fake = _FakeWaitable()
    with cls.waiting(fake, msg="working"):
        fake.events.append("body")
    assert fake.events == ["wait", "body", "waitdone"]


@pytest.mark.parametrize("cls", _waitable_classes())
def test_waiting_calls_waitdone_on_exception(cls):
    fake = _FakeWaitable()
    with pytest.raises(ValueError):
        with cls.waiting(fake, msg="working"):
            fake.events.append("body")
            raise ValueError("boom")
    # the dialog must still be closed even though the body raised
    assert fake.events == ["wait", "body", "waitdone"]


@pytest.mark.parametrize("cls", _waitable_classes())
def test_waiting_calls_waitdone_on_early_return(cls):
    fake = _FakeWaitable()

    def use_it():
        with cls.waiting(fake):
            fake.events.append("body")
            return "result"
    assert use_it() == "result"
    assert fake.events == ["wait", "body", "waitdone"]
