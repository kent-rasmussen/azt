# ADR 0004 — UI backend direction: tkinter keeps shipping, and the second backend is served view-model pages in a subprocess, not a widget-parity port

- Status: **accepted 2026-09-14**, with the amendment below. D2's hybrid
  view-model seam and D7's subprocess are **superseded**; D1 is narrowed to
  an invariant.
- Date: 2026-09-04, amended 2026-09-14
- Scope: `azt/` (desktop) — `frontend/` and both UI backends (`ui_tkinter.py`,
  `ui_webview.py` + `frontend/webview_html/`), the `frontend/ui_interface.py` contract, and
  the task↔window seam in `tasks/ui_protocol.py`. Touches every page.
- Author: drafted by Claude (AI agent) with Kent, from
  `agenda/webview_when_to_finish.md`'s 2026-09-04 research. Records decisions that were
  implicit and contradictory across `Electron_Conversion.md`, `UIvTasks.md`, `CLAUDE.md` and
  the code.

## Context

A-Z+T's UI is tkinter with a pluggable backend seam (`AZT_UI_BACKEND`) and a partially built
pywebview backend. Two things forced the question in September 2026.

**The Tk layout/lifecycle bug class is expensive and recurring.** `wrap_to_container`,
`availablexy`/`_measure_siblings` (which subtracts sibling sizes from the *screen* and goes
negative by construction), three XWayland deadlocks in one day, and a `ScrollingFrame` sizing
rule that took a revert and a second attempt. Each is intermittent and several needed field
round trips. And **the audit's zero-code escape hatch is gone**: GNOME removed its X11
session, so "develop in an Xorg session" — the reason `wayland_freeze_audit`'s Phases 1–4
were rated optional — no longer exists.

**The gating unknown turned out not to gate.** WebView2 is part of Windows 11, present on
"the vast majority" of Windows 10 devices per Microsoft, installable per-user without admin
via a 2 MB bootstrapper, detectable in one registry read, with a Fixed-Version fallback as a
floor; and `pythonnet` ships Python 3.13 Windows wheels, so nothing has to build from source.

Two further facts shaped the direction rather than the go/no-go:

- **Tone rendering is a font-feature problem, not a mark-stacking one.** The `Renderer`
  exists because Tk can only name a font *family*, so it cannot reach a tuned build; PIL can
  open a *path*, which is why `utilities/fonts.py` lists `-tstv` (hidden-staves) files first.
  SIL exposes the same behaviour as OpenType character variants — `cv92` hide tone contour
  staves, `cv91` tone numbers, `cv90` Chinantec — which **CSS can request directly and Tk
  cannot express at all**.
- **`docs/NEXT_GENERATION.md`** independently wants these pages served to phones over a LAN.
  That is a bonus, explicitly **not** an input to priority.

## AMENDMENT 2026-09-14 — two complete backends, and tkinter is the way back

Kent, after the mixed-mode slice was built and measured:

> "So, ADR ATM is we aggressively pursue webview WITHOUT BREAKING ANYTHING in
> tkinter, leaving users free to switch back as they need to."

**A1. Two complete backends, chosen at launch.** `--webview` and `--tkinter`
each do the whole job. There is no per-page mixing, no page that exists in
only one, and no state where the user is half in each.

**A2. Webview is pursued aggressively.** Bug hunts first, page by page, to
turn "the webview is unfinished" into a list of named faults. Two such hunts
exist already: `agenda/webview_discards_widget_options.md` (ten options
accepted and silently thrown away) and Step 6(a) below, the AST audit of
calls against the contract.

**A3. TKINTER MUST NOT REGRESS, and that is what makes A2 safe.** The way
back is the whole safety net: a user who meets a webview fault switches to
`--tkinter` and keeps working. So a webview change that breaks tkinter costs
more than the webview gain — this is an invariant, not a preference, and it
is the operative meaning of D1. It is also why `frontend/served.py`'s
supervision was worth building even though the architecture it served is
dropped: the fallback instinct was right, and the switch now carries it.

**A4. The eventual goal is to drop tkinter** — but only once webview is
better on every page, judged by Kent, not by a checklist.

### What this supersedes, and why

**D7 (a mixed page runs in a SUBPROCESS) — DROPPED.** It was built and it
worked: a Tk host, a webview child, view model over a pipe, supervision with
timeout-and-fall-back, the splash rendering and exiting cleanly (v1.15.22).
It fails on cost, not on mechanism. A child that runs the app's real builder
needs the project loaded, which was 53 s of boot when the question was asked
(10.1 s after `rescan_instead_of_grouping.md`) — Kent: *"I dont' think I want
to reparse lift each time I want to show a page."* The only variant avoiding
that is one persistent child, which doubles the database in memory and needs
a continuous write-ownership rule between two processes.

