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
    # pywebview's own variable, which `requested_engine()` reads: a developer
    # who exports it would otherwise change what these tests measure.
    monkeypatch.delenv('PYWEBVIEW_GUI', raising=False)
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


# --- how the request was made, and how the refusal reaches the user ---------
# `agenda/webview_requested_but_absent.md`: a declined switch used to leave no
# trace but a log line, and that line was printed twice.


@pytest.fixture
def fresh(monkeypatch):
    """`chosen()` caches its answer and its warning in module globals, and
    appends to a module-level list. Reset all three per test."""
    monkeypatch.setattr(backend, '_chosen', None)
    monkeypatch.setattr(backend, '_warned', False)
    monkeypatch.setattr(backend, 'BACKEND_PROBLEMS', [])
    return backend


def test_request_source_names_the_switch(monkeypatch):
    monkeypatch.setattr(backend.sys, 'argv', ['main.py', '--webview'])
    assert backend.request_source() == '--webview'


def test_request_source_names_the_variable_not_a_switch(monkeypatch):
    """THE POINT OF THIS FUNCTION. A refusal that hardcodes `--webview` sends
    someone who set the variable hunting through a command line that has no
    such flag on it."""
    monkeypatch.setenv('AZT_UI_BACKEND', 'webview')
    assert backend.request_source() == 'AZT_UI_BACKEND=webview'
    assert '--' not in backend.request_source()


def test_nobody_asked_means_no_source():
    assert backend.request_source() is None


def test_a_refusal_is_recorded_for_the_user(fresh, monkeypatch):
    """The refusal must survive past the log line: main.py raises it as a
    notice once there is a window to put it in."""
    monkeypatch.setattr(backend.sys, 'argv', ['main.py', '--webview'])
    monkeypatch.setattr(backend, 'webview_problem',
                        lambda: 'pywebview is not installed in X')
    assert backend.chosen() == 'tkinter'
    assert backend.BACKEND_PROBLEMS == [('--webview',
                                         'pywebview is not installed in X')]


def test_the_refusal_names_the_variable_when_that_is_how_it_was_asked(
        fresh, monkeypatch):
    monkeypatch.setenv('AZT_UI_BACKEND', 'webview')
    monkeypatch.setattr(backend, 'webview_problem', lambda: 'no host toolkit')
    backend.chosen()
    assert backend.BACKEND_PROBLEMS[0][0] == 'AZT_UI_BACKEND=webview'


def test_a_working_webview_records_nothing(fresh, monkeypatch):
    monkeypatch.setattr(backend.sys, 'argv', ['main.py', '--webview'])
    monkeypatch.setattr(backend, 'webview_problem', lambda: None)
    assert backend.chosen() == 'webview'
    assert backend.BACKEND_PROBLEMS == []


def test_a_plain_tkinter_run_records_nothing(fresh):
    assert backend.chosen() == 'tkinter'
    assert backend.BACKEND_PROBLEMS == []


def test_the_refusal_is_not_written_to_stderr_as_well(fresh, monkeypatch):
    """THE DOUBLE LINE. `logsetup` attaches a StreamHandler(sys.__stderr__) to
    the root logger with format '%(message)s', so `log.warning` ALREADY puts
    this text bare on stderr. The `sys.stderr.write` that used to follow it
    printed the same line a second time, which read as two deciders — there is
    only ever one. Don't put it back."""
    monkeypatch.setattr(backend.sys, 'argv', ['main.py', '--webview'])
    monkeypatch.setattr(backend, 'webview_problem', lambda: 'no pywebview')

    class Recorder:
        def __init__(self):
            self.written = []

        def write(self, text):
            self.written.append(text)

        def flush(self):
            pass

    recorder = Recorder()
    monkeypatch.setattr(backend.sys, 'stderr', recorder)
    backend.chosen()
    assert recorder.written == []


def test_the_refusal_is_recorded_once_however_often_it_is_asked(
        fresh, monkeypatch):
    monkeypatch.setattr(backend.sys, 'argv', ['main.py', '--webview'])
    monkeypatch.setattr(backend, 'webview_problem', lambda: 'no pywebview')
    for _unused in range(5):
        backend.chosen()
    assert len(backend.BACKEND_PROBLEMS) == 1


def test_engine_request_source_names_what_was_typed(monkeypatch):
    monkeypatch.setattr(backend.sys, 'argv', ['main.py', '--engine=qt'])
    assert backend.requested_engine() == 'qt'
    assert backend.engine_request_source() == '--engine=qt'


def test_engine_request_source_names_pywebviews_own_variable(monkeypatch):
    """PYWEBVIEW_GUI is honoured deliberately, so it is a real way in and a
    substitution made because of it must be reportable in those terms."""
    monkeypatch.setenv('PYWEBVIEW_GUI', 'gtk')
    assert backend.requested_engine() == 'gtk'
    assert backend.engine_request_source() == 'PYWEBVIEW_GUI=gtk'


def test_no_engine_asked_for_has_no_source(monkeypatch):
    monkeypatch.delenv('PYWEBVIEW_GUI', raising=False)
    assert backend.requested_engine() is None
    assert backend.engine_request_source() is None
