# coding=UTF-8
"""The webview Button calls its command the way the COMMAND expects.

WHY. `_build_command` decided what to pass from what the CALLER supplied: a
`choice` kwarg meant "pass the choice". A caller that supplies a choice
alongside a command taking no arguments therefore produced, on every click:

    TypeError: Sort.runcheck() takes 1 positional argument but 2 were given

and the button did nothing visible, because `on_event` logs the traceback and
carries on — so it presented as a dead button (Kent's Mac, webview backend,
2026-09-11). The presence of a `choice` says what the BUTTON knows; only the
command's signature says what the command wants.

`_takes` is a plain method, so these call it on a stand-in `self` — no
pywebview, no window, no display.
"""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ui_webview = pytest.importorskip('frontend.ui_webview',
                                 reason='needs the webview backend importable')

Button = ui_webview.Button


def stand_in(command, choice=None, window=None):
    """Enough of a Button for `_build_command`, with the registration and the
    resulting call captured."""
    obj = types.SimpleNamespace(command=command, choice=choice, window=window,
                                _wid=1)
    obj._takes = types.MethodType(Button._takes, obj)
    obj._build_command = types.MethodType(Button._build_command, obj)
    return obj


def built(command, choice=None, window=None, monkeypatch=None):
    """Build the command and return the callable it registered."""
    obj = stand_in(command, choice, window)
    registered = {}
    monkeypatch.setattr(ui_webview._api, 'register',
                        lambda wid, name, fn: registered.setdefault('fn', fn))
    obj._build_command()
    return registered.get('fn') or obj._final_cmd


# ─── The regression ─────────────────────────────────────────────────────────

def test_a_no_argument_command_is_called_with_no_arguments(monkeypatch):
    """THE BUG. `Sort.runcheck(self)` accepts nothing more; a choice must not
    be forced on it."""
    calls = []

    def runcheck():
        calls.append('called')

    built(runcheck, choice='V', monkeypatch=monkeypatch)(None)
    assert calls == ['called'], 'the command must be called, not raise'


def test_a_command_that_wants_the_choice_still_gets_it(monkeypatch):
    """The behaviour that made the old rule look right — and must survive."""
    got = []
    built(lambda value: got.append(value), choice='V',
          monkeypatch=monkeypatch)(None)
    assert got == ['V']


def test_a_command_that_wants_choice_and_window_gets_both(monkeypatch):
    got = {}

    def cmd(value, window=None):
        got['value'] = value
        got['window'] = window

    built(cmd, choice='V', window='W', monkeypatch=monkeypatch)(None)
    assert got == {'value': 'V', 'window': 'W'}


def test_a_command_wanting_the_choice_but_NOT_a_window(monkeypatch):
    """Passing `window=` to something without that parameter is the same
    failure in a different costume."""
    got = []
    built(lambda value: got.append(value), choice='V', window='W',
          monkeypatch=monkeypatch)(None)
    assert got == ['V'], 'the window must be dropped, not forced'


# ─── Shapes the inspection has to survive ───────────────────────────────────

def test_bound_methods_are_measured_without_their_self(monkeypatch):
    """`inspect.signature` of a BOUND method already excludes `self`, which is
    the whole subtlety: the traceback said "takes 1 positional argument but 2
    were given" because `self` was the first."""
    seen = []

    class Task:
        def runcheck(self):
            seen.append('no args')

        def sortselected(self, choice):
            seen.append(choice)

    task = Task()
    built(task.runcheck, choice='V', monkeypatch=monkeypatch)(None)
    built(task.sortselected, choice='V', monkeypatch=monkeypatch)(None)
    assert seen == ['no args', 'V']


def test_star_args_commands_are_given_the_choice(monkeypatch):
    got = []
    built(lambda *a: got.append(a), choice='V', monkeypatch=monkeypatch)(None)
    assert got == [('V',)]


def test_kwargs_commands_accept_a_window(monkeypatch):
    got = {}
    built(lambda value, **kw: got.update(value=value, **kw),
          choice='V', window='W', monkeypatch=monkeypatch)(None)
    assert got == {'value': 'V', 'window': 'W'}


def test_an_uninspectable_callable_behaves_as_before(monkeypatch):
    """A compatibility shim that cannot tell should do what it used to, not
    silently drop an argument. `len` has no python signature."""
    obj = stand_in(len, choice=['a', 'b'])
    assert obj._takes(len, 1) is True


def test_no_command_is_harmless(monkeypatch):
    built(None, choice='V', monkeypatch=monkeypatch)(None)   # must not raise
