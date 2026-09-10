#!/usr/bin/env python3
# coding=UTF-8
"""Is this MICROPHONE any good, and what sample rate does it justify?

    cd <azt>
    ../env/bin/python -um tests.manual.sound_check.mic_check --help

WHY, AND HOW THIS DIFFERS FROM probe_real_capability.py
    That script asks whether the PATH is honest — whether a file claiming
    192 kHz really was sampled at 192 kHz. It cannot say whether the
    microphone puts anything useful into that band, and Kent asked the
    obvious next question (2026-09-10): "sounds like we should be running a
    mic check, too, then."

    A-Z+T has a `mikecheck()` already (tasks/sound.py:32) — but it only opens
    the settings window with record and play buttons. The human is the
    instrument: record something, listen, guess. This measures instead.

WHAT IT MEASURES, from three captures: silence, sound, silence
    The SILENT captures are what make the rest trustworthy: they give a real
    noise reference, so "usable bandwidth" means "where sound actually rises
    above this microphone's own noise" rather than "where some threshold I
    invented was crossed".

    There are TWO of them, bracketing the sound, because the first capture of
    a run does not come through the same path as the later ones — measured
    2026-09-10: the first capture arrives resampled from a lower rate, and
    dividing by it invents a flat 9-11 dB of ultrasonic "signal" that no
    microphone produced. The second silence is recorded on the same warmed-up
    path as the sound, moments after it, and the script picks whichever
    silence actually matches. The pair also measures whether the ROOM held
    still (a fan cycling mid-run), which is otherwise a thing a person has to
    remember.

      level        peak and RMS, in % of full scale and dBFS
      clipping     samples pinned at full scale — a ruined recording that
                   looks fine in a file listing
      noise floor  RMS of the silent capture: the mic and preamp's own noise
      SNR          how far the sound rose above that floor
      bandwidth    the highest frequency where sound beats the noise floor by
                   10 dB. THIS is the answer to "what rate is worth using":
                   sampling above twice this number records nothing but noise
      DC offset    a biased input, which wastes headroom and upsets analysis

WHAT IT CANNOT DO
    It is not a calibrated measurement. Absolute levels depend on the mic,
    its gain and the room; the BANDWIDTH figure needs broadband sound to be
    meaningful (speech alone rolls off around 8-10 kHz naturally, so a quiet
    "shhh" or rubbing paper near the mic is a better test signal than talking
    — it has energy everywhere the mic can hear).

Switches (no environment variables; nothing identified by colour):
  --list            List input devices by name, then exit.
  --device=NAME     Input device, BY NAME ('pipewire', 'default'). An index
                    also works but is unreliable: PortAudio's ALSA device
                    numbering shifts between runs, so --device=6 named two
                    different devices minutes apart on 2026-09-10.
                    Default: the system default input.
  --rate=N          Capture rate. THE RATE CAPS THE ANSWER: nothing above
                    N/2 can be seen, so a run at 48000 can never report a mic
                    limit above 24000 Hz. Hence the default is not a fixed
                    number but the HIGHEST of 192000/96000/48000/44100/8000
                    that the chosen device will actually open — 192 kHz where
                    it is available, which on some inputs it is not.
  --format=NAME     dtype: int32 (default) or int16. int32 for measurement:
                    its noise floor is ~48 dB lower, so it can see the mic's
  --quiet-seconds=S Silent capture (default 2.0)
  --loud-seconds=S  Sound capture (default 3.0)
  --countdown=S     Seconds to get ready before each capture (default 5;
                    0 starts immediately)
  --note=TEXT       Record the room conditions in the output ('AC blower on').
                    Worth using: figures are only comparable across runs if
                    what differed between them is written down with them.
                    (--sound-first, a one-day diagnostic switch, is gone: it
                    established that the FIRST capture of a run comes through
                    a resampled path, and the three-capture bracket below now
                    both detects and repairs that on every run.)
  --help            This
"""
import hashlib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def switch(name, default=None):
    for arg in sys.argv[1:]:
        if arg == '--' + name:
            return True
        if arg.startswith('--' + name + '='):
            return arg.split('=', 1)[1]
    return default


if switch('help'):
    print(__doc__)
    sys.exit(0)

try:
    import numpy
    import sounddevice
except Exception as e:
    from tests.manual.sound_check._which_python import how_to_run
    print(how_to_run('tests.manual.sound_check.mic_check',
                     missing='numpy and sounddevice ({})'.format(e)))
    sys.exit(1)

if switch('list'):
    # Names, because indices move. Printed with each device's own reported
    # rate, which is a claim rather than a measurement — the whole point of
    # this script is that those claims need checking.
    print("Input devices (use --device=<name>; names are stable, indices are"
          " not):")
    try:
        for i, d in enumerate(sounddevice.query_devices()):
            if d.get('max_input_channels', 0) > 0:
                print("  [{}] {!r}  (claims {:.0f} Hz)".format(
                        i, d.get('name'), d.get('default_samplerate', 0)))
    except Exception as e:
        print("  couldn't enumerate: {}".format(e))
    sys.exit(0)

