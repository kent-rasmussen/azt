# Sound checks — what to run, and what each one can actually tell you

Manual scripts. Run from `azt/`, **with A-Z+T's own python** — not the
`python` on your PATH. Its packages (numpy, sounddevice) live in the app's
virtual environment, and a bare `python` will fail with `No module named
'numpy'` even on a machine where A-Z+T runs perfectly.

```bash
# Linux / macOS
../env/bin/python -um tests.manual.sound_check.<name>

# Windows (Git Bash / MINGW64)
../env/Scripts/python.exe -um tests.manual.sound_check.<name>
```

Each script runs bare, with defaults that do the sensible thing. If you get
the import error anyway, it now prints the exact command for your machine —
**do not `pip install` numpy into your system python**, since the app will not
use it there.

`--help` on any of them prints its documentation — what it measures, what the
numbers mean, and what it cannot tell you. Worth reading before believing a
result, but it is not a step: nothing needs a switch to run.

## Start here if anything won't run

```bash
python tests/manual/sound_check/where_am_i.py
```

**Standard library only** — no venv, no packages, no `-um`, and it imports
nothing from the app, so it works when nothing else does. Every other script
here needs numpy and sounddevice, which is exactly what is missing when
things won't start, so the diagnostics were unavailable precisely when they
were needed (Kent, on Windows and macOS, 2026-09-10: *"I can't even get it to
run."*).

It reports which interpreter you used, where A-Z+T's own one is, what each
can import, and the exact commands for that machine. It changes nothing.

## Run this one on other machines

**`collect_audio_facts.py`** — unattended, ~20 s, no setup. Reports numbers,
**judges nothing**, and prints a block to paste back.

```bash
../env/bin/python -um tests.manual.sound_check.collect_audio_facts --note='dell xps, office'
```

This is the one worth asking other people to run. Everything else here was
built while diagnosing a single laptop, and every threshold in A-Z+T's audio
code rests on that one machine's numbers. Kent, 2026-09-10: *"are we making
these tests more correct/general, or are we just diagnosing my machine?"* —
for anything involving a threshold, the latter. Facts from several machines
are what would change that.

The column that matters is **top-of-band**. One machine gave:

| what it was | top-of-band |
|---|---|
| genuine 192 kHz capture | −25 dB |
| 48 kHz linearly interpolated (ALSA `plug`) | −35 dB |
| 48 kHz band-limited upsample (PipeWire) | −105 to −142 dB |

The first two are 10 dB apart, from different sources. If that gap does not
separate the same way elsewhere, **A-Z+T cannot decide a sample rate from
this number and should stop trying** — which is a result, not a failure.

## The others, and their limits

| script | asks | trust it? |
|---|---|---|
| `collect_audio_facts.py` | what does this machine do? | yes — it reports, doesn't judge |
| `mic_check.py` | is this microphone any good? | level/clipping/noise floor yes; **bandwidth needs a broadband sound the user must make, and failed 7 of 8 attempts** |
| `mic_compare.py` | which of my mics is best? | comparisons yes, when every mic hears the same speaker; the bandwidth column is capped by the SPEAKER |
| `probe_real_capability.py` | which settings are real? | **NO — known false positives.** It calls 192 kHz REAL on two upsampling devices, because its noise floor is estimated from the part of the band the resampler's residue lives in. Needs the absolute test folded in. |
| `run_sound_check.py` | does record/play work at all? | yes, as a smoke test |
| `time_card_probe.py` | what does probing cost? | yes |

## Automated tests guarding this area

Headless, in `azt/tests/` — run with `pytest` from `azt/`:

| file | guards |
|---|---|
| `test_sound_units.py` | `zero_runs`, `rate_is_fake`, format ranking, config migration — including the int16 blind spot and the cheap-resampler gap, asserted so neither can be quietly closed by tuning |
| `test_sound_settings_contracts.py` | the settings object: choosing a card moves index AND name, `resolve_cards`' three outcomes, findings recorded but never acted on |
| `test_sound_ui_handlers.py` | the window's handlers, called on a stand-in `self` with no Tk: every setter re-derives the test filename, and `relabel_settings` does not |
| `test_take_diagnostics.py` | what a finished take TELLS THE USER — muted input, silence, dropouts, gating, one notice per take, and above all that a healthy take says nothing |
| `test_sound_plumbing.py` | `quiet_probing` gives stderr back (and leaks no descriptors), and the "wrong python" hint finds a venv on POSIX and Windows layouts |

Those last two exist because **every bug that reached Kent on 2026-09-10 was
in the seam between a UI handler and the state it changes** — not in the
measuring code, which the unit tests already covered. A picked microphone
that would not stick, a take written to a filename describing different
settings, a rate changed without being asked. None of it needs a display to
catch.

## What generalises, and what does not

Established today, and worth keeping straight:

**Generalises — physics or arithmetic, no fitted number:**

- exact-zero runs: analogue audio does not land on exactly zero repeatedly, so
  a long run is a gate, a mute or a dropout, on any hardware
- clipped samples at full scale
- frames ÷ elapsed vs the rate requested
- nothing above the old Nyquist ⇒ something upsampled (interpolation cannot
  create content it never had)

**Generalises as design:**

- device indices are unstable; identify by NAME (`--device=pipewire`, not `=6`)
- the device list mixes hardware PCMs with virtual paths whose destination
  changes underneath
- a figure computed from a rejected reference must be suppressed, not printed
  with a disclaimer next to it

**Does NOT generalise — one machine's numbers:**

- any threshold separating "real" from "cheaply resampled" by level. The two
  overlap; `rate_is_fake` therefore proves only the band-limited case and
  returns "can't tell" otherwise
- the 10 dB bandwidth criterion, "too quiet" at 1%, the 20 ms zero-run bar

## Traps that cost a day, so nobody repeats them

- **Check the level before reading a spectrum.** A capture at 99.6% of full
  scale is clipping, and everything downstream of clipping is manufactured. An
  imaging conclusion was drawn from exactly such a capture and retracted.
- **An absolute check beats a relative one.** Comparing three numbers to each
  other while never asking whether any was plausible on its own cost hours:
  all three were ~120 dB down, which was the finding, and the 10 dB
  differences between them were noise.
- **Prefer a prediction to a threshold.** "If this were converter noise the
  margin must fall when the signal rises" cannot be satisfied by accident; a
  number I picked can.
- **A stable figure is not a trustworthy one.** A bandwidth number barely
  moved across runs differing by 25 dB of level; that was an extreme-value
  artefact, and its stability was the symptom.
- **A test can perturb what it measures.** PipeWire's graph rate is sticky, so
  a 96 kHz probe left the graph there and the next 192 kHz probe was falsely
  accused of resampling.
- **A mirror/imaging detector was attempted four ways and abandoned.** See
  `_mirror_test_abandoned_2026_09_10` in `backend/core/sound.py` before
  building another one.
