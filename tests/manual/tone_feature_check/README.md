# Tone feature check

**A ten-minute manual test. It answers one question: can a browser render
A-Z+T's tone letters the way the app must show them — joined into contours,
and (where wanted) without staves?**

This is **Step 2** of `agenda/webview_when_to_finish.md`, and unlike the Keyman
check it has a **real kill condition**. Keyman was political: a failure there
costs acceptance, not function. This one is functional. If tone letters cannot
render correctly in a webview, tone pages cannot be ported and the whole
webview item shrinks to non-tone pages.

Everything here is self-contained and ships in the repo. Tier 1 needs nothing
installed and no paths edited.

## Why it is not obvious either way

The app's current staveless mechanism is **a font FILE, not a feature**.
`utilities/fonts.py:31-37` lists the `-tstv` (hidden-staves) builds *first* for
every family, and `Renderer.render` opens the first one that exists with
`PIL.ImageFont.truetype(path)`, drawing the string to a bitmap that becomes the
label's image. **That is why the Renderer exists at all:** Tk asks for fonts by
*family name* and can never select a particular file; PIL opens a *path*, so it
can.

A browser has a lever Tk does not: it can ask the **stock installed font** for
the feature directly, with `font-feature-settings: "cv92" 1`. Per SIL's feature
page (`software.sil.org/charis/features/`):

| Feature | Tag | Affects |
|---|---|---|
| Chinantec tones | `cv90` | U+02CB U+02C8 U+02C9 U+02CA |
| Tone numbers | `cv91` | U+02E5–02E9, U+A712–A716 |
| **Hide tone contour staves** | **`cv92`** | U+02E5–02E9, U+A712–A716 |

`cvNN` variants are **off by default**, and the Renderer passes no `features=`
to Pillow — so the "no features" column of the matrix should look like what the
app does today *unless* this machine has a `-tstv` file.

## Run it

| Tier | How | Installs | Tests |
|---|---|---|---|
| **1** | double-click **`run_edge.cmd`** (Windows) or open `index.html` in any browser | nothing | the browser engine |
| **2** | `python run_pywebview.py` | pywebview (+ pythonnet on Windows) | the **embedded** webview — the real configuration |
| **baseline** | `python render_pil_baseline.py` | Pillow, and the azt checkout | what the app draws **today**, via the Renderer's own mechanism |

Run tier 1 on **both** machines: the Linux box is WebKitGTK, Windows is
WebView2/Chromium, and both are HarfBuzz-based, so a **difference between them
is itself diagnostic**.

On Linux, pywebview also needs a host toolkit — `run_pywebview.py` prints the
two install routes if neither is present.

## What to do

1. Open the page. Read the **Environment** block: it reports
   `devicePixelRatio`, the resolvable font families, and CSS px-per-mm.
2. **Hold a real ruler against the two bars.** They claim 100 mm and 4 inches.
   CSS assumes 96 px = 1 inch regardless of the real display, so a mismatch on
   a scaled screen is *expected* — record it, don't fix it. This answers the
   DPI question (§5 of the agenda item) in the same pass.
3. Pick a family in **Font under test** and read the **matrix**. The two
   contour rows are the ones that matter: `˥˩` must render as **one** falling
   contour on a shared stave, not two letters side by side.
4. Compare the `"cv92" 1` column against `"cv92" 0`. A visible difference means
   the feature is reaching the font.
5. **Get a `-tstv` build into the page** — the direct test of whether the app's
   *current* staveless mechanism survives the port. Three ways in, because one
   is not enough:
   - **drag the `.ttf` onto the drop zone** — works in a browser;
   - **the file picker** — goes through the native file dialog, so it works
     where the drop does not;
   - **do nothing**: `run_pywebview.py` searches the font directories for a
     `*tstv*` file and injects the bytes itself, saying so on the console. Pass
     a path as its first argument to choose the file.

   **Drag-and-drop does not work under pywebview** (observed 2026-09-04: fine
   in the browser, nothing under pywebview). An embedded webview does not
   always deliver a dropped file to the page. That is why the other two exist —
   and it is worth knowing on its own, since a ported A-Z+T would lose any
   feature built on dropping OS files into the window.
6. Look at the family marked **← wrong on purpose** (`Chariss SIL`). It shows
   the silent fallback that `theme.css` currently produces, which is the thing
   the "your font can't do this" notice has to catch.
7. Answer the seven **Verdict** questions by eye.

**Two things the page tells you that your eyes cannot:**

- **The diagnostic box under the matrix** reports what the browser *actually
  computed* for a probe cell — the resolved `font-feature-settings`, the
  resolved family, and whether that family exists here. **Read it before
  concluding anything.** If it says `normal`, the CSS never reached the text.
  (This exists because the first version of the page silently dropped every
  declaration, and the result was indistinguishable by eye from "the font does
  not support cv92".)
- **The feature list beside a loaded font file** parses the file's own `GSUB`
  and `GPOS` tables and names every feature tag in it, flagging `cv90/cv91/cv92`
  and whether the file carries Graphite tables (`Silf`/`Glat`) as well as
  OpenType. That turns "cv92 did nothing" into two different answers: *the font
  has no such feature*, or *it has it and the engine ignored it*. Only possible
  for a font whose bytes the page holds — an installed font asked for by name
  cannot be inspected.

Use the **extra feature column** box to try any tag the inspector reports —
`"ss01" 1`, another `cvNN`, whatever the font actually has.

Optionally run `render_pil_baseline.py` and put its PNGs beside the page. Its
console output also names the font file that actually won for each family —
which is the open question in `agenda/tstv_font_availability.md`.

## Reading the result

- **Any one of these three passing is enough to proceed:** tone letters join;
  `cv92` hides staves; a dropped `-tstv` file renders staveless.
- **All three failing is the kill condition.** Record it and tone pages stay
  tkinter.
- **`Charis SIL` vs `Charis`** is not a typo — v6 ships the family "Charis SIL",
  v7 renames it to "Charis", and a machine can carry either. The dev box
  resolves `Charis SIL=yes / Charis=no`. `webview_html/theme.css:24` asks for
  `Charis` with **no `@font-face`**, so on that machine a real webview page
  silently falls back to DejaVu. Confirming that on a second machine is useful.
- **Divergence between machines is expected and must not be "fixed".** A
  machine with a tuned font legitimately renders differently from one without;
  the `-tstv` preference is not to be removed, because pulling it would take
  stave-free output away from anyone who has the file.

**Read the verdict off the screen.** The report button is a convenience — the
Keyman run established that a field Windows machine may have neither write
access nor the wish for one, so nothing here depends on getting text back.

## Notes

- Not a pytest test, on purpose: no `test_` prefix, not collected, and
  `tests/manual/` is for things a human runs and judges.
- `index.html` imports nothing from azt and duplicates the family alias list
  from `utilities/fonts.py` on purpose — it has to run on a machine that has
  only done `git pull`. `render_pil_baseline.py` is the opposite: it imports
  the real table, so it is dev-box only.
