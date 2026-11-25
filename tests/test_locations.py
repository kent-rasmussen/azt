"""Sorting locations from CV profiles (backend/core/locations.py; Kent, 2026-11-25)."""
from backend.core import locations as L


def locs(profile):
    return [loc for _i, loc in L.locations(profile)]


def test_edges_only():
    assert locs('CV') == ['#C', 'V#']
    assert locs('VC') == ['#V', 'C#']


def test_one_vowel_word_is_word_initial():
    assert locs('V') == ['#V']


def test_alternating_beginnings_are_named_by_the_first_segment():
    assert locs('VCVC') == ['#V', 'C1#V', 'V2#V', 'C#']
    assert locs('CVCV') == ['#C', 'V1#C', 'C2#C', 'V#']


def test_runs_of_the_other_type_collapse():
    # Kent: V1#C = V1 CV_, CCV_, CCCV_; C1#V = C1 VC_, VVC_; V2#C = CVCV_, CVCCV_, CCVCV_; V2#V = VCV_, VCCV_
    assert locs('CCV')[2] == 'V#' and locs('CCVC')[2] == locs('CCCVC')[3] == 'V1#C'
    assert locs('VVCV')[2] == 'C1#V'
    assert locs('CVCVC')[3] == locs('CVCCVC')[4] == locs('CCVCVC')[4] == 'V2#C'
    assert locs('VCVC')[2] == locs('VCCVC')[3] == 'V2#V'


def test_runs_of_the_same_type_are_spelled_out():
    assert locs('CVVC') == ['#C', 'V1#C', 'V2 CVV_', 'C#']
    assert locs('CVCCV') == ['#C', 'V1#C', 'C2#C', 'C3 CVCC_', 'V#']
    assert locs('CCV') == ['#C', 'C2 CC_', 'V#']


def test_consonant_types_and_marks_reduce_to_plain_c_and_v():
    assert L.reduce('NVGVʔ') == 'CVCVC'
    assert L.reduce('CVːCV̀') == 'CVCV'
    assert locs('CVN') == locs('CVC') == ['#C', 'V1#C', 'C#']


def test_not_a_profile():
    assert L.locations('Invalid') is None
    assert L.locations('') is None


def test_correspondence_both_ways_on_reduced_profiles():
    by_p, by_l, bad = L.correspondence({'CV': 10, 'CVCV': 3, 'CVːCV': 1, 'xx': 1})
    assert by_p['CVCV'] == ['#C', 'V1#C', 'C2#C', 'V#']
    assert by_l['#C'] == {'CV': 10, 'CVCV': 4}
    assert by_l['C2#C'] == {'CVCV': 4}
    assert bad == ['xx']


def test_coverage_lists_what_the_top_profiles_leave_out():
    counts = {'CV': 10, 'CVCV': 8, 'CVC': 1, 'VCV': 1}
    tops, needed, uncovered = L.coverage(counts, top=2)
    assert tops == ['CV', 'CVCV']
    assert needed == ['#C', 'V#', 'V1#C', 'C2#C']
    assert uncovered == [('CVC', ['C#']), ('VCV', ['#V', 'C1#V'])]   # ties: shorter, then A–Z


def test_counts_pool_ps_and_skip_ad_hoc_groups():
    pbs = {'analang': 'en', 'Noun': {'CV': ['a', 'b'], 'mine': ['c']}, 'Verb': {'CV': ['d']}}
    assert L.counts_from(pbs, {'Noun': {'mine': []}}) == {'CV': 3}


def test_a_check_maps_to_its_location_and_back():
    assert L.check_location('CVC', 'C2') == 'C#'
    assert L.check_location('CVCVC', 'C3') == 'C#'
    assert L.check_location('CVCVC', 'C2') == 'C2#C'
    assert L.check_location('NCV', 'C1') == 'C2 CC_'   # C1 = the literal C; N is a C here
    assert L.check_location('CV', 'C2') is None
    assert L.checks_of('CVC') == {'C1': '#C', 'V1': 'V1#C', 'C2': 'C#'}
    assert L.members('C#', ['CV', 'CVC', 'CVCVC']) == [('CVC', 'C2'), ('CVCVC', 'C3')]


def test_parse_code_takes_single_segment_checks_only():
    assert L.parse_code('C2=x') == ('C2', 'x')
    assert L.parse_code('V1=V2=1') is None


def test_carry_keeps_what_did_not_move_and_renames_it():
    # CVC → CVCVC: C1 (#C) and V1 (V1#C) kept; C2 (C#) becomes C3; the C2 group was final, now medial
    fields = {'CVC': ['C1=p', 'V1=a', 'C2=t']}
    ann = {'C1': 'p', 'V1': 'a', 'C2': 't'}
    add, set_ann, clear = L.carry('CVCVC', fields, ann)
    assert sorted(add) == ['C1=p', 'C3=t', 'V1=a']
    assert set_ann == {'C1': 'p', 'V1': 'a', 'C3': 't'}
    assert clear == ['C2']


def test_carry_drops_what_moved():
    # CV → VCV: C1 was #C, now C1#V, rechecked; the final vowel is still V# (V1 → V2), kept
    add, set_ann, clear = L.carry('VCV', {'CV': ['C1=p', 'V1=a']}, {'C1': 'p', 'V1': 'a'})
    assert add == ['V2=a'] and set_ann == {'V2': 'a'} and clear == ['C1', 'V1']


def test_carry_ignores_codes_the_annotation_no_longer_holds_and_existing_ones():
    fields = {'CVC': ['C1=p'], 'CV': ['C1=b']}
    assert L.carry('CV', fields, {'C1': 'b'}) == ([], {}, [])          # already verified under CV
    assert L.carry('CVCV', {'CVC': ['C1=p']}, {'C1': 'b'}) == ([], {}, [])   # resorted since


def test_location_codes_only_for_checks_verified_pooled():
    codes = ['C1=p', 'V1=a', 'C2=t']
    assert L.sync_location_codes('CVC', codes) == codes                # one profile: check codes only
    assert L.sync_location_codes('CVC', codes, ('C2',)) == codes + ['C#=t']
    assert L.sync_location_codes('CVCV', ['V1=V2=a', 'C2=t'], ('C2',)) == \
        ['V1=V2=a', 'C2=t', 'C2#C=t']


def test_location_codes_follow_their_check_codes():
    # C2 unsorted: its C# code goes; C2 re-sorted one profile alone: the old pooled C# code goes
    assert L.sync_location_codes('CVC', ['C1=p', '#C=p', 'C#=t']) == ['C1=p', '#C=p']
    assert L.sync_location_codes('CVC', ['C2=d', 'C#=t']) == ['C2=d']
    assert L.sync_location_codes('CVC', ['C2=d', 'C#=t'], ('C2',)) == ['C2=d', 'C#=d']
    assert L.sync_location_codes('CVC', []) == []


def test_carry_keeps_pooled_verification_pooled():
    single = {'CVC': ['C2=t']}
    pooled = {'CVC': ['C2=t', 'C#=t']}
    assert L.carry('CVCVC', single, {'C2': 't'})[0] == ['C3=t']
    assert L.carry('CVCVC', pooled, {'C2': 't'})[0] == ['C3=t', 'C#=t']


def test_report_shows_merges_and_ends_with_the_summary():
    text = '\n'.join(L.report({'CV': 10, 'CVN': 2, 'VCV': 1}, top=1))
    assert 'CVC ← CVN(2)' in text
    assert 'SUMMARY' in text and 'VCV (1): also needs #V, C1#V' in text
