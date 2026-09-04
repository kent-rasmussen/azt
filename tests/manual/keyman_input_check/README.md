# Keyman input check

**A five-minute manual test. It answers one question: does Keyman type
*consistently* into a browser engine, the way it already does into tkinter?**

Everything here is self-contained and ships in the repo, so a machine that has
done `git pull` already has it — nothing to install for tier 1, nothing to
configure, no paths to edit.

Why it exists: A-Z+T's UI may move from tkinter to a webview
(`agenda/webview_when_to_finish.md`). Keyman **works today** with tkinter, so
this is a regression check, not a hopeful experiment. There is one unresolved
2025 report on SIL's community forum of Keyman 18 on Windows 11
*"sporadically fail[ing] either to create special characters, or to produce any
output at all in Chrome and Edge"* — that is what we are trying to reproduce or
rule out. **"Sporadically" is why a single character proves nothing.**

## Run it

Requires: a **Windows** machine with **Keyman** and a **keyboard you actually
use** installed. (Linux with ibus-keyman is a useful smoke test but does not
transfer — the field is Windows and its input goes through TSF.)

| Tier | How | Installs | Tests |
|---|---|---|---|
| **1** | double-click **`run_edge.cmd`** | nothing | Chromium's input path with Keyman + TSF |
| **2** | `pip install pywebview` then `python run_pywebview.py` | pywebview (+ pythonnet on Windows) | WebView2 **hosted in a Python process** — the real configuration |

Tier 1 first: it costs nothing and can settle the question on its own if it
fails. Tier 2 matters because a WebView2 control inside a host app can handle
keyboard input differently from the Edge browser, so tier 1 passing is
necessary but not sufficient.

## What to do

1. Turn on your Keyman keyboard.
2. **Type your own real orthography.** There is no target string and nothing
   here knows what "correct" looks like — that is deliberate.
3. Type a line, press **Enter** to record it (in the textarea, **Shift+Enter**).
4. **Type the same line again and record it again.** That is the actual test:
   identical typing must produce identical codepoints. Repeat with the lines and
   sequences you care about — dead keys, multi-key sequences, tone marks,
   anything with combining diacritics.
5. Do a few hundred keystrokes **in each of the three boxes** — they are
   `<input>`, `<textarea>` and `contenteditable`, which genuinely differ under
   TSF, and a ported Transcriber would have to pick one.
6. Switch to another keyboard and back, then type some more. The forum report
   mentions other keyboards being involved.
7. Press **Build report**, then **Copy report**, and paste it into the agenda
   item (`agenda/webview_when_to_finish.md`, Research section) or back to Claude.

Optionally, for a baseline: type the same lines into the running app's
Transcriber and compare. That is the behaviour we must not regress from.

## Reading the result

- **`REPEAT MISMATCHES` is the verdict.** Same visible text, different
  codepoints, means the input path is not deterministic — different
  normalisation, a reordered mark, or a dropped one.
- **`swallowed?` and `spurious?` are hints, not failures.** A keystroke that
  produced no text within 300 ms, and text that appeared with no recent
  keystroke. Some keyboards do both legitimately (dead keys, composition,
  reordering), so read them next to the event log rather than as a score.
- The **event log** records `keydown` / `beforeinput` / `input` /
  `composition*` with `key`, `code`, `isComposing` and the field's codepoints
  after each event, so a failure is diagnosable and not just noticed.

**Pass:** several hundred keystrokes in each box, at normal speed, zero repeat
mismatches, no unexplained swallowed/spurious counts, and the same again after a
keyboard switch.

**Fail:** anything sporadic. Record it — a failure does not sink the webview
plan, because A-Z+T's own character palette (`frontend/transcriber.py`) is the
sanctioned input path and nothing *requires* an external keyboard. It means
pages where people type stay tkinter, deliberately, because taking someone's own
keyboard away is a real cost even when the function survives.

## Notes

- Not a pytest test, on purpose: no `test_` prefix, not collected, and
  `tests/manual/` is for things a human runs and judges.
- No `@font-face` here — the page asks for the tone-capable families by name so
  you see what the machine actually has. The **Environment** block reports which
  of Charis SIL / Charis / Doulos SIL / Gentium Plus / Andika resolve by name.
  Tone *rendering* (the `cv92` staveless-tone-letter feature) is a separate
  test; this one is only about input.