**D2 (hybrid target, view-model seam for data-dense pages) — DROPPED for the
same reason.** Its point was that data-dense pages would be served rather
than ported. With A1, every page must exist under `--webview` in-process, so
the widget layer IS the path — which is what the chooser, splash, sound
settings and task windows already are. A per-page view model would be a
second implementation of a page that has to work anyway.

The thing D2 was right about survives: **no layout arithmetic crosses the
seam** (D3), and the browser's own layout is the reason a ported page is
simpler than its Tk counterpart, not merely different.

### Stale in the original, corrected here

- **D8** names `AZT_WEBVIEW_GUI`. It is `--engine=gtk|qt` now, under the
  standing switches-not-environment-variables rule (2026-09-08). The devtools
  console is `--console`, off unless asked for; transports can be forced with
  `--gdk-backend=` / `--qt-platform=`.
- **D1**'s "detect availability and fall back to tkinter with a log line" is
  only half met — `ui_backend.chosen()` refuses and substitutes, but
  `agenda/webview_requested_but_absent.md` is still open, and under A3 that
  matters more than it did.
- **D5**'s `requirements-webview.txt` has not been verified to exist.
- **D6** stands and gains weight: a ported page must state what replaced its
  XWayland flush rule, because under A1 the Tk page keeps its rule while the
  webview page needs none.

### What has to happen to the mixed-mode code

`frontend/served.py`, `frontend/served_splash.py`,
`frontend/served_alphabet_chart.py`, the `--serve=` switch, `SERVED_PAGES`,
and the three-way splash choice in `main.py` all implement D7. Under A1 they
have no role. Deleting them is mechanical; what should be kept is written
down here and in `agenda/webview_when_to_finish.md`, because two of the
findings that came out of building them — `Toplevel._on_loaded` never firing
for pre-start windows, and `image_pixels` silently dropped — were real
webview bugs that the exercise surfaced.

## Decision

**D1. tkinter remains the shipping backend** until a page fully replaces its Tk counterpart
*and* has run in the field without regression. `frontend/__init__.py` **detects availability
and falls back to tkinter with a log line**. Today it does neither: it is a bare `if/else`,
so `AZT_UI_BACKEND=webview` without pywebview installed starts the app **with no window at
all** — NWAA with no watchdog running. That is a bug to fix regardless of this ADR.

**D2. Hybrid target, not a widget-parity port.** Keep the existing widget layer for
**chrome** (windows, frames, buttons, labels, menus, tabs, tooltips) — it is built, cheap and
maps onto HTML controls. Add a **view-model seam for data-dense pages** (sort, verify, the
status boards, image lists): backend produces plain data, an HTML template renders it, CSS
owns layout. Those are exactly the pages where Tk's manual layout arithmetic hurts. A pure
widget-parity port would carry the imperative measure-then-wrap model into the browser; a
pure rewrite would discard ~2,500 working lines of transport and chrome.
**The altitude for this seam already exists**: `tasks/ui_protocol.py::TaskUI` — semantic,
toolkit-free, headless-stubbable, with `drive_work` as the one member the codebase actually
adopted. Grow the view model there rather than inventing a new seam. See
`agenda/ui_protocol_finish_or_kill.md`; that decision is a prerequisite, and it must **not**
be "finished" by adding the `wait`/`waitdone` family, which would harden it in Tk's
vocabulary.

**D3. No layout arithmetic crosses the seam.** In the webview backend `availablexy`,
`wrap_to_container`, `windowsize`, `reflow`, `update`/`update_idletasks` are **no-ops
returning sentinels**, never numbers a caller can lay out against. The three named helpers
never leaked (0 live sites outside `frontend/`); the leaked *raw* arithmetic is a 7-site
cleanup list (`main.py:651,652,920`; `tasks/tasks.py:1951,2019`;
`transcribe_glyph.py:342,384`) plus 15 `wraplength=` sites. `.grid(row=…, column=…)` in
backend/tasks is **not** part of this — it already maps to CSS Grid (`widgets.js:15-53`).

