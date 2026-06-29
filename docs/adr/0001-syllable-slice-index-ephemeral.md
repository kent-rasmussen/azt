# ADR 0001 — Syllable prep slice index is session-local, not persisted to LIFT

- Status: proposed (provisional)
- Date: 2026-06-23
- Scope: `azt/` (desktop) — syllable PREP task (Task 1)
- Author: drafted by Claude (AI agent), not yet reviewed/owned by the maintainer
- Provisional terminology: the **group / slice / verification (membership /
  confirmation / page-index)** vocabulary used here is not yet settled. These
  terms are still in flux across the syllable-sort code and docs; this ADR is
  subject to revision once they are pinned down, and wording here may not match
  the eventual canonical terms.

## Context

The syllable PREP task (Task 1) verifies three primitive checks over the whole
wordlist — `#C` (word-initial C/V), `C#` (word-final C/V), and `syls` (syllable
count). Each check's groups are cut into stable pages ("slices") of at most
`syllable_max_slice` words so each verify list is one modest, image-bearing page.

For each word we track three distinct things:

| Thing | Meaning | Where it lived (before) |
|---|---|---|
| **group membership** | e.g. `#C`=C — which group, auto-seeded by orthography and **correctable by the user** (misfit move) | `<annotation name="#C">` in the LIFT |
| **confirmation** | `['#C=C']` — this word is confirmed for this check | `lc primitive verification` field in the LIFT |
| **slice index** | which ≤cap page the word was packed into | `<annotation name="#C-slice">` in the LIFT |

The slice index was persisted in the LIFT alongside the other two. But it is the
odd one out: the user never decides a word's *page* — it is pure packing state
produced by `assign_slices`. Persisting it in the LIFT:

- put process/UX state into a linguistic interchange format (also flowing through
  azt-collab sync/merge as noise);
- made every `syllable_max_slice` change rewrite per-word annotations (a visible,
  if tolerable, lag);
- could disagree with the live UI (a default cap in the label vs. a different cap
  baked into the persisted slices).

Crucially, persisting the slice index buys **only** boundary stability →
minimal re-verify. It carries no durable fact: `done` is already re-derived in
`build()` from each word's primitive verification, and group membership is its
own annotation.

## Decision

Keep the slice index **session-local** (an in-memory dict on `SyllableSliceDict`,
`{check: {sense_id: idx}}`), never written to the LIFT.

- **Within a session:** boundaries stay stable — `assign_slices` only fills words
  that have no index yet, so add/remove/misfit-move behaves exactly as before
  (minimal re-verify).
- **Across a restart:** the index is gone and slices recompute deterministically
  from the durable LIFT membership. `assign_slices` mirrors `move_misfit`'s
  placement: words whose **spelling** agrees with the group sort in naturally
  (by whole-word key); by-ear-only members (spelling implies another group, or
  unanalysable) go to the **end**, clustering in the last slice(s). So the rebuild
  reproduces the *interactive* layout — including the exception cohort — from
  durable data alone (membership annotation + the spelling-derived value), not a
  flat alphabetisation. Same inputs → same boundaries; they differ only when words
  changed between sessions. The spelling-derived value reads the **plain**
  `cvprofile` form (matching presort), not the `_MT` machine form.

Membership (`<check>` annotation) and confirmation (primitive verification field)
remain durable in the LIFT — those are the real facts. The status node
(`done`/`groups`/`slice_cap`) stays a cache in `data.json`, re-derived by `build()`.

The `syllable_max_slice` setting **is** persisted (it is a real user preference):
registered in `settings['defaults']['attributes']` so it round-trips through the
`ui` domain JSON like `buttoncolumns`. Default cap is **50**.

## Consequences

- LIFT holds only enduring facts; `build()` writes no LIFT data.
- Changing words/page is pure in-memory work + a small `data.json` node write —
  the cap-change lag is gone.
- The prep board must build to render: `_prep_board_data` now calls `build()` so
  the board repopulates from persisted membership after a restart (it would
  otherwise be empty until prep was re-run). `build()` only writes `data.json`
  when the node cache actually changed, so render-path calls are cheap.
- **Residual minor difference:** because `assign_slices` mirrors `move_misfit`, a
  by-ear misfit still lands in the last slice after a restart, so the exception
  cohort is preserved — not folded into a mid-list page. The only divergence left:
  a misfit moved interactively into a specific *existing* slice via the bracketing
  rule may, on rebuild, land in a different in-group slice if its spelling agrees
  with the group (it sorts in naturally). Nothing is lost (confirmations are
  durable); at most a slice's membership shifts slightly.
- Legacy `<check>-slice` annotations in existing LIFT files are now ignored (not
  read, not written). They are harmless; we do not actively strip them.
