# Machine time: the Mac and Windows walkthrough

Print this. It merges the standing queue in `agenda/cross_platform_checks.md`
(sections 1-7) with the webview backend work of 2026-09-22 to 09-24, which has
only ever run on Linux. Ordered to minimise restarts, not by topic.

**Version under test: 1.15.36** — confirm on the "Running A-Z+T v…" line.

**Use the app's own python**, not whatever is on PATH: a bare `python` reports
numpy and sounddevice missing on machines where the app runs fine.

| | macOS (Intel) | Windows |
|---|---|---|
| python | `<azt>/env/bin/python` | `<azt>\env\Scripts\python.exe` |

Below, `python` means that one. Record rather than debug: a failure here is
information, and chasing it in place costs the rest of the trip.

---

# Part 0 — both machines, before anything

- [ ] `python --version` → ____________
- [ ] OS version → ____________
- [ ] **clean install, or an existing one?** → ____________

Python version matters beyond this trip: ADR 0005 declares a floor of 3.10 and
a ceiling of 3.13 chosen from what still *resolves*, and wants evidence of
what is actually installed.

---

# Part 1 — macOS (Intel)

## 1.1 One tkinter session covers most of it

```
python main.py --tkinter
```

- [ ] starts, task chooser appears, version says 1.15.36
- [ ] **one** `display stack (...)` line per phase, and it does **not** say
      XWAYLAND. If it does, `USING_WAYLAND` is misfiring and the mutter guard
      is running where it must not. → `utilities/display.py`

**Still in the same session:**

**Alphabet chart timing.** Open the Alphabet Chart.
- [ ] seconds to appear → ______  (Linux/tkinter takes 37-42)
- [ ] any `scroller SLOW pass:` line in the log? ☐ yes ☐ no

That number decides something: fast here means the Tk round-trip volume only
hurts on X11 and is a Linux-desktop problem; slow here means it hurts
everywhere and is worth fixing rather than leaving to the webview port.
→ `agenda/wayland_freeze_audit.md`

**Leaving a page mid-load.** Open **Add and parse words with audio**, then
click **Tasks** before it finishes building.
- [ ] no traceback, and the chooser is really there and usable ☐
→ `agenda/work_outliving_its_window.md`

**Sound Settings.** Open it; look at the rate and format lists.
- [ ] rates descending, formats widest-first ☐
- [ ] each annotated "upsampled from {rate}" / "upsampled" / "not upsampled" ☐
- [ ] order: Speakers, Microphone, then "Recording settings" over Rate and
      Detail ☐
- [ ] closing returns to the task window ☐

The annotations come from what the hardware really reports, so this is a
genuinely different test here, not a repeat. → `agenda/honest_sound_settings.md`

**Two known macOS faults, while you are in a tkinter session:**

- [ ] **Do clicks land below the pointer?** Try the task chooser and a list of
      options. ☐ reproduces ☐ does not. The open lead is a 57px screen-height
      discrepancy; it has never been reproduced outside A-Z+T, and it may be
      the touchpad rather than us. → `agenda/macos_clicks_land_below_the_pointer.md`
- [ ] **Do theme colours reach buttons and frames?** Compare against the
      Linux look: ☐ themed ☐ system-default grey.
      → `agenda/macos_widget_colours_ignored.md`

## 1.2 The webview auto-install — new, never run off Linux

```
python main.py --webview
```

- [ ] a line saying it is installing pywebview → exactly what? ____________
- [ ] **no "restarting:" line.** That is the venv repair, which cannot apply
      here. If you see one, record and stop this step.
- [ ] the app came up, and **a window rendered with a legible page** ☐
- [ ] engine reported → ____________  (expect none: pywebview uses Cocoa)
- [ ] `display stack` line, and again **not** XWAYLAND ☐

**Then the same timing comparison:** open the Alphabet Chart under webview.
- [ ] seconds → ______

## 1.3 Second run — the stamp

```
python main.py --webview
```

- [ ] **no install line**, and no pip sync at startup ☐

That second point is its own item: the installer's dead PyAudio block was
withholding the requirements stamp, so pip re-ran on every open.
→ `agenda/pyaudio_to_sounddevice.md`

## 1.4 Ask for an engine that cannot exist here

```
python main.py --webview --engine=gtk
```

- [ ] what happened? ☐ used Cocoa anyway ☐ fell back to tkinter ☐ error
- [ ] **was there an on-screen notice** saying you did not get what you asked
      for? ☐ yes ☐ no

The notice is the point of the whole item. The app working anyway is not a
pass.

## 1.5 Intel-specific: torch and transcription

By marker in `requirements.txt`, an Intel Mac gets no torch and no
openai_whisper, so transcription is off and recording and sorting are not.
That is deliberate, not a fault.

