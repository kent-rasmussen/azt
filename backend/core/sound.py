"""Headless backend for audio device settings, the audio handle, ASR state,
and recording-task filename helpers.

This module holds *runtime* audio state (device enumeration, format
validation, ASR kwargs). Persistent user config lives in ``settings/audio.py``
(``AudioConfig``) — the two are intentionally separate.
"""
import copy
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


def rate_is_real(block, rate, margin_db=60.0):
    """Is `block` GENUINELY sampled at `rate`? True / False / None (unknown).

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
    log.info("rate check at %d Hz: top of band %.0f dB below the mid band "
             "(real needs better than -%.0f)", rate, margin, margin_db)
    return margin > -margin_db


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
            sounddevice.query_devices()
            return True
        except Exception as e:
            log.info("audio interface is not usable ({})".format(e))
            return False

    def devices(self):
        """[{'index','name','in','out','rate'}] for every device, or []."""
        out = []
        try:
            for i, d in enumerate(sounddevice.query_devices()):
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

    def default_out(self):
        self.audio_card_out = [k for k, v in self.cards['dict'].items()
                               if k in self.cards['out']
                               if 'default' in v]
        if self.audio_card_out:
            self.audio_card_out = self.audio_card_out[0]
        else:
            self.audio_card_out = min(self.cards['out'])

    # Verified rates, cached for the session, keyed by device NAME.
    #
    # By name and not index because indices are renumbered by the sound server
    # between runs — and even the name is only as stable as the hardware: on
    # 2026-09-10 'sof-hda-dsp: - (hw:0,6)' denoted a USB microphone that
    # vanished from the list when a headset was plugged in. So a miss is a
    # normal outcome, never an error, and we simply measure again.
    _verified_fs = {}

    def _device_name(self, index):
        try:
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
        for rate in sorted(self.cards['in'][self.audio_card_in], reverse=True):
            fmt = widest(self.cards['in'][self.audio_card_in].get(rate) or [])
            if not fmt:
                continue
            try:
                block = sounddevice.rec(int(rate * seconds), samplerate=rate,
                                        channels=1, dtype=fmt,
                                        device=self.audio_card_in,
                                        blocking=True)
            except Exception as e:
                log.info("rate check: %d Hz wouldn't record (%s)", rate, e)
                continue
            verdict = rate_is_real(block, rate)
            if verdict:
                best = rate
                break
            if verdict is None:
                log.info("rate check: %d Hz — too quiet to judge; not using "
                         "it as verified", rate)
            else:
                log.warning("rate check: %d Hz is UPSAMPLED on this input; "
                            "not offering it as the default", rate)
        if name:
            self._verified_fs[name] = best
        return best

    def default_fs(self):
        """The rate to use: the highest VERIFIED one, else a safe fallback.

        The fallback is deliberately NOT `max()` of the accepted rates any
        more. When measurement cannot decide (a silent room, no numpy, no
        backend), 48000 is the honest guess: it is what typical laptop codecs
        and a stock PipeWire graph actually run at, so it is the rate least
        likely to be silently resampled. `max()` picked the most likely to be.
        """
        measured = self.measured_fs()       # cache only; never records here
        if measured:
            log.info("audio settings: using %d Hz, verified by recording",
                     measured)
            self.fs = measured
            return
        available = (self.cards['in'][self.audio_card_in]
                     if self.audio_card_in in self.cards['in']
                     else self.cards['out'][self.audio_card_out])
        if 48000 in available:
            log.info("audio settings: no rate verified; using 48000 Hz, the "
                     "rate least likely to be resampled")
            self.fs = 48000
        else:
            self.fs = max(available)
            log.info("audio settings: no rate verified and no 48000 Hz "
                     "offered; falling back to %d Hz", self.fs)

    def verify_fs(self):
        """Measure what this input really delivers and adopt it. (rate, msg)

        The user action behind "check this microphone" — the one place that
        pays the recording cost. Returns the verified rate and a sentence to
        show, or (None, reason) when the room was too quiet to judge.
        """
        before = self.fs
        best = self.measured_fs(measure=True)
        if not best:
            return None, _("A-Z+T could not tell which sample rates are real "
                           "on this microphone, because the room was too "
                           "quiet while it checked. Try again with some "
                           "ordinary background sound, or just speak while "
                           "it runs.")
        self.fs = best
        offered = max(self.cards['in'][self.audio_card_in]) \
                  if self.audio_card_in in self.cards['in'] else best
        if best < offered:
            return best, _("This microphone really records at {best} Hz. It "
                           "offers {offered} Hz, but that is stretched from a "
                           "lower rate — the file would be larger with no "
                           "more detail in it. A-Z+T will use {best} Hz."
                           ).format(best=best, offered=offered)
        return best, _("This microphone really records at {best} Hz, the "
                       "highest it offers. A-Z+T will use it.").format(
                            best=best)

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

    def next_card_in(self):
        nxt = self._next_card('in', getattr(self, 'audio_card_in', None))
        if nxt is None:
            return 1
        self.audio_card_in = nxt
        self.default_fs()
        self.default_sf()

    def next_card_out(self):
        nxt = self._next_card('out', getattr(self, 'audio_card_out', None))
        if nxt is None:
            return 1
        self.audio_card_out = nxt

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

    def check_missing_attrs(self, include_input=False):
        """Return True if any required setting is missing or invalid."""
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
