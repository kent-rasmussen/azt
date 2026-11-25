# coding=UTF-8
"""Status for a POOL: one location (locations.py: '#C', 'C#', 'V2#C', …) sorted across profiles — and
across ps when ps is 'All' — as one (Kent, 2026-11-25; agenda cross_profile_segmental_sort.md, stage 2).

Nothing new is stored. Status stays keyed ps → profile → check, as now; a pool is the set of those
nodes whose check sorts its location (locations.members), and this module reads and writes across them:
- groups: the union of the members' groups;
- done (verified): a group is verified when every member that has it has it verified;
- distinguished: a pair holds when every member that has BOTH groups has distinguished them (a member
  without one of them has no say); a pair never judged anywhere is not distinguished;
- tosort / tojoin: any member; presorted: every member;
- writes go to every member, so going back to single profiles still sees them.

First pooling (`plan_pooling`): integer group names mean nothing across profiles (CV:#C=1 is not
CVC:#C=1), so a member joining a pool for the first time has its integers that collide renamed apart,
once; users then join them or not, as usual. A NAMED group found in more than one member was verified
apart, so it is unverified (heard once, pooled) — which also undoes per-profile macrosorting, as
macrosort takes only verified groups. Members are marked ('pooled') so this runs once each.
Pure: works on the status dict's nodes; the caller applies renames to LIFT and status.
"""
import itertools
from backend.core import locations

ALL = 'All'        # the ps setting's value for "all ps sort together"
MARK = 'pooled'    # node key: this member's groups have been reconciled into its pool


def members(status, cvt, location, ps=ALL):
    """[(ps, profile, check)] whose status nodes make up the pool."""
    out = []
    tree = status.get(cvt) or {}
    for p in sorted(tree) if ps == ALL else [ps]:
        profiles = tree.get(p) or {}
        for profile, check in locations.members(location, sorted(profiles)):
            if check in (profiles.get(profile) or {}):
                out.append((p, profile, check))
    return out


def _groups(node):
    return list(node.get('groups') or [])


def groups(nodes):
    out = []
    for n in nodes:
        out += [g for g in _groups(n) if g not in out]
    return out


def done(nodes):
    have = [n for n in nodes if _groups(n)]
    return [g for g in groups(nodes)
            if all(g in (n.get('done') or []) for n in have if g in _groups(n))]


def _pair_in(pair, node):
    d = node.get('distinguished') or ()
    return tuple(pair) in d or tuple(reversed(pair)) in d


def is_distinguished(pair, nodes):
    judges = [n for n in nodes if all(g in _groups(n) for g in pair)]
    return bool(judges) and all(_pair_in(pair, n) for n in judges)


def distinguished(nodes):
    pairs = set()
    for n in nodes:
        pairs.update(tuple(p) for p in (n.get('distinguished') or ()))
    return {p for p in pairs if is_distinguished(p, nodes)}


def pending_distinctions(nodes):
    """Verified pool-group pairs not yet distinguished (as StatusDict.pending_distinctions)."""
    v = [g for g in done(nodes) if g != 'NA']
    return {p for p in itertools.combinations(v, 2) if not is_distinguished(p, nodes)}


def tosort(nodes):
    return any(n.get('tosort') for n in nodes)


def tojoin(nodes):
    return any(n.get('tojoin', True) for n in nodes)


def presorted(nodes):
    return bool(nodes) and all(n.get('presorted') for n in nodes)


def distinguish(pair, nodes):
    for n in nodes:
        n.setdefault('distinguished', set())
        if not isinstance(n['distinguished'], set):
            n['distinguished'] = set(tuple(p) for p in n['distinguished'])
        n['distinguished'].add(tuple(pair))


def undistinguish_any_with(group, nodes):
    for n in nodes:
        d = n.get('distinguished')
        if d:
            n['distinguished'] = {p for p in d if group not in p}


def set_done(group, verified, nodes):
    """Verify/unverify a pool group in every member that has it. Unverifying voids its distinctions,
    as StatusDict.update does (a distinction dies with the verification it was made under)."""
    for n in nodes:
        if group not in _groups(n):
            continue
        d = n.setdefault('done', [])
        if verified and group not in d:
            d.append(group)
        elif not verified and group in d:
            d.remove(group)
    if not verified:
        undistinguish_any_with(group, nodes)


