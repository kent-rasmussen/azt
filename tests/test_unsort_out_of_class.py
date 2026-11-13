"""A profile sort that no longer fits its word's class is unsorted.

When a primitive changes (#C, C# or syls), the word moves to another profile
class but kept its old profile group, so a V-final class listed C-final
groups and the join paired them (Kent 2026-11-13). The rule: unsort it (clear
the sort group and the confirmed profile), so it is sorted again in its class.
"""
from backend.core import profiles


class _Sense:
    id = 's1'

    def __init__(self, anno, confirmed):
        self.anno = anno
        self.confirmed = confirmed

    def annotationvaluebyftypelang(self, ftype, lang, check, value=None):
        if value is None:
            return self.anno
        self.anno = value

    def primitiveverification(self, ftype):
        return ['#C=C', 'C#=C', 'syls=2']

    def cvprofilevalue(self, ftype, value=None):
        if value is None:
            return self.confirmed
        self.confirmed = value or None


class _Params:
    def __init__(self, pc):
        self.pc = pc

    def ftype(self):
        return 'lc'

    def profile_class_of_sense(self, sense, ftype=None):
        return self.pc

    def parse_profile_class(self, key):
        if key:
            return key[0], key[1:-1], key[-1]
        return None, None, None

    def profile_fits_class(self, profile, beg, syls, end):
        return profile[-1] == end  # enough to tell V-final from C-final


class _Fake:
    unsort_if_out_of_class = profiles.ProfileAnalyzer.unsort_if_out_of_class

    def __init__(self, pc):
        class DB:
            analang = 'en'

        class Prog:
            params = _Params(pc)
            db = DB()
        self.program = Prog()


def test_a_c_final_sort_in_a_v_final_class_is_unsorted():
    s = _Sense('CCVCVC', 'CCVCVC')
    assert _Fake('C2V').unsort_if_out_of_class(s)
    assert s.anno == ''
    assert not s.confirmed


def test_a_sort_that_fits_is_left_alone():
    s = _Sense('CCVCV', 'CCVCV')
    assert not _Fake('C2V').unsort_if_out_of_class(s)
    assert s.anno == 'CCVCV' and s.confirmed == 'CCVCV'


class _PrimSense:
    def __init__(self, value, codes):
        self.value = value
        self.codes = codes

    def annotationvaluebyftypelang(self, ftype, lang, check, value=None):
        return self.value

    def primitiveverification(self, ftype, value=None):
        if value is not None:
            self.codes = value
        return self.codes


class _Slices:
    from backend.core.analysis import SyllableSliceDict as _S
    _confirmed = _S._confirmed
    _group_of = _S._group_of
    _set_confirmed = _S._set_confirmed
    ftype = 'lc'
    analang = 'en'


def test_unconfirming_drops_only_that_checks_code():
    s = _PrimSense('V', ['#C=C', 'C#=C', 'syls=2'])
    _Slices()._set_confirmed(s, 'C#', 'V', verified=False)
    assert s.codes == ['#C=C', 'syls=2']


def test_no_class_or_parked_is_left_alone():
    assert not _Fake(None).unsort_if_out_of_class(_Sense('CCVCVC', None))
    assert not _Fake('C2V').unsort_if_out_of_class(_Sense('NA', None))
    assert not _Fake('C2V').unsort_if_out_of_class(_Sense('', None))
