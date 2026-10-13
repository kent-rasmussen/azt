"""A renamed project folder is a move, not a second copy.

Kent, 2026-10-13: the project folder was renamed (wmg-new → wmg-nopush);
the attach check compared paths only, called it "a different copy", and
switched collaboration off — and Advanced → Reconnect only re-probed the
server, which answered, so the app restarted into the same refusal.
"""
from types import SimpleNamespace

import pytest

collab = pytest.importorskip('backend.core.collab')


def program(reason):
    return SimpleNamespace(collab_wanted={'langcode': 'wmg',
                                          'reason': reason})


def test_reconnect_on_a_moved_project_re_registers_it(monkeypatch):
    monkeypatch.setattr(collab, 'AVAILABLE', True)
    called = []
    monkeypatch.setattr(collab, 'connect_current_project',
                        lambda p: called.append(p) or (True, 'Connected!'))
    monkeypatch.setattr(collab, 'restart_collab_daemon',
                        lambda: pytest.fail('must not just re-probe'))
    p = program(collab.MOVED)
    assert collab.retry_connection(p) == (True, 'Connected!')
    assert called == [p]


def test_reconnect_on_a_wrong_copy_does_not_loop(monkeypatch):
    monkeypatch.setattr(collab, 'AVAILABLE', True)
    monkeypatch.setattr(collab, 'restart_collab_daemon',
                        lambda: pytest.fail('a probe would restart into '
                                            'the same refusal'))
    ok, msg = collab.retry_connection(program(collab.WRONG_TREE))
    assert ok is False and 'wmg' in msg
