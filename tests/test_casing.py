"""Capitals of an orthography's glyphs (backend/core/casing.py) and their use in
profiling (Kent 2026-11-07: "This" profiled 'Invalid' — no capital T in the
inventory)."""
import pytest

from backend.core import casing


def test_matching_accepts_title_and_full_capitals():
    assert casing.matching_capitals('th') == {'Th', 'TH'}
    assert casing.matching_capitals('t') == {'T'}
    assert casing.matching_capitals('ŋ') == {'Ŋ'}
    assert casing.matching_capitals("'") == set()            # no case pair


def test_an_override_names_the_one_capital_or_none():
    o = {'ny': 'Ny', 'ŋ': None}
    assert casing.matching_capitals('ny', o) == {'Ny'}
    assert casing.matching_capitals('ŋ', o) == set()


def test_the_capital_shown_follows_the_rule():
    assert casing.capital('ny', 'full') == 'NY'
    assert casing.capital('ny', 'title') == 'Ny'
    assert casing.capital('ny', 'none') is None
    assert casing.capital('ny', 'full', {'ny': 'Ny'}) == 'Ny'
    assert casing.capital("'", 'full') is None


def test_fold_drops_a_capital_listed_beside_its_glyph():
    assert casing.fold(['f', 'F', 'W', 'b', 'B']) == ['f', 'W', 'b']


def _rxdict(sdict):
    rx = pytest.importorskip('utilities.rx')
    # undistinguished classes fold into C ('C+N+G+D+ʔ+S') and V ('V+̀+ː'), so
    # each must exist, empty as in a real inventory (rx.py's own example)
    sdict = {'N': [], 'G': [], 'S': [], 'D': [], 'ʔ': [], '̀': [], 'ː': [],
             '=': ['-'], '<': [], **sdict}
    return rx.RegexDict(distinguish={'G': False, 'N': False, 'S': False,
                                     'D': False, 'ʔ': False, 'Gwd': False,
                                     'Nwd': False, 'Swd': False, 'Dwd': False,
                                     'ʔwd': False, '<': True, '=': True,
                                     '̀': False, 'ː': False},
                        interpret={'NC': 'CC', 'CG': 'CC', 'CS': 'CC',
                                   'VV': 'VV', 'VN': 'VN'},
                        sdict=sdict,
                        profilelegit=['̃', 'N', 'G', 'S', 'D', 'C', 'Ṽ', 'V',
                                      'ʔ', 'ː', "̀", '=', '<'],
                        invalidchars=[' '],
                        profilesegments=['N', 'G', 'S', 'D', 'C', 'V', 'ʔ'],
                        capitals=casing.matching_capitals)


def test_a_capital_profiles_as_its_glyph():
    d = _rxdict({'C': ['th', 't', 's', 'v', 'n'], 'V': ['i', 'a']})
    assert d.uncapitalized('This') == 'this'
    assert d.profileofform('This', ps='Word') == 'CVC'
    assert d.profileofform('THis', ps='Word') == 'CVC'


def test_capitals_that_are_class_letters_dont_eat_the_profile():
    # 'V' is the capital of the glyph v, and the class letter profiling writes
    d = _rxdict({'C': ['v', 'n', 's'], 'V': ['a', 'i']})
    assert d.profileofform('Vanis', ps='Word') == 'CVCVC'
    assert d.profileofform('vanis', ps='Word') == 'CVCVC'


def test_without_capitals_given_nothing_changes():
    d = _rxdict({'C': ['t', 'h', 's'], 'V': ['i']})
    d.capitals = None
    assert d.uncapitalized('This') == 'This'
