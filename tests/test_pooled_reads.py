"""Pooled sorting reads the whole pool (stage 3b, Kent 2026-11-25): the to-sort list, the verify write.
Real methods on fake `self`s; nothing here runs unless sorting is pooled."""
from types import SimpleNamespace as NS
from settings import Settings
from backend.core.sorting_engine import Sort


class Sense:
    def __init__(self, id, profile, groups):
        self.id, self.profile, self.groups = id, profile, groups

    def annotationvaluebyftypelang(self, ftype, lang, check):
        return self.groups.get(check)


class Status:
    def __init__(self, task):
        self._task, self.tosort_list, self.sorted_list, self.written = task, [], [], {}

    def task(self):
        return self._task

    def renewsensestosort(self, todo, done):
        self.tosort_list, self.sorted_list = list(todo), list(done)

    def marksensetosort(self, sense):
        self.tosort_list.append(sense)

    def marksensesorted(self, sid):
        self.sorted_list.append(sid)

    def groups(self, g=None, **kw):
        self.written[(kw.get('ps'), kw.get('profile'), kw.get('check'))] = sorted(g)


def test_the_to_sort_list_spans_the_pool_each_word_by_its_own_check():
    a = Sense('a', 'CVC', {'C2': 't'})          # sorted at C#
    b = Sense('b', 'CVCVC', {})                 # its C3 (C#) unsorted
    c = Sense('c', 'CVCVC', {'C2': 'k'})        # C2 of CVCVC is not C#: unsorted at C#
    bys = {('Noun', 'CVC'): [a], ('Noun', 'CVCVC'): [b, c]}
    task = NS(pool_members=lambda check, profile: [('Noun', 'CVC', 'C2'), ('Noun', 'CVCVC', 'C3')],
              program=NS(params=NS(ftype=lambda: 'lc')), analang='en')
    status = Status(task)
    program = NS(status=status, params=NS(cvt=lambda: 'C', check=lambda: 'C2'),
                 slices=NS(ps=lambda: 'Noun', profile=lambda: 'CVC',
                           senses=lambda ps, profile: bys[(ps, profile)]))
    s = NS(program=program)
    s.categorizebygrouping = lambda fn, sense, **kw: Settings.categorizebygrouping(s, fn, sense, **kw)
    s.storesettingsfile = lambda **kw: None
    Settings.updatesortingstatus(s)
    assert status.tosort_list == [b, c]
    assert status.sorted_list == ['a']
    assert status.written == {('Noun', 'CVC', 'C2'): ['t'], ('Noun', 'CVCVC', 'C3'): []}


def test_examples_and_counts_come_from_the_whole_pool():
    from backend.core.analysis import ExampleDict
    a, b = Sense('a', 'CVC', {}), Sense('b', 'CVCVC', {})
    a.ftypes, b.ftypes = {'lc': 'form-a'}, {'lc': 'form-b'}
    pooled = {'t': [a, b]}
    task = NS(pool_senses_in_group=lambda g, c, p=None: pooled.get(g, []),
              pooled_location=lambda c, p=None: 'C#')
    ex = NS(program=NS(task=task, params=NS(cvt=lambda: 'C', check=lambda: 'C2',
                                            ftype=lambda: 'lc')))
    ex._pooled_senses = lambda g, c, p=None: ExampleDict._pooled_senses(ex, g, c, p)
    assert ExampleDict.getexamples(ex, 't') == ['form-a', 'form-b']
    assert ExampleDict.sensesinslicegroup(ex, 't', 'C2') == [a, b]
    assert ExampleDict.prefetch_examples(ex, ['t']) is None      # no slice prefetch when pooled


def test_not_pooled_examples_take_the_slice_path():
    from backend.core.analysis import ExampleDict
    task = NS(pool_senses_in_group=lambda g, c, p=None: None)
    ex = NS(program=NS(task=task))
    assert ExampleDict._pooled_senses(ex, 't', 'C2') is None


def test_verifying_a_pooled_group_codes_each_word_under_its_own_check_and_profile():
    a, b = Sense('a', 'CVC', {}), Sense('b', 'CVCVC', {})
    slots = {'a': ('C2', 'CVC'), 'b': ('C3', 'CVCVC')}
    calls = []
    s = NS(program=NS(params=NS(check=lambda: 'C2', ftype=lambda: 'lc'),
                      status=NS(group=lambda: 't'), slices=NS(profile=lambda: 'CVC')),
           pool_senses_in_group=lambda group, check, profile: [a, b],
           word_slot=lambda sense, check, profile: slots[sense.id],
           verificationcode=lambda check, group: check + '=' + group,
           modverification=lambda sense, p, c, add: calls.append((sense.id, p, c, add)),
           maybewrite=lambda: None)
    Sort.updatestatuslift(s, verified=True, group='t')
    assert calls == [('a', 'CVC', 'C2', 'C2=t'), ('b', 'CVCVC', 'C3', 'C3=t')]
    calls.clear()
    Sort.updatestatuslift(s, verified=False, group='t')
    assert calls == [('a', 'CVC', 'C2', None), ('b', 'CVCVC', 'C3', None)]
