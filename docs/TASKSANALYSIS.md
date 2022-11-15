# Analysis Tasks

## Running reports
Reports are listed under analytical tasks because they are a fundamental part of the analytical process, and have more to do with looking at data that is there, than with adding or modifying primary data. That said, you may be interested in running a report, even if you otherwise just do data collection.

### Comprehensive Reports
Comprehensive reports give you reports across multiple lexical categories, and across multiple syllable profiles. The number of each is modifiable, if you want a larger or smaller report, but it starts at the most populous, so this is top 1, 2, 3, etc.
Setting the number of lexical categories at two (2) will almost always get you nouns and verbs.
These reports include data across all frames (for tone) or checks (for segments).

### Single Slice Reports
Reports not labeled comprehensive report on a single slice of data, as defined by lexical category and syllable profile. Set which of each you want in your report.
Segment reports report on one check at a time (e.g., V1, V1=V2, C2, etc), tone reports include all frames in the sorted data.

### (Comprehensive) Alphabet Reports
This report gives you information on Consonants and Vowels. Because the comprehensive reports can be very comprehensive (they contain each check relevant to each syllable profile), there are four of them, to help you focus on what you're interested in:
- Comprehensive Vowel Report
- Comprehensive Consonant Report
- Comprehensive CxV Phonotactics Report
- Comprehensive Alphabet Report (all of the above)

### (Comprehensive) Tone Report
This report gives you information on words in tone frames, according to the lexical category and syllable profile, organized with each framed example under its head word. The (by frames) report organizes the examples by frame, listing each word that has been sorted into that frame. The Comprehensive report gives you the top [two] lexical categories (should be Nouns and Verbs), in the [two] largest syllable profiles, across all appropriate checks (both of these numbers are configurable, if you want more or less of either).

## Transcribe Vowels into letters
In this tool, users can change the symbol used to represent a meaningful vowel group. If a group was split into two groups in [the sort vowels task](TASKSCOLLECTION.md#sort-vowels), at least one should be renamed here, so they will be distinct in the writing system.

## Transcribe Consonants into letters
In this tool, users can change the symbol used to represent a meaningful consonant group. If a group was split into two groups in [the sort consonants task](TASKSCOLLECTION.md#sort-consonants), at least one should be renamed here, so they will be distinct in the writing system.

## Transcribe Tone (Surface Groups)
In the [tone sorting process](TASKSCOLLECTION.md#sort-tone), A→Z+T assigns numbers to the surface tone groups of a data slice for each frame, because the first and main purpose is to distinguish what is different, and group what is the same. But here we can make those numbers more meaningful, assigning a phonetic value to the one tone melody shared by the group. This should be done in symbolic notation (e.g., [˦˦˦  ˨˨˨]), though you can use other notation as well. In any case, this is **surface tone transcription**, not any kind of underlying representation, so any reference to High or Low tones is inapprpriate here.

## Join Underlying Form Groups
The UF groups drafted by A→Z+T are almost always clearly hypersplit. Here you can join those that (in your judgement) should be joined, and give them more meaningful names than the defaults (e.g., Noun_CVCV_1). These can by anything you want, including maintaining the lexical category and syllable profile info, and it is appropriate to add here your hypthesis about underlying forms.
These groups can be renamed as you like, and these names will be represented in reports.
All these changes remain in the database until/unless you sort more data. In that case, the next report will redo the analysis, so you can start this joining work from the current group analysis. Alternatively, you can redo this analysis at any point, if you don't like the results of your groupings.

[A→Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[Praat]: https://www.fon.hum.uva.nl/praat/
