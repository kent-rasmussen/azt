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
