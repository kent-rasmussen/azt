# coding=UTF-8
"""Backend work must test that the frontend is still there before continuing.

Kent's rule, 2026-09-14, on the crash that started this: "if there is backend
logic that relies on the frontend, it should test that it is there before
continuing. I used to have lots of code that would diesel on long after
tkinter had shut down, until I started asking about that." And on where:
"the answer here may be more of a check the catalog to not return to a window
that just isn't there."

The crash, from clicking Tasks while a page was still loading:

    _tkinter.TclError: bad window path name
        ".!taskwindow.!taskwindow.!frame.!frame"

TWO FAULTS, and the tests are in two halves to match:

  * `Senses._window_is_there()` — the boundary test. Stops the work.
  * `TaskBase.hide_chooser()` — honours the click that stopped it. Without
    this the app was left with NO WINDOW AT ALL, because the task's
    `__init__` withdrew the chooser that `gettask()` had just revealed.

WHAT `_window_is_there` ASKS ABOUT IS THE POINT, and a wrong answer was
shipped before the right one. `ui.frame` is absent during construction as
well as after teardown — the same observation, and only one of them is a
reason to stop. `exitFlag` is per-window and would serve, but it reports only
a quit routed through `on_quit`. The window itself is created before any slow
work and destroyed by `on_quit`'s final `destroy()`, so it is false exactly
when the work has nowhere to go, whatever killed it. Several tests below pin
that distinction.

Unit tests with a fake `self`, per tests/README.md: no Tk, no display, no
program, so they run on all three platforms and say nothing about either
backend. The fakes are real subclasses, built inside the tests — the guards
are called as methods, and building the fakes at import time would run the
skip-if-absent check during collection, which pytest reports as an error
rather than a skip.
"""
import importlib

import pytest


def _lexicon():
    try:
        return importlib.import_module('backend.core.lexicon')
    except ImportError as e:
        pytest.skip("optional dependency not installed: {}".format(e.name))


def _base():
    try:
        return importlib.import_module('tasks.base')
    except ImportError as e:
        pytest.skip("optional dependency not installed: {}".format(e.name))


class Explode:
    """Marker: asking this window whether it exists raises."""


class Flag:
    def __init__(self, value=False):
        self.value = value

    def istrue(self):
        return self.value


class Window:
    """A task window. `exists` is what Tk would answer."""

    def __init__(self, exists=True, frame=True):
        self._exists = exists
        if frame:
            self.frame = object()
        self.shown = []

    def winfo_exists(self):
        if self._exists is Explode:
            raise RuntimeError('bad window path name ".!taskwindow"')
        return self._exists

    def deiconify(self):
        self.shown.append('deiconify')


def task(window=True, **attrs):
    """A fake task carrying the REAL guard: a bare `Senses` with only what it
    reads. `window` takes a Window, True (a live one), or False (none)."""
    t = type('FakeTask', (_lexicon().Senses,), {})()
    if window is True:
        t.ui = Window()
    elif window is not False:
        t.ui = window
    for k, v in attrs.items():
        setattr(t, k, v)
    return t


# ── _window_is_there: what it asks about ─────────────────────────────────

def test_a_live_window_is_there():
    assert task()._window_is_there()


def test_a_destroyed_window_is_not_there():
    """The case that crashed: a live Python object naming a dead Tk widget,
    which only Tk can settle."""
    assert not task(window=Window(exists=False))._window_is_there()


def test_a_window_that_refuses_to_answer_is_not_there():
    """Tk raising about the path IS the dead-window answer."""
    assert not task(window=Window(exists=Explode))._window_is_there()


def test_a_window_still_being_dressed_IS_there():
    """NOT `ui.frame`. A page has no content frame yet during construction and
    none any more after teardown — the same observation, and only one of them
    is a reason to stop. Guarding on it refused every page in the app."""
    assert task(window=Window(frame=False))._window_is_there()


def test_a_set_exitflag_does_not_by_itself_mean_gone():
    """NOT `exitFlag`. It is per-window and would work, but it only reports a
    quit that went through `on_quit`; `winfo_exists` also covers a window
    destroyed any other way, and needs no state kept in sync. One signal,
    and it is the window itself."""
    w = Window(exists=True)
    w.exitFlag = Flag(True)
    assert task(window=w, exitFlag=Flag(True))._window_is_there()


