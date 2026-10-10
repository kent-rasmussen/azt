# Working from a Dekereke database

If your language data is already in a [Dekereke] phonology database, you do not
have to retype it into [A-Z+T]. A-Z+T can read your Dekereke file, work on it,
and write your results back into it.

[Dekereke]: https://casali.canil.ca/
[A-Z+T]: https://github.com/kent-rasmussen/azt

## Importing

When A-Z+T asks *What do you want to work on?*, choose **Import a Dekereke
phonology database**, then:

1. Pick your Dekereke `.xml` file.
2. Give the language code, on the same page a new project uses.
3. Check the columns.

Step 3 is the only unusual one, and it only happens once.

### Why A-Z+T has to ask about your columns

Dekereke lets *you* name the columns of your database, so no two databases look
alike: one may have `Phonetic`, `Gloss` and `Orthography`, another `Fonetik`,
`Arti` and `Tulisan`. A-Z+T cannot know which is which, so it guesses from the
names — in English and Indonesian — and shows you the guesses to confirm or
correct.

The most important choice is **the form to sort and analyze**. A-Z+T works on
one form per word, so if your database has several columns of forms (a second
speaker, a second dialect, a careful and a fast pronunciation), you have to say
which one the speakers will be sorting. It is usually your phonetic column.

The other choices worth knowing about:

| Choice | What A-Z+T does with the column |
|---|---|
| the form to sort and analyze | the headword: this is what gets sorted, transcribed and reported on |
| how it is written | the orthographic form |
| meaning | a gloss and definition, in the language code you give beside it |
| part of speech | groups the word for sorting, since checks are done per category |
| sound file | plays the recording during sorting |
| a frame A-Z+T can sort | becomes an example, so this column can be sorted for tone like any other frame |
| the tone of a frame | the tone value that goes with that frame |
| record number | keeps the link back to your Dekereke row |
| keep it, but don't analyze it | carried along untouched, and written back on export |

Nothing is ever thrown away: a column A-Z+T has no use for is still carried
through, and comes back when you export.

### A note for languages with a lot of variation

If your database has a column per speaker or per dialect — common where forms
vary a great deal between speakers — you have a choice to make.

Marking such a column **a frame A-Z+T can sort** makes it a condition A-Z+T can
work on, so a speaker can sort those forms too, and A-Z+T will compare the
groups across columns the way it compares tone across frames. Marking it **keep
it, but don't analyze it** preserves the column without A-Z+T reasoning about
it.

A-Z+T was designed around one form per word, so the first option is using its
frame machinery for something close to, but not the same as, what it was built
for. It works, and it is worth knowing about; the reports will still call these
frames.

### If you keep your own syllable profile column

Some workflows have the researcher decide each word's syllable profile by hand,
in a column of the Dekereke database, rather than letting software guess it from
the spelling. If that is how you work, mark that column **syllable profile
(already checked)**.

A-Z+T organises every segmental sort by syllable profile, and it distinguishes a
profile *it* guessed from one *you* confirmed: it slices by the confirmed one,
and its fill-in pass never overwrites a profile that is already there. So a
column marked *already checked* is taken as it stands, and A-Z+T works from your
analysis instead of its own.

Mark the column **syllable profile (a guess to check)** instead if it was
auto-generated. A-Z+T will then treat it as a starting point to be confirmed.

If you use *already checked*, the digraph settings below matter much less for
your data — A-Z+T will not be deriving your profiles.

### Check the digraph settings before you sort

Do this once, right after importing, before any sorting:
`Advanced` ▸ `Digraph and Trigraph settings` (see [POLYGRAPHS.md](POLYGRAPHS.md)).

A-Z+T has to decide whether a two-letter sequence in your data is one sound or
two, and it starts from defaults borrowed from English or French spelling —
which mark `ou`, `ei`, `ai`, `oi` and friends as single vowels. If those are
really sequences of two vowels in your language, untick them.

This matters more than it sounds: every sort is organised by syllable profile,
so a word treated as `CV` instead of `CVV` is grouped with different words. It
is much cheaper to fix now than after your speakers have sorted.

### What happens to your sound files

Dekereke stores bare file names in the database and remembers the folder in a
sibling settings file (`<name>-DkUserSettings.xml`), which A-Z+T reads. Copy the
recordings into your new project's `audio` folder; A-Z+T tells you where that
is when it opens the project.

If your database records a separate take per column, A-Z+T attaches each take to
its own column, so you can hear the right recording next to the right form.

### Records that cannot be imported

A record with nothing in the column you chose to analyze cannot become an entry
— there would be nothing for a speaker to sort — so it is skipped. It is *not*
lost: it stays in your Dekereke file, and an export puts it back untouched.

## Exporting

Exporting writes your work back into **a copy of your original Dekereke file**,
rather than building a new one from scratch. Every column A-Z+T does not
understand — other speakers, acoustic measurements, your own notes — is copied
across unchanged, and only the columns you mapped are updated.

This is deliberate. A Dekereke database usually holds much more than A-Z+T works
on, and an export that rebuilt the file from A-Z+T's data alone would quietly
throw the rest away.

Two things do **not** go back to Dekereke:

- **Your sorting and verification record.** A-Z+T keeps track of which words a
  speaker judged alike, on which check. Dekereke has no place for it, and putting
  it in a column would show up as editable nonsense in Dekereke's own window. So
  the LIFT file stays the master copy of your analysis — keep it.
- **Anything with no column to go in.** A word's second sense, for instance: a
  Dekereke record is a single row.

## Files A-Z+T keeps beside your project

- `<name>.lift` — your project, the master copy of your analysis.
- `<name>.dekereke.xml` — a small file A-Z+T writes and reads for you. It
  remembers your column choices, their order, and where your sound files were,
  which is what makes an export able to put your database back together. You do
  not need to edit it, but do not delete it.

## If something goes wrong

**"Converting Dekereke files needs the 'lxml' module."** The import option only
appears when that module is installed; if you see this message, reinstall the
requirements (`pip install -r requirements.txt`).

**"No column is set as the form to analyze."** Go back and mark one column as
*the form to sort and analyze*.

**"These Dekereke column names can't be written to XML."** A column name that
starts with a digit, or contains a space or a symbol, cannot be written back as
an XML element. Rename the column in Dekereke and import again.

**Old Dekereke files.** Dekereke has changed the encoding it saves in over the
years. All three are read, and an export writes back in the same encoding the
file came in, so an older database stays readable by an older Dekereke.
