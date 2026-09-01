"""Policy tests for the global no-window watchdog (added in v1.14.3).

The watchdog exists because "the user has no window" was, for a year, a bug we
could not see: the scoped guard was suppressed by an ambient window and logged
nothing, so the 2026-07-29 field incident produced no evidence at all. Its
value is therefore entirely in WHEN it speaks — too eager and its warnings get
ignored, too shy and we are back to no evidence. That policy is what is tested
here.

Driven through the real `_tick` with a fake program and a stubbed
`anything_viewable`, so the actual state machine runs. `_schedule` is stubbed
out because there is no event loop in a headless test; ticks are delivered by
hand instead.
"""
import pytest

visibility = pytest.importorskip("frontend.visibility")


class _FakeWindow:
    """Minimal stand-in for a ui.Window: content presence + deiconify record."""
    def __init__(self, content=True, exists=True):
        self._content = content
        self._exists = exists
        self.deiconified = 0

    def winfo_exists(self):
        return self._exists

    def deiconify(self):
        self.deiconified += 1


class _FakeProgram:
    def __init__(self, task=None, taskchooser=None):
        self.task = task
        self.taskchooser = taskchooser


def _watchdog(monkeypatch, viewable, program=None, windows=None):
    """A watchdog whose visibility answer and reveal list we control."""
    wd = visibility.VisibilityWatchdog(program or _FakeProgram())
    wd.running = True
    monkeypatch.setattr(wd, "_schedule", lambda: None)
    monkeypatch.setattr(wd, "_shutting_down", lambda: False)
    monkeypatch.setattr(wd, "_reveal_candidates", lambda: list(windows or []))
    monkeypatch.setattr(visibility, "anything_viewable",
                        lambda *a, **k: viewable())
    return wd


def _reports(wd, monkeypatch):
    """Record each time the watchdog decides to speak."""
    calls = []
    monkeypatch.setattr(wd, "_report_and_reveal", lambda: calls.append(wd.misses))
    return calls


def test_silent_until_it_has_seen_a_window(monkeypatch):
    """Boot legitimately has no window (the root is withdrawn, the splash comes
    later), so an unarmed watchdog must never fire — however slow the machine."""
    wd = _watchdog(monkeypatch, viewable=lambda: False)
    calls = _reports(wd, monkeypatch)
    for _ in range(wd.STRIKES * 4):
        wd._tick()
    assert calls == []


def test_reports_after_consecutive_strikes(monkeypatch):
    """One unlucky sample is not evidence — a page may withdraw one window
    before revealing the next — so it takes STRIKES in a row."""
    seen = [True]
    wd = _watchdog(monkeypatch, viewable=lambda: seen[0])
    calls = _reports(wd, monkeypatch)
    wd._tick()                     # arms
    seen[0] = False
    for _ in range(wd.STRIKES - 1):
        wd._tick()
    assert calls == [], "spoke before the strike count was reached"
    wd._tick()
    assert calls == [wd.STRIKES]


def test_one_report_per_episode(monkeypatch):
    """A genuinely stuck app must not write a line every poll: that buries the
    first, most useful one."""
    seen = [True]
    wd = _watchdog(monkeypatch, viewable=lambda: seen[0])
    calls = _reports(wd, monkeypatch)
    wd._tick()
    seen[0] = False
    for _ in range(wd.STRIKES * 5):
        wd._tick()
    assert len(calls) == 1


def test_recovery_rearms_for_the_next_episode(monkeypatch):
    """Reporting once per episode must not mean once per session — a second
    occurrence later on is exactly what the scoped one-shot guard missed."""
    seen = [True]
    wd = _watchdog(monkeypatch, viewable=lambda: seen[0])
    calls = _reports(wd, monkeypatch)
    wd._tick()
    seen[0] = False
    for _ in range(wd.STRIKES):
        wd._tick()
    seen[0] = True
    wd._tick()                     # recovered
    seen[0] = False
    for _ in range(wd.STRIKES):
        wd._tick()
    assert len(calls) == 2


def test_reveal_is_off(monkeypatch):
    """THE 1.14.3 REGRESSION. The watchdog revealed the task window on top of
    the tone-frame drafter the user was working in — because it could not find
    that page, not because the page was absent. A global watchdog cannot tell
    "the user has nothing" from "I failed to find what the user is looking at",
    and acting on the second wrecks work that the first would only stall. It
    reports; the scoped guard (which knows which run window belongs to the call
    in flight) reveals."""
    built = _FakeWindow(content=True)
    wd = _watchdog(monkeypatch, viewable=lambda: False, windows=[built])
    monkeypatch.setattr(visibility, "has_content", lambda w: w._content)
    wd.misses = wd.STRIKES
    wd._report_and_reveal()
    assert visibility.VisibilityWatchdog.REVEAL is False
    assert built.deiconified == 0


def test_never_reveals_an_empty_window(monkeypatch):
    """Even with revealing turned back on: a window with no content is a
    fullscreen block of theme colour whose only control is Exit, which reads as
    'quit the app?' at the worst possible moment (Kent 2026-08-24)."""
    empty = _FakeWindow(content=False)
    wd = _watchdog(monkeypatch, viewable=lambda: False, windows=[empty])
    monkeypatch.setattr(visibility, "has_content", lambda w: w._content)
    wd.REVEAL = True
    wd.misses = wd.STRIKES
    wd._report_and_reveal()
    assert empty.deiconified == 0


def test_reveals_the_first_window_with_content(monkeypatch):
    """Preference order, for whenever revealing is earned back: the run window
    of the task in flight before the task window, and the chooser last."""
    empty, built = _FakeWindow(content=False), _FakeWindow(content=True)
    wd = _watchdog(monkeypatch, viewable=lambda: False, windows=[empty, built])
    monkeypatch.setattr(visibility, "has_content", lambda w: w._content)
    wd.REVEAL = True
    wd.misses = wd.STRIKES
    wd._report_and_reveal()
    assert (empty.deiconified, built.deiconified) == (0, 1)


def test_global_watchdog_waits_longer_than_the_scoped_guard():
    """The scoped guard knows WHICH run window belongs to the call in flight,
    so it must always get first refusal. If someone shortens the global poll
    below RUNWINDOW_GUARD_MS, the blunt guard starts revealing pages mid-build
    — the 2026-08-24 regression, back again."""
    ui_shell = pytest.importorskip("frontend.ui_shell")
    scoped = ui_shell.TaskDressing.RUNWINDOW_GUARD_MS
    wd = visibility.VisibilityWatchdog
    assert wd.POLL_MS * wd.STRIKES > scoped
