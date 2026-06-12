# SortSyllables + syllable-profiles-as-data — design / scoping

Status: draft for Kent's review. Started 2026-06-10 (settings_rebuild).
Author: Claude (from a 3-subsystem code audit; see citations inline).

Background and the bug that triggered this: see memory
`syllable-profile-segmentation-ambiguity` (guest→guuest) and
`sort-syllables-profiles-as-data`. Short version: syllable profiles are
currently **analysis** (recomputed, segmentation re-derived independently by the
update path), so an ambiguous word (`gu` is a consonant, `ue` a vowel → `guest`
is `CVCC` two ways) gets re-segmented inconsistently and corrupted on update. The
fix is to make profiles **user-confirmed data**, and to model the confirming flow
on **tone** (relabel groups, never rewrite the surface form).

## Decisions (locked with Kent, 2026-06-10)

1. **Build SortSyllables end-to-end**, tone-modeled, hybrid (renamable
   profile-label groups *plus* a persisted confirmed segmentation for faithful
   reconstruction).
2. **Storage** (Kent's correction): field `type="cvprofile_lc"` (ftype-keyed):
   - form `lang="<analang>-x-cvprofile_MT"` → **machine-analyzed** profile
     (presort source). `_MT` = `backend.langtags.machine_transcription_code`.
   - form `lang="<analang>-x-cvprofile"` (plain) → **user-confirmed profile =
     the data / sorting result** (the truth).
3. **Seed/migrate** like the segmental presort: pre-group from the machine
   analysis so obvious cases are pre-sorted; the user only pulls out the ones
   that differ, then resorts. Users should not have to sort the obvious.

## Storage model + the LINCHPIN (needs Kent's eyes before it goes live)

Today (io_put/lift.py:560-572) the database builds `sensesbyps_profile` /
`ps_profiles` — i.e. **the slice definition for every segmental task** — from
`cvprofilevalue()`, which reads the plain `…-x-cvprofile` form. And
`ProfileAnalyzer.getprofileofsense` (profiles.py:263) **writes that same plain
form every boot**. So the plain form is currently machine-owned and boot-clobbered.

The spec makes the plain form *user-owned data*. Required changes:

- **L1.** `getprofileofsense` writes the machine profile to the **`_MT` form**
  (new `cvprofilemachinevalue`), and writes the plain form **only as a seed when
  it is empty** — never overwriting an existing confirmed value. *This is the
  same boot-overwrite hazard that caused the 1.2.14–1.2.20 data-loss fixes; it
  must be implemented with the "don't overwrite existing data" guard.*
- **L2.** Slicing (lift.py:560-572) reads the plain (confirmed) form, falling
  back to the `_MT` form when the plain form is empty. So unconfirmed senses
  still slice by the machine guess; confirmed senses slice by the user's truth.

**Why flagged:** L1+L2 change the slice source for *every* task, and re-tread the
exact data-loss bug pattern from earlier this session. Recommend implementing
behind a short verification pass (load a real lexicon, confirm slices unchanged
for unconfirmed data, confirm a confirmed profile survives a reboot).

## Storage primitives (safe, additive — implemented now)

- `LiftXML.profilelang(analang, machine=False)` (lift.py:4265) currently ignores
  its `machine` flag. Fix to append `_MT` when `machine=True`, mirroring
  `tonelangname`/`phoneticlangname` (lift.py:146-170). All existing callers pass
  the default, so behavior is preserved.
- Add `Sense.cvprofilemachinevalue(ftype='lc', value=None)` mirroring
  `cvprofilevalue` (lift.py:2994) but targeting the `_MT` form:
  `self.fieldvalue('cvprofile_'+ftype, profilelang(self.db.analang, machine=True), value=value)`.
  Read/write of `field`+`form` nodes auto-creates them (lift.py:2737-2752,
  2486-2487). Distinct from the legacy `cvprofile-user_lc` field
  (`cvprofileuservalue`, lift.py:2983) — that field is *not* used by this design.

## Tone-modeled sort flow (Phase 1 — buildable by mirroring tone)

The full sort→verify→join→rename machinery in `Categories`
(backend/core/categories.py) and `Sort` (sorting_engine.py) is cvt-agnostic and
reused as-is. Renaming a tone group never rewrites the surface form — it only
relabels status + verification + the group's data field
(`updatebygroupsense`/`rename_group`/`status.renamegroup`, with
`Tone.updateformtoannotations` = `pass`). Syllables must behave identically.

Pieces to add/change (gated on `cvt=='S'`, so T/segmental are untouched):

- **Add `Syllables(Senses)` mixin** (lexicon.py), parallel to `Tone` (lexicon.py:1682):
  - `getitemgroup(item, check)` → `item.cvprofilevalue(check)` (confirmed plain form)
  - `setitemgroup(item, check, group)` → `item.cvprofilevalue(check, group)`
  - `getsensesingroup(check, group)` → senses whose `cvprofilevalue(check)==group`
  - `updateformtoannotations` → **`pass`** (never rewrite the word)
  - `presortgroups` / `name_new_glyphs` → as needed (presort seeds groups; no glyph phase)
- **Re-point `SortSyllables`** (tasks.py:982) to `(Sort, Syllables, Task)` and make
  `presortgroups` a real generator that seeds **status groups** from
  `profiles.profilesbysense[ps]` (group = profile string), mirroring
  `Segments.presortgroups` (lexicon.py:124-163) via `presort`→`marksortgroup`.
  Delete the redundant `runcheck` override.
- **Add `TranscribeSyllables(Transcribe, Syllables)`** mirroring `TranscribeT`
  (tasks.py:1400) to let the user rename a group (CVCC→CVC). Reuses
  `submitform`/`switchgroups`/navigation as-is (`updateforms=True` is safe
  because `Syllables.updateformtoannotations` is a no-op).
- **`maybesort` (sorting_engine.py:402)** `if self.cvt != 'T':` → `not in ('T','S')`
  so 'S' skips the glyph/macrosort phase exactly like tone.
- **`updatesortingstatus` (settings/__init__.py:885)** route `cvt=='S'` to the
  syllable getter (`Syllables.getitemgroup`) instead of `Segments.getitemgroup`.
- **Sentinel profile for 'S' slices.** Status nodes are `[cvt][ps][profile][check]`
  and `slices.senses(ps,profile)` requires a real profile, but 'S' groups *across*
  profiles within a ps. Pin a sentinel profile for 'S' and make `slices.senses`
  (analysis.py:587) + `updatesortingstatus` (settings/__init__.py:880) resolve it
  to the full ps sense set (`slices._sensesbyps[ps]` / `db.sensesbyps[ps]`).

### Bugs found en route (real, pre-existing)

- **`renewchecks` 'S' branch** (analysis.py:1190) uses `cvchecknamesdict().keys()`
  (all cvts flattened) instead of the `_checknames['S']` codes
  (analysis_inputs.py:164-170). Should pull only the 'S' check codes.
- **`'S'` missing from `_cvts`** (analysis_inputs.py:353) → `cvtname`/`cvtdict['S']`
  `KeyError` on any 'S' path (e.g. renewchecks log analysis.py:1206). Add an
  `'S'` entry.

## Phase 2 — confirmed segmentation + digraph inference (NEEDS DESIGN SIGN-OFF)

This is the novel part (no existing code to mirror) and the part that actually
cures the guuest class of bug. Proposed, not to be built blind:

- **Segmentation from the confirmed profile.** Given a confirmed profile (e.g.
  `CVCC`) and the base monograph C/V classification, segment the word by matching
  maximal same-class letter-runs to the profile pattern; where a run is longer
  than the profile demands, the excess collapses into a digraph *within that run*
  (e.g. confirmed `CVCC` over `guest` with vowel-run `ue` ⇒ V1=`ue`; the profile
  count resolves `gu|e` vs `g|ue` without guessing). After a rename CVCC→CVC, the
  final `st` run collapses to one C ⇒ consonant digraph `st`.
- **Digraph inference.** Accumulate these forced collapses across all confirmed
  words to derive the legal digraph inventory, and surface/write it into the
  digraph settings (addresses "users ignore digraph settings").
- **Faithful reconstruction.** Replace the independent re-segmentation in
  `RegexDict.update` (rx.py:345) / `Segments.updateformtoannotations` with the
  single canonical segmenter driven by the confirmed profile, so updates never
  re-split a word differently than it was filed.
- **Open questions for Kent:** trigraphs/longer; ambiguity when a profile admits
  multiple boundary placements even with counts fixed; whether digraph inference
  is auto-applied or proposed-for-confirmation; interaction with the existing
  per-check segmental sort.

## Interim corruption guard (recommended, low-risk)

Independent of the above: in `Segments.updateformtoannotations`
(lexicon.py:189) or `RegexDict.update`, skip the rewrite when the form already
satisfies the group's membership regex (`buildregex`/`makeprofileforcheck`,
rx.py:609) — i.e. it is already a conformant member of `check=value`. That regex
segments correctly (it filed the word), so an already-conformant word (like
`guest` in `V1=ue`) is left untouched instead of being re-segmented and doubled.