DEVICE = switch('device')
if DEVICE is not None:
    # A NAME is the safe way to say which device you mean; an index is not.
    # On 2026-09-10 `--device=6` selected 'pipewire' in one run and
    # 'sysdefault' in another minutes later, because PortAudio enumerates
    # ALSA devices by open-testing them — the set that opens varies, so the
    # numbering shifts under you. sounddevice matches a string against device
    # names, so pass 'pipewire' and get pipewire.
    try:
        DEVICE = int(DEVICE)
    except ValueError:
        pass                       # leave it a string for sounddevice to match
FMT = switch('format', 'int32')
# Rate is chosen below, once we can test the device: see pick_rate().
CANDIDATE_RATES = (192000, 96000, 48000, 44100, 8000)
QUIET_S = float(switch('quiet-seconds', 2.0))
LOUD_S = float(switch('loud-seconds', 3.0))
COUNTDOWN = float(switch('countdown', 5))


def rate_opens(rate):
    """Does this device actually open an input stream at `rate`?

    By opening one, not by asking. `check_input_settings()` reports what a
    device will ACCEPT, and this project has now been burned by that answer in
    both directions (see agenda/honest_sound_settings.md).
    """
    try:
        s = sounddevice.InputStream(samplerate=rate, device=DEVICE,
                                    channels=1, dtype=FMT)
        s.start()
        s.stop()
        s.close()
        return True
    except Exception:
        return False


def pick_rate():
    """Highest candidate rate this device will open. (rate, why)

    Default 48000 was worse than it looked: the capture rate caps what the
    run can see, so a 48 kHz run can only ever conclude "justifies 48000 Hz"
    — the answer was the question. And Kent's policy is 192 kHz where it is
    available (2026-09-10), which is exactly what "where available" needs a
    real test to establish: input [3] on this machine opens ONLY at 48000.

    Opening is not proof the rate is honest — that is what the mic check and
    probe_real_capability.py are for — only that it is worth trying.
    """
    asked = switch('rate')
    if asked:
        return int(asked), 'you asked for it'
    for rate in CANDIDATE_RATES:
        if rate_opens(rate):
            return rate, 'highest of {} that this device would open'.format(
                                '/'.join(str(r) for r in CANDIDATE_RATES))
    return CANDIDATE_RATES[-2], 'nothing opened; trying anyway'


def countdown(instruction, seconds=None):
    """Say what to do, count down, then return so the caller can record.

    A keypress would be worse here than it looks: the hand that presses Enter
    makes a noise on the desk, and that lands in the first moments of the
    capture — in the SILENT capture especially, where it becomes the measured
    noise floor and corrupts every figure derived from it.
    """
    secs = COUNTDOWN if seconds is None else seconds
    print("  " + instruction)
    try:
        n = int(secs)
        while n > 0:
            sys.stdout.write("\r  starting in {}... ".format(n))
            sys.stdout.flush()
            time.sleep(1.0)
            n -= 1
        sys.stdout.write("\r  RECORDING NOW    \n")
        sys.stdout.flush()
    except KeyboardInterrupt:
        print()
        sys.exit(1)


def capture(seconds):
    """Record `seconds`; return (mono float array in -1..1, provenance dict).

    PROVENANCE IS NOT DECORATION. On 2026-09-10 this script reported figures
    identical to the last digit — peak 38.4%, floor -38.3 dBFS, ceiling 23038
    Hz — for a room with the AC blower running and the same room with it off.
    Live audio cannot do that, so either the data was not fresh or the run was
    not fresh, and NOTHING IN THE OUTPUT COULD TELL THE TWO APART. A
    measurement tool that cannot prove it measured is worse than no tool: it
    is a tool that lies confidently, which is the exact failure this whole
    line of work exists to stop.

    So every capture now reports frames, wall-clock duration, the rate those
    two imply, and a digest of the samples. Two runs that produce the same
    digest recorded the same bytes, full stop.
    """
    blocks = []
    over = {'n': 0}
    t0 = time.time()

    def cb(indata, frames, time_info, status):
        if status and getattr(status, 'input_overflow', False):
            over['n'] += 1
        blocks.append(indata.copy())

    try:
        s = sounddevice.InputStream(samplerate=RATE, device=DEVICE,
                                    channels=1, dtype=FMT, callback=cb)
        s.start()
        t0 = time.time()
        time.sleep(seconds)
        s.stop()
        elapsed = time.time() - t0
        s.close()
    except Exception as e:
        print("  couldn't record: {}".format(e))
        return None, None
    if not blocks:
        print("  the stream delivered NO data at all.")
        return None, None
    raw = numpy.concatenate(blocks)
    mono = raw if raw.ndim == 1 else raw[:, 0]
    info = {'over': over['n'], 'frames': len(mono), 'elapsed': elapsed,
            'rate': len(mono) / elapsed if elapsed > 0 else 0,
            # Digest the RAW samples, before any scaling, so it is a
            # fingerprint of what the device handed us and nothing else.
            'digest': hashlib.sha256(mono.tobytes()).hexdigest()[:12]}
    if mono.dtype.kind == 'i':
        full = float(numpy.iinfo(mono.dtype).max)
        return mono.astype('float64') / full, info
    return mono.astype('float64'), info


