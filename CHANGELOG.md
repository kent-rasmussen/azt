# In Process
## Issues from November 2020 Zulgo beta test
### Cleanup
- fix references to self.name which change and don't reset (e.g., reports)
  - """self.name set here""" annotated (just wordsbypsprofilechecksubcheck)
- check for iteration reset problems for self.subcheck, other variables
## Next Features
- fully distinguish C, CG, and NC onsets (or just word initial?), C and N finals
  - look for CG and NC first, then C.
  - how to treat C1=C2? CG1=CG2? Do we want S to be larger units, or to have N and G modifications?
  - how to treat N and C different word finally? (may have to leave this for analysis)
  - set lift.c={} with values lift.c['C'], lift.c['CG'], lift.c['NC']
    - C could include N and G, but other would be distinct from CC.
  - set lift.v={}, with lift.v['V'], lift.v['V:'], and lift.v['Ṽ'] or lift.v['VN']?
    - some people may want V to include Vː, others may not (for tone, probably all should...)
    - setup questionː is <VN> [Ṽ] or [VN]? —This is important for tone.
  - make setting to turn this off
- add C and V sorting (and CV?)
- make record button work for different contexts, by `self.type`:
  - T: tone report (as is currently done)
  - C,V: citation forms (new page? plural, other forms? all <form @lang/>)
  - ad hoc?
- XLP export
### Prioritization
- make checkcheck reference most popular *unfinished* ps-profile combo
### Documentation
- Add what and why pages in different places, with rationales and instructions specific to context?
## Issues since November 2020 Zulgo beta test
### UI Improvements
- add second icon for joinT pages
### CV Report
- make CV report not include ei as both V and VV, but not exclude a word for both C1 and C2.
- make CV report not include Caa in V1 or V2
- make data only give once (not in V1 or V2 if in V1=V2)
### Under the Hood
- put `setdefaults.py` into Check class
- transition to gloss only (no definition references)
  - make docs specify gloss should be populated (maybe instructions to bulk copy?)
- distinguish between lc and lx
  - make CV report only reference lx field
  - make docs specify the difference, start with lc references (maybe instructions to bulk copy?)
# Version 0.3.1
## new features:
### prioritization
- function to determine most populous syllable profile, with its ps
  - assumes most populous ps-profile filter, until another is chosen.
  - runs (and refreshes) with other syllable profiles on certain startups
### reports
- CV report now takes most populous syllable profiles, and runs all checks
  - most restrictive (e.g., V1=V2) first
  - includes data only once per Sn (not in V1 or V2 if in V1=V2, nor in C1 or C2 if in C1=C2)
  - repeats data selected for by another Sn (C1 and V1 both is OK, for CV profile)
### Useability
- only question required on first open (for now) is C,V,CV, or T; everything else has an initial assumed value (though still changeable through the menus).
- `Record` button on main window, with unencombered icon
  - checkcheck picks the most numerous profile, along with it's ps.
- label method to wrap on availablexy
- main window displays number of words in current ps-profile filter
- new (Advanced) menu option to redo syllable profile analysis
- Sort now ask user to affirm "This word is OK in this frame" on first word.
- added second gloss fields to tone frame addition window
- added second gloss (now by iso code) to getframeddata
## bug fixes:
### Useability
- make all file open options with `encoding='utf-8'`
- Fixed issue where `exit` sorted into last group; now just exits sorting.
- remove `lift_url.py` from repo
  - if non file found in `lift_url.py`, rejects and asks for a file.
  - if non-LIFT file is given, AZT quits on an exception, with console and UI message, and deletes `lift_url.py`.
- fixed C/V report
- fixed missing frames on tone checks --asks user to define a frame if none there.
- reworked buggy distinction of integer and named groups
- removed Noform Nogloss entries from recording screen
- resolved problem of leaving triage resulting in incorrect sorting
### UI
- Added icons to distinguish sort and verify pages, as well as join pages
- resolved joinT second window problem with the scrolling frame
- fixed scrolling frame problems
- removed (inappropriate) tone group designation from items on tone up report
### Under the hood
- framed script now addresses both senses and examples
- fixed problems that arise from empty form (cut processing of those records)
- group name references now use int() instead of len()
- remove requirement for location key in tone frames
- gloss and form usage removed from self.toneframes references in getframeddata --now iso codes
- changed lift.py functions (addexamplefields,addpronunciationfields,
  exampleisnotsameasnew,exampleissameasnew) to work on iso codes
- Changed references to getframeddata with ['gloss'] or ['form'] to iso (['formatted'] and ['tonegroup'] OK)
- reworked addexamplefields and dependent functions to work with iso gloss/forms
- self.toneframes references with form and gloss converted to iso

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
