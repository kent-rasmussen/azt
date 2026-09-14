# coding=UTF-8
"""Serving a page as a webview child, with Tk keeping the mainloop.

ADR 0004 D7. Mixed mode is the DEFAULT from 2026-09-14 (Kent: "no, this
mixed mode is now default. the other two are opt in"), with the standing
constraint that `--tkinter` and `--webview` each stay fully functional on
their own.

**WHAT THESE TESTS ARE FOR.** The child needs a display, so the rendering
cannot be tested here and is checked by hand (`frontend/served_splash.py`'s
docstring has the one-line invocation). What CAN and must be tested headless
is the part that protects everything else: **that a child which does not
appear costs nothing.** Every refusal and every failure has to end with the
caller free to build its Tk page.

So these tests pin three things:

  * the two pure modes serve nothing, and a page that is not in the registry
    serves nothing;
  * a child that fails to start, fails to report ready, or dies, yields None
    rather than an exception or a hang;
  * the view model is plain data, and survives a program whose git calls
    raise.
"""
import json

import pytest

served = pytest.importorskip('frontend.served',
                             reason='needs frontend importable')


# ── which modes serve, and which do not ──────────────────────────────────

def test_the_default_mode_serves_a_registered_page():
    """No explicit backend request, Tk host: this is the default, and it is
    the one that serves."""
    assert served.available('splash', 'tkinter', None) is True


def test_tkinter_only_serves_nothing():
    """`--tkinter` means tkinter ONLY — Kent's constraint. If this ever
    returns True, the pure Tk mode has quietly grown a subprocess."""
    assert served.available('splash', 'tkinter', 'tkinter') is False


def test_webview_only_serves_nothing():
    """Under full webview there is no Tk host and nothing to fall back to,
    and the page already renders in-process."""
    assert served.available('splash', 'webview', 'webview') is False
    assert served.available('splash', 'webview', None) is False


def test_an_empty_command_line_is_not_a_request_for_tkinter(monkeypatch):
    """THE REGRESSION, 2026-09-14. `ui_backend.requested()` DEFAULTS to
    'tkinter', so asking it "what was requested" made a bare `python -m main`
    look like `--tkinter`: the splash was never served and the log blamed a
    switch Kent had not typed. `explicit()` is the question mixed mode needs,
    and it must answer None."""
    backend = pytest.importorskip('utilities.ui_backend')
    monkeypatch.setattr(backend.sys, 'argv', ['main.py'])
    monkeypatch.delenv('AZT_UI_BACKEND', raising=False)
    assert backend.explicit() is None
    assert backend.requested() == 'tkinter'
    assert served.available('splash', 'tkinter', backend.explicit()) is True


@pytest.mark.parametrize('argv,expected', [
    (['main.py', '--tkinter'], 'tkinter'),
    (['main.py', '--webview'], 'webview'),
    (['main.py', '--no-splash'], None),
])
def test_explicit_reports_only_what_was_typed(monkeypatch, argv, expected):
    backend = pytest.importorskip('utilities.ui_backend')
    monkeypatch.setattr(backend.sys, 'argv', argv)
    monkeypatch.delenv('AZT_UI_BACKEND', raising=False)
    assert backend.explicit() == expected


def test_the_env_var_counts_as_explicit(monkeypatch):
    """`AZT_UI_BACKEND=tkinter` asks for tkinter only just as the switch
    does, which is why `available()`'s refusal says "tkinter only was asked
    for" rather than naming a switch."""
    backend = pytest.importorskip('utilities.ui_backend')
    monkeypatch.setattr(backend.sys, 'argv', ['main.py'])
    monkeypatch.setenv('AZT_UI_BACKEND', 'tkinter')
    assert backend.explicit() == 'tkinter'


def test_an_unported_page_is_never_served():
    """The registry is the only gate on the default mode, which is what
    makes the default shippable while the port is unfinished."""
    assert 'sort' not in served.SERVED_PAGES
    assert served.available('sort', 'tkinter', None) is False


def test_the_registry_holds_only_verified_pages():
    """A reminder in test form: adding a name here turns it on for every
    user of the default mode, so it belongs only to a page seen working."""
    assert served.SERVED_PAGES == frozenset({'splash'})


# ── the view model is plain data ──────────────────────────────────────────

class Repo:
    def lastcommitdate(self):
        return '2026-09-14'

    def lastcommitdaterelative(self):
        return 'today'


class Program:
    name = 'A-Z+T'
    version = '1.15.21'
    source_repo = Repo()


def test_the_splash_view_model_is_json_serialisable():
    """It crosses a pipe, so anything that is not plain data is a bug here
    rather than a mystery in the child."""
    view = served.splash_view(Program())
    assert json.loads(json.dumps(view)) == view


def test_the_splash_view_model_carries_what_the_page_shows():
    view = served.splash_view(Program())
    for key in ('title', 'version', 'updated', 'loading', 'description',
                'image', 'progress'):
        assert key in view, "view model is missing {}".format(key)
    assert '1.15.21' in view['version']
    assert 'today' in view['updated']


def test_a_repo_that_raises_does_not_stop_the_boot():
    """`source_repo` reads git. A boot must not die because a date could not
    be formatted."""
    class Broken:
        def lastcommitdate(self):
            raise RuntimeError('not a git repository')

        def lastcommitdaterelative(self):
            raise RuntimeError('not a git repository')

    class P(Program):
        source_repo = Broken()

    view = served.splash_view(P())
    assert '?' in view['updated']


