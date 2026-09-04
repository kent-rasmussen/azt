# ADR 0004 — UI backend direction: tkinter keeps shipping, and the second backend is served view-model pages in a subprocess, not a widget-parity port

- Status: **proposed**
- Date: 2026-09-04
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
