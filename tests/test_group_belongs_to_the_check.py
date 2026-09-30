"""A group belongs to the check it was sorted under.

Kent, 2026-09-30, on the syllable sort's status line reading
"Checking Syllable Profiles, working on Whole Citation Word Syllable
Profile = C": *"C is not a legal value in C3C. I assume we're mixing checks
and groups across the two stages?"* Exactly that — `C` is a stage-1 answer to
`#C`/`C#`, and the check shown was the stage-2 profile check, whose groups
are cvprofiles.

The display was honest; the STATE was mixed. A group belongs to a
(cvt, ps, profile, check) slice, and nothing re-checked it when any of those
changed — `StatusDict.makegroupok` was written for this and had **no callers
anywhere in the app**.

An older patch treated the same class at the label rather than the state:
`cvgrouplabel` still carries a comment about the frame showing "working on
First Vowel None" when it "went stale from an x-check phase".
"""
import inspect
import types

import pytest

from backend.core import analysis


def _status(groups, group):
    """A stand-in with only what `makegroupok` touches."""
    ns = types.SimpleNamespace(_group=group)
    ns.groups = lambda **kw: list(groups)
    ns.group = analysis.StatusDict.group.__get__(ns)
    ns.makegroupok = analysis.StatusDict.makegroupok.__get__(ns)
    return ns


def test_a_group_outside_the_slice_is_replaced():
    """The main case: stage 1 left `C`, stage 2's groups are cvprofiles."""
    s = _status(['CVC', 'CVCVC'], 'C')
    s.makegroupok()
    assert s.group() == 'CVC'


def test_a_group_inside_the_slice_is_left_alone():
    """It must not reset the user's position on every refresh."""
    s = _status(['CVC', 'CVCVC'], 'CVCVC')
    s.makegroupok()
    assert s.group() == 'CVCVC'


def test_an_empty_slice_clears_the_group():
    """It used to leave the old one, which is how a stage-1 answer stayed on
    screen beside a stage-2 check. None renders as "All groups"."""
    s = _status([], 'C')
    s.makegroupok()
    assert s.group() is None


def test_an_empty_slice_with_no_group_stays_quiet():
    s = _status([], None)
    s.makegroupok()
    assert s.group() is None


def test_it_defines_the_attribute_it_reads():
    """Callable before anything has set a group."""
    ns = types.SimpleNamespace()
    ns.groups = lambda **kw: []
    ns.group = analysis.StatusDict.group.__get__(ns)
    analysis.StatusDict.makegroupok(ns)
    assert ns.group() is None


def test_something_actually_calls_it():
    """THE WHOLE BUG WAS THAT NOTHING DID. `makegroupok` existed, was
    correct, and had no callers — so the group was never validated against
    the check anywhere in the app."""
    from settings import Settings
    src = inspect.getsource(Settings.refreshattributechanges)
    assert 'makegroupok()' in src, \
        'the group must be settled after a settings change'


def test_the_check_changers_settle_the_group_themselves():
    """FOUR PATHS CHANGE A CHECK, and asking each caller to remember is what
    produced this. The two that live in `StatusDict` now do it themselves:

    * `makecheckok` — called from `setcvt` AFTER `refreshattributechanges`
      has run, so nothing downstream would have caught it;
    * `nextcheck` — `Transcribe.nextcheck` calls it directly and rebuilds
      its window, never reaching `setcheck`.
    """
    for fn in (analysis.StatusDict.makecheckok, analysis.StatusDict.nextcheck):
        assert 'makegroupok' in inspect.getsource(fn), fn.__name__


def test_opening_a_task_settles_the_group_too():
    """TWO PATHS, AND FIXING ONE DID NOT FIX THE OTHER.
    `refreshattributechanges` runs on settings CHANGES; opening a task runs
    `makeeverythingok`, which validated cvt, ps, profile and check and left
    the group. So a task opened straight after another kept its group —
    Kent, 2026-09-30, opening Sort Vowels from the syllable sort: "I just
    saw group=CVCCCV on SortV". A cvprofile is not a vowel."""
    from tasks import base
    src = inspect.getsource(base.TaskBase.makeeverythingok)
    assert 'makegroupok()' in src
    assert src.index('makecheckok()') < src.index('makegroupok()'), \
        'the group depends on the check, so it is settled after it'


def test_it_runs_after_the_branches_that_invalidate_the_group():
    """Order matters: cvt, ps, profile and check are all settled in the
    branches above, and a group validated before them would be validated
    against the OLD slice."""
    from settings import Settings
    src = inspect.getsource(Settings.refreshattributechanges)
    for branch in ("'cvt' in self.attrschanged", "'profile' in self.attrschanged",
                   "'check' in self.attrschanged"):
        assert src.index(branch) < src.index('makegroupok()'), branch
