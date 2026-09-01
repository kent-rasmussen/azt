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
    # first_viewable, not anything_viewable: _tick needs the WINDOW so it can
    # tell a work surface from the boot splash. A plain _FakeWindow (no
    # boot_only) stands in for "something usable is on screen".
    _seen = _FakeWindow()
    monkeypatch.setattr(visibility, "first_viewable",
                        lambda *a, **k: _seen if viewable() else None)
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


def test_first_window_hook_skips_the_splash(monkeypatch):
    """The hook clears the restart marker, so it must mean "the app is usable",
    not "a window exists". The splash is visible for the whole of boot, and
    everything that can fail happens after it (Kent 2026-09-01)."""
    fired = []
    splash = _FakeWindow(); splash.boot_only = True
    chooser = _FakeWindow()
    seen = [splash]
    wd = visibility.VisibilityWatchdog(_FakeProgram(),
                                       on_first_window=lambda: fired.append(1))
    wd.running = True
    monkeypatch.setattr(wd, "_schedule", lambda: None)
    monkeypatch.setattr(wd, "_shutting_down", lambda: False)
    monkeypatch.setattr(wd, "_reveal_candidates", lambda: [])
    monkeypatch.setattr(visibility, "first_viewable", lambda *a, **k: seen[0])

    wd._tick()
    assert fired == [], "cleared the marker on the splash"
    assert wd.armed, "a visible splash must still arm the alarm"

    seen[0] = chooser
    wd._tick()
    assert fired == [1], "never fired once a work surface appeared"
    wd._tick()
    assert fired == [1], "fired more than once"


class _FakeFrame:
    def __init__(self, children=()):
        self._children = list(children)

    def winfo_exists(self):
        return True

    def winfo_children(self):
        return list(self._children)


class _FakePage:
    """A window with an Exit button, as QuitOnlyGuard cares about."""
    def __init__(self, children=(), viewable=True, waiting=False, exitbtn=True):
        self.frame = _FakeFrame(children)
        self.exitButton = object() if exitbtn else None
        self._viewable = viewable
        self._waiting = waiting

    def winfo_exists(self):
        return True

    def winfo_viewable(self):
        return self._viewable

    def iswaiting(self):
        return self._waiting

    def title(self):
        return "a page"


def _guard(monkeypatch, windows):
    g = visibility.QuitOnlyGuard(_FakeProgram())
    g.running = True
    monkeypatch.setattr(g, "_schedule", lambda: None)
    monkeypatch.setattr(visibility, "candidate_windows", lambda *a: list(windows))
    filled = []
    monkeypatch.setattr(g, "_fill", lambda w: filled.append(w))
    monkeypatch.setattr(g, "_unfill", lambda w: None)
    return g, filled


def test_quit_only_page_is_acted_on_after_strikes(monkeypatch):
    page = _FakePage(children=[])
    g, filled = _guard(monkeypatch, [page])
    for _ in range(g.STRIKES - 1):
        g._tick()
    assert filled == [], "acted before the strike count"
    g._tick()
    assert filled == [page]


def test_a_wait_dialog_excuses_an_empty_frame(monkeypatch):
    """A wait covering the window IS the sanctioned way to have an empty frame —
    both innocent readings (still building, just torn down) use one."""
    page = _FakePage(children=[], waiting=True)
    g, filled = _guard(monkeypatch, [page])
    for _ in range(g.STRIKES * 3):
        g._tick()
    assert filled == []


def test_a_brief_gap_does_not_count(monkeypatch):
    """A teardown on its way to a withdraw, or a rebuild that lands promptly, is
    over in milliseconds. Strikes must reset when content appears."""
    page = _FakePage(children=[])
    g, filled = _guard(monkeypatch, [page])
    g._tick()
    page.frame._children = [object()]  # the rebuild landed
    g._tick()
    page.frame._children = []          # a later, different gap
    g._tick()
    assert filled == [], "strikes carried across an intervening good poll"


def test_a_page_with_content_is_never_touched(monkeypatch):
    page = _FakePage(children=[object()])
    g, filled = _guard(monkeypatch, [page])
    for _ in range(g.STRIKES * 3):
        g._tick()
    assert filled == []


def test_a_window_without_an_exit_button_is_not_this_symptom(monkeypatch):
    """exit=False windows (the sound settings window) show no Quit at all, so an
    empty frame there is ugly but not the harm this guards against."""
    page = _FakePage(children=[], exitbtn=False)
    g, filled = _guard(monkeypatch, [page])
    for _ in range(g.STRIKES * 3):
        g._tick()
    assert filled == []


def test_global_watchdog_waits_longer_than_the_scoped_guard():
    """The scoped guard knows WHICH run window belongs to the call in flight,
    so it must always get first refusal. If someone shortens the global poll
    below RUNWINDOW_GUARD_MS, the blunt guard starts revealing pages mid-build
    — the 2026-08-24 regression, back again."""
    ui_shell = pytest.importorskip("frontend.ui_shell")
    scoped = ui_shell.TaskDressing.RUNWINDOW_GUARD_MS
    wd = visibility.VisibilityWatchdog
    assert wd.POLL_MS * wd.STRIKES > scoped