def test_no_repo_at_all_is_survivable():
    class P:
        name = 'A-Z+T'
    view = served.splash_view(P())
    assert isinstance(view['updated'], str)


# ── failure yields None, never an exception ──────────────────────────────

def test_a_child_that_cannot_start_falls_back(monkeypatch):
    def boom(*a, **k):
        raise OSError('no such interpreter')
    monkeypatch.setattr(served.subprocess, 'Popen', boom)
    page = served.ServedPage('splash', 'frontend.served_splash')
    assert page.start({}) is False


def test_a_child_that_never_reports_ready_is_killed_and_falls_back(monkeypatch):
    """The timeout is the whole safety property. Note it is waited for
    SYNCHRONOUSLY on purpose: `main.py` runs the whole of boot without
    returning to the mainloop, so an `after()`-based check would resolve
    after the thing it gates — the 400ms wait-dialog delay's mistake."""
    fake = _FakeProc()
    monkeypatch.setattr(served.subprocess, 'Popen', lambda *a, **k: fake)
    page = served.ServedPage('splash', 'frontend.served_splash')
    assert page.start({}, timeout=0.2) is False
    assert fake.closed, "a child that never came up was left running"


def test_a_child_that_reports_ready_is_used(monkeypatch):
    fake = _FakeProc(stdout_lines=[json.dumps({'kind': served.MSG_READY})])
    monkeypatch.setattr(served.subprocess, 'Popen', lambda *a, **k: fake)
    page = served.ServedPage('splash', 'frontend.served_splash')
    assert page.start({}, timeout=2.0) is True
    assert page.alive


def test_splash_returns_none_when_the_child_fails(monkeypatch):
    """The factory's contract: None means "build the Tk Splash", and it is
    the ordinary path, not an error path."""
    monkeypatch.setattr(served.subprocess, 'Popen',
                        lambda *a, **k: _FakeProc())
    assert served.splash(Program(), 'tkinter', None, ) is None


def test_a_broken_pipe_does_not_propagate(monkeypatch):
    """Once the caller has committed to a served page, a splash that stops
    animating must not take the boot down with it."""
    class Stdin:
        def write(self, s):
            raise BrokenPipeError('child is gone')

        def flush(self):
            pass
    fake = _FakeProc()
    fake.stdin = Stdin()
    monkeypatch.setattr(served.subprocess, 'Popen', lambda *a, **k: fake)
    page = served.ServedPage('splash', 'frontend.served_splash')
    page.proc = fake
    assert page.send(served.MSG_UPDATE, fields={'progress': 5}) is False
    assert page.send(served.MSG_UPDATE, fields={'progress': 6}) is False


# ── the parent-side splash wears Splash's surface ────────────────────────

class FakePage:
    def __init__(self):
        self.sent = []
        self.closed = False
        self.alive = True

    def send(self, kind, **fields):
        self.sent.append((kind, fields))
        return True

    def close(self):
        self.closed = True
        self.alive = False


def test_progress_crosses_as_an_update():
    p = FakePage()
    s = served.ServedSplash(p)
    s.progress(25)
    assert p.sent == [(served.MSG_UPDATE, {'fields': {'progress': 25}})]


def test_withdraw_and_destroy_both_close_the_child():
    for method in ('withdraw', 'destroy'):
        p = FakePage()
        getattr(served.ServedSplash(p), method)()
        assert p.closed, "{} left the child running".format(method)


def test_winfo_exists_follows_the_child():
    p = FakePage()
    s = served.ServedSplash(p)
    assert s.winfo_exists() is True
    s.destroy()
    assert s.winfo_exists() is False


def test_the_exit_flag_never_reads_as_the_user_quitting():
    """`exitFlag.istrue()` is how the user cancels during boot
    (tasks/chooser.py:493,549). A served splash has no channel to say that
    yet, so it must answer False — inventing True would abort a boot nobody
    asked to abort. Same accepted loss as `_NoSplash` under `--no-splash`."""
    s = served.ServedSplash(FakePage())
    assert s.exitFlag.istrue() is False
    s.exitFlag.true()
    assert s.exitFlag.istrue() is False


def test_the_rest_of_the_splash_api_is_swallowed():
    """~15 call sites across three modules touch `splash`. Anything not
    implemented must be a no-op, as `_NoSplash` established."""
    s = served.ServedSplash(FakePage())
    for name in ('lift', 'update_idletasks', 'title', 'geometry'):
        assert getattr(s, name)() is None


# ── a subprocess stand-in ────────────────────────────────────────────────

class _FakeProc:
    """Enough of Popen for the supervision logic. Deliberately not a real
    subprocess: these tests must run with no display, no interpreter launch
    and no timing luck."""

    def __init__(self, stdout_lines=(), alive=True):
        self.pid = 4242
        self.stdout = list(stdout_lines)
        self.stderr = []
        self.stdin = _FakeStdin()
        self.closed = False
        self._alive = alive

    def poll(self):
        return None if self._alive else 0

    def wait(self, timeout=None):
        self.closed = True
        self._alive = False
        return 0

    def terminate(self):
        self.closed = True
        self._alive = False

    kill = terminate


class _FakeStdin:
    def __init__(self):
        self.written = []

    def write(self, s):
        self.written.append(s)

    def flush(self):
        pass
