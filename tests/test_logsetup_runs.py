"""Per-run log naming, retention, and the dedupe filter (v1.15.x).

Kent's spec, 2026-09-02: "one log per run, not counting restarts for updates or
venv. then keep five of those, so we can see the last five runs." And, on the
size cap: he needs the BEGINNING of a run, not the tail — `_001` carries the
version banner, and a field log that has rotated its banner away cannot even be
attributed to a build. Both of those are invariants rather than preferences, so
they are tested.
"""
import logging

import pytest

logsetup = pytest.importorskip("utilities.logsetup")


@pytest.fixture
def logdir(tmp_path, monkeypatch):
    import utilities.file as _file
    monkeypatch.setattr(_file, "getlogdir", lambda: tmp_path, raising=False)
    monkeypatch.delenv(logsetup.RUN_ENV, raising=False)
    monkeypatch.delenv("AZT_VENV_RELAUNCHED", raising=False)
    return tmp_path


def _touch(d, runid, part, size=0):
    p = d / "log_{}_{:03d}.txt".format(runid, part)
    p.write_bytes(b"x" * size)
    return p


def test_a_hand_launch_mints_a_new_run(logdir, monkeypatch):
    monkeypatch.setattr(logsetup.sys, "argv", ["main.py"])
    first = logsetup._runid()
    monkeypatch.delenv(logsetup.RUN_ENV, raising=False)
    assert logsetup._runid() is not None
    assert first


def test_a_restart_continues_the_same_run(logdir, monkeypatch):
    """The whole point: an update or venv relaunch is not a new run."""
    monkeypatch.setenv(logsetup.RUN_ENV, "2026-09-02T120000")
    monkeypatch.setattr(logsetup.sys, "argv", ["main.py", "--restart"])
    assert logsetup._runid() == "2026-09-02T120000"


def test_a_hand_launch_ignores_an_inherited_run(logdir, monkeypatch):
    """A stale env var must not glue an unrelated launch onto an old run."""
    monkeypatch.setenv(logsetup.RUN_ENV, "2026-09-02T120000")
    monkeypatch.setattr(logsetup.sys, "argv", ["main.py"])
    assert logsetup._runid() != "2026-09-02T120000"


def test_parts_are_allocated_forward(logdir):
    _touch(logdir, "2026-09-02T120000", 1)
    _touch(logdir, "2026-09-02T120000", 2)
    assert logsetup._nextpart(logdir, "2026-09-02T120000") == 3


def test_sweep_keeps_five_whole_runs(logdir):
    for n in range(8):
        rid = "2026-09-02T1200{:02d}".format(n)
        _touch(logdir, rid, 1)
        _touch(logdir, rid, 2)
    logsetup.sweep(logdir, runid=None)
    left = {p.stem[len("log_"):].rsplit("_", 1)[0] for p in logdir.glob("log_*")}
    assert len(left) == logsetup.RUNS_KEPT
    assert "2026-09-02T120007" in left, "dropped the newest run"
    assert "2026-09-02T120000" not in left, "kept the oldest run"


def test_sweep_never_leaves_a_run_without_its_first_part(logdir):
    """THE INVARIANT. _001 has the version banner, so a run missing it is worse
    than no run at all — you cannot tell which build produced it."""
    for n in range(8):
        rid = "2026-09-02T1200{:02d}".format(n)
        for part in (1, 2, 3):
            _touch(logdir, rid, part, size=10)
    logsetup.sweep(logdir, runid=None)
    runs = {}
    for p in logdir.glob("log_*"):
        rid, part = p.stem[len("log_"):].rsplit("_", 1)
        runs.setdefault(rid, set()).add(int(part))
    for rid, parts in runs.items():
        assert 1 in parts, "run {} survived without its _001".format(rid)


def test_sweep_never_drops_the_current_run(logdir, monkeypatch):
    monkeypatch.setattr(logsetup, "TOTAL_BYTES", 1)  # force size pressure
    for n in range(3):
        _touch(logdir, "2026-09-02T1200{:02d}".format(n), 1, size=1000)
    logsetup.sweep(logdir, runid="2026-09-02T120000")
    assert (logdir / "log_2026-09-02T120000_001.txt").exists()


def _record(msg):
    return logging.LogRecord("t", logging.INFO, __file__, 1, msg, (), None)


def test_dedupe_suppresses_repeats_and_keeps_the_count():
    """Nothing is lost: the tally rides the line that broke the run, so it
    cannot be stranded behind a crash the way a trailing summary would be."""
    f = logsetup.DedupeFilter()
    first = _record("same")
    assert f.filter(first) is True
    for _ in range(86):
        assert f.filter(_record("same")) is False
    changed = _record("different")
    assert f.filter(changed) is True
    assert "repeated 86" in changed.getMessage()
    assert "different" in changed.getMessage()


def test_dedupe_passes_distinct_lines_untouched():
    f = logsetup.DedupeFilter()
    a, b = _record("one"), _record("two")
    assert f.filter(a) and f.filter(b)
    assert a.getMessage() == "one"
    assert b.getMessage() == "two"


def test_dedupe_compares_the_formatted_message():
    """Two calls with different args are different lines — which is what a
    reader cares about, and why this compares getMessage() not record.msg."""
    f = logsetup.DedupeFilter()
    r1 = logging.LogRecord("t", logging.INFO, __file__, 1, "n=%d", (1,), None)
    r2 = logging.LogRecord("t", logging.INFO, __file__, 1, "n=%d", (2,), None)
    assert f.filter(r1) is True
    assert f.filter(r2) is True