## Staged build order

1. (done) Safe storage primitives: `profilelang(machine=)` fix +
   `cvprofilemachinevalue`. Plus `'S'` in `_cvts` (latent KeyError) and the
   `renewchecks` 'S' fix — all gated/additive.
2. `Syllables` mixin + re-point `SortSyllables` + generator `presortgroups`;
   `TranscribeSyllables`; the `cvt=='S'` branches; sentinel profile.
3. **LINCHPIN (review first):** machine→`_MT` write + confirmed-first slicing
   with `_MT` fallback (L1/L2), with the no-overwrite guard.
4. Phase 2 (design sign-off first): canonical segmenter, digraph inference,
   reconstruction; retire the interim guard once reconstruction is canonical.

---

# Cyclical / orthogonal syllable sort (AGREED DIRECTION, 2026-06-11)

This supersedes the "one 150-way whole-profile check" approach above (v1.2.33–
1.2.41). Built/landed pieces of that (cvt='S' storage split, `_MT` migration,
ftype-gating, the `Syllables` mixin, slice handling) are **reused**; what changes
is the **check model** and the progress board.

## Why

Asking "which of ~150 profiles is this word?" is hard even for a linguist, and it
forces the machine to resolve segmentation it can't (the `gu`/`ue` ambiguity that
caused guest→guuest). Instead, decompose the profile into orthogonal dimensions
that are each an EASY perceptual judgement, and compose them into manageable
buckets. **Principle (across the board): presort by orthography, the user judges
by ear** — so the ambiguous calls (esp. syllable count) are made by the human,
which is the correct authority.

