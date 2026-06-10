# Code Audit Findings

Audit started: 2026-04-27
Re-verified: 2026-06-05
Fixes applied: 2026-06-05 (app v1.2.0)
Branch: settings_rebuild

Scope notes
- Skipping commented-out code unless it indicates an unfinished feature.
- Focusing on bugs, latent issues, performance, architectural smells, and abstraction leaks.

## Fixes applied 2026-06-05 (app v1.1.0 → v1.2.0)

This session's code changes, beyond the fixes already present at re-verification:

- **Stuck-progress-dialog (`wait()`/`waitdone()`) — systemic fix.** Added a `waiting()` context manager to `ui_tkinter.Waitable` and `ui_webview`, declared on `ui_interface.WaitableInterface`. Converted all 16 exposed openers (9 via `with …waiting():`, 7 via `try/finally`; 2 async sites left by design) so the progress dialog can no longer be left open by an exception or early return. The analang/demolang flows were restructured to show modal errors *after* the dialog closes; `generator.py:955` Multislice also now restores `sys.stdout` via a nested `finally`. See the dedicated section below for the per-site table and status.
- **#13** residual `waitdone()` gap closed by the above.
- **settings/__init__.py** — deleted the orphaned `import gettext as _gettext` (the live translator is `from utilities.i18n import _`).
- **Not yet verified by execution**: no test suite + no shell in the authoring session — a `py_compile` pass and a manual smoke run of the converted flows are still pending.

