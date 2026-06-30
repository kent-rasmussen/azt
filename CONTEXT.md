# AZT Desktop

The desktop AZT app — sort, transcribe, record, and analyze lexical
data from LIFT XML lexicons. Originating member of the suite; owns
the LIFT data-model vocabulary that other sub-repos consume.

## Language

**analang**:
The language being analyzed — the language documented in the
lexicon. Lexical entries' headwords and forms are IN the analang.
A LIFT project has at least one.
_Avoid_: vernlang, vernacular language, target language

**glosslang**:
A language a gloss is written in (e.g. English, French). A project
may have multiple glosslangs.
_Avoid_: analysis language, definition language

**audiolang**:
A BCP-47 tag flagging an audio attachment in LIFT. Equals the base
extended code (with any private-use dialect subtags) plus `-x-audio`
— for example `en-US-x-kent-x-audio` is the audio attachment for the
`x-kent` dialect of US English. Used in `<form lang="...">` elements
under `<citation>` (and as a fallback under `<lexical-unit>`).
_Avoid_: audio code, audio language

**autonym**:
A language's name as written in that language itself (e.g. "Deutsch"
for German, "Français" for French). Distinct from the user-preferred
display name.

**display name** (of a language):
The name the user wants to use for a language in this project's UI.
May be the autonym, an English name, or something else entirely
(e.g. a local project-specific name). Stored per-project; settable
on any of analang / glosslang / ui_language. `ui_language` itself is
owned by [azt-collab](../azt-collab/CONTEXT.md).

## Sorting (data collection)

The whole app collects one kind of data: **how words sound, judged by the
ear of people who speak the language.** Every step is that, with a single
exception — **presort**.

**tier**:
The phonological dimension a sort works in — **segment**, **tone**, or
**syllable-profile** — mirroring the (autosegmental) tiers of a spoken
word. The segment tier subdivides into the **C** (consonant) and **V**
(vowel) tiers. In code this is the `cvt` parameter (`C`/`V`/`T`/`S`);
`tier` is the domain term for it. (Praat's TextGrid "tiers" in
`praatfns.py` are a *different* concept — acoustic annotation layers — so
the shared word is a mild overlap, not a real collision.)
_Avoid_: cvt (code-only label).

**presort**:
The one machine step: a provisional grouping guessed from a word's
orthography, to spare the speaker obvious work. The sole exception to "all
sort data comes from the ear." Not every sort has one: tone has no presort
*today*, but that's a **practical** gap (early ASR + tonal IPA could make an
orthographic guess sensible later), not a permanent rule.
_Avoid_: auto-sort.

**sort** (the activity):
A speaker judging that a word *sounds the same* as the words already in a
group (and different from the others), on a given check. The primary data.
Distinct from **presort** (the machine seed).
_Avoid_: classify, categorize.

**join**:
A speaker judging that two groups are in fact the same group — the
group-level counterpart of a sort. Also by ear.

**group**:
A set of words judged the same on a given check.

**check**:
The specific test a sort is judged on. Segment checks are **positional**
(`C1`, `V1`, `V2`, …) — defined by position in the word, **category-
independent**, and they **persist across all slices** (a check applies
wherever its position exists; not all are relevant to every profile —
`V2` ∉ `CVC`). A check also carries a **data type** — *open* (full sort:
create new groups **and** join), *boolean*, or *bounded integer* — and the
data type, **not the tier**, governs which operations apply: boolean/int
checks are presort-determined and verify-only (no create-new, no join).
Tone's analog is a **frame**, which is a different kind of thing — see the
flagged ambiguity below.

**slice**:
The comparable subset of the wordlist a sort works through at once, so the
comparisons stay manageable and comparable. Segments and tone: a
`(part-of-speech, profile)` pair. Syllables: a **macrogroup**.

**macrosort**:
Re-running the sort with **groups** themselves as the items, to aggregate
slice-bound groups into the whole-language writing system (**glyphs**).
Currently segments only; planned for tone (via a new structure parallel to
`program.alphabet`). The data model around this is under active redesign.

**glyph**:
An orthographic unit of the alphabet that macrosort assigns groups to; may
be multi-character (a digraph such as "ng"). Held in `program.alphabet`.

**macrogroup** (syllables):
The coarse syllable bucket `Beg + count + End`, **derived** from the three
syllable primitives (`#C`, `C#`, `syls`) — not stored as a composite. The
syllable analog of a segment **profile** as a slice.

**primitive** (syllables):
One of the three stored per-word syllable judgements: `#C` (word-initial
C/V), `C#` (word-final C/V), `syls` (count, a bounded integer). The
**macrogroup** derives from them; the per-macrogroup **profile** sort is a
separate, finer level.

### Tone terms

**surface tone**:
A word's tone *as actually pronounced in a given frame* — one value per
frame, the raw sort result. Stored per-frame on the sense's **examples**
(`tonevaluebyframe`), not on the form-annotation channel segments use.