def say_provenance(label, info):
    print("  {}: {} frames in {:.2f}s = {:.0f} Hz measured, id {}".format(
            label, info['frames'], info['elapsed'], info['rate'],
            info['digest']))
    off = abs(info['rate'] - RATE) / float(RATE)
    if off > 0.05:
        print("     WARNING: asked for {} Hz, got {:.0f} Hz — {:.0f}% off."
              .format(RATE, info['rate'], 100 * off))


def db(x):
    return 20.0 * numpy.log10(max(float(x), 1e-12))


def rms(a):
    return float(numpy.sqrt(numpy.mean(numpy.square(a)))) if len(a) else 0.0


def window_size(*arrays):
    """One FFT size both captures can use.

    Must be shared: the bandwidth test divides one spectrum by the other, so
    they have to have the same number of bins. Deriving n per-array meant a
    short --quiet-seconds silently disabled the measurement.
    """
    shortest = min(len(a) for a in arrays)
    return 1 << int(numpy.floor(numpy.log2(min(shortest, 32768))))


def spectrum(a, rate, n):
    """(freqs, magnitudes) of the average magnitude spectrum."""
    if n < 1024 or len(a) < n:
        return None, None
    # Average several windows so a transient does not dominate.
    mags = []
    step = n // 2
    for start in range(0, max(1, len(a) - n), step):
        seg = a[start:start + n]
        if len(seg) < n:
            break
        mags.append(numpy.abs(numpy.fft.rfft(seg * numpy.hanning(n))))
        if len(mags) >= 24:
            break
    if not mags:
        return None, None
    mag = numpy.mean(mags, axis=0)
    return numpy.fft.rfftfreq(n, 1.0 / rate), mag


def ultrasonic_margin(freqs, mag):
    """How much content a capture has above 24 kHz, relative to 4-24 kHz.

    A SELF-CONTAINED property of one capture: no division by another capture,
    so it cannot be corrupted by the two disagreeing. That is the point — it
    is what identifies WHICH capture is anomalous, where the sound/silence
    ratio can only say that one of them is.

    A capture genuinely sampled at 192 kHz carries converter noise across the
    whole band, so this sits near 0 dB or mildly negative. One upsampled from
    48 kHz has nothing above 24 kHz at all and comes out strongly negative.
    """
    if freqs is None:
        return None
    hi = (freqs >= 24000)
    mid = (freqs >= 4000) & (freqs < 24000)
    if not hi.any() or not mid.any():
        return None
    return db(numpy.median(mag[hi])) - db(numpy.median(mag[mid]))


print('=' * 74)
print("Microphone check — measuring, not guessing")
# Which build of this script ran. Several times on 2026-09-10 a result was
# discussed as though it came from the current code when it came from the
# previous one — the edits and the runs were interleaved. A line that changes
# whenever the file changes settles that without anyone having to remember.
try:
    BUILD = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:8]
except Exception:
    BUILD = '?'
print("  script build {}".format(BUILD))
try:
    info = sounddevice.query_devices(
                DEVICE if DEVICE is not None else None, 'input')
    DEVNAME = info.get('name')
    if DEVICE is None:
        print("  device: '{}' — chosen for you, no --device given".format(
                DEVNAME))
    else:
        print("  device: '{}' — asked for as {!r}".format(DEVNAME, DEVICE))
except Exception as e:
    DEVNAME = '?'
    print("  device: {} (couldn't query: {})".format(DEVICE, e))
NOTE = switch('note') or 'none given'
RATE, RATE_WHY = pick_rate()
print("  capturing at {} Hz as {} — {}".format(RATE, FMT, RATE_WHY))
# The capture rate CAPS what this run can discover: nothing above RATE/2 can
# be seen at all. Saying so up front stops the result from reading as a fact
# about the microphone when it is partly a fact about this switch.
print("  so this run can only see up to {} Hz.".format(int(RATE / 2)))
# --note puts the room conditions INSIDE the output. Without it they live in
# whatever the runs were labelled with afterwards, and on 2026-09-10 I compared
# noise floors across runs as though the room had been constant when the
# annotations said otherwise — blower on in some, off in others. A figure is
# only comparable to another if what differed is recorded next to it.
print("  conditions: {}{}".format(
        NOTE, "" if switch('note') else
        "  (--note='AC blower on' records them)"))
print('=' * 74)

# Settle the path at RATE before the reference capture. The silent capture
# goes FIRST, so without this it is the one most likely to catch the path
# still at some other rate — and it is the one every later figure is divided
# by. Warming up costs a second and removes that asymmetry.
try:
    _warm = sounddevice.InputStream(samplerate=RATE, device=DEVICE,
                                    channels=1, dtype=FMT)
    _warm.start()
    time.sleep(0.8)
    _warm.stop()
    _warm.close()
except Exception:
    pass

def stage_silence(n):
    # "of 2" was left in the format string after the third capture was added,
    # so the callers' "1 of 3" printed as "Stage 1 of 3 of 2" (Kent's Windows
    # run, 2026-09-10). The caller says how many there are; this must not.
    print("\nStage {} — SILENCE. Measures the microphone's own noise."
          .format(n))
    countdown("BE QUIET — no typing, no shifting in your chair — for {:.0f}s."
              .format(QUIET_S))
    data, info = capture(QUIET_S)
    if data is None:
        sys.exit(1)
    say_provenance("silence", info)
    return data, info


