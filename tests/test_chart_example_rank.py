# coding=UTF-8
"""chart_example_rank: default example-word selection for the alphabet chart.

Kent's rule (agenda default_image_page_ordering, DECIDED 2026-07-11):
prefer words where the glyph is the ONLY distinct segment of its class
(CVCV with C1=C2 …), then word-initial (C1 over C2), among pictured words
(picturedness is gated by the caller, not ranked here).
"""
import pytest

pytest.importorskip("lxml")  # alphabet.py -> sorting_engine -> ... -> lxml
from backend.core.alphabet import chart_example_rank


def test_only_consonant_in_word_wins():
    # CVCV with C1=C2=g: 'g' is the only consonant → rank 0
    assert chart_example_rank('C', 'g', {'C1=C2': 'g', 'V1': 'a', 'V2': 'o'}) == 0


def test_single_slot_profile_counts_as_only():
    # CV: one C slot, and it's the glyph → rank 0
    assert chart_example_rank('C', 'b', {'C1': 'b', 'V1': 'a'}) == 0


def test_word_initial_beats_merely_present():
    keys = {'C1': 'b', 'C2': 'sh', 'V1': 'ʊ'}
    assert chart_example_rank('C', 'b', keys) == 1   # initial
    assert chart_example_rank('C', 'sh', keys) == 2  # present, not initial


def test_vowel_class_mirrors():
    assert chart_example_rank('V', 'i', {'V1': 'i', 'V2': 'i', 'C1': 'b'}) == 0
    assert chart_example_rank('V', 'i', {'V1': 'i', 'V2': 'a', 'C1': 'b'}) == 1
    assert chart_example_rank('V', 'a', {'V1': 'i', 'V2': 'a', 'C1': 'b'}) == 2


def test_other_class_slots_do_not_disqualify():
    # A C-glyph's rank ignores how many vowels the word has
    assert chart_example_rank('C', 'm', {'C1': 'm', 'V1': 'a', 'V2': 'e'}) == 0


def test_no_keys_is_merely_present():
    assert chart_example_rank('C', 'b', {}) == 2
    assert chart_example_rank('C', 'b', None) == 2