**underlying form (UF) tone**:
The single abstract tone category a word belongs to, **composed from its
surface groups across all frames** (words with the same cross-frame
signature share a UF). One value per sense (`uftonevalue`). Drafts are named
like `Noun_CVC_1` until the user renames them ("High", …). Structurally the
tone analog of a syllable **macrogroup** (a composition), not of a glyph.

**surface tone group** / **UF group**:
A group of words judged alike in one frame (surface) vs. a group sharing one
underlying category across all frames (UF).

**tone frame**:
The syntactic context a word's tone is judged in (isolation, a possessive
frame, …); tone's analog of a segment **check**, but category-bound (see
flagged ambiguity). **isolation** is the one universal, context-free frame.

**tone melody**:
The pitch pattern of a word/morpheme (e.g. ˥˨) that a surface tone group
shares; notated symbolically, not stored as its own field.

**tone-orthography** (not built yet):
The foreseen whole-language written representation of tone — the tone analog
of the segment alphabet (`program.alphabet`), an *aggregation*. Distinct
from UF (a *composition*).

## Flagged ambiguities

**"Analysis language" in prose**:
In AZT and SIL tradition, "analysis language" means the language
BEING analyzed (= `analang`). Outside the SIL world, "analysis
language" usually means the language DOING the analysis (= a gloss
language). The viewer's `lift_api.py` `getGlossLanguages()` docstring
("Analysis/gloss language codes") reflects this drift. When writing
prose for an outside audience, prefer "the analyzed language" /
"the documented language" for `analang`; for documentation aimed at
SIL users, "analysis language" / `analang` is fine.

**`S` overloaded (syllable cvt vs `SortS` class vs segment macrocategory vs sonorant class)**:
Four uses of `S` coexist:
- **cvt** (`program.params.cvt()`): `'S'` is the whole-word **Syllable-profile**
  sort (added with `SortSyllables`), alongside `V`/`C`/`CV`/`VC`/`T`.
- **class name**: the task class **`SortS`** is **Segment** sorting (cvt
  `C`/`V`) — its `S` means *Segment*, the opposite of the syllable cvt
  `'S'` (= `SortSyllables`). So `SortS` ≠ cvt `'S'`: same letter, different
  kind of sort. Untangling this is one driver of the data-model redesign.
- **segment placeholder**: in the regex/profile machinery (e.g. `utilities/rx.py`
  `makeprofileforcheck`, `nX`) a local `S` is a generic **Segment** standing for
  either `C` or `V` — i.e. the macrocategory whose members are C and V — used
  when building per-segment checks (`C1`, `V2`, …).
- **alphabet segment class**: `'S'` is also a consonant subclass key in
  `sdict`/`profilesegments` (sonorants: l, r, ll, rr, …), beside C, V, G, N, D, ʔ.

These live in separate scopes today (a `params.cvt()` value vs a local var in
regex building vs an `sdict` key), so they don't collide — **but the syllable
cvt rides the *same shared sort engine* as segmental sorting**, so a stray
`cvt=='S'` test sitting near segment-placeholder code is a latent trap. If they
ever share scope, disambiguate (rename the syllable cvt, or the placeholder).
Safe for now; flagged to revisit.

**`check` vs `frame` (segments vs tone) — same role, different scope**:
Both are "the test a sort is judged on," but they are NOT the same kind of
thing. A **segment check** is **positional and category-independent** (`C1`
= the first consonant of *any* word that has one), so it persists across
every slice. A **tone frame** is a **syntactic construction tied to one
lexical category** — a grammatical environment that words of another
category cannot grammatically enter — so a frame is category-bound, not
universal. The lone exception is **isolation** (the bare word, no syntactic
context), which behaves like a category-independent check. The historical
code calls tone's tests "frames" (and "location" in some comments) and
segments' "checks"; unifying them
needs a check abstraction that can declare its **scope** (positional-
everywhere vs bound-to-a-category), NOT a rename pretending they're
identical. To reconcile.

**`Analysis` and `group` overloaded (tone)**:
`Analysis` (`backend/core/analysis.py`) is **tone-only** — the surface→UF
grouping algorithm — despite the generic name; `program.analysis` is tone.
And `group` means three things: a **surface group** (a tone category in one
frame), a **UF group** (an abstract cross-frame category), or a syllable
**macrogroup** — disambiguate when reasoning across tiers.

## Example dialogue

> Linguist: "I want to record an audio sample for this entry."
> Dev: "Which language? The headword is in the analang — we'd tag
> the audio as `<analang>-x-audio`."
> Linguist: "And the gloss?"
> Dev: "The gloss is in a glosslang. It doesn't get an audio
> attachment in this flow — only the analang form does. The
> glosslang is just where the meaning is written."
