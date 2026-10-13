"""Only words Trust can profile count for the "Set up syllable profiles?" gate.

Kent, 2026-10-13: "if they aren't eligible for machine profiling, they
shouldn't trigger that gate." Audio-only words kept a machine profile from
older data, Trust could not apply it ("has no wmg form; can't apply"), and
the gate offered them again at every start.
"""
from types import SimpleNamespace

import pytest

profiles = pytest.importorskip('backend.core.profiles')


class FakeSense:
    def __init__(self, form, machine, confirmed=None):
        self.form, self.machine, self.confirmed = form, machine, confirmed

    def cvprofilevalue(self, ftype):
        return self.confirmed

    def cvprofilemachinevalue(self, ftype):
        return self.machine

    def textvaluebyftypelang(self, ftype, lang):
        return self.form


def analyzer():
    from backend.core import analysis_inputs
    a = profiles.ProfileAnalyzer.__new__(profiles.ProfileAnalyzer)
    p = analysis_inputs.CheckParameters.__new__(analysis_inputs.CheckParameters)
    a.program = SimpleNamespace(db=SimpleNamespace(analang='wmg'), params=p)
    p.program = a.program
    p.ftype = lambda: 'lc'
    a.constrain_presort_profile = lambda s, m, f: m   # no confirmed primitives
    return a


def test_a_word_trust_would_decline_is_not_counted():
    """Trust skips a word whose constrained profile is empty or Invalid; the
    offer used to count it anyway, so it came back after every Trust."""
    a = analyzer()
    a.constrain_presort_profile = lambda s, m, f: 'Invalid'
    assert not a.affirmable(FakeSense('baba', 'CVCV'), 'lc')
    a.constrain_presort_profile = lambda s, m, f: None
    assert not a.affirmable(FakeSense('baba', 'CVCV'), 'lc')


class Recorder(FakeSense):
    """Fails the test if anything tries to write an annotation."""
    def annotationvaluebyftypelang(self, ftype, lang, name, value=None):
        if value is not None:
            raise AssertionError(f'wrote {name}={value} on an audio-only word')
        return None

    def primitiveverification(self, ftype, value=None):
        if value is not None:
            raise AssertionError('wrote primitive verification')
        return []

    def cvprofilevalue(self, ftype, value=None):
        return self.confirmed


def test_the_seeder_skips_an_audio_only_word():
    """'has no wmg form; can't apply' at every start came from here."""
    a = analyzer()
    assert a.program.params.seed_sense_primitives(
        Recorder(None, 'CVC'), 'lc', 'wmg') is None


def test_the_trust_writers_skip_an_audio_only_word():
    a = analyzer()
    a._primitive_codes = lambda s, f: {}
    assert a._trust_primitives(Recorder(None, 'CVC'), 'lc',
                               {'#C': 'C', 'C#': 'C', 'syls': '1'}) == []
    assert a.needs_primitive_backfill(Recorder(None, 'CVC'), 'lc') is False


def test_a_written_word_with_a_machine_profile_is_affirmable():
    assert analyzer().affirmable(FakeSense('baba', 'CVCV'), 'lc')


def test_an_audio_only_word_is_not():
    a = analyzer()
    assert not a.affirmable(FakeSense(None, 'CVCV'), 'lc')
    assert not a.affirmable(FakeSense('  ', 'CVCV'), 'lc')


def test_confirmed_or_unanalysed_words_are_not():
    a = analyzer()
    assert not a.affirmable(FakeSense('baba', 'CVCV', confirmed='CVCV'), 'lc')
    assert not a.affirmable(FakeSense('baba', 'Invalid'), 'lc')
    assert not a.affirmable(FakeSense('baba', None), 'lc')
