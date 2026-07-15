# coding=UTF-8
"""Booklet page ordering (Kent 2026-07-11): page 1 'a'; remaining vowels in
facing pairs — LEFT = most frequent remaining, RIGHT = its most similar
sound; then consonants likewise. Similarity from the feature tables;
unknown symbols pair by frequency."""
import pytest

pytest.importorskip("lxml")
from backend.core.alphabet import propose_page_sequence, segment_distance


def test_voicing_pairs_are_nearest():
    assert segment_distance('p', 'b', 'C') < segment_distance('p', 't', 'C')
    assert segment_distance('s', 'z', 'C') < segment_distance('s', 't', 'C')


def test_vowel_neighbors_are_nearest():
    assert segment_distance('i', 'ɪ', 'V') < segment_distance('i', 'a', 'V')
    assert segment_distance('o', 'ɔ', 'V') < segment_distance('o', 'i', 'V')


def test_digraph_spelling_normalizes():
    # 'sh' is ʃ: closer to s than to p
    assert segment_distance('s', 'sh', 'C') < segment_distance('p', 'sh', 'C')


def test_a_first_then_similar_pairs_by_frequency():
    freq = {'a': 100, 'e': 50, 'ɛ': 30, 'i': 20, 'ɪ': 10}
    out = propose_page_sequence(['a', 'i', 'ɪ', 'e', 'ɛ'], [], freq)
    # 'a' alone first; e leads the next spread, ɛ faces it (similar, and the
    # frequency tie-break vs ɪ); i/ɪ close it out.
    assert out == ['a', 'e', 'ɛ', 'i', 'ɪ']


def test_consonants_follow_vowels_voicing_opposed():
    freq = {'a': 9, 'p': 40, 's': 30, 'b': 20, 'z': 10}
    out = propose_page_sequence(['a'], ['p', 'b', 's', 'z'], freq)
    assert out == ['a', 'p', 'b', 's', 'z']


def test_unknown_symbols_pair_by_frequency():
    freq = {'zz': 9, 'xx': 8, 'k': 1}
    out = propose_page_sequence([], ['zz', 'xx', 'k'], freq)
    assert out[:2] == ['zz', 'xx']  # both unknown → frequency decides
    assert out[2] == 'k'


def test_no_literal_a_seeds_with_most_a_like_vowel():
    # English-demo shape: no 'a'; æ is "the 'a' of this language"
    # (front low), ɑ the next candidate — NOT the most frequent (e).
    freq = {'e': 50, 'ɑ': 10, 'æ': 9, 'ʌ': 8, 'i': 7}
    out = propose_page_sequence(['e', 'ɑ', 'æ', 'ʌ', 'i'], [], freq)
    assert out[0] == 'æ'
    # and without æ, ɑ takes page 1
    out2 = propose_page_sequence(['e', 'ɑ', 'ʌ', 'i'], [], freq)
    assert out2[0] == 'ɑ'


def test_orthographic_y_pairs_as_glide():
    from backend.core.alphabet import segment_distance
    assert segment_distance('y', 'w', 'C') < segment_distance('y', 'h', 'C')
