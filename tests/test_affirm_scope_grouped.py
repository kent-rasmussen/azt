"""The Trust dialog's list groups words that Trust would treat alike (Kent
2026-11-12): one line per (profile, #C, C#, syls), listing its words, and the
fewer-than-10 limit counts lines, not words."""
from types import SimpleNamespace

import pytest

sorting_engine = pytest.importorskip('backend.core.sorting_engine')


class FakeSense:
    def __init__(self, form, machine):
        self.form, self.machine = form, machine

    def textvaluebyftypelang(self, ftype, lang):
        return self.form

    def cvprofilemachinevalue(self, ftype):
        return self.machine


def fake_self():
    params = SimpleNamespace(
        word_initial=lambda p: 'C' if p.startswith('C') else 'V',
        word_final=lambda p: 'C' if p.endswith('C') else 'V',
        syllable_count=lambda p: p.count('V'))
    profiles = SimpleNamespace(
        constrain_presort_profile=lambda s, machine, ftype: machine)
    return SimpleNamespace(program=SimpleNamespace(
        db=SimpleNamespace(analang='xx'), params=params, profiles=profiles))


def scope(senses):
    return sorting_engine.Sort._affirm_scope_text(fake_self(), senses, 'lc')


def test_words_that_behave_alike_share_a_line():
    text = scope([FakeSense('bad', 'CVC'), FakeSense('ma', 'CV'),
                  FakeSense('back', 'CVC')])
    assert text.splitlines() == [
        'bad, back  → CVC  (#C=C C#=C syls=1)',
        'ma  → CV  (#C=C C#=V syls=1)']


def test_many_alike_words_are_still_listed():
    """Ten words, one kind: one line, not the bare count it used to be."""
    text = scope([FakeSense(f'w{i}', 'CVC') for i in range(25)])
    assert len(text.splitlines()) == 1 and 'w0, w1' in text


def test_ten_kinds_fall_back_to_the_count():
    kinds = ['CV', 'CVC', 'VC', 'V', 'CVCV', 'CVCVC', 'VCV', 'VCVC',
             'CVCVCV', 'CVVC']
    text = scope([FakeSense(f'w{i}', k) for i, k in enumerate(kinds)])
    assert '10' in text and '→' not in text
