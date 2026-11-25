# coding=UTF-8
"""Sorting LOCATIONS from CV profiles, both ways, to try on real data (Kent, 2026-11-25).

Draft of the cross-profile segmental sort (agenda: cross_profile_segmental_sort.md).

Profiles are first reduced to plain C and V: every consonant type (N G S D ʔ) is C, Ṽ is V, and marks
(length, tone, '=', '<', '.') are dropped — so CVN counts with CVC here (tone keeps the difference; this is
only for segments). Each segment of the reduced profile then gets ONE location, the check that sorts it:
- a word's first segment: '#C' / '#V'; its last: 'C#' / 'V#'; a one-segment word ('V'): '#V';
- any other segment: its ordinal (Cn = the nth C, as the current checks count) and the word's beginning
  through it, with runs of the OTHER type collapsed to one ('CCV' → 'CV' for a vowel). When that beginning
  simply alternates, it is named by its first segment: V2#C = 2nd vowel of a C-initial word (CVCV_,
  CVCCV_, CCVCV_ …); C1#V = 1st C of a V-initial word (VC_, VVC_). Otherwise the beginning is spelled out:
  'V2 CVV_' (two vowels in a row), 'C3 CVCC_' (2nd C of a cluster).
`report(counts)` gives the log lines: profiles → locations, locations → profiles, and a coverage summary
(locations needed for the top profiles; the other profiles those don't fully cover). Pure: no program, no
frontend; `log_report(profilesbysense, ...)` is the load-time entry point.
"""
import re
from utilities import logsetup

log = logsetup.getlog(__name__)

CONSONANTS = ('C', 'N', 'G', 'S', 'D', 'ʔ')
VOWELS = ('V', 'Ṽ')
MARKS = ('̃', 'ː', '̀', '=', '<', '.')     # the rest of ProfileAnalyzer.profilelegit


def reduce(profile):
    """The profile as plain C and V; None if it has a character outside the profile alphabet."""
    out = ''
    for ch in profile:
        if ch in CONSONANTS:
            out += 'C'
        elif ch in VOWELS:
            out += 'V'
        elif ch not in MARKS:
            return None
    return out or None


def _alternates(s):
    return all(a != b for a, b in zip(s, s[1:]))


def locations(profile):
    """[(segment index, location)] for each segment of the reduced profile; None if it isn't one."""
    p = reduce(profile)
    if p is None:
        return None
    last = len(p) - 1
    seen = {'C': 0, 'V': 0}
    out = []
    for i, seg in enumerate(p):
        seen[seg] += 1
        if i == 0:
            loc = '#' + seg
        elif i == last:
            loc = seg + '#'
        else:
            other = 'V' if seg == 'C' else 'C'
            begin = re.sub(other + '+', other, p[:i + 1])
            if _alternates(begin):
                loc = '{}{}#{}'.format(seg, seen[seg], begin[0])
            else:
                loc = '{}{} {}_'.format(seg, seen[seg], begin)
        out.append((i, loc))
    return out


SINGLE_CHECK = re.compile(r'^([CV])(\d+)$')


def segment_index(profile, check):
    """Where check 'Cn'/'Vn' falls in `profile`: the index of its nth LITERAL C/V (as the current
    checks count them; N, G, … are not C here), which is also its index in the reduced profile. None if
    the check isn't a single-segment check, or the profile hasn't that many."""
    m = SINGLE_CHECK.match(check or '')
    if not m:
        return None
    seg, n = m.group(1), int(m.group(2))
    i = -1
    for ch in profile:
        if ch in CONSONANTS or ch in VOWELS:
            i += 1
            if ch == seg:
                n -= 1
                if not n:
                    return i
        elif ch not in MARKS:
            return None
    return None


def check_location(profile, check):
    """The location a profile's check sorts (C2 of CVC → 'C#'); None if it has none."""
    i = segment_index(profile, check)
    if i is None:
        return None
    return dict(locations(profile) or ()).get(i)


def checks_of(profile):
    """{check: location} for every single-segment check the profile has."""
    out, seen = {}, {'C': 0, 'V': 0}
    for ch in profile:
        if ch in ('C', 'V'):
            seen[ch] += 1
            check = '{}{}'.format(ch, seen[ch])
            loc = check_location(profile, check)
            if loc:
                out[check] = loc
    return out


