"""Headless backend for audio device settings, the audio handle, ASR state,
and recording-task filename helpers.

This module holds *runtime* audio state (device enumeration, format
validation, ASR kwargs). Persistent user config lives in ``settings/audio.py``
(``AudioConfig``) — the two are intentionally separate.
"""
import contextlib
import copy
import os
import sys
from utilities import file, rx, logsetup
from utilities import utilities as utils
from utilities.i18n import _   # verify_fs() returns text for the user
log = logsetup.getlog(__name__)
# The audio backend and numpy are OPTIONAL app-wide (program['nosound']):
# this module must stay importable without them — its importers are
# everywhere, and a hard import here killed boot on machines where the audio
# library didn't build (2026-07-16). Audio CLASSES fail at USE instead.
SOUND_PROBLEMS = []  # (component, error) — main.py surfaces these LOUDLY
#                      (blocking startup notice): degraded sound must never
#                      be silent in a sound-centric app (Kent 2026-07-16).
#
# ── WHY sounddevice AND NOT PyAudio (ported 2026-09-09) ────────────────────
# PyAudio publishes WINDOWS-ONLY WHEELS, and always has: checked against PyPI
# 2026-09-09, every release from 0.2.8 to 0.2.14 ships win32/win_amd64 and
# nothing else. Linux and macOS therefore always built it from source — which
# is why the Linux installer installs portaudio19-dev — and on a Mac with no
# Xcode tools it cannot be installed AT ANY VERSION. That is not a gap
# awaiting an upload; there was nothing to wait for.
#   sounddevice ships PortAudio INSIDE its wheel for macOS (universal2, so
# Intel and Apple Silicon) and Windows (including arm64), and its wheels are
# `py3-none-*` rather than cp-specific, so a new python needs no new build.
# Linux uses the `py3-none-any` wheel plus the system `libportaudio2` — a
# runtime library, no compiler.
#   The second reason is the one Kent hit: PyAudio's blocking write() can
# WEDGE at high rates, and a wedged stream cannot be closed (PortAudio forbids
# closing mid-write; doing it corrupted the heap, 2026-07-16). The only
# recovery was to abandon the stream and leak its device handle — and eight
# leaks in one session took the sound card away from every other program on
# the machine, Praat included. Probing was measured and does NOT explain it
# (192 kHz/int32 is reported supported), so the model had to go, not the
# settings. See agenda/pyaudio_to_sounddevice.md.
try:
    import sounddevice
    AUDIO_OK = True
except Exception as _e:
    sounddevice = None
    AUDIO_OK = False
    SOUND_PROBLEMS.append(('sounddevice (recording/playback)', str(_e)))
    log.error("sounddevice unavailable ({}); sound features are off. On Linux "
              "this usually means the system PortAudio runtime is missing: "
              "install libportaudio2.".format(_e))
try:
    import numpy
except Exception as _e:
    numpy = None
    SOUND_PROBLEMS.append(('numpy (audio data)', str(_e)))
    log.error(f"numpy unavailable ({_e}); sound/ASR features are off "
              "until it installs.")
try:
    from backend import asr
    log.info("ASR loaded OK")
except Exception as e:
    # ASR pulls in the heavy ML stack (transformers/torch/scipy); damage
    # there (e.g. a numpy version mismatch) must degrade to sound-without-
    # transcription, not kill every importer of the sound stack (it took
    # the whole app down via ui_shell→io_put.sound→here, 2026-07-16).
    asr = None
    SOUND_PROBLEMS.append(('ASR (transcription)', str(e)))
    log.error(f"ASR unavailable ({e}); recording/playback still work, "
              "transcription is off until this is fixed.")

try:
    _
except NameError:
    def _(x):
        return x


# ── Sample formats: named by WIDTH, not by a vendor enum ──────────────────
# PyAudio's constants ran INVERSE to width (paFloat32=1 … paUInt8=32), so
# `min()` selected the widest and `max()` the narrowest — which is how
# `default_sf` came to have two branches that disagreed with each other, and
# `max_sf` came to pick the narrowest thing available. sounddevice takes dtype
# STRINGS, so the enum is gone; this table replaces it and says width out
# loud, so nothing has to know an ordering to be read correctly.
#
# int24 is absent deliberately (Kent 2026-09-09: "no problem. let's use what
# there is"). PortAudio has paInt24 and sounddevice maps 'int24', but numpy
# has no 24-bit dtype, so numpy-based streams cannot carry it; a raw stream
# could, if it ever matters to the acoustics. It IS supported by this
# hardware, so this drops a real capability, not a theoretical one.
#
# float32 is absent deliberately too, and this is the one to be careful with:
# it is sounddevice's DEFAULT dtype for numpy streams, so the path of least
# resistance leads straight into it — and Kent, 2026-09-09: "I think there
# was a bug somewhere that made 32float cause problems, so I stopped short of
# that. But that was some time ago, so may no longer apply." Enabling it is
# its own change with its own test, never a side effect of choosing a default.
SAMPLE_FORMATS = {
    'int32': {'bits': 32, 'label': _('32 bit integer')},
    'int16': {'bits': 16, 'label': _('16 bit integer')},
}
# Reading a config written by the PyAudio era: it stored the constant's
# integer. Without this, an existing install comes back with a sample_format
# that means nothing and no way to tell that is what happened.
_PYAUDIO_FORMAT_INTS = {1: 'float32', 2: 'int32', 4: 'int24', 8: 'int16'}


def format_bits(fmt):
    """Bits per sample of a dtype name, or 0 if we don't offer it. Ranking
    goes through here so 'widest' is a statement about width."""
    return SAMPLE_FORMATS.get(fmt, {}).get('bits', 0)


def widest(formats):
    """The widest of a collection of dtype names. Replaces `min()` over
    PyAudio constants, which did this by accident of their numbering."""
    return max(formats, key=format_bits) if formats else None


def narrowest(formats):
    return min(formats, key=format_bits) if formats else None


def spectral_ceiling(block, rate):
    """The highest frequency in `block` still carrying real energy, in Hz —
    or None when it is too quiet to tell.

    THE ONLY RELIABLE TEST FOR SILENT RESAMPLING, and the reason is worth
    stating because two easier signals both failed first:

      * `check_input_settings()` reports what a device ACCEPTS. A sound server
        accepts everything and converts (measured 2026-09-10: `default` took
        192 kHz while PipeWire ran at 48 kHz).
      * frames-per-second CANNOT see it either. Upsampling delivers exactly
        the rate requested — that is what upsampling is — so a take that
        "implies 192985 Hz" may still be 48 kHz content in a 192 kHz wrapper.
      * a device's own `default_samplerate` is not evidence: the `pipewire`
        node reports 44100 and delivers a genuine 192 kHz (Kent 2026-09-10,
        which is what retired the warning built on it).

    What upsampled audio cannot hide is a spectral cliff: 48 kHz content
    stretched to 192 kHz has NOTHING above 24 kHz, not even noise. So the
    highest frequency above the noise floor gives the real rate away.

    Needs sound to have been recorded — room noise is enough, since the cliff
    shows in the noise floor too. Returns None in silence rather than
    guessing, because "the room was quiet" and "the rate was faked" must never
    be confused.
    """
    if numpy is None or block is None or not len(block):
        return None
    mono = block if getattr(block, 'ndim', 1) == 1 else block[:, 0]
    if mono.dtype.kind == 'i':
        mono = mono.astype('float64') / float(numpy.iinfo(mono.dtype).max)
    else:
        mono = mono.astype('float64')
    if mono.size < 2048 or float(numpy.abs(mono).max()) < 0.0005:
        return None
    n = 1 << int(numpy.floor(numpy.log2(min(mono.size, 65536))))
    mag = numpy.abs(numpy.fft.rfft(mono[:n] * numpy.hanning(n)))
    if mag.max() <= 0:
        return None
    freqs = numpy.fft.rfftfreq(n, 1.0 / float(rate))
    db = 20.0 * numpy.log10(numpy.maximum(mag / mag.max(), 1e-12))
    # Noise floor from the top 5% of the band: in a resampled capture that
    # region holds only the FFT's numerical noise, so anything real stands
    # well clear of it.
    floor = float(numpy.median(db[int(len(db) * 0.95):]))
    above = numpy.nonzero(db > floor + 12.0)[0]
    if not len(above):
        return None
    return float(freqs[above[-1]])


def _mirror_test_abandoned_2026_09_10():
    """Why there is no mirror/imaging detector here, so it is not rebuilt.

    A cheap resampler's images sit ~25 dB down, where a real converter's noise
    also sits, so LEVEL cannot separate them. Images are a reflection of the
    baseband, so SHAPE should — and four attempts failed, each differently:

      1. correlate levels, sampled by interpolation between bins: r=0.03 on a
         synthetic 4x upsample. Interpolating between bins compares different
         bins, and adjacent noise bins are independent.
      2. correlate levels, bin-aligned: r=-0.94 — right place, and unusable.
         ANY monotone spectrum anti-correlates about ANY axis, so an honest
         capture with a rolloff scores the same. |r| would call every
         microphone a resampler.
      3. correlate detrended residuals (fine structure only): killed the
         structured case (no detection) while a FLAT-noise upsample scored
         0.63 — a false positive on the one input the method cannot judge.
      4. and the interpretation was wrong throughout: a 48 kHz source repeats
         every 48 kHz, so it has mirror axes at 24k, 48k AND 72k. An axis does
         not identify the source rate; only the LOWEST one does.

    Each fix was a threshold tuned until one machine came out right, which is
    how a test that only works on one machine gets built. Kent named it:
    "are we making these tests more correct/general, or are we just
    diagnosing my machine?"

    What to do instead, if this is picked up again: get captures from several
    machines and resamplers FIRST, and only then fit a statistic — or find a
    prediction that needs no threshold, as the exact-zero-run detector does.
    Until then `rate_is_real` says "don't know" over the range where a cheap
    resampler would live, which is honest and costs only an unverified rate.
    """


