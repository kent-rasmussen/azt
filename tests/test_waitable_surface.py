# coding=UTF-8
"""Both webview window classes must answer the whole Waitable contract.

`ui_webview.Root` and `ui_webview.Toplevel` do NOT share a base for this:
each carries its own copy of `wait`, `waitdone`, `waitprogress`,
`drive_work` and the rest. That is a standing invitation to add a method to
one and not the other, and the cost is not a missing feature — it is an
AttributeError raised inside a pywebview event callback, where `on_event`
logs it and carries on, so the app simply stops mid-operation with no error
on screen.

It has now happened twice:

  * `drive_work` was on Root and not on Toplevel. `sorting_engine.py:666`
    calls `self._get_safe_window().drive_work(...)`, and the safe window is
    a Window — never the root — so the root's copy could not be reached
    from there. Running a sort check under webview raised
    "PORT GAP: 'Window' object has no attribute 'drive_work'" (Kent, GTK,
    2026-09-15). `azt/CLAUDE.md` calls `drive_work` the one member the task
    protocol and the Tk-shaped API agree on, which makes a window unable to
    answer it the worst member of the set to lose.
  * `cancel_drive_work` was missing outright until the 2026-09-11 parity
    audit, for the same reason.

The real fix is for the two classes to share the mixin they are pretending
to be (`tasks/ui_protocol.py`'s unadopted `TaskUI` is the other half of that
conversation). Until then, this test is what makes the duplication safe:
add a Waitable member to one class and the suite says which one is missing
it, instead of a user finding out when a sort page stops responding.
"""
import pytest

pytest.importorskip('frontend.ui_webview',
                    reason='webview backend not importable here')

from frontend import ui_webview            # noqa: E402  (after importorskip)

# The wait/work contract. Every name here is called on a WINDOW somewhere in
# the app, not only on the root.
WAITABLE = (
    'wait',
    'waitdone',
    'waitprogress',
    'waitcancel',
    'waitpause',
    'waitunpause',
    'iswaiting',
    'waiting',
    'drive_work',
    'cancel_drive_work',
    'wait_and_drive_work',
)

# The window verbs the app calls on both — `ui_shell` asks for these on the
# root as well as on task windows (:2739, :2952).
WINDOW_VERBS = (
    'withdraw',
    'deiconify',
    'lift',
    'lower',
    'protocol',
    'on_quit',
    'title',
    'attributes',
    'takekioskscreen',
    'takefullscreen',
    'releasefullscreen',
    'bind_all',
    'unbind_all',
)


@pytest.mark.parametrize('name', WAITABLE + WINDOW_VERBS)
@pytest.mark.parametrize('cls', ('Root', 'Toplevel'))
def test_window_class_answers_the_contract(cls, name):
    """Each window class implements each member, callably."""
    klass = getattr(ui_webview, cls, None)
    assert klass is not None, "ui_webview has no {}".format(cls)
    attr = getattr(klass, name, None)
    assert attr is not None, (
        "ui_webview.{} has no {!r}. The other window class probably does — "
        "these two duplicate the whole set, so a member added to one and not "
        "the other raises inside a pywebview callback, where on_event logs it "
        "and the app carries on with the operation half done.".format(
            cls, name))
    assert callable(attr), "ui_webview.{}.{} is not callable".format(cls, name)
