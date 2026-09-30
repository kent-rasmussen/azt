"""The ps/profile picture belongs to ONE word form, and follows the chosen one.

Every CV profile in the slice dicts is read off a `cvprofile_<ftype>` field, so
which words have a profile, which profiles exist, and what the boards count are
all relative to a form. Three sites in `io_put/lift.py` had that form wired to
`'lc'`:

    i.cvprofilevalue()                                  # default ftype='lc'
    sense.annotationvaluedictbyftypelang('lc', …)       # literal
    sense.annotationkeysbyftypelang('lc', …)            # literal

`load_ps_profiles()` called them with nothing, so it rebuilt the citation
picture whatever the user had chosen. That made `Sort.reload_for_word_check` a
no-op BY CONSTRUCTION — the form chooser on a segmental sort page moved, the
rebuild ran, and it "returned the same data" (Kent, 2026-09-30). The chooser
was cosmetic.

Only 'lc' has ever been profiled in any project, so another form now gives a
near-empty picture until that form is profiled. That is the point, not a
regression: Kent, asked, *"near-emtpy: yes, that's what I expecte."* Showing
citation data under a Root heading is the alternative, and it is a lie.

The behavioural test runs the real method against a fake `self`, the way the
suite prefers; the rest are source guards on the callers, since a caller that
forgets the argument silently gets 'lc' back.
"""
import inspect
import re
from types import SimpleNamespace

import pytest

from io_put import lift


class FakeSense:
    """Just enough sense for the slicing: a ps and a per-form profile."""

    def __init__(self, ps, profiles):
        self._ps = ps
        self._profiles = profiles  # {ftype: profile}

    def psvalue(self):
        return self._ps

    def cvprofilevalue(self, ftype='lc', value=None, machine=False):
        return self._profiles.get(ftype)


def _fake_db(senses):
    """A `self` for the unbound Lift slicing methods."""
    db = SimpleNamespace(senses=senses,
                         entries=[],
                         pss=sorted({s.psvalue() for s in senses}),
                         analang='xyz-x-py')
    db.slicebyps = lambda: lift.LiftXML.slicebyps(db)
    return db


def test_the_slices_are_built_for_the_form_asked_for():
    """The whole point: ask for 'pl' and get the plural picture."""
    senses = [FakeSense('Noun', {'lc': 'CVC', 'pl': 'CVCV'}),
              FakeSense('Noun', {'lc': 'CVC'})]  # no plural profiled
    db = _fake_db(senses)

    lift.LiftXML.load_ps_profiles(db, 'lc')
    assert db.ps_profiles['Noun'] == {'CVC'}
    assert len(db.sensesbyps_profile['Noun']['CVC']) == 2

    lift.LiftXML.load_ps_profiles(db, 'pl')
    assert db.ps_profiles['Noun'] == {'CVCV'}, \
        'the profiles must come off the form asked for, not off lc'
    assert len(db.sensesbyps_profile['Noun']['CVCV']) == 1, \
        'a word with no profile in that form has no profile DATA yet'


def test_an_unprofiled_form_gives_an_empty_picture_not_the_lc_one():
    """Kent, 2026-09-30: "near-emtpy: yes, that's what I expecte." Nothing has
    ever written a `cvprofile_lx`, so Root shows nothing to sort — rather than
    silently showing citation data under a Root heading."""
    db = _fake_db([FakeSense('Verb', {'lc': 'CVCV'})])
    lift.LiftXML.load_ps_profiles(db, 'lx')
    assert db.ps_profiles['Verb'] == set()
    assert db.sensesbyps_profile['Verb'] == {}


@pytest.mark.parametrize('name', ['slicebyps_profile', 'get_ps_profiles',
                                  'load_ps_profiles',
                                  'annotation_values_by_ps_profile',
                                  'verified_groups_by_ps_profile'])
def test_every_profile_reader_takes_a_form(name):
    """Each of these reads one form's node and must be told which."""
    sig = inspect.signature(getattr(lift.LiftXML, name))
    assert 'ftype' in sig.parameters, \
        '{} reads a per-form field and must take an ftype'.format(name)


def test_no_profile_reader_hardcodes_the_citation_form():
    """The literals that made the rebuild a no-op. `'lc'` as a DEFAULT is
    fine — it is what LIFT load uses, before params exist; `'lc'` passed to a
    per-sense reader inside the body is the bug."""
    for name in ('slicebyps_profile', 'get_ps_profiles',
                 'annotation_values_by_ps_profile'):
        src = inspect.getsource(getattr(lift.LiftXML, name))
        body = src.split('\n', 1)[1]  # drop the def line, where the default is
        assert "'lc'" not in body, \
            "{} must read the form it was given, not the citation form".format(
                                                                        name)


@pytest.mark.parametrize('mod,fn', [
    ('backend.core.sorting_engine', 'Sort.reload_for_word_check'),
    ('backend.core.profiles', 'ProfileAnalyzer.rebuild_slices'),
    ('tasks.tasks', 'SortSyllables.reload_for_word_check'),
])
def test_the_rebuild_callers_name_a_form(mod, fn):
    """A caller that forgets the argument gets 'lc' and rebuilds the wrong
    picture — the exact failure this item started from, silently."""
    import importlib
    obj = importlib.import_module(mod)
    for part in fn.split('.'):
        obj = getattr(obj, part)
    src = inspect.getsource(obj)
    assert re.search(r'load_ps_profiles\(\s*\w', src), \
        '{} must pass the live form to load_ps_profiles'.format(fn)
