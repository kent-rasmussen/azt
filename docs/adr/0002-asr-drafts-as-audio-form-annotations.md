# ADR 0002 — ASR transcription drafts are LIFT annotations on the audio form

- Status: proposed (provisional)
- Date: 2026-06-24
- Scope: `azt/` (desktop) — record / bulk-ASR / transcription-select workflow
- Author: drafted by Claude (AI agent), not yet reviewed/owned by the maintainer
- Related: [design doc](../asr_bulk_transcription_design.md); machine-form
  precedent in `Sense.cvprofilemachinevalue` (`io_put/lift.py`); selection UI in
  `WordCollectionwRecordings.show_drafts` (`tasks/tasks.py`).

## Context

Recording audio, getting ASR transcription drafts, and selecting/correcting a
transcription are today fused into one interaction (`WordCollectionwRecordings`
+ `RecordnTranscribeButtonFrame`): the moment a recording stops, ASR runs
**synchronously on the Tk main thread** (`get_transcriptions`), the resulting
candidates are turned into selection buttons (`show_drafts`), and the user
clicks one. The ASR candidate dicts (`transcriptions`, `transcriptions_ipa`,
`tone_melody`) live only on the in-memory recorder for the session and are
**never persisted** — only the *selected* IPA/tone reach LIFT (via
`store_phonetic`/`store_tone`, into the `-x-phonetic`/`-x-tone` machine forms).

We want to break this into three stages that can run on **different days and
machines**, communicating only through the data repository (LIFT file + audio):

1. **Record** (done) — writes the audio file and its `<analang>-x-audio` form.
2. **Bulk ASR** — a non-interactive *specialisation* batch over every recorded
   form, run once on a competent machine.
3. **Select & correct** — the existing button UI, but built from stored drafts
   with no per-word ASR lag.

For the stages to decouple, the ASR candidates produced in stage 2 must become
**durable, machine-portable data** that stage 3 reads. There is no existing
"candidate pool" structure in the LIFT model; alternatives elsewhere use the
`<annotation name=… value=…/>` child of a `<form>`, and machine-computed values
(tone, phonetic, cvprofile) sit in parallel `…-x-MT` forms alongside the
user-confirmed value.

## Decision

Persist each ASR draft as an `<annotation>` child of the **`<analang>-x-audio`
form** — the form that already holds the recorded audio filename, i.e. the thing
the transcription annotates. One annotation per model/lane, keyed by ASR repo:

```xml
<form lang="gnd-x-audio">
  <text>dive.wav</text>
  <annotation name="allosaurus"     value="dìve"/>   <!-- transcription -->
  <annotation name="ipa-neurlang"   value="diːve"/>  <!-- IPA lane -->
  <annotation name="tone-katyayego" value="HL"/>      <!-- tone lane -->
  <annotation name="md5"            value="<md5 of dive.wav>"/>
</form>
```

Naming (the ASR-annotation namespace on this form):

- `{repo}` — the postprocessed transcription from that model.
- `ipa-{repo}` — the IPA transcription from that model (a model may yield both).
- `tone-{repo}` — the tone melody from that model (≥1; future-proof, and lets the
  selector filter tone in/out while keeping its origin explicit).
- `md5` — fingerprint of the audio file the drafts describe.

Rationale for the audio form (not a dedicated field, not the `-x-MT` forms):

- It **is** what the drafts annotate; co-locating draft + audio is the natural
  model and survives the audio link moving between citation/lexical/example.
- Transcription text is **writing-system-agnostic** here — the annotation
  carries no `lang`, so we don't falsely imply an orthography; provenance is the
  repo name.
- The annotation name→value shape matches the ASR output dicts (`{repo: text}`)
  one-to-one, reusing `Form.annotationvalue` / `annotationvaluedict`.

**No separate provenance/version record.** The presence of a `{repo}` annotation
*is* the record that that model has run on this file. Re-running stage 2 with
more models/languages just fills gaps; an interrupted run resumes the same way.

**Staleness via `md5`.** "Latest audio file wins": the drafts always describe the
*current* audio. Before drafting, compute the file's md5; if it differs from the
stored `md5` annotation (or none is stored — e.g. a re-recording with the same
filename), **wipe this form's ASR annotations and redraft**, then write the new
`md5`. The live record→transcribe path writes through the same helper, so the
LIFT always holds the latest result for the current audio.

**Wipe scope is doubly bounded:** only annotation names in the ASR namespace
(`{repo}`, `ipa-{repo}`, `tone-{repo}`, `md5`) **and** only within the
`<analang>-x-audio` form node. Annotations on any other form (e.g. revert-history
`0,1,2` on the analang data form) are a different XML node and are never touched.

The existing `store_phonetic`/`store_tone` (selected value → `-x-phonetic`/
`-x-tone` machine forms) are **retained**: those are the *accepted* draft (data);
the annotations are the *candidate set* (provenance/options).

## Consequences

- Stage 2 and stage 3 share no in-memory state — only LIFT + audio. Either can
  run alone, on any machine, in any order after recording. The per-word ASR lag
  moves out of selection entirely (stage 3 reads stored drafts, runs no model).
- A symmetric helper pair carries the contract: `persist_drafts(audio_node, …)`
  (written by both the live path and the bulk batch) and `load_drafts(audio_node)`
  (read by the selector to hydrate the existing `show_drafts` button flow).
- **Collab churn:** at project scale (~1700 entries × up to ~8 models/langs) this
  adds 10k+ small annotation nodes, written incrementally and rewritten on
  re-record. Whether the `azt-collab` merge path diffs these at sub-element
  granularity (vs blob-merging a touched form/entry) is filed for investigation
  in `azt-collab/azt_collab_client/NOTES_TO_DAEMON.md`. Marking ASR annotations
  as machine-regenerable (prefer-latest on conflict) is a candidate policy.
- **Selector dedup:** many models/languages produce identical strings. The
  selector dedups candidates by *value* while retaining `value → [repos]`, orders
  buttons **most-frequent-first** (consensus on top), and on click tallies *every*
  contributing repo (`asr_repo_tally`) so model-preference stats stay honest.
- Legacy LIFT files simply have no ASR annotations until stage 2 runs; the
  selector falls back to manual entry (always available).
