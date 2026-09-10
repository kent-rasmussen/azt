#!/usr/bin/env python3
# coding=UTF-8
"""Manual sound check — and the BEFORE/AFTER instrument for the PyAudio →
sounddevice port (agenda/pyaudio_to_sounddevice.md).

    cd <azt>            # must run from the azt directory
    ../env/bin/python tests/manual/sound_check/run_sound_check.py --help

WHY A BASELINE. The port's done-criteria include "same cards listed, same
rates and formats offered, same files written" — which is unfalsifiable by
eye. So: run this on the CURRENT backend and save the answer, do the port,
run it again and compare. A difference is then a fact, not an impression.

    # before the port
    ... run_sound_check.py --save=before.json
    # after
    ... run_sound_check.py --compare=before.json

WHAT IT CANNOT TELL YOU. Whether the audio SOUNDS right. Dropouts, crackle,
latency and clipping need ears, so the record/playback steps ask you to
listen and say. That is the point of it being manual.

Conventions (standing rules): switches, never environment variables; nothing
is identified by colour — steps are named, and results are the words PASS,
FAIL and SKIP.
"""
import json
import platform
import sys
import time
import traceback
from pathlib import Path

# Run from the azt directory so `backend`, `io_put` etc. import.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

RESULTS = []          # (step, outcome, detail)
BASELINE = {}         # the machine-comparable facts


def switch(name, default=None):
    """--name=value → value; --name → True. No environment variables."""
    for arg in sys.argv[1:]:
        if arg == '--' + name:
            return True
        if arg.startswith('--' + name + '='):
            return arg.split('=', 1)[1]
    return default


def record(step, outcome, detail=''):
    RESULTS.append((step, outcome, detail))
    print('  {:<5} {}{}'.format(outcome, step,
                                ' — ' + detail if detail else ''))


def step(name):
    """Decorator: run a step, catch anything, keep going. A harness that dies
    on step 2 tells you nothing about steps 3-6."""
    def wrap(fn):
        def run(*a, **k):
            print('\n== {}'.format(name))
            try:
                return fn(*a, **k)
            except Skip as e:
                record(name, 'SKIP', str(e))
            except Exception as e:
                record(name, 'FAIL', '{}: {}'.format(type(e).__name__, e))
                if switch('traceback'):
                    traceback.print_exc()
        return run
    return wrap


class Skip(Exception):
    pass


def ask(question):
    """Ask the human. --yes answers everything affirmatively, for a
    no-questions run that still exercises the code paths."""
    if switch('yes'):
        print('  (--yes) {}  y'.format(question))
        return True
    try:
        return input('  {} [y/N] '.format(question)).strip().lower() == 'y'
    except (EOFError, KeyboardInterrupt):
        print()
        return False


if switch('help') or switch('h'):
    print(__doc__)
    print("""Switches:
  --seconds=N        Recording length (default 3)
  --device=N         Input device index to record from (default: configured)
  --save=PATH        Write the machine-comparable facts to PATH as JSON
  --compare=PATH     Compare this run against a saved JSON and report drift
  --no-record        Skip recording (and therefore playback of it)
  --no-play          Skip playback
  --no-beeps         Skip the tone-beep generator
  --yes              Answer every listening question 'yes' (unattended run)
  --traceback        Print full tracebacks on failure
  --help             This
""")
    sys.exit(0)


print('=' * 72)
print('A-Z+T sound check')
print('  platform: {} {} ({})'.format(platform.system(), platform.release(),
                                      platform.machine()))
print('  python:   {}'.format(sys.version.split()[0]))
BASELINE['platform'] = platform.system()
BASELINE['machine'] = platform.machine()
BASELINE['python'] = sys.version.split()[0]


# ─── 1. Does the audio stack import at all? ─────────────────────────────────
sound_mod = None
io_sound = None