def stage_sound(n):
    print("\nStage {} of 2 — SOUND. Measures level, and how much of the band"
          .format(n))
    print("the microphone can actually hear.")
    print("  SIGNAL: a steady \"shhhh\" or paper rubbed near the mic — energy")
    print("  everywhere. Speech rolls off at 8-10 kHz and understates the mic.")
    countdown("MAKE THAT SOUND steadily, close to the mic, for {:.0f}s."
              .format(LOUD_S))
    data, info = capture(LOUD_S)
    if data is None:
        sys.exit(1)
    say_provenance("sound  ", info)
    return data, info


# TWO silences, bracketing the sound. Not belt-and-braces — it answers the
# question a single silence cannot.
#
# Runs on 2026-09-10 showed the ultrasonic bands reading a flat +5 to +12 dB
# "over silence" while the audible bands read +2 dB: impossible for a
# microphone, so the two captures were not coming through the same path. But
# with one silence there is no way to tell WHICH capture is the odd one — the
# silence (a rate-change artifact) or simply whichever ran first (a settling
# artifact). I asked for a --sound-first run twice to find out.
#
# Bracketing settles it in a single run AND repairs the measurement:
#   silence-before differs from silence-after  -> the FIRST capture is odd;
#                                                 use the trailing silence
#   the two silences agree                     -> order is not the cause
# It also gives the only reference that is directly comparable: a silence
# recorded on the same warmed-up path as the sound, moments after it.
quiet, quiet_info = stage_silence('1 of 3')
loud, loud_info = stage_sound('2 of 3')
print("\n  (a second silence follows, recorded on the same warmed-up path —")
print("  it is the reference that can be trusted if the first one cannot)")
quiet2, quiet2_info = stage_silence('3 of 3')

for a, b, what in ((quiet_info, loud_info, 'silence 1 and the sound'),
                   (quiet_info, quiet2_info, 'the two silences')):
    if a['digest'] == b['digest']:
        print("\n  WARNING: {} are identical, byte for byte. Nothing below"
              " is a measurement.".format(what))

# ── Which silence is a valid reference? ───────────────────────────────────
# CONFIRMED by Kent's --sound-first run, 2026-09-10: with order silence,sound
# the ultrasonic bands read a flat +9.3 dB; with order sound,silence they read
# a flat -11.1 dB. The sign follows the ORDER, so in both runs the capture
# that ran FIRST was the one missing its ultrasonic half. The first stream
# after startup comes through a resampled path and the next one does not — a
# settling artifact, not a property of silence, and the 0.8 s warm-up above is
# not enough to prevent it.
#
# Hence: divide by the silence whose own ultrasonic content matches the sound
# capture's. That is a repair, not just a diagnosis.
NFFT = window_size(quiet, loud, quiet2)
fq, mq = spectrum(quiet, RATE, NFFT)
fl, ml = spectrum(loud, RATE, NFFT)
fq2, mq2 = spectrum(quiet2, RATE, NFFT)
mq1 = mq          # kept because `mq` may be reassigned to mq2 below
m_loud = ultrasonic_margin(fl, ml)
m_q1 = ultrasonic_margin(fq, mq)
m_q2 = ultrasonic_margin(fq2, mq2)
# COLLECTED, not printed. This is the evidence that identifies which capture
# is anomalous, so it belongs BELOW the "copy from this line down" marker with
# the rest of the results. Printing it above the marker (build 57f298ff) put
# the single most useful diagnostic outside what got pasted back.
ref_lines = []
reference_note = None
no_valid_reference = False
band_limited = False

# FIRST: is there anything up there AT ALL, in any capture?
#
# This test comes before comparing captures to each other, because it is
# absolute and they are relative — and getting that order wrong cost most of
# an afternoon on 2026-09-10. The three margins came back -122.0, -112.4 and
# -118.3 dB, and I read the ~10 dB DIFFERENCES between them as evidence about
# which capture was anomalous. The differences were noise on top of the real
# finding, which was the magnitude: every capture was ~120 dB empty above
# 24 kHz.
#
# 120 dB down is not sound. A real 192 kHz capture carries converter noise
# 20-40 dB below its audible band, because an ADC's noise is broadband. What
# sits 120 dB down is the numerical residue of an UPSAMPLER — arithmetic, not
# acoustics. So the whole path is running at 48 kHz and interpolating up.
#
# It also explains the flat ultrasonic ratios that misled me: numerator and
# denominator are both residue proportional to their own input level, so the
# ratio is flat across the whole ultrasonic band and equals the broadband
# level difference between the two captures. That is why its SIGN followed
# whichever capture was louder — which in one run happened to correlate with
# capture order, and I concluded the first capture was resampled. It was not:
# they all were.
def audible_level(freqs, mag):
    """dB level of the 4-24 kHz band of one capture."""
    if freqs is None:
        return None
    sel = (freqs >= 4000) & (freqs < 24000)
    return db(numpy.median(mag[sel])) if sel.any() else None