Terminology note: use **word-initial / word-final** (Beg/End) in code and UI —
NOT "onset/coda" (those are syllable-internal parts).

## The four checks

Syllable sorting becomes FOUR sorts. The first three bucket each word into a
**macrogroup**; the fourth resolves the exact profile within that bucket. The
first three must complete before the fourth. They differ in group behaviour:

| Check | Class | Groups | "other"? | join? | Notes |
|---|---|---|---|---|---|
| word-initial | closed boolean | C, V | no | no | "different" ⇒ it's the other one |
| word-final | closed boolean | C, V | no | no | same |
| #syllables | determined integer | 1..n | no | no | not created/joined ad hoc; miscount fixed via Shorter/Longer |
| profile (within macrogroup) | open | the profiles in the cell | **yes** | **yes** | the normal segment-style sort, now scoped small: create as many as needed, join when oversplit |

So the same **(pre)sort → verify → join** machinery is used throughout, but the
first three **suppress the "other"/new-group button and the join phase** (closed
/ determined classes); only the fourth keeps full create+join (oversplit
recovery). Each of the first three gets a **dedicated verify pass** (esp. count —
an up-front by-ear pass catches systematic vowel-run miscounts better than
stumbling on them cell-by-cell).

Presort (orthography): word-initial = class of first letter; word-final = class
of last letter; #syllables = count of vowel-sequences separated by
consonant-sequences (vowel-run count); profile = the computed profile string.

Order of the first three: orthogonal ⇒ outcome-independent. Default to the two
booleans first (word-initial, word-final) then count; make it user-choosable
later only if feedback asks. Hard rule: all three before the profile sort.

## Macrogroup = composed on the fly

A word's macrogroup is `(Beg, Count, End)` **derived from the three stored
primitives at read time** — NOT stored as a composite field. Single source of
truth, nothing to desync, power-fault safe, and "Shorter/Longer/flip" just bump
one primitive and the cell follows. Cell membership, the 2-D board, and the
escape-hatch destinations all derive from this composition.

## Persistence (power-fault tolerant, like segments)

Store each of the four attributes per word as its own field/annotation
(value + per-dimension verification status), written **immediately on each sort
action** — exactly the segment model, where every click persists and a crash
loses at most the in-progress click. Four primitives → four small per-word
fields; macrogroup and progress board are derived (nothing composite to lose).

## UI