class _Done(list):
    """The pool's verified groups; append/remove go to the members (append: those that have the group,
    else the page's own node)."""
    def __init__(self, pool):
        super().__init__(done(pool.nodes))
        self._pool = pool

    def append(self, g):
        if g not in self:
            super().append(g)
        have = [n for n in self._pool.nodes if g in _groups(n)] or [self._pool.home]
        for n in have:
            d = n.setdefault('done', [])
            if g not in d:
                d.append(g)

    def remove(self, g):
        if g in self:
            super().remove(g)
        for n in self._pool.nodes:
            if g in (n.get('done') or []):
                n['done'].remove(g)


class _Distinguished(set):
    """The pool's distinguished pairs (pools.distinguished); membership by is_distinguished (either
    order); add/discard/remove go to every member."""
    def __init__(self, pool):
        super().__init__(distinguished(pool.nodes))
        self._pool = pool

    def __contains__(self, pair):
        return is_distinguished(tuple(pair), self._pool.nodes)

    def add(self, pair):
        super().add(tuple(pair))
        distinguish(pair, self._pool.nodes)

    def discard(self, pair):
        super().discard(tuple(pair))
        for n in self._pool.nodes:
            d = n.get('distinguished')
            if d:
                d.discard(tuple(pair))

    def remove(self, pair):
        self.discard(pair)


class PoolNode(dict):
    """Stands in for ONE status node (StatusDict.node) while sorting pooled: reads across the members,
    writes to them. `home` is the page's own node (a member, or the node new things go to)."""
    AGGREGATE = {'tosort': tosort, 'tojoin': tojoin, 'presorted': presorted}

    def __init__(self, nodes, home):
        super().__init__()
        self.nodes = list(nodes)
        self.home = home
        if not any(n is home for n in self.nodes):
            self.nodes.append(home)

    def __getitem__(self, key):
        if key == 'groups':
            return groups(self.nodes)
        if key == 'done':
            return _Done(self)
        if key == 'distinguished':
            return _Distinguished(self)
        if key in self.AGGREGATE:
            return self.AGGREGATE[key](self.nodes)
        if key == 'recorded':
            out = []
            for n in self.nodes:
                out += [g for g in (n.get('recorded') or []) if g not in out]
            return out
        return self.home[key]

    def __setitem__(self, key, value):
        if key == 'groups':
            value = list(value)
            for n in self.nodes:
                n['groups'] = [g for g in _groups(n) if g in value]
            known = groups(self.nodes)
            self.home['groups'] = _groups(self.home) + [g for g in value if g not in known]
        elif key == 'done':
            value = list(value)
            for n in self.nodes:
                n['done'] = [g for g in value if g in _groups(n)]
        elif key == 'distinguished':
            for n in self.nodes:
                n['distinguished'] = set(tuple(p) for p in value)
        elif key in self.AGGREGATE:
            for n in self.nodes:
                n[key] = value
        else:
            self.home[key] = value

    def __contains__(self, key):
        return any(key in n for n in self.nodes)

    def get(self, key, default=None):
        return self[key] if key in self else default

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]


def plan_pooling(member_nodes):
    """member_nodes: [(member, node)] in a stable order. Returns (renames {member: {old: new}},
    unverify {group: [members]}, to_mark [members]) for the members not yet reconciled."""
    marked = [(m, n) for m, n in member_nodes if n.get(MARK)]
    fresh = [(m, n) for m, n in member_nodes if not n.get(MARK)]
    if not fresh:
        return {}, {}, []
    ints = {int(g) for _m, n in member_nodes for g in _groups(n) if g.isdigit()}
    taken = {int(g) for _m, n in marked for g in _groups(n) if g.isdigit()}
    nxt = max(ints, default=0) + 1
    renames = {}
    for m, n in fresh:
        for g in _groups(n):
            if not g.isdigit():
                continue
            if int(g) in taken:
                renames.setdefault(m, {})[g] = str(nxt)
                taken.add(nxt)
                nxt += 1
            else:
                taken.add(int(g))
    unverify = {}
    for g in groups([n for _m, n in member_nodes]):
        if g.isdigit() or g == 'NA':
            continue
        have = [m for m, n in member_nodes if g in _groups(n)]
        if len(have) > 1 and any(g in _groups(n) for _m, n in fresh):
            unverify[g] = have
    return renames, unverify, [m for m, _n in fresh]
