# coding=UTF-8
"""What a finished recording TELLS THE USER.

WHY THESE, AND WHY HERE. The measuring code had unit tests all evening
(2026-09-10) and stayed right. The messages built from it were wrong four
times: a real-rate figure derived from a contaminated estimate ("192000 Hz
really holds only 180000 Hz"), the same arithmetic contradicting itself
("says 96000 Hz but really holds only 96000 Hz"), a rate changed without
being asked, and — the one that mattered most — a muted microphone producing
NO notice at all, because every branch was guarded by `if frames` and a muted
input delivers none.

So these test the notices, not the maths: which one fires, whether any fires,
and that a good take is silent. `_report_take` is called on an instance built
with `__new__`, so no audio device, no file and no Tk are involved.

THE MOST IMPORTANT TEST HERE is the one asserting a healthy take says
NOTHING. A diagnostic that cries wolf gets dismissed, and then the real
warning — your recordings are being gated, your rate is fake — is dismissed
with it.
"""
import sys
import time
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

io_sound = pytest.importorskip('io_put.sound')


class FakeSettings:
    """Records what the take reported back, and never acts on it."""

    def __init__(self):
        self.faked = []
        self.realed = []

    def note_fake_rate(self, rate):
        self.faked.append(rate)
        return None         # notify-only: never returns a new rate

    def note_real_rate(self, rate):
        self.realed.append(rate)


def take(rate=48000, seconds=2.0, peak=0.3, overflows=0, zeros=0,
         zero_run=0, frames=None, blocks=None):
    """A finished SoundFileRecorder, as `_report_take` expects to find it."""
    rec = io_sound.SoundFileRecorder.__new__(io_sound.SoundFileRecorder)
    rec._asked_rate = rate
    rec._t0 = time.perf_counter() - seconds
    rec._frames_in = int(rate * seconds) if frames is None else frames
    rec._peak = peak
    rec._overflows = overflows
    rec._zeros = zeros
    rec._zrun_max = zero_run
    # Empty by default so the SPECTRAL branch is skipped: these tests are
    # about level, gating and dropouts, and rate_is_fake has its own unit
    # tests. A test that exercises everything at once cannot say which part
    # produced the message.
    rec._frames = blocks if blocks is not None else []
    rec.settings = FakeSettings()
    return rec


def notices(rec, monkeypatch):
    """Run the report and return whatever the user would have been shown."""
    shown = []
    monkeypatch.setattr(io_sound, 'notify_user',
                        lambda text, **k: shown.append(text))
    rec._report_take()
    return shown


# ─── A good take must be quiet ──────────────────────────────────────────────

def test_a_healthy_take_says_nothing_at_all(monkeypatch):
    """THE LOAD-BEARING TEST. Every other notice here is worth having only
    while this one holds: a warning that appears after ordinary recordings
    trains the user to dismiss all of them."""
    assert notices(take(), monkeypatch) == []


def test_a_healthy_take_reports_its_rate_as_fine(monkeypatch):
    """And it should say so to the settings, so an earlier 'upsampled' mark
    can be withdrawn — the graph rate changes underneath us."""
    rec = take()
    notices(rec, monkeypatch)
    assert rec.settings.faked == []


# ─── The muted microphone: no frames, and it used to say nothing ────────────

def test_a_take_with_no_frames_says_the_input_is_muted(monkeypatch):
    """Kent, 2026-09-10: "mic muted doesn't register a recording at all, as I
    think we asked it to." It didn't: every test in `_report_take` was
    guarded by `if frames`, so the one case most likely to leave a user with
    nothing was the one case that produced no message."""
    shown = notices(take(frames=0), monkeypatch)
    assert shown, "a take that received nothing must say so"
    assert 'muted' in shown[0].lower()


def test_no_frames_is_distinguished_from_a_quiet_room(monkeypatch):
    """"Nothing arrived" and "the room was quiet" need different actions —
    check the mute button versus move the microphone closer."""
    nothing = notices(take(frames=0), monkeypatch)[0]
    quiet = notices(take(peak=0.0001), monkeypatch)[0]
    assert nothing != quiet
    assert 'not even silence' in nothing.lower()


# ─── Level ──────────────────────────────────────────────────────────────────

def test_a_silent_take_is_reported(monkeypatch):
    """A file of digital silence passes `file_ok`, which checks only SIZE, so
    without this the take is filed as good and found weeks later."""
    shown = notices(take(peak=0.0001), monkeypatch)
    assert shown and 'no sound' in shown[0].lower()


def test_a_very_quiet_take_is_reported_but_not_as_silence(monkeypatch):
    shown = notices(take(peak=0.005), monkeypatch)
    assert shown
    assert 'quiet' in shown[0].lower()


def test_a_normal_level_is_not_complained_about(monkeypatch):
    for level in (0.05, 0.3, 0.8):
        assert notices(take(peak=level), monkeypatch) == [], \
            '{} of full scale is a fine recording'.format(level)


# ─── Dropouts and gating: the same symptom, different causes ────────────────

def test_dropped_samples_are_reported(monkeypatch):
    shown = notices(take(overflows=3), monkeypatch)
    assert shown and 'missing' in shown[0].lower()


def test_a_long_run_of_exact_zeros_is_reported_as_noise_removal(monkeypatch):
    """The USB mic through `default` delivered 13-100% of a quiet capture as
    exact zeros. Analogue audio does not do that; noise suppression does, and
    it removes quiet speech first."""
    rate = 48000
    shown = notices(take(rate=rate, zeros=rate // 4, zero_run=rate // 4),
                    monkeypatch)
    assert shown
    assert 'quiet parts' in shown[0].lower()


def test_zeros_WITH_overflows_are_blamed_on_dropouts_instead(monkeypatch):
    """Same silence, different cause, different fix — and the overflow count
    is what separates them: a gate does not overflow the input."""
    rate = 48000
    shown = notices(take(rate=rate, zeros=rate // 4, zero_run=rate // 4,
                         overflows=2), monkeypatch)
    assert shown
    assert 'quiet parts' not in shown[0].lower(), \
        'with overflows present this is a dropout, not noise removal'


def test_a_few_zero_samples_are_not_worth_a_warning(monkeypatch):
    """24 samples at 192 kHz is 0.125 ms — a real take showed exactly that
    and must not be flagged."""
    assert notices(take(rate=192000, zeros=24, zero_run=24),
                   monkeypatch) == []


# ─── One take, one message ──────────────────────────────────────────────────

def test_several_problems_arrive_as_one_notice(monkeypatch):
    """Five separate popups about one recording is noise, and noise gets
    dismissed; they are collected into a single message."""
    shown = notices(take(peak=0.001, overflows=2), monkeypatch)
    assert len(shown) == 1
    assert shown[0].count('*') >= 2, 'both problems should be listed'


def test_a_broken_notifier_never_costs_the_recording(monkeypatch):
    """The take is already written by this point. A diagnostic that raises
    must not take the user's audio down with it."""
    def explode(text, **k):
        raise RuntimeError('no UI here')
    monkeypatch.setattr(io_sound, 'notify_user', explode)
    take(peak=0.0001)._report_take()        # must not raise


def test_report_take_does_nothing_when_start_never_ran(monkeypatch):
    """`stop()` can be called on a recorder that never opened a stream."""
    rec = io_sound.SoundFileRecorder.__new__(io_sound.SoundFileRecorder)
    shown = []
    monkeypatch.setattr(io_sound, 'notify_user',
                        lambda text, **k: shown.append(text))
    rec._report_take()
    assert shown == []
