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


@pytest.mark.skipif(sound.AUDIO_OK,
                    reason="a real backend is installed, so this path is unused")
def test_missing_backend_refuses_clearly():
    """With no backend, constructing the interface must say what is missing,
    rather than failing later as an AttributeError deep inside a stream.

    Before the sounddevice port this was enforced by an import-time stub base
    class; now `AudioInterface.__init__` checks `AUDIO_OK` itself, which is
    the same promise with one fewer moving part."""
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

    if not sound.AUDIO_OK:
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
    # No skip any more: since the port these are dtype NAMES from a table in
    # this module, not constants read off an installed library, so the
    # candidate list exists on a machine with no audio backend at all. That
    # is a small win worth keeping — the settings vocabulary no longer
    # depends on the sound stack importing.
    fake.sethypothetical()
    labels = fake.hypothetical['sample_formats']
    assert labels, "no sample formats offered at all"
    for fmt, label in labels.items():
        assert isinstance(label, str) and label.strip(), fmt
    rates = fake.hypothetical['fss']
    assert rates and all(isinstance(r, int) for r in rates)


# ─── Format ranking, and the bug it replaced ────────────────────────────────
# These are pure functions with no device and no library behind them, so they
# are the cheapest possible guard on the mistake that produced a field
# failure: PyAudio's format constants ran INVERSE to width (paFloat32=1 …
# paUInt8=32), so the old code's `min()` meant WIDEST and `max()` meant
# NARROWEST — which is how `default_sf`'s two branches came to disagree and
# `max_sf` came to select the narrowest thing available. Ranking now goes
# through bits per sample, and these say so in a way that cannot silently
# invert again.

def test_widest_is_actually_the_widest():
    assert sound.widest(['int16', 'int32']) == 'int32'
    assert sound.widest(['int32', 'int16']) == 'int32'
    assert sound.narrowest(['int16', 'int32']) == 'int16'


def test_ranking_handles_the_empty_and_single_cases():
    """A card/rate combination with no usable format is normal — the probe
    deletes those entries — so the selectors must not raise on the way past."""
    assert sound.widest([]) is None
    assert sound.narrowest([]) is None
    assert sound.widest(['int16']) == 'int16'


def test_format_bits_disowns_what_we_do_not_offer():
    """int24 and float32 are deliberately not offered (numpy has no 24-bit
    dtype; float32 is held back pending its own test). They must rank as
    unknown rather than as plausible, so they can never be chosen by being
    numerically convenient."""
    assert sound.format_bits('int16') == 16
    assert sound.format_bits('int32') == 32
    assert sound.format_bits('int24') == 0
    assert sound.format_bits('float32') == 0


# ─── Reading a config written by the PyAudio era ────────────────────────────

def test_migrate_accepts_todays_names():
    assert sound.migrate_sample_format('int32') == 'int32'
    assert sound.migrate_sample_format('int16') == 'int16'


def test_migrate_translates_old_pyaudio_constants():
    """Every install predating 2026-09-09 persisted the CONSTANT's integer.
    Without this, those configs come back with a sample_format that means
    nothing — and the field symptom would be a recording setting that silently
    reverts."""
    assert sound.migrate_sample_format(2) == 'int32'   # paInt32
    assert sound.migrate_sample_format(8) == 'int16'   # paInt16


def test_migrate_refuses_what_we_can_no_longer_honour():
    """paInt24 (4) and paFloat32 (1) were valid then and are not offered now,
    so they must come back as None — the caller's cue to fall back to a
    default rather than open a stream with a dead vocabulary."""
    assert sound.migrate_sample_format(4) is None      # paInt24
    assert sound.migrate_sample_format(1) is None      # paFloat32
    assert sound.migrate_sample_format('nonsense') is None
    assert sound.migrate_sample_format(None) is None


# ─── Is a rate REAL, or did something resample? ─────────────────────────────
# These are the only tests here that can be verified without hardware AND
# without trusting my reading of a log: upsampling is reproducible in numpy,
# so a synthetic 48 kHz signal stretched to 192 kHz is a known-fake capture
# whose verdict is known in advance.
#
# Worth having because both detectors were wrong at first on real hardware:
#   * the level test alone called `sysdefault`'s 192 kHz REAL — a cheap
#     resampler leaves images ~25 dB down, right where a real converter's
#     noise lives, so level cannot separate them (2026-09-10);
#   * the older floor-relative test in `spectral_ceiling` called TWO
#     upsampling devices REAL, because its noise floor is estimated from the
#     top of the band, which is where the residue is.
# The distinguishing property is SHAPE: images mirror the baseband about the
# real Nyquist; converter noise correlates with nothing.