def members(location, profiles):
    """[(profile, check)] that a pooled `location` reads and writes, over `profiles`."""
    return [(p, c) for p in profiles for c, loc in checks_of(p).items() if loc == location]


def parse_code(code):
    """'C2=x' → ('C2', 'x'); None for anything but a single-segment check's code (V1=V2=x, …)."""
    check, sep, group = (code or '').rpartition('=')
    if sep and group and SINGLE_CHECK.match(check):
        return check, group
    return None


def sync_location_codes(profile, codes, pooled=()):
    """`codes` (a profile's verification list) with its LOCATION codes kept true. A location code sits
    beside a check's code ('C2=t' + 'C#=t' in CVC's list) when that check was verified POOLED — with the
    whole location, across profiles — so the field shows what was verified in what context (Kent,
    2026-11-25). Verifying one profile alone writes the check code only.
    - pooled: the checks just verified pooled; each gets its location code (for its current group).
    - Any location code whose check code is gone or now names another group is dropped, so unsorting
      or re-sorting a check (in either mode) takes its pooled verification with it.
    Location names are never check names ('#C', 'V1#C', 'C2 CC_'), so readers that look for an exact
    '<check>=' part are unaffected. Verification only: annotations stay keyed by check name."""
    locs = checks_of(profile)
    if not locs:
        return list(codes)
    groups = dict(filter(None, map(parse_code, codes)))        # check → group
    by_loc = {loc: check for check, loc in locs.items()}
    out = []
    for code in codes:
        name, _sep, group = code.rpartition('=')
        if name in by_loc and groups.get(by_loc[name]) != group:
            continue                                           # its check moved on
        out.append(code)
    for check in pooled:
        if check in locs and check in groups:
            loc_code = '{}={}'.format(locs[check], groups[check])
            if loc_code not in out:
                out.append(loc_code)
    return out


def carry(current, fields, annotations):
    """What to change when a word's profile is now `current`, so a check whose LOCATION didn't change
    keeps its verification (Kent, 2026-11-25: C1 of CV → CVC keeps C1; → VCV, rechecked from scratch).

    fields: {profile: [verification codes]} — the word's segmental verification fields; annotations:
    {check: group} — its group annotations. A code under an older profile counts only while the
    annotation still holds it (it is the word's current group). Returns (codes to add under `current`,
    {check: group} annotations to set, [checks] whose annotations to clear — groups sorted at a location
    the check no longer has). Codes under the old profiles stay: they are true for that profile."""
    verified = {}
    for code in fields.get(current, ()):
        parsed = parse_code(code)
        if parsed:
            verified[parsed[0]] = parsed[1]
    evidence = {}   # location → {group}, from older profiles' codes the annotations still hold
    stale = set()   # checks whose annotated group was sorted at another location
    pooled = set()  # (location, group) verified pooled under an older profile: stays pooled
    mine = checks_of(current)
    for profile, codes in fields.items():
        if profile == current:
            continue
        pooled.update(tuple(c.rpartition('=')[::2]) for c in codes
                      if c.rpartition('=')[0] in checks_of(profile).values())
        for code in codes:
            parsed = parse_code(code)
            if not parsed or annotations.get(parsed[0]) != parsed[1]:
                continue
            loc = check_location(profile, parsed[0])
            if loc:
                evidence.setdefault(loc, set()).add(parsed[1])
            if loc != mine.get(parsed[0]):
                stale.add(parsed[0])
    add, set_ann = [], {}
    for check, loc in mine.items():
        groups = evidence.get(loc, set())
        if check in verified or len(groups) != 1:
            continue
        group = next(iter(groups))
        add.append('{}={}'.format(check, group))
        if (loc, group) in pooled:
            add.append('{}={}'.format(loc, group))
        set_ann[check] = group
    clear = sorted(c for c in stale if c not in verified and c not in set_ann)
    return add, set_ann, clear


def reduce_counts(counts):
    """counts {profile: items} → ({reduced profile: items}, {reduced: [profiles merged into it]},
    [profiles that aren't profiles])."""
    reduced, merged, bad = {}, {}, []
    for profile, n in counts.items():
        r = reduce(profile)
        if r is None:
            bad.append(profile)
            continue
        reduced[r] = reduced.get(r, 0) + n
        merged.setdefault(r, []).append(profile)
    return reduced, merged, bad


