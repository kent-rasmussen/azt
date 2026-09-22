# coding=UTF-8
"""The two faults behind the Sort Tone no-window-at-all (Kent, 2026-09-22).

From the log: the user clicked a tone group, `makewindow` created its run
window hidden and withdrew the task window, and then

  1. the run window's cover failed — `could not cover the run window while
     it builds (AttributeError("'TranscribeT' object has no attribute
     'RUNWINDOW_DEFAULT_MSG'"))` — so the cover's `thenshow` never revealed it.
     `RUNWINDOW_DEFAULT_MSG` had become the method `_runwindow_default_msg`
     and one caller still named the attribute; the except-and-log hid it on
     every task for six days;
  2. the handler died — `'TranscribeT' object has no attribute
     'soundsettings'` — because under webview the audio probe runs beside the
     UI and had six seconds still to go. tkinter blocks on that probe, so the
     attribute always existed there. The segmental glyph helper already
     tolerated this; the tone `makewindow` did not.

Nothing was left to reveal anything. These pin both.
"""
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SHELL = (ROOT / 'frontend' / 'ui_shell.py').read_text()
TASKS = (ROOT / 'tasks' / 'tasks.py').read_text()


def test_nothing_names_the_retired_class_attribute():
    assert 'RUNWINDOW_DEFAULT_MSG' not in SHELL, \
        "the default message is a METHOD (translation runs at call time); " \
        "a caller naming the old attribute raises on every run window"
    assert '_runwindow_default_msg()' in SHELL


def test_the_tone_makewindow_does_not_read_soundsettings_bare():
    start = TASKS.index('def makewindow(self')
    body = TASKS[start:start + 4000]
    assert 'soundsettings=self.soundsettings' not in body, \
        "read it through sound_settings_for(); the probe may not have run"


glyph = pytest.importorskip('tasks.transcribe_glyph',
                            reason='needs the tasks package importable')


def test_sound_settings_for_prefers_what_the_task_holds():
    held = object()
    task = types.SimpleNamespace(soundsettings=held)
    program = types.SimpleNamespace(nosound=False)
    assert glyph.sound_settings_for(program, task) is held


def test_sound_settings_for_is_none_when_there_is_no_sound():
    task = types.SimpleNamespace()               # probe not finished: no attribute
    program = types.SimpleNamespace(nosound=True)
    assert glyph.sound_settings_for(program, task) is None


def test_sound_settings_for_never_raises(monkeypatch):
    """`SoundSettings.ensure` may fail for a hundred audio reasons; a rename
    window without tone beeps is still a rename window."""
    task = types.SimpleNamespace()
    program = types.SimpleNamespace(nosound=False, languages=None)
    import backend.core.sound as sound

    def boom(*a, **k):
        raise RuntimeError('no audio today')
    monkeypatch.setattr(sound.SoundSettings, 'ensure', boom)
    assert glyph.sound_settings_for(program, task) is None


def test_sound_settings_for_never_probes_on_the_click(monkeypatch):
    """The first version called `ensure` here and so ran the seven-second
    device probe inside the click, under a wait page that read as broken
    (Kent: "Wow; that took forever"). Now: published or None, nothing else."""
    import backend.core.sound as sound
    monkeypatch.setattr(sound.SoundSettings, 'ensure',
                        classmethod(lambda cls, *a, **k: pytest.fail(
                            'ensure (the probe) must not run on the click')))
    program = types.SimpleNamespace(nosound=False,
                                    settings=types.SimpleNamespace())
    assert glyph.sound_settings_for(program, types.SimpleNamespace()) is None


def test_when_ready_calls_back_at_once_when_published():
    held = object()
    program = types.SimpleNamespace(
        nosound=False, settings=types.SimpleNamespace(soundsettings=held))
    got = []
    assert glyph.sound_settings_when_ready(program, types.SimpleNamespace(),
                                           got.append) is None
    assert got == [held]


def test_when_ready_fetches_off_the_caller(monkeypatch):
    """Nothing published: a thread asks `ensure` (which shares one
    construction with a probe the task may already be running) and hands
    the result to the callback. The caller is not blocked."""
    import backend.core.sound as sound
    made = object()
    monkeypatch.setattr(sound.SoundSettings, 'ensure',
                        classmethod(lambda cls, program, analang_obj=None: made))
    program = types.SimpleNamespace(nosound=False, languages=None,
                                    settings=types.SimpleNamespace())
    got = []
    t = glyph.sound_settings_when_ready(program, types.SimpleNamespace(),
                                        got.append)
    assert t is not None
    t.join(5)
    assert got == [made]


def test_when_ready_does_nothing_without_sound():
    program = types.SimpleNamespace(nosound=True)
    got = []
    assert glyph.sound_settings_when_ready(program, types.SimpleNamespace(),
                                           got.append) is None
    assert got == []


def test_ensure_shares_one_construction_across_threads(monkeypatch):
    """Two callers during the probe must get ONE object. Kent's log,
    2026-09-22: two "Making new soundsettings object" lines two seconds
    apart, then a second probe that took 17.7s under contention."""
    import threading
    import backend.core.sound as sound
    builds = []

    class Fake:
        def __init__(self, program, analang_obj=None):
            builds.append(self)
            import time
            time.sleep(0.05)           # the "probe"

        def load_from_file(self):
            pass
    monkeypatch.setattr(sound.SoundSettings, '__new__',
                        lambda cls, *a, **k: Fake(*a, **k))
    program = types.SimpleNamespace(settings=types.SimpleNamespace())
    results = []
    threads = [threading.Thread(target=lambda: results.append(
                    sound.SoundSettings.ensure(program))) for _ in range(3)]
    for th in threads:
        th.start()
    for th in threads:
        th.join(5)
    assert len(builds) == 1, "three concurrent callers built {} objects".format(len(builds))
    assert len(set(map(id, results))) == 1
