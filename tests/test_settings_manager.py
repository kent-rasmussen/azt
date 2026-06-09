"""Unit tests for settings/manager.py — JSON config round-trip + encoder.

These cover the persistence contract that the whole settings rebuild relies on:
sets and Paths survive a save/load cycle, and ConfigManager reads back what it
wrote. They also pin the documented (if surprising) behavior that assigning an
attribute persists immediately — so a future change to that has to be deliberate.
"""
import json

import pytest

from settings.manager import (
    ConfigManager,
    CustomEncoder,
    custom_object_hook,
    make_hashable,
)


def test_make_hashable_converts_nested_lists_to_tuples():
    assert make_hashable([1, [2, 3], [4, [5]]]) == (1, (2, 3), (4, (5,)))


def test_make_hashable_leaves_non_lists_alone():
    assert make_hashable("x") == "x"
    assert make_hashable(7) == 7


def test_set_round_trips_through_json():
    data = {"glosses": {"a", "b", "c"}}
    encoded = json.dumps(data, cls=CustomEncoder)
    decoded = json.loads(encoded, object_hook=custom_object_hook)
    assert decoded == {"glosses": {"a", "b", "c"}}


def test_path_encodes_to_string():
    from pathlib import Path
    encoded = json.dumps({"p": Path("/tmp/x")}, cls=CustomEncoder)
    assert json.loads(encoded) == {"p": "/tmp/x"}


def test_configmanager_save_load_round_trip(tmp_path):
    base = tmp_path / "proj"
    cm = ConfigManager("data", base)
    cm.set("words", [1, 2, 3])
    # a fresh manager pointed at the same base reads the saved file
    cm2 = ConfigManager("data", base)
    cm2.load()
    assert cm2.get("words") == [1, 2, 3]


def test_configmanager_set_persists_python_set(tmp_path):
    base = tmp_path / "proj"
    cm = ConfigManager("data", base)
    cm.set("checks", {"C1", "C2"})
    cm2 = ConfigManager("data", base)
    cm2.load()
    assert cm2.get("checks") == {"C1", "C2"}


def test_configmanager_get_default(tmp_path):
    cm = ConfigManager("data", tmp_path / "proj")
    assert cm.get("missing", "fallback") == "fallback"


def test_setattr_routes_to_data_and_persists(tmp_path):
    """Documented behavior: assigning a non-reserved attr writes to JSON."""
    base = tmp_path / "proj"
    cm = ConfigManager("data", base)
    cm.somekey = "value"
    assert cm.filename.exists()  # the write happened on assignment
    cm2 = ConfigManager("data", base)
    cm2.load()
    assert cm2.get("somekey") == "value"


def test_per_host_domains_use_host_user_in_filename(tmp_path):
    base = tmp_path / "proj"
    project = ConfigManager("project", base, hostname="HOST", user="USER")
    data = ConfigManager("data", base, hostname="HOST", user="USER")
    # 'project' is host/user-scoped; 'data' is not
    assert project.filename.name == "proj.USER.HOST.project.json"
    assert data.filename.name == "proj.data.json"


# ── write-amplification fix: coalescing + batch() (v1.2.x) ───────────────

def test_save_skips_write_when_content_unchanged(tmp_path):
    cm = ConfigManager("data", tmp_path / "proj")
    cm.set("a", 1)
    assert cm._writes == 1
    cm.save()              # identical content -> coalesced away
    assert cm._writes == 1
    cm.set("a", 2)         # changed -> writes
    assert cm._writes == 2


def test_batch_defers_writes_until_exit(tmp_path):
    base = tmp_path / "proj"
    cm = ConfigManager("data", base)
    with cm.batch():
        cm.set("a", 1)
        assert cm._writes == 0          # nothing on disk yet
        assert not cm.filename.exists()
    assert cm._writes == 1              # one write on exit
    reread = ConfigManager("data", base)
    reread.load()
    assert reread.get("a") == 1


def test_batch_coalesces_many_sets_to_one_write(tmp_path):
    cm = ConfigManager("data", tmp_path / "proj")
    with cm.batch():
        cm.set("a", 1)
        cm.set("b", 2)
        cm.set("c", 3)
    assert cm._writes == 1
    assert (cm.get("a"), cm.get("b"), cm.get("c")) == (1, 2, 3)


def test_batch_defers_attribute_assignment_too(tmp_path):
    base = tmp_path / "proj"
    cm = ConfigManager("data", base)
    with cm.batch():
        cm.foo = "bar"                  # routes to data via __setattr__
        assert cm._writes == 0
    assert cm._writes == 1
    reread = ConfigManager("data", base)
    reread.load()
    assert reread.get("foo") == "bar"


def test_nested_batch_only_outer_flushes(tmp_path):
    cm = ConfigManager("data", tmp_path / "proj")
    with cm.batch():
        cm.set("a", 1)
        with cm.batch():
            cm.set("b", 2)
        assert cm._writes == 0          # inner batch must not flush
    assert cm._writes == 1


def test_empty_batch_writes_nothing(tmp_path):
    cm = ConfigManager("data", tmp_path / "proj")
    with cm.batch():
        pass
    assert cm._writes == 0
    assert not cm.filename.exists()


def test_settingsmanager_batch_propagates_to_domains(tmp_path):
    try:
        from settings import SettingsManager
    except Exception as e:  # heavy package import; skip if env can't load it
        pytest.skip(f"settings package import failed: {e}")
    mgr = SettingsManager(tmp_path / "proj")
    with mgr.batch():
        mgr.data.set("x", 1)
        mgr.data.set("y", 2)
    assert mgr.data._writes == 1