@step('1. import the audio stack')
def step_import():
    global sound_mod, io_sound
    from backend.core import sound as _sound
    sound_mod = _sound
    BASELINE['backend_ok'] = bool(_sound.AUDIO_OK)
    BASELINE['sound_problems'] = [c for c, _e in _sound.SOUND_PROBLEMS]
    if not _sound.AUDIO_OK:
        # Not a harness failure: this is the machine telling us it has no
        # audio backend, which the program is designed to survive.
        record('1. import the audio stack', 'PASS',
               'imported, but NO BACKEND: {}'.format(
                   ', '.join('{}: {}'.format(c, e)
                             for c, e in _sound.SOUND_PROBLEMS) or 'unknown'))
        return
    from io_put import sound as _io
    io_sound = _io
    record('1. import the audio stack', 'PASS',
           'backend present, io_put.sound imported')


step_import()


# ─── 2. What devices does this machine have? ────────────────────────────────
@step('2. enumerate devices')
def step_devices():
    if sound_mod is None or not sound_mod.AUDIO_OK:
        raise Skip('no audio backend')
    iface = sound_mod.AudioInterface()
    names = {}
    try:
        host = iface.get_host_api_info_by_index(0)
        count = host.get('deviceCount')
        for i in range(count):
            info = iface.get_device_info_by_host_api_device_index(0, i)
            names[i] = {'name': info.get('name'),
                        'in': info.get('maxInputChannels'),
                        'out': info.get('maxOutputChannels'),
                        'rate': info.get('defaultSampleRate')}
    finally:
        try:
            iface.terminate()
        except Exception:
            pass
    for i, d in sorted(names.items()):
        print('        [{}] {}  in={} out={} default_rate={}'.format(
            i, d['name'], d['in'], d['out'], d['rate']))
    BASELINE['devices'] = names
    record('2. enumerate devices', 'PASS',
           '{} device(s)'.format(len(names)))


step_devices()


# ─── 3. Which rates and formats survive probing? ────────────────────────────
# This is the one most likely to shift under a backend swap, and the one the
# settings UI shows users — so it is the heart of the before/after diff.
@step('3. probe rates and formats')
def step_probe():
    if sound_mod is None or not sound_mod.AUDIO_OK:
        raise Skip('no audio backend')
    settings = _settings()
    if settings is None:
        raise Skip('could not build SoundSettings (see step 4 detail)')
    cards = getattr(settings, 'cards', None)
    if not cards:
        raise Skip('no probed card table on the settings object')
    summary = {}
    for io in ('in', 'out'):
        for card, rates in (cards.get(io) or {}).items():
            key = '{}:{}'.format(io, card)
            summary[key] = {str(r): sorted(map(str, fmts))
                            for r, fmts in rates.items()}
            print('        {} {} → {}'.format(
                io, cards.get('dict', {}).get(card, card),
                ', '.join('{}Hz[{}]'.format(r, len(f))
                          for r, f in sorted(rates.items()))))
    BASELINE['probed'] = summary
    record('3. probe rates and formats', 'PASS',
           '{} card/direction combination(s)'.format(len(summary)))


_SETTINGS = []


def _settings():
    """One SoundSettings for the run, or None with the reason recorded.

    Deliberately tolerant: SoundSettings wants a program and a language, and
    its constructor has a documented sharp edge (a fallback that accepts an
    audio handle where `program` belongs — see transcriber.py:87-99). If it
    cannot be built here, the device steps still ran and said so.
    """
    if _SETTINGS:
        return _SETTINGS[0]
    try:
        from backend import langtags
        languages = langtags.Languages()
        language = languages.get_obj('tbt')   # as io_put/sound.py's own __main__
        settings = sound_mod.SoundSettings(analang_obj=language)
        _SETTINGS.append(settings)
        return settings
    except Exception as e:
        record('   (SoundSettings)', 'FAIL',
               '{}: {}'.format(type(e).__name__, e))
        _SETTINGS.append(None)
        return None


step_probe()


# ─── 4. Record ──────────────────────────────────────────────────────────────
recorded = []