- [ ] does the app say transcription is unavailable, clearly, without implying
      the machine is broken? ☐ yes ☐ no → wording: ____________
- [ ] is anything else degraded that should not be? ____________

**The "pin an older torch" option is probably already closed**, and by
arithmetic rather than judgement. `--versions torch` reported ZERO torch
builds for macos-x86_64 at python 3.13 and 3.14, and the last versions that
did ship Intel Mac wheels predate 3.13, so they have no build for it either
(Kent, 2026-09-24: "older torch is incompatible with current python, at this
point"). Settle it with one command on any machine before you go:

    python modules_by_python_version.py --versions torch --range 3.10-3.14

If the macos-x86_64 row is zero at every python at or above the 3.10 floor,
pinning an older torch would mean shipping an older PYTHON to that machine,
which collides with ADR 0005's install target. Then the decision is made and
what is left here is only the WORDING — which is the checkbox above, and is
worth your eye precisely because the machine is not broken and must not be
told it is. → `agenda/torch_for_intel_mac.md`

---

# Part 2 — Windows

## 2.1 One tkinter session, same shape

```
python main.py --tkinter
```

- [ ] starts, chooser appears, version 1.15.36 ☐
- [ ] `display stack` line present, and **not** XWAYLAND ☐
- [ ] Alphabet Chart seconds → ______ ; any `scroller SLOW pass:`? ☐
- [ ] leaving **Add and parse words with audio** mid-build: no traceback,
      chooser usable ☐
- [ ] Sound Settings: same four checks as 1.1 ☐

**Windows-specific UI fault, same session:**

- [ ] **'Change syllable profile name' page — does it scroll?** Reported as
      not scrolling on Windows specifically. ☐ scrolls ☐ does not
      → `agenda/syllable_profile_rename_scroll.md`

## 2.2 The webview auto-install

```
python main.py --webview
```

- [ ] install line → ____________ (expect pywebview, and `pythonnet` with it)
- [ ] **no "restarting:" line** ☐
- [ ] window rendered, page legible ☐
- [ ] engine reported → ____________ (expect `edgechromium`)
- [ ] Alphabet Chart under webview: seconds → ______

**If the window is blank, crashes during startup, or renders as unstyled
garbage**, that is the WebView2 runtime question and it has its own item.
Record and stop rather than chasing it:

- [ ] what you saw → ____________
- [ ] `C:\Program Files (x86)\Microsoft\EdgeWebView\Application`
      ☐ present ☐ absent
→ `agenda/windows_webview2_unchecked.md`

## 2.3 Second run, and a refused engine

```
python main.py --webview
python main.py --webview --engine=gtk
```

- [ ] second run: no install line ☐
- [ ] refused engine: on-screen notice? ☐ yes ☐ no

## 2.4 Keyman under WebView2 — the gate

This is the big one and it has its own harness. It passed on 2026-09-04 but
only verbally: no report file, no record of whether any line was typed twice,
and box 2 (the `textarea`) had a harness bug and has never been re-run.

```
tests\manual\keyman_input_check\run_edge.cmd
python tests\manual\keyman_input_check\run_pywebview.py
```

**Pass = several hundred keystrokes in each of three field types with zero
repeat mismatches, repeated after switching keyboards.**

- [ ] run_edge.cmd: box 1 ______ box 2 ______ box 3 ______
- [ ] run_pywebview.py: box 1 ______ box 2 ______ box 3 ______
- [ ] after a keyboard switch: ☐ clean ☐ mismatches
- [ ] **keep the report file** ☐

This is also the Windows column of the page walk for every typing page. A
failure does not break function, since the character palette is the sanctioned
input path, but it makes people feel bad about their own keyboard — so it is a
cost to weigh deliberately, not a bug to discover in the field.

---

# What to bring back

1. Both Alphabet Chart timings per platform, tkinter and webview. Four numbers.
2. Whether a window rendered under webview, per platform.
3. The engine each reported.
4. Any "restarting:" line — there should be none on either.
5. Whether the refused-engine notice appeared, per platform.
6. The Keyman report file.
7. Python version and OS version per machine.
8. Log files for anything that failed — the file, not a summary.

---

# Already known — do not chase

- **openai_whisper has no wheel anywhere.** Installs from source, is pure
  python, works. Not a platform fault.
- **Intel macOS gets no torch and no transcription**, by marker, deliberately.
- **`torch==2.7.1+cpu` comes from the PyTorch index**, not PyPI.
- **The venv repair and the GTK host checks are Linux-only.** Seeing them do
  nothing is correct. The host check should print "not applicable" for GTK on
  both these platforms.
- **Sounddevice record and playback are already confirmed** on all three
  platforms.
- Missing icons, card-image backing, splash parts and the language-object
  chooser are known broken everywhere and have their own items.