# ── it may only stop work on positive evidence ───────────────────────────

def test_no_window_attribute_counts_as_there():
    """Absent is not evidence of death. A page that never appears is a worse
    failure than one that raises, so silence must not stop the build."""
    assert task(window=False)._window_is_there()


def test_a_window_that_cannot_be_asked_counts_as_there():
    class Bare:
        pass
    assert task(window=Bare())._window_is_there()


def test_a_hostile_bridge_counts_as_there():
    """`self.ui` resolves through the task-window bridge, which can raise
    something other than AttributeError while a window is dying."""
    def boom(self, name):
        raise RuntimeError('bridge is down: {}'.format(name))
    t = type('Hostile', (_lexicon().Senses,), {'__getattr__': boom})()
    assert t._window_is_there()


# ── the whole family inherits it ─────────────────────────────────────────

@pytest.mark.parametrize('name', ['Senses', 'Segments', 'WordCollection',
                                  'Parse', 'Tone', 'Syllables'])
def test_every_sense_class_can_ask(name):
    """It lives on `Senses` so builders anywhere in the family can use it; a
    class that cannot ask cannot be guarded."""
    cls = getattr(_lexicon(), name)
    assert callable(getattr(cls, '_window_is_there', None)), \
        "{} cannot ask whether its window is there".format(name)


def test_there_is_exactly_one_predicate_for_this():
    """Three overlapping versions of this test were written in one session
    (`_task_quit`, `_task_gone_reason`, `_task_is_gone`). Two names for one
    question is the `mainwindow`/`ismainwindow` trap — see
    agenda/bridge_shadowed_attributes.md — so the retired ones must stay
    retired."""
    senses = _lexicon().Senses
    stale = [n for n in ('_task_quit', '_task_gone_reason', '_task_is_gone',
                         '_window_state')
             if hasattr(senses, n)]
    assert not stale, "retired predicates are back: {}".format(stale)


# ── getwords: the reported crash site ────────────────────────────────────

class Reached(LookupError):
    """Raised by a fake `lex_ui` to prove the guard was passed."""


def _presenter_tripwire(t, explode=Reached):
    """Make `lex_ui` announce itself. It is the statement right after the
    guard, so touching it proves the guard let the build through. `type(t)` is
    a throwaway class built per `task()` call, so this pollutes nothing."""
    def tripped(self):
        raise explode('asked for the presenter')
    type(t).lex_ui = property(tripped)
    return t


def test_getwords_bails_before_touching_anything():
    """The guard must come before `self.lex_ui`: on the way out, nothing
    should be resolved through a bridge to a dead window."""
    lex = _lexicon()
    touched = []

    def boom(self, name):
        touched.append(name)
        raise AssertionError('touched {} after the window died'.format(name))

    t = _presenter_tripwire(task(window=Window(exists=False)),
                            explode=AssertionError)
    type(t).__getattr__ = boom
    assert lex.WordCollection.getwords(t) is None
    assert not touched, "getwords reached for {}".format(touched)


def test_getwords_builds_while_the_window_is_still_being_assembled():
    """getwords runs during page construction, so it must not stop for a
    window that is merely unfinished."""
    lex = _lexicon()
    t = _presenter_tripwire(task(window=Window(frame=False)))
    with pytest.raises(Reached):
        lex.WordCollection.getwords(t)


# ── hide_chooser: the NWAA ───────────────────────────────────────────────
#
# Stopping the build was only half the job. Clicking Tasks mid-load runs
# `gettask()` NESTED INSIDE the task's still-running `__init__` — the affix
# load drains the event loop — and it quits the task and re-reveals the
# chooser. Then the stack unwound back into `__init__`, which withdrew the
# chooser again. Nothing was left on screen.

class Chooser:
    def __init__(self):
        self.hidden = 0

    def withdraw(self):
        self.hidden += 1


class Program:
    def __init__(self):
        self.task = None
        self.taskchooser = Chooser()


def _task_with_chooser(live=True):
    t = type('FakeTask', (_base().TaskBase,), {})()
    t.program = Program()
    t.program.task = t if live else None
    return t


def test_hide_chooser_hides_it_for_the_live_task():
    t = _task_with_chooser(live=True)
    assert t.hide_chooser() is True
    assert t.program.taskchooser.hidden == 1


