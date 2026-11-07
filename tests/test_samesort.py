"""sameSort sets (backend/core/samesort.py) and per-lexicon settings (SettingsManager lexicon_base).

sameSort: senses one word for sorting, each carrying the set id as a trait; every sort write goes to each
member, and pages show one item per set. Fake senses stand in for lift.Sense (only samesortvalue is used).
"""
import pytest

from backend.core import samesort


class FakeSense:
    def __init__(self, id, setid=None):
        self.id = id
        self.setid = setid

    def samesortvalue(self, value=None):
        if value == '':
            self.setid = None
        elif value:
            self.setid = value
        return self.setid

    def __repr__(self):
        return f"<{self.id}:{self.setid}>"


class FakeProgram:
    def __init__(self, senses):
        self.db = type('DB', (), {'senses': senses})()


def index(*senses):
    return samesort.SameSort(FakeProgram(list(senses)))


def test_members_of_a_set_lead_with_the_sense_asked_about():
    a, b, c = FakeSense('a', 'S'), FakeSense('b', 'S'), FakeSense('c', 'S')
    ix = index(a, b, c)
    assert ix.members(b) == [b, a, c]


def test_a_sense_in_no_set_is_its_own_set():
    a = FakeSense('a')
    ix = index(a, FakeSense('b', 'S'), FakeSense('c', 'S'))
    assert ix.members(a) == [a]


def test_a_set_of_one_is_dissolved_on_build():
    lone = FakeSense('a', 'S')
    index(lone, FakeSense('b'))
    assert lone.samesortvalue() is None


def test_representatives_keep_the_first_of_each_set_in_order():
    a, b, c, d = FakeSense('a', 'S'), FakeSense('b'), FakeSense('c', 'S'), FakeSense('d', 'T')
    e = FakeSense('e', 'T')
    ix = index(a, b, c, d, e)
    assert ix.representatives([b, c, a, e, d]) == [b, c, e]


def test_join_keeps_the_larger_sets_id():
    a, b, c = FakeSense('a', 'BIG'), FakeSense('b', 'BIG'), FakeSense('c', 'BIG')
    d, e = FakeSense('d', 'SMALL'), FakeSense('e', 'SMALL')
    ix = index(a, b, c, d, e)
    assert ix.join(d, a) == 'BIG'
    assert {s.samesortvalue() for s in (a, b, c, d, e)} == {'BIG'}
    assert 'SMALL' not in ix.sets
    assert set(ix.members(e)) == {a, b, c, d, e}


def test_joining_two_lone_senses_mints_a_set():
    a, b = FakeSense('a'), FakeSense('b')
    ix = index(a, b)
    setid = ix.join(a, b)
    assert setid and a.samesortvalue() == b.samesortvalue() == setid
    assert ix.members(a) == [a, b]


def test_leave_takes_one_out_and_the_rest_stay_a_set():
    a, b, c = FakeSense('a', 'S'), FakeSense('b', 'S'), FakeSense('c', 'S')
    ix = index(a, b, c)
    ix.leave(a)
    assert a.samesortvalue() is None
    assert ix.members(a) == [a]
    assert set(ix.members(b)) == {b, c}


def test_leave_from_a_pair_ends_the_set():
    a, b = FakeSense('a', 'S'), FakeSense('b', 'S')
    ix = index(a, b)
    ix.leave(a)
    assert a.samesortvalue() is None and b.samesortvalue() is None
    assert 'S' not in ix.sets


def test_module_helpers_without_an_index_change_nothing():
    a = FakeSense('a', 'S')
    program = object()
    assert samesort.members(program, a) == [a]
    assert samesort.representatives(program, [a]) == [a]
    assert samesort.marked(program, a, 'word') == 'word'


def test_marked_shows_the_set_size():
    a, b, c = FakeSense('a', 'S'), FakeSense('b', 'S'), FakeSense('c', 'S')
    program = FakeProgram([a, b, c])
    samesort.SameSort(program)
    assert samesort.marked(program, a, 'word') == 'word ×3'


