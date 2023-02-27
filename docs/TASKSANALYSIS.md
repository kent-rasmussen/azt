# Analysis Tasks

If you want to run a report on any of the following (to see what you have done), those are described [here](REPORTS.md).

## Transcribe Vowels into letters
In this tool, users can change the symbol used to represent a meaningful vowel group. If a group was split into two groups in [the sort vowels task](TASKSCOLLECTION.md#sort-vowels), at least one should be renamed here, so they will be distinct in the writing system.

## Transcribe Consonants into letters
In this tool, users can change the symbol used to represent a meaningful consonant group. If a group was split into two groups in [the sort consonants task](TASKSCOLLECTION.md#sort-consonants), at least one should be renamed here, so they will be distinct in the writing system.

## Transcribe Tone (Surface Groups)
In the [tone sorting process](TASKSCOLLECTION.md#sort-tone), A-Z+T assigns numbers to the surface tone groups of a data slice for each frame, because the first and main purpose is to distinguish what is different, and group what is the same. But here we can make those numbers more meaningful, assigning a phonetic value to the one tone melody shared by the group. This should be done in symbolic notation (e.g., [˦˦˦  ˨˨˨]), though you can use other notation as well. In any case, this is **surface tone transcription**, not any kind of underlying representation, so any reference to High or Low tones is inapprpriate here.

## Join Underlying Form Groups (Tone)
The UF tone groups drafted by A-Z+T are almost always clearly hypersplit. Here you can join those that (in your judgment) should be joined, and give them more meaningful names than the defaults (e.g., Noun_CVCV_1). These can by anything you want, including maintaining the lexical category and syllable profile info, and it is appropriate to add here your hypthesis about underlying forms.
These groups can be renamed as you like, and these names will be represented in reports.
All these changes remain in the database until/unless you sort more data. In that case, the next report will redo the analysis, so you can start this joining work from the current group analysis. Alternatively, you can redo this analysis at any point, if you don't like the results of your groupings.

[A-Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[Praat]: https://www.fon.hum.uva.nl/praat/