# SECOND band-limit test: does ultrasonic content TRACK THE SIGNAL?
#
# The -40 dB threshold below cannot tell genuine converter noise from a cheap
# resampler's imaging, and that mattered: `sysdefault` came back at -25 dB and
# I reported it as a real 192 kHz path. It is not. ALSA's plug layer
# interpolates with a leaky stopband, leaving artifacts ~25 dB down, where
# PipeWire's high-quality resampler leaves them ~120 dB down. Same fakery,
# different resampler quality — and -25 dB sits comfortably inside the range I
# had called "plausible converter noise".
#
# The physics separates them cleanly:
#   REAL high-rate capture — ultrasonic is the converter's own noise, FIXED,
#     independent of what the microphone hears. So when the audible band rises
#     by 20 dB, the ultrasonic-to-audible margin FALLS by about 20 dB.
#   RESAMPLED — ultrasonic is imaging OF the signal, proportional to it. Both
#     bands rise together and the margin BARELY MOVES.
# On that sysdefault run the margin moved 0.2 dB while the capture went to
# 99.6% peak. That is imaging, and it was visible in data I already had.
a_loud = audible_level(fl, ml)
a_quiet = audible_level(fq, mq1)
if (not band_limited and None not in (m_loud, m_q1, a_loud, a_quiet)
        and a_loud - a_quiet > 10.0 and abs(m_loud - m_q1) < 3.0):
    band_limited = True
    ref_lines.append("  ** THIS RATE IS NOT REAL (resampler imaging) **")
    ref_lines.append("    The audible band rose {:.0f} dB from silence to"
                     " sound, but the".format(a_loud - a_quiet))
    ref_lines.append("    ultrasonic margin moved only {:.1f} dB — so the"
                     " content above".format(abs(m_loud - m_q1)))
    ref_lines.append("    24 kHz TRACKS the signal instead of being fixed"
                     " converter")
    ref_lines.append("    noise. That is a resampler mirroring the audio"
                     " upward, not")
    ref_lines.append("    real sampling. Use --rate=48000 on this device.")

margins = [m for m in (m_q1, m_loud, m_q2) if m is not None]
if not band_limited and margins and max(margins) < -40.0:
    band_limited = True
    ref_lines.append("  ** THIS RATE IS NOT REAL **")
    ref_lines.append("    Above 24 kHz every capture is {:.0f}-{:.0f} dB down"
                     .format(-max(margins), -min(margins)))
    ref_lines.append("    — numerical residue of an upsampler, not sound. A")
    ref_lines.append("    true {} Hz capture would carry converter noise only"
                     .format(RATE))
    ref_lines.append("    20-40 dB down. So this path runs at 48000 Hz and")
    ref_lines.append("    interpolates up: the file would claim {} Hz and"
                     .format(RATE))
    ref_lines.append("    hold nothing above 24000 Hz, at 4x the size.")
    ref_lines.append("    Re-run with --rate=48000 to measure the microphone.")

if not band_limited and None not in (m_loud, m_q1, m_q2):
    ref_lines.append("  ultrasonic per capture (>24 kHz vs 4-24 kHz; each")
    ref_lines.append("  capture on its own, NOT a comparison):")
    ref_lines.append("    silence1 {:+.1f} | sound {:+.1f} | silence2 {:+.1f} dB"
                     .format(m_q1, m_loud, m_q2))
    # Pick the closer silence, THEN require it to be close ENOUGH. Picking the
    # better of two bad references and reporting anyway is what build 57f298ff
    # did: it announced "using silence 2" and still showed a flat +12.3 dB
    # ultrasonic excess. "Better" is not "valid".
    if abs(m_q2 - m_loud) + 1.0 < abs(m_q1 - m_loud):
        quiet, quiet_info, mq = quiet2, quiet2_info, mq2
        chosen, chosen_margin = 'silence2', m_q2
        reference_note = "silence1 mismatched the sound; using silence2"
    else:
        chosen, chosen_margin = 'silence1', m_q1
    gap = abs(chosen_margin - m_loud)
    ref_lines.append("    using {} — differs from the sound capture by {:.1f} dB"
                     .format(chosen, gap))
    if gap > 3.0:
        no_valid_reference = True
        reference_note = ("NO valid reference: closest silence still differs"
                          " {:.1f} dB from the sound".format(gap))
        ref_lines.append("    -> NEITHER silence matches the sound capture, so")
        ref_lines.append("       no valid noise reference exists in this run.")

# Did the ROOM hold still? The two silences bracket the sound, so comparing
# their low-frequency levels measures exactly that — mq1 (kept above) against
# mq2, never the chosen `mq` against itself. Kent's AC blower cycles roughly
# half the time and he offered to run only when it was off and "try to
# remember"; a tool should measure that rather than ask a person to track it.
# A STEADY blower is harmless — it sits in every capture and mostly cancels,
# costing low-frequency sensitivity only. One that switches DURING a run is
# what corrupts the comparison.
if fq is not None and mq1 is not None and mq2 is not None:
    lf = (fq >= 20) & (fq < 1000)
    if lf.any():
        lf_change = db(numpy.median(mq2[lf])) - db(numpy.median(mq1[lf]))
        if abs(lf_change) > 3.0:
            ref_lines.append("    -> ROOM NOISE CHANGED {:+.1f} dB below 1 kHz"
                             " between".format(lf_change))
            ref_lines.append("       the silences — a fan started or stopped."
                             " Low-frequency")
            print("       bandwidth result above 4 kHz is largely unaffected.")