@contextlib.contextmanager
def quiet_probing():
    """Silence PortAudio's C-level stderr while probing devices.

    PortAudio's ALSA host API writes straight to FILE DESCRIPTOR 2 from C, so
    no Python-level redirection reaches it: `contextlib.redirect_stderr`
    swaps `sys.stderr` and the C library never looks at that. The only way is
    to replace the descriptor.

    Worth doing because the noise is not incidental — it buries the answer.
    Each rejected combination prints a four-line trace, so probing produced 24
    lines around one verdict, and one run emitted 21 identical
    "unable to open slave" lines (2026-09-10). A diagnostic nobody can read
    is not much better than one that never ran.

    DELIBERATELY NARROW: wrap only the probing calls, where a failure to open
    is an expected outcome we are measuring rather than an error. Anything
    outside keeps its stderr, so a real crash is still visible.
    """
    if not hasattr(os, 'dup2'):
        yield
        return
    try:
        saved = os.dup(2)
        devnull = os.open(os.devnull, os.O_WRONLY)
    except Exception:
        yield               # if we cannot swap it, noise beats breakage
        return
    try:
        sys.stderr.flush()
        os.dup2(devnull, 2)
        yield
    finally:
        try:
            os.dup2(saved, 2)
        finally:
            for fd in (devnull, saved):
                try:
                    os.close(fd)
                except Exception:
                    pass


def zero_runs(block, carry=0):
    """Exactly-zero samples in `block`. (count, longest_run, trailing_run)

    THE ONE DETECTOR HERE THAT NEEDS NO THRESHOLD FITTED TO ANY MACHINE, and
    the reason is worth stating: analogue audio does not land on exactly zero,
    and certainly not repeatedly. A long run of exact zeros is therefore not
    quiet audio — it is a gate, a mute, or a dropout, on any hardware, in any
    format. Nothing about it is calibrated to a particular card.

    `carry` is the run still open at the end of the previous block, and
    `trailing_run` is the one still open at the end of this one, so a caller
    processing a stream in callback-sized pieces measures runs that cross
    block boundaries. A gate's silence is far longer than one callback, so
    counting within blocks would understate it badly.

    Pure, so it can be tested against known input rather than inferred from a
    log — which is the only way anything here becomes general.
    """
    if numpy is None or block is None or not len(block):
        return 0, carry, carry
    flat = block.reshape(-1) if getattr(block, 'ndim', 1) > 1 else block
    zero = (flat == 0)
    count = int(zero.sum())
    if zero.all():
        run = carry + len(flat)
        return count, run, run
    live = numpy.flatnonzero(~zero)
    longest = carry + int(live[0])
    if len(live) > 1:
        gaps = numpy.diff(live) - 1
        if gaps.size:
            longest = max(longest, int(gaps.max()))
    trailing = len(flat) - 1 - int(live[-1])
    return count, max(longest, trailing), trailing


def rate_is_fake(block, rate, margin_db=100.0):
    """Is `block` PROVABLY not sampled at `rate`? True / None (can't tell).

    NEVER RETURNS FALSE, and that is the finding rather than an omission.
    This was `rate_is_real` and returned True for a capture nothing caught.
    Then the synthetic tests measured the two cases side by side:

        genuine 192 kHz capture (Kent's hardware)   top of band  -25 dB
        48 kHz linearly interpolated to 192 kHz     top of band  -35 dB

    Ten dB apart, from two different sources, with no reason to think the gap
    holds on other hardware. That is an OVERLAP, not a separation, so no
    "this rate is real" verdict is available from level at all — and four
    attempts at a shape-based test that might have separated them failed
    (`_mirror_test_abandoned_2026_09_10`).

    What survives is one-directional and needs no fitted number: a capture
    with essentially NOTHING above some frequency was band-limited, because
    an ADC's noise is broadband and cannot have a hole in it. That is the
    PipeWire case — the one that actually put 4x-size 48 kHz files on this
    machine — and it measures -105 to -142 dB, nowhere near the ambiguous
    range.

    HOW PROVED IS A `True` HERE (Kent asked, 2026-09-10):
      * the physics is sound — a 100 dB hole is not an ADC's noise;
      * it is tested against TWO synthetic band-limited upsamples (2x, 4x)
        and observed on ONE real resampler (PipeWire's). Another resampler
        leaving residue at -90 dB would be missed;
      * the -100 dB threshold sits in a gap seen on ONE machine, between
        -25/-35 (ambiguous) and -105/-142 (fake). Nothing establishes that
        gap elsewhere;
      * **and it is blind in int16** — quantisation noise there is ~48 dB
        higher and broadband, so it fills the hole and the verdict comes back
        None. Asserted in test_int16_hides_upsampling_from_this_detector,
        alongside a pair showing the same content caught in int32 and missed
        in int16. Treat this as an int32 detector.
    So: strong enough to TELL a user their file carries less than it claims;
    thin ground for silently changing a setting they chose.

    Replaces the threshold-over-a-noise-floor logic in `spectral_ceiling` for
    this question, because that logic produces FALSE POSITIVES and did so on
    this project's own hardware: `probe_real_capability.py` called 192 kHz
    REAL on two upsampling devices (2026-09-10). Its floor estimate is taken
    from the top 5% of the band — which in an upsampled capture is exactly
    where the resampler's residue lives, so residue was compared against
    itself and cleared the bar.

    The reliable signal is ABSOLUTE, not relative to a floor. Measured on one
    machine, same microphone, same room:

        genuine 192 kHz capture      top of band  -25 dB vs the mid band
        48 kHz upsampled to 192 kHz  top of band  -105 to -142 dB

    A real converter's noise is broadband, so it fills the top of the band
    within a few tens of dB. What sits 100+ dB down is an interpolator's
    arithmetic. Nothing plausible lies between, which is why one threshold
    separates them with room to spare — and why a MICROPHONE's own rolloff
    (tens of dB) does not trip it.

    Returns None when the capture is too quiet for the comparison to mean
    anything: "the room was silent" must never be reported as "the rate was
    faked".
    """
    if numpy is None or block is None or not len(block):
        return None
    mono = block if getattr(block, 'ndim', 1) == 1 else block[:, 0]
    if mono.dtype.kind == 'i':
        mono = mono.astype('float64') / float(numpy.iinfo(mono.dtype).max)
    else:
        mono = mono.astype('float64')
    if mono.size < 4096:
        return None
    n = 1 << int(numpy.floor(numpy.log2(min(mono.size, 65536))))
    mag = numpy.abs(numpy.fft.rfft(mono[:n] * numpy.hanning(n)))
    freqs = numpy.fft.rfftfreq(n, 1.0 / float(rate))
    nyq = float(rate) / 2.0
    # Top 30% of the band: far enough above any real microphone's rolloff
    # that only converter noise or interpolator residue lives there.
    top = (freqs >= 0.70 * nyq) & (freqs <= nyq)
    mid = (freqs >= 1000.0) & (freqs < 0.20 * nyq)
    if not top.any() or not mid.any():
        return None
    mid_level = float(numpy.median(mag[mid]))
    top_level = float(numpy.median(mag[top]))
    if mid_level <= 0 or mag.max() <= 0:
        return None
    # Too quiet to judge: the mid band must itself be clear of the FFT's own
    # numerical floor, or both medians are noise and their ratio is arbitrary.
    if 20.0 * numpy.log10(mid_level / mag.max()) < -100.0:
        return None
    margin = 20.0 * numpy.log10(max(top_level, 1e-20) / mid_level)
    if margin <= -margin_db:
        log.warning("rate check: %d Hz is FAKE — the top of the band is %.0f "
                    "dB down, which is a hole, not noise. Something upsampled "
                    "this.", rate, margin)
        return True
    log.info("rate check at %d Hz: top of band %.0f dB down. Not band-limited,"
             " so not provably upsampled — but this does NOT prove the rate is"
             " real (a cheap resampler measures about -35 dB here, real "
             "hardware about -25).", rate, margin)
    return None


def quietest_window_db(block, rate, window_ms=200.0):
    """The quietest stretch of `block`, in dBFS — or None if unmeasurable.

    A NOISE FLOOR WITHOUT ASKING FOR SILENCE. The floor is by definition the
    quietest part of a capture, so the quietest window of an ordinary take
    gives one — no prompt, no "be quiet for five seconds", no button. That
    matters because the checks worth having are the ones needing no test
    signal and no instructions to follow or fail (the triage in
    agenda/honest_sound_settings.md), and because the card-switch measurement
    had just finished removing the human from this loop.

    IT IS AN UPPER BOUND, and that is the safe direction: a speaker who never
    paused makes the figure pessimistic, which UNDERSTATES the signal-to-noise
    rather than flattering the microphone.

    Free at both moments A-Z+T already records: the per-take diagnostics have
    the whole take in hand, and the rate check's own short captures are often
    silence anyway (peaks of 0.1-0.7% of full scale in a quiet room, measured
    2026-09-11).

    ON GAIN, since it is the obvious objection: a microphone at high gain
    reads noisier, so this compares takes on one setting rather than ranking
    microphones against each other. Kent, 2026-09-11: "if someone is playing
    with gain, they should certainly know the consequences of that." Quite —
    and the figure is honest about the take in front of it either way.

    dBFS, so -60 is quiet and -20 is not; None when there is nothing to
    measure.
    """
    if numpy is None or block is None or not len(block):
        return None
    mono = block if getattr(block, 'ndim', 1) == 1 else block[:, 0]
    if mono.dtype.kind == 'i':
        mono = mono.astype('float64') / float(numpy.iinfo(mono.dtype).max)
    else:
        mono = mono.astype('float64')
    n = int(float(rate) * float(window_ms) / 1000.0)
    if n < 64 or mono.size < n:
        n = mono.size            # too short to window: use the lot
    if n < 64:
        return None
    windows = mono.size // n
    if windows < 1:
        return None
    trimmed = mono[:windows * n].reshape(windows, n)
    rms = numpy.sqrt(numpy.mean(numpy.square(trimmed), axis=1))
    quietest = float(rms.min())
    if quietest <= 0:
        # Digital silence. Real for a gated path, and `zero_runs` is the
        # detector that says so — do not report -inf dB as a noise floor.
        return None
    return 20.0 * numpy.log10(quietest)


