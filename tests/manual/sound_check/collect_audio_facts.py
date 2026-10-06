#!/usr/bin/env python3
# coding=UTF-8
"""Collect audio facts from THIS machine, for comparison with others.

    cd <azt>
    ../env/bin/python -um tests.manual.sound_check.collect_audio_facts

Runs unattended in about 20 seconds. Make ordinary room noise or talk while
it runs — it needs *some* sound, and says so if it did not get any.

WHY THIS EXISTS
    Everything else in this directory was built while diagnosing ONE machine,
    and Kent asked the question that matters (2026-09-10): "are we making
    these tests more correct/general, or are we just diagnosing my machine?"
    Mostly the latter, for the parts that involve a threshold. The evidence
    behind every number A-Z+T now uses is one laptop, and where two cases
    landed 10 dB apart on that laptop there is no reason to think the gap
    holds anywhere else.

    So this script does NOT judge. It measures and prints, and the numbers
    from several machines are what would let a threshold be set from evidence
    instead of from one example. A verdict here would just propagate the
    guess it is supposed to test.

WHAT IT REPORTS, per input device and candidate rate
    opens        whether a stream opens at all (many will not; that is data)
    got Hz       frames divided by elapsed time — the rate actually delivered
    peak         loudest sample, as % of full scale
    top-of-band  level at the top 30% of the band, relative to 1 kHz-20% of
                 Nyquist. THE KEY NUMBER. A real converter's noise is
                 broadband and lands within a few tens of dB; a band-limited
                 resample leaves a hole 100+ dB down. On the one machine
                 measured so far: -25 dB genuine, -35 dB cheaply resampled,
                 -105 to -142 dB band-limited. Whether those ranges separate
                 anywhere else is exactly the open question.
    zeros        exactly-zero samples, and the longest unbroken run of them.
                 Analogue audio does not land on exactly zero repeatedly, so
                 a long run means a noise gate, a mute, or a dropout. This one
                 needs no threshold and should be trustworthy anywhere.

WHAT TO DO WITH IT
    Paste the block under "COPY FROM HERE". Nothing in it identifies you or
    your files: device names, sample rates and signal levels only.

Switches (no environment variables; nothing identified by colour):
  --seconds=S   Capture length per combination (default 0.4)
  --note=TEXT   Anything about the machine or room worth recording
  --rates=A,B   Rates to try (default 192000,96000,48000,44100,22050,8000)
  --help        This
"""
import platform
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
    # The path here used to be hardcoded POSIX (`../env/bin/python`), which
    # is wrong on Windows — the platform where a colleague running this is
    # most likely to hit it, and where Kent did (2026-09-10).
    from tests.manual.sound_check._which_python import how_to_run
    print(how_to_run('tests.manual.sound_check.collect_audio_facts',
                     missing='numpy and sounddevice ({})'.format(e)))
    sys.exit(1)

SECONDS = float(switch('seconds', 0.4))
NOTE = switch('note') or 'none given'
RATES = [int(r) for r in switch('rates',
                                '192000,96000,48000,44100,22050,8000'
                                ).split(',')]


def db(x):
    return 20.0 * numpy.log10(max(float(x), 1e-20))


def top_of_band(mono, rate):
    """Level at the top of the band vs the mid band, in dB. None if unusable.

    Deliberately the same computation `backend.core.sound.rate_is_fake` uses,
    so what is collected here is what the app decides on — a number gathered
    by a slightly different method would not test anything.
    """
    if mono.size < 4096:
        return None
    n = 1 << int(numpy.floor(numpy.log2(min(mono.size, 65536))))
    mag = numpy.abs(numpy.fft.rfft(mono[:n] * numpy.hanning(n)))
    if mag.max() <= 0:
        return None
    freqs = numpy.fft.rfftfreq(n, 1.0 / float(rate))
    nyq = rate / 2.0
    top = (freqs >= 0.70 * nyq) & (freqs <= nyq)
    mid = (freqs >= 1000.0) & (freqs < 0.20 * nyq)
    if not top.any() or not mid.any():
        return None
    mid_level = float(numpy.median(mag[mid]))
    if mid_level <= 0:
        return None
    if db(mid_level / mag.max()) < -100.0:
        return None             # too quiet for the ratio to mean anything
    return db(float(numpy.median(mag[top])) / mid_level)


def capture(device, rate, fmt, seconds):
    """(mono float array, measured rate) or (None, reason)."""
    blocks = []
    over = {'n': 0}

    def cb(indata, frames, time_info, status):
        if status and getattr(status, 'input_overflow', False):
            over['n'] += 1
        blocks.append(indata.copy())

    try:
        stream = sounddevice.InputStream(samplerate=rate, device=device,
                                         channels=1, dtype=fmt, callback=cb)
        stream.start()
        t0 = time.time()
        time.sleep(seconds)
        stream.stop()
        elapsed = time.time() - t0
        stream.close()
    except Exception as e:
        return None, str(e).split('\n')[0][:60]
    if not blocks:
        return None, 'no data delivered'
    raw = numpy.concatenate(blocks)
    mono = raw if raw.ndim == 1 else raw[:, 0]
    scale = float(numpy.iinfo(mono.dtype).max) if mono.dtype.kind == 'i' else 1
    return (mono.astype('float64') / scale,
            (len(mono) / elapsed if elapsed > 0 else 0, over['n']))


