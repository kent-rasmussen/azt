# ADR 0003 — Every sort carries two values per item (sort value + verification), and the status board shows them the same way across all sort types

- Status: proposed
- Date: 2026-07-03
- Scope: `azt/` (desktop) — the shared sort engine and status board across ALL
  sort types: segmental (C/V), tone, syllable (profile within macrogroup), and
  macrosort (sort-groups → alphabet glyphs / language categories)
- Author: drafted by Claude (AI agent) with Kent; codifies a contract that was
  implicit in the segmental/tone code and was violated by the syllable rebuild.

## Context

A-Z+T has several sort types that all ride one sort/verify/join engine. They
looked different enough that the syllable rework (2026-06) re-implemented parts
of the status model on its own key — and diverged from the others in a way that
only surfaced once real data accumulated. This ADR pins down the contract they
**all** share, so future sort types conform and reviewers can spot divergence.

### The unifying model

Every sort type sorts **items** into **groups**. The *item* is whatever that sort
operates on:

| Sort type | Item | Group |
|---|---|---|
| Segmental (C/V) | a word (sense) | a segment group (e.g. `V1`=2) |
| Tone | a word (sense) | a tone melody |
| Syllable profile | a word (sense) | a CV-profile group, within a macrogroup |
| **Macrosort** | **a sorted group of words** | an alphabet glyph / language category |

For **every** item there are **two** distinct pieces of state, both meaningful
per-item and aggregated per-group:

1. **Sort value (membership)** — *which group is this item in?* Set when the item
   is sorted. An item with no sort value is **unsorted**.
2. **Verification of that sort value** — *has this item's membership been
   confirmed (by ear / by the user)?* Set only on an explicit verify. Membership
   can exist without verification (the normal state right after sorting).

Aggregated to the group:

- A group **exists** once it has ≥1 member (item with that sort value).
- A group is **done / verified** iff it has members AND **every** member's sort
  value is verified. Sorting one new (unverified) item into a done group
  un-verifies it — that item lacks the verification.

Where the two live in LIFT differs by sort type, but the *shape* is identical:

| Sort type | Sort value (membership) | Verification |
|---|---|---|
| Segmental / tone | `lc` annotation `<check>=<group>` | per-member code `<check>=<group>` in the `<profile> … verification` field |
| Syllable profile | `lc` annotation = the profile group | the plain `field[@type='cvprofile_lc']/form[@lang='…-x-cvprofile']` matching the annotation |
| Macrosort | the group's glyph assignment | glyph verification state |

`done` is **derived** from those durable facts (computed from LIFT on reload —
`verified_groups_by_ps_profile` for segmental; `rebuild_syllable_profile_done`
for syllable), never trusted from a stale status-file cache. See ADR 0001 for the
matching rule that the slice/page index is *not* durable.

### The two UI indicators (must mean the same thing on every board)

The status board (`StatusFrame`) must present the two values identically for all
sort types, so a user learns one vocabulary:

- **White border on a cell** = the cell contains **unsorted items** (items with
  no sort value). Clicking the cell + `Sort!` presents those items **to sort**.
  (Segmental: driven by the node's `tosort`. Syllable: derived fresh from members
  with no `lc` annotation.)
- **A trailing `+` on a listed group** = that group is **verified**. Its absence
  = the group has members still **to verify**; they are presented for
  verification after all items in the cell are sorted.

So "unsorted" and "unverified" are **different** states with **different**
indicators. A fully green cell = every item sorted *and* every group verified.

## Decision

1. Treat sort value and verification as two separate per-item facts for every
   sort type, both aggregated to the group as above. New sort types must map onto
   this contract rather than invent their own status shape.
2. The status board shows exactly two indicators — **white border = unsorted
   items present**, **`+` = group verified** — with the same meaning on every
   board.
3. `done` is derived per-group by **membership**: a group is done iff every item
   *whose sort value is that group* is verified. `done` and `groups` are computed
   on the **same key** (membership), so `groups − done` = "groups still to
   verify" is always correct.

## Consequences

- **Regression fixed (the reason for this ADR).** The syllable rework had:
  - the board's white border keyed to *verification* (`groups ⊆ done`) instead of
    *unsorted items* — wrong indicator; and
  - `done`/`groups` computed on the **`cvprofilevalue` bucket** instead of the
    **`lc` annotation membership**.

  Because `maybesort` reads `groups` (annotation-derived) minus `done`
  (cvprofile-bucket-derived), the two used different keys: a word **sorted**
  (annotation=G) but **not yet verified** (no matching cvprofile) contributed its
  group G to `groups` while sitting in the `'—'` cvprofile bucket, so if G was
  already in `done` (its *verified* members exist) the group looked complete →
  "all done" → the sort advanced past the unverified word. The board still drew a
  white border (its own, verification-based rule), so the cell and the engine
  disagreed. This was invisible in early testing and only appeared once data had
  a done group that later gained an unverified member. Fixed by moving both the
  board indicators and `rebuild_syllable_profile_done` onto the membership key
  (this ADR's rule 3), matching segmental.

- Board and engine can no longer disagree about a cell: both read a
  membership-keyed node, and the white border is derived from the same membership
  facts.

- New sort types get a checklist: define the item, where its sort value and
  verification live, and confirm the board's two indicators light up per this
  contract. A board that borders on "unverified" or lists groups on a key other
  than membership is a regression against this ADR.

- Macrosort already conforms (item = sort-group, verification = glyph state); it
  is included here so the contract is understood as sort-type-agnostic, not a
  word-only rule.
