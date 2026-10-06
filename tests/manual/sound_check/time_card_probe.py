#!/usr/bin/env python3
# coding=UTF-8
"""How much does REAL sound-card probing cost, and what does it change?

    cd <azt>
    ../env/bin/python tests/manual/sound_check/time_card_probe.py

WHY. `getactual()` (backend/core/sound.py) takes a `test=` flag, and its only
caller passes nothing — so `test=False`, and `is_format_supported` is never
called: every device is credited with all five candidate rates and all three
formats whether it can do them or not. The port is to probe for real at
startup (Kent, 2026-09-09), which is a startup-cost decision, so measure it
before committing rather than after. Kent: "set a test to time the difference
in probing sound cards."

WHAT IT MEASURES, on THIS machine's devices — the number that matters is not
a benchmark, it is "would a user notice at boot":

  1. PortAudio initialisation (paying for the handle at all).
  2. getactual(test=False) — today's behaviour: build the table by claiming.
  3. getactual(test=True)  — the honest version: ask the device every time.
  4. The DIFFERENCE IN THE TABLE: how many rate/format combinations the
     unprobed run claims that the probed run rejects. That is the size of the
     lie the current defaults are chosen from, and it is why playback opens
     192kHz/32-bit streams on cards that may support neither.

It builds no SoundSettings, needs no language, project or program: getactual
touches only `self.audio`, `self.hypothetical` and `self.cards`, so a stand-in
object with those three carries it. That keeps this runnable on any machine
with a sound card and nothing else set up.

Switches (no environment variables, no colour):
  --repeat=N     Time each pass N times and report the mean (default 3)
  --quiet        Skip the per-card table dump
  --help         This
"""
import sys
import time
import types
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

REPEAT = int(switch('repeat', 3))
QUIET = bool(switch('quiet'))

from backend.core import sound

if not sound.AUDIO_OK:
    print("No audio backend on this machine, so there is nothing to time:")
    for component, error in sound.SOUND_PROBLEMS:
        print("  {}: {}".format(component, error))
    sys.exit(1)


def fake_settings(audio):
    """The three attributes getactual actually uses, and nothing else."""
    fake = types.SimpleNamespace(audio=audio, cards=None)
    for name in ('sethypothetical', 'getactual'):
        setattr(fake, name,
                types.MethodType(getattr(sound.SoundSettings, name), fake))
    fake.sethypothetical()
    return fake


def combos(cards):
    """(device/direction count, rate/format combination count) in a table."""
    places = 0
    total = 0
    for io in ('in', 'out'):
        for _card, rates in (cards.get(io) or {}).items():
            places += 1
            for _fs, formats in rates.items():
                total += len(formats)
    return places, total


print('=' * 72)
print("Sound-card probe timing")

# 1. PortAudio init
t0 = time.perf_counter()
audio = sound.AudioInterface()
init = time.perf_counter() - t0
print("\n  PortAudio init:            {:.3f}s".format(init))

fake = fake_settings(audio)
ndev = len(fake.hypothetical['fss']), len(fake.hypothetical['sample_formats'])
print("  candidate rates x formats: {} x {}".format(*ndev))

# 2 & 3. The two passes.
results = {}
for label, test in (("unprobed (test=False, today)", False),
                    ("probed   (test=True)", True)):
    times = []
    for _i in range(REPEAT):
        t0 = time.perf_counter()
        fake.getactual(test=test)
        times.append(time.perf_counter() - t0)
    results[test] = {'mean': sum(times) / len(times),
                     'min': min(times), 'max': max(times),
                     'cards': fake.cards,
                     'shape': combos(fake.cards)}
    r = results[test]
    print("\n  {}".format(label))
    print("    mean of {}: {:.3f}s   (min {:.3f}s, max {:.3f}s)".format(
        REPEAT, r['mean'], r['min'], r['max']))
    print("    table: {} card/direction entries, {} rate+format combinations"
          "".format(*r['shape']))

try:
    audio.stop()
except Exception as e:
    print("\n  (couldn't terminate the audio handle: {})".format(e))

# 4. What honesty costs, and what it changes.
unprobed, probed = results[False], results[True]
extra = probed['mean'] - unprobed['mean']
print("\n" + '=' * 72)
print("Cost of probing for real: {:+.3f}s at startup".format(extra))
print("  (plus {:.3f}s for PortAudio init, which is paid either way)"
      "".format(init))
claimed = unprobed['shape'][1]
real = probed['shape'][1]
print("\nTable content: {} combinations claimed, {} actually supported"
      "".format(claimed, real))
if claimed:
    print("  → {} of {} ({:.0f}%) of today's table is not real"
          "".format(claimed - real, claimed,
                    100.0 * (claimed - real) / claimed))
if real == 0:
    print("  WARNING: the probe rejected EVERYTHING. Either this machine's"
          "\n  devices refuse every candidate, or is_format_supported is not"
          "\n  usable here — check before concluding the table should shrink.")

if not QUIET:
    print("\nPer card, what survived probing (name: rates -> formats kept):")
    cards = probed['cards']
    for io in ('in', 'out'):
        for card, rates in sorted((cards.get(io) or {}).items()):
            name = cards.get('dict', {}).get(card, card)
            print("  [{}] {} {}".format(io, card, name))
            for fs in sorted(rates, reverse=True):
                print("        {:>7} Hz: {}".format(fs, rates[fs]))

print("\nRead this as: is the difference something a user would notice while"
      "\nA-Z+T starts? If yes, probing belongs behind the splash's progress"
      "\nbar, or on the selected card only. If no, probe and stop guessing.")