def test_splitting_off_a_member_gives_it_a_row_of_its_own():
    a, b, c = FakeSense('a', 'S'), FakeSense('b', 'S'), FakeSense('c', 'S')
    program = FakeProgram([a, b, c])
    samesort.SameSort(program)
    assert samesort.split(program, b, shown=[a]) == [b]
    assert samesort.members(program, a) == [a, c]


def test_splitting_off_the_row_itself_gives_the_rest_a_row():
    a, b, c = FakeSense('a', 'S'), FakeSense('b', 'S'), FakeSense('c', 'S')
    program = FakeProgram([a, b, c])
    samesort.SameSort(program)
    assert samesort.split(program, a, shown=[a]) == [b]
    assert samesort.members(program, a) == [a]
    assert set(samesort.members(program, b)) == {b, c}


def test_splitting_a_pair_leaves_two_lone_rows():
    a, b = FakeSense('a', 'S'), FakeSense('b', 'S')
    program = FakeProgram([a, b])
    samesort.SameSort(program)
    assert samesort.split(program, b, shown=[a]) == [b]
    assert a.samesortvalue() is None and b.samesortvalue() is None


def test_joined_rows_are_covered_by_the_target():
    a, b, c = FakeSense('a'), FakeSense('b', 'S'), FakeSense('c', 'S')
    d = FakeSense('d')
    program = FakeProgram([a, b, c, d])
    samesort.SameSort(program)
    samesort.join(program, a, b)
    assert samesort.covered_by(program, [b], [a, b, c, d]) == [a, b, c]


def test_module_join_and_split_without_an_index_change_nothing():
    a, b = FakeSense('a'), FakeSense('b')
    program = object()
    assert samesort.join(program, a, b) is None
    assert samesort.split(program, a, [a]) == []
    assert a.samesortvalue() is None


# ---- per-lexicon settings -------------------------------------------------------------------------------

def _manager():
    try:
        from settings import SettingsManager
    except Exception as e:  # heavy package import; skip if env can't load it
        pytest.skip(f"settings package import failed: {e}")
    return SettingsManager


def test_a_text_lexicon_keeps_status_and_place_apart(tmp_path):
    SettingsManager = _manager()
    main = SettingsManager(tmp_path / "prj", hostname="H", user="U")
    main.set('ps', 'Noun')
    main.set('analang', 'baf')
    main.set('status', {'V': {'Noun': {}}})
    text = SettingsManager(tmp_path / "prj", hostname="H", user="U", lexicon_base=tmp_path / "story")
    assert text.separate_lexicon
    assert text.get('ps') is None                # the main lexicon's place isn't this one's
    assert text.get('status') is None
    assert text.get('analang') == 'baf'          # the project's settings are shared
    text.set('ps', 'Word')
    assert SettingsManager(tmp_path / "prj", hostname="H", user="U").get('ps') == 'Noun'
    assert (tmp_path / "story.U.H.lexicon.json").exists()


def test_a_text_lexicon_shares_the_projects_letter_decisions(tmp_path):
    SettingsManager = _manager()
    main = SettingsManager(tmp_path / "prj", hostname="H", user="U")
    main.data.save({'polygraphs': {'baf': {'gb': True}}, 'status': {'x': 1}})
    text = SettingsManager(tmp_path / "prj", hostname="H", user="U", lexicon_base=tmp_path / "story")
    assert text.get('polygraphs') == {'baf': {'gb': True}}
    assert text.get('status') is None
    text.set('interpret', {'baf': {'kp': 'C'}})      # a decision made while sorting a text...
    again = SettingsManager(tmp_path / "prj", hostname="H", user="U")
    assert again.get('interpret') == {'baf': {'kp': 'C'}}   # ...is the project's
    assert 'interpret' not in text.data.data