def correspondence(counts):
    """counts {profile: items} → (by_profile {reduced profile: [locations]}, by_location {location:
    {reduced profile: items}}, bad [profiles that aren't profiles])."""
    reduced, _merged, bad = reduce_counts(counts)
    by_profile, by_location = {}, {}
    for profile, n in reduced.items():
        by_profile[profile] = [loc for _i, loc in locations(profile)]
        for loc in by_profile[profile]:
            by_location.setdefault(loc, {})[profile] = n
    return by_profile, by_location, bad


def _by_items(counts, profiles):
    return sorted(profiles, key=lambda p: (-counts[p], len(p), p))


def coverage(counts, top=5):
    """(top reduced profiles, the locations they need, [(profile, missing locations)] for every other
    profile those locations don't fully cover), most items first."""
    reduced, _merged, _bad = reduce_counts(counts)
    by_profile, _by_loc, _bad = correspondence(counts)
    tops = _by_items(reduced, by_profile)[:top]
    needed = []
    for p in tops:
        needed += [loc for loc in by_profile[p] if loc not in needed]
    uncovered = [(p, [loc for loc in by_profile[p] if loc not in needed])
                 for p in _by_items(reduced, by_profile) if p not in tops]
    return tops, needed, [(p, miss) for p, miss in uncovered if miss]


def report(counts, top=5):
    """The log text, as a list of lines."""
    reduced, merged, bad = reduce_counts(counts)
    by_profile, by_location, _bad = correspondence(counts)
    total = sum(reduced.values())
    lines = ["LOCATIONS: {} profiles ({} as plain C/V), {} items".format(
                len(counts) - len(bad), len(reduced), total),
             "Profiles → locations (items):"]
    for p in _by_items(reduced, by_profile):
        lines.append("  {} ({}): {}".format(p, reduced[p], ', '.join(by_profile[p])))
    lines.append("Locations → profiles (items):")
    for loc in sorted(by_location, key=lambda l: (-sum(by_location[l].values()), l)):
        profs = by_location[loc]
        lines.append("  {} [{}]: {}".format(loc, sum(profs.values()), ' '.join(
            '{}({})'.format(p, profs[p]) for p in _by_items(profs, profs))))
    folded = {r: ps for r, ps in merged.items() if ps != [r]}
    if folded:
        lines.append("Reduced to plain C/V:")
        for r in _by_items(reduced, folded):
            lines.append("  {} ← {}".format(r, ' '.join(
                '{}({})'.format(p, counts[p]) for p in _by_items(counts, folded[r]))))
    if bad:
        lines.append("Not profiles (left out): " + ' '.join(
            '{}({})'.format(p, counts[p]) for p in sorted(bad)))
    tops, needed, uncovered = coverage(counts, top)
    lines.append("SUMMARY: the top {} profiles: {}".format(len(tops), ' '.join(
        '{}({})'.format(p, reduced[p]) for p in tops)))
    lines.append("  need {} locations: {}".format(len(needed), ', '.join(needed)))
    covered = total - sum(reduced[p] for p, _m in uncovered)
    lines.append("  these cover {} of {} items completely".format(covered, total))
    lines.append("  profiles NOT completely covered ({}, {} items):".format(
        len(uncovered), total - covered))
    for p, miss in uncovered:
        lines.append("    {} ({}): also needs {}".format(p, reduced[p], ', '.join(miss)))
    return lines


def counts_from(profilesbysense, skip=()):
    """{profile: items}, pooled over ps (segments aren't sliced by ps by default). profilesbysense is
    {ps: {profile: [senses]}} (+ 'analang'/'ftype'); `skip` = {ps: names} not to count (ad hoc groups)."""
    counts = {}
    for ps, profiles in profilesbysense.items():
        if not isinstance(profiles, dict):
            continue
        for profile, senses in profiles.items():
            if profile in skip.get(ps, ()):
                continue
            try:
                n = len(set(senses))
            except TypeError:
                n = len(senses)
            counts[profile] = counts.get(profile, 0) + n
    return counts


def log_report(profilesbysense, adhoc=None, top=10):
    """Write the report to the log. Never raises: this is diagnostics."""
    try:
        counts = counts_from(profilesbysense, adhoc or {})
        if counts:
            log.info('\n'.join(report(counts, top)))
    except Exception as e:
        log.info("locations report failed: %s", e)