@step('4. record')
def step_record():
    if switch('no-record'):
        raise Skip('--no-record')
    if io_sound is None:
        raise Skip('no audio backend')
    settings = _settings()
    if settings is None:
        raise Skip('no settings object')
    seconds = float(switch('seconds', 3))
    out = Path(__file__).with_name('sound_check_recording.wav')
    device = switch('device')
    if device is not None:
        settings.audio_card_in = int(device)
    print('        recording {}s to {} — SAY SOMETHING'.format(seconds, out.name))
    # Three arguments, and the method is start(): I wrote this harness with
    # two and called a `record()` that does not exist (2026-09-09), which
    # would have failed step 4 for a reason having nothing to do with audio.
    rec = io_sound.SoundFileRecorder(str(out), settings.audio, settings)
    rec.start()
    time.sleep(seconds)
    rec.stop()
    size = out.stat().st_size if out.exists() else 0
    BASELINE['recorded_bytes_nonzero'] = size > 44   # 44 = bare WAV header
    if size <= 44:
        record('4. record', 'FAIL',
               'file is {} bytes — header only, no audio'.format(size))
        return
    recorded.append(out)
    record('4. record', 'PASS', '{} bytes'.format(size))


step_record()


# ─── 5. Play it back ────────────────────────────────────────────────────────
@step('5. play back the recording')
def step_play():
    if switch('no-play'):
        raise Skip('--no-play')
    if io_sound is None:
        raise Skip('no audio backend')
    if not recorded:
        raise Skip('nothing was recorded')
    settings = _settings()
    player = io_sound.SoundFilePlayer(str(recorded[0]),
                                      settings.audio, settings)
    player.play()
    time.sleep(float(switch('seconds', 3)) + 1)
    heard = ask('Did you hear the recording, clean (no crackle or gaps)?')
    BASELINE['playback_heard'] = bool(heard)
    record('5. play back the recording', 'PASS' if heard else 'FAIL',
           'you heard it' if heard else 'you did not hear it cleanly')


step_play()


# ─── 6. Beeps ───────────────────────────────────────────────────────────────
# The tone-beep generator, which is what Transcriber uses. This is the path
# io_put/sound.py's own __main__ block exercises.
@step('6. tone beeps')
def step_beeps():
    if switch('no-beeps'):
        raise Skip('--no-beeps')
    if io_sound is None:
        raise Skip('no audio backend')
    settings = _settings()
    beeps = io_sound.BeepGenerator(audio=getattr(settings, 'audio', None),
                                   settings=settings)
    beeps.compile()
    beeps.play()
    time.sleep(2)
    heard = ask('Did you hear the beeps?')
    BASELINE['beeps_heard'] = bool(heard)
    record('6. tone beeps', 'PASS' if heard else 'FAIL',
           'you heard them' if heard else 'you did not')


step_beeps()


# ─── Report ─────────────────────────────────────────────────────────────────
print('\n' + '=' * 72)
print('Results')
for name, outcome, detail in RESULTS:
    print('  {:<5} {}{}'.format(outcome, name, ' — ' + detail if detail else ''))
counts = {}
for _n, outcome, _d in RESULTS:
    counts[outcome] = counts.get(outcome, 0) + 1
print('  ' + ', '.join('{} {}'.format(v, k) for k, v in sorted(counts.items())))

save = switch('save')
if save:
    Path(save).write_text(json.dumps(BASELINE, indent=2, sort_keys=True,
                                     default=str))
    print('\nBaseline written to {}'.format(save))
    print('After the port, run:  --compare={}'.format(save))

compare = switch('compare')
if compare:
    print('\n' + '=' * 72)
    print('Comparison with {}'.format(compare))
    try:
        old = json.loads(Path(compare).read_text())
    except Exception as e:
        print('  could not read it: {}'.format(e))
        sys.exit(1)
    drift = 0
    for key in sorted(set(old) | set(BASELINE)):
        was, now = old.get(key, '<absent>'), BASELINE.get(key, '<absent>')
        if was != now:
            drift += 1
            print('  CHANGED {}'.format(key))
            print('     was: {}'.format(json.dumps(was, sort_keys=True,
                                                   default=str)[:400]))
            print('     now: {}'.format(json.dumps(now, sort_keys=True,
                                                   default=str)[:400]))
    if drift:
        print('\n  {} difference(s). Expected ones for the sounddevice port:'
              '\n    - probed formats losing 24-bit (decided: dropped)'
              '\n    - device INDEXES and names, if the backend enumerates'
              '\n      differently — check the names still identify the same'
              '\n      hardware, since the indexes are what get persisted.'
              '\n  Anything else wants explaining before the port is done.'
              .format(drift))
    else:
        print('  No differences.')

sys.exit(1 if any(o == 'FAIL' for _n, o, _d in RESULTS) else 0)
