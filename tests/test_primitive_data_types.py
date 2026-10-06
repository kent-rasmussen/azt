"""The syllable primitives declare their data types; readers read the declaration.

Kent, 2026-10-02: "keep C/V as the two labels". `#C` and `C#` are boolean —
two answers and only two — with the stored labels 'C' and 'V' unchanged;
`syls` is cardinal, any true result of len(). A data type carries its own
validator, so a stored syllable count of 0 is repaired by the type rather than
by a rule written into `seed_sense_primitives` (Kent: "this would flow from
the data type, rather than needing to be stipulated elsewhere in the code").
"""
import pytest

from sourcescan import code as _code

from backend.core import analysis_inputs


def _params():
    # An instance without __init__ (which needs a live program).
    return analysis_inputs.CheckParameters.__new__(analysis_inputs.CheckParameters)


def test_the_declaration():
    p = _params()
    assert p.data_type('#C') == 'boolean'
    assert p.data_type('C#') == 'boolean'
    assert p.data_type('syls') == 'cardinal'
    assert p.data_type('V1') == 'open'
    assert p.data_type('lc') == 'open'
    assert p.labels('#C') == ('C', 'V')
    assert p.labels('syls') is None
    assert p.labels('V1') is None


def test_boolean_means_two_labels_and_the_other_one():
    p = _params()
    assert p.other_label('#C', 'C') == 'V'
    assert p.other_label('C#', 'V') == 'C'
    assert p.other_label('syls', '2') is None
    assert p.valid_value('#C', 'C') and p.valid_value('#C', 'V')
    assert not p.valid_value('#C', 'True'), "the labels are C and V, not a Python bool's spelling"
    assert p.coerce_value('#C', 'x') is None, "a non-label has no nearest label"


def test_cardinal_is_any_true_len():
    p = _params()
    assert p.valid_value('syls', '1') and p.valid_value('syls', 4)
    assert not p.valid_value('syls', '0')
    assert not p.valid_value('syls', '-2')
    assert not p.valid_value('syls', 'two')
    assert p.coerce_value('syls', '0') == '1'
    assert p.coerce_value('syls', '-2') == '1'
    assert p.coerce_value('syls', '3') == '3'
    assert p.coerce_value('syls', 'two') is None


def test_open_accepts_anything_non_empty():
    p = _params()
    assert p.valid_value('V1', 'i') and p.valid_value('V1', '3')
    assert not p.valid_value('V1', '')
    assert p.coerce_value('V1', 'i') == 'i'


def test_the_predicate_reads_the_declaration():
    p = _params()
    assert p.is_syllable_boolean_check('#C')
    assert p.is_syllable_boolean_check('C#')
    assert not p.is_syllable_boolean_check('syls')
    assert not p.is_syllable_boolean_check('V1')
    src = _code(analysis_inputs.CheckParameters.is_syllable_boolean_check)
    assert "data_type(check)" in src
    assert "('#C','C#')" not in src, "no second copy of the two codes"


def test_no_other_button_for_a_non_open_location():
    """`getanotherskip` suppresses "Other" by the declaration, not by naming
    the two boolean codes; and an un-analysable word gets one syllable rather
    than no count (Kent, 2026-10-02: "just give them 1 syl, and users can
    increase as needed")."""
    sort_buttons = pytest.importorskip('frontend.sort_buttons')
    src = _code(sort_buttons.SortButtonFrame.getanotherskip)
    assert "data_type(self.check)!='open'" in src.replace(' ', '')
    assert 'is_syllable_boolean_check' not in src
    seed = _code(analysis_inputs.CheckParameters.seed_sense_primitives)
    assert "av(ftype,analang,'syls','1')" in seed.replace(' ', '')
    assert 'only syls missing, and no profile to count it from' not in seed


def test_the_flip_and_the_repair_read_the_type_not_the_letters():
    from backend.core import analysis
    flip = _code(analysis.SyllableSliceDict.move_misfit)
    assert "other_label(check,cur)" in flip.replace(' ', '')
    assert "'V' if cur=='C' else 'C'" not in flip
    seed = _code(analysis_inputs.CheckParameters.seed_sense_primitives)
    assert "valid_value('syls'" in seed and "coerce_value('syls'" in seed
    assert "=='0'" not in seed, "the 0→1 rule lives in the cardinal type now"