def rate_check_possible(rate):
    """Can the band test address `rate` AT ALL? Structural, not about audio.

    `rate_is_fake` and `top_of_band_db` compare a TOP band (>= 0.70 x Nyquist)
    against a MID band (1000 Hz .. 0.20 x Nyquist). The mid band only EXISTS
    when 1000 < rate/10, i.e. above 10000 Hz. At 8000 Hz the range is
    "at least 1000 Hz and under 800 Hz" — empty — so the function returns None
    for every capture, however loud.

    FOUND BY KENT'S RUN, 2026-09-11: 8000 Hz came back NO SIGNAL on all four
    inputs with peaks of 0.6-0.7% of full scale. Plenty of signal, so "the
    room was quiet" was not it — and NO SIGNAL is documented as "a fact about
    the ROOM, not about the setting", which sent the reader looking in the
    wrong place and suggested making noise, which cannot help.

    Kept as its own question rather than widened: the 1000 Hz floor is there
    to stay clear of rumble and mains hum, and lowering it for 8 kHz would
    change what the detector measures at every rate to fix the one rate
    nobody documents speech at. Saying "this test does not reach 8 kHz" is
    both true and cheap.
    """
    try:
        return float(rate) > 10000.0
    except (TypeError, ValueError):
        return False


def top_of_band_db(block, rate):
    """How far down the top of the band is, in dB — or None if unmeasurable.

    THE NUMBER THE VERDICT IS ACTUALLY BASED ON. `rate_is_fake` computes this
    and only logged it, so every caller that wanted to SHOW evidence reached
    for `spectral_ceiling` instead — the relative metric that produces false
    positives, and whose figures then sat next to verdicts they contradicted:

        RESAMPLED  the top of the band is EMPTY … spectrum reaches 47965 Hz
                   of 48000 possible

    Kent, 2026-09-11: *"'spectrum reaches 47965 Hz of 48000 possible' still in
    LIE"*. The verdict says empty, the figure beside it says full, and both
    came from the same capture — because they came from different detectors.
    THIRD time in one afternoon that the untrustworthy metric leaked into
    output through a path I had not swept.

    So: one number, from the detector that decides. Near 0 dB means the band
    is full to Nyquist; -100 dB or worse is the hole `rate_is_fake` calls
    fake; in between is the ambiguous range where nothing can be claimed
    (about -25 dB for real hardware, about -35 for a cheap resampler, on the
    one machine where both were measured).

    Same blindness as `rate_is_fake`: int16's quantisation noise fills the
    hole, so treat this as an int32 figure.
    """
    if numpy is None or block is None or not len(block):
        return None
    mono = block if getattr(block, 'ndim', 1) == 1 else block[:, 0]
    if mono.dtype.kind == 'i':
        mono = mono.astype('float64') / float(numpy.iinfo(mono.dtype).max)
    else:
        mono = mono.astype('float64')
    if mono.size < 4096:
        return None
    n = 1 << int(numpy.floor(numpy.log2(min(mono.size, 65536))))
    mag = numpy.abs(numpy.fft.rfft(mono[:n] * numpy.hanning(n)))
    freqs = numpy.fft.rfftfreq(n, 1.0 / float(rate))
    nyq = float(rate) / 2.0
    top = (freqs >= 0.70 * nyq) & (freqs <= nyq)
    mid = (freqs >= 1000.0) & (freqs < 0.20 * nyq)
    if not top.any() or not mid.any():
        return None
    mid_level = float(numpy.median(mag[mid]))
    top_level = float(numpy.median(mag[top]))
    if mid_level <= 0 or mag.max() <= 0:
        return None
    if 20.0 * numpy.log10(mid_level / mag.max()) < -100.0:
        return None            # mid band is itself at the FFT's floor
    return 20.0 * numpy.log10(max(top_level, 1e-20) / mid_level)


def migrate_sample_format(stored):
    """A persisted sample_format → a dtype name we can use, or None.

    Accepts what this version writes (a dtype name) and what every earlier
    version wrote (a PyAudio constant). Returns None when it cannot be
    honoured — including int24 and float32, which we no longer offer — so the
    caller falls back to a default rather than opening a stream with a value
    from a vocabulary that no longer exists."""
    if stored in SAMPLE_FORMATS:
        return stored
    name = _PYAUDIO_FORMAT_INTS.get(stored)
    if name in SAMPLE_FORMATS:
        log.info("audio settings: sample format {!r} was stored as a PyAudio "
                 "constant; reading it as {!r}".format(stored, name))
        return name
    if stored is not None:
        log.info("audio settings: stored sample format {!r} is not one A-Z+T "
                 "offers now ({}); falling back to the default".format(
                        stored, ', '.join(sorted(SAMPLE_FORMATS))))
    return None


class AudioInterface(object):
    """The audio backend, as an object A-Z+T can hold and pass around.

    It no longer SUBCLASSES the library: PyAudio's entry point was a class
    (`pyaudio.PyAudio`) and this inherited it, so `program.audio` was itself a
    PortAudio handle. sounddevice is module-level functions with no such
    object, so this becomes a plain holder that names the operations A-Z+T
    needs — which is the better shape anyway: the codebase asked this object
    for `get_format_from_width` purely to find out whether it still worked
    (frontend/sound_ui.py), a trick that only existed because there was no
    honest question to ask. There is now: `usable()`.
    """

    def __init__(self):
        if not AUDIO_OK:
            raise RuntimeError("sounddevice is not installed (sound is off)")
        log.debug("PortAudio: {}".format(
                    getattr(sounddevice, 'get_portaudio_version',
                            lambda: ('?', '?'))()))

    def usable(self):
        """Can this interface still talk to the audio system?

        Replaces `task.audio.get_format_from_width(1)` inside a try, which was
        the old way of asking — an API call chosen for its side effect. A
        device list is the real question, and it is cheap."""
        if not AUDIO_OK:
            return False
        try:
            with quiet_probing():
                sounddevice.query_devices()
            return True
        except Exception as e:
            log.info("audio interface is not usable ({})".format(e))
            return False

    def devices(self):
        """[{'index','name','in','out','rate'}] for every device, or []."""
        out = []
        try:
            # ENUMERATION is where most of the ALSA noise comes from, not the
            # per-combination checks: PortAudio's ALSA backend OPENS each PCM
            # to discover its capabilities, and every `dmix` slave that will
            # not open prints "unable to open slave". Wrapping only
            # `supported()` left that untouched, so the flood continued
            # (2026-09-10).
            with quiet_probing():
                listing = list(enumerate(sounddevice.query_devices()))
            for i, d in listing:
                out.append({'index': i,
                            'name': d.get('name'),
                            'in': d.get('max_input_channels', 0),
                            'out': d.get('max_output_channels', 0),
                            'rate': d.get('default_samplerate')})
        except Exception as e:
            log.error("could not list audio devices ({})".format(e))
        return out

    def supported(self, device, rate, fmt, output, channels=1):
        """Does this device really do this rate and format, in this
        direction? The question `is_format_supported` used to answer — and
        which the old enumeration never actually asked (its caller passed
        test=False, so every device was credited with every candidate)."""
        check = (sounddevice.check_output_settings if output
                 else sounddevice.check_input_settings)
        # A rejection here is an ANSWER, not an error — but PortAudio's ALSA
        # layer prints a four-line C-level trace to fd 2 for each one, so
        # probing buries its own result: 24 lines around one verdict, and 21
        # identical "unable to open slave" lines in another run (2026-09-10).
        # Silenced only around the probe itself; see quiet_probing().
        with quiet_probing():
            try:
                check(device=device, samplerate=float(rate), dtype=fmt,
                      channels=channels)
                return True
            except Exception:
                return False

    def stop(self):
        """Stop anything playing. NOT `terminate()`: there is no handle to
        tear down, and stopping is the operation callers actually wanted."""
        try:
            sounddevice.stop()
        except Exception as e:
            log.info("nothing to stop, or couldn't ({})".format(e))
    done = close = finished = stop


