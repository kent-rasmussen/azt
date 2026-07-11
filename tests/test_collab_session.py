"""Unit tests for backend.core.collab's CollabSession — the Phase 2/3
base-and-staleness bookkeeping that the no-clobber guarantee rides on.

The load-bearing invariants pinned here:

1. A fast-path commit advances the base (next save stays fast).
2. A MERGED_WITH_LOCAL save does NOT advance the base — the in-memory
   tree still derives from the old base, and advancing would let the
   next save fast-path replace the merged file, content-clobbering
   the peer changes the daemon just folded in. (Regression test for
   the flaw found in design review 2026-07-07.)
3. The poll distinguishes benign HEAD advances (artifact commits;
   LIFT on disk untouched → adopt new base silently) from foreign
   LIFT changes (→ 'changed', base NOT advanced, reload offered).
4. Probe/transport failures are never events ('none').

No daemon, no network: the client module is replaced by a stub. The
azt_collab_client status module IS imported for real (via the
discovery shim) so code constants can't drift silently.
"""

import os
import types

import pytest

from backend.core import collab

pytestmark = pytest.mark.skipif(
    not collab.AVAILABLE,
    reason='azt_collab_client not importable (no sister azt-collab '
           'clone); collab seams are inert in this checkout')

if collab.AVAILABLE:
    from azt_collab_client.status import Result, Status


def _result(*codes_params, head_sha=''):
    """Build a client-shaped Result: [(code, params), ...] + the
    wrapper-attached head_sha attribute."""
    res = Result(statuses=[Status(code, dict(params))
                           for code, params in codes_params])
    res.head_sha = head_sha
    return res


@pytest.fixture
def session(tmp_path, monkeypatch):
    lift = tmp_path / 't.lift'
    lift.write_bytes(b'<lift/>')
    s = collab.CollabSession(types.SimpleNamespace(name='test'),
                             'xx-x-test', 'base1',
                             lift_path=str(lift))
    s.record_lift_stat()
    # A stub client; individual tests overwrite the calls they use.
    monkeypatch.setattr(collab, '_client', types.SimpleNamespace())
    return s


def _stage(session, content=b'<lift>v2</lift>'):
    staged = session.lift_path + '.part'
    with open(staged, 'wb') as fh:
        fh.write(content)
    return staged


# ── submit(): base bookkeeping ────────────────────────────────────────


def test_submit_fast_path_advances_base(session):
    staged = _stage(session)
    collab._client.submit_file = lambda *a: _result(
        ('COMMITTED_LOCAL', {'head_sha': 'head2'}), head_sha='head2')
    assert session.submit(session.lift_path, staged) == 'ok'
    assert session.base_sha == 'head2'
    assert session.stale is False


def test_submit_nothing_to_commit_is_benign(session):
    """Identical-content saves (autosave cadence; post-degraded-write
    catch-up) answer NOTHING_TO_COMMIT: adopt head, clear degraded,
    'ok' — NOT the consumed-but-errored warning path (2026-07-11)."""
    staged = _stage(session)
    session.degraded = True
    collab._client.submit_file = lambda *a: _result(
        ('NOTHING_TO_COMMIT', {'head_sha': 'head3'}), head_sha='head3')
    assert session.submit(session.lift_path, staged) == 'ok'
    assert session.base_sha == 'head3'
    assert session.degraded is False
    assert session.stale is False


def test_submit_merged_keeps_base_and_flags_stale(session):
    """Invariant 2 — the clobber-prevention regression test."""
    staged = _stage(session)
    collab._client.submit_file = lambda *a: _result(
        ('MERGED_WITH_LOCAL', {'n_conflicts': 1, 'base_sha': 'base1'}),
        ('COMMITTED_LOCAL', {'head_sha': 'merge1'}),
        head_sha='merge1')
    assert session.submit(session.lift_path, staged) == 'ok'
    assert session.base_sha == 'base1'      # NOT advanced to merge1
    assert session.stale is True


def test_submit_contributor_unset_is_ok_without_base_move(session):
    staged = _stage(session)
    collab._client.submit_file = lambda *a: _result(
        ('CONTRIBUTOR_UNSET', {}))
    assert session.submit(session.lift_path, staged) == 'ok'
    assert session.base_sha == 'base1'


def test_submit_failure_with_staged_intact_falls_back(session):
    staged = _stage(session)
    collab._client.submit_file = lambda *a: _result(
        ('SERVER_UNAVAILABLE', {'error': 'x'}))
    assert session.submit(session.lift_path, staged) == 'fallback'
    assert session.degraded is True
    assert os.path.exists(staged)           # caller's os.replace source


def test_submit_failure_with_staged_consumed_is_ok(session):
    """Daemon replaced the file then failed later (e.g. commit) —
    bytes are durable, so reporting a write failure would be false."""
    staged = _stage(session)
    def fake(*a):
        os.unlink(staged)                   # daemon consumed it
        return _result(('SERVER_ERROR', {'error': 'post-replace'}))
    collab._client.submit_file = fake
    assert session.submit(session.lift_path, staged) == 'ok'


# ── poll_remote_change() ─────────────────────────────────────────────


def _status(head):
    return types.SimpleNamespace(head_sha=head)


def test_poll_none_when_head_equals_base(session):
    collab._client.project_status = lambda lc: _status('base1')
    assert session.poll_remote_change() == 'none'


def test_poll_benign_artifact_commit_advances_base(session):
    collab._client.project_status = lambda lc: _status('head9')
    # LIFT on disk untouched since record_lift_stat().
    assert session.poll_remote_change() == 'benign'
    assert session.base_sha == 'head9'
    assert session.stale is False


