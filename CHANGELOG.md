# In Process
## Issues from November 2020 Zulgo beta test (and since)
### *UI Improvements*
- *still* fix record button image and words
### *Prioritization*
- consider check to automatic addition of data to first group (e.g., if not valid data).
## Cleanup
- fix references to self.name which change and don't reset (e.g., reports)
- put `setdefaults.py` into Check class
## Next Features
- add C and V sorting (and CV?)
- add recording page for unsorted data (just citation forms, to go in lc field)
- make record button work for different contexts (ad hoc, tone report, citation forms)
### *UI Improvements*
- add icons for joinT pages
### *Prioritization*
- make checkcheck reference most popular *unfinished* ps-profile combo
### *CV Report*
- make CV report not include ei as both V and VV, but not exclude a word for both C1 and C2.
- make CV report not include Caa in V1 or V2
- make CV report only reference lx field
- make data only give once (not in V1 or V2 if in V1=V2)

# Version 0.3.1
new features:
- function to determine most populous syllable profile, with its ps
  - assumes most populous ps-profile filter, until another is chosen.
  - runs (and refreshes) with other syllable profiles on certain startups
- CV report now takes most populous syllable profiles, and runs all checks
  - most restrictive (e.g., V1=V2) first
- main window displays number of words in current ps-profile filter
- new (Advanced) menu option to redo syllable profile analysis
- only question required on first open (for now) is C,V,CV, or T; everything else - - `Record` button on main window.
has an initial assumed value (though still changeable through the menus).
  - checkcheck picks the most numerous profile, along with it's ps.
- label method to wrap on availablexy
- Sort now ask user to affirm "This word is OK in this frame" on first word.
bug fixes:
- make all file open options with `encoding='utf-8'`
- Fixed issue where `exit` sorted into last group; now just exits sorting.
- remove `lift_url.py` from repo
  - if non file found in `lift_url.py`, rejects and asks for a file.
  - if non-LIFT file is given, AZT quits on an exception, with console and UI message, and deletes `lift_url.py`.
- fixed C/V report
- fixed missing frames on tone checks --asks user to define a frame if none there.
- removed (inappropriate) tone group designation from items on tone up report
- Added icons to distinguish sort and verify pages
  - includes data only once per Sn (not in V1 or V2 if in V1=V2, nor in C1 or C2 if in C1=C2)
  - repeats data selected for by another Sn (C1 and V1 both is OK, for CV profile)
- remove requirement for location key in tone frames
- reworked buggy distinction of integer and named groups
- removed Noform Nogloss entries from recording screen
- framed script now addresses both senses and examples
- fixed problems that arise from empty form (cut processing of those records)
- resolved problem of leaving triage resulting in incorrect sorting
- group name references now use int() instead of len()
- resolved joinT second window problem with the scrolling frame
- fixed scrolling frame problems

# Version 0.3 (November 2020)
## language and search parameters
- logic to make appropriate assumptions
- UI menus for changing parameters
- current parameters indicated in UI (main window)
##Search basics
- data filtering by part of speech (grammatical category) and syllable profile
- basic search (no checks yet) for vowels
- basic search (no checks yet) for consonants
- basic search (no checks yet) for consonant-vowel combinations
## Tone frame checks:
- Tone frame definitions (in advanced menu, should be done by a linguist)
- Sort page to sort filtered data into groups (for a given tone frame)
- Verify page to remove items that don't belong in a given group
- Join page to combine groups with the same surface tone in that frame
  - this can be called from the Advanced menu at any time
- Iterative logic to Sort, Verify, and Join until all of the following are true (at the same time):
  - no words are unsorted (except for those intentionally skipped)
  - the user affirms that each group is just one thing
  - the user affirms that each group is distinct from other groups
- user can change to another frame, profile or part of speech at any time
## Recording
- Once some is done, recording is possible (via Advanced menu)
- dialog to set and test sound card and recording parameters
- Words selected by analyzed tone group, one per group, then a second, etc. up to 15 (currently)
- each context/frame where a word has been sorted is presented for recording
- recording is done by click-speak-release on a single `record` button.
- once recorded, the user is presented with buttons to play and/or redo the recording.

## Progress
- the type of search (Consonant, Vowel, Consonant-Vowel, or Tone) is indicated by an icon on the `Sort` button on the lower left of the main window.
- the right side of the main window shows a table of progress, once some sorting has been done
  - for one check type at a time (the current check type)
  - for one grammatical category at a time (the current grammatical category)
  - The table is organized by syllable profile v subgrouping
  - cell contents count the number of groups, if unnamed
  - cell contents list groups, if named