**Sort buttons** (within a macrogroup's profile sort): the per-profile group
buttons + **"other {macrogroup prose}"** (= a new profile in this cell; the
existing "Other {check}" mechanism) + **"not {macrogroup prose}"** (escape) +
**"skip"**. For the three closed/determined checks, the buttons are just the
fixed groups (C/V, or the counts) — no "other".

**Escape window** (opens on "not {macrogroup}"): correct exactly ONE dimension,
re-sorting the word immediately into a fully-determined destination cell whose
prose is shown on the button (so the user knows the result before clicking — no
pointless unsort/resort, correction scoped to one axis):
- "beginning is {~Beg}"  → `(~Beg, Count, End)`
- "end is {~End}"        → `(Beg, Count, ~End)`
- "Shorter"              → `(Beg, Count-1, End)`
- "Longer"               → `(Beg, Count+1, End)`
- "Cancel"

Booleans are complete (the opposite is the only option). For count, ±1 is the
90% case; add ±2 / pick-a-number later if feedback needs it.

**Configurable prose renderer.** `(Beg, Count, End)` → human prose must be
**configurable** (it appears on cell labels, escape buttons, instructions, and
will be tuned against real-user feedback). One renderer feeds all sites.

## Progress board

Restore a real **2-D table: `Beg_End {C_C, C_V, V_C, V_V}` × `count {1..n}`**,
each cell a SET of profiles (e.g. `C_C×2 = {CVCVC, CVCCVC, CCVCVC}`), one active,
sorted on click. This **retires the custom 1-D `makeSyllableprogresstable`**
(v1.2.36–1.2.41) in favour of (a variant of) the existing 2-D leaderboard.

## What changes vs. what's reused

- **Reuse:** cvt='S' plumbing — storage split + `_MT` migration, ftype-gating,
  the slice/sentinel handling, the `Syllables` mixin shape, (pre)sort/verify/join
  engine, the example/getexamples 'S' branch.
- **Change:** the 'S' **check set** from `[the whole profile]` to
  `[word-initial, word-final, #syllables, profile]`; gate "other"/join off for
  the first three; add the escape-hatch window; add the configurable prose
  renderer; replace the 1-D board with the 2-D Beg_End×count board.
- **Retire:** the 1-D `makeSyllableprogresstable`; the single whole-profile
  check semantics.

## Open / to-confirm

- Whether the fine profile sort still feeds Phase-2 reconstruction/digraph
  inference, or macrogroups suffice for downstream alphabet work.
- Count verify-"different" UX: reuse the Shorter/Longer move (vs. a re-count).

## LOCKED architecture (2026-06-11, choice B + slice clarification)

- **Slice:** C/V/T → `ps + profile`; **S → `Beg + count + End` (the
  macrogroup)**. The macrogroup is the 'S' analog of "profile".
- **Four checks** (in `_checknames['S']`, iterated in this order by
  updatechecksbycvt): `#C` (word-initial C/V), `C#` (word-final C/V), `syls`
  (syllable count) — run on the WHOLE wordlist (slice = ps, profile dimension =
  sentinel) — then the **profile check = the current ftype** (`lc`/`lx`/`pl`/
  `imp`, one at a time via `params.ftype()`), run WITHIN each macrogroup
  (profile dimension = the macrogroup, e.g. `C_2_C`). The first three are
  closed/determined (no "other", no join); the profile check is the open
  create+join sort, scoped small.
- **Storage:** all four on the **annotation channel** (like segments).
  Primitives `#C`/`C#`/`syls` annotations hold `C`/`V`/`C`/`V`/count; the profile
  annotation is named by the ftype and holds the profile string. Surface form is
  never rewritten (`updateformtoannotations` = no-op). Power-fault tolerant
  (written per action).
- **Presort** (by orthography, from the computed profile): `#C` = first symbol
  vowel?, `C#` = last symbol vowel?, `syls` = vowel-run count, profile = the
  computed string. User then verifies each by ear.
- **Macrogroup** composed on the fly from the three primitive annotations
  (`Syllables.macrogroup` → `'Beg_syls_End'`); the C_C/C{syls}C strings are
  SLICE-description prose (a configurable renderer), not checks.
- **Progress board:** 2-D `Beg_End × count`, each cell a macrogroup slice holding
  its profiles, biggest first; retires the 1-D board.
- **Escape hatch** (from the profile sort): one-axis move (flip Beg / flip End /
  Shorter / Longer) → re-slice into the named destination cell, immediate.

### Build status (this is an all-or-nothing swap; 'S' not runnable until all land)
- [x] `_checknames['S']` trimmed to real checks (Kent); checks =
  `[#C, C#, syls, ftype]` in renewchecks/updatechecksbycvt.
- [x] `Syllables` mixin on annotation channel: primitives compute, `macrogroup`,
  four-attribute presort, no-op form rewrite.
- [x] Slicing: macrogroup as the 'S' profile dimension. `params` owns the
  macrogroup helpers (`compose_macrogroup`/`parse_macrogroup`/
  `macrogroup_of_sense`/`is_syllable_primitive_check`/`SYLLABLE_SLICE_SENTINEL`);
  `SliceDict.profile/senses/renewsenses/profiles` resolve sentinel (whole
  wordlist, for the primitives) vs a macrogroup (the profile check). Reverted the
  stale cvprofile 'S' branches in `getexamples`/`prefetch_examples` to the
  annotation path.
- [ ] maybesort flow: three primitives (no join) → per-macrogroup profile sort
  (with join); closed-class gating (no "other") for the primitives.
- [ ] 2-D Beg_End×count board (replace `makeSyllableprogresstable`).
- [ ] Escape-hatch window + configurable macrogroup→prose renderer.
