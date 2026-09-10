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
    REAL       The stream opened, frames arrived at the rate we asked for, and
               the audio carries energy up near that rate's Nyquist limit.
               This setting is what it claims to be.
    RESAMPLED  Frames arrived at the right rate, but the audio has NO energy
               above some lower limit — so something upsampled it. The file
               would be honest about its rate and dishonest about its content.
               The reported ceiling is roughly twice the real sample rate.
    RATE OFF   Frames arrived at a materially different rate than requested:
               duration and pitch would be wrong.
    NO SIGNAL  Opened and delivered frames, but silence — so the spectral test
               cannot say whether the rate is real. Not a failure of the
               setting: a failure of the ROOM. Make some noise and re-run.
    FAILED     The stream would not open at all, with the reason given.

    NOTE THE ASYMMETRY: REAL and RESAMPLED are conclusions about the audio.
    NO SIGNAL is a conclusion about the test. Do not read it as "unsupported".

HOW THE RESAMPLING TEST WORKS, and its limits
    Upsampled audio has a hard spectral cliff: 48 kHz content stretched to
    192 kHz has nothing above 24 kHz, not even noise. So the highest frequency
    still carrying energy above the noise floor tells us the REAL rate. This
    needs some sound in the room — even room noise is enough, since the cliff
    shows in the noise floor too. In an anechoic silence it reports NO SIGNAL
    rather than guessing.

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
    """The highest frequency still carrying real energy, in Hz — or None when
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
    ceiling = spectral_ceiling(data, rate)
    peak = float(numpy.abs(data).max())
    scale = float(numpy.iinfo(data.dtype).max) if data.dtype.kind == 'i' else 1.0
    notes.append('peak {:.1f}%'.format(100.0 * peak / scale))
    if ceiling is None:
        return 'NO SIGNAL', ', '.join(notes)
    # "spectrum reaches", not "energy to": at 192 kHz this number lands near
    # 95 kHz, and Kent reasonably asked how that can be real (2026-09-10).
    # It is not SOUND — nothing acoustic happens at 95 kHz, and no microphone
    # delivers it. It is the ADC's own broadband noise, which in a genuine
    # capture extends to Nyquist. That is precisely the signature: an
    # upsampled file is conspicuously EMPTY above the old Nyquist, while a
    # real one is noisy all the way up. The wording said "energy", which
    # invites reading it as captured signal.
    notes.append('spectrum reaches {:.0f} Hz of {:.0f} possible'.format(
                    ceiling, rate / 2.0))
    # A real capture carries energy to somewhere near its own Nyquist. Allow
    # a wide margin: microphones roll off, and content is not white noise.
    if ceiling < rate * 0.28:
        real = int(round(ceiling * 2 / 1000.0) * 1000)
        return 'RESAMPLED', 'really ~{} Hz; '.format(real) + ', '.join(notes)
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
print("  MAKE SOME NOISE while this runs — speak, tap the desk. The")
print("  resampling test needs sound; in silence it reports NO SIGNAL.")
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
                elif verdict in ('REAL', 'RESAMPLED', 'NO SIGNAL'):
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
print("Summary — settings that are REAL")
real = [r for r in rows if r[5] == 'REAL']
if real:
    for io, idx, name, rate, fmt, _v, _d in real:
        print("  {:<3} [{}] {:<28} {:>7} Hz {}".format(io, idx, name[:28],
                                                       rate, fmt))
else:
    print("  NONE verified. If most rows say NO SIGNAL, the room was quiet —")
    print("  re-run while making noise. Otherwise this machine cannot deliver")
    print("  any of the rates tried.")

resampled = [r for r in rows if r[5] == 'RESAMPLED']
if resampled:
    print("\nSettings that LIE — accepted, recorded, and secretly resampled:")
    for io, idx, name, rate, fmt, _v, detail in resampled:
        print("  {:<3} [{}] {:<28} {:>7} Hz {:<7} {}".format(io, idx,
                                            name[:28], rate, fmt, detail))
    print("  A file recorded at these settings states its rate honestly and")
    print("  contains no detail above half the real one. On PipeWire, add the")
    print("  rate to clock.allowed-rates to make it genuine.")

counts = {}
for r in rows:
    counts[r[5]] = counts.get(r[5], 0) + 1
print("\n  " + ', '.join('{} {}'.format(v, k) for k, v in sorted(counts.items())))

# THE NOISE REMINDER, REPEATED AT THE END — because the one at the top scrolls
# past before anyone has read it (Kent 2026-09-10: "it's running before I read
# it. maybe add (restart if you weren't making noise when this ran)?").
print("\n  WHAT 'REAL' DOES AND DOES NOT PROVE:")
print("   * It proves the file was really SAMPLED at its stated rate: its")
print("     spectrum reaches its own Nyquist, which an upsampled file cannot.")
print("     The figure quoted per row is mostly the ADC's noise floor, NOT")
print("     captured sound — nothing acoustic happens at 95 kHz. Its presence")
print("     is the evidence; its content is not music.")
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

quiet = counts.get('NO SIGNAL', 0)
print("\n  WERE YOU MAKING NOISE while that ran? The rate test needs sound —")
print("  speak, tap the desk, anything. RE-RUN THIS if the room was quiet.")
if quiet:
    print("  {} combination(s) came back NO SIGNAL, which usually means "
          "exactly that.".format(quiet))
print("  (NO SIGNAL is a fact about the room, not about the setting: it means")
print("  the test could not judge, NOT that the setting is unsupported.)")

csv_path = switch('csv')
if csv_path:
    import csv as _csv
    with open(csv_path, 'w', newline='') as fh:
        w = _csv.writer(fh)
        w.writerow(['direction', 'device', 'name', 'rate', 'format',
                    'verdict', 'detail'])
        w.writerows(rows)
    print("\n  table written to {}".format(csv_path))
