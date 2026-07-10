# coding=UTF-8
"""Segments.build_form_from_verified: the authoritative whole-word rebuild.

Regression anchor: 2026-07-10, real data — 'bush dweller' had verified
segments C1=b, C2=sh, and V1 verified into a group whose NAME was still the
digit placeholder '1' (not yet named; was last called 'ʊ'). The build path
concatenated the placeholder into the citation form: 'bʊsh' → 'b1sh'. Every
patch path guards unnamed groups (updateformtoannotations single-check and
do_not_do_these; _conform_form_to_profile INSERT); the build path must too:
verification stands, but the form must not update until the group is named.
"""
import pytest

pytest.importorskip("lxml")  # lexicon.py -> io_put.lift -> lxml
from types import SimpleNamespace
from backend.core.lexicon import Segments


class _FakeSense:
    """Only what build_form_from_verified touches."""
    id = "test-sense"

    def __init__(self, profile, actualkeys, done=True):
        self._profile, self._keys, self._done = profile, actualkeys, done

    def cvverificationdone(self, ftype):
        return self._done

    def cvprofilevalue(self, ftype):
        return self._profile

    def getcvverificationkeys(self, ftype):
        counts = {c: self._profile.count(c) for c in self._profile}
        return counts, self._keys


def build(sense):
    # unbound call with a minimal self: the method only reads self.ftype
    return Segments.build_form_from_verified(
        SimpleNamespace(ftype="lc"), sense)


def test_builds_from_fully_named_verified_segments():
    sense = _FakeSense("CVC", {"C1": "b", "V1": "ʊ", "C2": "sh"})
    assert build(sense) == "bʊsh"


def test_unnamed_digit_group_defers_build():
    # THE regression: V1 verified into placeholder group '1' must not
    # produce 'b1sh' — return None so the word falls to the stopgap.
    sense = _FakeSense("CVC", {"C1": "b", "V1": "1", "C2": "sh"})
    assert build(sense) is None


def test_na_group_defers_build():
    sense = _FakeSense("CVC", {"C1": "b", "V1": "NA", "C2": "sh"})
    assert build(sense) is None


def test_missing_slot_returns_none():
    sense = _FakeSense("CVC", {"C1": "b", "C2": "sh"})  # no V1 at all
    assert build(sense) is None


def test_not_fully_verified_returns_none():
    sense = _FakeSense("CVC", {"C1": "b", "V1": "ʊ", "C2": "sh"}, done=False)
    assert build(sense) is None