def test_poll_changed_on_foreign_lift_write(session):
    collab._client.project_status = lambda lc: _status('head9')
    with open(session.lift_path, 'ab') as fh:
        fh.write(b'<!--peer-->')            # size change → stat differs
    assert session.poll_remote_change() == 'changed'
    assert session.base_sha == 'base1'      # NOT advanced
    assert session.stale is True


def test_poll_stale_stays_changed_and_never_advances_base(session):
    session.stale = True
    session.base_sha = 'base1'
    collab._client.project_status = lambda lc: _status('head9')
    assert session.poll_remote_change() == 'changed'
    assert session.base_sha == 'base1'          # never advances while stale
    assert session._last_detected_head == 'head9'  # but tracks newest head


def test_poll_stale_tolerates_probe_failure(session):
    session.stale = True
    def boom(lc):
        raise RuntimeError('down')
    collab._client.project_status = boom
    assert session.poll_remote_change() == 'changed'


def test_poll_probe_failure_is_never_an_event(session):
    def boom(lc):
        raise RuntimeError('daemon down')
    collab._client.project_status = boom
    assert session.poll_remote_change() == 'none'
    collab._client.project_status = lambda lc: None
    assert session.poll_remote_change() == 'none'


# ── adopt_reloaded_db(): A5 in-place-reload rebase ────────────────────


def test_adopt_reloaded_db_rebases_and_clears_latch(session):
    """After an in-place reload the in-memory tree derives from the
    on-disk (merged) LIFT: base adopts the daemon's head, the stale
    latch and offer memory clear, and the NEW db gets the write seam."""
    session.stale = True
    session._last_detected_head = 'head9'
    session._offered_head = 'head9'
    db = types.SimpleNamespace()
    session.program.db = db
    collab._client.project_status = lambda lc: types.SimpleNamespace(
        head_sha='head9', lift_blob_sha='blob9')
    session.adopt_reloaded_db()
    assert db.collab_submit == session.submit
    assert session.base_sha == 'head9'
    assert session.base_lift_blob == 'blob9'
    assert session.stale is False
    assert session._last_detected_head == ''
    assert session._offered_head == ''


def test_adopt_reloaded_db_daemon_down_keeps_base(session):
    """Daemon unreachable at rebase: keep the old base (saves stay
    safe — they re-merge against it), still hook the new db and clear
    the latch (the tree DOES now derive from the on-disk merge)."""
    session.stale = True
    db = types.SimpleNamespace()
    session.program.db = db
    def boom(lc):
        raise OSError('down')
    collab._client.project_status = boom
    session.adopt_reloaded_db()
    assert db.collab_submit == session.submit
    assert session.base_sha == 'base1'
    assert session.stale is False


# ── reload_offer_due() rate limiting + new-head bypass ───────────────


def test_reload_offer_snoozes_same_head(session):
    session._last_detected_head = 'h1'
    assert session.reload_offer_due(snooze_s=300) is True    # first offer
    assert session.reload_offer_due(snooze_s=300) is False   # snoozed
    assert session.reload_offer_due(snooze_s=0) is True      # timer elapsed


def test_reload_offer_new_head_bypasses_snooze(session):
    """The user's case: decline once, then a genuinely new peer change
    must re-offer immediately despite the snooze."""
    session._last_detected_head = 'h1'
    assert session.reload_offer_due(snooze_s=300) is True    # offer for h1
    assert session.reload_offer_due(snooze_s=300) is False   # decline → snooze
    session._last_detected_head = 'h2'                       # new team work
    assert session.reload_offer_due(snooze_s=300) is True    # bypasses snooze
    assert session.reload_offer_due(snooze_s=300) is False   # h2 now snoozed


# ── Phase 4: sync() + route_sync_result() ────────────────────────────


@pytest.fixture
def routing(monkeypatch):
    """Capture the routing side effects: notices shown, settings UI
    opened. translate_result is stubbed to a codes-string so tests
    don't depend on translations."""
    import azt_collab_client as client_pkg
    from utilities import error_handler
    seen = types.SimpleNamespace(notices=[], settings_opened=0)
    monkeypatch.setattr(error_handler, 'notify_error',
                        lambda text, **kw: seen.notices.append(text))
    monkeypatch.setattr(client_pkg, 'translate_result',
                        lambda r: '|'.join(r.codes()))
    def fake_open_server_ui(on_status=None):
        seen.settings_opened += 1
        return {'ok': True, 'pid': 0}
    monkeypatch.setattr(client_pkg, 'open_server_ui',
                        fake_open_server_ui)
    return seen


def test_route_config_class_opens_settings(session, routing):
    session.route_sync_result(_result(('AUTH_REQUIRED', {})))
    assert routing.settings_opened == 1
    assert any('AUTH_REQUIRED' in n for n in routing.notices)


def test_route_success_notifies_without_settings(session, routing):
    session.route_sync_result(_result(('PUSHED', {'branch': 'main'})))
    assert routing.settings_opened == 0
    assert len(routing.notices) == 1


def test_route_pulled_flags_stale_for_reload_offer(session, routing):
    res = _result(('PULLED', {}), ('PUSHED', {}), head_sha='pull9')
    session.route_sync_result(res)
    assert session.stale is True
    assert session._last_detected_head == 'pull9'


def test_sync_retries_once_on_job_interrupted(session, routing):
    calls = []
    def fake_sync(lc):
        calls.append(lc)
        if len(calls) == 1:
            return _result(('JOB_INTERRUPTED', {}))
        return _result(('PUSHED', {}), head_sha='h2')
    collab._client.sync_project = fake_sync
    result = session.sync()
    assert len(calls) == 2
    assert result.has('PUSHED')
    assert session._sync_in_flight is False


def test_sync_in_flight_guard(session, routing):
    session._sync_in_flight = True
    # No sync_project on the stub: a call would AttributeError.
    assert session.sync() is None
