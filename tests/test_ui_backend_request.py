# coding=UTF-8
"""Which UI backend was asked for, and whether one was asked for at all.

`utilities.ui_backend` is the one place that question is decided
(`frontend/__init__.py` says so). It answers two DIFFERENT questions and the
difference matters:

  * `requested()` — which backend to use, **defaulting to tkinter**.
  * `explicit()` — which backend the user actually named, or **None**.

`explicit()` exists because asking `requested()` "did anyone ask?" made a
bare `python -m main` indistinguishable from `--tkinter`, and a feature gated
on that refused to run with a log line blaming a switch Kent had not typed
(2026-09-14). The feature is gone; the distinction is real, and these tests
are what remain of that lesson.
"""
import pytest

backend = pytest.importorskip('utilities.ui_backend',
                              reason='needs utilities importable')


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv('AZT_UI_BACKEND', raising=False)
    monkeypatch.setattr(backend.sys, 'argv', ['main.py'])


def test_nothing_asked_for_is_None_not_tkinter():
    """THE DISTINCTION. `requested()` must still default, so `chosen()`
    keeps working; `explicit()` must not pretend a default was a request."""
    assert backend.explicit() is None
    assert backend.requested() == 'tkinter'


@pytest.mark.parametrize('flag,expected', [
    ('--tkinter', 'tkinter'),
    ('--webview', 'webview'),
])
def test_a_switch_is_explicit(monkeypatch, flag, expected):
    monkeypatch.setattr(backend.sys, 'argv', ['main.py', flag])
    assert backend.explicit() == expected
    assert backend.requested() == expected


def test_an_unrelated_switch_is_not_a_request(monkeypatch):
    monkeypatch.setattr(backend.sys, 'argv',
                        ['main.py', '--no-splash', '--console'])
    assert backend.explicit() is None


def test_the_env_var_is_explicit_too(monkeypatch):
    """`AZT_UI_BACKEND=tkinter` asks for tkinter as plainly as the switch
    does — so anything reporting a refusal must not name a switch."""
    monkeypatch.setenv('AZT_UI_BACKEND', 'webview')
    assert backend.explicit() == 'webview'


def test_a_switch_beats_the_env_var(monkeypatch):
    monkeypatch.setattr(backend.sys, 'argv', ['main.py', '--tkinter'])
    monkeypatch.setenv('AZT_UI_BACKEND', 'webview')
    assert backend.explicit() == 'tkinter'


def test_an_unknown_env_value_is_not_a_request(monkeypatch):
    """And `requested()` still falls back to tkinter and warns, which is the
    behaviour `chosen()` depends on."""
    monkeypatch.setenv('AZT_UI_BACKEND', 'gtk')      # not a backend
    assert backend.explicit() is None
    assert backend.requested() == 'tkinter'