def zero_facts(mono):
    """(count, longest run) of exactly-zero samples."""
    zero = (mono == 0.0)
    count = int(zero.sum())
    if not count:
        return 0, 0
    if zero.all():
        return count, len(mono)
    live = numpy.flatnonzero(~zero)
    longest = int(live[0])
    if len(live) > 1:
        gaps = numpy.diff(live) - 1
        if gaps.size:
            longest = max(longest, int(gaps.max()))
    return count, max(longest, len(mono) - 1 - int(live[-1]))


print("Collecting audio facts. About {:.0f} seconds; make ordinary room "
      "noise or talk\nwhile it runs.".format(len(RATES) * SECONDS * 3 + 5))

rows = []
inputs = []
try:
    for i, d in enumerate(sounddevice.query_devices()):
        if d.get('max_input_channels', 0) > 0:
            inputs.append((i, str(d.get('name')),
                           float(d.get('default_samplerate') or 0)))
except Exception as e:
    print("couldn't list devices: {}".format(e))
    sys.exit(1)

for index, name, claims in inputs:
    print("  {} ...".format(name))
    for rate in RATES:
        for fmt in ('int32', 'int16'):
            mono, info = capture(index, rate, fmt, SECONDS)
            if mono is None:
                rows.append((name, claims, rate, fmt, 'no', None, None, None,
                             None, None, info))
                break           # if int32 fails, int16 usually fails the same
            got, overflows = info
            zeros, longest = zero_facts(mono)
            rows.append((name, claims, rate, fmt, 'yes', got,
                         float(numpy.abs(mono).max()),
                         top_of_band(mono, rate), zeros, longest,
                         'overflows={}'.format(overflows) if overflows else ''))

print('\n' + '=' * 78)
print("COPY FROM HERE")
print('=' * 78)
try:
    ver = sounddevice.get_portaudio_version()[1].split('\n')[0]
except Exception:
    ver = '?'
print("machine: {} {} | python {} | portaudio: {}".format(
        platform.system(), platform.release(),
        platform.python_version(), ver))
print("note: {} | capture {:.2f}s per combination".format(NOTE, SECONDS))
print("\ninputs seen (index: name — the rate it CLAIMS, which is not "
      "evidence):")
for index, name, claims in inputs:
    print("  {}: {!r} claims {:.0f} Hz".format(index, name, claims))
print("\n{:<26} {:>7} {:>5} {:>4} {:>8} {:>6} {:>9} {:>7}".format(
        "device", "rate", "fmt", "open", "got Hz", "peak%", "top-of-band",
        "0-run"))
for (name, claims, rate, fmt, opened, got, peak, top, zeros, longest,
     extra) in rows:
    if opened == 'no':
        print("{:<26} {:>7} {:>5} {:>4}   {}".format(
                name[:26], rate, fmt, 'NO', extra or ''))
        continue
    print("{:<26} {:>7} {:>5} {:>4} {:>8.0f} {:>6.1f} {:>9} {:>7} {}".format(
            name[:26], rate, fmt, 'yes', got, 100.0 * peak,
            "{:+.0f} dB".format(top) if top is not None else "too quiet",
            longest, extra))

# ── What the numbers would have to show, said plainly ────────────────────
print("\nnotes for whoever reads this:")
quiet = [r for r in rows if r[4] == 'yes' and r[7] is None]
if quiet:
    print("  * {} combination(s) were too quiet to give a top-of-band figure."
          .format(len(quiet)))
    print("    That is about the ROOM, not the hardware — re-run with some")
    print("    steady sound if those rows matter.")
gated = [r for r in rows if r[4] == 'yes' and r[9] and r[9] > 0.02 * r[2]]
if gated:
    print("  * {} combination(s) contained a run of exact zeros longer than"
          .format(len(gated)))
    print("    20 ms. Analogue audio does not do that: something is gating or")
    print("    dropping. Worth naming which device, since this is the one")
    print("    finding here that needs no threshold and should hold anywhere:")
    for r in gated[:6]:
        print("      {} at {} Hz: {} samples ({:.0f} ms)".format(
                r[0][:24], r[2], r[9], 1000.0 * r[9] / r[2]))
hot = [r for r in rows if r[4] == 'yes' and r[6] and r[6] > 0.95]
if hot:
    print("  * {} combination(s) peaked above 95% of full scale. Those are"
          .format(len(hot)))
    print("    CLIPPING, and every spectral figure from a clipped capture is")
    print("    manufactured — do not read the top-of-band column for them.")
print("  * The top-of-band column is the open question. On the only machine")
print("    measured so far: -25 dB genuine, -35 dB cheaply resampled, -105 to")
print("    -142 dB band-limited. If those ranges do not separate the same way")
print("    elsewhere, A-Z+T cannot decide a rate from this number and should")
print("    stop trying.")
print('=' * 78)