Still open after this session (verified 2026-06-06): none of the top-15 — only the broader bare-`except`/`exit()` cleanup tracked per-file below (io_put/lift.py, utilities/*, settings/manager.py, etc.). All of #1–#15 are fixed except #13 (downgraded). #7, #9, #12, #15 were fixed externally; an earlier draft mislabeled #9/#15 — see the Re-verification note.

## ErrorNotice spawns a second Tk root → `pyimage doesn't exist` crash + oversized error page (fixed 2026-06-08, v1.2.7)

`vcs.findpresentremotes` (vcs.py:372) showed an `ErrorNotice(..., image='USBdrive', wait=True)` with **no parent/program**. `error_notice.py` then fell into `else: parent=ui.Root()` and created a **second Tk interpreter** (log: `Root called with program None` → dummy `Kim theme` block). The `'USBdrive'` image resolves against the main interpreter's theme, so in the new interpreter it's invalid → `_tkinter.TclError: image "pyimage111" doesn't exist` (and the `pyimage89` iconphoto errors). That exception bounced the app to the problem page (**bug #1**); and with two live `Tk()` roots, `tkinter.font.Font` binding got confused, rendering the error page's native-font text grossly oversized (**bug #2** — *not* the Renderer; the only special-char label there is `norender=True`). **Fix:** (a) `error_notice.py` reuses the existing app root instead of constructing a fresh `Root` when no parent/program is supplied (systemic — protects every unparented ErrorNotice); (b) `vcs.findpresentremotes` passes `program=self.program` explicitly. Eliminating the dummy root removes the cross-interpreter image error and the font confusion. Confirmed fixed by the user. Lesson: two disproven hypotheses (Renderer scaling; tk point-DPI) before the log showed the real cause — the traceback was the decisive artifact.

**Refinement (v1.2.8):** the first cut had `error_notice` reach into `tkinter._default_root`, which (1) leaks the backend's tkinter detail across the `from frontend import ui` boundary and (2) returns a *bare* root that may not be the themed `ui.Root` with `.theme.photo` (a fakeroot/dummy lacks photos — so `image='USBdrive'` could still fail). Replaced with `ui.default_root()`: each backend (`ui_tkinter`, `ui_webview`) tracks its **main themed app root** in a module-level `_app_root`, registered when a Root is created whose program is **not a dummy** (`dummy.App` now carries `self.dummy=True`, set 2026-06-08) **and** `noimagescaling=False` (i.e. not the image-scaling fakeroot). That's the root that runs `mainloop`. Inference from the `program` argument was rejected as unsound — `program is not None` can't tell `ui.Root(program=dummy.App())` from the real app — so the dummy now marks itself explicitly. Context menus use `parent._root()` and tooltips use `Toplevel`, so neither creates a competing root. `error_notice` does `parent = ui.default_root() or ui.Root()` — no tkinter import, and guaranteed to get the photo-bearing root when one exists.

## Project-open hang — `writefilename` stranded behind soundfile guard (fixed 2026-06-08, v1.2.6)

Selecting a LIFT project hung silently ("then nothing" after `setfilenameandcontinue` logs). Root cause: an external refactor moved `writefilename` (a **non-audio** app-settings helper) into the new `utilities/file_sound.py`, which `import soundfile` at module top. `utilities/file.py` only re-exports it via `if soundfileOK: from .file_sound import *` (file.py:418-419). So when `soundfile` isn't installed, `file.writefilename` doesn't exist → `setfilenameandcontinue` (ui_shell.py:2834) raises `AttributeError` inside the Tk button callback → Tk swallows it → `LiftChooser.wait_window` never returns → hang. (Worse: `file_sound.writefilename` referenced `_app_settings`, which it never imports, so it was also broken *with* sound on — a `NameError` on call.) **Fix:** defined `writefilename` in `utilities/file.py` next to the other `_app_settings()` helpers (always available), and removed the broken copy from `file_sound.py` so `import *` can't clobber it. Regression guard added: `tests/test_utilities.py::test_writefilename_available_without_soundfile` (the import-smoke can't catch a conditionally-*defined* function). **Watch-for:** other non-audio helpers must not be parked behind the `soundfile` guard.

## Current status & recommended next actions (2026-06-06)

**Where things stand**

- **Top-15 highest-priority findings:** 14 fixed, 1 downgraded (#13), 0 open. Verified by direct read on 2026-06-06.
- **Stuck-progress-dialog (`wait()`/`waitdone()`):** fixed in source (the `waiting()` context manager + all 16 conversions are present and intact), but **not yet verified by execution** — no `py_compile`, no smoke run. This is the one open risk on the v1.2.0 work.
- **Broader hygiene findings** (bare `except:`, production `exit()`, the `settings/manager.py` shadow + write-amplification, protocol drift): **untouched**, confirmed still present per-file below.
- **Test suite:** started 2026-06-06 (`tests/`, pytest). Guardrails (import-smoke + `waiting()` contract) + units (settings.manager, utilities) + backend/core API guards; behavioral backend tests stubbed. See `tests/README.md`. **First run: 118 passed, 3 skipped (intended stubs), 0 real failures** — every v1.2.0 test (incl. the `waiting()` contract) passed, so the dialog work imports clean and the contract holds.
- **Orphan modules surfaced by the import-smoke test (new finding, 2026-06-06):** four modules don't import as package modules and are imported nowhere in the app — `harmony_sync.py` (needs absent `harmony_client`; WIP), `praatfns.py` + `setdefaults.py` (Python-2-style bare `import logsetup`), `utilities/openclipart.py` (bare `import urls`). They're skipped-with-reason in `tests/test_import_smoke.py` (`EXPECTED_NOT_IMPORTABLE`). Decide per module: delete if dead, fix the bare imports (`from utilities import logsetup`/`urls`) if they should live, or leave as standalone. If wired into the app as-is they'd `ModuleNotFoundError` at import.

**Recommended next actions, in order**

1. **Run the new test suite** *(blocking — do first)*. `cd azt && source env/bin/activate && pip install -r requirements-dev.txt && pytest`. The import-smoke test stands in for the `py_compile` pass over the v1.2.0 edits, and the `waiting()` contract test guards the dialog fix. Then a manual smoke of the two restructured flows (new-LIFT-file setup = analang, demo-language setup) plus one report and one sort. Fix any red before further work.
2. ~~**Process-death `exit()` calls**~~ ✅ **Done 2026-06-06 (v1.2.1).** Converted all six production `exit()` calls to typed exceptions (existing diagnostic logs kept): `io_put/lift.py` → `RuntimeError`×2 + `ValueError` (ambiguous target head); `io_put/xlp.py` → `AttributeError` (missing `program.name`); `utilities/utilities.py` `setnesteddictval` → `TypeError`; `sound_ui.py` → `AttributeError` (missing task attr) + `FileNotFoundError` (missing ASR cache dir). Uncaught, these now propagate to `sys.excepthook`→`handle_exception` (logged traceback) instead of silent process death. Left untouched: `lift.py`'s `__main__`-guarded `exit()` and `utilities.py`'s intentional `sysshutdown`/`sysrestart` `sys.exit()`. Also fixed the `utilities/logsetup.py` `datetime.utcnow()` deprecation (naive-UTC, filename format unchanged). *Possible follow-up:* a dedicated `LiftError`/domain exception type if callers want to catch these specifically.
3. ~~**`settings/manager.py` write-amplification**~~ ✅ **Done 2026-06-08 (v1.2.2).** Two-part fix: (a) **always-on coalescing** — `_write()` skips the write when the file already holds identical content (compared against disk, so correct even with another writer), which collapses the redundant rewrites in the store→load→re-store verify flow; (b) **opt-in `batch()` context manager** on `ConfigManager` (defer + dirty flag, nestable) and on `SettingsManager` (batches all domains via `ExitStack`), collapsing a run of `set()`/attribute writes into one write. Default behavior is unchanged (immediate write outside a batch). Deliberately **not** auto-wrapped around the init sequence: it interleaves write-then-read-back verification (`storesettingsfile`→`loadsettingsfile`, L284-285), and deferring those writes would break the read-back — `batch()` is documented as "don't read the file back inside the block." Tests added in `tests/test_settings_manager.py` (coalescing, defer, nesting, all-domains propagation).
4. ~~**Bare `except:` sweep**~~ ✅ **Done 2026-06-08 (v1.2.3)** for the io_put + utilities + backend/core scope (24 sites). Narrowed where the failure mode was unambiguous, else widened to `except Exception:` (stops swallowing `KeyboardInterrupt`/`SystemExit`): `io_put/lift.py` ×7 (read→`Exception`, candidate-probe loops→`Exception`, `os.replace`→`OSError`, `find().text`→`AttributeError`, two `r+=[i]` init-guards→`NameError`); `io_put/sound.py` ×3→`Exception`; `io_put/xlp.py` ×3 (import→`ImportError`, XSLT→`Exception`); `utilities/file.py` ×2 (attr→`AttributeError`, import→`ImportError`); `utilities/utilities.py` ×2→`AttributeError`; `utilities/rx.py`→`AttributeError`; `utilities/xmletfns.py` read→`Exception`; `backend/core/analysis.py` ×2→`KeyError`; `backend/core/alphabet.py`→`Exception`; `backend/core/vcs.py`→`Exception`; `utilities/executables.py` subprocess-decode→`Exception`. **Left:** `executables.py:51` (a `__main__`-block translation shim). **Out of this sweep's scope (still bare):** a larger second cluster in frontend/tasks/other-backend — `frontend/{ui_shell,ui_tkinter,sound_ui,sort_buttons,alphabet_chart,alphabet_comparison,transcriber}.py`, `tasks/{tasks,transcribe_glyph}.py`, `backend/{core/lexicon,asr,langtags}.py`, `io_put/pdf_fonts.py`, `utilities/file_sound.py`, `main.py` — these were not in #4's enumerated list; do as a follow-up sweep.
5. **Cosmetic / low-priority cleanup**: `settings/manager.py:7` `_=gettext.gettext` shadow → `from utilities.i18n import _`; `sound_ui.py:99` `self.id=id` (dead); `backend/core/sound.py:68` stray `%s`; `tasks/ui_protocol.py` declare the `wait`/`waitdone` family (protocol drift); remove obsolete `guidtriage`/`guidtriagebyps` in `tasks/chooser.py`.

Suggested grouping: #1 now; #2+#3 as one small PR; #4 as its own sweep; #5 opportunistically.

## Re-verification (2026-06-05)

Re-checked the 15 highest-priority findings against current source, **re-verified on 2026-06-05/06** (direct reads of the live files). **14 of 15 are now fixed**; 0 outstanding; 0 partial; 1 downgraded (#13). Per-item status is in the "Highest-priority issues" table below (**Status** column). Original per-file line numbers predate the fixes and have drifted — trust the table.

> ⚠️ The working tree was being edited **concurrently** during this review, so earlier drafts of this file mislabeled several items. Two corrections worth recording: (1) **#7** and **#12** were fixed externally mid-review (first-pass reads were stale). (2) An intermediate subagent pass over-reported **#9** and **#15** as still-broken — direct re-reads on 2026-06-06 showed both are fixed (#9 has only a cosmetic stray `%s`; #15 uses the recommended `… or ui.Root()` short-circuit, which is *not* eager). Lesson noted: confirm by direct read before asserting status.

Fixed since the audit (verified 2026-06-05):
- #1 `tasks/sound.py:2` — now `from frontend import sound_ui, ui`.
- #2 `ui_tkinter.py` — `except tkinter.TclError` (no longer the unimported `_tkinter`).
- #3 `ui_tkinter.py` — `ScrollingListBox.__init__` has the missing comma.
- #4 `lexicon.py` imageparameters block — all four calls now use `p.label`/`p.button`.
- #5 `ui_shell.py` `getcheck` — no-checks branch now references in-scope `kwargs`, not undefined `cvt/ps/profile`.
- #6 `ui_shell.py` `multicheckscopelabel` — now returns the formatted string.
- #7 `ui_shell.py` `ImageFrame` L2222 — now `bgl=ui.Label(self,...)`; the undefined `verb` is gone.
- #8 `error_notice.py` — `self.title = title` removed (commented out); uses `self.text` instead.
- #9 `backend/core/sound.py` — `BaseException`+unreachable-`except` pair gone (now `except Exception … return 1`); `default_in()` now `raise AttributeError("audio_card_in")`. Only a cosmetic stray `%s` literal remains at L68 (no crash); no format arg-count mismatch exists.
- #10 `ui_tkinter.py` — `randint(0, len(pot)-1)` (off-by-one corrected).
- #11 `ui_tkinter.py` `Renderer.render` — `if 'cannot open resource' in str(e)` with `else: raise`.
- #12 `ui_shell.py:1456` — now `if n == optionlist_maxi` (was `is`).
- #14 `tasks/tasks.py` `ExportData.__init__(self, program)` — sets `self.program`, uses `tk_root`.
- #15 `vcs_ui.py:52` + `error_notice.py` — both fixed; `vcs_ui.py` now uses `getattr(…, None) or ui.Root()` (short-circuit, lazy — the recommended fix).

Downgraded:
- #13 — see the "Downgraded" note below; its residual `waitdone()` gap was fixed in v1.2.0.

Other findings — verified status (these were NOT part of the v1.2.0 work):
- **Fixed:** settings/__init__.py `exit()` calls are now `raise AttributeError`/`raise FileNotFoundError` (L298/L554) and the `makesettingsdict` bare `except:` is now typed `except (AttributeError, KeyError):` (L404). The orphaned `import gettext as _gettext` was deleted 2026-06-05. main.py `handle_exception` **is** wired (`sys.excepthook = self.handle_exception`, ~L625).
- **Fixed 2026-06-06 (v1.2.1):** all production `exit()` in io_put/lift.py (×3), io_put/xlp.py, utilities/utilities.py `setnesteddictval`, and sound_ui.py (×2) → typed exceptions (see next-action #2 above).
- **Fixed 2026-06-08 (v1.2.2):** settings/manager.py write-amplification — coalescing + `batch()` (see next-action #3 above). The save-on-every-`__setattr__` still happens *outside* a batch (by design, immediate-write default), but redundant identical writes are now skipped and bulk paths can opt into `batch()`.
- **Fixed 2026-06-08 (v1.2.3):** bare-`except:` sweep across io_put + utilities + backend/core (24 sites) — see next-action #4 above.
- **`datetime.utcnow()` deprecation — completed 2026-06-08 (v1.2.4).** v1.2.1 only changed `logsetup.py:71`; the remaining *production* sites are now fixed too: `utilities/logsetup.py:106` and `utilities/xmletfns.py:93` (naive-UTC replacement, formats unchanged). The other occurrences do **not** fire in production and were left as-is: `utilities/times.py:5-11`'s `now()` already uses `datetime.datetime.now(datetime.UTC)` on 3.11+ (the `utcnow()` is a `<=3.11` fallback, dead on 3.13); `backend/parser.py:685/689` is dev-scratch (its `now()` depends on a `start` global defined only under `__main__`). Commented occurrences in lift.py:4307 and ui_tkinter.py are inert. (Earlier drafts of this note wrongly listed `times.py:11` as the live central helper to fix — it isn't.)
- **Fixed 2026-06-08 (v1.2.5):** bare-`except:` **second cluster** swept — frontend/{ui_shell ×7, ui_tkinter ×8, sound_ui ×3, sort_buttons ×1, alphabet_chart ×4+2-shims, alphabet_comparison ×4, transcribe_glyph ×1}, tasks/tasks.py ×6, backend/{core/lexicon ×2, asr ×1, langtags ×4}, io_put/pdf_fonts.py ×1, utilities/file_sound.py ×1, main.py ×7. Narrowed where the failure mode was clear (tkinter ops→`tkinter.TclError`, `os.makedirs`→`OSError`, dict→`KeyError`, attr→`AttributeError`, `int()`→`(ValueError,TypeError)`, `lineage[0]`→`IndexError`), else `except Exception:`. main.py's top-level last-resort handler (after `except Exception as e`) → `except BaseException:` (explicit; it intentionally logs everything). **Left bare (intentional):** `try: _ / except:` i18n shims inside `__main__` blocks (executables:51, sound_ui:809, transcriber:181, alphabet_chart:597), and the orphan modules harmony_sync.py / praatfns.py (future-work / obsolete per owner).
- **Still present (verified):** settings/manager.py module-level `_=gettext.gettext` shadow (L7); tasks/ui_protocol.py still omits the `wait`/`waitdone` family; tasks/chooser.py obsolete `guidtriage`/`guidtriagebyps` (NameError if re-enabled) + redundant `except (AttributeError, Exception)` (L430); tasks/base.py `makeeverythingok` swallow (L107); ui_interface.py `updatebindings` vs ContextMenu `_bind_to_makemenus`; frontend/__init__.py docstring vs env-only `_get_backend`; frontend/transcriber.py twin `' '`/U+00A0 checks (L124/L129); sound_ui.py `self.id=id` (L99).
- **Fixed 2026-06-08 (verified by read):** `lexicon.py submitparse` — the broken `kwargs['entry'].sense.id` recovery is gone; the `except` now logs and `raise e`. `lexicon.py showwhenready` — the unbounded 1ms self-reschedule now caps at `self.try_times` (100) × `self.try_each_ms` (100ms) with a give-up + error log; bounds defined at L1679-1680.
- **Note:** main.py `program['exceptiononload']` is read but its main gate is dead-disabled (`if False and self.exceptiononload:`).

Downgraded (re-assessed as not a bug):
- #13 `ui_shell.py` `analang_code_complete` — the `None` return is the intended "no file, pick again" contract and the try/except is deliberate debug instrumentation (see LiftChooser section). Its residual `waitdone()` gap was **fixed 2026-06-05 (v1.2.0)** as part of the wait()/waitdone() pairing work — `_analang_code_complete` now uses `with self.waiting(...)`, so the dialog closes even on an unexpected exception.

---

## Stuck-progress-dialog audit — `wait()` / `waitdone()` pairing (2026-06-05)

**Serious UX problem, systemic.** A `wait()` opens a modal progress dialog ("Setting up…", "Reloading ASR model(s)", "Filling images…", etc.); `waitdone()` closes it. **No call site in the codebase wraps the intervening work in `try/finally`.** So whenever an exception — or, in several sites, an early `return` — lands between `wait()` and `waitdone()`, the dialog is left open and the app appears hung. Every opener below is exposed; severity tracks how likely the intervening code is to fail (network downloads, file writes, XML/analysis work = high).

**Recommended fix (do this first):** add a context-manager form to the wait mechanism so the pairing can't be broken by an early exit. In `ui_tkinter.py` (and mirror in `ui_webview.py` + `ui_interface.py`):

```python
from contextlib import contextmanager
@contextmanager
def waiting(self, msg=None, **kwargs):
    self.wait(msg=msg, **kwargs)
    try:
        yield self
    finally:
        self.waitdone()
```

Then convert call sites to `with self.ui.waiting(msg): ...` incrementally (highest-risk first). Where a site legitimately keeps the dialog open across an async continuation (`drive_work`/`on_done`), leave it — those are not leaks, just note them.

### Inventory of `wait()` openers and their exposure

| Site | Risk | Why |
|---|---|---|
| `ui_shell.py:2750` (demolang setup) | **High — confirmed gap** | Two early `return`s (L2762 file-exists, L2765 no-filename) after `wait()`, neither calls `waitdone()`. The success path (L2771 `return str(demo.filename)`) also returns with **no** `waitdone()`. Multiple miss paths — worst offender. |
| `sound_ui.py:731` (reload ASR models) | **High** | `load_ASR()` (L739) sits between `wait`/`waitdone` (L740) with no guard; the dialog itself warns "may require a large download" — a failed/raising download leaves it stuck. |
| `backend/reporting/generator.py:955` (Multislice report) | **High** | `waitdone()` only on the early-return (L966) and success (L1034) paths; the long body (xlpstart, `iteratecvt`, file writes) can raise in between. Compounded: L971 does `sys.stdout = open(...)`, restored only at L1032 — an exception both leaves the dialog open *and* leaves stdout redirected to the report file. |
| `ui_shell.py:2613` (`_analang_code_complete`, #13) | Medium | `except` wrapper in `analang_code_complete` returns `None` without `waitdone()`; intentional return value, but the dialog opened at L2613 stays if work after it raises. |
| `backend/core/lexicon.py:858` (OpenClipart download) | Medium — partial | Expected `urls.MaxRetryError` is handled with `waitdone()`+return (L876-881); any *other* exception (e.g. `file.makedir`, disk write, scraper) between there and the final `waitdone()` (L923) skips it. |
| `backend/core/sorting_engine.py:1012` (`join_pair`) | Medium | macrosort branch: `join_glyphs()` raising skips `waitdone()` (L1031). Non-macrosort branch `return`s at L1029 into an async `drive_work`/`on_done` continuation — that path is by-design, not a leak. |
| `frontend/ui_tkinter.py:188` (`setimages` scaling) | Medium | `waitdone()` (L250) is in a try/except, but an unexpected image exception re-raised at L227 propagates past it, leaving the "Scaling Images" dialog open. |
| `backend/reporting/generator.py:104`, `:471` | Medium | Same unguarded `wait → work → waitdone` shape. |
| `tasks/tasks.py:1652` (`redo` tone analysis) | Medium | `analysis.do()` (L1653) can raise before `waitdone()` (L1654). |
| `tasks/sound.py:102` (record pages loop) | Medium | Exception in `makelabelsnrecordingbuttons`/widget build skips `waitdone()` (L122). |
| `frontend/sort_buttons.py:169` | Medium | `prefetch_examples` / `addgroupbutton` can raise before `waitdone()` (L179). |
| `frontend/alphabet_chart.py:499` | Medium | Image `scale()` can raise before `waitdone()` (L507). |
| `backend/core/lexicon.py:1603` (load affixes) | Low–Med | Unguarded loop before `waitdone()` (L1609). |
| `backend/core/sorting_engine.py:144` | Low–Med | Unguarded `wait → work → waitdone` (L204). |
| `frontend/ui_shell.py:2079` (`killall`) | Low | Shutdown path; `maybewrite()`/`trackuntrackedfiles()` could raise before `waitdone()` (L2088), but app is closing anyway. |
| `frontend/ui_shell.py:217` (`fill_db_images`) | N/A — by design | `wait()` + `drive_work(...)` async; dialog closed by the `do_wait` mechanism, not inline. |
| `frontend/ui_shell.py:2041` (`show_run_window`) | N/A — by design | `wait(thenshow=True)` is deliberately left open; closed later by the run-window lifecycle. |

**Status:** ✅ **Fixed 2026-06-05** (app v1.2.0). Implemented the `waiting()` context manager on both backends (`ui_tkinter.Waitable`, `ui_webview`) and declared it on `ui_interface.WaitableInterface`. Converted every exposed opener so `waitdone()` is now guaranteed:

- **`with …waiting(…):`** (lexically-paired open/close): analang (`_analang_code_complete`), demolang setup, `sound_ui` get-transcriptions, `sort_buttons`, `tasks.py` redo, `tasks/sound.py` record loop, `lexicon.py:1603` affixes, `generator.py:104`, `killall`. The two modal-error sites (analang, demolang) were restructured to capture the outcome inside the block and show the `ErrorNotice(wait=True)` *after* the dialog closes.
- **`try/finally`** (conditional-open or async-aware, where a `with` didn't fit): `sound_ui` reload-ASR, `lexicon.py:858` OpenClipart, `sorting_engine.py:144` Ad Hoc build, `sorting_engine.py:1012` join_pair (sync branch only — async `drive_work` branch left intact), `generator.py:471`, `generator.py:955` Multislice (nested `try/finally` also restores `sys.stdout`), `ui_tkinter.setimages` scaling loop.
- **Untouched by design:** `ui_shell.py:217` `fill_db_images` and `ui_shell.py:2041` `show_run_window` (async/intentionally-held dialogs).

**Re-verified present in source 2026-06-06** (direct grep/read): all conversions are intact — `def waiting` in all three backends (`ui_tkinter.py:1022`, `ui_webview.py:1786`, `ui_interface.py:341`), 9 `with …waiting():` sites, and the `try/finally`+`waitdone()` sites (`ui_tkinter:251`, `alphabet_chart:508`, `sound_ui:743`, `generator:491`/`1034`/`1037`, `sorting_engine:204`/`1035`, `lexicon:925`). Nothing was reverted by the concurrent external edits.

Not yet run: `py_compile` over the touched files, and a live smoke test through the app (no test suite). Code-level fixed; runtime-unverified.

---

## frontend/ui_tkinter.py

### Theme (L51-519)

- **`_` shadowed (L3-4)**: `import gettext; _=gettext.gettext` re-binds the translator at module level. CLAUDE.md says all modules must `from utilities.i18n import _` so the live translator can be swapped at startup. Strings translated in this module won't follow user-language switches.
- **L266 `randint(0, len(pot))-1`**: Off-by-one. `randint` is inclusive on both ends, so this can return `-1`. `pot[-1]` happens to be valid (last element), so it skews the distribution toward the last theme but isn't crash-causing — still a real bug. Should be `randint(0, len(pot)-1)`.
- **L268-272 hostname theme override**: Hard-codes `CS-477`/`karlap` for theme picking. Doesn't belong in the Theme class — move to dev/local config.
- **L184-190 setimages side effect**: Inside what looks like image preparation, a hidden `Root` window is created to host a progress UI. Pure compilation routine pulls in UI. Acceptable but undocumented; mention in docstring at minimum.
- **L223-228 silent image failures**: `tkinter.TclError` with "not enough free memory" → `continue` to next resolution; outer `Exception` at L227 logs and re-raises but is then caught at L239 by an outer `except Exception as e` that just logs. Net effect: a non-loadable image vanishes silently and `self.photo[name]` will `KeyError` later.
- **L249-257 `try: … except: pass`**: Swallows all exceptions during `unbootstraptheme` / `fakeroot.destroy`. Hide-then-fail pattern.
- **`startruntime`/`nowruntime`/`logfinished` (L140-159)**: Timing helpers on Theme that have nothing to do with theming. Move to a util.
- **L498-505**: When `program.theme` is already a `Theme`, the constructor logs "Found a Theme theme attribute" as an error and silently `return`s — but `__init__` returns None. The caller's `Theme(...)` call still produces a half-initialized object (no `name`, no `image_cache`, etc.). Caller has no way to detect this. Either raise, or initialize cleanly.

### Renderer (L532-665)

- **L629 `if e == 'cannot open resource'`**: Comparing an `OSError` instance to a string — always False. Should be `if 'cannot open resource' in str(e)`. Effect: the swallow-and-continue logic for missing font files never matches and falls through to the `break` path implicitly (after the `try` raises, we leave the for loop because of the wrong path… actually no — `OSError` is *only* caught here, so the `else: log.debug` never logs. Also if it's any other OSError, nothing happens).
  - Inspect: it's `except OSError as e:` → `if e == ...` → empty body if false. So all `OSError`s are silently swallowed and we move to the next file. The only consequence is the missing debug log; not a functional bug, but the comparison is dead.
- **L621 `return` from `render`**: When font-family is unknown, returns mid-method without setting `self.img`. Caller does `self.tkimg=self.renderer.img` (L1499); if `img` was set on a prior call, the stale value would be used. The constructor sets `self.renderings={}` only — `self.img` is never initialized. First-time error here would attribute-error on the caller path.
  - Actually L548 `self.img=None` clears it at start of each render call. OK.
- **L633 `if str(fontkey) not in self.imagefonts`**: Re-checks after the for-loop. Order issue: if all `truetype()` calls raised non-OSError, we'd never have populated `imagefonts[fontkey]`, and we'd reach this branch — fine. But if we raised on something like `PIL.UnidentifiedImageError`, that's not caught.
- **L549 `fontkey=font=kwargs['font'].actual()`**: Single chained assignment immediately followed by L552 `fname=font['family']`. Then `font` gets overwritten to a `PIL.ImageFont` at L624. Reusing `font` for both is confusing.

### Childof / Gridded / UI mixins (L666-981)

- **L668-671 `pre_tk_init` swallows everything**: `try: super().pre_tk_init(); finally: return kwargs`. The bare `return` in `finally` discards any exception. Use `try/except` with explicit handling, not finally-swallowing.
- **L676-677 post_tk_init exception**: Catches `Exception` but only logs for non-Menu classes. Means real errors during widget post-init pass silently for menus.
- **L701-707 `is_descendant_of`**:
  ```python
  while (y:=self.parent) not in [w,self.winfo_toplevel()]:
      return y.is_descendant_of(w)
  if w == y:
      return True
  ```
  This uses `while` but `return`s on the first iteration — it's just an `if`. And `y` is only bound inside the `while` condition, so if the while body doesn't run, the `if w == y` line uses an undefined name (NameError). Logic is broken; rewrite as plain recursion.
- **L962-963 `if self.withdrawn: self.withdraw()`** in `UI.post_tk_init`. Then `__init__` (L979-980) also withdraws. Double-withdraw on Root. Harmless but redundant.
- **L1011-1019 on_quit**: `if (to_root or getattr(self,'ismainwindow',False)) and self.parent: self.parent.on_quit(to_root=True)` — after parent.on_quit (which destroys parent), execution returns here and `self.destroy()` is called. If parent.destroy() already destroyed self, this raises a `TclError` that isn't caught.
- **L1080 `except (tkinter.TclError,AttributeError) as e: pass`** with `e` bound but unused. Minor.
- **L1086 `if self.showafterwait and not self is self.theme.program.tk_root:`**: `not self is X` parses as `(not self) is X` due to precedence — but `not self` for tkinter widgets uses the bool dunder which Tk widgets typically don't override, so this *might* coincidentally work. Replace with `self is not self.theme.program.tk_root` to be unambiguous.

### Image (L1095-1228)

- **L1208-1218**: When PIL load fails, sets `self.base_img=None` and returns. Then `self.compile()` is called from `__init__` only if `__init__` proceeds — but `__init__` early-returns at L1218. So no compile() call: good. But callers calling other methods later will hit AttributeError on `scaled` etc. Document the failed-init contract.
- **`transparent` (L1174-1199)**: Returns immediately with no work — entire method is dead. If you need it removed, kill it; otherwise mark TODO. (User said skip commented-out code, but this is a live `return` followed by dead code; flagging the live `return` as a stub.)

### Root / Toplevel / Menu / Window (L1230-2012)

- **L1232-1235 Root.on_quit**: Calls `super().on_quit()` then `logsetup.shutdown(); sys.exit()`. `sys.exit()` raises SystemExit which leaks past Tk's mainloop — fine, but worth noting that `self.destroy()` already happens in super, so `sys.exit()` is the kill signal.
- **L1248**: When the assertions fail, falls through to `Theme(self.program, **{**kwargs,'noimagescaling':self.noimagescaling})`. But `kwargs` may already contain `noimagescaling`, which is fine because the `**{**kwargs,...}` syntax overrides. OK.
- **L1660 `except _tkinter.TclError`**: `_tkinter` is not imported in this file (only `tkinter`). This is a NameError waiting to fire. Should be `except tkinter.TclError` (or import `_tkinter`).
- **L1767-1770 ListBox post_tk_init**:
  ```python
  try:
      assert not hasattr(self['listvariable'].get(), '__iter__')
      self['listvariable'].set(self._display)
  except:
      self['listvariable']=tkinter.Variable(value=self._display)
  ```
  The bare `except:` catches everything including KeyboardInterrupt/SystemExit. Also: `self['listvariable']` for a tkinter widget returns the option *value as a string* (the Tcl variable name), not a Variable instance — calling `.get()` on a string would raise `AttributeError`, fall through to assigning a new Variable. Reads as control-flow-by-exception. Cleaner to check explicitly.
- **L1856 `raise NotImplementedError`** in `SearchableComboBox.__init__`: marked as not functional. Class still defines methods that reference undefined `self.options`, `self.listbox`, `self.entry`, `self.dropdown_id` — instantiable subclasses will break. Either remove the class entirely or stub it as `class SearchableComboBox: pass # TODO`.
- **L2008 `cmd=lambda:backcmd(parent, window, check, entry, choice)` in Window.__init__**: `window`, `check`, `entry` are not defined in this scope. `choice` is a parameter. This lambda will NameError if invoked. Confirm whether `backcmd` is ever exercised.
- **L2019 unpost via `if self.menu.winfo_exists()`**: doesn't guard against `self.menu` not yet existing. `self.menu` is created in `menuinit`; the popup boolean may be True before menu attr exists if state corrupts. Marginal.
- **L1934-1940 Window.post_tk_init**: configures grid weights for rows 0,2 then iconphotos. The except-and-log on iconphoto failure is fine.

### ButtonFrame / ScrollingFrame / others (L2062-2490)

- **L2125 f-string with single quotes inside**: `f' ({str(choice['description'])})'` — Python 3.12+ allows reused single quotes in f-string, but if running on older 3.x it's a SyntaxError. Project uses 3.13 (per CLAUDE.md), so OK; flag for portability if that ever changes.
- **L2160-2168 ButtonFrame loop**: `if not choice: continue` after `choice_kwargs=self.regularize_choice(choice)` — but `regularize_choice` may have just returned `None` (set into `choice_kwargs`), while `choice` is still the original truthy iterable. Should test `choice_kwargs`, not `choice`. Effectively, malformed entries currently still proceed to `self.buttons[choice_kwargs['choice']]` and crash with TypeError.
- **L2154 `log.info("list is empty!",type(self.optionlist))`**: log call passes a second positional arg expecting log-formatting; `log.info` doesn't accept a second arg as data unless it's % formatting. As written, the second arg is treated as args to a non-existent format string in the message, raising a logging error or being dropped silently. Should be a single formatted message.
- **L2138 / L2147 / L2155 fallthroughs**: `regularize_choice`, optionlist-not-iterable, optionlist-empty all `return` from `__init__`, leaving the frame partially constructed. Caller can't tell.
- **L2362 `super().__init__(parent, *args, **kwargs)`** in ScrollingFrame, then `self.post_tk_init()` is called manually (L2363) — but Frame.__init__ already calls post_tk_init for non-Frame subclasses (L1571-1572). ScrollingFrame is a non-Frame subclass, so post_tk_init runs there too. Result: `post_tk_init` may run twice for ScrollingFrame. Confirm.
- **L2378 `self.canvas['background']=parent['background']`** — uses raw tk option access, bypassing the theme inheritance pattern used elsewhere.
- **L2440-2442 ScrollingListBox is broken**:
  ```python
  self.listbox=ListBox(self,
                      row=0,column=0,sticky='nsew'
                      **kwargs)
  ```
  Missing comma. Parses as `sticky='nsew' ** kwargs` — `str ** dict` — a runtime TypeError every time `ScrollingListBox(...)` is called. (Not a SyntaxError; module imports fine.) Add the missing comma.

### ToolTip (L2491-2561)

- **L2535 `self.widget.unbind("<Leave>")`**: rebinds `<Leave>` later at L2555. Each `showtip` call leaks one tk binding tag if `<Leave>` was previously bound by other code on the widget — `unbind` without the `funcid` argument deletes *all* bindings. Pattern can clobber unrelated bindings on the same widget.
- **L2537 `x, y, cx, cy = self.widget.bbox("insert")`**: most non-text widgets (Button, Label, Frame) raise TclError or return None for `bbox("insert")`. Tooltips on these widgets will crash.
- **L2542 uses `self.event.x_root`**: only set in `enter()`. If `showtip` is ever invoked from outside the enter→schedule path, `self.event` may be missing.

### Wait (L2563-2615)

- **L2585 `self['background']=parent['background']`**: bypasses theme inheritance like ScrollingFrame does. Both are pre-existing; consistent at least.
- **L2614 `try/except Exception`**: swallows any error in `deiconify()`/`update_idletasks()`. Acceptable for cosmetics but hides real problems.

### Module tail (L2618+)
- `testapp2`, `testapp3`, `testapp4`, `testappY`, `testapp` — five debug/test functions left in the production module. Move to a separate `test.py` or strip before release.

### ui_tkinter.py — top hits
1. `_tkinter.TclError` at L1660 referencing an unimported name — NameError will mask any TclError raised on Button enter/leave bindings.
2. `ScrollingListBox.__init__` will TypeError on every call (missing comma at L2441).
3. ButtonFrame's `if not choice: continue` at L2162 tests the wrong variable — malformed entries crash later.
4. `is_descendant_of` (L701-707) — `while` is an `if` with a return; code smell. Not a logic bug per re-read (walrus binds `y` before the `not in` check).
5. Module-level `_=gettext.gettext` defeats the i18n architecture documented in CLAUDE.md.
6. `randint(0, len(pot))-1` skews to last theme.
7. `Renderer.render` `if e == 'cannot open resource'` (L629) — comparing OSError instance to str; never matches.

---

---

## frontend/__init__.py

- Docstring says "selected via the `AZT_UI_BACKEND` env var or configuration." But `_get_backend()` *only* checks `os.environ`. There's no consult of any settings/config file. CLAUDE.md repeats the same claim. Either wire it up or correct the docs.

## frontend/ui_interface.py

- File header says "Not enforced at runtime — serves as documentation and a reference for implementors." Nothing in the codebase imports `WidgetInterface` etc. for type-checking, so the contract drifts silently. Add at least one runtime smoke test that asserts both backends expose the documented public names.
- **`ContextMenuInterface.updatebindings`** (L321) — abstract method, but `ui_tkinter.ContextMenu` does not implement `updatebindings` (it has `_bind_to_makemenus`). Either rename in interface or implement in the concrete class.
- **`nfc`/`nfd`** are defined here AND at the bottom of `ui_tkinter.py` (and presumably in `ui_webview`). Three copies. Move to `utilities/encodings.py` (which already exists per CLAUDE.md) and re-export.
- `RootInterface.iconphoto(default, *args)` — docstring missing in body but signature uses an unusual `default` first arg. Check whether webview backend honors this signature.
- `ButtonInterface` body is `pass` — kwarg list is in the docstring only. Without abstract methods, `ABC` does nothing. Same for `MessageInterface`, `RadioButtonInterface`, etc. The interface is closer to docs than ABC.

---

## frontend/ui_shell.py (~3500 lines)

### Imports & top-level
- **L11 `from utilities.utilities import *`**: star-import; lots of unknowns flow into the module. Used names: `nn`, `donothing`, `sysrestart`, `setnesteddictobjectval`, `unlist`, `openweburl`, `grouptype`. Worth replacing with explicit imports.
- **L19 `from utilities.error_handler import notify_error as ErrorNotice`**: aliased to the old class name — works but `ErrorNotice` isn't strictly a class anymore. Tracking the rename in CLAUDE.md.

### `Menus` class (L195-492)
- **L209-215 `change(self)`**: builds a "Change" cascade only if `is_sort_task`. The code for `parameterslice` is invoked inside `change` but doesn't add to "Change" cascade for non-sort tasks. Not a bug but the structure is hard to trace.
- **L322-325 `redoadvanced`**: `self.delete(_("Advanced"))` — but the menu was added with `_("Advanced")` translated; if the locale changed since, the lookup will miss. Should track menu indices, not labels.
- **L461 `from main import updateazt`** inside `help()`: circular import workaround. Better: pass updateazt in via constructor.
- **L491-492**: `if self.program.me: self.command(self,self.program.filename,None)` — passes `None` as `cmd`; tk will balk with `command=None` on add_command (it accepts None and silently treats as no-op, so OK).

### `StatusFrame` (L494-1391)
- 900-line class, ~40 small methods, each touching `self.program.X.Y.Z`. Strong god-object coupling. The "label/update label/get label-text" triplet for every status field is duplicated 15 times — abstract into a `StatusLine` helper.
- **L869-870 `multicheckscopelabel`**: assigns to `t` and never returns it. Method returns `None`. Caller does `self.labels['cvgroup']['text'].set(self.multicheckscopelabel())` (L868) — sets text to `None`. Bug.
- **L1149 `if skipped:=set(allprofiles)-set(profiles):`**: walrus with `set()-set()` — fine, but the message logs a "skipped insanely long profiles" error for any profile longer than 20 chars. Real linguistic data may have long profiles; this filters them out silently from the table. Document the cutoff or make configurable.
- **L1303 `self.activate_cell(self._cells[(curprofile,curcheck)])`**: KeyError if the current profile/check isn't a cell (e.g., partial state). No `try/except` or `.get(...)`.

### `TaskDressing` (L1393-2166)
- **L1456 `if n is optionlist_maxi`**: uses `is` for integer equality. Works for small CPython-cached ints (-5..256), but unreliable. Use `==`.
- **L1795 NameError**: in `getcheck`'s "no checks" branch, the error message uses `cvt`, `ps`, `profile` — none of these are defined in this method's scope. Reachable when `cvt != 'T'` and `not checks`.
- **L1655-1660 `i_am_mainwindow`**: uses `try: assert self is not self.program.mainwindow; …; except Exception: pass`. AssertionError flows into pass; the rest of the body is also caught. Replace with explicit `if self.program.mainwindow is not None and self.program.mainwindow is not self:`.

### `ImageFrame` (L2169-2260)
- **L2189 `except (AttributeError, Exception) as e`**: `Exception` already covers `AttributeError`. The tuple is redundant — but worse, the guard `if e.args and ('value for "-file" missing' not in e.args[0] and "couldn't recognize data in image file" not in e.args[0]):` will TypeError if `e.args[0]` is not a string. Use `str(e)` instead.
- **L2222 `bgl=ui.Label(verb,...)`**: `verb` is not defined in this scope. The `except:` at L2226 swallows it, so this code is dead — but if a future change reorders, NameError will leak. Either delete the dead path or define `verb`.

### `LiftChooser` (L2339-2868)
- **L2179 `raise` (bare)**: `if not self.url and not self.show_none: raise` — bare raise outside an except block raises `RuntimeError("No active exception to re-raise")`. This is in `ImageFrame.getimage`, not LiftChooser. Either raise a specific exception or use `notify_error`.
- **L2604-2605 `analang_code_complete`** *(re-assessed 2026-06-05 — NOT a bug)*: catches `Exception`, logs with `exc_info=True`, returns None. The `None` return is the **correct, intentional** contract: `startnewfile` (L2442) returns it straight through, and `None` means "no LIFT file created — send the user back to pick again" (same signal the two deliberate `return` paths at L2611/L2618 already use). The try/except is **intentional debug instrumentation** to surface unknown errors with a full traceback in the log; reasonable to keep for now, slated for removal later. The one residual nit — the except path didn't call `waitdone()`, so an unexpected exception could leave the "Setting up new LIFT file now." dialog open — was **fixed 2026-06-05 (v1.2.0)**: `_analang_code_complete` now wraps its work in `with self.waiting(...)`, guaranteeing the dialog closes on any exit. The debug instrumentation (the outer `analang_code_complete` try/except) is retained as intended.
- **L2733-2734 `settings.Settings.langnames(self,demo.db.glosslangs)`**: calls an instance method as a free function with `self`=LiftChooser. Mutates LiftChooser instance to attach `languagenames` etc. Hacky but works because `Settings` doesn't exist yet at this point. Better: extract `langnames` into a free function in `settings`, use from both call sites.
- **L2864-2867 bare `except: pass`** around hiding the splash window — typical defensive pass.

### `Settings` class (L2871+)
- **Naming collision**: this class is called `Settings`, and the project's settings package also has `settings.Settings` (as referenced at L2734). The `Settings` here in ui_shell.py is in fact the *UI* settings — it's installed at `program.ui_settings`. Rename to `UISettings` or `SettingsUIDialogs` to disambiguate.

### Bare excepts (also see top-of-file `except:` listing)
- L1030, L1125, L2226, L2463, L2541, L2563, L2866. Pattern is "ignore failure during cleanup or optional UI ops." Each is small but together obscure real bugs. Audit each individually; convert to specific exceptions or at least log.

### Top hits from ui_shell.py
1. L1795 NameError waiting (`cvt/ps/profile` undefined in `getcheck`'s no-checks-non-T branch).
2. L869-870 `multicheckscopelabel` returns None — sets a `StringVar` to `None`.
3. L1456 `is` for int equality.
4. L2222 `bgl=ui.Label(verb,...)` — `verb` undefined; only "saved" by surrounding bare `except:`.
5. Naming collision between `frontend.ui_shell.Settings` and `settings.Settings`.
6. `StatusFrame` is doing too much; needs decomposition.

---

## frontend/task_window.py
- Tiny shim. Per CLAUDE.md, the use of `object.__getattribute__(task, name)` to bypass the task's own `__getattr__` is intentional. Looks correct.
- **L26 `task.ui = self`**: bidirectional reference set in `__init__`. If `TaskDressing.__init__` raises afterward, `task.ui` already points to a half-constructed window. Acceptable.

## frontend/sort_buttons.py

- **L11 `class SortButtonFrame(ui.ScrollingFrame)`**: relies on `Frame.__init__`'s MRO behavior at ui_tkinter:1571 to fire `post_tk_init` for non-Frame subclasses. Brittle without a comment explaining why this works.
- **L156 `waiting=task`**: rename of `task` to `waiting` so `waiting.wait/.waitprogress/.waitdone` calls go through the task's `__getattr__` → `self.ui` chain. Works but obscures who's doing what.
- **L403-406 bare `except: pass`**: silently swallows any error from `verificationcode`. Replace with a specific exception.
- **L443 `max=0`**: shadows builtin `max`. Used at L447 only — rename `_max`.
- **L99-108 `frame_class(...)`**: SortGlyphGroupButtonFrame expects `group=glyph` while SortGroupButtonFrame expects `group=item code`. Different semantics, same kwarg name. Keep them separate or document loudly.

## frontend/sort_ui.py
- Pure presenter; clean.

## frontend/lexicon_ui.py
- **L9 `from frontend.ui_shell import ImageFrame`**: presenter pulls a UI class from `ui_shell`. Acceptable; consider moving `ImageFrame` to a shared module so presenters and UI shell don't share import edges.

## frontend/vcs_ui.py

- **L52 `getattr(self.program, 'tk_root', ui.Root())`**: the default `ui.Root()` is *eagerly evaluated* every time `show_exe_warning` is called, regardless of whether `tk_root` exists. Constructing a Root instantiates Theme, runs `setimages` (heavy), creates a tkinter window. Use `or` short-circuit:
  ```python
  parent = getattr(self.program, 'tk_root', None) or ui.Root()
  ```

## frontend/report_ui.py
- Clean.

## frontend/error_notice.py

- **L24 `parent=ui.Root()`**: same eager-Root issue as vcs_ui — calling ErrorNotice with neither `parent` nor `program` constructs a fresh Root. Acceptable for early-startup errors but document the contract.
- **L39 `self.title = title`**: clobbers `tkinter.Toplevel.title()` (a method) with a string attribute. Any later call to `self.title(...)` would TypeError. Either rename to `self._title` or skip the assignment.
- **L48-54 button binding chain**: `add='+'` binds withdraw → user_cmd → destroy. If `user_cmd` raises, `destroy` never fires; the window leaks.
- **L25-28 parent.exitFlag check**: if parent is exiting, the function logs and returns *with the partially-constructed Window already created* via super().__init__. Order matters — call super after the check, not before.

## frontend/transcriber.py

- **L124, L129 `if char == ' ': … elif char == ' ':`**: two equality checks against visually identical strings. Either second branch is unreachable, or one is U+00A0 (non-breaking space). Verify byte content; either way the code needs a comment or named constants.
- **L77-87**: creates fresh `AudioInterface`, `BeepGenerator`, possibly `SoundSettings` even if `soundsettings` was passed in. New AudioInterface conflicts with any concurrent Sound task that already opened a stream. Reuse the existing pyaudio handle from `program`/`task` if available.

## frontend/sound_ui.py

- **L99 `self.id=id`**: assigns the builtin function `id` to `self.id`. Almost certainly a leftover/typo — never read. Delete.
- **L103-104 bare `except`**: probes pyaudio and falls back to constructing a fresh `AudioInterface`. If the original pyaudio is broken, the fresh one will likely fail the same way. At least narrow to `AttributeError` (the most likely cause of the probe failing).
- **L110 `exit()`**: kills the Python process from inside a frame init. Should raise; let the caller decide how to handle missing settings.
- **`Task` class at L777**: a stub used only by the `if __name__ == "__main__":` self-test (L802+). Move to a separate test file or wrap in `if __name__`.

---

## tasks/base.py
- Clean. `__getattr__` recursion guard well-defended.
- **L101-108 `makeeverythingok`**: catches AttributeError and just logs. May hide real bugs in `slices`/`status`. Narrow the catch or assert preconditions.

## tasks/tasks.py

- **L24-138 `ExportData(ui.Window)`**: subclasses `ui.Window` directly instead of `Task`. Dead code (`Grep ExportData(` only finds the class definition; never instantiated). Bugs if it ever were:
  - **L131 `def __init__(self, arg)`**: `arg` parameter unused.
  - **L133 `self.program.name`**: `self.program` never set in this constructor — AttributeError.
  - **L134 `self.program.root`**: should be `tk_root`.
  Drop the class or rewrite as a real Task.

## tasks/chooser.py — TaskChooser

- **L52-89 `guidtriage`/`guidtriagebyps`**: marked obsolete. Both call `nowruntime()`/`logfinished()` which are NOT imported in this module — NameError on any actual call. Confirmed dead, but they're noise. Delete.
- **L142 `taskclass(program=self.program,**kwargs)`**: instantiates the task and discards the return value. The constructor has side-effect `self.i_am_the_task()` that wires `program.task=self`. Implicit data flow worth a comment.
- **L429-431 `except (AttributeError, Exception)`**: `Exception` already covers `AttributeError` — tuple is redundant.
- **L463-465 `on_quit`**: calls `super().on_quit()` then `self.parent.on_quit()`. After super destroys self, parent destruction in the chain may already be done. Probable double-destroy → TclError suppressed by Tk.

## tasks/sound.py — **Record mixin is broken**

- **L2 `from frontend import sound_ui, ui_shell as ui`**: aliases `ui_shell` to `ui`. The `Record` class then calls `ui.Label(...)`, `ui.Button(...)`, `ui.Frame(...)`, `ui.ScrollingFrame(...)` (e.g., L68, L92, L103, L119, L139, L159, L174, L177, L185, L188, L200-205, L240-244). But `ui_shell` does **not** re-export those widget names — they're accessible from inside ui_shell only as `ui.Label` (where `ui` is the backend module imported at ui_shell.py:10). `ui_shell.Label` does not exist.
- **Effect**: any `Record` method that creates a widget will AttributeError on first call.
- `Record` is mixed into `RecordCitation` (tasks/tasks.py:1778) and `RecordCitationT` (L1794) — both user-selectable from `chooser.py`. Recording menu items will crash.
- **Fix**: change L2 to `from frontend import sound_ui, ui` (drop the `ui_shell as ui` rename). `ui_shell` itself isn't otherwise used in this file.

## tasks/ui_protocol.py
- Pure abstract. CLAUDE.md says `TaskDressing` implements it, but `ui_shell.py` has no `show_run_window`/`clear_run_window` methods — backend code uses `getrunwindow`. Protocol and implementation are out of sync.

---

## tasks/alphabet_chart.py and tasks/alphabet_comparison.py
- Both have `from frontend import ui` *inside method bodies* (chart L25, L39; comparison L24) to keep top-of-module backend-pure. Acceptable workaround. The save_settings methods log "Didn't find ui.Variable" as info — debug-level chatter.

---

## backend/core/lexicon.py — **violates frontend-isolation contract**

CLAUDE.md states "All backend modules have zero frontend imports" and "Presenters handle UI widget creation … `LexiconPresenter` for `lexicon.py`."

- **L807, L810, L813, L815**: bare `ui.Label(...)` and `ui.Button(...)`. **`ui` is not imported anywhere in this file** — the surrounding lines correctly use `p.label(...)`/`p.button(...)` (the LexiconPresenter), but four lines slip back to `ui.X` references. NameError at call time.
  - Fix: change `ui.Label` → `p.label`, `ui.Button` → `p.button`. The same imageparameters block uses `p.button` at L800 and L804, so the pattern is established right above the bug.
- **L1543 bare `except: …`** in `submitparse`: catches everything just to access `kwargs['entry']` from outside the try-block; the variable `kwargs` is not even in this method's scope, so the recovery line itself NameError's. Confirm `kwargs` is reachable; if not, this except-arm is dead-and-broken.
- **L1615 bare `except: …`** in `showwhenready`: catches all errors and reschedules via `self.after(1, ...)`. If `self.status.winfo_exists()` fails because `status` doesn't exist, the loop never terminates.
- **L51, L222, L241, L661, L833, L880, L921 ErrorNotice calls**: imported as `notify_error as ErrorNotice` from `utilities/error_handler.py` — fine pattern.

## backend/core/sorting_engine.py
- No frontend imports, no bare excepts, no `ui.X`. Clean per the contract.

## backend/core/categories.py
- Clean.

## backend/core/sound.py
- **L73-77**:
  ```python
  except BaseException as e:
      log.debug(...)
  except:
      log.info("Problem playing! %s")
      return 1
  ```
  `BaseException` catches everything (including SystemExit, KeyboardInterrupt). The bare `except:` after it is **unreachable**. Remove or restructure.
- **L76**: `"Problem playing! %s"` has a `%s` placeholder but no formatting args. Fix or drop.
- **L99 `raise`** inside `default_in()` (with no active exception): bare `raise` raises `RuntimeError("No active exception to re-raise")`. Should be `raise RuntimeError("...")`.

## backend/core/analysis.py
- **L40, L44 bare `except`**: standard "if-not-exists, init" pattern in `addresult`. Replace with `if check.name not in self.checkresults: …`. Class is "Not in use" per L28 comment — likely deletable.

## backend/core/alphabet.py
- **L482 bare `except: sense.image = None`** during image creation. Narrow to expected exceptions (FileNotFoundError, PIL.UnidentifiedImageError, etc.).

## backend/core/vcs.py
- **L496 bare `except: pass`** when appending command output to error text — ok for cosmetics but suppresses real bugs.
- **L499-502** pattern: `try: assert self.code == 'git'; ErrorNotice(text) except (RuntimeError, AssertionError):` — using AssertionError for control flow + RuntimeError because ErrorNotice may raise mid-startup. Awkward but documented.

## backend/core/file_parser.py
- L72: stale commented-out reference to `ui.Button(self.outsideframe, ...)`. Backend still references frontend symbols in comments; per project convention, consider making this a presenter call when un-comment.

## Verdict for backend/core
- The CLAUDE.md "zero frontend imports" claim holds for all files **except `lexicon.py`** (the four `ui.X` references at L807-815). Fix is small and local.

---

## settings/ (domain-split rebuild)

### settings/manager.py — `ConfigManager`

- **L72-88 `__getattr__`/`__setattr__`**: any attribute access (other than the four reserved names at L79) routes to `self.data` and *triggers a JSON write* on every `__setattr__`. This means:
  - Setting any setting hits the disk every time — N writes for N settings during init.
  - Any incidental `self.foo = bar` you might add to a subclass would also write to JSON. Surprising.
  - **L86 `self.save()`**: `set()` already calls save (L70). Setattr also writes. Two paths, same effect, inconsistent with no-op for known names.
- **L72-75 `__getattr__`**: raises AttributeError if `'data' not in self.__dict__`, but during pickle-restore or partial init that test could fail oddly. Minor.
- **CustomEncoder L17-25**: handles `set` and `Path`. The fallback `try: super().default(o); except TypeError: return str(o)` silently coerces anything to its `str()` — losing type info on round-trip.

### settings/__init__.py

- **Naming collision**: `class Settings(SettingsUI)` here AND `frontend/ui_shell.py` defines another `class Settings`. Code reading `settings.Settings` vs `ui_shell.Settings` requires careful imports. (Already noted in ui_shell findings.)
- **L119 `from frontend.config.settings_ui import SettingsUI`** at module top: the `Settings` class is therefore frontend-coupled. Any import of `settings` package triggers loading of frontend. CLAUDE.md says settings is the bridge — fine, but the `SettingsManager` and `AppSettingsManager` (L12, L40) defined *above* L119 should ideally live in their own module so headless code can use them without importing `Settings`/frontend.
- **L292 `exit()`** in `loadandconvertlegacysettingsfile`: kills the process if a legacy attribute didn't round-trip. Should raise instead.
- **L398 bare `except: …`** in `makesettingsdict`: catches all errors during attribute lookup, just logs. Replace with explicit `(AttributeError, KeyError)`.
- **L546 `exit()`** in `getdirectories`: process death on missing directory. Should raise/notify the user.
- **L93-94 `import gettext as _gettext; _builtins_gettext = _gettext.gettext`**: the `_builtins_gettext` reference is never used; dead.
- **L122 `class Settings(SettingsUI)`**: docstring says "backend logic + UI methods from SettingsUI", but the file has 1000+ lines of backend logic mixed with attribute-rerouting. Worth splitting into a real `SettingsBackend` and the UI subclass.
- **`fndict` pattern (L347-379)**: builds a dict of getter callables from object attributes during init. If any of the listed objects (`self.glosslangs`, `self.program.alphabet`, etc.) isn't ready, the whole dict-build fails partway and the rest of attributes are silently skipped (L374-377). `_log.error` is logged, but the function returns `[]` mid-init, leaving the settings object in an inconsistent state. Fragile; consider building `fndict` lazily.
- **L953-1003 `langnames`**: Hard-codes 50+ language names. Comment says it should use ldml files; never refactored.

### settings/{project,ui,audio,alphabet,contributors,data,reports,app}.py
- All small wrappers around `ConfigManager`. Trust until specific issues surface.

---

## io_put/

### io_put/sound.py
- L147, L181, L297: bare `except:` in playback/recording paths. Stream-cleanup flow that probably should narrow to PortAudio errors (`OSError`, `pyaudio.paError`).

### io_put/lift.py — pervasive `exit()` and bare excepts
- **L3766, L3803, L3932 `exit()`**: production code paths kill the process when XML structure looks unexpected. Each should `raise` a domain-specific exception so callers can recover or notify the user.
- **L4935 `exit()`**: inside `if __name__ == '__main__':` (L4871) — fine.
- **Bare `except:` instances**: L70, L188, L204, L1209, L2534, L3325, L3349 — most around XML node lookups. Each should be `except (AttributeError, KeyError, et.ParseError):` or whatever's actually expected. Bare except will swallow `KeyboardInterrupt` mid-load.
- **L4871-4935 ad-hoc analysis script** at module bottom: developer's scratch file pinned to specific paths under `/home/kentr/...`. Move to a separate script.

### io_put/xlp.py
- **L17 `exit()`**: production class init kills the process. Convert to raise.
- L78, L133 bare excepts.

### io_put/pdf_fonts.py
- L44 bare except.

### io_put/export.py
- Clean (no excepts/exits in spotcheck).

---

## utilities/

### utilities/error_handler.py
- Clean. The runtime-pluggable handler is the right pattern for backend → UI error notification.

### utilities/utilities.py
- **L266, L274 `sys.exit()`**: inside `sysshutdown()`/`sysrestart()`. Intentional and clearly named. OK.
- **L373 `exit()`**: in some helper that "should never happen" — replace with `raise RuntimeError(...)`.
- L169, L203 bare excepts.

### utilities/file.py
- L232, L234, L411 bare excepts on file-existence checks. Should be `except FileNotFoundError:` (or just `if not path.exists()`).

### utilities/rx.py
- L74 bare except.

### utilities/xmletfns.py
- L94 bare except.

### utilities/executables.py
- L33, L51 bare excepts on subprocess calls — narrow to `subprocess.CalledProcessError`/`FileNotFoundError`.

---

## main.py

- **L7-8 `if duplicates.running_file(__file__): exit()`**: top-level singleton check; fine.
- **L9-19 program dict**: documented; mutable global. Constructed before `App()` exists — has to be threaded through everything (per CLAUDE.md).
- **L45-53**: optional sound import wrapped in `try/except Exception`. `program['exceptiononload']=True` is set but never read elsewhere. Dead flag?
- **L72 `from frontend import ui`**: pulled in early because tkinter root is created here. OK.
- **L86-87 imports `Settings as UISettings` from `ui_shell`**: matches the rename suggestion — good practice. The other `Settings` (settings package) is imported at L102. Two `Settings` classes coexist via aliasing.
- **L88-91**: imports `notify_error` and `set_error_handler` and wires up `frontend.error_notice.ErrorNotice` as the handler on first import. Done at module top before `App.__init__` — startup-time errors before this line will use the default stderr handler.
- **L138-142 `handle_exception`**: ~~defined but Grep shows no `sys.excepthook` assignment~~ — *corrected 2026-06-05:* it **is** wired via `sys.excepthook = self.handle_exception` (~L625, in `App.__init__`). Not an issue.
- **L170, L189, L324, L414, L672, L725, L728 bare excepts**: typical defensive scaffolding around translation/scaling/exit cleanup. Each should narrow.
- **L676 `sys.exit()`** at the end of `App.run()` — intentional finalizer.
- **L324 `except: # Windows 8 or before`**: comment shows the intent (legacy Windows API miss); narrow to `(AttributeError, OSError)`.

---

# Summary — Highest-priority issues

These are the bugs that will fire (or silently corrupt behavior) under normal use, ranked roughly by severity:

| # | Location | Issue | Status (2026-06-05) |
|---|----------|-------|---------------------|
| 1 | `tasks/sound.py` L2 | `from frontend import sound_ui, ui_shell as ui` — `ui_shell.Label/Button/Frame/...` don't exist. Every Record-task widget call AttributeErrors at runtime. Affects user-facing RecordCitation / RecordCitationT. | ✅ Fixed |
| 2 | `frontend/ui_tkinter.py` L1660 | `except _tkinter.TclError` — `_tkinter` not imported. Any TclError on Button enter/leave bind raises NameError instead. | ✅ Fixed |
| 3 | `frontend/ui_tkinter.py` L2440-2442 | `ScrollingListBox.__init__` missing comma → `'nsew' ** kwargs` TypeError on every call. | ✅ Fixed |
| 4 | `backend/core/lexicon.py` L807-815 | Four `ui.Label/Button` calls without `ui` imported — NameError when the imageparameters block runs (image-selection workflow). | ✅ Fixed |
| 5 | `frontend/ui_shell.py` L1795 | `getcheck` no-checks-non-T branch references undefined `cvt/ps/profile`. NameError. | ✅ Fixed |
| 6 | `frontend/ui_shell.py` L869-870 | `multicheckscopelabel` returns None implicitly; `StringVar.set(None)` corruption. | ✅ Fixed |
| 7 | `frontend/ui_shell.py` L2222 | `bgl=ui.Label(verb,...)` — `verb` undefined; only "saved" by surrounding bare except. | ✅ Fixed (verified 2026-06-05 — now `ui.Label(self,...)`) |
| 8 | `frontend/error_notice.py` L39 | `self.title = title` clobbers `tkinter.Toplevel.title()` method. | ✅ Fixed |
| 9 | `backend/core/sound.py` ~L67-97 | `except BaseException` followed by unreachable bare `except`; bare raise at L99. | ✅ Fixed (direct-read 2026-06-06): `BaseException`+unreachable-`except` pair gone (now `except Exception as e: … return 1`, L73-75); `default_in()` now `raise AttributeError("audio_card_in")` (L97). Remnant is cosmetic only: L68 `"Problem recording! %s ({})".format(e)` prints a literal `%s` — no crash. (No format arg-count mismatch — an earlier draft claimed one; `io_put/sound.py:37-39` has 4 `{}` and 4 args.) |
| 10 | `frontend/ui_tkinter.py` L266 | `randint(0, len(pot))-1` skews theme distribution to last entry. | ✅ Fixed |
| 11 | `frontend/ui_tkinter.py` L629 | `if e == 'cannot open resource'` compares OSError instance to string — never matches. | ✅ Fixed |
| 12 | `frontend/ui_shell.py` L1456 | `if n is optionlist_maxi` — int identity comparison; unreliable. | ✅ Fixed (verified 2026-06-05 — now `if n == optionlist_maxi`) |
| 13 | `frontend/ui_shell.py` L2604 | ~~`analang_code_complete` swallows Exception silently; user sees nothing.~~ Re-assessed: **not a bug**. `None` is the correct "no file created, pick again" contract; the try/except is intentional debug instrumentation (logs full traceback). Keep for now. Minor nit: except path skips `waitdone()` — see LiftChooser section. | ⬇️ Downgraded — not a bug |
| 14 | `tasks/tasks.py` L24-138 (ExportData) | Dead and broken: `__init__(self, arg)` doesn't set `self.program`; references `self.program.root` (typo for `tk_root`). | ✅ Fixed (constructor; may still be unused) |
| 15 | `vcs_ui.py` L52 / `error_notice.py` L24 | `getattr(self.program, 'tk_root', ui.Root())` eagerly constructs a Root every call. | ✅ Fixed (direct-read 2026-06-06): both halves. `vcs_ui.py:52` is now `getattr(self.program, 'tk_root', None) or ui.Root()` — `or` short-circuits, so `ui.Root()` is built only when `tk_root` is missing (this is exactly the lazy fix the original finding recommended; NOT eager). `error_notice.py` uses the conditional `if not (parent:=…)` form. |

# Architectural concerns (lower priority, structural)

- **`StatusFrame` (~900 lines)** in `ui_shell.py` does too much; abstract a `StatusLine` helper for the duplicated label/update/get-text triplets.
- **Naming collisions**: two `Settings` classes (`frontend.ui_shell.Settings` and `settings.Settings`); two `Task` classes (`tasks.base.Task` and `frontend.sound_ui.Task` — though the latter is a self-test stub).
- **`tasks/ui_protocol.py` is out of sync** with `TaskDressing`'s actual API (`show_run_window` vs `getrunwindow`).
- **`ui_interface.py` is documentation-only**: `ABC` decorations don't enforce anything because most interface classes have empty bodies.
- **Pervasive bare `except:` and `try/except Exception: pass`**: documented above per file. Each obscures real bugs and is the largest source of "code that should fail but doesn't."
- **`exit()` and `sys.exit()` in production code paths**: lift.py, settings/__init__.py, sound_ui.py, utilities/utilities.py L373. Library code shouldn't kill the process; raise instead.
- **Frontend isolation contract** (per CLAUDE.md "All backend modules have zero frontend imports") is mostly upheld, with one violation in `lexicon.py` (#4 above) and slight wobbles where backend modules use `ui.X` in dead/commented code.
- **Module-level `_=gettext.gettext` shadowing** the swappable i18n: `ui_tkinter.py`, `settings/manager.py` (L7), and possibly others. CLAUDE.md says all modules should `from utilities.i18n import _`.
- **`StringVar` defaults from settings**: `settings/__init__.py` L1064-1071 lazily imports frontend to create UI vars. The settings package thus has both pure-config paths AND UI-coupled paths in the same class. Splitting `Settings` into a backend portion and a UI subclass is overdue.
- **DPI scaling and image-rescaling coupling**: `Theme.setimages` → `Theme.setscale` → `Renderer.render` form a tight chain of side effects across `ui_tkinter.py`. Document the lifecycle or break apart.

# Done
- All planned files audited. See sections above for per-file detail.


Top 5 real bugs to fix first:                                                                                                        
                                                                                                                                       
  1. tasks/sound.py:2 — from frontend import sound_ui, ui_shell as ui should be from frontend import sound_ui, ui. Every Record-task   
  widget call (RecordCitation, RecordCitationT) currently AttributeErrors at runtime because ui_shell doesn't re-export                
  Label/Button/Frame/ScrollingFrame.                                                                                                   
  2. frontend/ui_tkinter.py:1660 — except _tkinter.TclError references an unimported name; any TclError on Button enter/leave bind     
  triggers a NameError that masks the original error.                                                                                  
  3. frontend/ui_tkinter.py:2441 — ScrollingListBox.__init__ missing comma: sticky='nsew' **kwargs parses as str ** dict, TypeError on 
  every call.                                                                                                                          
  4. backend/core/lexicon.py:807-815 — four ui.Label/Button calls but ui is not imported; the surrounding code correctly uses the      
  presenter p. NameError when the image-selection workflow runs.                                                                       
  5. frontend/ui_shell.py:1795 — getcheck non-T no-checks branch references undefined cvt/ps/profile. NameError when reachable.
                                                                                                                                       
  Plus four broken-by-design items (ExportData has a no-arg constructor, multicheckscopelabel returns None, ErrorNotice clobbers       
  Toplevel.title(), randint off-by-one) and structural concerns documented in the summary section. The audit covers ui_tkinter,        
  ui_interface, ui_shell, presenters, task_window, all of tasks/ and backend/core/, settings, io_put, utilities, and main.             

