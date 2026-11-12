"""sameSort sets within the current slice (backend/core/samesort.py members; analysis.SliceDict.in_current).
Kent 2026-11-11: sliced by ps (C/V, tone) a set's nouns and verbs are sorted apart; for syllable profiles
(not sliced by ps) together. Intrinsic to the slicing, not a setting."""
import types

import pytest

try:
    from backend.core import samesort
except ImportError as e:  # optional dep missing in this env
    pytest.skip(f"optional dependency not installed: {e.name}", allow_module_level=True)


class Sense:
    def __init__(self, name, ps, setid='set1'):
        self.id, self.ps, self._set = name, ps, setid

    def samesortvalue(self, value=None):
        if value is not None:
            self._set = value
        return self._set


def _index(senses, slice_ps=None):
    """slice_ps: the ps of the current slice; None: not sliced by ps (syllable sort)."""
    slices = types.SimpleNamespace(
        in_current=lambda s: slice_ps is None or s.ps == slice_ps)
    program = types.SimpleNamespace(db=types.SimpleNamespace(senses=senses), slices=slices)
    return samesort.SameSort(program)


def test_syllable_sort_takes_the_whole_set():
    n1, n2, v1 = Sense('n1', 'Noun'), Sense('n2', 'Noun'), Sense('v1', 'Verb')
    index = _index([n1, n2, v1])
    assert index.members(n1) == [n1, n2, v1]


def test_a_ps_slice_takes_only_its_own_members():
    n1, n2, v1 = Sense('n1', 'Noun'), Sense('n2', 'Noun'), Sense('v1', 'Verb')
    index = _index([n1, n2, v1], slice_ps='Noun')
    assert index.members(n1) == [n1, n2]
    assert samesort.marked(index.program, n1, 'kalo') == 'kalo ×2'


def test_a_sense_outside_the_slice_gets_its_whole_set():
    n1, v1 = Sense('n1', 'Noun'), Sense('v1', 'Verb')
    index = _index([n1, v1], slice_ps='Noun')
    assert index.members(v1) == [v1, n1]


def test_join_on_a_ps_page_moves_the_whole_set():
    """Joining uses whole sets: otherwise the other ps's members would be left behind, unindexed."""
    n1, v1 = Sense('n1', 'Noun', 'A'), Sense('v1', 'Verb', 'A')
    n2 = Sense('n2', 'Noun', 'B')
    n3 = Sense('n3', 'Noun', 'B')
    index = _index([n1, v1, n2, n3], slice_ps='Noun')
    setid = index.join(n2, n1)
    assert {s.samesortvalue() for s in (n1, v1, n2, n3)} == {setid}
    assert len(index.sets[setid]) == 4
    assert index.members(n1) == [n1, n2, n3]                    # on the Noun page, still the nouns
