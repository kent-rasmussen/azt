"""Switching the word form must not destroy the status built under another.

Segmental status nodes are keyed `(cvt, ps, profile, check)` — THE FORM IS
NOT IN THE KEY. Their `profile` dimension is the CV profile, whose membership
comes from `db.ps_profiles`, and that dict is built for ONE form. On
2026-09-30 the profile readers learnt to follow the form the user picks, and
two places that read `ps_profiles` as ground truth became form-dependent
without anything saying so:

  1. `StatusDict.cull()`'s membership sweep deletes a profile node when the
     profile is absent from `ps_profiles[ps]`. Under an unprofiled form every
     ps key is still there with an EMPTY set, so it read "no member words"
     for every profile and deleted all of them. `cull()` runs from
     `maybeboard()`, which `reload_for_word_check` calls — so the deletion
     happened on the switch itself. Kent, switching a segmental sort to Root
     and back: *"the reload brought us to an empty status table, but
     returning to Citation didn't give us back our data."*

  2. `reloadstatusdata` clears every group and rebuilds from LIFT. Run on a
     form with no profiles, the rebuild sources nothing and the clear stands
     alone.

Both now require POSITIVE evidence of emptiness before destroying anything.
An empty board on an unprofiled form is correct and expected; losing the
other form's record on the way past is not.
"""
import pytest

pytest.importorskip("lxml")
from backend.core.analysis import StatusDict


class _Params:
    def cvt(self):
        return 'V'

    def check(self, c=None, unset=False):
        return 'V1'


class _Slices:
    def ps(self, p=None):
        return 'Noun'

    def profile(self, p=None):
        return 'CVC'


class _Db:
    def __init__(self, ps_profiles):
        self.ps_profiles = ps_profiles


class _Program:
    pass


def _status(ps_profiles):
    """A status tree holding one real segmental group, plus a db picture."""
    prog = _Program()
    prog.params = _Params()
    prog.slices = _Slices()
    prog.db = _Db(ps_profiles)
    initial = {'V': {'Noun': {'CVC': {'V1': {'groups': ['i', 'a'],
                                             'done': ['i']}}}}}
    return StatusDict('test-status', initial, prog), prog


def test_an_unprofiled_form_does_not_cull_the_other_forms_nodes():
    """THE REPORTED LOSS. Every ps key present, every set empty — which is
    what an unprofiled form leaves behind, and says nothing about whether
    those profiles have members under the form that built them."""
    sd, _ = _status({'Noun': set(), 'Verb': set()})
    sd.cull()
    assert sd['V']['Noun']['CVC']['V1']['groups'] == ['i', 'a'], \
        'an empty profile set is no information, not "no members"'


def test_a_populated_picture_still_culls_a_profile_with_no_members():
    """The sweep must keep working: with a real picture for this ps that
    genuinely lacks CVC, the node goes."""
    sd, _ = _status({'Noun': {'CV', 'CVCV'}})
    sd.cull()
    assert 'CVC' not in sd.get('V', {}).get('Noun', {})


def test_a_profile_that_is_present_survives():
    sd, _ = _status({'Noun': {'CVC', 'CV'}})
    sd.cull()
    assert sd['V']['Noun']['CVC']['V1']['groups'] == ['i', 'a']


def test_no_picture_at_all_culls_nothing():
    """The pre-existing `is not None` guard, unchanged: before profiles are
    computed there is nothing to test membership against."""
    sd, prog = _status({})
    prog.db = None
    sd.cull()
    assert sd['V']['Noun']['CVC']['V1']['groups'] == ['i', 'a']


def test_the_reload_refuses_to_clear_what_it_cannot_rebuild():
    """`reloadstatusdata` clears before it rebuilds, so a form with nothing
    to rebuild from must not reach the clear."""
    from sourcescan import code
    from settings import Settings
    src = code(Settings.reloadstatusdata)
    guard = src.index('ps_profiles.values()')
    assert guard < src.index('clear_all_groups'), \
        'the emptiness check must come BEFORE the clear'
