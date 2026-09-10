#!/usr/bin/env python3
# coding=UTF-8
"""Compare microphones by playing a KNOWN signal and recording it.

    cd <azt>
    ../env/bin/python -um tests.manual.sound_check.mic_compare --help
    ../env/bin/python -um tests.manual.sound_check.mic_compare --list
    ../env/bin/python -um tests.manual.sound_check.mic_compare \\
            --device='hw:0,0' --device='hw:0,6' --note='headset plugged in'

WHY THIS EXISTS, AND WHY mic_check.py COULD NOT DO IT
    mic_check.py asks the user to make a sound. Kent's verdict on a day of
    that (2026-09-10): "do they tell me when I have a good mic plugged in? do
    they tell me which of a couple mics is the best? will they allow us to
    sanely automate things for users?" — no, no, and only partly.

    The reason is that a human-produced "shhh" is not repeatable. Headset run:
    SNR 23 dB at 46% peak. Laptop run: SNR 11 dB at 2.2% peak. Those numbers
    cannot be compared, because the signal, the distance and the gain all
    differed. Seven of eight attempts failed outright.

    Here the SIGNAL IS GENERATED, so it is identical for every microphone and
    every run. That single change is what makes comparison possible, and it
    takes the user out of the loop: no instructions to follow, nothing to get
    wrong, nothing to remember.

WHAT IT DOES
    Plays band-limited flat-spectrum noise (same waveform every time — fixed
    seed) and records it on each candidate input in turn, with a silent
    capture before each for that input's own noise floor. Then reports, per
    microphone: level, noise floor, signal-to-noise per band, usable
    bandwidth, flatness across the speech band, and clipping.

ROUTING NOTE (placement itself is a known issue, out of scope here)
    Plugging in a headset routes playback to the earpiece, so mics are no
    longer equally exposed and the ranking stops meaning anything. --output
    can move playback only if ALSA exposes speakers as a separate PCM; where
    the codec auto-mutes them on jack insert (`amixer -c 0 sget 'Auto-Mute
    Mode'`) that is below the layer this script can reach. The script warns
    when some inputs hear the signal and others do not, which is the symptom.

WHAT THE NUMBERS MEAN, AND WHAT THEY DO NOT
    The measured path is SPEAKER -> ROOM -> MICROPHONE. So:

    * COMPARING two microphones on this machine, in this room, right now is
      VALID — the speaker and room are identical for both, so a difference is
      a difference between the microphones. This is the question worth asking.
    * The measured ceiling is min(speaker, microphone). If the speaker stops
      at 15 kHz, every microphone will read about 15 kHz. So this does NOT
      establish what sample rate a microphone justifies — do not use it for
      that. (mic_check.py's fake-rate detection is the honest answer to rate
      questions, and needs no test signal at all.)
    * Absolute levels depend on input gain, output volume and geometry, so
      they are not a spec sheet. Ranking is meaningful; the raw dBFS is not.
    * Room reflections comb-filter the response, putting ripple in the band
      profile. Ripple that is IDENTICAL across microphones is the room;
      ripple that differs is the microphone.

Switches (no environment variables; nothing identified by colour):
  --list            List input and output devices by name, then exit.
  --device=NAME     An input to test, BY NAME. REPEAT IT to compare several:
                      --device=pipewire --device=sysdefault
                    Not comma-separated: real device names contain commas
                    ('sof-hda-dsp: - (hw:0,0)'). A partial name matches, so
                    --device='hw:0,0' works too. Default: system default.
  --output=NAME     Output device to play through (default: system default).
  --rate=N          Capture/playback rate (default 48000, which is what is
                    genuinely available on typical hardware — see
                    agenda/honest_sound_settings.md. Higher rates are usually
                    resampled, and the speaker limits the top end anyway).
  --seconds=S       Noise burst length (default 3.0).
  --quiet-seconds=S Silent capture before each mic (default 1.5).
  --level=F         Playback amplitude, 0-1 (default 0.3). Keep it modest:
                    a loud speaker distorts and the distortion is measured
                    as if it were microphone behaviour.
  --countdown=S     Seconds before the first capture (default 3).
  --note=TEXT       Record conditions in the output.
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


def switches(name):
    """Every --name=VALUE, in order.

    Repeating the switch, rather than one comma-separated list, because the
    device names on real hardware CONTAIN commas: this machine offers
    'sof-hda-dsp: - (hw:0,0)'. Splitting on commas would cut that in half and
    match nothing. (Indices avoid the comma but move between runs, so they
    are not an option either.)
    """
    found = []
    for arg in sys.argv[1:]:
        if arg.startswith('--' + name + '='):
            found.append(arg.split('=', 1)[1])
    return found


if switch('help'):
    print(__doc__)
    sys.exit(0)

try:
    import numpy
    import sounddevice
except Exception as e:
    print("needs numpy and sounddevice: {}".format(e))
    sys.exit(1)


def as_device(text):
    """Names are stable; indices are not (they shifted twice on 2026-09-10)."""
    try:
        return int(text)
    except (TypeError, ValueError):
        return text


if switch('list'):
    print("Devices (use names, not indices — indices move between runs):")
    try:
        for i, d in enumerate(sounddevice.query_devices()):
            kinds = []
            if d.get('max_input_channels', 0) > 0:
                kinds.append('in')
            if d.get('max_output_channels', 0) > 0:
                kinds.append('out')
            print("  [{}] {!r}  {}  (claims {:.0f} Hz)".format(
                    i, d.get('name'), '/'.join(kinds) or '-',
                    d.get('default_samplerate', 0)))
    except Exception as e:
        print("  couldn't enumerate: {}".format(e))
    sys.exit(0)

RATE = int(switch('rate', 48000))
SECONDS = float(switch('seconds', 3.0))
QUIET_S = float(switch('quiet-seconds', 1.5))
LEVEL = float(switch('level', 0.3))
COUNTDOWN = float(switch('countdown', 3))
NOTE = switch('note') or 'none given'
OUTPUT = as_device(switch('output')) if switch('output') else None
def all_inputs():
    """Every input device, as indices valid for THIS process.

    Indices move between runs but are stable within one, so enumerating once
    and using what comes back is safe where a remembered index would not be.

    Testing all of them is the default because the tool is called mic_compare
    and the question is "which of my mics is best" — requiring the user to
    know which cryptic name is which microphone defeats the point. Several
    entries will be different PATHS to the same microphone; that is detected
    below rather than guessed at.
    """
    found = []
    try:
        for i, d in enumerate(sounddevice.query_devices()):
            if d.get('max_input_channels', 0) > 0:
                found.append(i)
    except Exception as e:
        print("couldn't enumerate inputs: {}".format(e))
    return found


INPUTS = [as_device(d) for d in switches('device')] or all_inputs()

try:
    BUILD = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:8]
except Exception:
    BUILD = '?'


def db(x):
    return 20.0 * numpy.log10(max(float(x), 1e-12))


def rms(a):
    return float(numpy.sqrt(numpy.mean(numpy.square(a)))) if len(a) else 0.0


def make_noise(rate, seconds, lo=60.0, hi_frac=0.48):
    """Flat-spectrum noise, band-limited, IDENTICAL on every call and run.

    Built in the frequency domain — unit magnitude across the band, random
    phase — rather than by filtering white noise, so the band edges are exact
    and the spectrum is genuinely flat. A flat played spectrum means the
    RECORDED spectrum is the system response directly, with no need to divide
    by the stimulus or to align playback and capture in time.

    The seed is FIXED. Every microphone hears the same waveform, which is the
    entire point of this script; it also makes runs days apart comparable.
    """
    n = int(rate * seconds)
    rng = numpy.random.default_rng(20260910)
    freqs = numpy.fft.rfftfreq(n, 1.0 / rate)
    spec = numpy.zeros(len(freqs), dtype=complex)
    band = (freqs >= lo) & (freqs <= hi_frac * rate)
    spec[band] = numpy.exp(1j * rng.uniform(0, 2 * numpy.pi, int(band.sum())))
    sig = numpy.fft.irfft(spec, n)
    peak = numpy.abs(sig).max()
    if peak > 0:
        sig = sig / peak
    return sig.astype('float32')


def countdown(instruction, seconds=None):
    secs = COUNTDOWN if seconds is None else seconds
    print("  " + instruction)
    try:
        n = int(secs)
        while n > 0:
            sys.stdout.write("\r  in {}... ".format(n))
            sys.stdout.flush()
            time.sleep(1.0)
            n -= 1
        sys.stdout.write("\r           \r")
        sys.stdout.flush()
    except KeyboardInterrupt:
        print()
        sys.exit(1)


def record(device, seconds, playing=None):
    """Record `seconds` on `device`, optionally playing `playing` meanwhile.

    Playback is started first and NOT synchronised with the capture: only the
    magnitude spectrum is used, so a few milliseconds of offset changes
    nothing. Avoiding a duplex stream matters — input and output are often
    different ALSA devices that will not open together.
    """
    blocks = []
    over = {'n': 0}

    def cb(indata, frames, time_info, status):
        if status and getattr(status, 'input_overflow', False):
            over['n'] += 1
        blocks.append(indata.copy())

    # Playback gets its OWN try/except. Wrapped together with the capture, a
    # failure to play was indistinguishable from a failure to record — and
    # showed up only as Kent not hearing anything, which is precisely the
    # human-as-instrument problem this script exists to remove.
    played = False
    if playing is not None:
        try:
            sounddevice.play(playing, samplerate=RATE, device=OUTPUT)
            played = True
        except Exception as e:
            print("    COULDN'T PLAY the test signal: {}".format(e))
            print("    (so this row measures the room, not the signal)")
    try:
        stream = sounddevice.InputStream(samplerate=RATE, device=device,
                                         channels=1, dtype='int32',
                                         callback=cb)
        stream.start()
        t0 = time.time()
        time.sleep(seconds)
        stream.stop()
        elapsed = time.time() - t0
        stream.close()
    except Exception as e:
        print("    couldn't record: {}".format(e))
        return None, None
    finally:
        if playing is not None:
            try:
                sounddevice.stop()
            except Exception:
                pass
    if not blocks:
        print("    the stream delivered no data.")
        return None, None
    raw = numpy.concatenate(blocks)
    mono = raw if raw.ndim == 1 else raw[:, 0]
    full = float(numpy.iinfo(mono.dtype).max) if mono.dtype.kind == 'i' else 1.0
    info = {'over': over['n'], 'frames': len(mono), 'elapsed': elapsed,
            'rate': len(mono) / elapsed if elapsed > 0 else 0,
            'digest': hashlib.sha256(mono.tobytes()).hexdigest()[:12]}
    return mono.astype('float64') / full, info


def spectrum(a, rate, n):
    if n < 1024 or len(a) < n:
        return None, None
    mags = []
    step = n // 2
    for start in range(0, max(1, len(a) - n), step):
        seg = a[start:start + n]
        if len(seg) < n:
            break
        mags.append(numpy.abs(numpy.fft.rfft(seg * numpy.hanning(n))))
        if len(mags) >= 32:
            break
    if not mags:
        return None, None
    return numpy.fft.rfftfreq(n, 1.0 / rate), numpy.mean(mags, axis=0)


# Third-octave-ish bands: enough resolution to see a rolloff, coarse enough
# that room ripple does not dominate, and few enough to read as a table.
BANDS = [(60, 125), (125, 250), (250, 500), (500, 1000), (1000, 2000),
         (2000, 4000), (4000, 8000), (8000, 12000), (12000, 16000),
         (16000, 20000), (20000, 24000)]
SPEECH_BANDS = [(250, 500), (500, 1000), (1000, 2000), (2000, 4000)]


def band_levels(freqs, mag):
    out = {}
    for lo, hi in BANDS:
        if lo >= RATE / 2:
            break
        sel = (freqs >= lo) & (freqs < min(hi, RATE / 2))
        if sel.any():
            out[(lo, hi)] = db(numpy.median(mag[sel]))
    return out


print('=' * 74)
print("Microphone comparison — same generated signal for every mic")
print("  script build {} | {} Hz | level {:.2f} | {}".format(
        BUILD, RATE, LEVEL, NOTE))
try:
    out_info = sounddevice.query_devices(OUTPUT, 'output')
    OUT_NAME = out_info.get('name')
except Exception as e:
    OUT_NAME = '? ({})'.format(e)
print("  playing through: {!r}".format(OUT_NAME))
print("  measured path is SPEAKER -> ROOM -> MIC, so comparisons between")
print("  mics are valid; absolute figures are not a spec sheet.")
print('=' * 74)

STIM_LO, STIM_HI = 60.0, 0.48 * RATE
NOISE = make_noise(RATE, SECONDS) * LEVEL
print("\nSignal: {:.1f}s flat-spectrum noise, {:.0f} Hz to {:.0f} Hz,"
      " fixed seed".format(SECONDS, STIM_LO, STIM_HI))

# Bands the STIMULUS actually fills. A band reaching past the signal's own
# upper edge is partly empty, so its level is an artefact of the signal, not
# of the microphone — and the bandwidth figure must not be allowed to stop
# there and call it a result. Build fd686864 reported "bandwidth 20.0k" for a
# stimulus that ended at 21600 Hz: the number was measuring my own noise
# generator. Same trap as the rate cap in mic_check.py, one layer further in.
FILLED = [b for b in BANDS if b[1] <= min(STIM_HI, RATE / 2)]

print("Testing {} input{}: about {:.0f}s in total."
      .format(len(INPUTS), '' if len(INPUTS) == 1 else 's',
              len(INPUTS) * (QUIET_S + SECONDS + 0.6)))
countdown("Stay quiet and don't move the microphones — runs unattended now.")

results = []
for dev in INPUTS:
    try:
        info = sounddevice.query_devices(dev, 'input')
        name = info.get('name')
    except Exception as e:
        print("\n[{}] couldn't query: {}".format(dev, e))
        continue

    # No prompt per device: the user has nothing to do. That is the point of
    # a generated signal — one instruction at the start, then it runs
    # unattended however many inputs there are.
    print("\n--- {!r} ---".format(name))
    quiet, qinfo = record(dev, QUIET_S)
    if quiet is None:
        continue
    print("    silence: {} frames, id {}".format(qinfo['frames'],
                                                 qinfo['digest']))

    loud, linfo = record(dev, SECONDS + 0.3, playing=NOISE)
    if loud is None:
        continue
    print("    signal:  {} frames, id {}".format(linfo['frames'],
                                                 linfo['digest']))

    NFFT = 1 << int(numpy.floor(numpy.log2(min(len(quiet), len(loud), 32768))))
    fq, mq = spectrum(quiet, RATE, NFFT)
    fl, ml = spectrum(loud, RATE, NFFT)
    if fl is None or mq is None:
        print("    captures too short to analyse.")
        continue

    lv_sig = band_levels(fl, ml)
    lv_floor = band_levels(fq, mq)
    snr = {b: lv_sig[b] - lv_floor[b] for b in lv_sig if b in lv_floor}

    # Usable bandwidth: highest band still 10 dB clear of that mic's own
    # noise. Bands, not bins — the extreme-value trap that produced fake
    # 21-24 kHz figures in mic_check.py came from taking the highest single
    # bin over a threshold out of ~16000 noisy ones.
    clear = [b for b in FILLED if b in snr and snr[b] > 10.0]
    bandwidth = clear[-1][1] if clear else None
    # Did it reach the top of what the SIGNAL could show? Then the ceiling is
    # the stimulus, and the microphone may go higher.
    at_stim_limit = bool(clear) and clear[-1] == FILLED[-1]

    speech = [lv_sig[b] for b in SPEECH_BANDS if b in lv_sig]
    flatness = (max(speech) - min(speech)) if len(speech) > 1 else None

    peak = float(numpy.abs(loud).max())
    results.append({
        'name': name, 'peak': peak, 'rms': rms(loud),
        'floor': rms(quiet), 'snr': snr, 'levels': lv_sig,
        'bandwidth': bandwidth, 'flatness': flatness,
        'clipped': int(numpy.count_nonzero(numpy.abs(loud) >= 0.999)),
        'over': qinfo['over'] + linfo['over'],
        'heard': db(rms(loud)) - db(rms(quiet)),
        'at_stim_limit': at_stim_limit,
        # Every S/N figure here is measured AGAINST the silent capture, so if
        # that capture is not the microphone's real noise, all of them are
        # wrong by the same amount. Build 30f930f4 reported a -91.4 dBFS floor
        # and 50 dB S/N where the run before it had -68.1 dBFS and 31 dB: a
        # 23 dB shift in the denominator, not in the microphone. A muted or
        # gated input reads like that, and exact zeros are the evidence —
        # analogue self-noise never lands on exactly zero repeatedly.
        'zeros': float(numpy.count_nonzero(quiet == 0.0)) / max(len(quiet), 1),
        'gated': (float(numpy.count_nonzero(quiet == 0.0))
                  / max(len(quiet), 1) > 0.05) or db(rms(quiet)) < -85.0,
    })

if not results:
    print("\nNothing measured.")
    sys.exit(1)

print('\n' + '=' * 74)
print("mic_compare RESULTS — copy from this line down")
print("  build {} | {} Hz | level {:.2f} | {}".format(BUILD, RATE, LEVEL,
                                                      NOTE))
print("  test signal spans {:.0f}-{:.0f} Hz, so nothing above {:.0f} Hz can"
      " be".format(STIM_LO, STIM_HI, STIM_HI))
print("  measured at all — a '>' below means the ceiling is the SIGNAL's.")
# WHERE THE SOUND CAME OUT belongs with the results, not only in the header
# above the copy marker. It determines whether the comparison is valid at all:
# every mic must hear the same source at comparable exposure, and the output
# device decides that. Plugging in a headset moves playback to the earpiece,
# inches from the headset mic and across the room from the internal one — so
# the two are no longer comparable, and nothing else in the output said so.
print("  played through: {!r}".format(OUT_NAME))
print()
print("  {:<28} {:>7} {:>8} {:>7} {:>9} {:>8}".format(
        "microphone", "level", "floor", "S/N", "bandwidth", "speech"))
for r in results:
    print("  {:<28} {:>6.1f}dB {:>7.1f}dB {:>5.0f}dB {:>8} {:>7}".format(
            r['name'][:28], db(r['rms']), db(r['floor']), r['heard'],
            # No bandwidth for a row that did not hear the signal. Build
            # 362e7357 printed "16.0k" for an input listed as having heard
            # nothing (0 dB S/N): one band of eleven scraped past the 10 dB
            # threshold, on data the script had already ruled unusable. A
            # figure must not survive the rejection of what it was computed
            # from — the recurring bug of this whole exercise.
            ("n/a" if r['heard'] < 10 else
             "{}{:.1f}k".format('>' if r['at_stim_limit'] else '',
                                r['bandwidth'] / 1000.0)
             if r['bandwidth'] else "none"),
            "n/a" if r['heard'] < 10 else
            "{:.0f}dB".format(r['flatness']) if r['flatness'] is not None
            else "-"))
print("    level/floor: dBFS, gain-dependent. S/N: signal over that mic's own")
print("    noise. speech: spread across 250-4000 Hz — SMALLER is flatter.")

print("\n  signal over each mic's own noise, per band (dB):")
header = "  {:<28}".format("band")
for r in results:
    header += " {:>11}".format(r['name'][:11])
print(header)
for lo, hi in BANDS:
    if lo >= RATE / 2:
        break
    if not any((lo, hi) in r['snr'] for r in results):
        continue
    row = "  {:<28}".format("{}-{} Hz".format(lo, hi))
    for r in results:
        v = r['snr'].get((lo, hi))
        row += " {:>11}".format("{:+.1f}".format(v) if v is not None else "-")
    print(row)

# ── Which rows are the same microphone? ───────────────────────────────────
# 'default', 'pipewire' and 'sysdefault' are PATHS to whatever the system
# currently routes, not microphones. Testing every input therefore produces
# several columns of the same mic, and presenting those as a comparison would
# be its own kind of lie. Two paths to one microphone give near-identical
# band profiles — measurable, so measure it rather than hard-coding a list of
# names that would rot the moment the audio stack changed.
def same_source(a, b, tol=2.5):
    shared = [k for k in a['snr'] if k in b['snr']]
    if len(shared) < 4:
        return False
    return max(abs(a['snr'][k] - b['snr'][k]) for k in shared) < tol


# Group only rows that actually HEARD the signal. Two inputs that heard
# nothing have flat ~0 dB profiles and therefore "match" each other perfectly
# — which grouped hw:0,0 with sysdefault on 2026-09-10 and called the result
# 3 distinct microphones. Matching on the ABSENCE of a measurement is not
# evidence of anything; a comparison of two silences is not a comparison.
heard_rows = [r for r in results if r['heard'] >= 10]
deaf_rows = [r for r in results if r['heard'] < 10]
groups = []
for r in heard_rows:
    for g in groups:
        if same_source(g[0], r):
            g.append(r)
            break
    else:
        groups.append([r])

if deaf_rows:
    print("\n  heard nothing (cannot be compared, and cannot be grouped —")
    print("  two silences look identical without being the same mic):")
    for r in deaf_rows:
        print("    {} ({:+.0f} dB over its own noise)".format(r['name'],
                                                              r['heard']))

if any(len(g) > 1 for g in groups):
    print("\n  these are the SAME microphone reached different ways (their")
    print("  band profiles match within 2.5 dB), so they are one mic, not"
          " several:")
    for g in groups:
        if len(g) > 1:
            print("    {}".format(' = '.join(x['name'] for x in g)))
    print("  {} distinct microphone{} among the {} that heard the signal."
          .format(len(groups), '' if len(groups) == 1 else 's',
                  len(heard_rows)))

# ── Problems worth naming ─────────────────────────────────────────────────
notes = []
for r in results:
    if r['clipped']:
        notes.append("{}: CLIPPING ({} samples). Lower input gain or"
                     " --level.".format(r['name'], r['clipped']))
    if r['heard'] < 10:
        # If NOTHING heard it, suspect playback or volume. If some mics heard
        # it well and others did not, volume is not the explanation — unequal
        # exposure is. Plugging in a headset routes playback to the earpiece,
        # so the headset mic hears it at close range and the internal mic
        # hears nothing; on 2026-09-10 that produced a 16 dB "difference
        # between microphones" that was purely geometry. Kent spotted it,
        # not the script.
        if any(o['heard'] >= 10 for o in results):
            # TWO causes, and levels cannot separate them: an empty jack and
            # a mic that simply is not exposed to the playback both read as
            # signal == own noise. Build a7ae3970 asserted the headset
            # explanation for an empty jack with the headset UNPLUGGED. State
            # both and let the user, who can see the hardware, decide.
            notes.append(
                "{}: heard nothing ({:.0f} dB) while another input heard the"
                " signal well, so volume is not the cause. Either nothing is"
                " connected to that input, or it is not exposed to '{}' —"
                " playback routed to a headset earpiece reaches the headset"
                " mic and not the built-in one. Its row cannot be compared"
                " either way.".format(r['name'], r['heard'], OUT_NAME))
        else:
            notes.append("{}: barely heard the signal ({:.0f} dB over its own"
                         " noise). Raise --level or the speaker volume; this"
                         " mic's row means little."
                         .format(r['name'], r['heard']))
    if r['peak'] > 0.9:
        notes.append("{}: very hot (peak {:.0f}%), near clipping."
                     .format(r['name'], 100 * r['peak']))
    if r['over']:
        notes.append("{}: {} input overflows — samples were dropped."
                     .format(r['name'], r['over']))
    if r['zeros'] > 0.05 or db(r['floor']) < -85.0:
        notes.append("{}: noise floor {:.1f} dBFS with {:.0f}% of the silent"
                     " capture at EXACTLY zero — that is a muted or gated"
                     " input, not microphone noise. Every S/N figure in this"
                     " row is inflated by however much the gate removed."
                     .format(r['name'], db(r['floor']), 100 * r['zeros']))

# The comparison itself, only where it is defensible.
# One representative per distinct microphone — ranking two paths to the same
# mic against each other would produce a "winner" that is an artefact of the
# software path, not a better microphone.
representatives = [max(g, key=lambda r: r['heard']) for g in groups]
usable = [r for r in representatives if r['heard'] >= 10]
if len(usable) > 1:
    print("\n  comparison (same signal, same room, so these are real")
    print("  differences between the microphones):")
    # S/N and noise floor BOTH come from the silent capture, so a gated input
    # invalidates both — rank without those rows rather than crowning one and
    # disclaiming it in a note underneath, which is what build 89a85217 did
    # ("best signal-to-noise: pipewire (35 dB)" directly above a note saying
    # that 35 dB was inflated by a gate).
    trusted = [r for r in usable if not r['gated']]
    if len(trusted) == 1:
        # "best signal-to-noise: X", "lowest noise floor: X", "flattest: X"
        # for the only candidate reads as three findings. It is none: there is
        # nothing to be better than.
        print("    ONLY ONE input qualifies — {} ({} of {} heard the signal"
              " and were not gated). Its figures stand on their own, but"
              " nothing here is a comparison."
              .format(trusted[0]['name'], len(trusted), len(results)))
        print("    {}: S/N {:.0f} dB, floor {:.1f} dBFS{}".format(
                trusted[0]['name'], trusted[0]['heard'],
                db(trusted[0]['floor']),
                ", speech spread {:.0f} dB".format(trusted[0]['flatness'])
                if trusted[0]['flatness'] is not None else ""))
    elif trusted:
        best_snr = max(trusted, key=lambda r: r['heard'])
        quietest = min(trusted, key=lambda r: r['floor'])
        print("    best signal-to-noise: {} ({:.0f} dB)".format(
                best_snr['name'], best_snr['heard']))
        print("    lowest noise floor:   {} ({:.1f} dBFS)".format(
                quietest['name'], db(quietest['floor'])))
        if len(trusted) < len(usable):
            print("    (ranked among the {} of {} inputs whose silence was"
                  " not gated)".format(len(trusted), len(usable)))
    else:
        print("    signal-to-noise: NOT RANKED — every input's silent capture")
        print("    was gated, so no trustworthy noise floor exists to measure")
        print("    against. Disable noise suppression on the input and re-run.")
    # Flatness is ALSO ranked among ungated inputs only. An earlier version
    # ranked it across all of them, reasoning that flatness comes from the
    # signal capture and a gate acts on the silence. That was wrong: the same
    # processing chain handles both captures. The signal is loud enough not to
    # be zeroed, but it is still spectrally shaped — so build fabea002
    # declared "flattest over speech: default (8 dB)" and was comparing a
    # noise-suppression DSP chain against a bare microphone, then calling the
    # difference a property of the microphone.
    flat = [r for r in trusted if r['flatness'] is not None]
    flattest = min(flat, key=lambda r: r['flatness']) if flat else None
    if flattest:
        print("    flattest over speech: {} ({:.0f} dB spread)".format(
                flattest['name'], flattest['flatness']))
    elif not trusted:
        print("    flattest over speech: NOT RANKED — see above.")
    print("    For recording speech, signal-to-noise and flatness matter;")
    print("    bandwidth rarely does, and here it is capped by the SPEAKER.")
elif len(usable) == 1 and len(representatives) > 1:
    notes.append("Only one microphone heard the signal well enough to"
                 " compare; the others' rows mean little.")
elif len(representatives) == 1 and len(results) > 1:
    # Only "all the same mic" when nothing was DROPPED for hearing nothing.
    # Build 527bbeda said "every input turned out to be the same microphone"
    # about a run holding two different mics — the second had been excluded
    # for inaudibility, not for being a duplicate, and the sentence read as a
    # finding about the hardware rather than about what the run could measure.
    if deaf_rows:
        notes.append("Only one microphone HEARD the signal, so there is"
                     " nothing to compare — not because the others are the"
                     " same mic, but because they could not hear it (see"
                     " above). Fix the exposure and re-run.")
    else:
        notes.append("Every input turned out to be the same microphone, so"
                     " there is nothing to compare. Plug in another mic and"
                     " re-run.")

gated_rows = [r for r in results if r.get('gated') and r['heard'] >= 10]
if gated_rows:
    print("\n  PROCESSED PATHS — measured, but not microphone measurements:")
    for r in gated_rows:
        print("    {}: {:.0f}% of its silence was exactly zero".format(
                r['name'], 100 * r['zeros']))
    print("  These are not a mic's own noise; something is emitting digital")
    print("  silence when it judges there is no speech (PipeWire's noise")
    print("  suppression does exactly that). Both captures pass through it,")
    print("  so level, S/N and flatness describe the PROCESSING, not the mic")
    print("  — which is why they are excluded from the ranking above.")
    print("  Worth knowing separately: this is what a recording through this")
    print("  path will actually contain. For speech documentation that is a")
    print("  problem, because suppression trained on speech removes quiet")
    print("  non-speech first — breathy release, final devoicing, weak")
    print("  fricatives — and the waveform still looks clean afterwards.")

if notes:
    print("\n  notes:")
    for n in notes:
        print("    * " + n)

print("\n  Reminder: the ceiling in 'bandwidth' is min(speaker, mic). A")
print("  speaker that stops at 15 kHz makes every mic read 15 kHz, so do")
print("  NOT read a sample rate off this. Ripple identical across mics is")
print("  the room; ripple that differs is the microphone.")
