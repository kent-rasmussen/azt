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

**`S` overloaded (syllable cvt vs segment macrocategory vs sonorant class)**:
Three unrelated meanings of `S` coexist:
- **cvt** (`program.params.cvt()`): `'S'` is the whole-word **Syllable-profile**
  sort (added with `SortSyllables`), alongside `V`/`C`/`CV`/`VC`/`T`.
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

## Example dialogue

> Linguist: "I want to record an audio sample for this entry."
> Dev: "Which language? The headword is in the analang — we'd tag
> the audio as `<analang>-x-audio`."
> Linguist: "And the gloss?"
> Dev: "The gloss is in a glosslang. It doesn't get an audio
> attachment in this flow — only the analang form does. The
> glosslang is just where the meaning is written."
