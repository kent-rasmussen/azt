# In Process
## Issues from November 2020 Zulgo beta test (and since)
### *Empty Form Problems*
- Noform Nogloss entries showing up on recording screen (ideally make never appear, at least skippable)
- fix problems that arise from empty form, or cut processing of those records earlier
### *UI Imporovements*
- make `Record` button on main window.
### *Naming Groups*
- figure out problem of leaving triage after one addition of words -- related to problem with empty group --related to having a single character name for the group
- make group name smarter than `len>1`
### *Prioritization*
- make checkcheck pick the most numerous profile that hasn't been finished, along with it's ps.
- add check to automatic addition of data to first group (e.g., if not valid data).
- Figure out why sort isn't showing any buttons
### *CV Report*
- make CV report not include ei as both V and VV, but not exclude a word for both C1 and C2.
- make CV report not include Caa in V1 or V2
- make CV report only reference lx field
- make data only give once (not in V1 or V2 if in V1=V2)
## Cleanup
- put `setdefaults.py` into Check class

# Version 0.3.1
new features:
- function to determine most populous syllable profile, with its ps
  - assumes most populous ps-profile filter, until another is chosen.
  - runs (and refreshes) with other syllable profiles on certain startups
- CV report now takes most populous syllable profiles, and runs all checks
  - most restrictive (e.g., V1=V2) first
- main window displays number of words in current ps-profile filter
- new (Advanced) menu option to redo syllable profile analysis
- only question required on first open (for now) is C,V,CV, or T; everything else has an initial assumed value (though still changeable through the menus).
bug fixes:
- remove `lift_url.py` from repo
  - if non file found in `lift_url.py`, rejects and asks for a file.
  - if non-LIFT file is given, AZT quits on an exception, with console and UI message, and deletes `lift_url.py`.
- fixed C/V report
- Added icons to distinguish sort and verify pages
  - includes data only once per Sn (not in V1 or V2 if in V1=V2, nor in C1 or C2 if in C1=C2)
  - repeats data selected for by another Sn (C1 and V1 both is OK, for CV profile)
- fixed missing frames on tone checks --asks user to define a frame if none there.
- make all file open options with `encoding='utf-8'`
- remove requirement for location key in tone frames

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
