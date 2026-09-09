#!/usr/bin/env python3
# coding=UTF-8
"""Headless guards for the audio layer. NO DEVICE, NO GUI, NO PyAudio needed.

Sketchy on purpose (Kent 2026-09-09: "can we draft even sketchy sound
tests?"), and written now because `backend/core/sound.py` is about to have its
audio backend replaced (agenda/pyaudio_to_sounddevice.md). Anything device-
shaped lives in tests/manual/sound_check/ instead — this file is only the part
that can run in CI, on a machine with no sound card at all.

Following tests/README.md's convention for backend/core: frontend-free, and
prefer a real method with a FAKE `self` over building the real object (which
would want a program, a language and a device).
"""
import sys
import types
import pytest

from backend.core import sound


# ─── The absent-backend contract ────────────────────────────────────────────
# This module must import on a machine with no pyaudio at all — half the
# program's imports lead here, and a hard import killed boot on installs where
# pyaudio didn't build (sound.py:13-16). These guard that promise, so a future
# refactor can't quietly make audio mandatory again.

def test_module_imports_without_a_backend():
    """The import above already proves it; this names the reason."""
    assert sound is not None


def test_sound_problems_is_a_list_of_pairs():
    """main.py:618-621 unpacks `for component,error in SOUND_PROBLEMS` AND
    calls `c.startswith(...)` on the first element to decide whether to show
    Linux users package-manager advice. So the SHAPE is load-bearing for a
    user-facing message, not just internal bookkeeping."""
    assert isinstance(sound.SOUND_PROBLEMS, list)
    for entry in sound.SOUND_PROBLEMS:
        assert isinstance(entry, tuple) and len(entry) == 2, entry
        component, error = entry
        assert isinstance(component, str)
        assert isinstance(error, str)


@pytest.mark.skipif(sound.PYAUDIO_OK,
                    reason="a real backend is installed, so the stub is unused")
def test_stub_backend_refuses_clearly():
    """With no backend, AudioInterface's base is a stub whose job is to raise
    something a human can read rather than AttributeError deep in a stream."""
    with pytest.raises(Exception) as caught:
        sound.AudioInterface()
    assert 'not installed' in str(caught.value).lower()


# ─── confirm_audio: one handle, reused ──────────────────────────────────────
# REGRESSION GUARD. Renaming `.pyaudio` to `.audio` (2026-09-09) left
# `hasattr(self.program, 'pyaudio')` behind as a string literal, so the reuse
# check could never match and every call built a FRESH AudioInterface — which
# is exactly the duplicate-handle bug transcriber.py:87-99 documents at
# length (a second handle racing an open stream). Caught before it shipped;
# these keep it caught.

class _FakeProgram:
    pass


def _settings_with(program):
    """A SoundSettings-shaped object carrying only what confirm_audio uses."""
    fake = types.SimpleNamespace(program=program)
    fake.confirm_audio = types.MethodType(
        sound.SoundSettings.confirm_audio, fake)
    return fake


def test_confirm_audio_reuses_an_existing_interface():
    program = _FakeProgram()
    existing = object.__new__(sound.AudioInterface)  # no device touched
    program.audio = existing
    settings = _settings_with(program)

    settings.confirm_audio()

    assert settings.audio is existing, "built a new handle instead of reusing"
    assert program.audio is existing, "replaced the program's handle"


def test_confirm_audio_ignores_a_wrong_type():
    """Anything that isn't an AudioInterface must be replaced, not trusted —
    the isinstance check is what catches a half-initialised or stubbed one."""
    program = _FakeProgram()
    program.audio = "not an interface"
    settings = _settings_with(program)

    if not sound.PYAUDIO_OK:
        with pytest.raises(Exception):
            settings.confirm_audio()   # stub refuses; that is correct
        return
    settings.confirm_audio()
    assert isinstance(settings.audio, sound.AudioInterface)
    assert program.audio is settings.audio, "handle must be shared, not local"


# ─── API surface the rest of the program calls ──────────────────────────────
# Cheap guards in the style of the existing backend/core tests: these are the
# names other modules reach for through the __getattr__ bridges, where a
# rename shows up as a runtime AttributeError rather than an import error.

@pytest.mark.parametrize('name', [
    'confirm_audio',     # tasks/sound.py, tasks/transcribe_glyph.py
    'done_audio',        # tasks/tasks.py (x4), tasks/sound.py (x3)
    'ensure',            # the canonical accessor (sort_buttons relies on it)
    'check_missing_attrs',
    'sethypothetical',
])
def test_soundsettings_keeps_its_public_names(name):
    assert hasattr(sound.SoundSettings, name)


def test_no_pyaudio_named_attributes_remain():
    """The handle is `.audio` now. If a `.pyaudio`-named method comes back,
    the two names will drift and the three-place lookup in
    sort_buttons.py:_playback will start missing again."""
    stale = [n for n in dir(sound.SoundSettings) if 'pyaudio' in n.lower()]
    assert not stale, "stale pyaudio-named members: {}".format(stale)


def test_candidate_formats_and_labels_agree():
    """`sethypothetical` builds the candidate rates/formats to probe and the
    human labels for them. Every candidate format needs a label or the
    settings UI shows a blank; every label needs a candidate or it advertises
    something never probed. (This is where 24-bit gets dropped in the port —
    the test should keep passing, with one fewer entry on both sides.)"""
    fake = types.SimpleNamespace()
    fake.sethypothetical = types.MethodType(
        sound.SoundSettings.sethypothetical, fake)
    if not sound.PYAUDIO_OK:
        pytest.skip("candidate formats are backend constants")
    fake.sethypothetical()
    labels = fake.hypothetical['sample_formats']
    assert labels, "no sample formats offered at all"
    for fmt, label in labels.items():
        assert isinstance(label, str) and label.strip(), fmt
    rates = fake.hypothetical['fss']
    assert rates and all(isinstance(r, int) for r in rates)
