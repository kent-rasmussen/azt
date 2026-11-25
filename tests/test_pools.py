"""Pool status across profiles (backend/core/pools.py; Kent, 2026-11-25, stage 2)."""
from backend.core import pools as P


def node(groups, done=(), dist=(), **kw):
    n = {'groups': list(groups), 'done': list(done), 'distinguished': set(dist)}
    n.update(kw)
    return n


def test_members_are_the_nodes_whose_check_sorts_the_location():
    status = {'C': {'Noun': {'CVC': {'C2': {}, 'C1': {}}, 'CVCVC': {'C3': {}}, 'CV': {'C1': {}}},
                    'Verb': {'CVC': {'C2': {}}}}}
    assert P.members(status, 'C', 'C#') == [('Noun', 'CVC', 'C2'), ('Noun', 'CVCVC', 'C3'),
                                            ('Verb', 'CVC', 'C2')]
    assert P.members(status, 'C', 'C#', ps='Verb') == [('Verb', 'CVC', 'C2')]
    assert P.members(status, 'C', '#C') == [('Noun', 'CV', 'C1'), ('Noun', 'CVC', 'C1')]


def test_groups_are_the_union_and_done_needs_every_member_that_has_the_group():
    a = node(['p', 't'], done=['p', 't'])
    b = node(['p', 'k'], done=['k'])
    assert P.groups([a, b]) == ['p', 't', 'k']
    assert P.done([a, b]) == ['t', 'k']          # p is unverified in b


def test_a_pair_is_distinguished_only_where_every_member_with_both_agrees():
    a = node(['p', 't'], dist={('p', 't')})
    b = node(['p', 't'])                          # has both, never judged
    c = node(['p', 'k'], dist={('k', 'p')})       # has no t: no say on p/t
    assert not P.is_distinguished(('p', 't'), [a, b])
    assert P.is_distinguished(('p', 't'), [a, c])
    assert P.is_distinguished(('p', 'k'), [a, c])
    assert not P.is_distinguished(('t', 'k'), [a, c])   # never judged anywhere
    assert P.distinguished([a, c]) == {('p', 't'), ('k', 'p')}


def test_pending_distinctions_over_the_pool():
    a = node(['p', 't'], done=['p', 't'], dist={('p', 't')})
    c = node(['k'], done=['k'])
    assert P.pending_distinctions([a, c]) == {('p', 'k'), ('t', 'k')}


def test_flags():
    assert P.tosort([node([], tosort=False), node([], tosort=True)])
    assert not P.presorted([node([], presorted=True), node([], presorted=False)])


def test_writes_go_to_every_member():
    a, b = node(['p', 't'], done=['p', 't']), node(['p'], done=['p'])
    P.distinguish(('p', 't'), [a, b])
    assert ('p', 't') in a['distinguished'] and ('p', 't') in b['distinguished']
    P.set_done('p', False, [a, b])
    assert a['done'] == ['t'] and b['done'] == []
    assert not a['distinguished'] and not b['distinguished']   # void with the verification


def test_pool_node_reads_across_members():
    a = node(['p', 't'], done=['p', 't'], dist={('p', 't')}, tosort=False, presorted=True)
    b = node(['p', 'k'], done=['k'], tosort=True, presorted=True)
    pn = P.PoolNode([a, b], home=a)
    assert pn['groups'] == ['p', 't', 'k']
    assert list(pn['done']) == ['t', 'k']
    assert pn['tosort'] is True and pn['presorted'] is True
    assert ('t', 'p') in pn['distinguished'] and ('p', 'k') not in pn['distinguished']
    assert 'tojoin' not in pn and pn.get('tojoin', 'x') == 'x'


def test_pool_node_writes_to_members():
    a = node(['p', 't'], done=['t'])
    b = node(['p'], done=[])
    pn = P.PoolNode([a, b], home=a)
    pn['done'].append('p')                         # verify p: every member that has it
    assert 'p' in a['done'] and 'p' in b['done']
    pn['done'].remove('p')
    assert 'p' not in a['done'] and 'p' not in b['done']
    pn['distinguished'].add(('p', 't'))
    assert ('p', 't') in a['distinguished'] and ('p', 't') in b['distinguished']
    pn['distinguished'].discard(('p', 't'))
    assert not a['distinguished'] and not b['distinguished']
    pn['tosort'] = False
    assert a['tosort'] is False and b['tosort'] is False


def test_pool_node_new_groups_go_home_and_removed_ones_go_everywhere():
    a, b = node(['p', 't']), node(['p'])
    pn = P.PoolNode([a, b], home=b)
    pn['groups'] = ['p', 't', '5']                 # add_int_group: new '5' on the page's node
    assert b['groups'] == ['p', '5'] and a['groups'] == ['p', 't']
    pn['groups'] = ['t', '5']                      # p gone from every member
    assert a['groups'] == ['t'] and b['groups'] == ['5']


def test_first_pooling_renames_colliding_integers_once():
    cv, cvc = node(['1', '2', 'p']), node(['1', '3'])
    renames, unverify, mark = P.plan_pooling([('CV', cv), ('CVC', cvc)])
    assert renames == {'CVC': {'1': '4'}}
    assert unverify == {} and mark == ['CV', 'CVC']


def test_a_named_group_in_two_members_is_heard_again():
    cv, cvc = node(['p', '1'], done=['p']), node(['p'], done=['p'])
    _r, unverify, _m = P.plan_pooling([('CV', cv), ('CVC', cvc)])
    assert unverify == {'p': ['CV', 'CVC']}


def test_once_marked_nothing_is_renamed_again():
    cv, cvc = node(['1'], pooled=True), node(['1'], pooled=True)   # joined since: one group
    assert P.plan_pooling([('CV', cv), ('CVC', cvc)]) == ({}, {}, [])
    new = node(['1', 'p'])                                         # a member joining later
    renames, unverify, mark = P.plan_pooling([('CV', cv), ('CVC', cvc), ('CVCVC', new)])
    assert renames == {'CVCVC': {'1': '2'}} and mark == ['CVCVC']
