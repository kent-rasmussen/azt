# A-Z+T Changelog

#UW priorities:
- sorting by click and drag
- check recording and transcription tasks are working normally
- ?other comparative wordlists

#Next up:
- rework USAGE.md
- Parsing:
  - Addition of second forms (primary data)
  - Parsing of lexeme forms (analysis)
  - writing of lexical categories (analysis)
  - Store affixes in entry and elsewhere (new settings file?)
  - Clarity for user wrt what is data (i.e. lc, pl, imp), and what is analysis (i.e., lx, ps) —in the presentation of the task itself, and in the documentation
- Migration to working on the appropriate form, synchronizing across frame definitions, etc.
- Catch up on translation
- make singleton reports run not in background, or give user more helpful info, if analysis isn't done.
- ?check on bug with getprofile in reports bringing up taskchooser; fixed in other tasks, but not reports?
- make showoriginalorthographyinreports a UI switch

# Version 1.10.2
- FEATURE (collaboration — open a team project from GitHub). The LiftChooser
  gains "Get a project from your team (GitHub)": spawns the collab daemon's
  project picker (sign-in, list, clone or create; the same picker the
  recorder uses), and opens the returned project CONNECTED — the picker's
  langcode pre-sets the per-project collab flag that `attach()` gates on, so
  no Advanced → Connect step is needed. The picker is a Kivy app, so azt
  drives it through the existing interpreter-candidate loop
  (`AZT_COLLAB_UI_PYTHON` → own python → suite venvs); requires client
  0.54.6 (`pick_project(python_exe=…)` — older clients fall back to the
  host interpreter, which works only if it has Kivy). Cancel returns to the
  chooser. Note: the daemon settings-UI's own project switching remains
  daemon-side only — azt reads its own last-file, not `last_project()`.
- FEATURE (install — sister-repo self-heal, one mechanism). New
  `utilities/sister_repos.py` owns a declarative table of the repos azt
  expects cloned beside its own clone — `azt-collab` (daemon+client),
  `images_CAWL` (illustrations, linked at `images/toselect`), and
  `lift_templates` (stock wordlists, linked at `lift_templates/SILCAWL`) —
  and the shared mechanics: startup `ensure_all()` from `py_modules` clones
  whatever is missing and creates the in-repo access links (symlink;
  Windows falls back to a directory junction, which needs no Developer
  Mode); a fresh `git clone azt` install self-completes on first run.
  Principles: never block startup (no git / offline / timeout /
  unrecognizable existing dir all log-and-continue), never touch anything
  the run didn't create, no network when a local copy is already reachable
  (dev symlink, pip, `AZT_COLLAB_DIR`, existing clone — boot never pulls).
  `images/to_select_update.py` and `lift_templates/SILCAWL_update.py` are
  now thin wrappers over it (their standalone CLI use and
  `io_put/cawl.py`'s lazy `ensure_available()` unchanged); their old
  copies' `sys.exit(1)` foot-gun (would have killed the app when the link
  target was a real directory) is gone with the duplication.
- FIX (pyflakes sweep — undefined names). Beyond the crash-driven fixes below
  (`ToneFrameDrafter`, `randint`, `fixnaivedatetime`, `nowruntime`), a full
  pyflakes pass caught the rest: `categories.py` `ftype`→`self.ftype` ×2 and
  undefined `group` in two error messages; `lift.py` `childrenwtext` `i`→`self`
  (gloss-node path) and `prettyprint`→`et.prettyprint`; `xlp.py`
  `except Error`→`Exception`; `encodings.py` missing `_` import;
  `executables.py` missing `stouttostr` import; `file_sound.py` missing
  io/os/tarfile + file-helper imports (librosa now lazy);
  `alphabet_comparison_pdf.py` `logging`→module `log`; `xmletfns.py` broken
  dead `TreeParsed` removed + local `BadParseError` defined (was a NameError
  on any bad-XML parse); chooser `logfinished`→log line; dnd_motion dead code
  removed; `Window` backcmd lambda no longer references never-existent names;
  `asr.py` faster-whisper stub gets `threads=4`; `langtags.unprivate` (never
  functional, no callers) now raises NotImplementedError.
  `utilities/openclipart.py` left as-is (documented orphan, not imported).
- FIX (reports — scope/background mixin init order). The report mixins
  (`Multislice`/`MultisliceS`/`MultisliceT`/`Multicheck`/`Background`) ran
  their bodies BEFORE the task chain initialized: `Background` read `self.do`
  before any report class had set it (crash opening every backgrounded
  report, e.g. Tone Report by frames), the scope mixins touched
  `self.program`/`self.status` before `Task.__init__`, and `Multicheck`
  didn't call `super().__init__` at all — so its variants never built a task
  window. All now run `super().__init__` first, set their report function
  via a shared `set_do()` (which re-applies the background wrap for
  Background variants), and rebuild the final buttons after changing `do`.
- FIX (reports — missing stylesheet killed the report silently).
  `xlp.stylesheet()` assumed `stylesheetdir` even though init explicitly
  supports its absence (no `xlpstylesheets/` ships with azt) — `close()`
  died there BEFORE `write()`, so the report file never landed and the
  failure was invisible (background thread). Reports are now written
  unstyled when no stylesheet directory exists, with one info line.
- FIX (reports — crashed run blocked all future runs). The 0-byte `.tmp`
  in-process sentinel is only cleared by `cleanup()` at the END of a
  successful `close()`, so any crash left it behind and every later run
  bailed at init ("already in process; not doing again") — forever.
  `close()` now clears the sentinel in a `finally:`, and init treats a
  sentinel older than an hour as stale (clears it and proceeds), so a
  crashed run self-heals instead of wedging the report.
- FIX (tone — join/rename pages never appeared). `tonegroupsjoinrename` and
  the rename-group comparison page blocked on `wait_window` over a runwindow
  that was never deiconified (created withdrawn; the reveal-via-wait path is
  gated on a mature legacy repo, which never exists under collab). Explicit
  `deiconify()` after `waitdone()` at both sites.
- FIX (tone — `fixnaivedatetime` NameError in `isanalysisOK`). Imported from
  `utilities.times` alongside `now`.
- FIX (tone frames — names containing 'x' vanished). The sort-task check list
  drops correspondence checks (V1xV2 etc.) by testing `'x' not in name` — safe
  for machine-generated segmental names, but it silently swallowed user-named
  tone frames like 'Exists'/"Doesn'tExist" (and demoted the current check on
  every boot, which mimicked a persistence bug). The filter now skips cvt 'T'.
- FIX (tone frames — persistence). Tone frames survive reboots again. The JSON
  settings migration had dropped the load-side special case: a saved
  `toneframes` dict was parked on the settings object instead of reaching
  `program.toneframes` (the legacy .ini reader had this case; `readsettingsdict`
  didn't). Frames now route through `toneframes.source()` on load, mirroring
  `status`. Also fixed swapped constructor args in `maketoneframes`.
- CHANGE (tone frames — own settings file). Tone frames now live in
  `<project>.tone_frames.json` (new `tone_frames` settings domain) instead of
  inside `<project>.data.json`. One-time relocation moves any `toneframes` key
  found in the data domain into the new file. Legacy `.ToneFrames.dat`
  migration now actually works too — it was permanently masked before because
  the data-domain JSON always had content, which suppressed the legacy reader.
- FIX (tone frames — drafter revival). The Define-a-New-Tone-Frame dialog
  (`ToneFrameDrafter`) had bit-rotted: missing `ToneFrameDrafter` import at the
  lexicon call site (backend-safe local import), missing `self.program`, a
  `t(...)` call on an undefined name, task-style `self.ui.…` calls in a class
  that IS the window (exitFlag/withdraw/deiconify), `program.root.wraplength`
  (no such attr; windows inherit `wraplength`), missing `randint` import, and
  example frames built without `scroll.reflow()` on the empty-name/no-example
  paths (invisible content). All repaired; frame definition verified live
  end-to-end (define → examples → submit → picker → reboot → still there).
- FIX (UI — drive_work robustness). `drive_work` now treats a `None` generator
  as zero work (close wait dialog, run on_done) in both backends — Tone's
  no-op `presortgroups` and the "presort already done" early return both
  produce None, which crashed with "'NoneType' object is not an iterator".
- FIX (UI — stale StatusFrame guard). `maybeboard()` returns early if its Tk
  widget was destroyed (task switch during the blocking "Done!" notice) —
  was: TclError "bad window path name … statusframe".
- Logging: one-line info on tone-frame load and add (real state changes);
  the DIAG-toneframes diagnosis lines from this arc are removed.

# Version 1.10.1
- CLEANUP (logging — DIAG scaffolding stripped). The groups-unverified diagnosis
  instrumentation is gone: all `DIAG-done` lines (analysis.py update-REMOVE,
  cull-DROP, group() non-str tripwire; settings full-reload SET; lift.py
  per-member read dump; sorting_engine.py verify-write dump) and all
  `DIAG-join-verify` node dumps (lift.py NOTDONE; sorting_engine.py
  maybesort/post-cull/join-start; categories.py after-reload). The join
  glyph-unverify line survives (real state change) without the DIAG prefix.
  `verified_groups_by_ps_profile` lost its now-unused `log_ps` parameter.
  Kept: DIAG-formconform, DIAG-conflict, DIAG-reveal (their arcs are open).
- CLEANUP (logging — boot/session noise demoted to debug, info kept for real
  events). A boot log drops from ~330 lines to ~40. Demotions: per-module
  "Logging INFO for …" (logsetup); the safe.directory triple dump + routine
  git config reads (vcs.py `do()` quiet-caller list: isbare, getusernameargs,
  get_all_safe, mark_safe, getfiles; plus abs_path, branch lookup, is-bare,
  useremail); settings moveattrstoobjects chatter — and its "Only finished
  settingsobjects up to …" line no longer logs at ERROR during normal
  progressive startup; chooser whatsdone() input dumps + per-field lines (the
  two done-with summaries stay); ui_tkinter screen-geometry block → one
  summary line; per-ps syllable-profile lines → one dict line; SGBF/glyph
  widget-build chatter; duplicated status.groups dumps (verify, add_int_group,
  categorizesenses); `_checkcodes_by_cvt`/`secondformfield` structure dumps.
  langtags' static language-support block now logs once per run (that module
  pins its logger to DEBUG, so it got once-guards instead of demotion).
  Everything demoted is still available at DEBUG loglevel; nothing that marks
  a data write, state change, error, or warning was removed.

# Version 1.10.0
- FEATURE (collaboration — in-place reload, "A5"). "Load now" on the team-changes
  offer now reloads the database IN PLACE: no process restart. Backend objects
  rebuild in boot order under the live UI; the task view swaps through the
  normal task-switch machinery; the collab session rebases to the daemon's head
  (`adopt_reloaded_db`, unit-pinned); a wait dialog covers the rebuild; and the
  task resumes AT THE USER'S POSITION (guid-keyed anchors for word collection
  and the record page). Any failure before the task swap falls back to the
  full restart. Field-verified through five hardening iterations (main.py
  `reload_database`; teardown lessons documented in the code).
- FEATURE (collaboration — ambient sync status). The visible window titles
  (task + runwindow) carry a live suffix from the 10 s poll: "N change(s) not
  yet shared" / "shared with team ✓" / "team changes available" / "saving
  locally — server unreachable". Keyed on `at_risk` (commits no other device
  has) so it's meaningful for LAN-only projects, where `wan_unshared` counts
  forever. (`CollabSession.ambient_status` + `App.collab_title_status`.)
- FIX (collaboration — NOTHING_TO_COMMIT is benign). Identical-content saves
  (unchanged autosaves; the healthy aftermath of a degraded direct write the
  respawned daemon already committed) no longer warn "history may catch up" on
  every save: adopt head, clear degraded, done. Unit-pinned.
- FIX (record tasks resurrected). `RecordCitation`/`RecordCitationT` lost the
  `Task` base at some refactor, making them unconstructible (kwargs rode the
  cooperative super() chain into `object`); `mikecheck` passed `program` where
  `SoundSettingsWindow` expects the task. Both fixed; record flows run again.
- FIX (LIFT serialization — whitespace hygiene). `Node.__init__`'s append path
  now maintains `.tail` whitespace, so azt-created nodes (citation, fields,
  forms, annotations) no longer serialize glued (`</sense><citation>`) —
  ending the meaningless whitespace diffs that inflated every merge.
- Field validation (2026-07-11, desktop ↔ phone over LAN): drills A1
  (phone→desktop incl. reload offer), A2 (desktop→phone), A3 (no-clobber:
  offline divergence both sides, merged, converged, nothing lost), A4
  (kill-daemon: silent degraded save, auto-respawn ≤10 s via the status poll,
  history self-caught-up), and no-gesture convergence in both directions.

# Version 1.9.0
- FEATURE (sorting — Review Letter Groups). Position-matched default presentation:
  when a pair of letter groups is shown, each glyph frame now defaults to the
  member whose check position best matches the other's — privileging FIRST the
  number of frames shown in the same position, THEN the position nearest the
  front of the word (C1 before C2; `C1=C2` counts as position 1; digitless
  checks last). Uncovered frames pair among themselves or fall to their own
  frontmost. Default only — manual cycling of groups/examples is untouched.
  `frontend/sort_ui.py` `choose_shown_checks` + `show_default_members`;
  tests in `tests/test_choose_shown_checks.py`. (Previously the shown member
  was set-iteration-order accident.)
- I18N (smartquotes sweep). All user-facing `_()` strings now use typographic
  quotes (‘ ’ / “ ” / don’t): 226 msgids across 39 files, with the matching
  msgids rewritten in lockstep in all five `translations/*.po` so no
  translation was orphaned. Machine-parsed quotes untouched.
- FIX (i18n — 13 latent translation misses). `.format()`/f-strings INSIDE `_()`
  made runtime lookup keys differ from extracted msgids (translation never
  matched); interpolation moved outside `_()` in `lift.py` ×4, `sound_ui.py` ×2
  (whose existing curly-quoted .po translations now finally apply),
  `py_modules.py` ×2, `utilities.py` ×2 (also fixes literal `{val} ({type(val)})`
  printing), `chooser.py` ×2, `generator.py` ×1.
- FIX (sorting — form corruption guard). `build_form_from_verified` (the
  authoritative whole-word rebuild) concatenated raw verified values, so a slot
  verified into a still-UNNAMED (digit-placeholder) group entered the form:
  'bʊsh'→'b1sh'. Now defers (logs `DIAG-formconform BUILD-DEFER`) until every
  slot's group is named — the same guard every patch path already had.
  Corrupted forms self-heal on the next whole-word update once named.
  `backend/core/lexicon.py`; tests in `tests/test_build_form_from_verified.py`.
- FIX (sorting — joins drained glyph memberships). `cull_glyph_members` treated
  "not currently done+distinguished" as "doesn't exist", so every join stripped
  the joined-into group's code from its glyph, deleted the emptied glyph from
  alphabet.json, and re-demanded a macrosort after re-verify. Existence
  (`items_existing`: group has members) now keys the cull; a join instead marks
  the containing glyph not-done (membership persists, the glyph re-verifies).
  `backend/core/alphabet.py` `refresh_items`/`cull_glyph_members`,
  `backend/core/sorting_engine.py` `join_pair_done`. NOTE: previously-drained
  memberships are not resurrected — re-macrosort once.
- FIX (sorting — spurious "Hey, you're not done…" notice). A completed inner
  pass (e.g. a join reached via an after()-fired maybesort inside an outer
  page's wait_window) tore down the shared runwindow, making the outer frame
  read as abandoned and warn mid-flow. Suppressed when a maybesort restart is
  already scheduled (`_maybesort_rescheduled`); genuine walk-aways still warn.
  Also removes the modal notice's 2s stall between a join and the next verify.
- FIX (data repair — collab-merge duplicate forms). A merge left a verification
  field with duplicate same-lang `<form>` nodes (observed ×29 on one entry),
  which shadow real data (reads/writes only see the document-first node).
  `Field.consolidate_forms_by_lang` (invoked from `verificationtextvalue`)
  unions the code lists into the surviving form, drops checks whose values
  conflict across duplicates (they re-verify), removes the extras, and logs a
  WARNING. Root cause (the merge itself) tracked in azt-collab.
- FIX (platform — XWayland wedges). Two hangs, one faulthandler-confirmed:
  `ScrollingFrame.reflow`'s bare `update_idletasks` deadlocked over a large
  backlog (booklet `add_pages`, ~40 page frames) — now a draining `update()`
  on Wayland only. The verify-page reveal path also drops its redundant second
  synchronous drain when the wait dialog already covered the build (waitdone
  did update+deiconify), skips pointless virtualization for lists that fit one
  screenful, and gains `DIAG-reveal` breadcrumbs so any future wedge names its
  call in the log.
- TESTS. `tests/test_status_dict.py` fake program gains `db=None` (cull()'s
  membership sweep reads `program.db.ps_profiles`; None = not computed).

# Version 1.8.6
- FIX (sorting — segmental join direction). When joining two groups where neither
  name is a digit placeholder, the SIMPLER (shorter) existing name is now kept and
  the longer one removed into it ('g' + 'gu' → keep 'g'), instead of the previous
  lexicographic accident of `sorted(key=str)` (which kept 'gu'). Digit placeholders
  still always lose to real names. No new names are invented — we only choose
  between the two that exist. `backend/core/sorting_engine.py` `join_pair`.

# Version 1.8.5
- FIX (collaboration — spurious "Team changes available" popup, azt side).
  Companion to azt-collab 0.53.8. All in `backend/core/collab.py` unless noted.
  - **F1 (root cause):** the consumed-but-errored save branch of
    `CollabSession.submit` (daemon stored the file but the commit step failed)
    returned OK without re-recording the LIFT stat, so azt's stat went stale
    against its OWN save and the next HEAD advance read as a peer change. Now
    calls `record_lift_stat()` there. Eliminates the whole observed popup class.
  - **F2 (self-healing latch):** once `stale` latched, `poll_remote_change`
    returned `'changed'` forever with no recovery. Now un-latches when the
    on-disk LIFT still matches our last write AND HEAD's LIFT blob equals our
    base's blob (content identity, via 0.53.8's new `lift_blob_sha`). Also fixes
    the double-dialog quirk (snooze-bypass now requires a non-empty prior offer).
  - **F5 (diagnosability):** the safe-save warning now also logs the daemon's
    preserved `SERVER_ERROR` detail, not just `result.codes()`.
  - **F6 (UX):** one reload-offer window at a time (`_collab_offer_win`
    `winfo_exists()` guard; `error_handler.notify_error` now returns the notice)
    — no more stacked "Team changes available" windows.
- FIX (sort robustness) — `Sort.presenttosort` no longer crashes the mainloop
  with `TclError: bad window path name` when the sort item is destroyed during
  the pre-wait `update()`/`reflow()` re-entrancy; `wait_window` is now guarded
  and falls through to the normal return (same end state as the item being
  destroyed during the wait). *(Pending field confirmation of no re-loop.)*

# Version 1.8.4
- FIX (presort, follow-on to 1.8.3) — positional checks now presort by that
  position alone, over cvprofile MEMBERSHIP, not whole-word regex shape.
  - **C1 (and any single Cn/Vn check) presorts by first/that consonant (or
    vowel), ignoring the rest of the form.** A word the linguist recorded as
    CVC whose surface form doesn't parse as CVC (e.g. `poe`/`doe` → the
    algorithm reads CV, `ʌng` → VCC) is now grouped by its C1 anyway — "if it
    starts with p, it goes with the other p words"; wrong guesses are corrected
    by the user at verify. Presort uses the positional matcher
    (`rxdict.rx[check]`) over `slices.senses(ps, profile)`; the whole-form
    `makeprofileforcheck`/`fromCV` match is bypassed for these checks.
    **cvprofile + check values are DATA and authoritative; `profileofform`
    is analysis and must never override the stored profile.**
  - **NA is no longer a catch-all.** Only equality (`=`) checks auto-populate
    NA (the not-equal set the user verifies out). For every other check, words
    the presort can't place are left UNSORTED (presented to sort) — NA means
    the user deliberately skipped a word (taboo, unknown, …) and is terminal.
  - `=` checks unchanged from 1.8.3 (whole-form match, membership universe).

# Version 1.8.3
- FIX (presort regression, completes 1.8.2) — for **equality checks** (`=` in
  the code) words are again presorted into **NA** and offered for verification,
  with no stray "presented to sort" step. 1.8.2 gated the NA one-shot verify but
  the pool was still empty; three deeper layers were the real cause:
  - **Segment inventory poisoned by syllable-slice ids.** The syllable-prep
    pseudo-cvt `'S'` collides with the sonorant class `'S'` (the CONTEXT.md
    "S-overload" trap), so `all_groups_verified_anywhere()` fed `setupCVrxs`
    the syllable node's `group␟slice` `done` ids, which got appended onto the
    sonorant inventory and folded into C-class expansion — `fromCV('CVC')`
    matched **zero** real words, so nothing reached NA. Fixed at the injection
    boundary (`profiles.py`): tokens containing `SyllableSliceDict.SEP` are
    filtered out before extending the segment inventory (SEP is collision-free,
    so only synthetic ids drop, never a real grapheme).
  - **NA excluded from the sort-group list for all checks.**
    `categorizebygrouping` (`settings/__init__.py`) unconditionally dropped
    `'NA'` from the rebuilt group list, so even a populated NA never reached
    `groups(toverify)`. Now the exclusion is gated on check shape: `=` checks
    keep NA in the list (it rides the verify loop); others still hide it.
  - **Presort universe too narrow for `=` checks.** The NA pool was seeded from
    the form regex, stranding profile words whose surface form isn't a clean
    C·V·C (e.g. nose→n-o-s-e) as "to sort". For `=` checks the universe is now
    profile membership (`slices.senses(ps,profile)`): every non-equal word lands
    in NA, nothing is left to sort, and the user verifies matches out of NA.

# Version 1.8.2
- FIX (presort regression) — for **equality checks** (`=` in the code: C1=C2,
  C1=C2=C3, V1=V2, CV1=CV2, …) words presorted into **NA** (the not-equal
  remainder) are again offered in the verify loop, so the user can verify them
  out (pull back any that actually ARE equal) and re-verify on demand. Root
  cause: 1.3.77 added a one-shot terminal verify of NA in the presort
  (`lexicon.py` `presortgroups`) that marked NA `done` for *every* check, so
  `groups(toverify)=groups−done` never re-offered it — right for skip-piles,
  wrong for `=` checks where NA is the check's real result set. The one-shot now
  fires only for non-`=` checks (skip pile stays terminal); `=`-check NA rides
  the normal `groups−done` loop as it did pre-1.3.77. Keyed on check shape,
  never a literal code; `x`-correspondence checks are excluded from sort tasks
  upstream. NA stays off the picker/board (separate filters) and out of the
  write-unsafe `groups(wsorted)` path.

# Version 1.8.1
- FIX — "Collaboration settings" no longer dies silently with `spawn_exited`:
  the daemon settings UI is a Kivy app, and azt's venv may not carry Kivy.
  `open_settings` now tries candidate interpreters in order —
  `AZT_COLLAB_UI_PYTHON`, azt's own python, then the suite's recorder/viewer
  venvs beside the azt-collab clone (client 0.53.4 `python_exe` param) — logs
  each failure with the child's stderr, and on total failure shows the real
  detail plus the Kivy hint instead of a bare error code.

# Version 1.8.0
- NEW — **collaboration Phase 4: sync UX parity.** "Synchronize with your team
  now" runs the full recorder-style routing table (`CollabSession.sync` →
  `route_sync_result`): never-silenced codes (DATA_LOSS_RISK,
  COMMIT_REPEATEDLY_FAILED) surface first; configuration-class refusals
  (AUTH_REQUIRED, CONTRIBUTOR_UNSET, NO_REMOTE, NOT_A_REPO,
  WORK_OFFLINE_ENABLED) open the daemon settings UI; GitHub-side blocks
  (APP_NOT_INSTALLED / APP_SUSPENDED / REPO_NOT_AUTHORIZED / REPO_NO_ACCESS)
  open the fixing URL in the browser; transient failures just say so;
  JOB_INTERRUPTED gets one silent retry; PULLED flags the session stale so the
  Phase-3 poll raises the reload offer (no dialog stacking). In-flight guard
  per §17c. New Advanced-menu entries: **Collaboration status** (backup truth
  per §17b 0.53.3: "up to date" requires `wan_unshared == 0 AND main_merged`;
  also uncommitted count, work-offline, pending team changes, degraded state,
  contributor) and **Collaboration settings** (daemon settings UI as a
  separate process; available before connecting too, e.g. to fix the
  contributor name). Deferred from the Phase-4 list: new-project-at-birth
  registration under $AZT_HOME (tracked in the agenda item).

# Version 1.7.2
- FIX — a daemon outage can no longer silence a pending reload offer: when the
  session is already stale, `poll_remote_change` reports 'changed' from local
  knowledge; the status probe only feeds the newest-head snooze bypass (caught
  by `test_poll_stale_tolerates_probe_failure`). Phase 3 verified live
  2026-07-07: offer on peer commit, decline → new peer commit re-offers
  promptly, "Load now" restarts onto the merged file.