**D4. Fonts stay installed-only; tone behaviour comes from a FEATURE, not a tuned file.**
**No font is bundled** — the install package supplies Charis, so bundling would be dead
weight on most machines. `@font-face` uses `local(<alias>)` across the v6/v7 spellings with
`utilities.fonts.face_files()`'s resolved path as the in-place fallback. Staveless/ligated
tone letters come from `font-feature-settings: "cv92" 1` (and `cv90`/`cv91` where wanted).
The condition attached to not bundling is **faithful reporting**: add `font_version(path)`
(TTF `name`/`head`, `struct`, no new dependency) and `has_feature(path,'cv92')` (GSUB
FeatureList) to `utilities/fonts.py`, and **never block — always say so**, in the shape
`pdf_font()`/`warn_if_downgraded()` already uses. The Tk bitmap path (`Renderer` +
`Text`/`TextBase`, and the unwired webview mirror) is **replaced, not ported**, per page,
only after that page shows tone correctly by feature.
**The `-tstv` file preference is NOT removed.** Machines that have such a file get
stave-free output; removing the preference would take that away from everyone who has it —
a strict regression. Whether anyone but the dev has one is `agenda/tstv_font_availability.md`.

**D5. Nothing enters `requirements.txt` until D1's condition is met.** Webview dependencies
live in `requirements-webview.txt` (opt-in), because `requirements.txt` re-installs on every
install whose venv stamp changes, and a bad line there has broken every Windows install
before (`allosaurus`, 2026-07-16).

**D6. The XWayland flush comments are load-bearing and must be re-decided per page, not
deleted.** Twelve sites in `backend/`+`tasks/` encode X11/XWayland behaviour as backend
correctness — including `analysis.py:769,776`, where the X11 32767 px window cap and "a big
batch floods XWayland" set **batch sizes**. Under a browser these become *silently wrong*
rather than failing loudly. Any ported page must state what replaced its flush rule.

**D7. A mixed-backend page runs in a SUBPROCESS, never in-process.** `webview.start()` and
Tk's `mainloop()` both require the main thread, so in-process mixing is unavailable. A page
selected for the webview runs as a child: **view model in, result out**; the parent Tk keeps
the mainloop and therefore keeps `VisibilityWatchdog`/`QuitOnlyGuard`, and can **time out,
kill and re-render the page in Tk** if the child wedges. Suite precedent: the collab daemon's
Kivy subprocess UIs (`requirements.txt:63-67`, 2026-07-16).

**D8. The Linux renderer is a setting, defaulting to GTK.** `AZT_WEBVIEW_GUI` →
`webview.start(gui=…)`; today `ui_webview.py:1815` passes no `gui=` and `debug=True`
unconditionally (gate that on `program['testing']`). GTK by default so the app looks native
on an Ubuntu desktop; Qt/QtWebEngine on demand for engine parity with the Windows field and
as the escape hatch for WebKitGTK's DMABUF blank-window bug on NVIDIA + Wayland. The page
itself is our own HTML/CSS and looks identical either way; what differs is native chrome —
decorations, file dialogs, menus.

## Consequences

- **The port is page-at-a-time and reversible.** Two frontends are maintained only for pages
  actually ported. That tax is already being paid silently: CHANGELOG 1.15.x records no-op
  mirrors added to `ui_webview` purely to keep parity.
- **`ui_interface.py` stops being the target for new work.** It is Tk's vocabulary written as
  an ABC — it *mandates* `winfo_screenwidth`, `winfo_reqwidth`, `update_idletasks`, `after`,
  `wait_window`, `tk_popup` — so conformance to it does not buy portability. The per-page
  view model becomes the target.
- **`wait_window(canary_widget)` gets real semantics** in the webview backend (a per-widget
  waiter registry keyed on the already-recursive `destroy`), unblocking ~30 call sites
  without rewriting them.
- **Keyman is checked before any typing page is ported, and its cost is political.** It works
  with tkinter today. A failure does not break function — the `Transcriber` character palette
  is the sanctioned input path — it makes people feel bad about their own keyboard, which is
  a cost to weigh deliberately, not a bug to discover in the field. If it fails, typing pages
  keep their Tk builders and this ADR governs the rest.
- **Tone features are a genuine veto for tone pages.** If `cv92` does not render in WebView2,
  those pages are not ported; the `Renderer` stays.
- **`wayland_freeze_audit` Phase 2 must not be done for pages scheduled to be ported** — it
  rewrites exactly the flush-then-measure code a ported page deletes.
- **No trigger is recorded, deliberately.** Kent's rule is value versus cost in his own
  judgement, so `agenda/webview_when_to_finish.md` carries a **ledger** that is appended to
  as bugs are paid for and measurements come in. Two gates (Keyman, tone features) are
  binary preconditions, not value judgements.
- A-Z+T 2.0's multi-client sort would get its client pages as a by-product. This is recorded
  as a non-reason: it did not inform priority.
