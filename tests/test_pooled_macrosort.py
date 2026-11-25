"""Pooled macrosort: a pool group is one unit (backend/core/alphabet.py; stage 4, Kent 2026-11-25).
Real Alphabet methods on a fake `self`."""
from types import SimpleNamespace as NS
from backend.core.alphabet import Alphabet

A = 'Noun_CVC_lc_C2_t'        # C# pool, group t
B = 'Noun_CVCVC_lc_C3_t'      # same pool, same group: same unit
C = 'Noun_CVCVC_lc_C3_1'      # same pool, other (unnamed) group
D = 'Noun_CVCVC_lc_C2_t'      # C2 of CVCVC is C2#C: another pool


def alpha(pooled=True, all_ps=False, members=None):
    a = NS(program=NS(sorting_pooled=pooled, sorting_all_ps=all_ps),
           items_existing={A, B, C, D}, _gm=dict(members or {}), unsorted={}, conflicts={},
           _itemstomacrosort=set(), _itemsmacrosorted=set())
    for name in ('_pooled', 'pool_key', 'unit_items', 'conflict_code', 'parse_verificationcode',
                 'conflicting_items', 'mark_item_glyph', 'remove_item_from_glyph',
                 '_remove_item_from_glyph', 'itemstosort', 'mark_item_macrosorted',
                 'mark_item_tomacrosort', 'kick_conflicting_glyph_members'):
        setattr(a, name, getattr(Alphabet, name).__get__(a))
    a.glyph_members = lambda gm=None: a._gm if gm is None else a._gm.update(gm)
    log = []
    a._mark_item_glyph = lambda i, g: (log.append((i, g)),
                                       a._gm.setdefault(g, set()).add(i), None)[2]
    a.rm_glyph_member = lambda i, g=None: [m.discard(i) for m in a._gm.values()]
    a.cull_glyphdict = lambda: None
    a.marked = log
    return a


def test_not_pooled_nothing_changes():
    a = alpha(pooled=False)
    assert a.unit_items(A) == [A]
    assert a.conflict_code(A) == ['Noun', 'CVC', 'lc', 'C2']


def test_a_unit_is_the_pool_group_across_profiles():
    a = alpha()
    assert a.unit_items(A) == sorted([A, B])
    assert a.conflict_code(A) == a.conflict_code(C) == ['pool', 'Noun', 'lc', 'C#']
    assert a.conflict_code(D) != a.conflict_code(A)


def test_one_letter_for_the_whole_unit():
    a = alpha()
    a.mark_item_glyph(A, 't')
    assert sorted(a.marked) == sorted([(A, 't'), (B, 't')])


def test_its_own_unit_is_no_conflict_but_another_group_of_the_pool_is():
    a = alpha(members={'t': {B, C}})
    assert a.conflicting_items(A, 't') == [C]


def test_removing_one_item_returns_the_whole_unit_to_macrosort():
    a = alpha(members={'t': {A, B}})
    a.remove_item_from_glyph(A, 't')
    assert a._gm['t'] == set() and a._itemstomacrosort == {A, B}


def test_shown_once_per_unit():
    a = alpha()
    a._itemstomacrosort = {A, B, C}
    shown = a.itemstosort()
    assert len(shown) == 2 and C in shown and len({A, B} & set(shown)) == 1


def test_kick_leaves_a_units_items_together():
    a = alpha(members={'t': {A, B}})
    assert a.kick_conflicting_glyph_members() == []
    b = alpha(members={'t': {A, B, C}})
    kicked = b.kick_conflicting_glyph_members()
    assert {m for m, _g, _k in kicked} == {C}          # the unnamed group goes; t's unit stays
