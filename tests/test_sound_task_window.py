# coding=UTF-8
"""There is ONE Sound Card Settings window.

Kent, 2026-09-11: "apparently I can have multiple sound settings windows open
at the same time?" Both routes to it — the context menu (`_configure_sound`)
and the automatic one (`mikecheck`) — constructed a window unconditionally,
with nothing to notice an existing one.

Duplicate clutter is the mild half. The window WITHDRAWS the task window on
open and reveals it on close, so with two open the first close hands the task
window back while the second is still up. And both views read the SAME
settings object, so a change made in one leaves the other showing stale
values.

`Sound._sound_settings_window` is a plain method, so these call it on a
stand-in `self`: no display, no audio, no pywebview.
"""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

tasks_sound = pytest.importorskip('tasks.sound',
                                  reason='needs the task mixin importable')


class FakeWindow:
    """A settings window that can report itself alive, dead or destroyed."""

    def __init__(self, alive=True, exists=True):
        self._exists = alive
        self._winfo_exists = exists
        self.shown = 0
        self.lifted = 0
        self.exitFlag = types.SimpleNamespace(istrue=lambda: not alive)

    def winfo_exists(self):
        return self._winfo_exists

    def deiconify(self):
        self.shown += 1

    def lift(self):
        self.lifted += 1


def task_stand_in(existing=None):
    stand_in = types.SimpleNamespace()
    if existing is not None:
        stand_in.soundsettingswindow = existing
    made = []
    stand_in._made = made
    stand_in._sound_settings_window = types.MethodType(
        tasks_sound.Sound._sound_settings_window, stand_in)
    return stand_in


def patched(monkeypatch, stand_in):
    """Count constructions instead of making a real window."""
    def build(task):
        w = FakeWindow()
        stand_in._made.append(w)
        return w
    monkeypatch.setattr(tasks_sound.sound_ui, 'SoundSettingsWindow', build)


def test_an_open_window_is_REVEALED_not_rebuilt(monkeypatch):
    open_one = FakeWindow()
    stand_in = task_stand_in(existing=open_one)
    patched(monkeypatch, stand_in)
    got = stand_in._sound_settings_window()
    assert got is open_one, 'the window already open is the one to use'
    assert not stand_in._made, 'a second window must not be constructed'
    assert open_one.shown == 1, 'and it must be brought to the front'
    assert open_one.lifted == 1


def test_the_first_call_builds_one(monkeypatch):
    stand_in = task_stand_in()
    patched(monkeypatch, stand_in)
    got = stand_in._sound_settings_window()
    assert len(stand_in._made) == 1
    assert got is stand_in._made[0]
    assert stand_in.soundsettingswindow is got, \
        'it has to be remembered, or the next call builds another'


def test_a_DESTROYED_window_is_replaced(monkeypatch):
    """`mikecheck` destroys the window when it finishes, so the remembered
    reference goes stale — a later visit must build a fresh one rather than
    try to reveal a dead window."""
    dead = FakeWindow(exists=False)
    stand_in = task_stand_in(existing=dead)
    patched(monkeypatch, stand_in)
    got = stand_in._sound_settings_window()
    assert len(stand_in._made) == 1, 'a destroyed window must be replaced'
    assert got is not dead


def test_a_QUIT_window_is_replaced(monkeypatch):
    """Closed but not yet destroyed: `exitFlag` is the app's own signal that a
    window is finished with."""
    quit_one = FakeWindow(alive=False)
    stand_in = task_stand_in(existing=quit_one)
    patched(monkeypatch, stand_in)
    stand_in._sound_settings_window()
    assert len(stand_in._made) == 1


def test_a_window_that_raises_on_inspection_is_replaced(monkeypatch):
    """Never let a broken reference stop the user reaching the screen they
    asked for — this is the window people open BECAUSE sound has gone wrong."""
    class Hostile:
        _exists = True
        exitFlag = types.SimpleNamespace(istrue=lambda: False)

        def winfo_exists(self):
            raise RuntimeError('gone')

    stand_in = task_stand_in(existing=Hostile())
    patched(monkeypatch, stand_in)
    stand_in._sound_settings_window()
    assert len(stand_in._made) == 1


def test_both_routes_go_through_the_accessor():
    """Read from source: `_configure_sound` (context menu) and `mikecheck`
    (automatic) must not construct the window directly, or the guard above is
    bypassed by whichever one does."""
    import ast
    src = (Path(__file__).resolve().parents[1] / 'tasks' / 'sound.py')
    tree = ast.parse(src.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in ('_configure_sound', 'mikecheck'):
            continue
        for call in ast.walk(node):
            if not isinstance(call, ast.Call):
                continue
            func = call.func
            name = getattr(func, 'attr', None) or getattr(func, 'id', None)
            assert name != 'SoundSettingsWindow', \
                "{} builds the window directly; use _sound_settings_window" \
                "".format(node.name)