class SoundSettings(object):
    """Runtime audio device and ASR configuration.

    Owns the audio handle, enumerates available cards, validates
    rate/format combinations, and manages ASR kwargs/state. Load/save to
    the settings file is routed through here so device state has a single
    home.
    """

    # Settings that must be valid before playback is usable. Record tasks
    # additionally need ``audio_card_in`` — pass ``include_input=True``.
    required_attrs = ['fs', 'sample_format', 'audio_card_out']

    def test(self, pa):
        # only used from __main__; kept for parity
        import time
        filenameURL = "test_{}_{}_{}.wav".format(self.fs, self.sample_format,
                                                 self.audio_card_in)
        self.print1()
        try:
            from io_put.sound import SoundFileRecorder, SoundFilePlayer
            recorder = SoundFileRecorder(filenameURL, pa, self)
            recorder.start()
            time.sleep(1)
            recorder.stop()
            log.info("Finished recording!")
        except Exception as e:
            log.info("Problem recording! %s ({})".format(e))
            return 1
        player = SoundFilePlayer(filenameURL, pa, self)
        try:
            player.play()
        except Exception as e:
            log.debug("Hey, It didn't work! ({})".format(e))
            return 1

    def print1(self):
        values = []
        for setting in ['audio_card_in', 'sample_format', 'fs', 'audio_card_out']:
            values += [setting, getattr(self, setting)]
        log.info("{}: {}; {}: {}; {}: {}; {}: {}".format(*values))

    def print(self):
        for setting in ['audio_card_in', 'sample_format', 'fs', 'audio_card_out']:
            log.info("{}: {}".format(setting, getattr(self, setting)))

    def default_in(self):
        self.audio_card_in = [k for k, v in self.cards['dict'].items()
                              if k in self.cards['in']
                              if 'default' in v]
        if self.audio_card_in:
            self.audio_card_in = self.audio_card_in[0]
        elif self.cards['in']:
            self.audio_card_in = min(self.cards['in'])
        else:
            log.error("I can't find any input card!")
            raise AttributeError("audio_card_in")
        self._remember_card('audio_card_in')

    def default_out(self):
        self.audio_card_out = [k for k, v in self.cards['dict'].items()
                               if k in self.cards['out']
                               if 'default' in v]
        if self.audio_card_out:
            self.audio_card_out = self.audio_card_out[0]
        else:
            self.audio_card_out = min(self.cards['out'])
        self._remember_card('audio_card_out')

    # Verified rates, cached for the session, keyed by device NAME.
    #
    # By name and not index because indices are renumbered by the sound server
    # between runs — and even the name is only as stable as the hardware: on
    # 2026-09-10 'sof-hda-dsp: - (hw:0,6)' denoted a USB microphone that
    # vanished from the list when a headset was plugged in. So a miss is a
    # normal outcome, never an error, and we simply measure again.
    _verified_fs = {}
    # Rates DISPROVED by a real recording, per device name. Populated by
    # note_fake_rate() from the per-take check, which sees several seconds of
    # actual audio rather than a fraction of a second of probing.
    _fake_rates = {}
    # And rates a real take came back UN-band-limited at, per device name.
    # The positive counterpart, kept separately rather than inferred from
    # `_verified_fs` — that holds one DERIVED value per device and any news
    # about any rate clears it, so a good measurement of one rate used to be
    # erased by a bad one about another (2026-09-11).
    _real_rates = {}

    def _device_name(self, index):
        try:
            with quiet_probing():
                return str(sounddevice.query_devices(index).get('name'))
        except Exception:
            return None

    def measured_fs(self, seconds=0.3, measure=False):
        """The highest rate this input REALLY delivers. None if not known.

        WITHOUT `measure=True` this only READS the session cache and never
        records. That split is deliberate: `default_fs()` is on the startup
        path and in the step-down fallbacks, so probing from there would add
        about a second to every boot and re-probe during a failure recovery.
        Recording belongs to a user action ("check this microphone"), which
        passes measure=True once and populates the cache everything else
        reads.

        WHY MEASURE INSTEAD OF ASK. `default_fs` took `max()` of the rates the
        card ACCEPTS, and on a stock PipeWire desktop that is 192 kHz while
        the graph runs at 48 kHz — so the default A-Z+T chose was the one most
        likely to be a lie, producing files 4x the size with nothing above
        24 kHz in them (measured 2026-09-10, confirmed independently by
        `pw-metadata`: clock.allowed-rates = [ 48000 ]).

        Walks the accepted rates HIGH TO LOW and returns the first one that
        records genuine content at its own Nyquist. Costs one short capture
        per rate tried — a second or two at worst, and only until a rate
        passes, so an honest 192 kHz device costs exactly one capture.

        Needs some sound in the room: room noise is enough, and silence
        returns None rather than a guess.
        """
        if not (AUDIO_OK and numpy is not None):
            return None
        if self.audio_card_in not in self.cards['in']:
            return None
        name = self._device_name(self.audio_card_in)
        if name and name in self._verified_fs:
            return self._verified_fs[name]
        if not measure:
            return None         # cache miss, and we were not asked to record
        best = None
        disproved = self.fake_rates_here()
        for rate in sorted(self.cards['in'][self.audio_card_in], reverse=True):
            if rate in disproved:
                log.info("rate check: %d Hz already failed on a real take "
                         "here; not re-probing it", rate)
                continue
            fmt = widest(self.cards['in'][self.audio_card_in].get(rate) or [])
            if not fmt:
                continue
            block = self._capture_for_check(rate, fmt, seconds)
            if block is None:
                continue
            # THE FLOOR, FREE. These captures exist anyway, and in an ordinary
            # room they ARE silence — peaks of 0.1-0.7% of full scale when
            # this was measured (2026-09-11). So the card switch can report a
            # noise floor without asking the user for anything, which is the
            # second of the two places it comes for nothing (the other is
            # every real take). Kent, 2026-09-11: "If we can report the floor
            # for almost free on switch and take, why not? at least until we
            # see if it buys us much."
            # NEVER FATAL. The floor is a nice-to-have; the rate verdict is
            # load-bearing and decides what the user records at. An extra
            # figure must not be able to take the check down with it.
            try:
                floor = quietest_window_db(block, rate)
            except Exception as e:
                log.debug("couldn't measure the noise floor at %d Hz: %s",
                          rate, e)
                floor = None
            if floor is not None:
                log.info("noise floor on %r at %d Hz: %.0f dBFS (quietest "
                         "part of the rate-check capture; an upper bound, and "
                         "it moves with input gain)",
                         name or '?', rate, floor)
            # "Not provably fake" is the strongest available claim — see
            # rate_is_fake, which cannot certify a rate as real. So this
            # picks the highest rate we could not DISPROVE, which still
            # excludes the case that matters: a band-limited upsample.
            if rate_is_fake(block, rate):
                # NEVER ON ONE READING. This sweep walks the rates back to
                # back, which is exactly the condition that produced a FALSE
                # 'resampled' accusation in the manual prober: PipeWire's
                # graph rate is sticky, so the rate tested immediately before
                # can leak into the next measurement and a path that would
                # rather resample than renegotiate gets blamed for it
                # (agenda/honest_sound_settings.md, finding 2b — 48489 Hz
                # being almost exactly 96k/2 was the giveaway). The prober
                # was fixed with a settle pause and a mandatory retry; this
                # had neither until 2026-09-11.
                #   RESAMPLED is an accusation — it tells a user their device
                # is lying — so it has to repeat before it counts.
                self._settle()
                again = self._capture_for_check(rate, fmt, seconds)
                if again is not None and not rate_is_fake(again, rate):
                    log.info("rate check: %d Hz looked upsampled once and "
                             "clean on a second look after an idle pause; "
                             "not accusing it", rate)
                    self._record_check(name, rate, fake=False)
                    best = rate
                    break
                log.warning("rate check: %d Hz is upsampled on this input "
                            "(twice, with an idle pause between); not "
                            "offering it", rate)
                self._record_check(name, rate, fake=True)
                self._settle()
                continue
            self._record_check(name, rate, fake=False)
            best = rate
            break
        if name:
            self._verified_fs[name] = best
        return best

    # Long enough for a sticky graph rate to be released, short enough that
    # three rates stay inside the wait dialog a user is already watching.
    _SETTLE_SECONDS = 0.4

    def _settle(self):
        """Idle, so the rate just tested cannot leak into the next one."""
        import time
        time.sleep(self._SETTLE_SECONDS)

    def _capture_for_check(self, rate, fmt, seconds):
        """A short recording for the rate check, or None if it wouldn't."""
        try:
            with quiet_probing():
                return sounddevice.rec(int(rate * seconds),
                                       samplerate=rate, channels=1,
                                       dtype=fmt, device=self.audio_card_in,
                                       blocking=True)
        except Exception as e:
            log.info("rate check: %d Hz wouldn't record (%s)", rate, e)
            return None

    def _record_check(self, name, rate, fake):
        """SHARE WHAT THE PROBE FOUND, so the settings screen can show it.

        Kent, 2026-09-11: *"we're checking on load; why not share that with
        the user?"* — and he is right that withholding it was incoherent,
        because `verify_fs`'s own notice already ASSERTS the result in prose
        ("the higher rates were checked and found to be stretched from a
        lower one") while the rate menu, reading the same evidence, said
        nothing. One standard of proof, or none.

        The reason it was withheld was real but is now addressed: this sweep
        had no settle pause and no retry, so its verdicts were not sound
        enough to accuse a device with. Both are in place above, which is the
        same bar the manual prober was held to — so the evidence can be
        shared on the same footing as a real take's.
        """
        if not name:
            return
        if fake:
            self._fake_rates.setdefault(name, set()).add(rate)
            self._real_rates.get(name, set()).discard(rate)
        else:
            self._real_rates.setdefault(name, set()).add(rate)
            self._fake_rates.get(name, set()).discard(rate)

    def default_fs(self):
        """The highest rate not KNOWN to be a resampled fake.

        NOT a fallback to 48000. That was here briefly and Kent rejected it,
        correctly: "I want to know what we can, and pick the best that works,
        and give the user (and thereby us) good information. 'I'm not sure, so
        we're using 48khz' is bad, lazy policy." A guessed default is a guess
        whichever number it picks, and picking a low one hides the question
        instead of answering it.

        So: the highest rate this input offers, minus any that measurement has
        PROVED to be upsampled. Where nothing has been measured yet that is
        `max()` — the best the card claims — and the check runs at the first
        recording task, which is early enough to correct it before real data
        is collected, and reports what it found rather than deciding quietly.
        """
        available = (self.cards['in'][self.audio_card_in]
                     if self.audio_card_in in self.cards['in']
                     else self.cards['out'][self.audio_card_out])
        measured = self.measured_fs()       # cache only; never records here
        if measured:
            log.info("audio settings: using %d Hz — the highest this input "
                     "offers that was not shown to be resampled", measured)
            self.fs = measured
            return
        # Highest offered, minus anything a real take already disproved. That
        # subtraction is what makes this "the best that works" rather than
        # "the best that is claimed".
        disproved = self.fake_rates_here()
        usable = [r for r in available if r not in disproved]
        self.fs = max(usable) if usable else max(available)
        if disproved:
            log.info("audio settings: using %d Hz — the highest offered after "
                     "dropping %s, which real takes showed to be upsampled",
                     self.fs, sorted(disproved))
        else:
            log.info("audio settings: using %d Hz, the highest offered. Not "
                     "checked yet — the first test recording will measure it "
                     "and say so.", self.fs)

    def note_fake_rate(self, rate):
        """Record that a REAL TAKE at `rate` came back band-limited.

        The best evidence available, and it arrives for free. Kent already
        asks users to test a recording in the settings window before
        collecting data ("make sure 'record' and 'Play' work well here,
        before recording real data!") — so the first take on any machine is a
        deliberate test take of several seconds, which is far better material
        than the 0.3 s probe `measured_fs` can afford. Feeding its verdict
        back here means the user's own test does the work, and the rate they
        were offered stops being offered the moment it is disproved.
        """
        name = self._device_name(getattr(self, 'audio_card_in', None))
        if not name:
            return
        known = self._fake_rates.setdefault(name, set())
        if rate in known:
            return
        known.add(rate)
        # Latest evidence wins for THIS rate, as in note_real_rate — a rate
        # that recorded cleanly earlier and is band-limited now is no longer
        # something to tell the user is sound.
        self._real_rates.get(name, set()).discard(rate)
        log.warning("audio settings: %d Hz on %r produced a band-limited "
                    "take, so it is upsampled; it will not be chosen again "
                    "for this device", rate, name)
        # Any cached "highest not-provably-fake" answer was computed without
        # this, so it has to go.
        self._verified_fs.pop(name, None)
        # And RE-PICK NOW. Marking the rate without acting on it would leave
        # the very next take in this session recording at the rate just
        # disproved — the finding has to change what happens, not only what
        # is logged. fileclose() is between takes, so this is a safe moment.
        # NOTIFY, DO NOT SWITCH. This used to re-pick the rate immediately,
        # which was never agreed — Kent: "I thought we weren't dropping the
        # rate for upsampling, just notifying the user?" — and the evening's
        # evidence is all on his side. Automatic switching produced, in
        # order: a nonsense real-rate figure, a self-contradicting notice, a
        # mislabelled file, and a step-down that walked 192000 -> 96000 ->
        # 44100 heading for 8000 Hz, straight past the 48000 the graph
        # actually runs (it steps the RATE and never the FORMAT, and that
        # path will not take int32 at 48000). Four bugs, all in the acting-on
        # -it half, none in the measuring half.
        #   And the finding does not justify the action anyway: "upsampled"
        # is not "bad". A 44100 take resampled from a 48000 graph loses
        # nothing a linguist needs; what it costs is disk space, which is the
        # user's call to make, not ours to make for them mid-session.
        #   The record is still kept: `default_fs` subtracts disproved rates
        # when it RE-DERIVES a default, so a known-fake rate is not offered as
        # a default again. What it will not do is override a rate the user is
        # currently using.
        return None

    def note_real_rate(self, rate):
        """A real take at `rate` came back NOT band-limited — clear the mark.

        LATEST EVIDENCE WINS, and it has to, because what is being measured
        CHANGES. Kent, on two checks disagreeing about 192 kHz on the same
        device (2026-09-10): "if the rate is differ at these two times, one
        would expect a difference. this is why an 'on boot' test isn't the
        same as 'on run', especially in a window whos point is to change
        settings."
          Exactly right, and it makes `note_fake_rate`'s "will not be chosen
        again for this device" too strong: PipeWire renegotiates its graph
        rate, so a rate that was upsampled at one moment can be genuine at
        the next. Recording that moment as a permanent property of the device
        would lock a user out of a rate their hardware had started
        supporting, with no way back short of a restart.
        """
        name = self._device_name(getattr(self, 'audio_card_in', None))
        if not name:
            return
        if rate in self._fake_rates.get(name, set()):
            self._fake_rates[name].discard(rate)
            log.info("audio settings: %d Hz on %r recorded cleanly this time, "
                     "so the earlier 'upsampled' mark is withdrawn", rate,
                     name)
        # KEEP THE POSITIVE EVIDENCE, PER RATE. Until 2026-09-11 a clean take
        # left no record at all — it only withdrew a fake mark — so the
        # settings screen could annotate what was DISPROVED and nothing that
        # had been checked and found sound.
        #   The transient stand-in was `_verified_fs`, which `note_fake_rate`
        # pops (and so does the line below, for the same reason): it holds ONE
        # value per device, "the highest rate not provably fake", so news about
        # ANY rate invalidated it. Kent watched that happen: "I thought I
        # recalled a comment on 44.1, which wasn't there after 192 got one."
        # Exactly so — `verify_fs` had cached 44100, then a 192000 take was
        # marked fake, which cleared the cache and took 44.1's note with it.
        #   192 kHz being upsampled says NOTHING about whether 44.1 kHz
        # records cleanly. They are independent facts about independent rates
        # and are now stored that way, with the same provenance rule as the
        # fake marks: real takes only.
        self._real_rates.setdefault(name, set()).add(rate)
        # `_verified_fs` still goes: it is a DERIVED answer ("the highest that
        # delivers") and this take is new information about the ranking.
        self._verified_fs.pop(name, None)

    def forget_rate_checks(self, why=''):
        """Drop cached rate verdicts. Call when the audio path may have moved.

        A probe result describes the graph AT THE MOMENT IT RAN. Changing the
        card — the whole purpose of the settings window — is exactly when that
        stops being true, so keeping the cache across a card change would
        answer a new question with an old measurement.
        """
        if self._verified_fs or self._fake_rates or self._real_rates:
            log.info("audio settings: forgetting cached rate checks%s — they "
                     "described the audio path as it was", why)
        self._verified_fs.clear()
        self._fake_rates.clear()
        self._real_rates.clear()

    def fake_rates_here(self):
        """Rates already disproved on the current input, by real recordings."""
        name = self._device_name(getattr(self, 'audio_card_in', None))
        return self._fake_rates.get(name, set()) if name else set()

    def real_rates_here(self):
        """Rates a REAL TAKE on the current input recorded un-band-limited.

        NOT "rates proved real" — no such claim is available. `rate_is_fake`
        never returns False (see its docstring): the most that can be said is
        that nothing in the take disproved the rate. The settings screen must
        word it that way too, which is why the label says "not stretched"
        rather than "records cleanly".
        """
        name = self._device_name(getattr(self, 'audio_card_in', None))
        return self._real_rates.get(name, set()) if name else set()

    def verify_fs(self):
        """Measure what this input really delivers and adopt it. (rate, msg)

        The user action behind "check this microphone" — the one place that
        pays the recording cost. Returns the verified rate and a sentence to
        show, or (None, reason) when the room was too quiet to judge.
        """
        before = self.fs
        best = self.measured_fs(measure=True)
        if not best:
            return None, _("A-Z+T could not check the sample rates on this "
                           "microphone — the room was too quiet while it "
                           "tried. Try again with some ordinary background "
                           "sound, or speak while it runs.")
        self.fs = best
        offered = max(self.cards['in'][self.audio_card_in]) \
                  if self.audio_card_in in self.cards['in'] else best
        if best < offered:
            # Says what was actually established: the higher rates were shown
            # to be upsampled. It does NOT claim the chosen one is verified —
            # nothing available can certify that (see rate_is_fake).
            #   "upsampled", not "stretched" — Kent, 2026-09-11: "stretched
            # isn't normally used; let's do 'upsampled'; technical, but
            # precise." One word for one thing, here and in the rate list and
            # in the per-take notice; two names for it would be worse than
            # either.
            return best, _("A-Z+T will record at {best} Hz. This microphone "
                           "offers up to {offered} Hz, but the higher rates "
                           "were checked and found to be upsampled: the files "
                           "would be larger with no more sound in "
                           "them.").format(best=best, offered=offered)
        return best, _("A-Z+T will record at {best} Hz, the highest this "
                       "microphone offers. Nothing suggested it is being "
                       "upsampled.").format(best=best)

    # ── Sample-format choice, by WIDTH and said out loud ─────────────────────
    # PORTED 2026-09-09. What was here ranked PyAudio's constants, whose values
    # run INVERSE to width (paFloat32=1 … paUInt8=32), so `min()` meant widest
    # and `max()` meant narrowest. The consequences were both invisible in the
    # code and visible in the field:
    #   * `default_sf`'s two branches DISAGREED — `min()` (32-bit) when an
    #     input card was set, `max()` (16-bit) when only an output card was. A
    #     split by accident, not by policy.
    #   * `max_sf` used `max()` in both branches: a method named "max" that
    #     selected the NARROWEST format available.
    # A-Z+T wants the widest, for the same reason it wants 192 kHz. Now that
    # ranking goes through `format_bits`, both methods say which end they mean.
    def _formats_here(self):
        """The formats the CHOSEN direction actually offers at self.fs.
        Input wins when there is one, as before: a recording task's format has
        to be one the microphone can produce."""
        if self.audio_card_in in self.cards['in']:
            return self.cards['in'][self.audio_card_in].get(self.fs) or []
        return self.cards['out'][self.audio_card_out].get(self.fs) or []

    def default_sf(self):
        self.sample_format = widest(self._formats_here())

    def max_sf(self):
        """Kept under its old name because callers use it; it now does what
        the name says. It was the narrowest before."""
        self.sample_format = widest(self._formats_here())

    def min_sf(self):
        """The narrowest available — the deliberate fallback, named as one,
        for a caller that wants to trade fidelity for a stream that opens."""
        self.sample_format = narrowest(self._formats_here())

    def defaults(self):
        self.default_out()
        self.default_in()
        self.default_fs()
        self.default_sf()

    # ── "next card" has to cope with a card that ISN'T IN THE LIST ─────────
    # These did `list.index(current)`, which raises when the current card is
    # absent — and absent is a NORMAL state, not a corrupt one:
    # `audio_card_out` is PERSISTED AS AN INDEX, and PortAudio renumbers
    # devices as the sound server changes. A config written when the machine
    # had 11 devices can be read on a day it enumerates 9.
    #   That never fired before the sounddevice port because `getactual`
    # never actually probed (its only caller passed test=False), so
    # everything claimed to support everything and `check()` had no reason to
    # look for another card. With real probing, a stale index takes `check()`
    # straight here, and `ValueError: 10 is not in list` came out of
    # SoundSettings' constructor — killing task creation at startup rather
    # than degrading (Kent, 2026-09-10).
    #   A card we cannot find is exactly the case for starting at the first
    # one, which is what these are for. The proper fix is to persist the
    # device NAME and resolve it at use time; see
    # agenda/pyaudio_to_sounddevice.md.
    def _next_card(self, io, current):
        """The next card after `current` in direction `io`, or None when
        there are no more to try. Starts at the first when `current` is not
        in the list."""
        cards = sorted(self.cards[io].keys())
        if not cards:
            log.error("no %s cards at all; sound is off in that direction", io)
            return None
        try:
            i = cards.index(current)
        except ValueError:
            log.info("%s card %r is not among this machine's %s cards (%s) — "
                     "a saved device index that no longer resolves; starting "
                     "at %r", io, current, io, cards, cards[0])
            return cards[0]
        if i >= len(cards) - 1:
            return None
        return cards[i + 1]

    def _remember_card(self, attr):
        """Record WHICH DEVICE an index currently means.

        Must run at every site that sets a card index, not only at load: a
        stale name would out-vote a fresh index and `resolve_cards()` would
        faithfully drag the setting back to the device the user just moved
        away from.
        """
        index = getattr(self, attr, None)
        label = (self.cards.get('dict') or {}).get(index)
        if label is not None:
            setattr(self, self._CARD_NAMES[attr], str(label))

    def choose_card(self, direction, index):
        """Set the input/output card AND record which device that is.

        THE ONLY SAFE WAY to set a card from outside, and the reason is a bug
        this fix caused: the settings window assigned `audio_card_in` directly
        (three sites in frontend/sound_ui.py), so the stored NAME still held
        the previous device. `resolve_cards()` then did exactly what it is for
        and followed that name back — and since `soundcardlabel()` calls
        `check()`, which calls `resolve_cards()`, merely REDRAWING THE LABEL
        reverted the user's choice. Kent, 2026-09-10: "Couldn't get it to
        stick at pipewire mic", with the log showing "'default' moved from
        index 5 to 6; following the device" immediately after each pick.
          `_remember_card`'s own docstring predicted this ("a stale name would
        out-vote a fresh index") and I wired it into `next_card_*` and
        `default_*` only, missing the path the user actually clicks.
        """
        attr = 'audio_card_in' if direction == 'in' else 'audio_card_out'
        setattr(self, attr, index)
        self._remember_card(attr)
        self.forget_rate_checks(' after choosing a different card')

    def next_card_in(self):
        nxt = self._next_card('in', getattr(self, 'audio_card_in', None))
        if nxt is None:
            return 1
        self.audio_card_in = nxt
        self._remember_card('audio_card_in')
        self.forget_rate_checks(' after changing the microphone')
        self.default_fs()
        self.default_sf()

    def next_card_out(self):
        nxt = self._next_card('out', getattr(self, 'audio_card_out', None))
        if nxt is None:
            return 1
        self.audio_card_out = nxt
        self._remember_card('audio_card_out')
        self.forget_rate_checks(' after changing the speakers')

    # Same `.index()` fragility as the cards had, and for `sample_format` it
    # is not hypothetical: the persisted value used to be a PyAudio CONSTANT
    # (an int) and is now a dtype NAME, so every config written before
    # 2026-09-09 holds something that cannot be in these lists. `fs` has the
    # milder version — a rate the previous card offered and this one does not.
    # Absent means "start from the top", not "crash".
    def _step_down(self, values, current):
        """The next value after `current` in `values` (already ordered widest
        or highest first), or None at the end. Starts at the first when
        `current` is not among them."""
        if not values:
            return None
        try:
            i = values.index(current)
        except ValueError:
            log.info("%r is not one of %s — a saved setting this machine or "
                     "this version can't offer; starting at %r",
                     current, values, values[0])
            return values[0]
        if i >= len(values) - 1:
            return None
        return values[i + 1]

    def next_fs(self):
        rates = sorted((self.cards['in'].get(self.audio_card_in) or {}).keys(),
                       reverse=True)
        nxt = self._step_down(rates, getattr(self, 'fs', None))
        if nxt is None:
            exit = self.next_card_in()
            if exit == False:
                self.default_fs()
            return exit
        self.fs = nxt
        return False

    def next_sf(self):
        formats = sorted((self.cards['in'].get(self.audio_card_in) or {}
                          ).get(self.fs) or [], key=format_bits, reverse=True)
        nxt = self._step_down(formats, getattr(self, 'sample_format', None))
        if nxt is None:
            exit = self.next_fs()
            if exit == False:
                self.default_sf()
            return exit
        self.sample_format = nxt
        return False

    def next(self):
        return self.next_sf()

    def getactual(self, test=True):
        """Build `self.cards` — what each device REALLY does, per direction.

        `test` now defaults to TRUE, and that is the substance of this change
        rather than a tidy-up. It defaulted to False and its only caller
        passed nothing, so `is_format_supported` was NEVER called on the live
        path: every `except` was dead code and every device was credited with
        every candidate rate and format. `self.cards` was a copy of
        `hypothetical` wearing the name of a measurement, and the defaults —
        `max()` of the rates, widest of the formats — were chosen from it.
        That is how playback came to open 192 kHz/32-bit streams on whatever
        device happened to be default.

        MEASURED before deciding (Kent: "set a test to time the difference in
        probing sound cards"; tests/manual/sound_check/time_card_probe.py):
        real probing costs **~1.26s** on his box and rejects **33%** of what
        the old table claimed — two whole card/direction entries, plus 28 kHz
        and 8 kHz on the sof-hda-dsp outputs and hdmi. Decision, his: probe
        for real at startup. 1.3s is affordable; it just must not be invisible,
        so the caller runs it behind the splash's progress bar.

        `test=False` is kept ONLY so the timing harness can still measure the
        difference. Nothing in the app should pass it.

        Note what this does NOT fix: 192 kHz with int32 is *accepted* by every
        output here, so probing never would have prevented the playback wedge.
        That was the PyAudio blocking-write model, and it is why this module
        now uses sounddevice.
        """
        import time as _time
        started = _time.perf_counter()
        self.cards = {'in': {}, 'out': {}, 'dict': {}}
        # Noise suppression lives in `devices()` and `supported()`, which are
        # the only calls here that touch PortAudio — wrapping this method as
        # well would just nest the same thing.
        for dev in self.audio.devices():
            i = dev['index']
            if dev['in'] > 0:
                self.cards['in'][i] = {}
            if dev['out'] > 0:
                self.cards['out'][i] = {}
            self.cards['dict'][i] = dev['name']
        probes = 0
        for io, is_output in (('in', False), ('out', True)):
            for card in list(self.cards[io]):
                self.cards[io][card] = {}
                for fs in self.hypothetical['fss']:
                    keep = []
                    for fmt in self.hypothetical['sample_formats']:
                        if test:
                            probes += 1
                            # A device that refuses — or that hangs its own
                            # probe and raises — costs us THAT COMBINATION,
                            # never the enumeration and never startup.
                            if not self.audio.supported(card, fs, fmt,
                                                        output=is_output):
                                continue
                        keep.append(fmt)
                    if keep:
                        self.cards[io][card][fs] = keep
                if not self.cards[io][card]:
                    del self.cards[io][card]
        log.info("audio devices probed in {:.2f}s ({} checks): {} input, {} "
                 "output configurations usable".format(
                        _time.perf_counter() - started, probes,
                        len(self.cards['in']), len(self.cards['out'])))

    def printactuals(self):
        for io in ['in', 'out']:
            for card in self.cards[io]:
                log.debug("{} {} ({}):".format(io, self.cards['dict'][card],
                                               card))
                for fs in self.cards[io][card]:
                    for sf in self.cards[io][card][fs]:
                        log.debug('\t{}_{}'.format(self.hypothetical['fss'][fs],
                                  self.hypothetical['sample_formats'][sf]))

    # DELETED with the port: `sample_format_numpy()`. It mapped PyAudio
    # constants to numpy dtypes and was called from NOWHERE in the codebase —
    # and could not have worked if it had been, because it built its dict at
    # call time and `numpy.int24` does not exist, so it raised AttributeError
    # for EVERY format, not just 24-bit. sounddevice takes the dtype name
    # directly, so nothing needs the mapping.

    def sethypothetical(self):
        self.hypothetical = {}
        self.hypothetical['fss'] = {192000: '192khz',
                                    96000: '96khz',
                                    44100: '44.1khz',
                                    28000: '28khz',
                                    8000: '8khz'}
        # Keyed by dtype NAME now, from the one table that also carries the
        # width (SAMPLE_FORMATS, module level). 192 kHz stays at the top of
        # the rate list on purpose — "192khz should be used, where available"
        # (Kent 2026-09-09) — and `default_fs`'s max() is what implements
        # that, now that the probe below makes "available" mean something.
        self.hypothetical['sample_formats'] = {
            name: spec['label'] for name, spec in SAMPLE_FORMATS.items()}

    def _migrate_stored_format(self):
        """Turn a PyAudio-era `sample_format` into a dtype name, in place.

        Every audio.json written before 2026-09-09 stored the PyAudio
        CONSTANT (paInt32 is the integer 2); it is a dtype NAME now.

        CALLED FROM BOTH `makedefaultifnot` AND `check`, and it has to be:
        settings are also restored from file straight onto this object
        (settings/__init__.py), which reaches `check()` without passing
        through the constructor's validation. Doing it only in
        `makedefaultifnot` meant `check()` ran first with the raw integer,
        found that no device supports "192000 Hz / 2" — because 2 is not a
        dtype — and walked every card rejecting all of them before the value
        was ever translated (Kent 2026-09-10).

        Idempotent: a value already in SAMPLE_FORMATS is left alone.
        """
        stored = getattr(self, 'sample_format', None)
        if stored is None or stored in SAMPLE_FORMATS:
            return
        migrated = migrate_sample_format(stored)
        if migrated is None:
            try:
                del self.sample_format   # let default_sf() choose
            except AttributeError:
                pass
        else:
            self.sample_format = migrated

    def makedefaultifnot(self):
        self._migrate_stored_format()
        if (not hasattr(self, 'audio_card_out')
                or self.audio_card_out not in self.cards['out']
                or self.audio_card_out not in self.cards['dict']):
            self.default_out()
        if (not hasattr(self, 'audio_card_in')
                or self.audio_card_in not in self.cards['in']
                or self.audio_card_in not in self.cards['dict']):
            self.default_in()
        if (not hasattr(self, 'fs') or
                ((self.audio_card_in not in self.cards['in'] or
                  self.fs not in self.cards['in'][self.audio_card_in]) and
                 self.fs not in self.cards['out'][self.audio_card_out])):
            self.default_fs()
        if (not hasattr(self, 'sample_format') or
                ((self.audio_card_in not in self.cards['in'] or
                  self.fs not in self.cards['in'][self.audio_card_in] or
                  self.sample_format not in self.cards['in'][self.audio_card_in][self.fs])
                 and self.sample_format not in self.cards['out'][self.audio_card_out][self.fs])):
            self.default_sf()

    def check(self):
        # PORTED 2026-09-09. This used `is_format_supported` and then decided
        # what to do by MATCHING THE TEXT of PyAudio's ValueError ('Device
        # unavailable', 'Invalid sample rate') — a translated-string
        # dependency of the kind this suite bans elsewhere on principle, and
        # one that silently stopped recovering if a message was ever reworded.
        # sounddevice raises PortAudioError, whose text is no more stable, so
        # the reason is inferred from OUR OWN retries instead: try the next
        # card, then the next format, then give up. Each step is a fact we
        # established, not a string we recognised.
        #
        # FIRST make sure what we are about to ask about is askable: a
        # restored-from-file sample_format can still be a PyAudio integer, and
        # asking a device to support "2" fails for every device, which reads
        # in the log as hardware trouble rather than a stale setting.
        # And BEFORE that, make sure the card indices point where they were
        # chosen to point. `check()` steps the rate and format down against
        # `self.cards[...][index]`, so a renumbered index would have it
        # negotiating against the WRONG DEVICE's capabilities and "fixing"
        # settings that were never broken. Idempotent, so calling it here and
        # in check_missing_attrs costs nothing.
        self.resolve_cards()
        self._migrate_stored_format()
        if getattr(self, 'sample_format', None) is None:
            self.default_sf()
        if not self.audio.supported(self.audio_card_out, self.fs,
                                    self.sample_format, output=True):
            log.info("output card {} can't do {} Hz / {}; trying the next one"
                     "".format(self.audio_card_out, self.fs,
                               self.sample_format))
            if not self.next_card_out():
                self.check()
            return
        if not self.audio.supported(self.audio_card_in, self.fs,
                                    self.sample_format, output=False):
            log.info("input card {} can't do {} Hz / {}; trying the next card, "
                     "then the next format".format(self.audio_card_in, self.fs,
                                                   self.sample_format))
            if not self.next_card_in():
                self.check()
            elif not self.next_sf():
                self.check()

    def initial_ASR_kwargs(self, language_object):
        log.info("setting initial_ASR_kwargs")
        try:
            langs = language_object.supported_ancestor_codes_prioritized()
        except Exception as e:
            log.info(f"Exception: {e}")
            langs = ['en']
        self.asr_repos = {}
        self.asr_kwargs = {'sister_languages': langs}
        log.info(f"Done with initial self.asr_kwargs: {self.asr_kwargs}")

    def reload_ASR(self):
        self.get_changed_kwargs()
        self.asr.load_models_by_kwarg(**self.changed_kwargs['repos'])
        self.asr.load_postprocess_by_kwarg(**self.asr_kwargs)

    def load_ASR(self):
        """Only do this if there is no ASR; reload above."""
        if asr is None:
            log.info("ASR module unavailable; not loading models.")
            return
        try:
            assert isinstance(self.asr, asr.ASRtoText)
            self.reload_ASR()
            log.info("ASR reloaded")
        except (AssertionError, AttributeError) as e:
            log.info(f"Loading ASR ({e})")
            self.asr = asr.ASRtoText(self.program, **self.asr_kwargs)
            self.asr_kwargs = copy.deepcopy(self.asr.kwarg_defaults)
            log.info("ASR loaded")

    def tally_asr_repo(self, reponame):
        log.info(f"{self.asr_repos=} ({type(self.asr_repos)})")
        utils.setnesteddictval(self.asr_repos, 1, reponame, addval=True)

    def asr_repo_tally(self, d=None):
        if d and isinstance(d, dict):
            self.asr_repos = d
        return self.asr_repos

    def top_models_only(self):
        return bool(self.asr_kwargs.get('top_models_only'))

    def set_top_models_only(self, value):
        self.asr_kwargs['top_models_only'] = bool(value)

    def top_asr_keys(self, n=5, cap=20):
        """Draft/repo keys to keep when 'top models only' is on: the top n by
        usage tally, INCLUDING every key tied with the n-th's count, capped at
        cap. Returns None (== no limit) when the toggle is off, or nothing has
        been tallied yet (before any selections, all are 0 — so run everything)."""
        if not self.top_models_only():
            return None
        tally = self.asr_repos or {}
        if not tally:
            return None
        ranked = sorted(tally.items(), key=lambda kv: -(kv[1] or 0))
        threshold = ranked[min(n, len(ranked)) - 1][1] or 0   # n-th place count
        keep = [k for k, c in ranked if (c or 0) >= threshold]
        return set(keep[:cap])

    def asr_kwarg_dict(self, d=None):
        # d omitted -> getter (this is how the settings save calls it, via
        # fndict['asr_kwargs'](); a required arg here raised TypeError mid-save
        # and aborted the whole soundsettings write, so asr_kwargs never persisted).
        if d and isinstance(d, dict):
            self.asr_kwargs = d
        return self.asr_kwargs

    def get_changed_kwargs(self):
        if (asr is None or not hasattr(self, 'asr')
                or not isinstance(self.asr, asr.ASRtoText)):
            return 1
        changed_kwargs = {k: v for k, v in self.asr_kwargs.items()
                          if not hasattr(self.asr, k) or v != getattr(self.asr, k)}
        self.changed_kwargs = {
            'repos': {k: v for k, v in changed_kwargs.items()
                      if k in self.asr.repo_modelnames},
            'postprocess': {k: v for k, v in changed_kwargs.items()
                            if k in self.asr.postprocess_kwargs},
            'sister_languages': (changed_kwargs['sister_languages']
                                 if 'sister_languages' in changed_kwargs else []),
        }
        self.changed_kwargs['all'] = {**self.changed_kwargs['repos'],
                                      **self.changed_kwargs['postprocess'],
                                      'sister_languages': self.changed_kwargs['sister_languages']}

    def file_ok(self, filename):
        if not file.exists(filename):
            return False
        size = file.getsize(filename)
        # The size floor assumes UNCOMPRESSED wav (fs bytes/sec) to reject
        # accidental empty recordings. Compressed imports (.m4a/.aac/.mp3/.ogg —
        # e.g. audio recorded on the phone) are far smaller than that floor, so
        # only apply it to .wav; for other formats accept any non-trivial file.
        if str(filename).lower().endswith('.wav'):
            return size > self.min_audio_file_size()
        return size > 256

    def min_audio_file_size(self):
        return self.fs * self.min_audio_length_ms / 1000

    def confirm_audio(self):
        if (hasattr(self.program, 'audio')
                and isinstance(self.program.audio, AudioInterface)):
            self.audio = self.program.audio
        else:
            self.audio = self.program.audio = AudioInterface()

    # === Absorbed from former ``Sound`` mixin ===

    def done_audio(self):
        """Stop whatever is playing. Was `terminate()`, PyAudio's teardown of
        the handle this object used to BE; sounddevice has no handle, and
        stopping is what every caller wanted (they call this when leaving a
        record page, not when shutting the app down)."""
        try:
            self.audio.stop()
        except Exception:
            log.info("Apparently self.audio doesn't exist, or isn't initialized.")

    # ── Card IDENTITY, because an index is not one ───────────────────────────
    # `check_missing_attrs` validated a stored card by asking whether that
    # INDEX exists in today's device list. That check cannot do its job, and
    # Kent named the reason (2026-09-10): "I think this is unreliable, given
    # the potential shift in card numbers?" It is worse than unreliable — it
    # PASSES while pointing somewhere else. PortAudio renumbers devices as the
    # sound server changes, so index 6 was a USB microphone in one run and
    # 'sysdefault' minutes later. Settings then validate cleanly and describe
    # a different microphone: the rate and format are checked against
    # capabilities that are not the ones being used.
    #   So store the NAME with the index and resolve the name at load. Name
    # matching is not perfect either — the same USB mic disappeared from the
    # list entirely when a headset was plugged in — but a MISS is detectable,
    # where a wrong index is not, and a detected miss can re-derive defaults.
    #
    # Not "re-derive everything every boot" (Kent's fallback suggestion),
    # because that silently discards a deliberate choice: a user who picked a
    # specific microphone would have to pick it again every session, and would
    # not be told it had changed. Resolving by name keeps the choice exactly
    # as long as the choice still exists.
    _CARD_NAMES = {'audio_card_in': 'audio_card_in_name',
                   'audio_card_out': 'audio_card_out_name'}

    def _index_for_name(self, name, direction):
        """Today's index for a remembered device name, or None."""
        if not name:
            return None
        for index, label in (self.cards.get('dict') or {}).items():
            if str(label) == str(name) and index in self.cards.get(direction,
                                                                   {}):
                return index
        return None

    def resolve_cards(self):
        """Re-point stored card indices at the devices they were chosen AS.

        Three outcomes per card, all of them normal:
          * the name still resolves, to the same index -> nothing to do
          * it resolves to a DIFFERENT index -> follow the device, and say so
          * it does not resolve -> drop the setting, so defaults re-derive
        """
        for attr, name_attr in self._CARD_NAMES.items():
            direction = 'in' if attr.endswith('_in') else 'out'
            name = getattr(self, name_attr, None)
            index = getattr(self, attr, None)
            if not name:
                # MIGRATION: settings written before names were stored.
                #
                # Do NOT adopt whatever the old index points at today. The
                # first version did, and Kent's machine then reported
                # "'hdmi' moved from index 6 to 7; following the device" for
                # an output he had never chosen: the stored index was already
                # stale, and canonicalising it into a name made a transient
                # error PERMANENT — and worse than before, since a bad index
                # used to be re-derived once it failed validation, where a bad
                # NAME is now followed faithfully wherever it goes.
                #   The premise of this whole change is that an index is not
                # identity. That applies to the migration too: an index we
                # cannot vouch for is not evidence of a choice, so drop it and
                # let the defaults be re-derived and remembered properly.
                if index is not None:
                    log.info("audio settings: %s was stored as index %s with "
                             "no record of which device that was; choosing a "
                             "default rather than trusting it", attr, index)
                    try:
                        delattr(self, attr)
                    except AttributeError:
                        pass
                continue
            found = self._index_for_name(name, direction)
            if found is None:
                log.warning("audio settings: %s was %r, which is not present "
                            "now — choosing a default instead of trusting "
                            "index %s, which today means something else",
                            attr, name, index)
                for gone in (attr, name_attr):
                    try:
                        delattr(self, gone)
                    except AttributeError:
                        pass
            elif found != index:
                log.info("audio settings: %r moved from index %s to %s; "
                         "following the device", name, index, found)
                setattr(self, attr, found)

    def check_missing_attrs(self, include_input=False):
        """Return True if any required setting is missing or invalid."""
        self.resolve_cards()
        attrs = list(self.required_attrs)
        if include_input:
            attrs = ['audio_card_in'] + attrs
        for s in attrs:
            if hasattr(self, s):
                if s + 's' in self.hypothetical and (
                        getattr(self, s) not in self.hypothetical[s + 's']):
                    log.info(f"Sound setting {s} invalid; asking again")
                    return True
                elif 'audio_card' in s and (
                        getattr(self, s) not in self.cards['dict']):
                    log.info(f"Sound setting {s} invalid; asking again")
                    return True
            else:
                log.info(f"Missing sound setting {s}; asking again")
                return True
        return False

    def soundcheck(self, include_input=False):
        """Revalidate format against hardware, then check required attrs.
        Returns True if a mic-check UI pass is needed.
        """
        self.check()
        return self.check_missing_attrs(include_input=include_input)

    def load_from_file(self):
        """Pull persisted values in through the Settings file loader."""
        self.program.settings.loadsettingsfile(setting='soundsettings')
        if self.program.hostname == 'karlap' and (
                'cache_dir' not in self.asr_kwargs):
            self.asr_kwargs['cache_dir'] = '/media/kentr/hfcache'

    def store_to_file(self):
        """Persist values out through the Settings file writer."""
        self.program.settings.storesettingsfile(setting='soundsettings')

    @classmethod
    def ensure(cls, program, analang_obj=None):
        """Return ``program.soundsettings``, creating and loading it if
        missing. Idempotent; safe to call from every sound-using task.
        """
        ss = getattr(program.settings, 'soundsettings', None)
        if ss is None:
            log.info("Making new soundsettings object")
            ss = cls(program, analang_obj=analang_obj)
            program.settings.soundsettings = ss
            program.soundsettings = ss
            ss.load_from_file()
        elif not hasattr(program, 'soundsettings'):
            program.soundsettings = ss
        return ss

    def __init__(self, program, audio=None, analang_obj=None):
        # `audio` is ACCEPTED AND IGNORED, as `pyaudio` was before it: the
        # handle comes from confirm_audio() below, which reuses program.audio
        # so there is exactly one. Kept in the signature because callers pass
        # it positionally — including one that passes an audio handle where
        # `program` belongs (frontend/transcriber.py:87-99 documents that
        # trap), which this parameter's existence is what made survivable.
        self.program = program
        self.confirm_audio()
        self.sethypothetical()
        self.getactual()
        self.makedefaultifnot()
        # Exclude accidental recordings: 44.8 kHz @ 1 s = 14.6 k
        self.min_audio_length_ms = 500
        # bulk-ASR visibility (Kent 2026-07-14): which model/language units
        # the current/last bulk run still has to do and has done. Persisted
        # as a top-level audio.json key; updated live by tasks/bulk_asr.py.
        self.asr_in_process = {'todo': [], 'done': []}
        # SET BEFORE THE TRY, so the attributes exist on every path.
        # `initial_ASR_kwargs` is what created `asr_kwargs`, and it only runs
        # when `backend.asr` imported — so on a machine with no torch the
        # attribute never existed at all, and the first reader crashed:
        #
        #   tasks/sound.py:153 in setcontext
        #     label = ("Transcribe with all ASR models" if ss.top_models_only()
        #   AttributeError: 'SoundSettings' object has no attribute 'asr_kwargs'
        #
        # on an Intel Mac where torch CANNOT be installed, taking out the
        # Sound Settings menu — a recording feature — because a TRANSCRIPTION
        # engine was missing (Kent, 2026-09-11). Degrading means the optional
        # part goes quiet, not that the object comes out half-built.
        self.asr_kwargs = {}
        self.asr_repos = {}
        try:
            assert 'backend.asr' in sys.modules, "ASR module not loaded"
            self.initial_ASR_kwargs(analang_obj)
            self.asrOK = True
        except (Exception, AssertionError) as e:
            log.error("Exception loading ASR: {}".format(e))
            self.asrOK = False
        self.check()
        self.chunk = 1024
        self.channels = 1


