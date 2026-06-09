"""Unit tests for backend/core/analysis.py StatusDict.

StatusDict is the in-memory model for "the status of each sense's sort/verify
state": a nested dict ``self[cvt][ps][profile][check]`` holding `groups`,
`done`, `recorded`, `tosort`, `distinguished`, etc. It's what the sort and
macrosort flows read and write. Most methods either take explicit
cvt/ps/profile/check kwargs or fall back to *current* values from
program.params / program.slices — so a tiny fake program is enough to exercise
the real logic headlessly (no LIFT file, no Tk, no full App).

These cover: structure creation, group get/set + rename, verified(done)
read/write incl. update(), tosort/presorted/tojoin flags, distinguish pairing
(macrosort), the sense to-sort/sorted bookkeeping, and cull/clear_all_groups.
"""
import pytest

pytest.importorskip("lxml")  # analysis.py -> io_put.lift -> lxml
from backend.core.analysis import StatusDict


# ── minimal fakes: only what StatusDict touches for "current" defaults ────

class _Params:
    def __init__(self, cvt="T", check="c1"):
        self._cvt, self._check = cvt, check

    def cvt(self):
        return self._cvt

    def check(self, c=None, unset=False):
        if unset:
            self._check = None
        elif c is not None:
            self._check = c
        return self._check


class _Slices:
    def __init__(self, ps="Noun", profile="CVC"):
        self._ps, self._profile = ps, profile

    def ps(self, p=None):
        if p is not None:
            self._ps = p
        return self._ps

    def profile(self, p=None):
        if p is not None:
            self._profile = p
        return self._profile


class _Program:
    pass


def make_status(initial=None):
    prog = _Program()
    prog.params = _Params()
    prog.slices = _Slices()
    sd = StatusDict("test-status", initial or {}, prog)  # sets prog.status = sd
    return sd, prog


KW = dict(cvt="T", ps="Noun", profile="CVC", check="c1")


# ── structure creation ───────────────────────────────────────────────────

def test_build_creates_nested_node_with_defaults():
    sd, _ = make_status()
    sd.build(**KW)
    node = sd["T"]["Noun"]["CVC"]["c1"]
    assert node["groups"] == []
    assert node["done"] == []
    assert node["recorded"] == []
    assert node["tosort"] is True
    assert node["presorted"] is False


def test_node_builds_on_demand():
    sd, _ = make_status()
    node = sd.node(**KW)  # node() builds if missing
    assert node is sd["T"]["Noun"]["CVC"]["c1"]


# ── groups: create / list / set / rename ─────────────────────────────────

def test_groups_empty_then_set_returns_sorted():
    sd, _ = make_status()
    assert sd.groups(wsorted=True, **KW) == []
    sd.groups(["2", "1", "3"], wsorted=True, **KW)
    assert sd.groups(wsorted=True, **KW) == ["1", "2", "3"]


def test_renamegroup_updates_groups_done_and_distinguished():
    sd, _ = make_status()
    sd.groups(["1", "2"], wsorted=True, **KW)
    sd.verified(["1"], **KW)
    sd.distinguish(("1", "2"), **KW)
    sd.renamegroup("1", "9", **KW)
    node = sd["T"]["Noun"]["CVC"]["c1"]
    assert "9" in node["groups"] and "1" not in node["groups"]
    assert node["done"] == ["9"]
    assert ("9", "2") in node["distinguished"]


# ── verified / done: read + write (the core "status of a sense") ─────────

def test_verified_get_and_set():
    sd, _ = make_status()
    sd.build(**KW)
    assert sd.verified(**KW) == []
    sd.verified(["1"], **KW)
    assert sd.verified(**KW) == ["1"]


def test_update_marks_and_unmarks_verified_and_reports_change():
    sd, _ = make_status()  # fake current slice = T/Noun/CVC/c1
    sd.group("1")
    assert sd.update(verified=True, writestatus=False) is True
    assert "1" in sd["T"]["Noun"]["CVC"]["c1"]["done"]
    # marking the same group verified again is a no-op (no double-add)
    assert sd.update(verified=True, writestatus=False) is False
    # unmarking removes it and reports the change
    assert sd.update(group="1", verified=False, writestatus=False) is True
    assert "1" not in sd["T"]["Noun"]["CVC"]["c1"]["done"]


# ── per-check flags ──────────────────────────────────────────────────────

def test_tosort_flag_get_set():
    sd, _ = make_status()
    sd.build(**KW)
    assert sd.tosort(**KW) is True
    assert sd.tosort(False, **KW) is False
    assert sd.tosort(**KW) is False


def test_presorted_and_tojoin_flags():
    sd, _ = make_status()
    sd.build(**KW)
    assert sd.presorted(True, **KW) is True
    assert sd.tojoin(False, **KW) is False


def test_checktosort_true_until_tosort_cleared():
    sd, _ = make_status()
    assert sd.checktosort(**KW) is True       # nothing built yet
    sd.build(**KW)
    assert sd.checktosort(**KW) is True        # tosort defaults True
    sd.tosort(False, **KW)
    assert not sd.checktosort(**KW)            # cleared -> falsy (None)


# ── distinguish pairing (used by macrosort / join) ──────────────────────

def test_distinguish_and_isdistinguished_are_orderless():
    sd, _ = make_status()
    sd.build(**KW)
    sd.distinguish(("1", "2"), **KW)
    assert sd.isdistinguished("2", group="1", **KW)
    assert sd.isdistinguished("1", group="2", **KW)  # reversed pair matches
    sd.undistinguish(("1", "2"), **KW)
    assert not sd.isdistinguished("2", group="1", **KW)


# ── sense to-sort / sorted bookkeeping ───────────────────────────────────

def test_marksensesorted_moves_sense_and_clears_tosort_when_empty():
    sd, _ = make_status()
    sd.build(**KW)
    sd.renewsensestosort(["a", "b"], [])      # todo, done (strings stand in for senses)
    assert sd.sensestosort() == ["a", "b"]
    sd.marksensesorted("a")
    assert "a" in sd.sensessorted() and "a" not in sd.sensestosort()
    sd.marksensesorted("b")                    # list now empty -> tosort(False)
    assert sd.sensestosort() == []
    assert sd.tosort(**KW) is False


def test_marksensetosort_sets_tosort_true():
    sd, _ = make_status()
    sd.build(**KW)
    sd.renewsensestosort([], ["a"])
    sd.marksensetosort("a")
    assert "a" in sd.sensestosort()
    assert sd.tosort(**KW) is True


# ── current-group pointer ────────────────────────────────────────────────

def test_group_pointer_get_set():
    sd, _ = make_status()
    assert sd.group() is None
    sd.group("5")
    assert sd.group() == "5"
    sd.group(None)                             # None can be set explicitly
    assert sd.group() is None


# ── housekeeping ─────────────────────────────────────────────────────────

def test_cull_removes_empty_group_nodes_all_the_way_up():
    sd, _ = make_status()
    sd.build(**KW)                             # groups == []
    sd.cull()
    assert "T" not in sd                        # whole empty branch removed


def test_clear_all_groups_empties_group_lists_only():
    sd, _ = make_status()
    sd.groups(["1", "2"], wsorted=True, **KW)
    sd.verified(["1"], **KW)
    sd.clear_all_groups()
    node = sd["T"]["Noun"]["CVC"]["c1"]
    assert node["groups"] == []
    assert node["done"] == ["1"]               # clear_all_groups leaves 'done' alone
