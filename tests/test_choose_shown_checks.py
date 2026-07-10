# coding=UTF-8
"""choose_shown_checks: default member selection for Review Letter Groups.

Rule under test (see frontend/sort_ui.py): privilege FIRST the number of
frames shown in the same position, THEN the position nearest the front of
the word; uncovered frames get the rule reapplied among themselves.
"""
from frontend.sort_ui import choose_shown_checks


def test_both_word_initial():
    assert choose_shown_checks([['C1'], ['C1']]) == ['C1', 'C1']


def test_no_shared_position_each_shows_what_it_has():
    assert choose_shown_checks([['C1'], ['C2']]) == ['C1', 'C2']


def test_shared_position_beats_word_initial():
    # One glyph has C1 and C2, the other only C2: showing both at C2
    # (2 frames same position) outranks showing C1 (1 frame, fronter).
    assert choose_shown_checks([['C1', 'C2'], ['C2']]) == ['C2', 'C2']


def test_tie_on_count_falls_to_frontmost():
    assert choose_shown_checks([['C3', 'C2'], ['C2', 'C3']]) == ['C2', 'C2']


def test_compound_check_ranks_by_first_digit():
    # C1=C2 counts as position 1, so it beats plain C2 on the tiebreak.
    assert choose_shown_checks([['C2', 'C1=C2'], ['C1=C2', 'C2']]) \
        == ['C1=C2', 'C1=C2']


def test_uncovered_frame_gets_own_frontmost():
    # First two share V2; the third can't show V2, so it shows its V1.
    assert choose_shown_checks([['V2'], ['V2', 'V3'], ['V1', 'V3']]) \
        == ['V2', 'V2', 'V1']


def test_uncovered_frames_still_pair_up():
    # Winner is C1 (3 frames); the two frames without C1 share C3 and
    # should be paired there rather than each falling to its frontmost.
    assert choose_shown_checks(
        [['C1'], ['C1'], ['C1'], ['C3', 'C4'], ['C3', 'C5']]) \
        == ['C1', 'C1', 'C1', 'C3', 'C3']


def test_digitless_checks_rank_last_but_still_pair():
    assert choose_shown_checks([['T'], ['T']]) == ['T', 'T']
    assert choose_shown_checks([['T', 'V1'], ['V1', 'T']]) == ['V1', 'V1']


def test_empty_frame_returns_none():
    assert choose_shown_checks([[], ['C1']]) == [None, 'C1']
