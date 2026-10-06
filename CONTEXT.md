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

**form type** (`ftype`):
Which form of a word is being worked on: the **lexeme** (`lx`), the
**citation form** (`lc`), or a **secondary form** such as plural (`pl`) or
imperative (`imp`). Every fact a sort records about a word — its CV
profile, its group memberships, their verification — is a fact about one
form, so the form type is the widest scope of any sort datum. In LIFT the
lexeme and citation form are their own elements, while secondary forms are
fields whose type name the project chooses, so "form type" and "field
type" overlap and either covers the other with a slight stretch. The code
(`pl`) is stable; the field name ("Plural") is a project setting. On the
LIFT side any field can be asked for by its type (`tone`, `cvprofile_lc`);
the app's form-type setting only ever names a word form. The UI calls
choosing a form type a **word check**. On the syllable-profile sort the form
type is also the location, one-to-one (see **location**).
The lexeme and citation form belong to every entry whatever its category.
A secondary form can be made on any entry; the project maps each category
to its secondary form (nouns: plural; verbs: imperative), and the parse
runs that mapping backwards: having a plural is what makes an entry a
noun. Secondary forms are typically filled in after the citation form, so
they also slice the lexicon by completeness.

## Sorting (data collection)

The whole app collects one kind of data: **how words sound, judged by the
ear of people who speak the language.** Every step is that, with a single
exception — **presort**.

**tier**:
The phonological dimension a sort works in — **segment**, **tone**, or
**syllable-profile** — mirroring the (autosegmental) tiers of a spoken
word. The segment tier, also called the **CV tier**, subdivides into the
**C** (consonant) and **V** (vowel) tiers. In code this is the `cvt`
parameter (`CV`/`C`/`V`/`T`/`σ`, decided 2026-10-02; `S` was the syllable
code until then); `tier` is the domain term for it. (Praat's TextGrid "tiers" in
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
group (and different from the others), at a given location. The primary data.
Distinct from **presort** (the machine seed).
_Avoid_: classify, categorize.

**join**:
A speaker judging that two groups are in fact the same group — the
group-level counterpart of a sort. Also by ear.

**group**:
A set of words judged the same at a given location.

**location**:
Identifies what we are looking at when we ask the question "same or
different?". On the segment tier a location is a **position** in the word
(`C1`, `V1`, `V2`, …), **category-independent**, and it **persists across
all slices** (it applies wherever its position exists; not all are
relevant to every profile — `V2` ∉ `CVC`). On the tone tier a location is a
**frame**, a syntactic construction bound to one lexical category, with
**isolation** the one universal frame. On the syllable tier the locations
are the three primitives (`#C`, `C#`, `syls`) and, on the profile sort, the
**form type** itself, one location per form. A location has a **scope**,
the slices it applies to, read off one slice dimension (profile for a
position, part of speech for a frame, nothing for the syllable locations;
see **slice**), and a **data type** — *open* (full sort: create
new groups **and** join), *boolean* (two answers and only two; for `#C` and
`C#` the two labels are `C` and `V`, kept as stored — "boolean" is the
arity, not a program-language truth value), or *cardinal* (a count, any
true result of `len()`: the syllable count) — and the data type, **not the
tier**, governs which operations apply: boolean and cardinal locations are
presort-determined and verify-only (no create-new, no join). A data type
carries its own validator: a syllable count of 0 is not a value. The word
is the one LIFT already uses: every tone example records its frame in a
`location` field.
_Avoid_: check, frame (the code's identifiers for the segment and tone
cases; they name the same kind of thing and lag the glossary); bounded
integer (for cardinal).

**slice**:
The comparable subset of the wordlist a sort works through at once, so the
comparisons stay manageable and the whole list is got through one chunk
at a time. Its dimensions are the sort's: a `(part-of-speech, profile)`
pair for segments and tone; the **syllable profile class** (`#C`, `syls`,
`C#`) for the syllable-profile sort; none for the syllable primitives,
which work the whole list. Which **locations** apply in a slice is a
separate question, answered by one dimension per tier: segmental
positions depend on the profile and not the part of speech (`V2` ∉ `CVC`;
`CVC` nouns and verbs have the same positions); tone frames depend on the
part of speech and not the profile (a noun frame fits any noun); the
syllable locations depend on neither.

**macrosort**:
Re-running the sort with **groups** themselves as the items, to aggregate
slice-bound groups into the whole-language writing system (**glyphs**).
Each item carries the slice and location it was formed at, and a glyph
spans many of them: the speaker judges the first vowel of *these* words
against the second vowel of *those*. **A glyph never holds two groups from
the same slice and location**: within one slice and location the sort has
already judged them different, so macrosort compares only across slices
and locations. The same rule will hold for the tone-orthography.
Currently segments only; planned for tone (via a new structure parallel to
`program.alphabet`). The data model around this is under active redesign.

**glyph**:
An orthographic unit of the alphabet that macrosort assigns groups to; may
be multi-character (a digraph such as "ng"). Held in `program.alphabet`.

**syllable profile class** (or **profile class**):
The coarse syllable bucket `Beg + count + End`, **derived** from the three
syllable primitives (`#C`, `C#`, `syls`) — not stored as a composite. It
is the syllable-profile sort's **slice**: the sort works one profile
class at a time, as a segmental sort works one `(part-of-speech, profile)`
at a time. What it is distinguished from is a macrosort group: a
composition, not an aggregation (Kent, 2026-10-05, correcting an
earlier entry that called it "not a slice").
_Avoid_: macrogroup (echoes **macrosort**, which is an aggregation).

**primitive** (syllables):
One of the three stored per-word syllable judgements: `#C` (word-initial
C/V), `C#` (word-final C/V), `syls` (count, a cardinal). The
**profile class** derives from them; the per-class **profile** sort is a
separate, finer level. A judgement here may be the user's (a syllable-prep
sort) or **trusted** — "Trust machine analysis" records the primitives implied
by the profile it trusts, so a word always sits in some profile class and can be
sent back one level at a time rather than re-derived from zero. A user sort
always outranks a trusted value and is never overwritten by one.

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
tone analog of a **syllable profile class** (a composition), not of a glyph.