# ── Level and clipping ────────────────────────────────────────────────────
peak = float(numpy.abs(loud).max())
loud_rms = rms(loud)
floor_rms = rms(quiet)
clipped = int(numpy.count_nonzero(numpy.abs(loud) >= 0.999))
dc = float(numpy.mean(loud))

snr = db(loud_rms) - db(floor_rms)
overflows = quiet_info['over'] + loud_info['over']

# Everything needed to interpret or reproduce this run, restated here so the
# results block is self-contained and can be copied on its own — the header
# scrolls away, and a figure without its device, rate, build and conditions
# has repeatedly been read as meaning something it did not.
print('\n' + '=' * 74)
print("mic_check RESULTS — copy from this line down")
print("  {} Hz {} on '{}' | build {} | {}".format(
        RATE, FMT, DEVNAME, BUILD, NOTE))
print("  captures: silence,sound,silence — reference used: {} id {}".format(
        quiet_info['frames'], quiet_info['digest']))
for line in ref_lines:
    print(line)
print("  peak {:.1f}% ({:+.1f} dBFS) | avg {:.1f}% ({:+.1f} dBFS)".format(
        100 * peak, db(peak), 100 * loud_rms, db(loud_rms)))
print("  noise floor {:+.1f} dBFS | SNR {:.0f} dB | clipped {} | DC {:.2f}%{}"
      .format(db(floor_rms), snr, clipped, 100 * dc,
              " | OVERFLOWS {}".format(overflows) if overflows else ""))