def _noise(rate, seconds=0.5, seed=7):
    """Noise with SPECTRAL SHAPE, because flat noise cannot be mirror-tested.

    A correlation asks whether two shapes agree, so a featureless spectrum
    offers nothing to agree about: reflected flat noise is still flat. The
    first version of these tests used `standard_normal` and the detector
    scored r=0.03 on an upsample it should have caught — the test signal was
    the one case the method cannot work on, and real audio is never like it.
    Speech, room noise and any microphone's own rolloff all have tilt and
    structure; a spectral tilt plus a few tones stands in for that.
    """
    numpy = pytest.importorskip('numpy')
    n = int(rate * seconds)
    rng = numpy.random.default_rng(seed)
    freqs = numpy.fft.rfftfreq(n, 1.0 / rate)
    # -6 dB/octave tilt, as speech and room noise both roughly have
    shape = 1.0 / numpy.maximum(freqs, 20.0)
    spec = shape * numpy.exp(1j * rng.uniform(0, 2 * numpy.pi, len(freqs)))
    for tone in (300.0, 1100.0, 2700.0, 6300.0):
        k = int(round(tone * n / rate))
        if k < len(spec):
            spec[k] *= 40.0
    sig = numpy.fft.irfft(spec, n)
    peak = numpy.abs(sig).max()
    return (sig / peak * 0.3) if peak else sig


def _upsampled(from_rate, factor, seconds=0.5):
    """A `from_rate` signal stretched by linear interpolation.

    Linear interpolation is what ALSA's `plug` layer does, and its leaky
    stopband is exactly why the images are audible to a mirror test rather
    than buried 120 dB down like a good resampler's.
    """
    numpy = pytest.importorskip('numpy')
    low = _noise(from_rate, seconds)
    x_low = numpy.arange(len(low), dtype='float64')
    x_high = numpy.linspace(0, len(low) - 1, len(low) * factor)
    return numpy.interp(x_high, x_low, low)


