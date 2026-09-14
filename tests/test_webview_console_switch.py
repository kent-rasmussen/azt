# coding=UTF-8
"""The webview devtools console is OFF unless `--console` is passed.

Kent, 2026-09-14: "let's turn off the console by default. and rather than
calling it --no-i-really-do-want-the-console-this-time, let's just use
--console."

This default has moved twice already — unconditional (which opened a remote
debugging server on field machines), then following the app's dev-settings
flag (on in the working tree always, with `--user` the only way off) — so it
is worth pinning. `_engine` is monkeypatched throughout: engine *selection*
probes the host and is a separate question from whether the console is on.
"""
import pytest

wv = pytest.importorskip('frontend.ui_webview',
                         reason='needs pywebview importable')


class Dev:
    """A program with dev settings on — which must no longer matter here."""
    testing = True


@pytest.fixture
def engine(monkeypatch):
    """Choose the reported engine without probing the host."""
    def choose(name):
        monkeypatch.setattr(wv, '_engine', lambda: name)
    return choose


def _argv(monkeypatch, *args):
    monkeypatch.setattr(wv.sys, 'argv', ['main.py', *args])


def test_off_by_default(monkeypatch, engine):
    engine('gtk')
    _argv(monkeypatch)
    assert wv._start_kwargs()['debug'] is False


def test_off_even_with_dev_settings(monkeypatch, engine):
    """The regression this replaces: `debug = program.testing` meant the
    console was on in the working tree whether or not anyone wanted it."""
    engine('gtk')
    _argv(monkeypatch)
    assert wv._start_kwargs(Dev())['debug'] is False


def test_on_with_the_switch(monkeypatch, engine):
    engine('gtk')
    _argv(monkeypatch, '--console')
    assert wv._start_kwargs()['debug'] is True


def test_on_with_the_switch_even_without_dev_settings(monkeypatch, engine):
    engine('gtk')
    _argv(monkeypatch, '--console')
    assert wv._start_kwargs(None)['debug'] is True


def test_honoured_on_qt_despite_the_segfault(monkeypatch, engine):
    """It used to be suppressed on Qt, where `show_inspector` GCs inside a
    `resizeEvent`. Now that it has to be ASKED for, asking is answered — with
    a warning, not a silent refusal."""
    engine('qt')
    _argv(monkeypatch, '--console')
    assert wv._start_kwargs()['debug'] is True


def test_the_retired_switch_names_do_nothing(monkeypatch, engine):
    """One switch, one name. `--webview-devtools` and
    `--no-webview-devtools` both existed within a day of `--console` and must
    not linger as half-working aliases — the `mainwindow`/`ismainwindow` trap
    (agenda/bridge_shadowed_attributes.md)."""
    engine('gtk')
    for stale in ('--webview-devtools', '--no-webview-devtools'):
        _argv(monkeypatch, stale)
        assert wv._start_kwargs(Dev())['debug'] is False, \
            "{} still turns the console on".format(stale)


def test_the_engine_is_still_reported(monkeypatch, engine):
    """The console switch must not have disturbed the other half of this
    function: a named engine still reaches webview.start()."""
    engine('gtk')
    _argv(monkeypatch)
    assert wv._start_kwargs().get('gui') == 'gtk'


def test_no_engine_means_no_gui_key(monkeypatch, engine):
    """`None` means "let pywebview choose", which is not the same as asking
    for nothing."""
    engine(None)
    _argv(monkeypatch)
    assert 'gui' not in wv._start_kwargs()