# ── Usable bandwidth: where sound beats the noise floor ───────────────────
usable = None
# Set by the validity check below. A detected-bad noise reference must SUPPRESS
# the bandwidth conclusion, not merely be printed above it: build da611418
# announced "THESE FIGURES ARE NOT USABLE" and then reported "usable bandwidth
# up to about 95994 Hz" four lines later, drawn from the reference it had just
# disowned. Anyone skimming for the number gets the wrong answer, endorsed.
reference_bad = False
# When the path is band-limited, everything above its REAL Nyquist is
# upsampler residue — so analyse only the band that carries sound. The run
# then still answers the microphone question, up to 24 kHz, instead of being
# thrown away wholesale.
ANALYSIS_MAX = 24000.0 if band_limited else RATE / 2.0
signal_broadband = True     # defaults: the notes section reads these even
tilt = 0.0                  # when the spectra could not be computed
concentrated = False
max_band = 0.0
if fl is not None and mq is not None:
    with numpy.errstate(divide='ignore', invalid='ignore'):
        ratio = 20.0 * numpy.log10(numpy.maximum(ml, 1e-20)
                                   / numpy.maximum(mq, 1e-20))
    in_band = fl < ANALYSIS_MAX

    # WAS THE TEST SIGNAL BROADBAND? Attributing a low ceiling to the
    # microphone is only valid if there was high-frequency content for it to
    # fail to capture. Build 8462ccdf reported "1119 Hz — so that ceiling is
    # the MICROPHONE. Justifies ~2000 Hz" from a capture whose energy was
    # +10.1 dB at 0-1 kHz and +0.2 dB everywhere above: a thump, not a "shhh".
    # No headset microphone stops at 1.1 kHz, and the script had no business
    # saying one did — it asks for a broadband signal and then trusts that it
    # got one.
    lo_sel = (fl >= 100) & (fl < 1000)
    hi_sel = (fl >= 2000) & (fl < 8000)
    signal_broadband = True
    if lo_sel.any() and hi_sel.any():
        tilt = db(numpy.median(ml[hi_sel])) - db(numpy.median(ml[lo_sel]))
        if tilt < -20.0:
            signal_broadband = False
    # Highest frequency where sound is durably above this mic's own noise.
    #
    # NOT `fl[nonzero(ratio > 10)[-1]]`, which is what this did until
    # 2026-09-10 and which was pure artifact: that takes the single highest of
    # ~16000 noisy bins to clear the threshold, and across that many bins one
    # near the top always does by chance. It reported 21-24 kHz on captures
    # whose every band sat 1-4 dB above silence, and stayed suspiciously
    # steady across runs differing by 25 dB of level — an extreme-value
    # statistic masquerading as a bandwidth. I then read its stability as
    # evidence of a 48 kHz resampler. It was evidence of my own metric.
    #
    # Chunked medians instead: a chunk counts only if MOST of its bins clear
    # the threshold, so a lone spike cannot carry it, and we take the highest
    # chunk that does.
    CHUNK = 64
    ratio_band = ratio[in_band]
    usable_chunks = len(ratio_band) // CHUNK
    if usable_chunks:
        grid = ratio_band[:usable_chunks * CHUNK].reshape(usable_chunks, CHUNK)
        chunk_db = numpy.median(grid, axis=1)
        clear = numpy.nonzero(chunk_db > 10.0)[0]
        if len(clear):
            usable = float(fl[in_band][(clear[-1] + 1) * CHUNK - 1])

    # The single ceiling number cannot distinguish a MICROPHONE rolling off
    # from a RESAMPLER's brick wall, and those call for opposite responses:
    # the first means "a lower rate loses you nothing", the second means "this
    # path is lying about its rate". The shape tells them apart — a mic decays
    # over octaves, a resampler falls off a cliff in one band — so show the
    # shape rather than asking anyone to take the number on faith.
    print("\n  sound over silence, per band ('#' per 2 dB; 5 = real signal){}:"
          .format(" — only to {} Hz, the real Nyquist".format(int(ANALYSIS_MAX))
                  if band_limited else ""))
    edges = [0, 1000, 4000, 8000, 16000, 24000, 32000, 48000, 96000]
    profile = []
    for lo, hi in zip(edges, edges[1:]):
        if lo >= ANALYSIS_MAX:
            break
        sel = (fl >= lo) & (fl < min(hi, ANALYSIS_MAX))
        if not sel.any():
            continue
        band = float(numpy.median(ratio[sel]))
        profile.append((lo, int(min(hi, ANALYSIS_MAX)), band))
        bar = '#' * max(0, min(30, int(round(band / 2.0))))
        print("    {:>6}-{:<6} Hz  {:+5.1f} dB  {}".format(
                lo, int(min(hi, ANALYSIS_MAX)), band, bar))

    # IS THE SIGNAL SPREAD OUT, or packed into a few bins?
    #
    # Broadband RMS and per-band medians must tell the same story. Build
    # 39c0d7e2 reported SNR 23 dB while no band median exceeded +2.2 dB —
    # impossible for a broadband signal, and the tell that the energy was
    # concentrated in a handful of bins (a tone, hum, or a brief transient).
    # Total energy rose 23 dB; every band's MEDIAN barely moved, because a
    # median ignores a few big bins. That is exactly what makes it a good
    # bandwidth statistic and a bad level statistic, so the two must be
    # cross-checked rather than trusted separately.
    #
    # It also fixes bad advice: that run was told to aim for a higher peak and
    # more level when it already had 49% and 23 dB. Level was never the
    # problem.
    max_band = max((p[2] for p in profile), default=0.0)
    concentrated = snr > 10.0 and max_band < snr - 10.0

    # VALIDITY CHECK on the two-capture method itself.
    #
    # The whole design assumes both captures came through the same path. If
    # the sample-rate graph changes between them — PipeWire's rate is sticky,
    # and it was seen switching between the silence stage and the sound stage
    # on 2026-09-10 — then the silent capture is not a noise reference for the
    # sound capture, and dividing them invents signal that no microphone
    # produced. That run showed +0.4..+0.9 dB below 24 kHz and a flat +4.6 dB
    # above it: the silence had been upsampled from 48 kHz (nothing above its
    # 24 kHz Nyquist) while the sound capture ran natively at 192 kHz (real
    # converter noise to 96 kHz).
    #
    # The tell is physically impossible, which is what makes it a good check:
    # a microphone cannot be MORE sensitive ultrasonically than at 1 kHz.
    # Baseline is the UPPER AUDIBLE region (4-24 kHz), not 0-1 kHz. The first
    # version of this check used 0-1 kHz and then failed to fire on exactly
    # the data it was written for: a blower put +7.0 dB into that band, so the
    # baseline was inflated past the threshold. Low frequencies are where room
    # noise lives and where it varies most between two captures — the worst
    # possible reference. 4-24 kHz is where a microphone is already rolling
    # off, so ultrasonic content exceeding it is the impossible part.
    ultra = [p for p in profile if p[0] >= 24000]
    audible_top = [p[2] for p in profile if p[0] >= 4000 and p[1] <= 24000]
    if ultra and audible_top:
        base = float(numpy.median(audible_top))
        ultra_db = [p[2] for p in ultra]
        spread = max(ultra_db) - min(ultra_db)
        louder = float(numpy.median(ultra_db)) - base
        # Two independent tells, either one sufficient:
        #   louder  — ultrasonic above the upper audible range at all
        #   spread  — dead flat across 24-96 kHz, which no mic response is,
        #             but which a constant offset between two paths is
        if louder > 3.0 or (len(ultra) >= 3 and spread < 0.5 and louder > 1.0):
            reference_bad = True
            print("\n  ** BAD NOISE REFERENCE — figures below are void **")
            print("  ultrasonic {:+.1f} dB vs {:+.1f} dB at 4-24 kHz, flat to"
                  " {:.1f} dB.".format(float(numpy.median(ultra_db)), base,
                                       spread))
            print("  No mic hears better above 24 kHz than at 8 kHz: the two")
            print("  captures came through different sample-rate paths.")
            print("  (The ultrasonic-per-capture line above says which.)")

print()
# no_valid_reference (neither silence matched the sound capture) is as fatal
# to the bandwidth figure as the impossible-shape check is.
reference_bad = reference_bad or no_valid_reference
if reference_bad:
    print("  bandwidth: VOID (bad reference; would have said {:.0f} Hz)"
          .format(usable or 0))
elif usable is None:
    print("  bandwidth: CANNOT MEASURE — no band held 10 dB over silence.")
    if concentrated:
        # Level was fine; the signal was just not spread across frequencies.
        print("    Not a level problem: peak {:.1f}%, {:.0f} dB over silence,"
              " but no".format(100 * peak, snr))
        print("    band rose more than {:+.1f} dB. The energy was in a few bins"
              .format(max_band))
        print("    — a tone, hum, or a brief knock — not spread across")
        print("    frequencies. Needed: a SUSTAINED \"shhhh\" held for the whole")
        print("    3 s, a few inches away, not touching the mic or its cable.")
    else:
        print("    About the TEST, not the mic: peak {:.1f}%, {:.0f} dB over"
              " silence.".format(100 * peak, snr))
        print("    Need a loud steady \"shhh\" DURING stage 2 only: aim peak"
              " >20%, >30 dB.")
