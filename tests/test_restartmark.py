"""The restart breadcrumb (added in v1.15.x).

Level 1 of `azt/agenda/restart_recovery_handshake.md`. AZT restarts itself, and
until now a restart that never came back produced no evidence at all — the
2026-07-29 field report had no log line, because `os.execl` leaves no process to
write one. This marker is the evidence, so its two invariants are tested rather
than trusted:

  1. `report()` does NOT clear. Clearing at startup would destroy the marker in
     exactly the case worth reporting — a successor that dies during its own
     boot — and leave the next start with nothing.
  2. Nothing here may raise. A corrupt or unwritable marker must cost a log
     line, never a restart or a startup.
"""
import json

import pytest

restartmark = pytest.importorskip("utilities.restartmark")


@pytest.fixture
def logdir(tmp_path, monkeypatch):
    """Point the marker at a temp dir by faking utilities.file.getlogdir."""
    import utilities.file as _file
    monkeypatch.setattr(_file, "getlogdir", lambda: tmp_path, raising=False)
    return tmp_path


def test_round_trip(logdir):
    restartmark.mark(reason="update")
    data = restartmark.pending()
    assert data["reason"] == "update"
    assert data["pid"] and data["started"] and data["argv"]


def test_no_marker_reads_as_none(logdir, monkeypatch):
    monkeypatch.setattr(restartmark.sys, "argv", ["main.py"])
    assert restartmark.pending() is None
    assert restartmark.report() is None


@pytest.fixture
def by_hand(monkeypatch):
    """A copy the USER started: no --restart in argv."""
    monkeypatch.setattr(restartmark.sys, "argv", ["main.py"])
    monkeypatch.delenv("AZT_VENV_RELAUNCHED", raising=False)


def test_a_venv_relaunch_is_also_a_handover(monkeypatch):
    """py_modules.ensure_venv relaunches with sys.argv UNCHANGED — no --restart —
    so keying only on that flag would report every good venv relaunch as a
    restart that never landed. AZT_BOOTSTRAP_PARENT_PID would be more precise
    but duplicates.running_file pops it long before this is asked."""
    monkeypatch.setattr(restartmark.sys, "argv", ["main.py"])
    monkeypatch.setenv("AZT_VENV_RELAUNCHED", "1")
    assert restartmark.launched_by_restart() is True


@pytest.fixture
def by_restart(monkeypatch):
    """A copy a restart launched."""
    monkeypatch.setattr(restartmark.sys, "argv", ["main.py", "--restart"])


def test_report_does_not_clear(logdir, by_hand):
    """THE INVARIANT. If this boot also fails, the next one must still find it."""
    restartmark.mark(reason="update")
    assert restartmark.report() is not None
    assert restartmark.pending() is not None, "report() cleared the evidence"


def test_successor_does_not_cry_wolf(logdir, by_restart):
    """THE FALSE POSITIVE, from Kent's log 2026-09-01. The predecessor wrote the
    marker moments ago and only a UI that comes up clears it, so a marker is
    ALWAYS present in the successor. Warning there fires on every successful
    restart, which would teach the reader to ignore the one that matters."""
    restartmark.mark(reason="update")
    assert restartmark.report() is None
    assert restartmark.pending() is not None, "still must not clear it"


def test_hand_launch_with_a_marker_is_the_reportable_case(logdir, by_hand):
    """The field symptom: the restart chain died, so the user started it
    themselves — and a marker is still outstanding."""
    restartmark.mark(reason="update")
    assert restartmark.report()["reason"] == "update"


def test_clear_removes_it(logdir):
    restartmark.mark(reason="update")
    restartmark.clear()
    assert restartmark.pending() is None


def test_clear_is_safe_with_no_marker(logdir):
    restartmark.clear()  # must not raise
    restartmark.clear()


def test_corrupt_marker_still_reports_and_never_raises(logdir, monkeypatch):
    """A half-written marker is itself a symptom — treat it as present rather
    than swallowing it, and above all don't stop the app from starting."""
    monkeypatch.setattr(restartmark.sys, "argv", ["main.py"])
    (logdir / restartmark.MARKER).write_text("{not json", encoding="utf-8")
    data = restartmark.pending()
    assert data is not None
    assert "unreadable" in data["reason"]
    restartmark.report()


def test_mark_survives_an_unwritable_location(tmp_path, monkeypatch):
    """A diagnostic must never block a restart."""
    import utilities.file as _file
    monkeypatch.setattr(_file, "getlogdir",
                        lambda: tmp_path / "does" / "not" / "exist",
                        raising=False)
    restartmark.mark(reason="update")  # must not raise
    assert restartmark.pending() is None