class Record(object):
    """Headless mixin for recording-task filename/node logic.

    Depends on the task having ``self.program``, ``self.analang``, and
    ``self.glosslangs``. Audio device state is reached via
    ``self.program.soundsettings``.
    """

    def audioURL(self, relfilename):
        return str(file.getdiredurl(self.program.settings.audiodir, relfilename))

    def audioexists(self, relfilename):
        return file.exists(self.audioURL(relfilename))

    def hassoundfile(self, node, recheck=False):
        return node.hassoundfile(recheck)

    def filenameoptions(self, node):
        ps = self.program.slices.ps()
        if ps:
            pslocopts = [ps]
        else:
            pslocopts = []
        profile = self.program.slices.profile()
        if ps and profile:
            pslocopts.insert(0, ps + '_' + profile)
        fieldlocopts = [None]
        try:
            l = node.locationvalue()
            pslocopts.insert(0, ps + '-' + l)
            fieldlocopts.append(l)
        except AttributeError:
            pass
        if not pslocopts:
            pslocopts = [None]
        filenames = []
        form = node.textvaluebylang(self.analang)
        if not form:
            log.error("filenameoptions: no {ana} analang in "
                      "{id}!".format(ana=self.analang, id=node.sense.id))
        for pslocopt in pslocopts:
            for fieldlocopt in fieldlocopts:
                for legacy in ['_', None]:
                    for tags in [None, 1]:
                        args = [node.sense.id]
                        if tags:
                            args += [node.tag]
                            if node.tag == 'field':
                                args += [node.ftype]
                        args += [form]
                        for l in self.glosslangs:
                            args += [node.glossbylang(l)]
                        optargs = args[:]
                        optargs.insert(0, pslocopt)
                        optargs.insert(3, fieldlocopt)
                        wavfilename = '_'.join([x for x in optargs if x])
                        if legacy == '_':
                            wavfilename += '_'
                        wavfilename = rx.urlok(wavfilename)
                        filenames += [wavfilename + '.wav']
        return filenames

    def makeaudiofilename(self, node):
        if self.hassoundfile(node):
            return
        filenames = self.filenameoptions(node)
        for f in filenames:
            if self.audioexists(f):
                node.textvaluebylang(lang=self.program.params.audiolang(), value=f)
                break
        f = filenames[-1]
        node.audiofilenametoput = f
        node.audiofileURL = self.audioURL(f)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