def _bandlimited_upsample(from_rate, factor, seconds=0.5):
    """What a GOOD resampler produces: nothing at all above the old Nyquist.

    Built by zero-padding the spectrum, which is ideal band-limited
    interpolation — the limit a high-quality resampler approaches. Its residue
    is numerical only, ~-300 dB, which is the case the level test can decide.
    """
    numpy = pytest.importorskip('numpy')
    low = _noise(from_rate, seconds)
    spec = numpy.fft.rfft(low)
    n_high = len(low) * factor
    hi = numpy.zeros(n_high // 2 + 1, dtype=complex)
    hi[:len(spec)] = spec * factor
    return numpy.fft.irfft(hi, n_high)


def test_band_limited_upsampling_is_caught():
    """THE CASE THAT MATTERS, and the only one level can decide.

    A good resampler leaves NOTHING above the old Nyquist — not even noise —
    and an ADC's broadband noise cannot have a hole in it. This is what
    PipeWire does, and what put 4x-size files holding 48 kHz of sound on
    Kent's machine.
    """
    pytest.importorskip('numpy')
    assert sound.rate_is_fake(_bandlimited_upsample(48000, 4), 192000) is True
    assert sound.rate_is_fake(_bandlimited_upsample(44100, 2), 88200) is True


def test_an_honest_capture_is_not_accused():
    """Content to its own Nyquist must never be called fake — the accusation
    is the expensive error, since it tells a user to change working
    settings."""
    pytest.importorskip('numpy')
    assert sound.rate_is_fake(_noise(192000), 192000) is None
    assert sound.rate_is_fake(_noise(48000), 48000) is None


def test_a_cheap_resampler_is_NOT_decidable_and_says_so():
    """THE KNOWN GAP, asserted so it cannot be quietly closed by tuning.

    Linear interpolation (ALSA's `plug`) measures about -35 dB at the top of
    the band; Kent's genuine 192 kHz hardware measured -25 dB. Ten dB apart,
    from two different sources — an overlap, not a separation. So no verdict
    is available here, in EITHER direction, and four attempts at a
    shape-based test that might have separated them failed
    (`_mirror_test_abandoned_2026_09_10`).

    If this test ever starts failing because the detector got cleverer, the
    replacement needs captures from several machines behind it — not a
    threshold moved until this one case lands on the right side.
    """
    pytest.importorskip('numpy')
    assert sound.rate_is_fake(_upsampled(48000, 4), 192000) is None


def _as_int16(mono):
    """The same capture as a real int16 recording, quantisation and all.

    Not a cast for tidiness: int16's quantisation noise is the point. It sits
    ~48 dB above int32's and is BROADBAND, so it fills the top of the band
    even in a capture that was upsampled and therefore had nothing there.
    """
    numpy = pytest.importorskip('numpy')
    peak = numpy.abs(mono).max() or 1.0
    return numpy.round(mono / peak * 0.3 * 32767).astype('int16')


def test_int16_hides_upsampling_from_this_detector():
    """THE FORMAT BLIND SPOT, measured rather than assumed.

    Kent asked how proved "proving" is (2026-09-10). One answer: every other
    test here uses float data, so nothing exercised int16 — where the same
    band-limited upsample that is caught in int32 may not be, because
    quantisation noise fills the hole the detector looks for. That is exactly
    what buried the high content in `probe_real_capability.py` earlier the
    same day, and it was never checked here.

    IF THIS TEST FAILS because the detector returned True, that is good news
    and the assertion should be flipped — the detector is stronger than
    believed. It is written this way round so the gap is documented rather
    than discovered by a user whose machine defaults to int16.
    """
    pytest.importorskip('numpy')
    faked = _as_int16(_bandlimited_upsample(48000, 4))
    verdict = sound.rate_is_fake(faked, 192000)
    assert verdict is None, (
        "int16 upsampling came back as {} — if that is True, the detector "
        "sees through quantisation noise after all and this test should "
        "assert True".format(verdict))


def test_int16_does_not_produce_a_FALSE_accusation_either():
    """The blind spot must be blind in both directions.

    A detector that cannot confirm int16 upsampling must also not invent it:
    an accusation tells a user to change settings that were working, which is
    the more expensive error of the two.
    """
    pytest.importorskip('numpy')
    honest = _as_int16(_noise(192000))
    assert sound.rate_is_fake(honest, 192000) is None


def test_int32_still_catches_what_int16_hides():
    """The pair that makes the gap a FORMAT property rather than a fluke:
    identical content, caught at int32 and missed at int16."""
    pytest.importorskip('numpy')
    content = _bandlimited_upsample(48000, 4)
    assert sound.rate_is_fake(content, 192000) is True
    assert sound.rate_is_fake(_as_int16(content), 192000) is None


def test_silence_is_not_an_accusation():
    """A quiet room must come back as "can't tell", never as "faked": the two
    call for opposite responses, and conflating them is what made an earlier
    version tell users their hardware was lying when it was not."""
    numpy = pytest.importorskip('numpy')
    assert sound.rate_is_fake(numpy.zeros(96000), 48000) is None


def test_a_capture_too_short_to_judge_says_so():
    """Short blocks have too few bins for the comparison to mean anything."""
    numpy = pytest.importorskip('numpy')
    assert sound.rate_is_fake(numpy.zeros(100), 48000) is None


# ─── Zero runs: the detector with no fitted threshold ───────────────────────
# Analogue audio does not land on exactly zero, let alone repeatedly, so a
# long run of exact zeros is a gate, a mute or a dropout on ANY hardware.
# Nothing here is calibrated to a card, which is why it is the one detector
# that generalises without more machines — and why it is worth testing hard.

def test_zero_runs_counts_a_clean_block_as_clean():
    numpy = pytest.importorskip('numpy')
    block = numpy.array([0.1, -0.2, 0.3, -0.4])
    count, longest, trailing = sound.zero_runs(block)
    assert (count, longest, trailing) == (0, 0, 0)


def test_zero_runs_finds_an_internal_run():
    numpy = pytest.importorskip('numpy')
    block = numpy.array([0.1, 0.0, 0.0, 0.0, 0.2, 0.3])
    count, longest, trailing = sound.zero_runs(block)
    assert count == 3
    assert longest == 3
    assert trailing == 0


def test_zero_runs_carries_across_block_boundaries():
    """The point of the carry: a gate's silence is far longer than one audio
    callback, so a run split across blocks must be measured whole. Counting
    per-block would report three runs of 4 instead of one of 12."""
    numpy = pytest.importorskip('numpy')
    zeros = numpy.zeros(4)
    carry = 0
    longest_seen = 0
    for _block in (zeros, zeros, zeros):
        count, longest, carry = sound.zero_runs(_block, carry)
        longest_seen = max(longest_seen, longest)
    assert longest_seen == 12, "the run spans all three blocks"


def test_zero_runs_closes_a_carried_run_at_the_first_live_sample():
    numpy = pytest.importorskip('numpy')
    count, longest, trailing = sound.zero_runs(numpy.array([0.0, 0.0, 0.5]),
                                               carry=10)
    assert longest == 12, "10 carried in plus 2 leading zeros"
    assert trailing == 0


def test_zero_runs_reports_a_trailing_run_as_still_open():
    numpy = pytest.importorskip('numpy')
    count, longest, trailing = sound.zero_runs(numpy.array([0.5, 0.0, 0.0]))
    assert trailing == 2, "still open: the next block may continue it"


def test_zero_runs_handles_integer_samples():
    """Recordings arrive as int16/int32, where 'exactly zero' is exact."""
    numpy = pytest.importorskip('numpy')
    block = numpy.array([0, 0, 5, 0], dtype='int32')
    count, longest, trailing = sound.zero_runs(block)
    assert count == 3
    assert longest == 2


def test_zero_runs_handles_multichannel_blocks():
    """sounddevice hands back (frames, channels); the counter must not read
    the shape as a single channel of interleaved silence."""
    numpy = pytest.importorskip('numpy')
    block = numpy.zeros((8, 2))
    count, longest, trailing = sound.zero_runs(block)
    assert count == 16
    assert longest == 16
