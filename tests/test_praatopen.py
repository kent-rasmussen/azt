"""Open in Praat (utilities/executables.py praatopen). 2026-11-11: with sendpraat present and no Praat running,
the retry was praatopen(file, newpraat=True) — no `program` — so it raised and nothing opened."""
import subprocess
import types

import pytest

from utilities import executables


def test_no_praat_running_starts_one(monkeypatch):
    calls = []

    def check_output(args, **kwargs):
        calls.append(('sendpraat', args))
        return b'sendpraat: Program praat not running.\n'

    monkeypatch.setattr(subprocess, 'check_output', check_output)
    monkeypatch.setattr(subprocess, 'Popen', lambda args, **kwargs: calls.append(('praat', args)))
    program = types.SimpleNamespace(sendpraat='/x/sendpraat', praat='/x/praat')
    executables.praatopen(program, '/a/word.wav')
    assert [c[0] for c in calls] == ['sendpraat', 'praat']
    assert calls[1][1][-1] == '/a/word.wav'


def test_m4a_is_not_handed_to_praat(monkeypatch):
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('opened'))
    program = types.SimpleNamespace(praat='/x/praat')
    executables.praatopen(program, '/a/word.m4a')