**surface tone group** / **UF group**:
A group of words judged alike in one frame (surface) vs. a group sharing one
underlying category across all frames (UF).

**tone frame**:
The syntactic context a word's tone is judged in (isolation, a possessive
frame, …): a **location** on the tone tier, whose scope is one lexical
category, since a construction built for nouns cannot take a verb.
**isolation** is the one universal, context-free frame.

**tone melody**:
The pitch pattern of a word/morpheme (e.g. ˥˨) that a surface tone group
shares; notated symbolically, not stored as its own field.

**tone-orthography** (not built yet):
The foreseen whole-language written representation of tone — the tone analog
of the segment alphabet (`program.alphabet`), an *aggregation*. Distinct
from UF (a *composition*).

## Flagged ambiguities

**"Analysis language" in prose**:
In AZT, "analysis language" means the language
BEING analyzed (= `analang`). elsewhere, "analysis
language" usually means the language DOING the analysis (= a gloss
language). The viewer's `lift_api.py` `getGlossLanguages()` docstring
("Analysis/gloss language codes") reflects this drift. When writing
prose for an outside audience, prefer "the analyzed language" /
"the documented language" for `analang`; for documentation aimed at
SIL users, "analysis language" / `analang` is fine.

**`S` overloaded (syllable cvt vs `SortS` class vs sonorant class)**:
Three uses of `S` coexist (an earlier version of this entry listed four; the
"generic segment placeholder" it described does not exist in the code —
every `S` in the regex and profile machinery is the sonorant class below):
- **cvt** (`program.params.cvt()`): `'S'` was the whole-word **Syllable-profile**
  sort (`SortSyllables`), alongside `V`/`C`/`CV`/`VC`/`T`; now `'σ'`.
- **class name**: the task class **`SortS`** was **Segment** sorting, the base
  `SortV` and `SortC` inherit — its `S` meant *Segment*, the opposite of the
  syllable cvt `'S'`. Renamed **`SortCV`** on 2026-10-02 (and `TranscribeS` →
  `TranscribeCV`); the string-built task switch became one table. Built,
  awaiting verification.
- **sonorant class**: `'S'` is a consonant subclass (l, r, ll, rr, rh, wh, …)
  beside N, G, D and ʔ, in the profile machinery (`utilities/rx.py`,
  `backend/core/profiles.py`); undistinguished, it folds into C.

The first two are bridged by code that builds a task class name from the cvt
letter (`task_base + cvt`), so choosing `S` on a segment sort resolves to the
segment base, not the syllable sort. **Resolved 2026-10-02 (built the same
day, awaiting verification):** the syllable tier's code is **`σ`**, the standard single-letter
symbol for syllable; **`S` alone is always the sonorant class**; the
segmental tier's code is **`CV`**, since the segmental tier is also called the
CV tier and C and V are its dependent tiers, so the segmental base class is
`SortCV` and the combination checks (`CV1`, `VC2`) belong to it.

**`check` vs `frame` (segments vs tone) — resolved 2026-10-02 as `location`**:
Both were "the test a sort is judged on," and they are the same kind of
thing with different **scope**: a segment position applies to every slice
whose profile has it; a tone frame applies to one lexical category, with
isolation the exception. The one term is **location** (Kent: *"it
identifies what we're looking at when we ask the question 'same or
different?'"*), chosen because it is the word LIFT already uses for a tone
frame and reads naturally for both a position in the word and a position
in syntax. The code still says `check` for segments and `frame` for tone;
those identifiers lag the glossary and are not to be read as two concepts.

**`Analysis` and `group` overloaded (tone)**:
`Analysis` (`backend/core/analysis.py`) is **tone-only** — the surface→UF
grouping algorithm — despite the generic name; `program.analysis` is tone.
And `group` means three things: a **surface group** (a tone category in one
frame), a **UF group** (an abstract cross-frame category), or a syllable
**profile class** — disambiguate when reasoning across tiers.

## Example dialogue

> Linguist: "I want to record an audio sample for this entry."
> Dev: "Which language? The headword is in the analang — we'd tag
> the audio as `<analang>-x-audio`."
> Linguist: "And the gloss?"
> Dev: "The gloss is in a glosslang. It doesn't get an audio
> attachment in this flow — only the analang form does. The
> glosslang is just where the meaning is written."