def test_hide_chooser_declines_once_the_user_has_gone_back():
    """THE NWAA. `gettask()` clears `program.task` and reveals the chooser;
    withdrawing it again is what left the screen empty."""
    t = _task_with_chooser(live=False)
    assert t.hide_chooser() is False
    assert t.program.taskchooser.hidden == 0, \
        "hid the chooser the user had just asked for"


def test_hide_chooser_declines_when_another_task_took_over():
    t = _task_with_chooser(live=True)
    t.program.task = object()       # a different task is live now
    assert t.hide_chooser() is False
    assert t.program.taskchooser.hidden == 0


# ── showwhenready: the bounded retry ─────────────────────────────────────

def _parse_stub(window=True, status=False, tries=3):
    """A fake Parse mid-reveal. `status` is what its status window would say
    to `winfo_exists`."""
    lex = _lexicon()
    scheduled = []
    t = task(window=window)
    t.showwhenready = lex.Parse.showwhenready.__get__(t)
    t.status = Window(exists=status)
    t.try_times = tries
    t.try_each_ms = 100
    t.after = lambda ms, fn: scheduled.append((ms, fn))
    return t, scheduled


def test_showwhenready_retries_while_the_window_is_still_building():
    """A one-shot bail inside a retry loop is a page that never appears: the
    loop exists BECAUSE the status window is not ready yet, so "not ready"
    must schedule another look, never give up."""
    t, scheduled = _parse_stub(status=False)
    t.showwhenready()
    assert len(scheduled) == 1, "did not schedule a retry: {}".format(scheduled)
    assert scheduled[0][0] == 100
    assert not t.ui.shown


def test_showwhenready_stops_once_the_window_is_gone():
    t, scheduled = _parse_stub(window=Window(exists=False), status=False)
    t.showwhenready()
    assert not scheduled, "kept retrying after the window was destroyed"


def test_showwhenready_gives_up_after_its_budget():
    t, scheduled = _parse_stub(status=False, tries=3)
    t.ready_waits = 3
    t.showwhenready()
    assert not scheduled, "retried past try_times"


def test_showwhenready_shows_the_page_when_status_arrives():
    t, scheduled = _parse_stub(status=True)
    t.showwhenready()
    assert t.ui.shown == ['deiconify']
    assert not scheduled, "retried after showing the page"


def test_a_failed_show_is_not_retried_as_not_ready_yet():
    """One `try` used to wrap both the readiness test and the deiconify, so a
    failed SHOW was reported as "self.status not found" and retried 100
    times — a log full of lines about the wrong thing."""
    t, scheduled = _parse_stub(status=True)

    def boom():
        raise RuntimeError('window would not show')
    t.ui.deiconify = boom
    t.showwhenready()
    assert not scheduled, "retried a readiness check after the page was ready"


# ── the affix loop: where the dieseling was ──────────────────────────────

def test_the_affix_loop_stops_when_the_window_goes():
    """Kent: "a check the catalog to not return to a window that just isn't
    there." `waitprogress` tolerates a missing wait window silently, so
    nothing used to stop: the catalog ran to completion and only then tried
    to build a page, which is where the crash surfaced."""
    lex = _lexicon()
    progress = []
    window = Window(exists=True)

    class Waiting:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    class Collector:
        def getfromlift(self):
            for i in (10, 20, 30, 40):
                if i == 30:
                    window._exists = False      # the user clicks Tasks
                yield i

    class Catalog:
        reported = 0

        def report(self):
            Catalog.reported += 1

    t = task(window=window)
    t.loadfromlift = True
    t.pss = []
    t.waitprogress = progress.append
    t.ui.waiting = lambda msg: Waiting()

    class FakeProgram:
        pass
    t.program = FakeProgram()
    t.program.db = type('DB', (), {'pss': [], 'nodes': None, 'senses': []})()
    t.program.parsecatalog = Catalog()

    monkey = lex.parser
    real_catalog, real_collector = monkey.Catalog, monkey.AffixCollector
    monkey.Catalog = lambda *a, **k: Catalog()
    monkey.AffixCollector = lambda *a, **k: Collector()
    try:
        lex.Parse.initparsecatalog(t)
    finally:
        monkey.Catalog, monkey.AffixCollector = real_catalog, real_collector

    assert progress == [10, 20], \
        "kept loading after the window went: {}".format(progress)
    assert Catalog.reported == 0, "reported into a window that was gone"
