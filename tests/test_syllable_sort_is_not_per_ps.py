"""Syllable sorting carries no part of speech.

A word's cvprofile (`CVC`) and its profile class (`C2V`) are facts about the
FORM. Two words that look the same have the same profile whatever their
category, so establishing one is wordlist-wide work. Kent, 2026-09-30:
*"NOTHING in SortSyllables does [vary by ps] … we shouldn't be sorting by
syllable profile for each ps."*

The design said so already — `SYLLABLE_PREP_PS = '*'` is documented "ps
re-enters only downstream as the (profile × ps) segmental slice" — and prep
honoured it while the profile sort did not, so the same work was presented and
tracked once per category: a word sorted under Noun stayed unsorted under Verb.

These are source-level guards. The behaviour needs a loaded LIFT file, which
the suite deliberately does not have; what can be checked without one is that
no syllable path reaches for a live ps again.
"""
import inspect
import re

import pytest

from sourcescan import code as _code

from backend.core import analysis, analysis_inputs, sorting_engine


def _src(fn):
    return inspect.getsource(fn)


def test_the_sentinel_still_documents_the_rule():
    """The constant this all keys on, and the sentence that justifies it."""
    p = analysis_inputs.CheckParameters
    assert p.SYLLABLE_PREP_PS == '*'
    assert 'downstream' in inspect.getsource(analysis_inputs).split(
        'SYLLABLE_PREP_PS')[1][:400]


def test_the_syllable_wordlist_is_not_filtered_by_ps():
    """`SliceDict.senses` for cvt 'S' read `db.sensesbyps.get(ps, [])` while
    its own comment said "'S' works the WHOLE ps wordlist" — whole **ps**
    wordlist, where the design wants the whole wordlist."""
    head = _code(analysis.SliceDict.senses).split(
                        "cvt()=='σ'")[1].split('if not kwargs')[0]
    assert 'sensesbyps' not in head, \
        "the syllable wordlist must not be filtered by ps"
    assert 'db.senses' in head


def test_the_board_gate_keys_on_the_sentinel():
    """`maybeboard` asked whether the LIVE ps had a σ node; σ nodes live under
    SYLLABLE_PREP_PS, so the syllable board was never drawn (found 2026-10-02,
    while verifying the σ migration)."""
    ui_shell = pytest.importorskip('frontend.ui_shell')
    src = _code(ui_shell.StatusFrame.maybeboard)
    assert 'SYLLABLE_PREP_PS' in src
    assert "if self.ps in self.program.status[self.cvt]" not in src


def test_the_profile_done_rebuild_keys_on_the_sentinel():
    """`rebuild_syllable_profile_done` bucketed `by[ps][pc]` and wrote one
    node per ps, so identical profile work was tracked per category."""
    src = _code(sorting_engine.Sort.rebuild_syllable_profile_done)
    assert 'SYLLABLE_PREP_PS' in src
    assert not re.search(r"node\([^)]*ps=ps\b", src), \
        'the syllable profile node must not be keyed on a live ps'


def test_the_prep_slices_key_on_the_sentinel():
    """`syllable_slices` built `SyllableSliceDict(program, ps, ftype)` from
    `slices.ps()` and rebuilt whenever it changed — one wordlist-wide job
    turned into one job per category. `syllable_prep_complete` was already
    reading the node at the sentinel and ignoring the ps it was handed."""
    src = _code(sorting_engine.SyllablePrep.syllable_slices)
    assert 'SYLLABLE_PREP_PS' in src
    assert 'slices.ps()' not in src


def test_the_new_profile_options_read_the_sentinel_node():
    """`unused_profiles_for_class` excludes profiles already sorted into the
    class by reading its node; under a live ps it found an empty one and
    offered profiles another category had already taken."""
    src = _code(analysis_inputs.CheckParameters.unused_profiles_for_class)
    assert 'SYLLABLE_PREP_PS' in src
    assert 'slices.ps()' not in src


@pytest.mark.parametrize('name', ['makeSyllableprogresstable', 'boardtitle',
                                  'sliceline', 'profilevalue'])
def test_the_board_and_the_slice_line_dropped_ps(name):
    """The visible half: cells read the sentinel node, the title stops
    saying "Progress for Noun", and the slice line shows the profile class
    with no category beside it."""
    from frontend import ui_shell
    src = _src(getattr(ui_shell.StatusFrame, name))
    assert 'syllable-sort-is-not-per-ps' in src, \
        '{} should say why it dropped ps'.format(name)
