"""Gloss languages keep the user's order (Kent, 2026-10-19).

Glosslangs.sanitycheck de-duplicated with set(), so the order after any
change was hash order; and choosing the second language as the first
overwrote the first instead of swapping, leaving "second only".
"""
import pytest

ai = pytest.importorskip('backend.core.analysis_inputs')


def gl(*langs):
    return ai.Glosslangs(list(langs))


@pytest.mark.parametrize('a,b', [('en', 'fr'), ('fr', 'en'),
                                 ('swh', 'en'), ('en', 'swh')])
def test_the_order_survives_a_sanity_check(a, b):
    g = gl(a, b)
    g.sanitycheck()
    assert list(g) == [a, b]


def test_choosing_the_second_as_first_swaps():
    g = gl('en', 'fr')
    g.lang1('fr')
    assert list(g) == ['fr', 'en']


def test_choosing_the_first_as_second_swaps():
    g = gl('en', 'fr')
    g.lang2('en')
    assert list(g) == ['fr', 'en']


def test_a_new_first_language_replaces_the_first():
    g = gl('en', 'fr')
    g.lang1('swh')
    assert list(g) == ['swh', 'fr']


def test_a_new_second_language_replaces_the_second():
    g = gl('en', 'fr')
    g.lang2('swh')
    assert list(g) == ['en', 'swh']


def test_adding_a_second_keeps_the_first_first():
    g = gl('fr')
    g.lang2('en')
    assert list(g) == ['fr', 'en']


def test_the_first_cannot_also_be_the_second():
    g = gl('fr')
    g.lang2('fr')
    assert list(g) == ['fr']


def test_more_than_two_is_cut_to_the_first_two_in_order():
    g = gl('a', 'b', 'c')
    g.sanitycheck()
    assert list(g) == ['a', 'b']


def test_duplicates_and_none_go_keeping_order():
    g = gl('fr', None, 'fr', 'en')
    g.sanitycheck()
    assert list(g) == ['fr', 'en']
