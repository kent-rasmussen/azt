"""Pooled sorting writes each word under its OWN check and profile (backend/core/categories.py; stage 3a,
Kent 2026-11-25). Real Categories methods on a fake `self`."""
from types import SimpleNamespace as NS
from backend.core.categories import Categories


class Sense:
    def __init__(self, id, profile, groups=None):
        self.id, self.profile, self.groups = id, profile, groups or {}

    def cvprofilevalue(self, ftype):
        return self.profile


def task(pooled=True, all_ps=False, check='C2', profile='CVC', ps='Noun', senses=()):
    status = {'C': {'Noun': {'CVC': {'C2': {}}, 'CVCVC': {'C3': {}}},
                    'Verb': {'CVC': {'C2': {}}}}}
    bysp = {}
    for s in senses:
        bysp.setdefault((s.ps, s.profile), []).append(s)
    slices = NS(profile=lambda: profile, ps=lambda: ps,
                inslice=lambda lst, ps=None, profile=None: [s for s in lst
                                                             if s in bysp.get((ps, profile), [])])
    program = NS(sorting_pooled=pooled, sorting_all_ps=all_ps, status=status, slices=slices,
                 params=NS(check=lambda: check, ftype=lambda: 'lc'))
    t = Categories()
    t.program, t.cvt = program, 'C'
    t.getsensesingroup = lambda c, g: [s for s in senses if s.groups.get(c) == g]
    return t


def test_not_pooled_nothing_changes():
    t = task(pooled=False)
    assert t.pooled_location() is None
    assert t.word_slot(Sense('a', 'CVCVC'), 'C2', 'CVC') == ('C2', 'CVC')
    assert t.pool_senses_in_group('t') is None


def test_pooled_each_word_gets_its_own_check_and_profile():
    t = task()
    assert t.pooled_location() == 'C#'
    assert t.word_slot(Sense('a', 'CVCVC'), 'C2', 'CVC') == ('C3', 'CVCVC')
    assert t.word_slot(Sense('b', 'CVC'), 'C2', 'CVC') == ('C2', 'CVC')


def test_a_word_with_no_check_at_the_location_keeps_the_pages():
    t = task()
    assert t.word_slot(Sense('c', 'CV'), 'C2', 'CVC') == ('C2', 'CVC')


def test_members_one_ps_or_all():
    assert task().pool_members() == [('Noun', 'CVC', 'C2'), ('Noun', 'CVCVC', 'C3')]
    assert task(all_ps=True).pool_members() == [('Noun', 'CVC', 'C2'), ('Noun', 'CVCVC', 'C3'),
                                                ('Verb', 'CVC', 'C2')]


def test_senses_in_a_group_across_the_pool_by_their_own_check():
    a = Sense('a', 'CVC', {'C2': 't'}); a.ps = 'Noun'
    b = Sense('b', 'CVCVC', {'C3': 't'}); b.ps = 'Noun'
    c = Sense('c', 'CVCVC', {'C2': 't'}); c.ps = 'Noun'    # C2 of CVCVC is not C#
    d = Sense('d', 'CVC', {'C2': 't'}); d.ps = 'Verb'
    assert task(senses=[a, b, c, d]).pool_senses_in_group('t') == [a, b]
    assert task(all_ps=True, senses=[a, b, c, d]).pool_senses_in_group('t') == [a, b, d]
