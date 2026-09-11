#!/usr/bin/env python3
# coding=UTF-8
"""What can this card ACTUALLY do? Found out by recording, not by asking.

    cd <azt>
    ../env/bin/python tests/manual/sound_check/probe_real_capability.py --help

WHY THIS EXISTS
    `check_input_settings()` reports what a device will ACCEPT, and that is
    not what it will DELIVER. Twice now the difference has mattered:

      * 192 kHz/int32 was reported supported on every output here, and
        playback wedged on it (PyAudio era, 2026-09-09).
      * `default` accepted 192 kHz and PipeWire silently upsampled from 48 kHz
        — `clock.allowed-rates = [ 48000 ]` — so files SAID 192 kHz and held
        no detail above 24 kHz (2026-09-10).

    Kent's rule, and the reason this file exists: "If we can't find what
    settings are *actually* supported on a given card, we should facilitate
    whatever is needed to find out. … I can't expect them to do forensics on
    data we're lying about."

    So: open a real stream at every combination, capture a fraction of a
    second, and judge each one on what arrived.

WHAT EACH VERDICT MEANS
    REAL       The stream opened, frames arrived at the rate we asked for,
               the band is full up to near its own Nyquist, and nothing in the
               audio DISPROVED that rate. Not a guarantee: the detector (the
               app's own `rate_is_fake`) can prove a rate fake and cannot
               prove one genuine. "Nothing is wrong here" rather than "this is
               what it claims to be".
    NOT PROVED Nothing disproved the rate, but the top of the band was too
               quiet to judge on — so this is a statement about the EVIDENCE,
               not about the setting. Distinct from REAL on purpose: the
               detector never returns "genuine", so a quiet or empty capture
               used to inherit REAL's confidence without earning it
               (`8000 Hz REAL, spectrum reaches 51 Hz of 4000`, 2026-09-11).
    NOT TESTED The stream opened and delivered frames, and the band test
               cannot address this rate at all: it needs a mid band of
               1 kHz .. 0.20 x Nyquist, which does not exist below 10 kHz. A
               statement about the TEST. These used to read NO SIGNAL, which
               blamed the room — 8 kHz did so on four inputs at peaks of
               0.6-0.7% of full scale, where the room was plainly not the
               problem (2026-09-11).
    RESAMPLED  Frames arrived at the right rate, but the TOP OF THE BAND IS
               EMPTY — so something upsampled it. The file would be honest
               about its rate and hold less detail than that rate implies.
               NO REAL-RATE FIGURE IS QUOTED. One used to be (ceiling x 2) and
               it was worthless, because the ceiling comes from a metric that
               counts 120 dB-down residue as content: it produced
               "96000 Hz ... really ~96000 Hz" under this very heading
               (2026-09-11). Where the content stops is still reported, as a
               measurement rather than as a conclusion.
    RATE OFF   Frames arrived at a materially different rate than requested:
               duration and pitch would be wrong.
    NO SIGNAL  Opened and delivered frames, but silence — so the spectral test
               cannot say whether the rate is real. Not a failure of the
               setting: a failure of the ROOM. Make some noise and re-run.
    FAILED     The stream would not open at all, with the reason given.

    NOTE THE ASYMMETRY: REAL and RESAMPLED are conclusions about the audio.
    NO SIGNAL is a conclusion about the test. Do not read it as "unsupported".

HOW THE RESAMPLING TEST WORKS, and its limits
    Upsampled audio has a hard spectral cliff: 48 kHz content upsampled to
    192 kHz has nothing above 24 kHz, not even noise. So an EMPTY top of the
    band is the signature, and the detector (`backend.core.sound.rate_is_fake`,
    shared with the app) judges it on ABSOLUTE level.

    A QUIET ROOM IS FINE — and this is a correction, 2026-09-11. The script
    used to open by telling you to make noise, because the ORIGINAL detector
    estimated its noise floor from the top octave and so needed something to
    measure. It does not any more. Kent's quiet-room run produced peaks of
    0.1-0.7% of full scale and every verdict still formed, with no NO SIGNAL
    rows at all.

    Noise would not help even if it were needed: what proves a high rate is
    the CONVERTER'S OWN broadband noise reaching Nyquist, and nothing acoustic
    happens at 95 kHz. Playing a signal would only raise the audible band —
    which, against a fixed converter noise floor, makes the gap look DEEPER
    and an honest device look more upsampled, not less.

    THE LIMIT, learnt the hard way: the test needs DYNAMIC RANGE, so it can
    only be trusted in a wide format. int16's noise floor sits ~48 dB above
    int32's, and it buries exactly the faint high-frequency content the test
    looks for — so a narrow format reads as a cliff whether or not one is
    there. The first version of this script duly reported int16 at 96 k and
    192 k as "really ~46000 Hz" while calling the same ceiling REAL at 48 kHz.
    Since resampling is a property of the RATE (PipeWire negotiates its graph
    rate without asking what dtype the client wants), the rate is now judged
    in the widest format that opens and the narrower ones inherit the verdict,
    marked "(rate judged in …)".

Switches (no environment variables; nothing identified by colour):
  --device=N       Probe only this input device index (default: all inputs)
  --rates=A,B,C    Rates to try (default: 192000,96000,48000,44100,8000)
  --formats=A,B    dtypes to try (default: int32,int16)
  --seconds=S      Capture length per combination (default 0.35)
  --outputs        Also test whether each OUTPUT combination will open
  --csv=PATH       Write the table as CSV as well
  --quiet          Only print the summary table
  --help           This
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# THE APP'S OWN DETECTOR, so this script cannot disagree with the program it
# is diagnosing. Optional on purpose: this script must stay runnable on a
# machine where A-Z+T will not start (that is most of its value), and it says
# in each row when it had to fall back to its own threshold.
try:
    from backend.core.sound import rate_is_fake as app_rate_is_fake
    from backend.core.sound import top_of_band_db as app_top_of_band_db
    from backend.core.sound import rate_check_possible as app_rate_checkable
except Exception as _e:                                     # noqa: F841
    app_rate_is_fake = None
    app_top_of_band_db = None
    app_rate_checkable = None
    print("NOTE: could not import the app's rate detector ({}); falling back "
          "to this script's own threshold, which is known to call upsampled "
          "residue REAL above the graph rate.".format(_e))


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

QUIET = bool(switch('quiet'))
SECONDS = float(switch('seconds', 0.35))
# Idle time between combinations, so a sticky graph rate does not leak from one
# measurement into the next. 0.6s was enough on the machine where the leak was
# found; --settle= raises it if a system holds its rate longer.
SETTLE = float(switch('settle', 0.6))
RATES = [int(r) for r in
         str(switch('rates', '192000,96000,48000,44100,8000')).split(',')]
FORMATS = [f.strip() for f in str(switch('formats', 'int32,int16')).split(',')]
ONE_DEVICE = switch('device')

try:
    import numpy
except Exception as e:
    print("numpy is required for the spectral test: {}".format(e))
    sys.exit(1)
try:
    import sounddevice
except Exception as e:
    print("sounddevice is not available: {}".format(e))
    sys.exit(1)


def say(*a):
    if not QUIET:
        print(*a)


def spectral_ceiling(block, rate):
    """UNUSED SINCE 2026-09-11 — kept only so the record of WHY is next to it.

    Nothing calls this any more, and nothing should. It reads a noise floor
    from the top of the band and then asks which bins clear it, so in an
    upsampled capture it compares the resampler's residue against itself. It
    was wrong three different ways in one afternoon, each time by lending a
    plausible-looking number to a verdict:

      * it CALLED UPSAMPLED PATHS REAL (pipewire/default at 192 kHz, while the
        app and `pw-metadata` both said otherwise);
      * it produced "96000 Hz … really ~96000 Hz" under a heading saying the
        setting lies, because the claimed real rate was `ceiling * 2`;
      * it reported "reaches 9911 Hz of 24000" on a capture the real detector
        measured at -1 dB down, i.e. full — and that figure then drove a
        NOT PROVED verdict.

    Every number this script prints now comes from `top_of_band_db`, which is
    what `rate_is_fake` itself uses. Delete this function once nobody needs
    the history.

    (Original docstring:)
    The highest frequency still carrying real energy, in Hz — or None when
    the capture is too quiet to tell.

    Averages the magnitude spectrum, establishes a noise floor from the top
    octave, and walks down for the first band clearly above it. A resampled
    capture's cliff shows up as a ceiling well below rate/2.
    """
    mono = block if block.ndim == 1 else block[:, 0]
    if mono.dtype.kind == 'i':
        mono = mono.astype(numpy.float64) / float(
                                        numpy.iinfo(mono.dtype).max)
    else:
        mono = mono.astype(numpy.float64)
    if mono.size < 2048:
        return None
    peak = float(numpy.abs(mono).max())
    if peak < 0.0005:          # nothing audible: the room, not the setting
        return None
    # One window is enough for a cliff this gross, and keeps this fast.
    n = 1 << int(numpy.floor(numpy.log2(min(mono.size, 65536))))
    windowed = mono[:n] * numpy.hanning(n)
    mag = numpy.abs(numpy.fft.rfft(windowed))
    freqs = numpy.fft.rfftfreq(n, 1.0 / rate)
    if mag.max() <= 0:
        return None
    db = 20.0 * numpy.log10(numpy.maximum(mag / mag.max(), 1e-12))
    # Noise floor from the top 5% of the band. In a resampled capture that
    # region is empty, so the floor sits at the FFT's numerical noise and
    # anything real stands far above it.
    floor = float(numpy.median(db[int(len(db) * 0.95):]))
    threshold = floor + 12.0        # 12 dB clear of the floor
    above = numpy.nonzero(db > threshold)[0]
    if not len(above):
        return None
    return float(freqs[above[-1]])


def probe_input(device, rate, fmt):
    """Open, capture, judge. Returns (verdict, detail)."""
    blocks = []
    state = {'overflows': 0, 'frames': 0, 't0': None, 't_end': None}

    def cb(indata, frames, time_info, status):
        if state['t0'] is None:
            state['t0'] = time.perf_counter()
        if status and getattr(status, 'input_overflow', False):
            state['overflows'] += 1
        blocks.append(indata.copy())
        state['frames'] += len(indata)

    try:
        stream = sounddevice.InputStream(samplerate=rate, device=device,
                                         channels=1, dtype=fmt, callback=cb)
    except Exception as e:
        return 'FAILED', str(e).strip().splitlines()[0][:70]
    try:
        stream.start()
        negotiated = int(getattr(stream, 'samplerate', rate) or rate)
        time.sleep(SECONDS)
        stream.stop()
        # STOP THE CLOCK HERE — before close() and before the settle sleep.
        # The frame rate is frames ÷ elapsed, and `elapsed` used to be
        # measured all the way down at the verdict, which meant the idle pause
        # added below landed INSIDE the measured window: 0.35 s of frames
        # divided by 0.95 s of wall clock read as 37% of every rate, so a
        # whole run came back RATE OFF (2026-09-10). Nothing was wrong with
        # the audio; the ruler had grown.
        state['t_end'] = time.perf_counter()
        stream.close()
        # LET THE SERVER GO IDLE BEFORE THE NEXT COMBINATION. PipeWire's graph
        # rate is sticky: it switches on demand and holds until nothing is
        # attached. Without this pause the previous rate is still in force when
        # the next stream opens, and a path that would rather resample than
        # renegotiate produces a FALSE 'RESAMPLED' — see the retry in the main
        # loop, and the run that exposed it (2026-09-10).
        time.sleep(SETTLE)
    except Exception as e:
        try:
            stream.close()
        except Exception:
            pass
        return 'FAILED', str(e).strip().splitlines()[0][:70]

    if not state['frames']:
        return 'FAILED', 'opened but delivered no frames'
    # t_end, not "now": see the note where it is set.
    end = state['t_end'] or time.perf_counter()
    elapsed = (end - state['t0']) if state['t0'] else SECONDS
    implied = state['frames'] / elapsed if elapsed > 0.05 else rate
    notes = []
    if negotiated != rate:
        notes.append('negotiated {}'.format(negotiated))
    if state['overflows']:
        notes.append('{} overflow(s)'.format(state['overflows']))
    if implied < rate * 0.6 or implied > rate * 1.6:
        return 'RATE OFF', 'got ~{:.0f} frames/s; '.format(implied) + \
                           ', '.join(notes)

    data = numpy.concatenate(blocks)
    peak = float(numpy.abs(data).max())
    scale = float(numpy.iinfo(data.dtype).max) if data.dtype.kind == 'i' else 1.0
    notes.append('peak {:.1f}%'.format(100.0 * peak / scale))
    # ONE NUMBER, FROM THE DETECTOR THAT DECIDES. `spectral_ceiling` is gone
    # from every row: it is relative to a floor taken from inside the hole it
    # looks for, so it read 47965 Hz of 48000 ("full") on captures the
    # detector had just called EMPTY, and 9911 Hz of 24000 ("mostly empty")
    # on one measured at -1 dB ("full"). Printing it beside a verdict lent it
    # an authority it had not earned, three separate ways in one afternoon.
    # "THIS TEST DOES NOT REACH THAT RATE" is not "the room was quiet".
    # 8000 Hz came back NO SIGNAL on all four inputs at peaks of 0.6-0.7%
    # (Kent, 2026-09-11) — loud enough by any measure. The band test needs a
    # mid band of 1000 Hz .. 0.20 x Nyquist, which does not exist below
    # 10 kHz, so the rate is structurally unjudgeable. Saying NO SIGNAL sent
    # the reader after the room and suggested noise, which cannot help.
    if app_rate_checkable is not None and not app_rate_checkable(rate):
        return 'NOT TESTED', ('the band test does not reach this rate (it '
                              'needs a mid band above 1 kHz, which only '
                              'exists above 10 kHz); the stream opened and '
                              'delivered frames; ' + ', '.join(notes))
    margin = app_top_of_band_db(data, rate) if app_top_of_band_db else None
    if margin is None:
        return 'NO SIGNAL', ', '.join(notes)
    notes.append('top of band {:.0f} dB down'.format(margin))
    # THE APP'S DETECTOR DECIDES, not this script's own threshold.
    #
    # WHY THIS CHANGED (2026-09-11). This used `ceiling < rate * 0.28`, where
    # `ceiling` came from the local `spectral_ceiling` — which estimates its
    # noise floor from the top octave, i.e. from inside the very hole it is
    # looking for. So an upsampled capture's residue, 120 dB below the signal
    # but above that self-referential floor, read as energy reaching Nyquist,
    # and the verdict came back REAL. Kent's run of this script said:
    #
    #     in [7] pipewire  192000 Hz int32  REAL  reaches 86388 of 96000
    #     in [8] default   192000 Hz int32  REAL  reaches 57674 of 96000
    #
    # while the app, on the same machine minutes earlier, measured both as
    # band-limited with a -123 dB hole — and `pw-metadata` agreed with the
    # app. A DIAGNOSTIC THAT CONTRADICTS THE PROGRAM IS WORSE THAN NO
    # DIAGNOSTIC, because this is the script we hand to other machines to
    # settle exactly this question.
    #
    # `backend.core.sound.rate_is_fake` is the detector that was written to
    # fix this: it tests the ABSOLUTE level of the top of the band, it is
    # one-directional (it can prove a rate fake and never prove one real),
    # and it is the one the app itself uses. Sharing it makes the two agree
    # by construction rather than by coincidence.
    #
    if app_rate_is_fake is None:
        # Standalone fallback. It does NOT guess: the local `spectral_ceiling`
        # is the metric this whole change removed, so using it here would
        # reintroduce the fault on exactly the machines least able to notice.
        return 'NOT PROVED', ("the app's detector was not importable, so "
                              "nothing here can judge the rate; "
                              + ', '.join(notes))
    if app_rate_is_fake(data, rate):
        # NO "really ~N Hz" FIGURE. It was `ceiling * 2`, and `ceiling` comes
        # from the local `spectral_ceiling` — the metric just removed from the
        # verdict for being untrustworthy, because it estimates its noise
        # floor from the top octave and so counts 120 dB-down residue as
        # content. Keeping it for the estimate produced this (Kent,
        # 2026-09-11):
        #
        #     96000 Hz int32  RESAMPLED  really ~96000 Hz
        #
        # "96000 is really 96000" — under a heading saying the setting lies.
        # Kent: "96000 Hz int32 really ~96000 Hz is a LIE?" No, and the row
        # was refuting itself in print.
        #
        # THIS IS A DOCUMENTED BUG CLASS AND I REINTRODUCED IT. The four-bug
        # list in agenda/honest_sound_settings.md opens with exactly this:
        # "a real-rate figure computed from `spectral_ceiling`, which
        # estimates its floor inside the very hole being detected", and
        # "the same arithmetic producing a self-contradiction — 'says 96000 Hz
        # but really holds only 96000 Hz'". Removed there in the app; left
        # here, in the script, where it said the same thing again.
        #
        # What WAS established is stated instead: the top of the band is
        # empty, with the margin that says so (now in `notes`).
        return 'RESAMPLED', ('the top of the band is EMPTY, so this was '
                             'upsampled; ' + ', '.join(notes))
    # THE THIRD VERDICT: "can't tell" must not read as "fine".
    #
    # `rate_is_fake` returns True or None and NEVER False, so every non-fake
    # answer means only "not disproved" — which covers both a full band and a
    # capture too quiet or too empty to judge. Mapping both to REAL produced
    # this, in Kent's quiet-room run (2026-09-11):
    #
    #     8000 Hz int32  REAL  peak 0.1%, spectrum reaches 51 Hz of 4000
    #
    # 51 Hz of a possible 4000 is as band-limited as a capture gets, and the
    # row called it REAL with the contradicting figure printed beside it. That
    # is the mirror of the false-REAL just fixed: a confident word on no
    # measurement rather than on a weak one.
    #
    # THE CUT IS ON THE MARGIN, NOT ON THE CEILING — second correction in an
    # hour. My first version of NOT PROVED used `ceiling < rate * 0.28`, i.e.
    # the metric this change exists to remove, and it duly misfired: six rows
    # said "band mostly empty" about captures the detector measured at -1 dB,
    # which is as full as a band gets.
    #
    # THE FIGURES ARE FROM THE RECORD, not picked here. The item measured, on
    # this machine, same microphone, same room:
    #       genuine 192 kHz hardware       about -25 dB
    #       cheap linear interpolation     about -35 dB
    #       band-limited upsample (hole)   -105 to -142 dB
    # So -40 dB sits just below BOTH measured live cases and far above the
    # hole. A top of band quieter than that is neither a full band nor a
    # proven hole, which is exactly the state NOT PROVED exists to name.
    #
    # It cannot produce an accusation either way — it only moves a row between
    # REAL and NOT PROVED — which is why a figure with this little behind it
    # is tolerable here and would not be in the verdict.
    if margin <= -40.0:
        return 'NOT PROVED', ('nothing disproved this rate, but the top of '
                              'the band is too quiet to judge on; '
                              + ', '.join(notes))
    return 'REAL', ', '.join(notes)


def probe_output(device, rate, fmt):
    try:
        s = sounddevice.OutputStream(samplerate=rate, device=device,
                                     channels=1, dtype=fmt)
        s.start()
        got = int(getattr(s, 'samplerate', rate) or rate)
        s.stop()
        s.close()
        return ('REAL' if got == rate else 'RATE OFF',
                '' if got == rate else 'negotiated {}'.format(got))
    except Exception as e:
        return 'FAILED', str(e).strip().splitlines()[0][:70]


devices = []
try:
    for i, d in enumerate(sounddevice.query_devices()):
        devices.append({'index': i, 'name': d.get('name'),
                        'in': d.get('max_input_channels', 0),
                        'out': d.get('max_output_channels', 0),
                        'rate': d.get('default_samplerate')})
except Exception as e:
    print("couldn't list devices: {}".format(e))
    sys.exit(1)

print('=' * 78)
print("What this machine's audio can ACTUALLY do (by recording, not asking)")
print("  capture per combination: {}s".format(SECONDS))
print("  A quiet room is fine. Noise is not needed and does not help: the")
print("  evidence for a high rate is the converter's OWN noise reaching")
print("  Nyquist, which no sound in the room can supply.")
print('=' * 78)

rows = []
inputs = [d for d in devices if d['in'] > 0]
if ONE_DEVICE is not None:
    inputs = [d for d in inputs if d['index'] == int(ONE_DEVICE)]
if not inputs:
    print("no input devices to probe")
    sys.exit(1)

# WIDEST FORMAT FIRST, AND THE RATE IS JUDGED THERE ONLY.
# The spectral test needs headroom: it finds the highest frequency above the
# NOISE FLOOR, and a narrow format raises that floor by ~48 dB (int16 ≈ -96,
# int32 ≈ -144). So faint high content that int32 sees, int16 buries — and the
# first version of this script called that RESAMPLED. It reported int16 at
# 96 k and 192 k as "really ~46000 Hz" while calling the SAME ~23 kHz ceiling
# REAL at 48 kHz, which is the tell: the ceiling was a property of the format,
# not the rate (Kent's run, 2026-09-10).
#   Whether a resampler sits in the path is a property of the RATE, not of the
# client's sample format — PipeWire negotiates its graph rate without
# reference to it. So: judge the rate in the widest format that opens, and let
# the narrower ones inherit that verdict. They are still opened, because
# whether they open at all is theirs to answer.
_WIDTH = {'float32': 32, 'int32': 32, 'int24': 24, 'int16': 16, 'int8': 8}
FORMATS_WIDEST_FIRST = sorted(FORMATS, key=lambda f: -_WIDTH.get(f, 0))

for d in inputs:
    say("\nINPUT [{}] {}  (its own default rate: {})".format(
            d['index'], d['name'], d['rate']))
    for rate in RATES:
        judged = None          # (verdict, detail, fmt) from the widest format
        for fmt in FORMATS_WIDEST_FIRST:
            verdict, detail = probe_input(d['index'], rate, fmt)
            # NEVER ACCUSE ON ONE READING. A RESAMPLED verdict says the user's
            # device is lying to them, and this test can produce that verdict
            # by its own doing: it left PipeWire's graph at the previous rate,
            # and `default` @192k duly read as "really ~97000 Hz" — then came
            # back REAL when run on its own (Kent, 2026-09-10). So confirm it
            # in isolation, after a longer idle, and believe it only if it
            # repeats.
            if verdict == 'RESAMPLED':
                say("   {:>7} Hz {:<7} {:<10} {}".format(
                        rate, fmt, 'checking', 'looked resampled — retrying '
                        'after {:.1f}s idle'.format(SETTLE * 3)))
                time.sleep(SETTLE * 3)
                again, again_detail = probe_input(d['index'], rate, fmt)
                if again == 'RESAMPLED':
                    detail = again_detail + ' (confirmed on retry)'
                else:
                    verdict, detail = again, (
                        again_detail + ' (first read said RESAMPLED; that was '
                        'this test leaving the graph at another rate)')
            if verdict != 'FAILED':
                if judged is None:
                    judged = (verdict, detail, fmt)
                elif verdict in ('REAL', 'RESAMPLED', 'NO SIGNAL',
                                 'NOT PROVED', 'NOT TESTED'):
                    # Opened fine; the rate question was already settled in a
                    # format with the headroom to answer it.
                    verdict = judged[0]
                    detail = '{} (rate judged in {})'.format(judged[1],
                                                             judged[2])
            rows.append(('in', d['index'], d['name'], rate, fmt,
                         verdict, detail))
            say("   {:>7} Hz {:<7} {:<10} {}".format(rate, fmt, verdict,
                                                     detail))

if switch('outputs'):
    for d in [x for x in devices if x['out'] > 0]:
        say("\nOUTPUT [{}] {}  (opens only — no loopback to measure)".format(
                d['index'], d['name']))
        for rate in RATES:
            for fmt in FORMATS:
                verdict, detail = probe_output(d['index'], rate, fmt)
                rows.append(('out', d['index'], d['name'], rate, fmt,
                             verdict, detail))
                say("   {:>7} Hz {:<7} {:<10} {}".format(rate, fmt, verdict,
                                                         detail))

print('\n' + '=' * 78)
print("Summary — settings nothing argued against")
real = [r for r in rows if r[5] == 'REAL']
if real:
    for io, idx, name, rate, fmt, _v, _d in real:
        print("  {:<3} [{}] {:<28} {:>7} Hz {}".format(io, idx, name[:28],
                                                       rate, fmt))
else:
    print("  NONE. Every combination either failed to open, was shown to be")
    print("  upsampled, or gave too little to judge on (NOT PROVED).")

# LISTED SEPARATELY, not folded into either side. These are not endorsements
# and not accusations, and putting them in the REAL list was how a capture
# reaching 51 Hz of a possible 4000 came to be summarised as real.
unproved = [r for r in rows if r[5] == 'NOT PROVED']
if unproved:
    print("\nSettings with too little evidence to judge — not a fault of the")
    print("setting; the capture had too little in the band to read:")
    for io, idx, name, rate, fmt, _v, detail in unproved:
        print("  {:<3} [{}] {:<28} {:>7} Hz {:<7} {}".format(io, idx,
                                            name[:28], rate, fmt, detail))

resampled = [r for r in rows if r[5] == 'RESAMPLED']
if resampled:
    print("\nSettings that LIE — accepted, recorded, and secretly upsampled:")
    for io, idx, name, rate, fmt, _v, detail in resampled:
        print("  {:<3} [{}] {:<28} {:>7} Hz {:<7} {}".format(io, idx,
                                            name[:28], rate, fmt, detail))
    print("  A file recorded at these settings states its rate honestly and")
    print("  holds less detail than that rate implies. On PipeWire, add the")
    print("  rate to clock.allowed-rates to make it genuine.")

counts = {}
for r in rows:
    counts[r[5]] = counts.get(r[5], 0) + 1
print("\n  " + ', '.join('{} {}'.format(v, k) for k, v in sorted(counts.items())))

# THE NOISE REMINDER, REPEATED AT THE END — because the one at the top scrolls
# past before anyone has read it (Kent 2026-09-10: "it's running before I read
# it. maybe add (restart if you weren't making noise when this ran)?").
print("\n  WHAT 'REAL' DOES AND DOES NOT PROVE:")
print("   * It means nothing DISPROVED the rate, and the top of the band is")
print("     full — the figure quoted per row. That content is mostly the")
print("     ADC's own noise, NOT captured sound: nothing acoustic happens at")
print("     95 kHz. Its PRESENCE is the evidence; it is not music. An")
print("     upsampled file has a hole there instead.")
print("   * It does NOT prove the MICROPHONE gives you anything useful up")
print("     there. Most roll off well below 20 kHz, so a high rate can be")
print("     genuine and still carry only noise in its top half. That is a")
print("     question about the mic, and this test cannot answer it.")
print("   * It does NOT prove the hardware ran at that rate. DOWNsampling is")
print("     undetectable this way: properly downsampled 8 kHz audio has energy")
print("     to 4 kHz exactly like a native capture. For data quality that is")
print("     the same thing; for 'what is my card doing', it is not.")
print("   * RESULTS CAN DEPEND ON RUN ORDER. PipeWire's graph rate is sticky —")
print("     it switches on demand and stays until idle — so a rate tested just")
print("     before can leave the graph where a later test then resamples from.")
print("     A lone RESAMPLED row next to a REAL one at the same rate on another")
print("     device is the signature. Re-run with --rates=<just that one> to")
print("     judge it on its own.")

quiet = counts.get('NO SIGNAL', 0) + counts.get('NOT PROVED', 0)
if quiet:
    print("\n  {} row(s) came back NO SIGNAL or NOT PROVED. BOTH ARE FACTS "
          "ABOUT".format(quiet))
    print("  THE EVIDENCE, not about the setting — the test could not judge,")
    print("  which is not the same as the setting being unsupported. Making")
    print("  noise does NOT help: what proves a high rate is the converter's")
    print("  own broadband noise reaching Nyquist, and nothing in the room")
    print("  can put energy up there. (This block used to say the opposite.)")

csv_path = switch('csv')
if csv_path:
    import csv as _csv
    with open(csv_path, 'w', newline='') as fh:
        w = _csv.writer(fh)
        w.writerow(['direction', 'device', 'name', 'rate', 'format',
                    'verdict', 'detail'])
        w.writerows(rows)
    print("\n  table written to {}".format(csv_path))