else:
    justified = int(round(usable * 2 / 1000.0) * 1000)
    # If the signal runs right up to this run's Nyquist, the ceiling is the
    # SWITCH, not the microphone, and "justifies about <RATE>" would be
    # circular — the answer would just be the question. Say that instead.
    # Against ANALYSIS_MAX, not RATE/2. When the path is band-limited those
    # differ by 4x, and using the wrong one broke the guard on the laptop mic
    # (build dd8941fa): content reached 23619 Hz of the 24000 Hz visible, and
    # it still reported "well below what this run could see, so that ceiling
    # is the MICROPHONE" — because 23619 is indeed well below 96000, a number
    # this run could not actually see past 24000.
    if usable > 0.9 * ANALYSIS_MAX:
        print("  bandwidth: >={:.0f} Hz — as high as this run can SEE"
              .format(usable))
        if band_limited:
            print("    ({} Hz, the real Nyquist of this upsampled path — not"
                  .format(int(ANALYSIS_MAX)))
            print("    the {} Hz requested). The mic may well reach higher;"
                  .format(RATE))
            print("    this path cannot show it. Re-run on a device that is")
            print("    honest at a high rate to find the microphone's limit.")
        else:
            print("    ({} Hz). Re-run at a higher --rate to find the mic's"
                  .format(int(ANALYSIS_MAX)))
            print("    actual limit.")
    elif not signal_broadband:
        # The ceiling is real but says nothing about the microphone: there was
        # no high-frequency content in the test signal to begin with.
        print("  bandwidth: {:.0f} Hz — but the TEST SIGNAL was not broadband"
              .format(usable))
        print("    ({:.0f} dB less energy at 2-8 kHz than below 1 kHz), so this"
              .format(tilt))
        print("    is the SIGNAL's ceiling, not the microphone's. A thump or")
        print("    handling noise does this. Re-run with a steady \"shhh\".")
    else:
        print("  bandwidth: {:.0f} Hz — well below the {} Hz this run could"
              " see,".format(usable, int(ANALYSIS_MAX)))
        print("    so that ceiling is the MICROPHONE. Justifies ~{} Hz."
              .format(justified))
        # Honest direction of the error: a "shhh" loses energy with frequency
        # on its own, so some of this ceiling belongs to the signal. The
        # figure is a LOWER bound on the microphone — which is the safe way
        # for it to be wrong, since the conclusion drawn from it is "you do
        # not need a higher rate".
        print("    (A lower bound: a \"shhh\" fades with frequency too, so the")
        print("    mic may reach higher. Fine either way — the conclusion is")
        print("    that a higher rate buys nothing, and that only gets safer.)")
        if RATE > justified * 1.5:
            print("    Recording at {} Hz stores only noise above {:.0f} Hz."
                  .format(RATE, usable))

# ── Plain-language verdicts ───────────────────────────────────────────────
notes = []
if clipped:
    notes.append("CLIPPING: {} samples at full scale, unrecoverable. Lower"
                 " input gain.".format(clipped))
if peak < 0.05:
    notes.append("TOO QUIET: peak {:.1f}%. Raise gain or move closer; most"
                 " bit depth unused.".format(100 * peak))
elif peak > 0.9:
    notes.append("VERY HOT: peak {:.1f}%, near clipping. Leave headroom."
                 .format(100 * peak))
if reference_bad:
    # SNR and noise floor both come from the silent capture, so a failed
    # reference invalidates them along with the bandwidth. Level, clipping and
    # DC offset use only the sound capture and remain good.
    notes.append("Noise floor and SNR above are ALSO void (both from the"
                 " silent capture). Peak, clipping and DC still hold.")
elif snr < 20:
    notes.append("NOISY: {:.0f} dB over the mic's own noise. Expect hiss; a"
                 " higher rate will not fix it.".format(snr))
if concentrated:
    notes.append("SIGNAL IN A FEW BINS: {:.0f} dB total over silence but no"
                 " band above {:+.1f} dB — a tone, hum or knock, not a"
                 " broadband sound.".format(snr, max_band))
if band_limited:
    notes.append("RATE NOT REAL on this device: {} Hz is upsampled from"
                 " 48000. Use --rate=48000 here, or a device that is"
                 " honest at {} Hz.".format(RATE, RATE))
if not signal_broadband:
    notes.append("TEST SIGNAL NOT BROADBAND: {:.0f} dB less at 2-8 kHz than"
                 " below 1 kHz. A \"shhh\" is needed; a thump measures"
                 " nothing about bandwidth.".format(tilt))
if abs(dc) > 0.01:
    notes.append("DC OFFSET {:.2f}%: not centred on zero; wastes headroom,"
                 " upsets pitch/formant analysis.".format(100 * dc))
if overflows:
    notes.append("DROPPED SAMPLES: input overflowed {} times, so recordings"
                 " will have gaps.".format(overflows))
if not notes:
    notes.append("Nothing wrong found.")
print("\n  notes:")
for n in notes:
    print("    * " + n)