# Version 1.7.1
- Collaboration reload offer: declining ("later") snoozes 5 min as before, but a
  **genuinely new** team change (a peer head we haven't offered for yet) now
  bypasses the snooze and re-offers promptly — so "I said later" quiets only
  that specific change, while fresh work always gets through. The poll keeps
  tracking the newest head while stale without ever advancing the base. Dialog
  wording fixed to make clear only "Load now" restarts (OK keeps working).
  Pinned by `tests/test_collab_session.py::test_reload_offer_new_head_bypasses_snooze`.

# Version 1.7.0
- NEW — **collaboration Phase 3: peer-change detection + reload offer.** A
  10-second background poll (`App.collab_poll`, tk after-loop) compares the
  daemon's `head_sha` against the session base; a HEAD advance with the LIFT
  file untouched on disk (artifact-only commit) silently adopts the new base,
  while a real content change (peer merge landed via LAN/WAN, or a save that
  came back MERGED_WITH_LOCAL) raises a rate-limited (5 min) offer: "Load team
  changes" restarts the app onto the merged file. Correctness never depends on
  the poll — saves are base-aware — it only bounds how long stale peer data
  stays displayed.
- FIX — **base bookkeeping after a merged save** (design-review catch): a
  `MERGED_WITH_LOCAL` save no longer advances the session base to the merge
  commit. The in-memory tree still derives from the old base, so advancing
  would let the *next* save fast-path replace the merged file and content-
  clobber the peer changes. Keeping the old base makes every subsequent save
  re-merge (peer changes ride "ours" and survive) until the reload resets the
  session. Pinned by `tests/test_collab_session.py`.
- Anchor-preserving in-place reload (no restart) remains future work; the
  restart-based reload is the honest v1 (azt's own database-switch flow is
  restart-based too).

# Version 1.6.0
- NEW — **collaboration-server integration, phase 1–2 (opt-in, per-project)**:
  a project connected via `backend/core/collab.py::connect_current_project`
  saves through the azt-collab daemon's base-aware `submit_file` RPC instead
  of plain `os.replace` + its own git commit. Peer merges that land between
  saves are three-way merged server-side (never clobbered); push/pull are
  daemon-owned (scheduler drain + shutdown sync replacing `share()`); legacy
  VCS (`repocheck`/`repo_commit`/`share`) is disengaged for connected
  projects only. Non-connected projects run the legacy path bit-for-bit —
  every seam is a two-branch switch on the per-project `collab` setting.
  Daemon-unavailable degrades to direct disk writes with a logged warning
  (saving never blocks on the daemon). Requires azt-collab ≥ 0.53.0, found via
  a discovery shim (plain import / dev symlink → `AZT_COLLAB_DIR` → an
  `azt-collab` clone beside the azt folder) — the symlink is a dev convenience,
  not load-bearing, since Windows checkouts can't rely on git symlinks. Advanced-menu entries: "Connect to
  Collaboration server" (legacy projects) / "Synchronize with your team now" +
  "Disconnect" (connected projects); on success these tell the user and then
  restart the app themselves once the notice is closed (the seams re-branch
  only at startup). Not yet wired: mid-session reload on peer
  changes (Phase 3 — merged peer content appears on next open; plan in
  agenda/azt_run_with_server.md).
- FIX — **draft selector no longer collapses to zero buttons.** When the
  'top models only' window was unanimous (top-5 all emitting the same form),
  dedup left one value and the selector showed nothing — reading as "ASR didn't
  work", and hiding that the one available transcription might differ from the
  visible/citation form (e.g. stored `mbumi` vs on-screen `bumi`). Two changes
  in `tasks/tasks.py`:
  - **Adaptive top-X**: the top-models filter now widens 5→10→15… until at
    least two distinct forms survive, and falls back to *every* stored draft
    once widening stops adding repos — or when the whole draft set is unanimous
    anyway (`_filter_top_asr`; headless tests in
    `tests/test_asr_draft_selection.py`).
  - **Always ≥1 button**: a single (unanimous) form still gets its button, so
    the user can SEE what ASR produced and revert to it; auto-fill of an empty
    field retained. Zero drafts no longer render the "click on the best
    option(s)" instructions over an empty frame.
  - **The user's kwarg selection governs display, not just inference**: the
    draft buttons now funnel everything-stored → the user's selection
    (enabled models AND selected `sister_languages`, a macrolanguage counting
    for its members) → the 'top models' boolean, each step selecting only
    WITHIN the previous — 'top models' can never reach past the user's
    selection. Drafts from switched-off models and deselected
    language-directed runs (`(swh!)` keys; detected-language `(en?)` keys
    pass on the model) are hidden, not deleted: they reappear on re-enable.
    Repo matching is by name prefix, since stored keys carry language
    decorations (`facebook/mms-1b-all (swh!)`). With 101 models in play this
    is also the only practical way to exercise the one-button case.
  - **The selection filter works before any model loads**: the kwarg→repo
    mapping and the macrolanguage/alpha-3 helpers moved to module level in
    `backend/asr.py` (`REPO_MODELNAMES`, `sister_members`, `mms_lang`), so
    displaying stored drafts respects the selection even in a session where
    ASR never ran (previously the filter failed open until the first
    `load_ASR()` — e.g. opening the settings window — letting all stored
    languages through).
  - **Output-lane flags no longer masquerade as model selections**:
    `return_ipa` (forced on, no checkbox) and `show_tone` alias the
    neurlang/katyayego repos in `repo_modelnames`; they no longer let a
    deselected model's transcription drafts through the display filter.
  - **FIX — opening ASR settings no longer resets sister languages to "all"**:
    the freshly populated sister-language listbox now restores the SAVED
    subselection (saved == full set, or nothing saved, selects the explicit
    "All of the below" option). Previously the boot-time `save_sister()` found
    nothing selected and its nothing-means-all branch silently replaced the
    saved subselection with the full list.

# Version 1.5.0
- NEW — **three-stage ASR** (record → bulk transcribe → select), so transcription
  cost moves out of the per-word interaction into one unattended batch (ADR 0002,
  docs/asr_bulk_transcription_design.md):
  - **Storage** (`lift.Form.persist_drafts`/`load_drafts`/`wipe_drafts`): ASR
    drafts are annotations on the `<analang>-x-audio` form — `{repo}`,
    `ipa-{repo}`, `tone-{repo}`, `md5`; md5 mismatch (re-record) wipes+redrafts;
    idempotent (re-runs fill gaps). Headless unit test in `tests/test_asr_drafts.py`.
  - **Live path** now writes through `persist_drafts`, so drafts persist even in
    today's fused record→transcribe flow.
  - **Selector (stage 3)** sources from stored drafts, dedups by value (retaining
    `value→[repos]`), orders buttons **most-frequent (consensus) first**, and
    tallies **every** contributing repo on click. A display-time trigger shows the
    stored drafts for an already-recorded word without re-running ASR.
  - **Bulk task (stage 2)** on the **Advanced menu**: a worker-thread,
    model-major/language-major sweep (each model once over all files; MMS switches
    each language's adapter once) with a two-level throttled progress window
    (Wayland-safe), **checkpointing** every ~100 files via the background writer
    (crash/power-cut keeps finished work; resume fills gaps), **gap-fill** (skips
    `(file,model)` already done — adding a model only runs the new one), and
    Cancel/Done → task chooser. Progress denominators reflect what will actually
    run (models × supported languages, minus the top-models filter), not lexicon
    totals.
- NEW — **"top models only"** toggle (context menu, next to Transcription
  settings): limits both bulk and the selector to the most-used model/language
  combos by usage tally (top 5, ties at #5 included, capped 20); off = all.
- **Macrolanguage handling**: a macro sister language (e.g. `swa`) expands to ALL
  its members (`swh`, `swc`) so both are transcribed; the macro's own missing MMS
  adapter is silenced (members cover it); any unsupported language (macro, member,
  or typo) is logged at info and its unit skipped quietly — no per-run nag.
- FIX (core ASR): `is_cached` used a bare `cache_dir` (→ `self.cache_dir`);
  `load_ctc_adaptor` no longer swallows a missing-adapter `OSError` silently;
  **sister-language preflight** validates codes against available MMS adapters;
  sister codes are mapped to ISO 639-3 (`en`→`eng`) so MMS actually loads them.
- FIX (load path): analysis language is now detected from the RECORDINGS
  (`<lang>-x-audio`) when the text forms are only LWC glosses — a recordings-only
  import resolves to the object language, not `en`/`fr`; the database opens with no
  segmental data yet (`checks()` handles an empty check list); `changedatabase`
  no longer crashes when the LIFT chooser closes during setup; a selected
  sister-language **subset now persists** to `audio.json` (the listbox bound raw,
  bypassing the choice-mapping that threw on its empty `choices`).
- FIX (audio/UI): `.m4a`/`.aac` recordings **play** on desktop (decode to a temp
  WAV via ffmpeg at a rate the output card supports); `file_ok` accepts compressed
  audio (WAV size-floor no longer applied to non-WAV); word navigation no longer
  crashes on a 0-byte/corrupt/missing image (`Image` always defines `base_img`,
  `scale()` guards it, `scale_image` falls back to NoImage).
- NEW (tool) — `io_put/lift.clean_lift_file`/`clean_lift_tree`: de-pollute a LIFT
  file — remove EXACT-duplicate sibling nodes (bad-merge artifacts), strip empty
  forms and empty senses (keeping the definition parent), drop a lexical-unit form
  whose lang echoes a gloss/definition lang, and REPORT near-duplicate nodes for
  hand reconciliation. Report-only unless an output path is given.

# Version 1.4.3
- Terminology: the syllable Beg+count+End slice is a **profile class** (DERIVED
  from the three confirmed primitives — not a sorted group-of-groups), renamed
  throughout the syllable code from the overloaded "macrogroup"
  (`compose_profile_class`/`parse_profile_class`/`profile_class_of_sense`/
  `profile_class_prose`/`profile_class_*_name`/`_S_profile_class`/
  `Syllables.profile_class()`/`update_S_profile_class`). Segmental macrogroups
  (= glyphs) keep their name. The profile-class key is now delimiter-free (`C2V`,
  positional parse). See ADR 0003.
- FIX (companion to the slice regression): `SliceDict.profiles()` for cvt 'S' also
  read `_profilesbysense` (confirmed-only), so a profile class of only-unprofiled
  words wasn't enumerated. Now reads the whole ps wordlist, like `senses()`.
- NEW: "Other {profile class} profile" in the syllable profile sort. Instead of
  minting a meaningless integer group (`add_int_group`, which for syllables had no
  resolution step and, if verified, wrote the integer as the word's cvprofile), it
  opens a two-page picker: page 1 lists NEW legal profiles for the class
  (generated simplest-first from the all-length-1 baseline, excluding already-used
  profiles, capped ~12); page 2 ("Other… set by hand") is a free-text field with a
  work-with-a-linguist warning and a Back button. Both validate against the class
  primitives (word-initial/final + syllable count) and sort the word into that
  real, primitive-consistent profile. See ADR 0003 / cv_group_creation_merging.
- Syllable-profile verification consolidated to the `…-x-cvprofile` form as the
  single source of truth. The profile-verify no longer *also* writes redundant
  `lc=<profile>` codes into the `<macrogroup> lc verification` field (that field is
  for segmental checks); verifying/unverifying just sets/clears `…-x-cvprofile`.
- New `rebuild_syllable_profile_done`: the profile board's `done` (the `+` marks) is
  derived from LIFT on SortSyllables open (after `scrub_sorts_to_primitives` +
  `load_ps_profiles`), because `generate_status_by_annotations` skips 'S'. It uses
  the SAME membership+verification model as segmental sorting (ADR 0003): a profile
  group is the set of words with that `lc` annotation (the sort value), and the group
  is `done` iff every member is VERIFIED (its `…-x-cvprofile` matches its annotation).
  Also marks verified profile pairs `distinguished` (distinct cvprofile strings never
  merge).
- FIX (regression from this version's earlier syllable work, ADR 0003): the profile
  board and `done` had been keyed on the `cvprofilevalue` bucket while `maybesort`
  reads `groups` from the `lc` annotation — different keys. A word sorted-but-not-yet-
  verified (annotation=G, `cvprofile` empty) sat in the `'—'` bucket while G stayed in
  `done`, so `maybesort`'s `groups − done` dropped it → "all done" → the sort skipped
  the unverified word. Both `rebuild_syllable_profile_done` and the board's two
  indicators are now on the membership key. The board now follows the shared contract:
  WHITE BORDER = the class has UNSORTED words (presented to sort), `+` = that profile
  is VERIFIED (absence = to-verify) — the same meanings as the segmental board.
- FIX (companion regression, ADR 0003): the syllable slice (`SliceDict.senses` for
  cvt 'S') read `_sensesbyps`, built from `_profilesbysense` — which holds only words
  with a CONFIRMED cvprofile (`getprofileofsense` adds a word only when confirmed). So
  UNPROFILED words — the very ones syllable sorting exists to profile — were excluded
  from the board and from `maybesort`, making a wordlist with unprofiled words look
  entirely "sorted and verified" while `Sort!` just cycled the done macrogroups. 'S'
  now slices the WHOLE ps wordlist (`db.sensesbyps`), bucketed by macrogroup
  (primitives), so unprofiled words appear as unsorted and are presented to sort. (The
  code now matches the intent already documented at `getprofileofsense`.)
- Macrosort eligibility raised: a sort group is macrosortable only when VERIFIED and
  DISTINGUISHED from every verified sibling — via new shared
  `StatusDict.pending_distinctions`, which `to_distinguish` now also uses (fixing its
  latent current-slice keying bug). Stops macrosort from operating on not-yet-joined
  groups.
- Syllable profile board UI: the syllable-count column is now a narrow `Syls` header
  + number (no h-scroll to spare); profiles with <3 examples collapse to a
  `< 3 exs +(N)` / `< 3 exs (N)` summary, toggled by Show/Hide details (which now
  actually re-renders this board).
- The "Set up syllable profiles?" (Trust) window now lists its SCOPE: each affirmable
  word with its `#C/C#/syls` primitives and the profile Trust would assign (machine
  analysis CONSTRAINED to those primitives), or just a count when ≥10 — so the trust
  decision isn't made blind.
- DIAG (temporary): `DIAG-conflict` in `add_glyph_member` to catch a same-slice group
  co-located in one glyph (awaiting reproduction; remove once fixed).

# Version 1.4.2
- FIX ('Not {profile}' escape hatch — decouple from the syllable sort): clicking
  'Not {profile}' during a segmental sort used to (a) risk opening the syllable
  sort ON TOP of the still-running segmental sort, and (b) leave the check in a
  "not done" limbo. Now it DEFERS: it clears the word's confirmed profile + group,
  drops it from the live slice (`slices._profilesbysense[ps][profile]`) and the
  to-sort list (`status._sensestosort`) ad hoc — no per-click `load_ps_profiles`
  rebuild — and advances to the next word (new `_notprofile_advance` flag so
  `sortselected` doesn't read the empty selection as Exit). The missing-profiles
  offer (`offer_profile_setup`) is now the single gate: it fires at task open, on
  finishing a profile, and on 'Sort!', once per batch of newly-unsorted words
  (re-armed by the defer, not once-per-task), and NO LONGER launches the syllable
  task itself — the caller tears down the current task first, THEN opens it, so the
  two boards never coexist. 'Cancel' at the offer now continues sorting the profiled
  words instead of aborting the check.

# Version 1.4.1
- FIX (sort page scrolling): the sort ScrollingFrame snapped back to the top on
  every wheel/scrollbar movement once its content grew past one screen (regressed
  with the v1.4.0 syllable sort redesign). `_do_configure_interior` sized the
  canvas viewport — and, for the hugging sort page, the frame itself — to the
  content's FULL reqheight with no cap, so `yview()` was permanently (0,1):
  nothing lay outside the viewport, so scrolling had nowhere to go and the OS
  window clipped the over-tall canvas. Fixed by capping the viewport height at
  `self.maxheight` while leaving the scrollregion at the full content height, so
  over-tall content scrolls instead of snapping; short content still hugs (the
  v1.3.113 Other/Not-profile/Skip clip fix preserved). Only the sort page set
  `_hug_content`, so no other scroll frame was affected.

# Version 1.4.0
- MILESTONE: **Syllable sort redesign complete.** Verified end-to-end on a real
  lexicon (2026-06-30): a full sort → macrosort → glyph-naming cycle, with sort
  groups staying verified through the cycle (the original groups-invalidated bug
  is resolved in practice). Not bug-free — remaining issues are tracked separately
  (glyph-rename conflict when a default group collides with an existing glyph
  member; the conflict dialog's Retry leaving no UI) — but the redesign itself is
  done. See azt/agenda/syllable_sort_redesign.md.
- FIX (Alphabet word-selection window — chart AND booklet): showed words by
  ORTHOGRAPHY (every word whose spelling contained the glyph), including words not
  actually verified into the group. Now resolves a glyph's VERIFIED members only:
  per `glyph_members` item it confines to that member's slice (ps/profile) and
  keeps senses carrying the `<check>=<group>` verification code (not the sort
  annotation), collated across the glyph's slices (`Alphabet.senses_for_glyph`).
  No orthographic fallback — if nothing resolves, the user is told precisely why
  (no sort data / no members / members unverified / verified-but-no-picture). The
  window also reaches `program` via the root toplevel, so it works from the
  booklet's `PageFrameUI` (which doesn't carry `program`) as well as the chart.
- FIX (Alphabet word-selection window): built blank then painted content slowly on
  XWayland — now builds under a "Loading…" cover and reveals the finished window
  (waitdone update()+deiconify). Added a window title; excluded syllable-prep
  bookkeeping from the "printed examples" notice (see below).
- FIX (Alphabet Chart: PDF no longer opened in the OS viewer): the post-generate
  open used `from utilities import open_file`, but `open_file` lives in
  `utilities/utilities.py` and isn't re-exported by `utilities/__init__.py`, so the
  import raised `ImportError` — swallowed by the surrounding `try/except` as a bare
  `log.warning`. The PDF wrote fine; the open call never ran. Fixed the import to
  `from utilities.utilities import open_file` in `frontend/alphabet_chart.py` and
  `backend/core/alphabet.py`. (Confirmed: PDF reopens in the OS tool.)
- FIX (Alphabet Chart "Printed chart examples" notice): the window had no title and
  dumped the syllable-prep sort bookkeeping. It now has a title (paginated as
  "(n/m)" when it spans multiple windows) and excludes the six syllable-prep keys
  `#C`, `C#`, `syls`, `#C-slice`, `C#-slice`, `syls-slice` from the per-glyph
  annotation display via a new `exclude` predicate on `Sense.annotations_to_update`
  (display-only; stored data untouched). Reuses `params.is_syllable_primitive_check`
  + suffix-strip, matching the board's `_is_syl_prep` filter.
- FIX (ScrollingFrame canvas didn't grow/shrink to re-gridded content — clipped
  rows): added a synchronous `ScrollingFrame.reflow()` (`update_idletasks()` →
  `_do_configure_interior()`) and routed every dynamic content-add site through it,
  so the canvas + scrollregion track the new content instead of relying on the
  debounced `<Configure>` reflow the canvas can starve. The `update_idletasks()` is
  required: grid()/grid_forget() defer the requested-size recompute, so reading it
  without flushing reflowed to the stale size (observed: alphabet-chart +/- columns
  and show-all/pictured-only didn't resize). Sites fixed: alphabet chart
  (reflow_chart/show_chart/select_example), alphabet comparison (image grid,
  +2-pages booklet), tone-frame drafter (status/exemplified), JoinUFgroups rows,
  sound record-button pages + example recordings, sound transcription labels + card
  settings, glyph leaderboard, and the error-log window. Webview `ScrollingFrame`
  stub got a no-op `reflow()` for backend safety. See scrollframe-reflow-viewport-trap.

# Version 1.3.115
- FIX (Alphabet Chart / Comparison: redundant task page that quit AZT on close):
  `AlphabetChart` and `AlphabetComparisonPages` inherited `Task`, whose `__init__`
  builds a generic `TaskWindow` and makes it the app main window
  (`TaskDressing.__init__`→`i_am_mainwindow`). But each task's real UI is its OWN
  window (`OrderAlphabetUI` / `PageSetupUI`), so a pointless second "main page"
  appeared and closing it propagated `on_quit(to_root=True)` → quit AZT. (The old
  `self.mainwindow = False` was dead: `on_quit` checks `ismainwindow`.) Dropped
  `Task` from both — the config window IS the task now (matching the original
  design). Each registers itself as `program.task` with `self.ui = self`, hides
  the chooser while open, and binds the window-close to `taskchooser.gettask` so
  closing returns to the chooser exactly like the Tasks/Reports button instead of
  quitting. They use nothing else from `Task` (the chart UI/back end never call
  `self.ui.*`; the chooser only reads `tasktitle`/`taskicon`).
- FIX (Alphabet Comparison crashed on open: `NameError: name '_' is not defined`):
  `frontend/alphabet_comparison.py` used the `_()` translator without importing
  it. Added `from utilities.i18n import _` (the suite-wide convention).

# Version 1.3.114
- FIX (correspondence checks were wrongly offered for sorting): `V1xV2`/`C1xC2`
  (and the other `x` correspondence checks) are a REPORTING construct — the
  cross-tab chart, which the report builds by crossing the single-axis V1/V2
  groups (`generator.docheckreport`). They are not something to ask the user to
  sort/verify by; offering them produced a nonsensical `NA` pile (e.g. 69
  two-vowel words parked as "NOT Correspondence of First Two Vowels", when
  correspondence applies to anything with two vowels). The filter that drops them
  already existed in `StatusDict.checks()` but its trigger had been commented out
  (the old `isinstance(self.task(),Sort)`) and replaced by a `no_correspondence_checks`
  kwarg that nothing passed. Re-armed it with the flag-based equivalent: when the
  live task is a sort task (`getattr(self.task(),'is_sort_task',False)`), drop `x`
  checks. Gated on the SORT task, NOT on "is a report", because reports run with
  `status.task()` unset (None) in a subprocess and must keep the `x` checks for the
  chart. Check NAMES (analysis_inputs) are unchanged — the report still needs them.
- FIX (status frame showed "working on First Vowel None"): `cvgrouplabel()`
  returned a bare `None` for x-checks / no check, and `updatecvgroup()` does
  `StringVar.set(that)` — `set(None)` renders the literal "None". When the sort
  stepped through an `x`-check the group label was set to "None" and went stale
  when it advanced to a single-axis check (V1), so a None group (= all groups)
  read as "None". Return '' instead; a real None group still reads "(All groups)".

# Version 1.3.113
- FIX (sort page clips lower rows when a group button is added mid-sort): the
  scroll content self-heals through the content frame's `<Configure>` binding →
  `ScrollingFrame._do_configure_interior`, which resized the canvas + scrollregion
  but never the scroll frame's OWN height. Only `SortButtonFrame.reflow()` set
  that, and it ran once per item in `presenttosort`. So when a new group button
  appeared during sorting (user picks "Other", a new group is created +
  `addgroupbutton`) — or when a group's example image loaded *after* that one-shot
  reflow — the content grew, the canvas/scrollregion grew, but the frame (frozen
  by `grid_propagate(0)`) stayed short and pushed Other/Not-profile/Skip off the
  viewport. Moved the content-hug into `_do_configure_interior`, gated by a new
  per-instance `_hug_content` flag that `SortButtonFrame` sets for the sort
  (item-at-a-time) page only — so every reflow path (including the `<Configure>`
  one) keeps the viewport hugging its buttons, while the macrosort verify list
  (`remove_on_click`) keeps its fixed scrolling viewport.

# Version 1.3.112
- FIX (sort page scroll frame sized right): v1.3.111 gave the scroll frame grid
  weight, which made it FILL the window (a 2-3 button page had a big empty scroll
  area). Reverted that; instead `SortButtonFrame.reflow()` sets the scroll frame's
  OWN height to the content's `reqheight` (it has `grid_propagate(0)`), so the
  viewport HUGS the buttons — not frozen-too-small (clip) and not window-filling.
  If content ever exceeds the window, the grid cell caps it and the scrollregion
  handles scrolling.

# Version 1.3.111
- FIX (sort page clip — the actual cause): the v1.3.110 `DIAG-reflow` showed the
  reflow now sizes content + scrollregion correctly (→472), but the **canvas
  viewport stayed 347** — the scroll frame (`buttonframe`) is gridded into
  `groupsFrame` row 1 with no row weight and has `grid_propagate(0)`, so its cell
  stayed frozen at an early/partial height and the viewport couldn't grow into the
  empty window space below (buttons past 347 clipped, matching "scroll window grows
  but canvas doesn't"). `build_sort_layout` now sets `groupsFrame` row-1 + column-0
  weight so the scroll frame fills the available space and the buttons show. Removed
  the `DIAG-reflow` instrumentation; kept `SortButtonFrame.reflow()` +
  `presenttosort`'s synchronous call (they correctly size content/scrollregion).

# Version 1.3.110
- DIAG (sort page clip persists, no behavior change): the 1.3.108/109 reflows still
  leave later rows clipped — and the canvas/scrollregion (not the content frame) is
  the clamp (scroll frame grows, canvas doesn't). `SortButtonFrame.reflow()` now logs
  `DIAG-reflow` before/after `_do_configure_interior`: target object, suspend state,
  content `h`/`reqh`, canvas height, and scrollregion — to show whether the reflow
  runs with a stale `reqheight` or fails to expand the canvas/scrollregion.

# Version 1.3.109
- FIX (sort page: skip/"Other"/"Not-profile" rows still clipped & unscrollable):
  the v1.3.108 reflow was DEFERRED (re-armed `_configure_interior`) and could be
  consumed mid-build with a partial height (during a slow example-image load),
  before the later rows were counted — so the content still clamped short. Added
  `SortButtonFrame.reflow()` (synchronous `_do_configure_interior`) and call it from
  `presenttosort` right after the run window's `update()`, when the full geometry is
  settled, so the content sizes to its true `reqheight`. (Confirmed it's not just
  below-the-fold: content was clipped above an empty strip with a full-height
  scrollbar = clamped, not scrollable.)

# Version 1.3.108
- FIX (sort page: 2nd+ group button + skip/OK clipped & unscrollable): the scroll
  content is a canvas-embedded frame whose reflow is driven by its `<Configure>`.
  When a reflow runs MID-BUILD (the event loop pumped during a slow example load for
  a later group — here the ~2 s compound `V1=V2` regex/image), it pins the content
  window to the partial height; subsequent buttons grow the REQUESTED height but not
  the pinned actual height, so `<Configure>` never re-fires and the content stays
  clamped to the first button (later buttons + skip clipped, and unscrollable since
  the scroll region was computed at the partial size too). `SortButtonFrame` now
  re-arms one reflow after all buttons + skip are built (flushed by the run window's
  `update()`), mirroring the verify page's `resume_configure`. Diagnosed via the
  v1.3.107 `DIAG-sortbtn` dump (`content h=126, reqh=472`), now removed. Why it
  didn't bite before: fast builds reflow only after everything's in, and the verify
  page already batches with suspend/resume — only a slow mid-build pump triggers it.

# Version 1.3.107
- DIAG (sort page partial render, no behavior change): the v1.3.106 drained `update()`
  did NOT fix the missing 2nd group button + skip/OK, so it's layout, not paint-flush.
  Added a temporary `DIAG-sortbtn` dump in `presenttosort` logging each group
  button's mapped state + geometry, the skip frame's, and the scroll content height —
  to tell apart not-built / zero-size / unmapped / off-screen / scrollregion-clip.

# Version 1.3.106
- FIX (sort page partial render: 2nd group button + skip/OK don't draw, sort
  un-completable): `presenttosort` revealed the run window with `update_idletasks()`,
  which on XWayland leaves the just-mapped window's paint/`<Configure>` backlog
  un-flushed — so later group buttons and the skip/OK row didn't paint and the
  scroll region could stay stale and clip them. Switched to a drained `update()`
  (wrapped, like the verify page's `build_verify_layout` commit), which processes the
  backlog so the whole page paints. Not new wedge-chasing — it applies the existing
  verify-page render fix to the sort page, which had been missed.

# Version 1.3.105
- FIX (`KeyError: '#C'` crash on form update after sorting): `updateformtoannotations`
  (lexicon.py) iterated EVERY annotation and fed each to `rxdict.update`, including
  the syllable-prep primitives (`#C`, `C#`, `syls`) and the profile check (`lc`),
  which have no position regex in `rxdict.rx` → `self.rx['#C']` KeyError, killing
  `updateformsallchecks` mid-generator (seen via the macrosort form-update pass).
  Form updates apply only to SEGMENTAL checks; `do_not_do_these` now skips any check
  whose `=`-parts aren't all present in `rxdict.rx`.

# Version 1.3.104
- FIX ("go back and join" offered no pair to join): after the user intentionally
  un-distinguished a glyph to join it, `maybesort` immediately called
  `predistinguish`, which re-distinguishes "trivially distinct" single-member glyph
  pairs (deciding off the SORT-GROUP-level `status.isdistinguished`, which the
  glyph-level un-distinguish doesn't clear) — so the very pair the user asked to join
  was dropped from the join page. Now a one-shot `_skip_predistinguish_once` flag,
  set by both go-back paths (`name_new_glyphs` go-back and `redo_joinglyphs`), makes
  `maybesort` skip `predistinguish` for that single pass. Normal runs still
  predistinguish as before. (Two paths: predistinguish on normal run; don't when we
  just intentionally un-distinguished.)

# Version 1.3.103
- FIX (groups-unverified root cause): the segmental sort slice (`_profilesbysense`,
  via `getprofileofsense`) was built from the MACHINE analysis constrained to
  primitives, while the status slice (`sensesbyps_profile`/`verified_groups`) used the
  confirmed `cvprofile` data form — two indices that disagreed, so a word could be
  sorted in CVC but invisible to verification. Now `getprofileofsense` files each
  sense under its **confirmed `cvprofile` …-x-cvprofile form** (the trusted profile),
  matching the status slice. A word with no confirmed profile is left OUT of segmental
  slicing (it still gets syllable-prep'd to acquire one).
- NEW (on every load): `ProfileAnalyzer.scrub_sorts_to_primitives()` enforces the
  sort/verification distinction: (1) never auto-adds a missing `lc` profile-sort
  annotation; (2) constrains an ILLEGAL `lc` annotation to the confirmed primitives
  and rewrites it (the sort must be legal); (3) if the now-legal sort no longer
  matches the confirmed `cvprofile` form, CLEARS that cvprofile verification (the word
  drops out of segmental sorting → the profile-setup trigger fires for manual/trust
  re-set). The `'<profile> lc verification'` segmental fields (context-tagged by
  profile) are untouched. Self-healing and a no-op once data is consistent.
- FIX ("Go back and join" on the New Letter page did nothing → "not done" warning):
  the inline `name_new_glyphs` built `GlyphTranscribeHelper` with no `on_go_back`, so
  the button just closed the window. Now wires it: the flagged glyph is
  un-distinguished and `name_new_glyphs` returns True so `warnorcontinue` restarts
  `maybesort` onto the join-glyphs step (which precedes naming) — same effect as
  `redo_joinglyphs`, without a nested `maybesort`.

# Version 1.3.102
- FIX (New Letter page stuck on "Give a name!"): regression in `EntryField.__init__`
  (ui_tkinter.py). `reserve_kwargs` pops the caller's `textvariable` into
  `self.textvariable`, but the next line re-defaulted from `kwargs` (now empty) and
  always injected a THROWAWAY `StringVar`; `TextBase.__init__` then adopted the
  throwaway, so the visible Entry bound to it instead of the caller's var. Typing
  updated the throwaway, the caller's write-trace never fired, and `GlyphTranscribe`'s
  `updateform` never re-ran — leaving OK greyed with "Give a name!" even with text in
  the field. Now re-injects `self.textvariable` (the caller's var), defaulting to a
  fresh one only when none was passed. (This is the same class of bug the in-code
  comment at EntryField says was fixed before; it had regressed.)

# Version 1.3.101
- DIAG (groups-unverified, no behavior change): widened the `DIAG-done write` line
  (sorting_engine.updatestatuslift) to fire for EVERY verify write, not just
  digit-named groups, and to log the group NAME + its python TYPE, the profile, and
  the add/remove values. Reason: in the 2026-06-27 reload-only log, `grep DIAG-done
  write` and `grep update REMOVE` were both empty — so nothing was explicitly
  un-verified (poss. 4b out), and no integer-group code was written there. The empty
  write grep also hints the verified group may not be digit-named at write time
  (glyph/int name flip), which the old isdigit() gate hid. Now any verify is
  captured with its exact name/type/targets.

# Version 1.3.100
- DIAG (groups-unverified, no behavior change): exhaustive `DIAG-done` tracing of the
  full verify→done lifecycle for INTEGER (still-unnamed) groups in the active ps, to
  decide between the four possibilities for why a verified group ('2'/'3') reads as
  unverified. One `grep DIAG-done` now covers all four:
  - **write** (`updatestatuslift`, sorting_engine.py): `DIAG-done write check=g ->
    coding N/M inslice senses: [...] (full group [...])` — exactly which senses got
    the code written (poss. 1 root: was it ever written, or did
    getsensesincheckgroup/inslice miss members?).
  - **read** (`verified_groups_by_ps_profile`, io_put/lift.py): `DIAG-done read
    ps/profile check=g verified=? test='check=g' members=[(id, codes, present?), …]`
    — every member's LIFT verification codes + the exact membership test. Tells
    "no code in LIFT" (poss. 1) from "code present but == misses it" (poss. 2).
  - **build** (`generate_status_by_annotations`, settings/__init__.py): `DIAG-done
    full-reload SET … done=… verified=… groups=… NOT-done=… verified-but-not-in-
    groups=…` — whether a read-verified group is dropped by `verified ∩ groups`
    (poss. 3).
  - **remove** (`cull` DROP, `update` REMOVE, analysis.py) — already in place (poss.
    4); plus a `status.group` NON-STR tripwire.
  Groups are tiny (≈3 and ≈8 words) so member lists are dumped in full. Strip all
  `DIAG-done`/`DIAG-join-verify` once the cause is fixed.

# Version 1.3.99
- FIX (groups-unverified, str/int group hazard): `getsensesingroup` — the member
  lookup the VERIFY uses to write `<check>=<group>` codes — compared the LIFT
  annotation (always a str) to the raw `group` with no str cast, in all three
  variants (Segments lexicon.py:413, Tone :1813, Syllables :1851). The sibling
  example/display path (`analysis.py:217`) and the glyph path (`alphabet.py:412`)
  already cast `str(group)` with explicit "in case an int() group gets through"
  comments — so integer groups are known to leak. If a default integer group (e.g.
  '3') reached the verify as an int, `"3"==3` is False → the verify coded ZERO
  members → the macrosort transition's full reload
  (`renew_items_tomacrosort`→`refresh_items`→`reloadstatusdata`) then recomputed the
  group as NOT verified, re-asking the user to verify it. Now all three lookups cast
  `str(group)`, matching the guarded siblings.
- DIAG (temporary): tripwire at the `status.group` setter logs `DIAG-done group()
  set to NON-STR` if a non-str/non-None group is ever assigned, to confirm on the
  next repro whether ints actually leak into the group channel (and from where).

# Version 1.3.98
- DIAG (groups-unverified, no behavior change): added three tagged `DIAG-done` log
  lines at the ONLY three places the per-check `done` list can shrink, to pinpoint
  where verified integer groups (e.g. V1 '2'/'3') lose their done status during an
  unrelated macrosort glyph-verify cycle:
  - `StatusDict.update` — explicit un-verify (`verified=False` removal).
  - `StatusDict.cull` — groups intersected out of done (done entry with no group).
  - `generate_status_by_annotations` — the FULL reload recomputing done from LIFT
    per (ps,profile,check).
  NOTE: `verified_groups_by_ps_profile` is correctly **per-(ps,profile) slice** —
  it requires every member of a group to be coded *within that slice only*, with no
  cross-slice dependency (groups in different slices relate only via a shared
  glyph). `updatestatuslift`'s `slices.inslice` write is at the same granularity, so
  the drop is NOT a cross-profile coding gap. Within one slice, a group leaves
  `done` only if (a) a member was sorted in / re-annotated so its annotation puts it
  in the group but it carries no `<check>=<group>` code, (b) an explicit
  `update(verified=False)`, or (c) the cull (but the repro had '2','3' still in
  `groups`, ruling cull out). The DIAG lines name which on the next repro before any
  fix lands. See groups-invalidated-after-join note.

# Version 1.3.97
- FIX (run-window-never-deiconifies, 3rd recurrence of this class): a kiosk run
  window created withdrawn by `getrunwindow()` is only revealed if something later
  (a) calls `runwindow.wait(..., thenshow=True)` — which only `getrunwindow(msg=...)`
  does — or (b) calls `runwindow.deiconify()` explicitly. Reveal-via-`waitdone()`
  silently no-ops when the underlying wait is inactive or was opened on a withdrawn
  parent (`showafterwait` is False). Fixed three sites:
  - **macrosort (letter-group) verify** (`sort_ui.build_verify_layout`): relied on
    `runwindow.waitdone()`, but `SortButtonFrame` builds behind its own
    `with task.waiting()` opened on the withdrawn TaskWindow, so that wait is gone
    (and never targeted the run window) by the time we reach the reveal. Now
    deiconifies explicitly, matching the sort path (`presenttosort`).
  - **`name_new_glyphs` / glyph rename** (`transcribe_glyph.makewindow`):
    `getrunwindow(title=…)` with no msg, no wait opened during the build, and the
    upstream reload-wait already closed — so `waitdone()` was a no-op and the page
    stayed hidden while `wait_window()` blocked on it. Now deiconifies explicitly.
  - **ad-hoc/search report** (`generator.getresults`): `getrunwindow()` (no msg)
    then `runwindow.wait()` without `thenshow` → `showafterwait` False → the results
    window never showed. Now passes `thenshow=True` so `waitdone()` reveals it.

# Version 1.3.96
- "Trust" (affirm) now also runs `reconcile_profiles_to_primitives` — so taking
  the trust action both fills holes (affirm) and repairs existing trusted
  profiles (constrains primitive-violating ones and realigns drifted `lc`
  annotations). Idempotent on clean data.
- KNOWN ISSUE (deferred): groups are still being invalidated/unverified beyond
  what the join fix addressed. To be investigated after a clean re-sort; see the
  groups-invalidated note. Prime suspect: the per-slice reload
  (`reloadstatusdatabycvtpsprofile`) deriving group names differently than the
  full reload (`generate_status_by_annotations`) — earlier DIAG showed group
  names flipping glyph (ɩ/ɑj) ↔ integer (2/3) between post-cull and maybesort,
  dropping verified groups. `DIAG-join-verify` instrumentation left in place.

# Version 1.3.95
- Affirm/reconcile now keep the profile-sort annotation aligned with the trusted
  profile. Writing the plain …-x-cvprofile alone left the `lc` annotation showing
  the old machine value (e.g. plain `CCVC` but `lc`=`CCVCV`) — which misreads as
  "last sorted into CCVCV" and would trip the normal group/done unverify. New
  `_set_trusted_profile` writes BOTH the plain DATA and the `name=ftype` ('lc')
  annotation together, used by affirm and reconcile. `reconcile` also now repairs
  annotation drift even when the plain profile is already correct (so it fixes
  knife's stale `lc`=`CCVCV` left by the old raw affirm, which only touched the
  plain form).

# Version 1.3.94
- Principled human-vs-machine form selection via a `machine` kwarg, replacing the
  1.3.91 point-fix. `machine` now threads `fieldvalue → textvaluebylang →
  getlang`, and `getlang` resolves tone/cvprofile form-langs from
  `(analang, machine)` via `tonelangname`/`profilelang` — moved AHEAD of the
  single-form short-circuit, so the lang is determined by intent, never by
  whichever form happens to exist. This structurally kills the cvprofile
  plain-vs-`_MT` bug (a missing plain form no longer makes a plain read return the
  machine value) and sets tone up the same way for human-vs-machine transcription.
  `cvprofilevalue(…, machine=False)` is now the single reader; `cvprofilemachine
  value` and the tone readers (`uftonevalue`, `Example.tonevalue`) are thin
  pass-throughs of `machine`. Supersedes the 1.3.91 explicit lang-pin and the
  1.3.93 single-form docstrings for cvprofile/tone.

# Version 1.3.93
- Docstrings: marked `cvprofileuservalue` as UNUSED, and annotated every no-lang
  `fieldvalue` caller that's currently safe only because its field is single-form
  (`locationvalue`, `Example.tonevalue`, `uftonevalue`, `verificationtextvalue`)
  with a note to pin the lang if that field ever gains a second form-lang — so
  the cvprofile-style "wrong form returned" trap is noticed before it bites.

# Version 1.3.92
- Fixed `uftonevalue` never persisting a set: it called `fieldvalue('tone',value)`,
  passing `value` positionally into the `lang` parameter — so a write was treated
  as a lang lookup and the value was never stored. Now passes `value=value` (tone
  is single-form, so no lang needed).

# Version 1.3.91
- Fixed `cvprofilevalue` leaking the machine value. It called `fieldvalue` with
  NO lang; `fieldvalue→getlang` then falls back to the field's single remaining
  form. Since `cvprofile_lc` now carries TWO forms (plain `…-x-cvprofile` +
  machine `…-x-cvprofile_MT`), a word with only the `_MT` form (no confirmed
  profile) had `cvprofilevalue()` return the MACHINE value — so unprofiled words
  looked profiled: the "set up profiles?" trigger never fired for them, affirm's
  `!= m` guard skipped them, and segmental/tone sorts read raw machine as
  confirmed. `cvprofilevalue` now pins the plain lang (`profilelang(analang)`),
  mirroring `cvprofilemachinevalue`. (This is why deleting the plain form by hand
  didn't re-arm the trigger — the lone `_MT` form was answered instead.)

# Version 1.3.90
- Affirm now FILLS HOLES ONLY: it skips any sense that already has a plain
  profile, so it can never clobber hand-verified good data (previously it
  rewrote any sense whose profile differed from the constrained machine value).
- Added `ProfileAnalyzer.reconcile_profiles_to_primitives()` — the deliberate
  repair path that DOES touch existing profiles, but only to constrain ones that
  *violate* their verified #C/C#/syls (a no-op on already-consistent profiles, so
  good data is untouched). Use it once to clean up the bad profiles the old
  raw-copy affirm wrote (e.g. `CCVCV` on a C#=C/syls=1 word → `CCVC`). Not yet
  wired to a menu/trigger — invocation TBD with the user.

# Version 1.3.89
- "Use the machine analysis as profiles" (affirm) now RESPECTS verified syllable
  sorting. It copied the raw `…-x-cvprofile_MT` into the plain form, overriding a
  partly-done syllable sort — e.g. machine `CCVCV` (2 syls, V-final) on a word
  already verified `C#=C, syls=1`, leaving a plain profile that conflicts with the
  primitives AND with how the presort/SliceDict already groups the word (`CCVC`).
  Affirm now writes `constrain_presort_profile(...)` — the machine profile
  reconciled to the word's confirmed `#C/C#/syls` (no verified primitives → no-op
  → raw machine, as before). NOTE: this corrects FUTURE affirms; words already
  affirmed to a conflicting profile aren't auto-repaired (affirm won't re-trigger
  once they have a profile) — a one-time reconcile sweep can be added if wanted.

# Version 1.3.88
- `DIAG-join-verify NOTDONE` logging is now scoped to the CURRENT ps (passed as
  `log_ps` from `generate_status_by_annotations`). Other parts of speech are
  uncoded simply because no work has happened there, so they flooded the log with
  irrelevant empty-code lines (which also misled the earlier diagnosis). The
  `done`-from-LIFT computation still covers all ps; only the log is scoped.

# Version 1.3.87
- Fixed the greedy unverify behind "joining one group unverifies another".
  `updatestatuslift` computed `senses` via `getsensesincheckgroup()` with NO
  args, so it always targeted the CURRENT `status.group()` — ignoring the
  `check`/`group` it was actually told to (un)verify. So join's
  `updatestatus(group=lpr[1], verified=False)` stripped the `check=*` verification
  code off whatever group happened to be current (an unrelated, already-verified
  group) instead of the joined one. Now passes `check`/`group` through, so it
  (un)verifies exactly the intended group. (Normal verify is unchanged: there the
  intended group already IS the current one.) This bug had been stripping the
  verification code off an unrelated group on every join — the source of "join
  unverifies y."

# Version 1.3.86
- Fixed macrosort crash `AttributeError: 'ScrollingFrame' object has no attribute
  'updatecounts'`. In `sortselected`, the macrosort `recurring_conflicts` branch
  calls `sort_on_group_by_item`, which redirects via a nested `runcheck`/
  `maybesort` that rebuilds the display — then returned None, so the outer
  `sort()` loop kept going and called `updatecounts()` on the stale buttonframe
  the rebuild left behind. It now returns truthy so the outer loop bails (its
  `if r: return`), matching the other restart paths.
- Broadened the `DIAG-join-verify` diagnostic from PARTIAL-only to NOTDONE (any
  group with members not fully coded), logging the uncoded members and the codes
  they carry — to distinguish a real data gap from a code-on-wrong-member
  scramble. (Empty `grep PARTIAL` showed the dropping groups are FULLY uncoded.)

# Version 1.3.85
- TEMPORARY diagnostic: `verified_groups_by_ps_profile` now logs `DIAG-join-verify
  … PARTIAL` for any group whose members are split (some carry the
  `<check>=<group>` code, some don't) — naming the uncoded sense ids and the codes
  they DO carry. Pinpoints whether a group dropping out of `done` is correct (a
  word sorted in after verify, or codes on the wrong members) or a recompute bug.
  To be removed with the rest of the `DIAG-join-verify` instrumentation.

# Version 1.3.84
- Fix: a join no longer leaves *unrelated* groups needing re-verification. Root
  cause: `done` (group verified as a whole) was a cached value in the status
  file, and the full reload a join triggers mishandled it. `done` is now COMPUTED
  from LIFT on reload (option A): a group is verified iff it has members and every
  member carries its `<check>=<group>` verification code — exactly what a
  group-verify writes and a plain sort omits. New `db.verified_groups_by_ps_profile`;
  `generate_status_by_annotations` sets each segmental (V/C) node's `done` from it.
  Self-healing, so verified state can't go stale. Scope: segmental only —
  syllable-prep ('S') `done` is per-slice and left to the prep driver; tone still
  uses the cached `done` (its membership isn't in the 'lc' annotations this reads).
- Note: `done` is still cached in the status file and loaded at boot (consistent,
  since it's written alongside the LIFT codes); fully dropping it from the file
  (the "file holds only `distinguished`" endpoint) is a follow-up.

# Version 1.3.83
- TEMPORARY diagnostic logging (`DIAG-join-verify`) to trace how a group's
  verified (`done`) state moves through a join: logged at join start, after the
  reload (pre-cull, in updatebygroupsense), post-cull (join_pair_done), and where
  maybesort computes groups-to-verify. For diagnosing groups becoming unverified
  after an unrelated join. To be removed once the `done`-from-LIFT fix lands.

# Version 1.3.82
- Join page never appeared (and the app wedged in wait_window): `getrunwindow`
  creates the kiosk run window WITHDRAWN, and `join` only called `waitdone()` —
  a no-op when no wait dialog was active (its getrunwindow had no msg) — with the
  actual `deiconify()` commented out. So `wait_window` blocked on a window the
  user could never see or dismiss. `join` now reveals the run window each pair
  (waitdone → deiconify → update_idletasks), mirroring sort's `presenttosort`.

# Version 1.3.81
- The "set up profiles?" trigger now counts only words that affirming/sorting
  could actually profile: no confirmed profile yet AND a real (non-Invalid,
  non-empty) machine analysis to affirm. Words with no/Invalid machine analysis
  can never be affirmed, so they no longer keep the prompt alive forever — once
  "Trust" is taken (and now persisted, 1.3.80), the prompt is fully silenced.
  Trade-off: those few unprofilable words will silently not be sorted.

# Version 1.3.80
- "Use the machine analysis as profiles" (affirm) now PERSISTS: it set each
  sense's plain …-x-cvprofile in memory but never wrote the LIFT, so a restart
  re-read the file without the profiles and the "set up profiles?" trigger fired
  again. `affirm_machine_profiles` now calls `maybewrite(definitely=True)` after
  copying the machine forms. (Words with no/Invalid machine analysis still can't
  be affirmed — nothing to copy — so any such words remain unprofiled.)

# Version 1.3.79
- Real fix for the segment-board blank rows: the board was showing the syllable-
  PREP checks (#C/C#/syls, stored with a '-slice' suffix by older builds) as
  columns. A profile that has been syllable-sorted carries those nodes WITH
  groups but has no segmental data, so it drew a row of empty (irrelevant)
  columns. `makeprogresstable` now drops syllable-prep checks from a
  segmental/tone board's columns, and `hasboarddata` only counts data in checks
  the board actually shows (`self.checks`) — so a profile that's only been
  syllable-sorted no longer appears. (Supersedes the 1.3.75/76 heuristic, which
  counted those leftover groups as data.)

# Version 1.3.78
- "Set up syllable profiles?" window now builds withdrawn and is deiconified once
  composed (update_idletasks → deiconify → lift), instead of mapping empty and
  reflowing — fixes the slow/mis-placed appearance.

# Version 1.3.77
- NA ("not applicable") is no longer offered as a selectable group: the group
  picker (`_getgroup`) filtered every other surface but listed NA as a button.
  NA stays in the grouping/verification machinery but is never presented AS a
  group — not in the picker buttons, the sort-into buttons (already filtered),
  or the status board (1.3.75/1.3.76). NA collects words from two sources: the
  presort remainder of an `=` check (e.g. a V1≠V2 word under a V1=V2 check) and
  user-skipped items (taboo/unknown/etc., any check). It is verified exactly
  ONCE, explicitly, in the presort (`lexicon.py:177–179`) — where the pile is
  offered for removal → resort and then marked needn't-redo — and is NOT returned
  by the normal verify loop (`groups(toverify=True)`).

# Version 1.3.76
- Segment progress board: dropped the "always show the current profile" carve-out
  from 1.3.75 — no row is shown for a profile with no real data, period; it
  appears once it has a real (non-NA) group. (`NA` is the presort's
  unmatched/unsorted remainder bucket — and also where user "skip" files a word —
  so an NA-only profile has nothing sorted.) Made the current-profile cell
  highlight defensive (`_cells.get`) so an unlisted current profile no longer
  KeyErrors.

# Version 1.3.75
- Fixed `NameError: name 'Options' is not defined` crashing the Segment
  Interpretation page (`setSdistinctions`). `Options` (the grid-position helper)
  was stranded in `main.py` after the method was refactored into `ui_shell.py`,
  which can't import from `main` (circular). Moved it to `utilities/utilities.py`
  (alongside `Object`), where `ui_shell` already gets it via `import *`.
- Segment progress board no longer shows empty rows: a profile is listed only if
  it has real sorted/verified data (a non-NA group, or a verified group) in some
  check — profiles holding only NA / to-sort placeholders (which render as blank
  cells) are skipped. The current profile is always shown so the user can see
  where they are. (Complements 1.3.73's cull, which drops member-less profile
  nodes; this hides member-ful but as-yet-unworked ones from the board.)

# Version 1.3.74
- Syllable-profile offer is now resolved BEFORE the segmental/tone sort board
  appears, instead of popping over it. On a normal open, SortS/SortV/SortC/SortT
  stay withdrawn until the "Set up syllable profiles?" prompt is answered; the
  board is only deiconified once the user affirms / cancels / has profiles
  already. If the user chooses "Sort syllable profiles first," that task opens
  and this still-hidden board is torn down (new `TaskBase._dismiss_unshown`)
  rather than left behind the new task. Resume re-entries (redo_glyph /
  sort_immediately) are unaffected — they show immediately as before.

# Version 1.3.73
- Turned `PROFILE_CONSTRAINT['force_resort']` OFF (testing flag; also inert since
  the plain-form flip).
- `StatusDict.cull` now also drops a profile status node when NO sense currently
  carries that profile (membership of any kind — not "sorted"/"verified"), so the
  residue force_resort/the constraint wrote for machine-computed profiles is swept
  out of data.json as normal maintenance (cull runs from maybeboard). Scoped to
  segmental cvts (profile = CV profile, tracked in `db.ps_profiles`); 'S'
  macrogroups/sentinels and not-yet-computed ps are left alone.

# Version 1.3.72
- Design docs for the record → bulk-ASR → select rework: ADR 0002 (storage
  schema — ASR drafts as repo-keyed annotations on the -x-audio form, md5
  staleness) and docs/asr_bulk_transcription_design.md (three-stage
  architecture, two-pathway loop, CPU timing ~11 h/1700 files × 20 langs,
  phased plan). No code changes.

# Version 1.3.71
- Segment status board no longer shows empty/no-data rows: it now lists only
  profiles present in `db.ps_profiles` (confirmed/affirmed, empty-excluded),
  rather than every machine-computed profile from `slices.profiles()` — which is
  where force_resort/machine residue was coming through.
- The affirm/sort warning now fires when the segmental/tone sort page OPENS (via
  `after()` in SortS/SortT `__init__`), not only on 'Sort!' — `offer_profile_setup`
  returns the choice (and refreshes the board on affirm); the runcheck call is now
  just a guarded fallback.

# Version 1.3.70 (superseded within this session — see 1.3.71)
- Fixed the segment status board listing no-data profiles after the plain-form
  flip: `slicebyps_profile`/`get_ps_profiles` now exclude empty/Invalid profiles,
  so only profiles that actually have confirmed/affirmed data are sliced and
  listed (words with no profile yet aren't bucketed under an empty profile).
- Fixed the affirm/sort trigger not firing: it now fires when ANY word in the ps
  lacks a profile (not only when there are none at all), asked once per task open
  — so opening a segmental/tone sort with unfinished profiles offers affirm /
  go-to-SortSyllables / cancel.

# Version 1.3.69
- Moved the "Not {profile}" escape hatch from under the word into the CHOICE list
  on the one-word sort page — after "Other {check}", before "Skip this item"
  (`getanotherskip`). Unverifies the presented word's CV profile and advances;
  `unverify_profile` now also rebuilds the ps-profile slices so the word drops out.
  Segmental/tone profile sorts only (the syllable Task-2 keeps its macrogroup escape).

# Version 1.3.68
- "Not {profile}" escape hatch on the one-word sort page: a button that unverifies
  the presented word's CV profile (clears the plain …-x-cvprofile and the profile
  sort-group annotation) and advances, so a misplaced word drops out of its
  presorted profile and is re-derived on the next presort. (`_reject_profile` /
  `unverify_profile`; button added in `build_present_sense`.)
- Trigger when a segmental/tone sort opens with no syllable-profile data for the
  ps: offers "Use the machine analysis as profiles" (→ affirm_machine_profiles),
  "Sort syllable profiles first" (→ open SortSyllables), or Cancel — with a note
  that words lacking a syllable profile won't be sorted for anything else either.
  (`Sort._maybe_offer_profile_setup` + `sort_ui.offer_profile_setup`.)

# Version 1.3.67
- Flipped the plain …-x-cvprofile form to confirmed/affirmed-ONLY: `getprofileofsense`
  no longer auto-seeds it from the machine guess. It's the profile DATA the
  segmental/tone sorts read, and is now written only by a syllable-profile verify
  or by `affirm_machine_profiles`. (force_resort no longer affects it — now inert.)
- Wired the syllable-profile verify to the plain form: `updatestatuslift`, when the
  check is the ftype (the profile sort, not a #C/C#/syls primitive), sets each
  verified word's plain …-x-cvprofile to its CV profile group, and clears it on
  unverify — so confirmed profiles populate the data segmental reads, and an
  unverify ('Not {profile}', coming next) removes it.

# Version 1.3.66
- `…-x-cvprofile_MT` now holds the STRAIGHT machine CV analysis, irrespective of
  constraints (per the agreed model): `getprofileofsense` stores the raw profile
  in `_MT` and keeps the constrained value only for the presort/data form.
- New `ProfileAnalyzer.affirm_machine_profiles()`: copies each sense's `_MT`
  (machine analysis) into the plain `…-x-cvprofile` form (the profile DATA the
  segmental/tone sorts read) and rebuilds the ps-profile slices — so languages
  where syllable-profile sorting isn't worth it can accept the machine analysis
  wholesale and move straight to segmental/tone sorts. (Trigger to offer this on
  opening a segmental/tone sort without syllable profiles is the next step.)

# Version 1.3.65
- Syllable-prep seeding now runs at LIFT LOAD, not only on 'Sort!'. The per-sense
  seeding rule was extracted to `params.seed_sense_primitives` (single source,
  used by both the prep-task presort and the new load pass, so they can't drift),
  and `ProfileAnalyzer.run` calls it for every sense after profiles are computed —
  then rebuilds the syllable-prep slice node. So `syllable_prep_complete` reflects
  reality at load: a word that became analyzable but was stranded without a syls
  count (e.g. 'always') gets it on load, keeps prep open, and the 3D board only
  appears when prep is genuinely complete — no Sort! press required. Gated to
  databases where prep has started (any word has a #C primitive); pristine DBs are
  untouched. `presortgroups` refactored onto the shared seeder (dropped the
  one-time 1.3.21 vowel-initial DIAG; kept the seeded/defaulted/backfilled tally).

# Version 1.3.64
- Fixed words stuck with syls=None (no syllable count) even after their profile
  became analyzable. `presortgroups` seeds #C/C#/syls together only on first
  encounter with a valid profile; a word first seen with an empty/Invalid profile
  was defaulted #C=C/C#=C WITHOUT syls, and the idempotent "#C already set" guard
  then skipped it forever — so the "handled when analyzable" promise never fired,
  and the word, being in no syls group, never blocked syllable_prep_complete (the
  3D board showed while it was never sorted for syllables). The already-bucketed
  branch now seeds syls (and the profile annotation) when it's missing and the
  profile is analyzable (confirmed profile, falling back to the machine value);
  logs how many words it rescued.

# Version 1.3.63
- Reworked the syllable-profile presort constraint: SYLLABLES FIRST, then edges
  (the old version trimmed edges first and could delete a syllable's vowel —
  e.g. CCCVCCCV → CCCVCCC, dropping it from 2 syllables to 1).
  1. Syllable count: a profile's count is ambiguous between its vowel-SEQUENCE
     count (VV=1) and its INDIVIDUAL-vowel count (VV=2); if `syls` is in that
     range the vowels are left alone, else vowel runs are removed (over-count) or
     added (under-count), preferring an edge run whose removal/addition also fixes
     that edge's C/V constraint (one move, two fixes).
  2. Edges: add/remove CONSONANTS only — never delete a syllable's vowel just to
     fix an edge.
  3. Fallback: if still inconsistent, emit 'CV' per syllable (+final C if C#=C,
     −initial C if #C=V) — guaranteed consistent; logged as a fallback.
  `constrain_profile` now returns {profile, changed, fallback, valid} and never
  (by construction) emits a profile that violates the constraints; a validity
  check logs an error if one somehow does (once per input profile).
- Logging: conversions and invalid-result errors once per INPUT profile; syls=None
  (confirmed #C/C# but no verified count — a data anomaly) logged once per sense id.

# Version 1.3.62
- 3D syllable board cells now follow the segment-group board's conventions
  instead of invented ones: profiles shown as "profile (count)" (not "profile
  ×n"), each marked with a trailing "+" when that profile group is verified
  (same as `g+='+'` in makeprogresstable). Dropped the cell-level "✓" prefix and
  the arbitrary 6-line cap; the macrogroup keeps its "work remains" border.

# Version 1.3.61
- TESTING: `PROFILE_CONSTRAINT['force_resort']` flipped ON so the profile
  constraint re-applies to already-(pre)sorted words. This overwrites confirmed
  sort data — flip back to False before saving over good data.

# Version 1.3.60
- Syllable presort now reconciles a machine CV profile with the word's CONFIRMED
  primitives, so an analysis that contradicts what the user verified (e.g. 'CVCV'
  for a confirmed C_1_C word) is constrained to fit ('CVCV' → 'CVC'). New
  `params.constrain_profile` (segment-aware, so length/tone modifiers ride their
  base segment): trims leading segments to the confirmed #C type, trailing to the
  confirmed C# type; syllable-count enforcement is a documented OFF-by-default
  hook (interior vowel-run reduction is ambiguous; edge-trim handles the common
  over-count). Highly configurable via `params.PROFILE_CONSTRAINT`. Applied in
  `ProfileAnalyzer.getprofileofsense` (no-op until primitives are verified);
  logs each DISTINCT conversion once ('CVCV → CVC' once, however many words).
- 3D syllable progress board cells now show the actual profiles with counts
  (most common first, capped with the full breakdown + total in the tooltip),
  instead of just the macrogroup total. '—' marks not-yet-presorted words.
- TESTING flag `PROFILE_CONSTRAINT['force_resort']` (default off): re-applies the
  constraint to already-(pre)sorted words so its effect is visible on existing
  data. It overwrites confirmed sort data — logs a warning when on; don't save.

# Version 1.3.59
- Fixed a crash on the syllable Task-1 → Task-2 board transition:
  `_measure_siblings` (window-sizing) iterated the window's children and called
  `grid_info()` on each, but the "All the syllable groups are checked!"
  ErrorNotice is a Toplevel child (no `grid_info`). It's now skipped via the
  existing sibling-skip condition (`isinstance(sib, Toplevel)`), like other
  non-gridded siblings.

# Version 1.3.58
- Syllable-count chooser word highlight, take 4 (the one that should show): the
  background recolour was a no-op because several themes set activebackground ==
  background. Switched to the button's focus-highlight BORDER (highlightthickness
  + highlightbackground, the prep board's proven mechanism) in the theme accent
  ('highlight') colour, restored on Cancel.

# Version 1.3.57
- Syllable-count chooser word highlight, take 3: recolour the verify BUTTON's
  background to its active colour (matching the status-table `activate_cell`),
  not the wrapper frame's border (which didn't render). Added an
  `update_idletasks()` flush so the recolour is painted before the modal chooser
  takes the event loop — the likely reason the earlier button attempt showed
  nothing. Restored on Cancel; Shorter/Longer destroy the button.

# Version 1.3.56
- Syllable-count chooser placement now estimates the Shorter/Longer offset from
  the buttons' REQUESTED widths while still withdrawn (no off-screen park — that
  was visible at the screen edge on some WMs, and no mapping before positioning).
  Buttons pack left in adjacent columns, so their centre-midpoint is (3*sw+lw)/4
  (or lw/2 when only 'Longer' exists). The window is mapped once, already in
  place. Ignores the few-px frame border (an estimate). Falls back to the pointer
  position if measuring fails.

# Version 1.3.55
- Syllable-count chooser now APPEARS in its final spot instead of being drawn at
  the WM default position and visibly jumping. It's created withdrawn, parked
  off-screen (mapped but invisible) just long enough to measure the Shorter/Longer
  button geometry, then mapped at the computed position. Falls back to the pointer
  position (and is always deiconified) if measuring fails, so it can't get stuck
  hidden.

# Version 1.3.54
- Status pane now distinguishes the syllable prep primitives. `cvcheckname` keyed
  the check name on ftype, but #C/C#/syls share one ftype ('lc'), so all three
  read identically. New `params.syllable_check_name` names the actual primitive
  ("word-initial sounds" / "word-final sounds" / "syllable counts"), used by
  `cvcheckname` when on a syllable primitive (Task-2 profile sort still uses the
  ftype name). The group line (`cvgrouplabel`) now shows the human group name for
  syllable prep ("= consonant initial", "= 2 syllables") instead of the bare code.

# Version 1.3.53
- Syllable-count chooser reference, take 2: the active-colour highlight (1.3.49)
  recoloured the button's BACKGROUND, which is invisible behind the word's
  illustration (compound image). Now it borders the word's wrapper FRAME
  (highlightthickness/highlightbackground) — visible around the picture — and
  restores it on Cancel. (ui.Button is a real tkinter.Button, so it honours
  background/activebackground; the colour was just occluded by the image.)
- The chooser is now positioned so the pointer lands BETWEEN the Shorter and
  Longer buttons (their centre-midpoint, on the button row), not at the window's
  top-left — so reaching 'Longer' is no longer a longer mouse travel than
  'Shorter'. With only 'Longer' (n==1), the pointer aims at it.

# Version 1.3.52
- Removed the temporary blank-row DIAG (added 1.3.50). Confirmed: a non-breaking
  space in the gloss was the cause (verified by correcting the data); the 1.3.51
  display normalisation keeps it from blanking the label regardless.

# Version 1.3.51
- Fix for the illustration-only verify row: a non-breaking space (\xa0) in a
  word's display text (e.g. the untranslated "?\xa0?" French gloss) blanks the
  entire label on this Tk/font, leaving only the picture. The DIAG confirmed the
  formatted text was correct ('bake — …'), so the failure is in rendering, not
  data. `build_verify_button` now normalises \xa0 → plain space for display
  (data untouched).

# Version 1.3.50
- TEMPORARY diagnostic (removable): `verifybutton` logs `text`/`glosslangs`/
  `frame`/`cvt`/`ftype`/`en`-in-`lc`/`glosses` for any sense whose id contains
  "bake", to capture why one CAWL entry renders as illustration-only in the
  syllable verify (the static entry data traces to non-empty text, so this
  catches the runtime state). Remove once diagnosed.

# Version 1.3.49
- Syllable-count chooser now refers visibly to the word that opened it: the
  clicked verify button stays in its active colour while "How many syllables?"
  is open, and is restored on Cancel (Shorter/Longer move the word out, so the
  button is destroyed — only Cancel needs the restore). The chooser is also
  placed at the pointer (where the word was clicked), like a context menu —
  best-effort, since Wayland/XWayland may ignore a client-set window position.

# Version 1.3.48
- Fixed: flagging a word in the syllable-count (syls) verify did nothing. The
  Shorter/Longer chooser was built with `ui.Toplevel(parent, title=…)`, but
  ui.Toplevel passes kwargs straight to tkinter, so `title=` became the invalid
  widget option `-title` and raised (swallowed by the Tk error catcher, so the
  click silently failed). Switched to `ui.Window` like every other dialog (it
  accepts `title`, themes, builds `.frame`, and surfaces over the kiosk run
  window); content now grids into `w.frame`, with `w.lift()`.

# Version 1.3.47
- Syllable PREP navigation: finish the current check (forward + wrap within it,
  picking up any slice a misfit re-opened) before advancing — fixing 1.3.46,
  where finishing V# could jump to syls while a C# slice was still pending (the
  wrap spanned all checks instead of stopping at the check boundary). When the
  current check IS fully verified, the next slice is the earliest pending in
  fixed check order (#C, C#, syls), so an unverified slice in an EARLIER check
  (e.g. one skipped via a board click) is returned to rather than skipped.

# Version 1.3.46
- Syllable PREP verify navigation now walks each pass FORWARD instead of always
  jumping to the first unverified slice. `next_unverified_slice` keeps a cursor
  and returns the next pending slice after it, wrapping only at the end of the
  order (all #C=C, then #C=V, then C#…, syls…). So moving a misfit into an
  earlier slice (re-opening it) no longer cuts the user back to it mid-pass
  (V4 → C27 → V5 → C27…); re-opened slices are picked up on the wrap, after the
  rest of the pass. The "what's still unverified?" test is now at the end of a
  pass, not after every group. Board-click selection still overrides (and the
  pass continues from the clicked slice).

# Version 1.3.45
- Syllable PREP rebuild now reproduces the interactive slice layout. `assign_slices`
  mirrors `move_misfit`'s placement: words whose spelling agrees with the group
  sort in naturally; by-ear-only members (spelling implies another group, or
  unanalysable) go to the end, clustering in the last slice(s) as a re-verify
  cohort. So a from-scratch rebuild (now the norm, since the index is session-local)
  reconstructs the layout from durable data — membership annotation + the
  spelling-derived value — instead of a flat alphabetisation.
- The three primitives (`word_initial`/`word_final`/`syllable_count`) + `VOWEL_SYMS`
  moved from the `Syllables` task mixin to `params` (their canonical home), so they
  can be reached off the live task — needed because `assign_slices` runs on the
  board-render rebuild, where `program.task` may not be a syllable task.
  `Syllables._word_*`/`_syllable_count` now delegate to params; `_orthographic_value`
  uses params directly (reads the plain `cvprofile` form, matching presort).

# Version 1.3.44
- Syllable PREP board: clicking a slice cell now SELECTS it as the next slice to
  verify (and moves the highlight) instead of immediately launching the verify —
  matching every other sort task (click to select, then 'Sort!' to act). The
  selection is stored on `program.syllable_preferred_slice` so it survives the
  SyllableSliceDict rebuild that `runcheck` does between the click and the button
  press; `next_unverified_slice` honours it once. `verify_prep_slice` →
  `select_prep_slice`; new `StatusFrame.update_active_prep_cell` moves the
  highlight (prep cells are keyed by (check,group,idx), not profile). The board
  highlights the active slice (selection if still pending, else next pending).
  (Click-to-launch may return as an opt-in workflow later.)

# Version 1.3.43
- Syllable PREP slice/page index is now SESSION-LOCAL — no longer written to the
  LIFT as `<check>-slice` annotations. It's packing state, not a lexical fact, so
  it's recomputed deterministically each session from the durable LIFT data
  (group membership in the `<check>` annotation + confirmation in the primitive
  verification field). Boundaries stay stable within a session; across a restart
  they recompute (same inputs → same boundaries). `build()` writes no LIFT data
  now, and only persists the `data.json` node cache when it actually changed.
  `_prep_board_data` builds so the board repopulates from membership after a
  restart. Legacy `<check>-slice` annotations are ignored (not stripped).
  Rationale + the accepted minor regression: docs/adr/0001-syllable-slice-index-ephemeral.md
  (drafted by the AI agent; provisional, pending terminology review).
- Default words-per-page (`MAX_SLICE`) lowered from 150 to 50.
- Fixed: the `syllable_max_slice` setting was never persisted/loaded — it was in
  DOMAIN_MAPPING['ui'] but missing from settings['defaults']['attributes'], so
  `makesettingsdict` never collected it. It fell back to the default in the label
  while the slices on file used the user's real cap (disagreement + a needless
  re-slice on open). Now registered like `buttoncolumns`, so it round-trips.

# Version 1.3.42
- The "words per page" chooser now closes immediately on selection, before the
  syllable-prep board re-slices and redraws, instead of lingering on screen
  through the (slightly slow) re-slice and dying afterward. `setmaxslice`
  destroys the chooser first, then defers the `build()` + `maybeboard()` to a
  short `after()` so the window teardown renders first (and no synchronous Tk
  flush is forced). Bad input still leaves the chooser open to retry.

# Version 1.3.41
- Changing "words per page" (syllable_max_slice) now re-slices and redraws the
  syllable PREP board immediately, instead of only updating the label and
  deferring the reshape to the next prep run. `setmaxslice` now calls
  `_prep_board_data(ps).build()` (re-slices the checks whose stored slice_cap
  changed; 'done' is re-derived from the durable per-sense codes so verified
  words stay verified) followed by `maybeboard()`. Guarded to the syllable
  task (cvt=='S'). The slice data itself is durable (per-word <check>-slice
  annotations + the status node in data.json); program.syllable_slices is only
  the live reader over it.

# Version 1.3.40
- Syllable PREP (Task 1) status board now refreshes when you close the run window
  mid-prep. `SyllablePrep._finish_prep_slice` previously bailed out of its
  close branch without redrawing, so slices verified before closing kept their
  pre-task appearance until the task was reopened (the data was always persisted
  correctly — only the redraw was missing). It now calls `self.status.maybeboard()`
  on that branch, matching the per-completion `maybeboard()` the other sort
  checks already fire. Per-slice status is reported per slice (synthetic
  `group␟idx` ids in the `done` cache), and survives re-slicing because doneness
  is re-derived from durable per-sense primitive verification, not the slice ids.

# Version 1.3.39
- Wait window is now a SINGLETON owned by the Tk root, reused across waits instead
  of created+destroyed each time. `Wait` is built once (mastered by tk_root,
  withdrawn) and shown via `activate()`/`deactivate()` (deiconify/withdraw) rather
  than `Wait(...)`/`close()`→`destroy()`. `Waitable.wait()` records the window to
  background (`reveal_parent`/`do_reveal` on the singleton), swaps in the new
  message, and deiconifies the one window; `waitdone()` reveals the tracked parent
  then withdraws the singleton. New `Waitable._waitwindow()` resolves the per-root
  singleton via `self._root()` (so the startup fakeroot gets its own). `iswaiting()`
  now means "the one wait window is currently shown (active)", not "a ww object
  exists". Removes the per-wait realize/teardown cost and the extra window-state
  transition that was stacked right after the parent withdraw — so on the 2nd+ wait
  the dialog is just a deiconify (~0s) of an already-built window.
  - Progressbar is now ungridded on `activate()` and re-gridded on demand by
    `Window.progress()`, so a wait that reports no progress shows no (stale) bar in
    the reused window.
  - `make_cancellable()` is idempotent (build once, show/hide) since the window
    persists; added `hide_cancel()`.
  - Mirrored in the webview backend (`ui_webview.py` `Wait`/`Root`) and documented
    in the `WaitInterface`/`WaitableInterface` contract (`ui_interface.py`).
  - NOTE (scope): the parent window is still withdrawn (`self.withdraw()`) per the
    agreed design, so the parent-withdraw transition (XWayland deadlock ingredient
    "B") is unchanged; this change removes the per-wait window churn, not that
    transition. Putting the verify build back on the `drive_work` pump (so the
    dialog actually animates during a long build) remains a separate follow-on.

# Version 1.3.38
- The ~20s "blank" is `waitdone()`'s `update()` (the verify render); the fullscreen
  deiconify is ~0s (1.3.37 timing). Virtualization is confirmed working — it caps
  the render at the visible rows (~21), so 150-item slices cost ~the same as 30
  (the floor is ~21×~1s/item, the XWayland per-item render cost). Virtualization
  stays (it's what makes big slices viable). For that floor, reordered `waitdone()`
  to render+reveal the run window WHILE the "Loading…" dialog still covers the
  screen, then close the dialog — so the user sees "Loading…" during the render
  instead of a blank screen (the long-requested "cover it" fix). The deeper per-item
  render cost (~1s/item on this XWayland box) is left as-is — diminishing returns.

# Version 1.3.37
- Diagnostic: the `verify reveal (waitdone)` numbers show ~17–33s regardless of
  slice size (30→~22s, 75→~32s, 142→17s) — so it's a FIXED per-slice cost, not the
  per-item render. Virtualization (1.3.32) was therefore aimed wrong: it caps the
  visible-render and the scroll is nicer, but the clock barely moved. Split
  `waitdone()`'s timing (`waitdone: update Xs, deiconify Ys`) to confirm whether the
  fixed cost is the app-wide `update()` or the fullscreen kiosk `deiconify()` (the
  per-slice window remap). If it's the deiconify, the fix is to stop remapping the
  fullscreen window each slice (reuse it mapped) — and virtualization likely reverts.

# Version 1.3.36
- Fix the empty "Select Words Per Page" dialog: it used `scrolling=True`
  (`ScrollingListBox`), which rendered no options; switched to `scrolling=False`
  (`ListBox`), matching the working "button columns" dialog. The 8 options
  (15/30/50/75/100/150/200/300) fit without scrolling.

# Version 1.3.35
- Fix startup crash from 1.3.34 (`'Settings' object has no attribute 'get'`):
  `program.settings` is the legacy `Settings` object, which exposes settings as
  plain attributes (the `buttoncolumns` pattern), NOT the `.get()/.set()` domain
  API I'd assumed. Switched all three sites to the attribute (`syllable_max_slice`):
  `settings.setmaxslice`, the status `maxslicelabel`, and `SyllableSliceDict.max_slice`.
  (The old `max_slice` read `settings.get()` inside a try/except, so it silently
  fell back to the default and the setting had never actually applied — now it does.)
  Persistence still rides `DOMAIN_MAPPING['ui']` like `buttoncolumns`.

# Version 1.3.34
- Words-per-page (syllable slice size) is now a user setting, field-tunable per
  machine without code changes — since the right value depends on hardware and
  we've only tested one box. It lives in the status frame just under "button
  columns" (shown during syllable sorting, cvt='S'): click to pick from
  15/30/50/75/100/150/200/300. Stored as `syllable_max_slice` in the `ui` domain
  (auto-saved); `SyllableSliceDict.max_slice` already reads it, falling back to the
  `MAX_SLICE` default. Wiring: `Converter.DOMAIN_MAPPING['ui']` += the key;
  `settings.setmaxslice`; status `maxsliceline`/`maxslicelabel`/`updatemaxslice`;
  `ui_settings.getmaxslice` dialog.

# Version 1.3.33
- `MAX_SLICE` 30→150: virtualized verify (1.3.32) renders only the visible rows, so
  per-page render should be independent of slice size — testing big pages (fewer of
  them). This run also confirms whether virtualization actually cut the render: the
  `verify reveal (waitdone)` time at 150 should be small (a few seconds) if so, or
  ~tens of seconds if the off-screen unmap isn't landing before the render (a fixable
  timing bug). Scroll-height ceiling: ~150×80px is well under the X11 32767px cap.

# Version 1.3.32
- EXPERIMENTAL: virtualized verify list. The render wall is that Tk paints every
  *mapped* gridded child, so all N items render even though ~a dozen are visible
  (~0.5s/item → the "blank minute"). `_virtualize_verify` now unmaps rows outside
  the viewport before `waitdone()` renders, pinning each row's height (`minsize`)
  so the scrollbar still spans the whole list, and re-maps rows as you scroll (via
  a lightweight 150ms poll on `canvas.yview`). Goal: render ~0.5s×visible instead
  of ×N, independent of slice size. Contained to the verify build path; comment out
  the call (or revert this version) to disable. Untested first cut — expect to
  iterate (row-height estimate, initial-viewport math, scroll-lag are the risky
  bits). Does NOT touch the ~8s fixed per-slice cost (likely the kiosk deiconify).

# Version 1.3.31
- Correction: the batch build's "verify build 0.9s" was a misleadingly-scoped timer
  — the real per-slice cost is RENDERING the items, which moved into `waitdone()`'s
  `update()` (`verify reveal (waitdone)`), measured at ~22.6s for 30 items (~0.7s/
  item, roughly linear). So the batch rework didn't speed things up vs streaming; it
  only relocated (and hid) the cost. The genuine, solid win remains the FREEZE fix
  (no deadlock at any slice size). Small slices do NOT fix the render.
- Removed the 1.3.18/.19 full-wordlist image preload (a cache-exoneration DIAG that
  hoarded ~1700 images → ~4 GB RSS); reverted to the per-slice lookahead. Tests
  whether that 4 GB was slowing the per-item render (memory/X pressure). The LIFT
  write is already backgrounded, so it's not the main-thread blocker (GIL contention
  during its serialization is a possible secondary factor, not yet pursued).

# Version 1.3.30
- Located the "blank minute": it's `waitdone()`'s `self.update()` (ui_tkinter.py
  1170), which renders the whole build backlog (N buttons+images, ~1 XWayland
  round-trip each) AFTER closing the "Loading…" dialog and BEFORE deiconifying the
  run window — so it's invisible. The actual final paint is only ~2s. Added a timer
  (`verify reveal (waitdone) Xs`) so that gap is no longer silent.
- `MAX_SLICE` 75→30: the render is super-linear (~5s at 30 vs ~a minute at 75), so
  small slices keep each page snappy. (Big-and-fast needs virtualized scroll = #4.)
- Also surfaced: the LIFT write has grown to ~16s/slice over a session (whole-file
  rewrite + accumulating durability verification codes), entangled with the build's
  "residual" — a separate cost to address next, independent of slice size.

# Version 1.3.29
- Diagnostic: time the single `update()` commit (logs `verify commit (paint) Xs`).
  The build is fast (~0.9s) but the window appears ~a minute later — the gap is the
  PAINT (compositing N buttons+images on XWayland), one opaque blocking commit in
  batch mode. This measures it per slice size to drive the next decision (smaller
  slices for short paint gaps vs keeping a "Loading…" dialog up through the paint).

# Version 1.3.28
- Verify build rearchitected (#3): batch-build the whole slice with NO per-item
  flush, then a single drained `update()` commit. The logs showed the per-item
  synchronous progressbar flush (not the work — that's ~0.4s total for 75) was the
  ~0.6s/item cost AND the large-slice deadlock; total time scaled with item count,
  so page size couldn't fix it. Now: place all buttons under one `suspend_configure`
  → one `resume_configure` reflow (in `_grid_ok`) → one `runwindow.update()` (which
  DRAINS the event queue while flushing, avoiding the XWayland write-deadlock a bare
  `update_idletasks` hits on a big backlog). Expectation: ~44s→a few seconds, no
  per-item round-trips (so no per-item freeze risk), and big pages potentially both
  fast and safe. Replaces the `_first`/`_rest` streaming. `MAX_SLICE` stays 75 for
  the first test, then 150. Fallback if this regresses: restore streaming + one
  midpoint reflow.

# Version 1.3.27
- Reverted the 1.3.26 progressbar-flush guard: that flush is LOAD-BEARING — it's
  what commits the Wayland surface so the window paints during the build. Guarding
  it removed the large-slice deadlock but left the window unpainted (confirmed: no
  visible UI at all at 150/page, build never completes, event loop idle = not a
  deadlock). So the deadlock and the painting are the same call; it can't just be
  removed. The Wait.__init__ guard (1.3.24) stays (it helped the blank-dialog time
  and isn't the per-tick paint commit).
- `MAX_SLICE` 150→75 to find the largest slice that both paints (flush on) and
  avoids the deadlock. 75 was historically marginal, but the kept Wait guard
  removed one synchronous flush per slice, which may give it enough margin. If 75
  still wedges (faulthandler at progressbar→update_idletasks), 30 is the known-good
  size and large pages await the #3 fix: a non-deadlocking per-tick surface commit
  (e.g. `update()`, which drains the event queue rather than only flushing).

# Version 1.3.26
- Freeze fix, part 2: at 150/page the deadlock RELOCATED (faulthandler) from the
  now-guarded Wait flush to `Progressbar.current`→`update_idletasks` (reached via
  `waitprogress`/`drive_work`) — same synchronous-flush family, next call down. So
  it's the flushes, NOT window creation (the Wait window built fine; the hang was
  mid-drive). Scoped-guarded that flush on Wayland too: the bar value still sets and
  the `after(1)` event loop paints it, no forced round-trip. `MAX_SLICE` stays 150
  to test whether this clears the large-page freeze (→ big pages safe, retiring the
  many-pages cost) or relocates again (→ next flush, or the #3 single-window work).

# Version 1.3.25
- Diagnostic: `MAX_SLICE` 30→150 to test the second suspected freeze mechanism now
  that the Wayland flush-deadlock is guarded (1.3.24). 1.3.24 also visibly cut the
  blank-dialog time from ~6–7s to <1s (the forced flush was delaying the paint it
  was meant to force). If 150/page builds clean, the guarded flush was the whole
  story and big pages are safe (retiring the many-pages UX cost); if it wedges,
  there's a real compositor pixmap/texture limit on the tall 1-column verify list
  and we add the columns / scroll-height fix.

# Version 1.3.24
- Freeze fix (item 2): scoped-guard the synchronous `update_idletasks()` in
  `Wait.__init__` on Wayland. That flush (a blocking server round-trip right after
  `deiconify()`) is the faulthandler-confirmed XWayland deadlock point; it only
  force-paints the dialog before the slow work, which `drive_work`'s `after(1)`
  event loop does ~1ms later anyway — so it's redundant and we skip it on Wayland
  ONLY. Deliberately NOT the module-wide `WAYLAND_UPDATE_GUARD` (that would also
  kill the legitimate geometry-measurement flushes); just the one deadlocking call.
  Keeps the wait dialog (it still paints via the loop). MAX_SLICE stays 30 for the
  first confirming run; raising it is the next test (whether big pages are now safe).

# Version 1.3.23
- Syllable PREP verification is now LIFT-durable, fixing an inconsistency the prep
  rework introduced: the segmental/profile checks persist confirmation per-sense in
  the LIFT (and status is drawn from it), but prep stored verified-slice state only
  in data.json — so prep confirmation was lost if data.json died.
  - New profile- AND ps-INDEPENDENT field `'<ftype> primitive verification'`
    (`Sense.primitiveverification`, routed via a `PRIMITIVE_VPROFILE` sentinel in
    `verificationkey`) holding per-sense codes `#C=C` / `C#=V` / `syls=2`. Profile-
    independent because the primitives DETERMINE the profile (can't be keyed by it;
    the old `whole-word lc verification` pseudo-profile was that same smell).
  - `SyllableSliceDict.mark_slice` writes/removes these per-sense codes; the status
    `done` list is now DERIVED from them in `build()` (a slice is done iff every
    member is confirmed) — so prep status is reconstructed from the LIFT like
    everything else.
  - `mark_for_reverify` no longer strips members' confirmations (a moved-in misfit
    just lacks a code, so the slice is auto-pending) — preserves real user data.
  - presort is deliberately UNCHANGED (still idempotent): we do NOT auto-re-derive
    machine defaults, which would clobber corrected-but-unconfirmed values on
    restart. The bad-data source (ps-less profiles, threading race) is fixed in
    1.3.22, so stale pre-fix values (e.g. 'away'='C') are left for manual cleanup.
  - Note: existing prep `done` (data.json) and the legacy `whole-word lc
    verification` fields are not migrated; prep re-verifies once, then persists
    durably in the new field.

# Version 1.3.22
- CV profiles are now computed for EVERY sense, including ps-less ones (principled
  de-ps of profile computation). The profile is a ps-independent form fact
  (`profileofform` ignores ps for the value; it only refused to run when ps was
  falsy), but `run()` iterated `for ps in db.pss`, and `getpss()` drops falsy ps —
  so a word with no part of speech (e.g. 'away') never got a profile, and
  wordlist-wide presort then defaulted it to consonant-initial. Now a ps-less pass
  computes their profile under a truthy `PSLESS` sentinel, VALUE only (no per-ps
  aggregation, so no phantom ps leaks into segmental/report views). Words that
  have a ps still populate every per-ps structure exactly as before.
- Fixed the profile-computation threading bug: `_getprofiles` spawned a
  fire-and-forget thread per sense and joined only the last, so ~all profile
  writes raced on the shared XML tree + aggregation dicts (could land wrong/
  incomplete, vary run-to-run). Now synchronous — deterministic and race-free
  (the work is cheap regex; the GIL gave the threads no real CPU win anyway).

# Version 1.3.21
- Diagnostics only: investigating why, after de-ps (1.3.20), vowel-initial words
  (e.g. 'a'-initial adjectives) land in the consonant-initial (#C='C') bucket.
  presort now logs, for each word it defaults to consonant, the form + the RAW
  `cvprofile_<ftype>` value it read (empty vs 'Invalid' vs a real profile), plus
  the count skipped as already-bucketed. This distinguishes the candidate causes:
  empty profile (→ likely the fire-and-forget threading in
  `ProfileAnalyzer._getprofiles`, which spawns un-joined background threads that
  mutate the XML tree concurrently and joins only the last) vs 'Invalid' (a real
  form issue) vs already-bucketed-wrong. No fix yet; awaiting the log.

# Version 1.3.20
- Syllable PREP is now WORDLIST-WIDE, not per-part-of-speech. The three primitive
  checks (#C / C# / syls) are ps-INDEPENDENT form facts, so they're established
  once over the whole wordlist; ps re-enters only downstream as the (profile × ps)
  intersection for segmental slices. Changes:
  - `SyllableSliceDict._psenses()` → `db.senses` (all ps), so groups/slices/board
    span the whole wordlist (this also resolves the cache-test plateau at ≈920 =
    Nouns-only — prep itself now walks every illustrated word).
  - Prep verify state moved under a new `params.SYLLABLE_PREP_PS='*'` sentinel ps
    (shared across ps) instead of the live ps; `_node()` and
    `syllable_prep_complete()` (now ps-agnostic) follow.
  - `Syllables.presortgroups()` seeds EVERY word, not just the current ps.
  - Note: existing per-ps prep verify state is orphaned (re-verify from scratch) —
    already the case anyway since the 75→30 cap change forces a re-slice.

# Version 1.3.19
- Diagnostics only: the v1.3.18 full preload plateaued at cache≈920 because
  `all_uris()` walks the ps-bound slice dict (Nouns only ≈ 924 forms). Repointed
  the cache-ceiling test at `program.db.senses` (the whole wordlist, all parts of
  speech) so the cache races to its true ceiling (~all illustrated words). Same
  intent as 1.3.18: confirm a full cache does not break 30/page builds.

# Version 1.3.18
- Diagnostics only (agenda item 1 — cache-exoneration test): at syllable-prep
  start, preload EVERY illustration (new `SyllableSliceDict.all_uris()`) so the
  image cache races to its full size (~all illustrated words) while the user works
  30 items/page. The v1.3.17 run already ran clean to cache≈566 / RSS 2 GB with a
  FLAT ~7.5s `update_idletasks` (cumulative pressure falsified; per-page button
  count confirmed as the freeze driver). This pushes the cache to its ceiling to
  confirm absolutely that a large cache does not break small-slice builds — i.e.
  that we may keep the cache and cache aggressively. No fix; awaiting the run.

# Version 1.3.17
- Diagnostics only: `MAX_SLICE` knocked 75→30 to falsify the cumulative-pressure
  hypothesis. The v1.3.16 run showed the freezing `update_idletasks` flush scaling
  with accumulated session state (1.9s @ cache 0 → 8.5s @ cache 170 → hang @ cache
  286), *not* with the current slice's button count (a 153-item slice built fine at
  cache 170; the 75-item slice that built fine early hung later at cache 286). If
  that read is right, 30/page should still wedge — just after more page rebuilds,
  as the per-flush cost creeps up. No fix yet; awaiting the run.

# Version 1.3.16
- Diagnostics only: per-step timing inside the Wait-window build. A SIGUSR1
  faulthandler dump pinned the freeze at `update_idletasks()` (the synchronous
  flush right after `deiconify()`) in `Wait.__init__` — the classic XWayland
  state-transition + flush deadlock; the `WAYLAND_UPDATE_GUARD` that used to skip
  it is currently OFF. This release logs each sub-step — kiosk withdraw (in
  `wait()`), realize, widget build, deiconify, update_idletasks — each BEFORE the
  next risky call, so a frozen run leaves a trail naming the wedged step, plus a
  per-attempt `cache≈N` (live PhotoImage count, an X-pixmap proxy) to test whether
  the freeze correlates with accumulated X resources. True server-side counts:
  align these lines with an external xrestop trace by timestamp.

# Version 1.3.15
- MAX_SLICE 30 → 75, to re-run the 1.3.14 diagnostic at a larger slice. 1.3.14
  pinned ~18 of the ~23s per 30-item slice on the Wait dialog (progress-bar
  updates ~11s + Wait-window creation ~7s), with content ~0.3s. At 75/slice the
  per-item Wait costs (progressbar, paint) should scale ~2.5×; the goal is to
  confirm the Wait machinery — not content — dominates at larger N too, before
  removing it. Re-slices 30→75 on the next prep run via the slice_cap marker.
  Diagnostics from 1.3.14 retained.

# Version 1.3.14
- Diagnostics only (no behavior change): finer split of the per-slice build. 1.3.13
  showed ~all 22s as "residual" — NOT image/widget/reflow (each ~0.1s) and NOT
  affected by the preloader (a fully-prefetched slice built in the same 22s, so
  decode/pixmap are conclusively irrelevant). This release splits the residual:
  (a) a timer around `verifybutton_fn` per item (backend status/annotation work vs
  the widget build already timed), and (b) `drive_work` instrumented per tick into
  generator-work / progress-bar-update / event-loop-gap. The gap is `after()` +
  the Tk event-loop pass that paints the just-added imaged button — one synchronous
  XWayland round-trip per item, the prime suspect for the ~0.7s/item. The log line
  now reads: per-item work [image/widgets/backend] | drive: genwork/progressbar/
  eventloop-paint over N ticks | reflow | residual. To be read, then removed.

# Version 1.3.13
- Diagnostics only (no behavior change): the per-slice verify build (~22s flat,
  whether or not the 1.3.12 preloader prefetched — which falsifies the I/O/decode
  hypothesis) now logs WHERE its seconds go. A second log line under
  `verify build:` partitions the time into image work (split by path:
  built/preloader-compiled/full-scaled), widget creation, layout reflow, and
  residual. The `compiled` path is preloader-fed, so its time is pure Tk
  `PhotoImage` pixmap upload — if that dominates, the wall is X round-trips and the
  real fix is fewer/cheaper pixmaps, not off-thread decode. To be read, then likely
  removed once the bottleneck is identified.

# Version 1.3.12
- Background image preloader for syllable prep (attacks the proven cause: the
  per-slice build is I/O/decode-bound — ~0.6–0.7s/image, CPU idle — serialized on
  the Tk thread, which is what wedged at MAX_SLICE=150). While the user reads the
  current slice aloud, a daemon worker decodes+resizes the next slices' images
  OFF the Tk thread; the main-thread build then only does the cheap PhotoImage
  compile. Confirmed by the 30-across-slices test: slices 2/3 do NOT hang, so the
  per-slice wait dialog is exonerated and the cost is purely size/load.
  - `Image.__init__(compile_now=False)` restored: skips the lone Tk call so
    open/decode can run off-thread; `prepare()` does the PIL resize; `compile()`
    stays on the main thread.
  - `SortPresenter.preload_images(iuris)`: one daemon worker + queue; dedupes by
    (uri, size); never clobbers a fully-built image; a bad image can't kill it.
  - `set_sense_illustration`: when an image was prepared off-thread, it just
    `compile()`s (cheap) instead of re-running the resize.
  - `SyllableSliceDict.upcoming_slices`/`preload_uris` feed the next N pending
    slices' image URIs in walk order; `verify_slice` queues them once a slice is up.
  - Lookahead depth configurable: `syllable_preload_lookahead` (default 2).
  - MAX_SLICE stays 30 for now; the preloader is the lever to raise it later.

# Version 1.3.11
- Reverted to the known-good test point: MAX_SLICE back to 30 and the per-page
  background-load WAIT dialog left in place. The 150-slice test failed two ways:
  a 71s build (I/O-bound) AND a hard hang on slice 2 in *Wait-window creation*
  (mapping the Wait dialog over the already-mapped kiosk window). Open question
  to disambiguate by testing 30 across multiple slices: is the slice-2 hang
  size-dependent (→ I/O/build-size) or the per-slice wait dialog (size-independent)?
- Kept `Image.prepare()` (PIL resize split from the Tk PhotoImage compile) as
  groundwork for the I/O hypothesis / a future background preloader. Inert until
  called. (Its companion, `Image.__init__(compile_now=False)`, was NOT kept.)

# Version 1.3.10
- MAX_SLICE default back to 150 (was 30) to test whether the suspend_configure
  reflow fix (1.3.9) makes full-size prep slices build acceptably. The cap-change
  re-slice in SyllableSliceDict.build will re-slice existing 30-word data to 150
  on the next prep run (slice_cap marker per check). Still tunable via
  'syllable_max_slice'.

# Version 1.3.9
- LIKELY THE REAL FIX for slow verify builds. The data (30 items, 21.5s, no CPU,
  flat RSS) pointed at per-item blocking, not compute. Cause: the verify build
  never wrapped item placement in `ScrollingFrame.suspend_configure()` /
  `resume_configure()` (those exist for exactly this but were called nowhere), so
  every streamed item triggered a full O(n) scrollregion reflow — a synchronous X
  round-trip — making the build O(n²) round-trips ("0.7s/item, no CPU"). Now
  `build_verify_layout` suspends the reflow during the batch and resumes once
  after the first screenful and once at the end. Expect the per-page time in the
  "verify build:" log to drop sharply (and likely makes larger slices viable
  again — retest before raising `syllable_max_slice`).

# Version 1.3.8
- Build log now also reports live cached-image count ("N cached imgs") — a
  client-side proxy for X pixmap pressure, since xrestop shows "no pid" for
  XWayland clients (they don't advertise _NET_WM_PID). Pair with Xwayland's own
  VmRSS (server-side pixmap memory) to separate build-time from resource limits.

# Version 1.3.7
- Wayland update guard is now a one-line toggle: `WAYLAND_UPDATE_GUARD` at the top
  of frontend/ui_tkinter.py (default False = call update through normally; set True
  to restore the Wayland skip). (Correction: pulling the guard *correlated* with
  the transition working — not claimed as proven cause.)
- Instrumented the verify build to measure what's actually limited: logs
  "verify build: N items in Ts, RSS A→B MB (C cols)" via psutil. Combine with
  `xrestop` (X pixmaps) to tell build-time (CPU/IO) from resource pressure.

# Version 1.3.6
- Result (Kent): with the Wayland guard pulled, the post-page window transition
  works fine — i.e. SKIPPING update_idletasks was the cause of the wedge (stale
  geometry the next transition choked on), not the cure. Guard stays disabled.
- Cache scaled illustrations (`SortPresenter.set_sense_illustration`): `scale()`
  re-ran PIL.resize() AND allocated a fresh Tk PhotoImage (X pixmap) on every
  call. The same word's 65px image is shown across all 3 prep checks, every
  re-verify, the profile sort, and transcription — now it's built ONCE per
  (image, zoom) and the same PhotoImage is reused; loaded images are also stored
  in theme.image_cache by URI. Big speed win on rebuilds/repeat displays; the
  trade-off is more steady-state cached pixmaps (bounded by #unique word images
  ~800) — add an LRU cap if `xrestop`/RSS shows pressure.
- NOTE: the ~32,767px Tk canvas height cap (16-bit coords) still bounds a SINGLE
  column (~360 image-rows); big pages need multiple columns (`buttoncolumns`) or
  a smaller `syllable_max_slice`. Caching does not change that ceiling.

# Version 1.3.5
- Diagnosis (Kent): 500+ buttons kills the page build itself; ~150 builds fine
  but the following window transition kills it. So, for testing:
  - Disabled the Wayland skip on `UI.update`/`update_idletasks` — they call
    through unconditionally now, so pages refresh when asked (re-enable by putting
    `if not USING_WAYLAND:` back in front of each super() call).
  - Restored the per-page background-load WAIT in `build_verify_layout`: build the
    first screenful behind a "loading" wait, reveal, then stream the rest in
    behind it (`runwindow.wait` + `wait_and_drive_work`), as the working segmental
    verify does. Prep verify passes a "Loading the words that are {desc}…" message.
  - The reused prep run window stays (one window for the whole prep session,
    content rebuilt per slice), so there's no per-slice fullscreen transition —
    the "150 kills the following transition" half. MAX_SLICE default stays 30
    (tunable via 'syllable_max_slice'); raise toward ~150 to test bigger pages.

# Version 1.3.4
- Keep CAWL images in syllable-prep verify (NOT dropping them — per Kent). The
  prep freeze tracked with building a whole big slice's images at once (~0.4s
  each), so instead SHRINK the slice: MAX_SLICE default 150 → 30, so each prep
  verify builds like a normal image-bearing segmental verify group (which works).
  Still tunable via the 'syllable_max_slice' setting (raise if the box is happy,
  lower if a slice is slow to appear).
- `SyllableSliceDict.build` now re-slices a check ONCE when the cap changes
  (stores `slice_cap` per check node) — existing per-word slice indices are
  otherwise sticky, so lowering the default wouldn't re-slice already-sliced data.
  A normal misfit (slice one-over-cap) does NOT trigger re-slicing.

# Version 1.3.3
- Fix (the real one): syllable prep recreated the kiosk-fullscreen run window
  PER SLICE (`getrunwindow` destroys+remaps a new fullscreen window each call);
  on XWayland a fresh fullscreen MAP wedges the compositor (pure-`mainloop` hang,
  no Python wait involved). Segmental never hits this because its page loop builds
  the window ONCE and only rebuilds content. Prep now does the same: ONE reused
  run window for the whole prep session (`_prep_runwindow` clears + rebuilds its
  frame per slice; `getrunwindow` fires at most once / reuses the presort window),
  so there's a single fullscreen map for all slices. `_finish_prep_slice` no
  longer `on_quit`s between slices; the window closes only when prep completes or
  the user quits.

# Version 1.3.2
- Fix: syllable prep froze at `wait_window` (sorting_engine.py:131) — the
  per-slice destroy→create→deiconify→`wait_window` churn blocks the X server
  while the new run window's map is still in flight, which XWayland deadlocks
  (the central guard only covers `update_idletasks`, not `wait_window`/`tkwait`).
  Reworked the prep loop to be EVENT-DRIVEN: `verify_slice` builds the slice and
  returns; the OK button (the canary's `<Destroy>`) marks the slice verified and
  schedules the next via `after()`. No blocking server-wait anywhere in prep.
  The end-of-prep notice is now `wait=False` for the same reason.
- NOTE: the shared `verify()` (segmental/tone) still uses `wait_window`; it is
  single-page so it's the lower-risk case, but for full Wayland-safety it would
  need the same event-driven treatment (out of this redesign's scope — run Xorg,
  or ask and I'll convert it).

# Version 1.3.1
- Fix: syllable-prep verify froze on XWayland again. `build_verify_layout` now
  builds the (single-page) verify list IN PLACE — reveal the run window and
  stream items in, with NO Wait dialog. Mapping a Wait transient over the kiosk
  window (+ its `update_idletasks`) was the deadlock; "designed out" means no
  dialog, not just one page.
- Fix: the syllable-prep progress board no longer renders a header-only skeleton
  before there are slices to show (`makeSyllableprepboard` bails to `makenoboard`
  unless real slice cells exist — as elsewhere).
- Restored the central XWayland guard (`UI.update`/`update_idletasks` skip on
  Wayland; `utilities/display.py`). It's invisible on Windows/X11 (where users
  run) and keeps every other popup/Wait dialog (ErrorNotice, join, status reload,
  the end-of-prep notice) from deadlocking on the dev's Wayland box. The
  verify-in-place change above stands regardless.

# Version 1.3.0
- syllable_sort_redesign STEPS 2 & 3 — syllable sorting split into two tasks
  (docs/syllable_sort_redesign.md):
  - **Task 1 (PREP).** New `SyllableSliceDict` (`backend/core/analysis.py`,
    `MAX_SLICE=150`, override via `settings 'syllable_max_slice'`): each of the
    three primitive checks (#C word-initial, C# word-final, syls count) has its
    groups cut into STABLE per-group slices of ≤MAX_SLICE words. A word's slice
    index is persisted per-word ('<check>-slice' annotation); removing a word
    shrinks its slice (no re-verify), only ADDING one (a moved misfit) re-verifies
    the target slice. Per-(group,slice) verify state is stored as synthetic group
    ids in the existing sentinel-profile status node.
  - **Dedicated driver** `SyllablePrep.maybeverifysyllables`/`verify_slice`
    (`backend/core/sorting_engine.py`), NOT maybesort: picks the next unverified
    slice, runs a single-page read-aloud verify (so the XWayland freeze is
    designed out), and on a flag-out applies the misfit rule — recompute the
    word's orthographic key for the target group, natural-sort it in if it
    matches else append to that group's last slice, and mark the target for
    re-verify. Count miscounts use a ±1 Shorter/Longer chooser
    (`SortPresenter.ask_syllable_count`).
  - **Task-1 board** `makeSyllableprepboard` (`frontend/ui_shell.py`): columns =
    groups (#C #V | C# V# | 1 2 3 …) under check headers, ragged rows = slices,
    live word counts, verified ✓ / bordered; click a cell to verify that slice.
  - **Task 2 (SORT) gated on Task 1.** `params.syllable_prep_complete(ps)` is the
    single predicate gating the board choice (prep board vs the kept 2-D
    macrogroup board) and `SortSyllables.runcheck` (prep vs the macrogroup profile
    sort). The shared engine's 'S' check set is now just the profile (ftype)
    check; the primitives are the prep driver's. `SortSyllables` gains
    `SyllablePrep` first in its MRO.

# Version 1.2.90
- syllable_sort_redesign STEP 1 (revert to the clean, segmental-matching
  baseline): removed verify-list PAGINATION (`frontend/sort_ui.py`
  `build_verify_layout` is now a single straight build — first screenful behind a
  wait, then the rest streams in; no pages, no `_render_page`/`_grid_nav`/
  `_verify_goto`, no per-page Wait) and collapsed the `verify()` page loop in
  `backend/core/sorting_engine.py` to a single `wait_window(verifycanary)`.
- Removed the global XWayland workarounds: the `UI.update`/`update_idletasks`
  Wayland no-op overrides and the `on_quit` `-fullscreen` release
  (`frontend/ui_tkinter.py`), the `notdonewarning` log-vs-popup split (back to the
  unconditional "Not Done!" popup, `backend/core/lexicon.py`), and the
  `USING_WAYLAND` flag. `utilities/display.py` is now a tombstone (safe to
  `git rm`). Kept the `faulthandler` SIGUSR1 dumper (`main.py`).
- Rationale: the freeze is designed out by keeping every verify list
  single-page/slice-bounded, not patched per-call-site. Segmental + tone are
  untouched (every removed line was inside a pagination or `USING_WAYLAND` block).
  Syllable's own dedicated prep/sort path lands in STEP 2/3.

# Version 1.2.76
- Release `-fullscreen` before a window is torn down (in `on_quit`), so the
  compositor (Wayland/mutter especially) restores keyboard focus to the window
  underneath promptly instead of leaving a gap where you can't type right after
  exiting a kiosk window. No-op for non-full-screen windows; cleanup()/maybewrite
  runs between the release and the destroy, giving the compositor a beat to act.

# Version 1.2.89
- syllable_sort_redesign.md: made "revert pagination + the global Wayland hacks
  back to the clean, segmental-matching baseline" the explicit STEP 1, so the
  rebuild starts from known-good code rather than the saga pile.

# Version 1.2.88
- Wrote docs/syllable_sort_redesign.md: the agreed two-task design (prep =
  3 checks × per-group stable slices ≤150, groups×slices board, dedicated
  `maybeverifysyllables`, misfit→last-slice; sort = macrogroup, gated, 2-D
  board) plus the plan to remove pagination, the cvt='S' branches, and the
  global Wayland hacks. Spec only — no behavior change.

# Version 1.2.87
- Make syllable verify behave like the WORKING segmental verify: SINGLE PAGE,
  no pagination. A sub-agent study of segmental vs syllable confirmed segmental
  verify works because its groups are slice-bounded (one CV-profile in one ps)
  and always fit one page, while syllable's primitive checks (#C/C#/syls) span
  the whole wordlist (~824 words) and are the ONLY verify that paginated — and
  the page TRANSITION is the XWayland freeze. Forcing npages=1 removes the
  transition entirely (the build/wait path is exactly the one segmental uses and
  that has always worked). A large group is tall (column setting manages that,
  as in every other sort) — no freeze. Next: undo the unnecessary global Wayland
  hacks (the update() guard etc.), per Kent.

# Version 1.2.86
- Verify pagination restructured into a page LOOP in verify(), so each page is
  built OUTSIDE its wait_window. Confirmed by logs: page 1 builds (after-ticks
  fire inside wait_window), but page 2 — whose build chain is started from a
  callback nested INSIDE wait_window — stalls at item 1 on XWayland (after-tick
  never wakes the loop). Fix: a nav button now ENDS its page's wait (destroys the
  page's canary) and records the target in `_verify_goto`; verify() then renders
  the next page via `_verify_render_page(page)` OUTSIDE the wait and waits again.
  Every page now builds the way page 1 did (which always worked). Single column,
  OK at the end of the list, per-page Wait on X11/Windows — all unchanged.

# Version 1.2.85
- Verify page transition (still froze after 1.2.84 — dump parked in wait_window,
  page-2 build not progressing): the Back/OK nav buttons live in the content that
  `_render` clears, so clicking one destroyed that very button mid-callback —
  which can wedge Tk event handling and explains why page 1 (no click) builds but
  page 2 (click → self-destroy) stalls. `_goto` now DEFERS `_render` to a fresh
  event-loop tick (`runwindow.after(1, _render)`) so the click returns first.
  Added per-page item-progress logging (item 1, then every 50) to tell a stall
  from a slow (~0.44s/item) build.

# Version 1.2.84
- Verify page transition: on WAYLAND ONLY, build each page IN PLACE (no
  `wait()`/withdraw, no per-page Wait dialog). Confirmed by faulthandler that the
  1.2.82 guard wasn't enough — page 2 still wedged in `wait_window` because the
  per-page Wait WITHDRAWS the mapped kiosk-full-screen run window, and that
  transition deadlocks under XWayland (page 1 builds because it starts
  withdrawn; page 2 withdraws a visible full-screen window). On Wayland the run
  window now stays mapped and drive_work fills items in place (update_idletasks
  skipped by the guard). X11/Windows keep the per-page Wait unchanged — users
  are unaffected, and the in-place build the user rejected globally is confined
  to the dev's Wayland session.

# Version 1.2.83
- Cleanup of the saga-era hacks now that the central Wayland guard (1.2.82)
  exists. Moved the flag to utilities/display.py (USING_WAYLAND) so backend can
  read it. Reverted the wait()/waitdone() `-fullscreen` toggle (it flickered on
  Windows and the guard supersedes it). Gated the on_quit `-fullscreen` release
  to Wayland only. Restored the "Not Done!" popup on X11/Windows (where it works,
  for the actual users) while logging it on Wayland (where the dialog can't show
  over kiosk full-screen). Restored ErrorNotice `-topmost` + the pre-wait_window
  repaint (now guarded → skipped on Wayland), and trimmed the verbose
  debug step-logging added during diagnosis. faulthandler SIGUSR1 dumper kept.

# Version 1.2.82
- Central XWayland guard (Kent's design): detect Wayland once (`USING_WAYLAND`,
  from `XDG_SESSION_TYPE`/`WAYLAND_DISPLAY`) and override `update()` /
  `update_idletasks()` on the `UI` base mixin to skip the synchronous X
  round-trip ON WAYLAND ONLY — the event loop repaints anyway. `UI` is in every
  widget/window's MRO before the tkinter base, so this one override neutralises
  every call site at once; X11/Windows behaviour is unchanged. Restored the
  per-site `update_idletasks()` calls I'd deleted during the saga (Progressbar.
  current, Wait creation) — they now run on X11 and are skipped centrally on
  Wayland. This should fix the verify page-transition freeze at the source (the
  wedge was the ScrollingFrame reconfigure's `update_idletasks` firing as items
  were added during the build).

# Version 1.2.81
- wayland_freeze_audit.md: recorded the decision to KEEP kiosk full-screen (it's
  for the Windows users' presentation; those users have no XWayland so they don't
  hit the freeze — it's a Linux/Wayland dev-environment issue). Recommendation:
  the dev develops/tests in an Xorg session (zero code, behaves like Windows);
  do NOT rewrite verify to build-in-place (rejected, unneeded); treat removing
  the synchronous-X calls as optional robustness, not an emergency.

# Version 1.2.80
- Added docs/wayland_freeze_audit.md: a full audit of the XWayland freeze (root
  cause = a synchronous X round-trip — update/update_idletasks/wait_window/grab —
  during a window-state transition deadlocks with mutter) and a principled,
  phased solution, replacing the per-site whack-a-mole. No code changed.

# Version 1.2.79
- Fixed the verify page-transition freeze at its actual source: `Progressbar.
  current()` called `self.update_idletasks()` after setting the value, and
  faulthandler caught the page 1→2 hang wedged in exactly that call (waitprogress
  → progress → current → update_idletasks). That synchronous X round-trip from a
  progress tick deadlocks under XWayland/mutter while the run window is
  backgrounded. Removed it — setting `['value']` updates the bar and the event
  loop repaints it. (The 1.2.76/1.2.78 `-fullscreen` releases were right but not
  sufficient; the progress tick was the real wedge.)

# Version 1.2.78
- `wait()` now releases `-fullscreen` before withdrawing the window to show the
  Wait dialog, and `waitdone()` restores it on reveal — the same fix as on_quit
  (1.2.76), applied to the backgrounding path. This is what should fix the verify
  page 1→2 transition freeze (the per-page Wait withdraws the kiosk-full-screen
  run window; withdrawing a full-screen window under XWayland/mutter is the
  freeze). Single-column pagination kept; no in-place build, no multi-column.

# Version 1.2.77
- REVERTED the 1.2.75 in-place page build (it broke the page 1→2 transition —
  empty content stuck on "loading page 2/5"). Restored the prior per-page build
  (first screenful behind the Wait, then stream). Multi-column auto-widening
  also rejected — columns stay the user's setting. The page-transition freeze
  under XWayland is still open, to be solved without in-place or multi-column.

# Version 1.2.75 (reverted in 1.2.77)
- Tried building each page in place to dodge the per-page withdraw; it broke the
  transition. Reverted.

# Version 1.2.74
- "Not Done!" freeze, unblock: stop popping the ErrorNotice Toplevel from
  `notdonewarning` — just log "NOT DONE: …". The dialog's `__init__` now runs to
  completion (logs through `wait_window returned`, wait=False), so creation is
  fine; the freeze is that the dialog can't get focus/input once the loop idles
  under XWayland+mutter+kiosk-full-screen — parent shown → full-screen blocks
  input; parent withdrawn → transient-parent gone so mutter won't focus it. A
  no-win for a standalone dialog in this context, and it was blocking exit. So
  log instead (FYI; maybesort returns right after anyway). TODO: surface the
  message in a window that already works (task chooser) rather than a dialog.

# Version 1.2.73
- "Not Done!" freeze, likely real cause (to verify): the app runs under
  GNOME/Wayland via XWayland, and BOTH the task window and run window are kiosk
  FULL-SCREEN (takekioskscreen). On XWayland/mutter a normal dialog shown over a
  full-screen window can't get input → app looks frozen (mainloop runs, nothing
  responds/paints — matches the dumps and the "not responsive" report). The
  verify Wait dialog works ONLY because wait() withdraws its full-screen parent
  before showing it. So ErrorNotice now does the same: withdraw the full-screen
  parent while the popup is up (re-adding the withdraw I wrongly removed in
  1.2.72), restore it via on_quit on dismiss. Kept non-modal. UNVERIFIED.

# Version 1.2.72
- "Not Done!" freeze: 4th dump showed it now wedged in `wait_window` (after
  update_idletasks was removed). Conclusion from all dumps: ANY blocking Tk call
  (update_idletasks, wait_window) deadlocks when this popup is shown MODALLY from
  the verify-teardown callback while its parent is withdrawn — and the Wait
  dialog that also froze is modal+withdrawn-parent too, whereas the verify Wait
  that WORKS is non-modal. So: (a) "Not Done!" is now non-modal (wait=False) —
  it's an FYI and maybesort returns right after it anyway; (b) ErrorNotice no
  longer withdraws its parent, so the popup shows over a mapped window with no
  withdrawn-master state to deadlock. faulthandler stays armed.

# Version 1.2.71
- "Not Done!" / Wait freeze: removed the deadlocking call itself. A 2nd
  faulthandler dump showed it STILL wedged in `update_idletasks` after -topmost
  was removed (so -topmost was NOT the cause — wrong again). The deadlocking
  call is `self.update_idletasks()` itself: a synchronous X round-trip that
  never returns on this WM when the popup's parent has just been withdrawn.
  Removed it from both ErrorNotice and the Wait window. ErrorNotice relies on
  the following `wait_window` (a real event loop) to map+paint; the Wait window
  relies on the running main loop. faulthandler stays armed — if it ever wedges
  in `wait_window`/`tkwait` instead, the next dump will say so.

# Version 1.2.70
- Removed `-topmost` from ErrorNotice + the Wait window. NOTE: did NOT fix the
  freeze (a later dump still showed `update_idletasks` wedged) — -topmost was
  not the cause. Kept the removal anyway (harmless; popups are active windows).

# Version 1.2.69
- Freeze diagnostic: faulthandler SIGUSR1 dump now writes to /tmp/azt_stacks.txt
  (a file) instead of stderr, so the stack is easy to retrieve after a hang.

# Version 1.2.68
- "Not Done!" freeze: stop guessing, get ground truth. Reverted 1.2.67's
  parent-withdraw removal — its premise ("non-withdrawn-parent popups don't
  hang") was false: the Wait window (non-withdrawn parent) also hangs. The two
  hanging cases share only being `-topmost` popups that deiconify + do a
  synchronous X round-trip, intermittently (a WM race). Added a faulthandler
  stack-dumper on SIGUSR1 (pid logged at startup) so the next hang dumps the
  exact blocked call — even from inside a C-level Tk/X call — instead of more
  theorizing. (Kept 1.2.67's duplicate-`wait_window` removal.)

# Version 1.2.67 (reverted into 1.2.68)
- Attempted parent-withdraw removal for the freeze; premise was wrong, reverted.

# Version 1.2.66
- Removed `self.lift()` + `self.focus_force()` from ErrorNotice (added in 1.2.57).
  NOTE: this did NOT fix the "Not Done!" freeze — it still hangs at the same
  `deiconified` log line. Worth removing anyway (they were my additions and add
  nothing over `-topmost`), but the freeze is a window-state problem, addressed
  in 1.2.67.

# Version 1.2.65
- Verify OK button keeps its affirmation text (oktext, e.g. "These are all
  consonant initial") with the page indicator appended, instead of being
  replaced by "OK — page x/y". Now "<oktext> — page x/y ▶" (and "…, finish" on
  the last page). That's the statement the user is confirming.

# Version 1.2.64
- Verify wait dialog: keep the prep message ("…verify all the words that are
  consonant initial") AND add the page indicator, instead of replacing the
  message with just "Loading page x/y". Now: "<prep>\n(loading page x/y)".

# Version 1.2.63
- Verify pagination: the OK button is back INSIDE the scroll content, at the end
  of the word list (where it belongs, as in every other sort) — along with the
  Back button — instead of in a separate bar outside the scroll frame. The
  completion sentinel stays separate so it survives per-page rebuilds.
- Replaced the title's "(N remaining)" (which counted verify groups — e.g.
  consonant- + vowel-initial = "2 remaining", useless to the reader) with
  "page x/y".
- "Not Done!" black box: split the post-deiconify steps into separately-logged
  calls (deiconified / lifted / focus_forced / updated). The 12:38 log stopped
  at `deiconify`, so the hang is in deiconify/lift/focus_force — the next run
  will name the exact call.

# Version 1.2.62
- Fixed crash loading SortSyllables directly: `SliceDict.count()` read raw
  `self._profile`, which (a) isn't set before slices are built and (b) never
  gets set for cvt='S' (which tracks its slice in `_S_macrogroup`). The except
  only caught KeyError; now catches AttributeError too → count 0 ("empty,
  because we're still building it"). Flagged in-code that a dedicated syllable
  SliceDict would remove this whole class of cvt='S' special-casing.

# Version 1.2.61
- Verify list is now PAGINATED (confirmed cause: content was 39,079px tall,
  past the ~32,767px X11 frame cap, so lower items couldn't render). Pages of
  VERIFY_PAGE_ITEMS (200) with a Back / "OK — page x/y" nav bar; the final
  page's OK finishes. Pagination fixes only the height — NOT the load — so each
  page keeps the "first screenful first" reveal: VERIFY_FIRST_REVEAL items build
  behind a "Loading page x/y" progress wait, the page reveals, then the rest of
  the page streams in behind it. (Total page count computed up front.)
- "Not Done!" black/frozen popup: still reproduces with the crash gone, so it is
  a SEPARATE pre-existing bug (NOT the TclError I wrongly blamed — that was a
  diagnostic I added in 1.2.57). The log stops inside `ErrorNotice.__init__`, so
  added step-by-step logging there (create / withdraw-parent / label / deiconify
  / update / wait_window) to pinpoint exactly which call blocks the event loop. the `notdonewarning`
  diagnostic called `rw.winfo_viewable()` on the run window, which is normally
  already DESTROYED by the time "Not Done!" fires (the user closed it). That
  raised `TclError: bad window path name`, which propagated out of the after()
  callback and out of `mainloop` — killing the event loop and freezing input.
  All Tk calls in `notdonewarning` are now guarded; confirmed via traceback
  (it pointed straight at lexicon.py:63). Also learned the run window is gone
  when the popup is born — relevant to the black-render investigation.

# Version 1.2.59
- Diagnosing the "buttons disappear on finish" regression. The double-place
  guard did NOT fire, so it isn't a double-build. Most likely cause: the content
  frame exceeds the ~32767px X11 window height limit (824 image-buttons at
  ~90px ≈ 74,000px), so items past the cap can't render. Added a warning that
  logs the content height when it crosses 32000px to confirm. Real fix is a
  design choice (multi-column / pagination / text-only for huge groups).

# Version 1.2.58
- Verify list is now ordered, not a random pile of words: alphabetical by the
  word form. For word-final tests (the 'C#' syllable primitive) it's sorted from
  the END of the word instead, so words with like endings group together.
  (`CheckParameters.is_word_final_check`; sort applied in `verify()`.)

# Version 1.2.57
- Verify-list load now uses the established `wait_and_drive_work` pattern (as in
  "Updating forms…"/"Updating annotations…") instead of a bespoke wait setup:
  - Progress bar now actually moves. It was scaled over the whole list (0→2%
    over the first 24 of 824, then the dialog vanished — looked frozen); it's
    now scaled over the FIRST PAGE, 0→100%.
  - The first page builds behind the wait via `wait_and_drive_work`; on
    completion drive_work fires `waitdone` (reveals the window) and an `on_done`
    callback streams the rest in behind it. The run window starts withdrawn, so
    `wait(prep, thenshow=True)` is set first so `waitdone` actually reveals it.
- End-of-build button overlap ("buttons on top of buttons at the top"):
  instrumented + hardened, root cause not yet confirmed. The reveal no longer
  fires `waitdone()`/`self.update()` from inside the running build generator
  (which forced a relayout mid-build); reveal is driven by drive_work's
  completion. Added a double-place guard that refuses to grid the same item
  index twice and logs if it ever happens — that log will tell us whether the
  overlap is a double-build (guard prevents it) or a canvas redraw artifact (to
  chase next).
- "Not Done!" popup: gave it a keyboard escape hatch (Return/Escape dismiss) and
  forced focus + a full repaint, so it can no longer hard-block when its content
  fails to paint (came up black, OK button invisible, killable only). Added a
  diagnostic logging the run-window wait/viewable state when it appears, to
  pin down the black-render root cause (prior drive_work-cancel fix missed it).

# Version 1.2.56
- Verify-list load, corrected approach. The 1.2.55 reflow theory was WRONG:
  suspending it changed nothing (211s vs 219s = noise), AND it suppressed the
  scroll-frame sizing so the first page never rendered until the very end ("no
  UI until streamed remaining"). The real per-item cost is `set_sense_illustration`
  loading + scaling a unique CAWL image from disk (~0.25s each → ~3.5 min for
  800 words) — irreducible without dropping/deferring images, which we don't
  want. So instead of fighting the total time, the load is now non-blocking:
  - The whole list builds via `drive_work` behind a `ui.Window.wait()` dialog
    that shows a prep message ("On the next page you will verify all the words
    that are <consonant initial / 2 syllables / …>") and a progress bar.
  - The window is revealed the moment the FIRST PAGE is built (a short,
    acknowledged wait), then the remaining items stream in behind the visible,
    usable page while the user reads aloud (which takes far longer than the
    load). `suspend_configure` is no longer used in the verify build.

# Version 1.2.54
- Fixed the "Not Done!" popup getting stuck (black/unresponsive, freezing input
  for ~1 min) when quitting during a big verify-list build. Root cause: the
  build's `drive_work` `after()` chain kept draining the event loop (hundreds of
  per-item illustration loads, back-to-back) even after the user quit, so the
  modal that came up next couldn't paint or take its OK click until the build
  finished. `drive_work` now tracks its pending `after` id and bails early if
  the window is exiting; `on_quit` and `notdonewarning` cancel any in-flight
  chain so quitting frees the loop immediately.

# Version 1.2.53
- Verify list load: build a full first page synchronously (FIRST_VERIFY_ROWS ×
  columns, min FIRST_VERIFY_MIN items) so the window opens with a complete,
  readable first screen, then stream the REST via drive_work in document order
  while the user reads (not scroll-visibility — no images popping in mid-read).
- Diagnostics: log how long `sensesinslicegroup` takes (pre-build item list) and
  how long the first page vs the streamed remainder take to build, so we can see
  exactly where the load time goes rather than guessing.

# Version 1.2.52
- Verify list: columns now follow the user's column setting (as in every other
  sort window), not the number of items in the group. Was
  `bc = buttoncolumns if len(items) >= min_to_multicolumn else 1`; now just the
  setting. `min_to_multicolumn` no longer gates the verify list.

# Version 1.2.51
- Verify list: fixed the items drawing on top of one another in a diagonal
  cascade (and bloating the scroll region). `build_verify_button` gridded the
  per-item button at `column=<the content-grid column>` *inside its own frame*
  instead of `column=0`, so in any multi-column verify each item's button was
  pushed right by its column index — making frames ever-wider, overlapping, and
  few-per-row (hence very tall). Now `column=0`. Pre-existing; bit any
  multi-column verify (multi-column is the user's setting, not group size).

# Version 1.2.50
- SortSyllables verify: fixed the scroll region being ~5× too tall (tiny
  scrollbar with only a few items). The OK "canary" was gridded at a huge
  sentinel row (10**6) to keep it after the progressively-built items, which
  inflated the ScrollingFrame's scrollregion. It's now created up front (so
  verify can still wait on it) but gridded right after the last item — at
  `content.nrows()` for macrosort, or at the end of the `drive_work` populate for
  the normal case.

# Version 1.2.49
- SortSyllables verify:
  - Clear text for the binary/count checks: title, OK button, and instructions
    now name the specific group — "These are all consonant initial" / "Click on
    any that are NOT consonant initial" / title "consonant initial" (via
    `params.syllable_group_name`) — instead of the nonsensical "…whole word
    syllable profile".
  - The verify item list is now built PROGRESSIVELY via `drive_work` instead of
    a synchronous loop, so a big group (e.g. all consonant-initial words —
    hundreds of illustration-laden widgets) paints/shows progress rather than
    freezing the UI for minutes. Item rows are indexed by placed-count.

# Version 1.2.48
- SortSyllables progress board:
  - Only shows once the three primitive checks (#C/C#/syls) are HUMAN-verified —
    macrogroup slices aren't defined by presort alone. Until then it's the
    big-icon board.
  - Zero-syllable counts are nonsense: `_syllable_count` now clamps to ≥1, and
    the presort normalises any existing `syls=0` annotation to `1`.
  - Hierarchical headers indicate the 3-D slice: row 0 = initial
    (consonant/vowel, spanning its finals), row 1 = final (consonant/vowel),
    rows = syllable count.

# Version 1.2.47
- SortSyllables: no sort page for the binary word-initial/word-final checks
  (they're closed classes — like we don't sort-page binaries elsewhere). The
  presort now buckets EVERY word, defaulting un-analyzable forms (capitalised,
  multi-word, out-of-alphabet — e.g. "Big Dipper") to consonant for both
  word-initial and word-final, and logs how many were defaulted so the consonant
  groups can be reviewed for outliers. `presortgroups` is now idempotent (fills
  only missing attributes, preserving confirmed ones, no early-return guard), so
  words a prior presort skipped get bucketed on the next run. The booleans go
  straight to verify (confirm by ear); syls stays an OPEN class (keeps its sort
  page / "Other" — `is_syllable_boolean_check` vs `is_syllable_primitive_check`),
  pending Kent's review of the integer field.

# Version 1.2.46
- SortSyllables board: when there are no macrogroups yet (the #C/C#/syls
  primitives haven't been sorted, so no `#C`/`C#`/`syls` annotations exist), the
  2-D board falls back to the big-icon `makenoboard()` instead of showing an
  empty grid under "Progress for {ps}" — matching the other no-data boards.

# Version 1.2.45
- SortSyllables cyclical redesign — flow, board, and escape hatch (ALL chunks
  now landed; first end-to-end run, untested by me — flow navigation across
  macrogroups and the escape-window layout are the likely iteration points).
  - maybesort: join is gated to the profile check only (the closed #C/C#/syls
    primitives never join); `getanotherskip` suppresses the "Other"/new-group
    button for those closed checks.
  - 2-D progress board: `makeSyllableprogresstable` rewritten to rows = syllable
    count × columns = Beg_End, cells = Beg+count+End macrogroup slices (word
    count, ✓/bordered/active); clicking sets the current slice. `update_active_cell`/
    `sync_active_cell` key on the macrogroup for 'S'.
  - Escape hatch: on the profile sort, a "doesn't belong in this group" button
    opens a window of one-axis moves (flip word-initial/word-final, Shorter,
    Longer) to a named destination cell, re-bucketing the word immediately.
    Configurable macrogroup→prose renderer added on `params`.

# Version 1.2.44
- SortSyllables cyclical redesign — slicing (still mid-migration; not runnable
  until the flow/board/escape land). The 'S' slice is the Beg+count+End
  macrogroup: `params` now owns the macrogroup helpers (`compose_macrogroup`,
  `parse_macrogroup`, `macrogroup_of_sense`, `is_syllable_primitive_check`,
  `SYLLABLE_SLICE_SENTINEL`), and `SliceDict.profile/senses/renewsenses/profiles`
  resolve the sentinel (whole wordlist, for the #C/C#/syls primitives) vs a
  macrogroup (the per-word-form profile check). `Syllables.macrogroup` delegates
  to params. Reverted the stale cvprofile-based 'S' branches in
  `getexamples`/`prefetch_examples` to the annotation path.

# Version 1.2.43
- SortSyllables cyclical redesign — engine data-model (first chunk of an
  all-or-nothing swap; **'S' is mid-migration and not runnable until the
  remaining chunks land** — see the build-status checklist in
  `docs/sort_syllables_design.md`). Choice B + slice = Beg+count+End:
  - 'S' checks are now `[#C (word-initial C/V), C# (word-final C/V), syls
    (syllable count), <current ftype = the whole-word profile>]` in
    `renewchecks`/`updatechecksbycvt`. First three run on the whole wordlist and
    compose into a macrogroup slice; the profile check runs within it.
  - `Syllables` mixin rewritten to the annotation channel (like segments): the
    three primitives are seeded by orthography from the computed profile (user
    judges by ear), `macrogroup()` composes Beg_syls_End on the fly, the
    four-attribute presort writes them, and the surface form is never rewritten.
  - Architecture LOCKED in the design doc (slice defs, four checks, annotation
    storage, presort, board, escape hatch) with a remaining-work checklist.
- Still TODO (next): macrogroup slicing (+ revert the stale cvprofile 'S'
  branches), the maybesort flow, the 2-D Beg_End×count board, and the
  escape-hatch window + prose renderer.

# Version 1.2.42
- Docs: `docs/sort_syllables_design.md` now specs the agreed **cyclical /
  orthogonal** syllable sort that supersedes the single whole-profile check.
  Four checks — word-initial (C/V), word-final (C/V), #syllables, and
  profile-within-macrogroup — where the first three are closed/determined
  classes (presort+verify, no "other"/no join) that compose (on the fly) into a
  macrogroup, and the fourth is the normal open create+join sort scoped to that
  small bucket. Includes the escape-hatch window (one-axis, immediate re-sort to
  a named destination cell), a configurable (Beg,Count,End)→prose renderer,
  per-attribute power-fault-tolerant persistence, and restoring a 2-D
  Beg_End×count progress board (retiring the 1-D one). No code yet.

# Version 1.2.41
- SortSyllables progress board: replace the hard-coded ⅓-screen budget (1.2.40)
  with `availablexy()` — the same space-measuring mechanism text wrapping uses.
  The board now fits as many uniform columns as the actually-available width
  (screen − siblings, e.g. the prose-status column) allows without overflowing,
  recomputed on `<Visibility>`/`<Configure>`. Adapts to status-frame layout
  changes and translations instead of a fixed fraction.

# Version 1.2.40
- SortSyllables progress board: the `<Configure>`-reflow from 1.2.39 collapsed
  to a single column — the leaderboard ScrollingFrame is `sticky=''`/content-
  sized, so the canvas reports one cell's width, not a viewport. Now wrap to a
  width BUDGET (≈⅓ screen) instead: columns = budget ÷ uniform-cell-width,
  growing as many rows as needed and scrolling vertically. Deterministic, no
  measurement race.

# Version 1.2.39
- SortSyllables progress board now fits the scroll window's width instead of a
  squarish grid: the ScrollingFrame scrolls vertically only, so cells use a
  uniform width (widest label) and the column count is computed from the canvas
  width and recomputed on `<Configure>` (reflow), wrapping to as many rows as
  needed. Still biggest-pile-first, same cell dressing.

# Version 1.2.38
- SortSyllables verify window: stop showing the raw check codes (lc/lx/pl/imp),
  which mean nothing to users, and drop the "sound" grammar that fits C/V/T but
  not whole-word profiles. For cvt='S' the verify title is now "for {prose}"
  (was "for 'lc' ({prose})"), the OK button is "These all have the same {prose}"
  (was "… ({lc})"), the instruction is "…click on any with a different {prose}."
  (no "sound"), and the item name is the cvt name ("Syllable Profile", was
  "lc Group"). C/V/T text is unchanged (their codes/grammar are correct).
- SortSyllables progress board: match the 2D leaderboard cell decorations —
  `padx/pady=0`, `ipadx/ipady=0`, and `highlightthickness=3` (was 4px pad and a
  thinner 2px border).

# Version 1.2.37
- SortSyllables: two distinct group orderings, as intended. The sort-INTO order
  (sort buttons / verify, via `StatusDict.order_groups`) stays shortest→longest;
  the progress board now orders profile piles **biggest→smallest** (by current
  count) so users can attack the largest first — matching how profiles are
  prioritised elsewhere.

# Version 1.2.36
- SortSyllables progress board: the 2D profile×check leaderboard crashed for
  cvt='S' (`KeyError: ('whole-word','lc')` — `activate_cell` looked up a cell
  that the sentinel profile / single check never created). Syllable sorting is
  one pile sorted into profile groups in a single dimension, so it now gets its
  own `StatusFrame.makeSyllableprogresstable`: a squarish grid (≈√n columns) of
  profile cells, each showing the profile and its current count, dressed like
  other sort cells — verified (✓) vs not (bordered) vs active (highlighted).
  Clicking a cell makes that profile the current group (verify can start there).
  `update_active_cell`/`sync_active_cell` now key on the profile group (not
  profile×check) when cvt='S'.

# Version 1.2.35
- SortSyllables tuning (from second run + Kent's direction):
  - One word type at a time: 'S' checks are now gated on `params.ftype()` (like
    other tasks) instead of cycling lc/lx/pl/imp. `updatechecksbycvt`/`renewchecks`
    compute the single current-ftype check for 'S' (kills the wasted empty-check
    passes).
  - Migration: old code wrote the machine profile into the plain
    `…-x-cvprofile` form (the form that's now user data). `ProfileAnalyzer`
    now migrates once, before analysis — if no `…-x-cvprofile_MT` (analysis)
    form exists anywhere for the ftype, the existing plain values are treated as
    old analysis: each is moved to its `_MT` form and the plain form is cleared
    (so stale values like the `CVC=VC=CVC` junk aren't mistaken for confirmed
    data). Idempotent (skips if any `_MT` form already exists).
  - Canonical group order for 'S': syllable profiles are presented
    shortest→longest then alphabetically (`StatusDict.order_groups`), since
    profiles are related to one another (unlike segment/tone groups, which stay
    plain-alphabetical). Replaces the rejected top-N idea — all groups are shown
    (any value may be wrong and is fixed by sorting), just ordered sensibly.
- Docs: CONTEXT.md flags the `S` overload (syllable cvt vs the C/V segment
  macrocategory placeholder vs the sonorant `sdict` class) — safe today, revisit
  if they ever share scope.

# Version 1.2.34
- SortSyllables fixes from first run:
  - The verify/sort window for cvt='S' showed nothing: the page icon / sort
    button resolved `image='S'`, but there was no `'S'` theme photo
    (`Found self.image='S'` error), breaking the window build. Renamed the
    dormant `'CV'` photo key ('ZA alone clear6.png', the syllable image — its
    only reader was the not-offered SortCV task) to `'S'`, so the syllable cvt
    now has its proper icon. Dropped the `'Word'` stopgap and the SortSyllables
    `dobuttonkwargs`/`pageicon` special-cases (the inherited paths now resolve
    `'S'` correctly).
  - Status-frame label "Looking at {profile}…" showed the 'S' sentinel profile
    ("whole-word"); for cvt='S' it now reads "Sorting whole words by syllable
    profile" instead.

# Version 1.2.33
- SortSyllables Phase 1: whole-word syllable-profile sorting, tone-modeled
  (relabel profile groups, never rewrite the surface form). Builds on 1.2.32.
  See `docs/sort_syllables_design.md`. NOT yet end-to-end-verified — expect a
  test-iterate pass (esp. the sort/verify/join UI for cvt='S').
  - New `Syllables(Senses)` mixin (lexicon.py): group = the syllable-profile
    string, stored in the sense's cvprofile field; `getitemgroup`/`setitemgroup`
    read/write `cvprofilevalue`; `updateformtoannotations`/`name_new_glyphs` are
    no-ops; `presortgroups` seeds groups from each sense's (machine-seeded)
    profile.
  - `SortSyllables` re-pointed to `(Sort, Syllables, Segments, Task)` — Syllables
    overrides win, Segments supplies shared helpers; dropped the broken
    `presortgroups`/`runcheck` overrides (uses the inherited `Sort.runcheck`).
  - Linchpin: `getprofileofsense` now writes the machine analysis to the
    `…-x-cvprofile_MT` form and keeps the plain (confirmed) form in sync only
    while it still equals the machine guess — preserving any user-confirmed
    value. Slicing keeps reading the plain form (now seed-or-confirmed).
  - `cvt='S'` plumbing: `maybesort` skips the glyph/macrosort phase for 'S';
    `updatesortingstatus` reads groups via `Syllables.getitemgroup`;
    `SliceDict.profile/senses/renewsenses` treat 'S' as a whole-ps slice with a
    sentinel profile; `ExampleDict.getexamples`/`prefetch_examples` fetch 'S'
    example words by cvprofile; `makecvtok` no longer resets 'S' to 'V'.
  - Bug fixes surfaced en route: `renewchecks` 'S' now uses the 'S' check codes
    (lc/lx/pl/imp) instead of all-cvt codes; added the missing `'S'` entry to
    `_cvts` (was a latent `KeyError`).
- Deferred (per Kent): Phase 2 (canonical segmenter / digraph inference /
  faithful reconstruction — the guuest cure) and `TranscribeSyllables` (renaming
  a group e.g. CVCC→CVC via the transcribe page). Design in the doc.

# Version 1.2.32
- Groundwork for syllable-profiles-as-data / `SortSyllables` (see
  `docs/sort_syllables_design.md`). Additive, zero behavior change so far:
  - `profilelang(analang, machine=True)` now appends the machine-transcription
    code (`_MT`), mirroring `tonelangname`/`phoneticlangname`; it previously
    ignored its `machine` flag. All existing callers pass the default.
  - Added `Sense.cvprofilemachinevalue(ftype, value)` to read/write the
    machine-analyzed profile in the `…-x-cvprofile_MT` form of the
    `cvprofile_<ftype>` field, alongside (never clobbering) the plain form that
    will hold the user-confirmed profile. No callers yet.
- Design doc `docs/sort_syllables_design.md` records the locked decisions, the
  storage model, the data-integrity LINCHPIN to review (machine→`_MT` write +
  confirmed-first slicing, same boot-overwrite class as the 1.2.14–1.2.20 saga),
  the tone-modeled sort flow, two pre-existing 'S' bugs found, and the Phase-2
  segmentation/digraph-inference design that needs sign-off before coding.

# Version 1.2.31
- Fix (scroll-frame mouse wheel going dead, intermittently, not motion-related):
  replaced the per-`ScrollingFrame` wheel claim/release scheme with a single
  app-wide dispatcher. The old design used a global `bind_all` wheel that each
  frame "claimed" via `<Enter>`/`<Leave>`/`<Map>`/`<Visibility>` plus a deferred,
  pointer-gated `_claim_wheel_if_pointer_inside`. Because scroll frames are built
  inside `with task.waiting(...)`, which *withdraws* the run window and shows a
  separate Wait window, the one-shot claim raced the withdraw/deiconify reveal:
  if `winfo_containing()` didn't resolve to the frame at that single instant
  (pointer elsewhere, or Wait window still overlapping, or position not settled),
  the frame never bound and — since the window reappears under a stationary
  pointer, firing no `<Enter>` — stayed dead until the user moved out and back in.
  Now `Root._on_global_mousewheel` is bound once (`bind_all`) on the real app
  root; on each wheel event it finds the widget under the pointer and scrolls the
  nearest enclosing `ScrollingFrame`. The target is decided at *scroll* time, so
  there is no reveal-timing dependence, no claim/release, and nested/multiple
  scroll frames work too (innermost under the pointer wins). Removed
  `initialize_wheel_bindings`, `_bound_to_mousewheel`, `_unbound_to_mousewheel`,
  `_on_mousewheel*`, `_pointer_inside`, `_bind_wheel_if_pointer_inside`, and
  `_claim_wheel_if_pointer_inside` from `ScrollingFrame`.

# Version 1.2.30
- Docs: corrected `docs/sorting_workflow.svg`. The "Done!" notice does not
  appear between Sort and Verify; `maybesort` flows straight from sorting into
  verification with no dialog. The single "Done!" notice ("...verified and
  distinct!", sorting_engine.py:500-506) fires only once nothing is left to
  sort/verify/join (after naming), and either announces "Moving on to the next
  check/profile!" — restarting the cycle on a new slice — or finishes back to
  the Task Chooser. Diagram now shows Sort→Verify direct and the end-of-cycle
  notice with both branches.

# Version 1.2.29
- Docs: added `docs/sorting_workflow.svg`, a screen-by-screen state diagram of
  the vowel sorting process. Shows every Run-Window screen and dialog the user
  can see — Task Chooser, Sort, "Done!" notice, Verify, Join, then the same
  machine on letters (Macrosort, Verify, Join) and Name/Transcribe — with the
  ↻ next-item self-loops, the rework back-edges (a differing word/group returns
  to sorting; "Go back and join"), the standalone TranscribeV entry, and the
  transient/modal overlays (wait, error notice, VCS commit, compare-letter
  picker).

# Version 1.2.28
- Docs: added `docs/workflow.svg`, a phased pipeline diagram of the user
  workflow from initial data collection through analysis and reporting to the
  two final products (alphabet chart PDF and alphabet comparison booklet PDF),
  with the LIFT lexicon shown as the central read/write store.

# Version 1.2.27
- Fix: adding a word back into a group did not pull that group out of 'done',
  so the user was told "all done" instead of being asked to re-verify the group
  that had changed. Repro: verify a word *out* of a group (the group stays
  verified for its remaining members), then sort that word back *into* the same
  group. `marksortgroup` calls `self.marksorted(sense, group,
  kwargs.get('updateverification'))` to unverify on a sort, but
  `kwargs.get('updateverification')` is `None` when the key is absent (the
  normal sorting case). That `None` reached `StatusDict.update()`, which
  compares `verified == False` exactly — and `None == False` is `False` in
  Python, so neither the add-to-done nor the remove-from-done branch ran. The
  group silently stayed in 'done'. The argument is now coerced with `bool(...)`
  so an ordinary sort always unverifies (the documented intent of that line),
  while `updateverification=True` callers are unaffected. Applies to tone and
  segmental sorts alike.

# Version 1.2.26
- Fix (root cause of the wraplength/off-screen-button bug from 1.2.24): an
  explicit `wraplength` was still being overwritten by the inherited root
  default (1344) even after the `restore_kwargs` guards, so text wrapped far too
  wide and pushed OK/Exit off-screen (e.g. the glyph example got 1344 instead of
  the passed 548). Widgets like `Button` reserve their kwargs *before*
  `super().__init__()` runs — `Button.__init__` calls `self.reserve_kwargs()`
  (popping `wraplength=548` into `self.wraplength`) and only then calls
  `super().__init__()`, which reaches `Childof.inherit()` and unconditionally did
  `setattr(self,'wraplength', parent.wraplength)`, clobbering the reserved 548
  with the parent's 1344. `inherit()` now treats the parent's values as defaults:
  it skips any attribute already set on the widget (`theme`, `wraplength`,
  `renderer`, `exitFlag`), so an explicitly-reserved value wins while the
  inherited default still applies when the widget passed none.

# Version 1.2.25
- Fix: exiting the "Name New Letter" page without naming all glyphs advanced
  the sort to the next activity instead of returning to the task. `maybesort`
  called `name_new_glyphs` and, when it returned unfinished (user exited / went
  back), fell through to the form-update + navigation block — which assumes all
  glyphs are named — and finalized anyway. It now returns to the task in that
  case. (Finishing all names still proceeds normally.)

# Version 1.2.24
- Fix: an explicit `wraplength` passed to a widget was silently overwritten by
  the inherited root default, so text wrapped far too wide and pushed buttons
  (OK, Exit) off-screen on several pages. `Childof.inherit()` copies the
  parent's `wraplength` onto the widget; `Text.restore_kwargs` then did
  `kwargs[k]=getattr(self,k)` unconditionally, clobbering the caller's
  `wraplength=…` with that inherited value before `__init__` read it (e.g. the
  glyph example got 1344 instead of 548). `restore_kwargs` now only re-injects a
  value that was actually reserved out of kwargs — it no longer overwrites a
  kwarg that's still explicitly present — so explicit `wraplength` wins while the
  inherited default still applies when none was given.

# Version 1.2.23
- Cleanup: removed the dead pre-helper segmental glyph-naming path from the
  Transcribe task, so `polygraphwarn` now lives in exactly one place
  (`GlyphTranscribeHelper`) instead of being duplicated. Segmental letter
  naming (TranscribeS/V/C and Sort.name_new_glyphs) already ran through the
  helper; the base `Transcribe` still carried the old implementation
  (`polygraphwarn`, `submitform`'s `cvt != 'T'` branch, and `TranscribeS.done`),
  reachable only via the unwired `TranscribeS.done`. Deleted those. Tone is
  unaffected: `Transcribe.submitform` keeps its tone branch verbatim, and
  `TranscribeT`'s own window/handlers are untouched.

# Version 1.2.22
- Fix: clicking OK on the "Name New Letter" page did nothing (logged
  "GlyphTranscribe done" then silently failed). `GlyphTranscribeHelper.submitform`
  called `polygraphwarn`, which delegated to `self.task.polygraphwarn` — but the
  helper is shared between the Transcribe task (which defines it) and
  `Sort.name_new_glyphs`, whose task (`SortV`/`SortC`) does not, so it raised
  `AttributeError` (swallowed by the Tk button callback). Made the helper's
  `polygraphwarn` self-contained, using its own `group`/`program`/`analang`/`cvt`,
  so it works regardless of which task drives it.

# Version 1.2.21
- Fix: text entry fields didn't track the `textvariable` passed to them, so any
  logic driven by that variable's trace never fired — most visibly the "Name
  New Letter" page, which stayed stuck on "Give a name for this group!" with OK
  disabled even after typing a name. `EntryField.__init__` ended with
  `super().post_tk_init()` instead of `self.post_tk_init()`, skipping
  `EntryField`'s own `post_tk_init` that re-binds the Entry to the caller's
  variable (needed because `reserve_kwargs` pops `textvariable` out of kwargs,
  leaving the Entry on a throwaway `StringVar`). Now calls `self.post_tk_init()`
  like every other widget, so the Entry tracks the caller's variable and its
  `<write>` traces fire on input.

# Version 1.2.20
- Fix (root cause of the persistence bugs): `ConfigManager` now loads its JSON
  on construction. Previously `get`/`set`/`save` all acted on an in-memory
  `self.data` that stayed empty until some caller happened to call `load()`, so
  a fresh/unloaded manager returned defaults on read and clobbered on-disk
  sibling keys on write. That root caused the migration and legacy-reader
  clobbers, and two more latent instances: `store_analang`
  (frontend/ui_shell.py — `save_all()` wrote empty domains over the template
  DB) and `file_parser` (`mgr.project.get('analang')` always returned None).
  Loading in `__init__` makes a fresh manager correct by default (reads see
  real data, writes merge). Verified migration still runs before the manager is
  built, so it sees migrated data.

# Version 1.2.19
- Fix: macrosort glyph-member buttons rendered blank (glyph name + check name,
  but no word/image), even though the example data was present. `make_sgbf`
  passes `gridwait=True` for the member frame, but `gridwait` was in neither
  `frameargs` nor `unbuttonargs`, so it leaked through `buttonkwargs()` into the
  member's child buttons. Each button then ran grid → grid_remove → (gridwait)
  return-without-restore, leaving the buttons permanently `grid_remove`d (frame
  reqwidth collapsed to 1px). Added `gridwait` to `unbuttonargs` so it's a
  frame-only kwarg and never reaches child buttons. (Only macrosort hit this;
  regular sort buttons aren't built with `gridwait`.)

# Version 1.2.18
- Fix (data loss): the legacy-reader clobber fixed for status in 1.2.15 also
  affected every other domain whose data is spread across attributes rather
  than a single same-named key — notably `alphabet` (`glyph_members`,
  `glyphdict`, `glyphs_distinguished`), plus `defaults`, `profiledata`,
  `soundsettings`. The 1.2.15 guard only skipped the legacy reader when the
  setting name was itself a JSON key (status/toneframes), so those other
  domains were still overwritten by their frozen legacy `.ini`/`.dat` on every
  load (e.g. glyph membership reset to the pre-migration alphabet). The guard
  now skips the legacy reader whenever the JSON domain supplied any content.

# Version 1.2.17
- Fix: mouse wheel again not scrolling a frame built under a stationary pointer
  — a regression from the 1.2.13 fix. The sort-button frame builds behind the
  "Sorting words..." wait dialog, so its `<Map>` fired while it was obscured/
  unsized and the pointer-inside check failed (and no `<Enter>` follows a still
  pointer). The wheel check now also runs on `<Visibility>` (frame revealed when
  the wait dialog closes) and is deferred to `after_idle` so geometry is settled
  before testing containment.

# Version 1.2.16
- Fix (data loss): the legacy→JSON settings migration ran on every boot and
  overwrote the JSON domain files with the frozen legacy `.dat`/`.ini`
  snapshot. Because the legacy files are never updated or removed, each boot
  reset every domain — most visibly the sort status — to its pre-migration
  state, wiping work saved since (e.g. CVC sort progress, while the older CV
  data in the legacy file survived). `MigrationManager.migrate()` now skips any
  domain whose JSON file already exists, making migration strictly one-time;
  once the app owns a domain's JSON it is authoritative.

# Version 1.2.15
- Fix (data loss): freshly-saved sorting status was wiped on the next boot. With
  status now persisting to the JSON `.data.json` domain (1.2.14), the legacy
  `.ini`/`.dat` reader in `loadsettingsfile` — intended only for migration —
  still ran after the JSON load and, for `status`/`toneframes`, rebuilt the
  object unconditionally from the frozen pre-migration legacy file, overwriting
  the JSON-loaded data. The next write then persisted that clobbered status, so
  CVC (and other) sort progress vanished every restart. The legacy reader is now
  skipped once the JSON domain has supplied the setting (migration still works
  when JSON has no data yet).

# Version 1.2.14
- Fix (data loss): sorting status was never written to disk, so all sort/verify
  progress — including the `presorted` flag — was lost on every reboot (which
  is why presorting re-ran on startup). `storesettingsfile` set `d` to the raw
  `program.status` object (keyed by cvt: V/C/T) for `status`/`toneframes`, then
  filtered `d`'s keys against the data domain's *attribute* names; nothing
  matched, so `domain_data` was empty and the save was silently skipped. The
  object is now wrapped under its attribute name (`{setting: obj}`) so it is
  actually persisted to the `.data.json` domain file and reloaded on boot.

# Version 1.2.13
- Fix: scrolling frames now respond to the mouse wheel when the pointer is
  already inside one at build time. The wheel binding is global (`bind_all`),
  and `ScrollingFrame` used to grab it unconditionally on construction, so
  whichever frame was built last captured the wheel regardless of pointer
  location — and a frame built under a stationary pointer (which fires no
  `<Enter>`) stayed unscrollable until the user left and re-entered it. The
  frame now claims the wheel on `<Map>` only when the pointer is actually
  inside it (matched by widget-path prefix, so child widgets count too).

# Version 1.2.12
- Perf: `maybesort` no longer re-derives the entire lexicon's sorting status on
  every pass. Only the current `(cvt, ps, profile)` slice can have changed
  since the last pass, and navigation reads sibling slices' flags from their
  last build, so it now rebuilds just the current slice via
  `reloadstatusdatabycvtpsprofile` (the current check rebuilt last, since
  `updatesortingstatus` overwrites the shared `_sensestosort`). This drops the
  per-pass whole-lexicon `annotation_values_by_ps_profile` walk, the redundant
  `load_ps_profiles` (already done once at LIFT load), and the global
  `clear_all_groups`.
- Perf: skip the status rebuild entirely when nothing was written since the
  last rebuild and the slice is unchanged. A `program.status_dirty` flag is set
  on every LIFT write (`maybewrite`) and cleared after the rebuild.

# Version 1.2.11
- Fix: "No groups to sort into!" with all groups empty after removing items
  from a group. `maybesort` kicked off the status reload via the asynchronous
  `drive_work` (which defers continuation through `after()`), then immediately
  read the status to sort. Because `reloadstatusdata` clears every group up
  front and only repopulates across its yields — and the cull cleanup runs
  only on completion — the sort read a freshly-blanked groups dict with stale
  `done`. Now `maybesort` drains the reload synchronously (and runs cleanup)
  before reading status, matching every other `reloadstatusdata` caller. The
  reload's heavy work is front-loaded, so async chunking gave no benefit here.

# Version 1.0.1
- Extracted syllable profile analysis from Settings into ProfileAnalyzer (backend/core/profiles.py)
- Deleted dead profiles.py at repo root
- Settings now delegates profile analysis to program.profiles; file persistence stays in Settings

# Version 1.0.0
- Alphabet chart up and printing
- ps-profile sort groups now sorting in to glyph/letter groups
- French translation 80% done
- Machine translations for some of Chinese, Spanish, and Arabic

# Version 0.9.11
- Finished parsing, though not always used. There is now a task to add and parse words in one step, and another to parse words added earlier.
- use of pictures (some from open clipart, first 110 from stability)

# Version 0.9.8
- initial Git integration should now be smooth, with initial clone and init, both for data and a flash drive
- demo database creation now in Choose LIFT database dialog. Can be specific to any gloss language in the stock CAWL.

# Version 0.9.7
- Substantial reworking of reports, which all now run in the background, and with improved initial placement of tables.
- Git integration works, both for updating A-Z+T and for language data. If your data is in a git repository, A-Z+T can make automatic commits for you, as well as pull and push from/to a respository on flash drive for sharing.

# Version 0.9.4
## Zulgo workshop tweaks
- lots of issues surrounding weird interface on their computer. For instance, the square consonant pushes everything off their screen, becausae of large space in buttons...
- A number of additions to make the update process smoother (now you can restart or retry, as appropriate, from the notification window)
- Multiple attempts to fix auto-reboot on Windows —sorry, nothing working yet.

# Version 0.9.3
  - Consonant and vowel sorting and renaming done, **except for renames that change Syllable profiles**
    - If you change syllable profiles (e.g., change o>ou, or iy>i), your results will not be predictable. I recommend if you do this, immediately restart A-Z+T, and redo a syllable profile analysis. I am working to account for this, but am not done yet.

# Version 0.9.2
- Windows batch file now
  - downloads and installs from USER/Downloads
  - gives user indication of download size in advance
  - makes unique names for repo and program link
- Fixed bug where functions called for objects created after wordlist collection, when wordlist collection wasn't done yet.
- If analang is guessed by filename, go back and tell lift object about it (at least for pss dict)
- Guide for OWLs used to FLEx

# Version 0.9.1
- SILCAWL now converts template ps to local values
- Set up ps sublcass to use '{}-infl-class'.format(self.kwargs['ps'] trait
- Set up morphtype trait URL
- Use button column variable to give up to three columns for sorting
- fixed bug leaving old sound file links
- removed MS Windows filename illegal characters from sound file names
- fixed scaling problem for smaller screens (had made big buttons)

# Version 0.9
- Rendering works now with Charis 6.0 font name, and more efficiently
- fixed screen scaling
- added new icons to better distinguish tasks
- fixed soundcard bug, removed buggy parameter option
- scroll sound card options, remove from default tasks
- remove wordy messages, move to tooltips
- improve logic for empty or missing data nodes
- added hg ignore functionality, with some defaults

# Version 0.8.9
- Complete rework of UI, now task oriented, with tasks divided by data collection and analysis functions.
- mercurial (if installed) now adds
  - ProfileData.dat
  - ToneFrames.dat
  - VerificationStatus.dat
- put UF fields in form/text nodes
- (non)-default report now more intuitive. If sort since last report, report runs again.
- User also has button to rerun analysis manually.
- Check for sound card now shows on every sound task beginning.

# Version 0.8.7
- changed .py config files to .ini and .dat, with clearer and simpler syntax. This should automatically migrate, but please let me know if it doesn't.
- should put those files into hg repository
- sendpraat should now be working, if installed
- massive changes under the hood:
  - ui.py extracted
  - new objects for examples, parameters
  - Hg should now track all .dat files (not .ini, per user)

# Version 0.8.6
- added referify data for current subgroup
- give warning if user is going to undo analysis regroupings
- mark a sensid to sort again without losing the sound file attached to it.
- major overhaul to LIFT urls, including class to generate them and catalog to store them
- major overhaul to framed data, including class to generate and catalog to store
- Added comparison group button for rename framed group window (to help with transcriptions)
- added actual groups by datapoint for non-default tone reports
- Reworked and multiple improvements to naming groups:
  - playable buttons
  - praat link to sound file
  - comparison button(s)
  - navigation buttons to continue through groups
- added interpretation of glottal stop into sdistinctions.
- added settings for interpretation of trigraphs and digraphs
- multiple fixes to segment interpretation settings
- set up mail of bug report, and links to webpage documentation

# Version 0.8.5
- reworked buttons and UI on transcription window
- comparison option for transcription window
- refresh group buttons now iterate through list (only random on first try)
- context menu to hide group names, in case they are distracting
- status table key and refresh/save settings option in upper left corner
- added rendering field where entries may contain combining characters that don't otherwise show up (in entry fields).
- Added SILCAWL (for later use)
- Prepped addition of XLP transforms
- Improved logic for next frame in transcription window, more sensible, less breaky
- added landscape option for sections, used when summary table is more than 6 columns wide
- split tables over seven columns wide into multiple tables
- call praat in recording buttonframe and in playable groupbutton (with tooltips)
- end cleanly on exit
- new FramedData and related classes
- fix problem with empty tone group node not presented for sorting

# Version 0.8.4
- added number of groups to XLP table
- non-default reports now end with 'mod' in filename
- added table of frame values for join UF groups window
- name groups doesn't crash on no groups selected; guesses
- redo group rename UI, add unsort button
- Various UI and documentation improvements
- Added button to rename groups which pulls a sense from that group (if the analyst decides it doesn't belong, to mark for resorting)

# Version 0.8.3
- fixed wav file link problem; now filename only in LIFT, relative link in reports.
- constrained search for language forms to analang (for multilingual dictionaries)
- don't crash on weird senseids
- fixed error on sound card not found to just not play (instead of crashing)
- fixed error of crash on PIL not installed.
- fixed error on trying data again
- updated documentation
- Made a simple output with characters that make invalid words (and the number of words impacted), so people can see them before noticing that words are just not there.
- Added context menu to make smaller font theme, for where that is helpful.
- set record button frame to notify user (and not make live buttons) where there is not audiolang set.
- only auto-add link if audiolang is specified.
- fixed window exit issues
- fixed numerous crashes on window exit
- removed final "\_" in sound filenames, left in legacy forms
- improved detection of screen resolution
- ratio of actual/expected resolution used to scale fonts an images, so it should look the (more or less) same whatever the resolution is.
- store font image renderings for later use, and use them
- XLP: don't print empty listWords, and don't print examples without at least one listWord
- autorefresh on playable buttons, if there is no sound file to play (up to the number of words to pick from, then give up)

# Version 0.8.2
- moved PyAudio functions to module, improved function
- Added glottal stop distinctions similar to Nasal distinctions
- Added redo status file (will not redo verification status, but will recover groups.)
    - Iterates across profilesbysense entries for ps and profile
    - looks into LIFT file for groups present
- added main_buggy.py and more logging in exception tracker
- cleaned up blipping on wait window
- checked on wait window in verifyT
- added ps and type buttons to all status boards
- fixed pl/imp not appearing on recording screen
- added field name (pl/imp) to filenames
- Every setting now has at least one button
- Context menu working correctly
- fixed but where CV type wouldn't set with ad hoc group as profile (it now resets/guesses the profile)
- New file name schema is working correctly field name (and type if name='field')
- new updatestatuslift, to add verification info to lift file, including removing on unverification, etc. Status is now stored in the LIFT file, for each sense.
- reduced writes to LIFT file, where AZT iterated across multiple changes
- fixed some syntax errors
- fixed MS Windows Unicode issue
- added user accessible switch between labels and buttons on the main screen (via context menu)
- cleaned up exiting fuctions
- fixed recording filename problems
- updated writing to lift file
- updated references to updatestatus with appropriate updatestatuslift calls
   - check name changes on groups and frame names
- removed "different" button from sort page, until at least one button is there
- added window to rename surface groups with a single button (with refresh) for the group, to play sound. This is a modification of the rename while verifying window (but with sound button, and next group button)
- fixed nbsp printing out as code point

# Version 0.8
- set up ad hoc groups to be more permanent:
    - saved to file
    - reloaded after reanalysis
- fixed scrolling window not wide enough in frame dialog
- numerous minor fixes
- set up on different input and output sound cards
- tone frames window now scrolls
- temporary fix for reconfigure scrolling window frame problem
- made function to add link if sound file is there (does nothing if link already there).
    - set up alternation, to accept either sound file nomenclature: w/wo location
- moved check analyses up to point of changing frame or profile (as appropriate), to keep from continuing to run it at other times.
- Set title in add/mod ad hoc group window to indicate if adding or modding
- split and regularized profilecountsValid and profilecountsValidwAdHoc.
- for Join window, don't ask if only one (avoid nonsensical "these are all different").
- Join window now removes second group from groups variable.
- included profile count in status table.
- make refresh example button only appear if there are at least two examples to pick from
- make status table into buttons for cells, which set profile and frame. (from CH)
- fixed sort logic to exit on exit (moved on), including recursive joinT funtions
- toneframetodo is now sensitive to the need to sort, as well as verification.
    - so "next frame" will give you the next frame with unsorted data, even if the known groups are all marked as verified.
- gettonegroups now removes groups from the list of verified groups, if they aren't actually in the lift file.
- observation that joinT page was (at least sometimes) removing an item (at least) from a group (at least), then giving the join page again, resulting in one less group in at least one case (sorting five elements over four groups). The tone report shows a group of [''] for that element, which is no longer in the join list of buttons.
    - This issue was caused by underspecificity in lift.rmexfields()
- Status table scrolls now
- made ps title a button to change ps
- made sort button in largest title case, with more padding
- highlight active cell (or row, if no frame)
- put refresh button on left (to not move)
- On 'finished sorting' window: include profile in title, rework next buttons
- Tooltips added in multiple locations

# Version 0.7
- truncate definitions after three words or before parentheses
- group names in status table now listed if any is non-integer; otherwise counts
- skip verification if zero or one item in group.
- kicked quit up to tone recording
- quit after ten scroll frame configurations
- For recording windows, added a "skip to next undone"
- basic report includes co-ocurrance tables
- fixed addframe button not showing up with longer defninitions (moved to left)
- removed underlining in table headers (to italics)
- Removed invalid from prioritized lists (of words to record, profiles to select)
- removed function which was creating duplicate references to the same recording
- Sortǃ Now selects frame and continues, rather than making user hit sort again.
- CV gui report now making its own runwindow (not trying to reuse old one)
- change frame menu should be like change profile
- prioritized group and frame ordering on tone output, according to new function for comparing sets of dictionaries.
    - similar groups in each axis should now be more or less together.
- Added explanation with explicit statement of structured ordering of groups to XLP output.
- moved self.tonegroups to self.status[self.type][self.ps][self.profile][self.name]['groups']
- No longer writing ui_lang.py on each run
- Breaking lines importing to XLP (for column headers)
- indicating progress verified/present and sorted status in main window (with !)
- dictionaries written to settings files are now pretty printed, for easier (human) reading.
- conversion to new status schema is now automatic, once any work is done on a ps-profile slice.
- Added logic for manual adjustment of tone groups
  - Separatee out logic to draft tone groups; you can now run tone report with or without analysis (without in advanced menu)
  - Allow creation of reports without auto drafting (in advanced menu)
  - document new tone groups functions

# Version 0.6.2
- Added new digraphs and trigraphs for idiosyncratic Chufie' orthography
- made crash logs zipped and ready to send
- reports now exclude final N if appropriate to settings.
- store and reuse examples for tone groups, assuming they remain relevant.
    - unless removed by refresh button
    - relevance is determined by presence in group to check, so all will be reset on ps-profile and/or frame change.
- frame names now included in recording filenames

### UI
- New buttons to allow user to ask for a different comparison word for tone group
    - These seem to be working
    - with icon
- added thin themed vertical scrollbars
- clarified instructions when there is no tone frame yet.
- Added distinction for recording of dictionary words:
    - Record button gives slice of data as indicated on the main screen (selected ps-profile)
    - Menu (Do/Recording/Record Dictionary words...) gives a page for each slice, starting with largest
- made troughs on scrollbar follow theme (at least on Linux)
- Improved join page visibility (button to label, not button recreated)
- Added wait window to page creation and page final processing functions
- Fixed/improved JoinT appearance and function
- Added window with error message if tone group rename function attempts to use a name already in use.
- windows now (mostly?) on the screen for MS Windows
- Fixed problem where skipping first word in sort created a group button
- reverse selection of examples for recording; they now appear most recent first.
- put recording buttons on the left, so they would never be pushed off the screen
- pulled words submenu, made ps and profile selection in main "change" menu
- New Add/Modify Ad Hoc sorting pages
    - multiple tweaks to form
- New (Advanced) window to set user option for number of tone examples to record (1,5,100, or 1000)
- Add Frame window now removed check session (on bottom) on any keypress, in any field on the page (this should keep users from changing the information in the fields, then submitting before those changes are checked.)
- buttons for next CV profile on done screens:
    - Recording: next CV profile  
    - Sorting: next Frame or new frame, next CV profile or ps   
- show count of batch numbers on recording screen (x/y), where y is the total number per group you asked for.
- now resolve automatically conflicts between profile and type of check.
    - ad hoc sort group definition/modification/selection sets check type to Tone.
    - Selecting anything other than Tone in the menu changes to a CV profile.

### Under the Hood
- fixed problem with empty examples and tonevalues
- improved calculation of column width inside scrolling frame (not great, but better)
- cleaned up exit on a couple functions
- set file write to a .part file, until finished, before overwriting lift
- fixed some internals that were causing crashes on particular data.
- fixed sound card settings window overwriting settings
- converted ww=Wait(parent) to window method (with self.ww=Wait(self))
- implemented double canary system, to allow for joinT to progress without destroying and remaking page
+ Added treatment of long vowels, similar to consonant distinctions/interpretation
    + lift.s['VV'] includes xx for x in lift.s['V'] (though there is no VV regex made, as it would be superfluous)
    + lift.s['Vː'] includes x:, and xː (if both ':' and 'ː' are in the database) for x in lift.s['V'].
    -? Long vowels (lift.s['Vː'] or VV>V) require the same V formulation on both Vs:
        - VdVd and dVdV are OK, but not dVVd and VddV.
    + lift.s['V'] includes lift.s['d'], if present
    + lift.s['VV'] is interpretable as V, VV, or Vː
    + These lists test what is actually there before making the regexs...
    + diacritics now in vowel variables
- add tone frame shouldn't add the frame anywhere until final check completed
- Add morpheme now allows skipping any gloss language, and doesn't create gloss or definition nodes, as appropriate.
- Function to remove extra example fields (added by Chorus?), running now on each load

# Version 0.6.1
- cleanup of exceptions on code running after windows closed.
- fixed logic in sort/verify/join and recording windows
- set logic to record just one (selected) slice of lexicon for lc/lx recordings
    - There is no setting for this yet, just quick to change the code
    - skip button only when doing multiple pages.
- Reworking of regex for V and C combinations
    - All bfj characters are now taken up by regexs


# Version 0.6
- fixed numerous report problems (should be mostly working now)
- Implemented XLingPaper export (at least beginning)
    - Organized data written to valid XLP XML file, which compiles to PDF in XXE.
    - data is written from entry lc/lx or sense examples, as appropriate
    - If a sound file exists, it is linked in XLP to the data form.
    - There are three report options:
        - Basic, for top ps-profile combos (Menu)
        - Just data as currently filtered (click on C/V "Sort" button)
        - Tone report, with examples (Menu)

## UI
- removed subcheck from main screen, at least until we are using it again

## Bug fixes
- Analysis lang is correctly treated on change (triggering reanalysis)

## Under the hood
- cleaned up report with close() method

# Version 0.5
- made help:about scroll
- fixed multiple sense glosses pulled into CV reports (now senses are sorted individually)
- added linebreaks to tone frame definition window, to keep it on the page

# prioritization
- We now guess analysis language (when unspecified) based on the one with the most appearances.
- User can now distinguish C,N,N#,G, and S as desired, NC and CG can be that, C or CC.

## UI
- Added page to instruct A-Z+T how to distinguish certain segment classes
- removed redo profile analysis from easy temptation
- Second gloss now showing for lc/lx recording page
- C/V check now just outputs filter by ps-profile; buttons no longer cause a crash.

### Under the Hood
- added variables for version number and program name, added to help:about
- Fixed bug where recording settings aren't being reused
- clean up code to organize functions in groups
- removed profile from recording names (so analysis changes don't require file name changes)
- set lc recordings to go on entries, not senses.
- variables to (potentially) distinguish nasals, glides, and other sonorants from other consonants
- Set menus to have 'Redo' set, for advanced things (incl. profile analysis - get this off the beaten path!)
- removed invalid check from profilecheck
- set up log to run by default, working in modules: seems to be working in MS Windows
- added check and warning for fr or en encoded lc/lx data (<10 examples)
- Fine grained logging works now (log.log(1,x))
- Added exceptions to logs, both from python and tkinter
- Analysis language guessing seems to work on various lift files.
- distinguished between segment type distinctions x[N,C,G,S] and segment combination x[CG,NC,NCG,NCS] distinctions, which are non boolean (as xy, as CC, or as C).
  - set up init init, check, and UI to work with new variables
- set getresults to use profile data, so it doesn't pick up <ch> = CC.

# Version 0.4
## new features:
### Functions
- New page ("Record dictionary words") to record and store links in one of the following (the last two have a number of possible names in field[@type={possible name}]; the tool currently guesses from a number of options, based on what is in the lift database):
    - lexical-unit/form[@lang=voicelang]/text
    - citation/form[@lang=voicelang]/text
    - {pluralname}/form[@lang=voicelang]/text
    - {imperativename}/form[@lang=voicelang]/text

### UI
- New `wait` window for longer tasks (reports, recording)
- Record button now works for different contexts, by `self.type`:
    - T: tone report (as was done before)
    - C,V: citation forms (new page? plural, other forms? all <form @lang/>)
- "Record dictionary words" page also accessible through record menu
- added check for parameters before making recording windows
- added button for next group in citation recording pages, distinct from exit.

### Bugs
- fixed problem with dot (.) in directory name

# Version 0.3.1
## new features:
### prioritization
- now assumes *every* setting for initial startup
    - check type should be `Vowel` until selected otherwise
    - assumes most populous ps-profile filter, until another is chosen.
        - new function to determine most populous syllable profile, with its ps
        - runs (and refreshes) with other syllable profiles on certain startups
        - selects most restrictive check available for profile (i.e. CVCV vowel checks start with V1=V2, not V1 or V2)
        - selects most populous V or C to check first
          - for CV checks, asks user which C and V (can't really guess that)
- C, V and profile selection dialogs now sorted by (included) counts, for the user to select based on frequency
    - counts are for valid data by ps, in the whole database

### reports

- CV report now takes most populous syllable profiles, and runs all checks
    - most restrictive (e.g., V1=V2) first
    - includes data only once per Sn (not in V1 or V2 if in V1=V2, nor in C1 or C2 if in C1=C2)
    - repeats data selected for by another Sn (C1 and V1 both is OK, for CV profile)

### Useability
- only question required on first open (for now) is C,V,CV, or T; everything else has an initial assumed value (though still changeable through the menus).
- `Record` button on main window, with unencombered icon
- `checkcheck` picks the most numerous profile, along with it's ps.
- label method to wrap on availablexy
- main window displays number of words in current ps-profile filter
- new (Advanced) menu option to redo syllable profile analysis
- Sort now ask user to affirm "This word is OK in this frame" on first word.
- added second gloss fields to tone frame addition window
- added second gloss (now by iso code) to getframeddata
- Trimmed down settings that are reset by another to a few essentials
    - checkcheck (flash) only when a setting is actually changed.
    - subcheck, if current values are appropriate to selected values.
- Join dialog is now more intuitive: one window with a single reset frame on select, instructions ask user to select two groups (as opposed to one, then the other). The first selection sets the first variable (as before), but leaves text in place, now as a label --other buttons remain.

## bug fixes:
### Useability

- make all file open options with `encoding='utf-8'`
- Fixed issue where `exit` sorted into last group; now just exits sorting.
- remove `lift_url.py` from repo
    - if non file found in `lift_url.py`, rejects and asks for a file.
    - if non-LIFT file is given, AZT quits on an exception, with console and UI message, and deletes `lift_url.py`.
- fixed C/V report
- fixed missing frames on tone checks --asks user to define a frame if none there.
- reworked buggy distinction of integer and named groups
- removed Noform Nogloss entries from recording screen
- resolved problem of leaving triage resulting in incorrect sorting
- now guesses:
    - UI language (via gloss, which is in turn guessed from database)
    - Analysis language
    - Gloss languages
- fixed problems with recording settings and file names

### UI
- Added icons to distinguish sort and verify pages, as well as join pages
- resolved `joinT` second window problem with the scrolling frame
- fixed scrolling frame problems
- removed (inappropriate) tone group designation from items on tone up report
- syllable profile and vowel windows now scroll

### Under the hood
- framed script now addresses both senses and examples
- fixed problems that arise from empty form (cut processing of those records)
- group name references now use int() instead of len()
- remove requirement for location key in tone frames
- gloss and form usage removed from self.`toneframes` references in `getframeddata` --now iso codes
- changed `lift.py` functions (`addexamplefields`,`addpronunciationfields`,
  `exampleisnotsameasnew`,`exampleissameasnew`) to work on iso codes
- Changed references to `getframeddata` with ['gloss'] or ['form'] to iso (['formatted'] and ['tonegroup'] OK)
- reworked `addexamplefields` and dependent functions to work with iso gloss/forms
- `self.toneframes` references with form and gloss converted to iso
- fixed references to self.name which iterate. They are now stored and reset (just `name` and `subcheck` in and wordsbypsprofilechecksubcheck, but also `type`, `ps`, and `profile` fixed in basicreport)
- added checks to checkcheck to zero out obsoleted settings (not valid for new setting)
- Fixed iteration reset problems for self.subcheck, other variables

# Version 0.3 (November 2020)
## language and search parameters
- logic to make appropriate assumptions
- UI menus for changing parameters
- current parameters indicated in UI (main window)

##Search basics
- data filtering by part of speech (grammatical category) and syllable profile
- basic search (no checks yet) for vowels
- basic search (no checks yet) for consonants
- basic search (no checks yet) for consonant-vowel combinations

## Tone frame checks:
- Tone frame definitions (in advanced menu, should be done by a linguist)
- Sort page to sort filtered data into groups (for a given tone frame)
- Verify page to remove items that don't belong in a given group
- Join page to combine groups with the same surface tone in that frame
    - this can be called from the Advanced menu at any time
- Iterative logic to Sort, Verify, and Join until all of the following are true (at the same time):
    - no words are unsorted (except for those intentionally skipped)
    - the user affirms that each group is just one thing
    - the user affirms that each group is distinct from other groups
- user can change to another frame, profile or part of speech at any time

## Recording
- Once some is done, recording is possible (via Advanced menu)
- dialog to set and test sound card and recording parameters
- Words selected by analyzed tone group, one per group, then a second, etc. up to 15 (currently)
- each context/frame where a word has been sorted is presented for recording
- recording is done by click-speak-release on a single `record` button.
- once recorded, the user is presented with buttons to play and/or redo the recording.

## Progress
- the type of search (Consonant, Vowel, Consonant-Vowel, or Tone) is indicated by an icon on the `Sort` button on the lower left of the main window.
- the right side of the main window shows a table of progress, once some sorting has been done
    - for one check type at a time (the current check type)
    - for one grammatical category at a time (the current grammatical category)
    - The table is organized by syllable profile v subgrouping
    - cell contents count the number of groups, if unnamed
    - cell contents list groups, if named
