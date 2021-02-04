# Changelog

## In process
### Cleanup Unresolved from November 2020 Zulgo beta test
- Find again (not happening now) and fix scrolling frame size problem on rename
    - frame in a frame? (this problem looks familiar...)

### CV Report
    - fix key 7 problem for sxw
## In Process
- XLP export (these are not likely to happen)
    - run dotexpdf (once you figure out where that is) to generate pdf?
    - run script to generate html?
    - figure out window specific variations (with Andy?)
- Add treatment of long vowels, similar to consonant distinctions/interpretation
  - lift.s['VV'] should include xx for x in lift.s['V']
  - lift.s['V:'] should include x:, and xː for x in lift.s['V'], as for c['pn'], which is always C.
  - lift.s['VV'] (where V1-V2) should be interpretable as V, VV, or V:
    - add to appropriate check.s variable, as for NC and CG
    - or make VV>V: or not, and feed that to V:>V or not.
  - lift.s['V:'] should consider VdVd, dVdV, dVVd, and VddV as possibles/hypotheticals.  
  - lift.s['V'] should include lift.s['d'], if present
  - set lift.s['V'] distinct from, lift.v['V:'], and lift.v['Ṽ'] or lift.v['VN']?
      - setup question: is <VN> [Ṽ] or [VN] (hopefully not both!)? —This is important for tone.
      - or is lift.s['V'] and lift.s['d'] enough?
      - doing it here is nice to have the test of what is actually there...
- done? Update regex functions a=to allow for C(V)C\1, CVC(V)C\1, and C(V)C\1C\1, for vowel and consonant reports and checks
- bring diacritics into vowel variables
- figure out why multiple fuŋ entries aren't showing for recording on bfj
    - '6e2a67cb-6695-4536-bc55-423fad4f019b',<+
    - '7cdcddfc-5b9f-44bf-bfe5-d5ce164720cd',
- need to fix multiple links to the same recording
- check that changes to S regexs don't break too much.
- Find faithful way to keep window on the screen for MS Windows
- diagnose pl/imp not appearing on recording screen
  - not really there?
  - pushed off the screen?

## Next Features
    - add C and V sorting (and CV?)

### Prioritization
- make checkcheck reference most popular *unfinished* ps-profile combo

### Documentation
- Add what and why pages in different places, with rationales and instructions specific to context?

### Under the Hood
- put `setdefaults.py` into Check class
- transition to gloss only (no definition references)
    - make docs specify gloss should be populated (maybe instructions to bulk copy?)
- distinguish between lc and lx
    - make CV report only reference lx field
    - make docs specify the difference, start with lc references (maybe instructions to bulk copy?)

# Version 0.6.1
- cleanup of exceptions on code running after windows closed.
- fixed logic in sort/verify/join and recording windows
- set logic to record just one (selected) slice of lexicon for lc/lx recordings
    - There is no setting for this yet, just quick to change the code
    - skip button only when doing multiple pages.
- Reworking of regex for V and C combinations
    - All bfj characters are now taken up by regexs


# Version 0.6
- fixed numerous report problems (should be mostly working now)
- Implemented XLingPaper export (at least beginning)
    - Organized data written to valid XLP XML file, which compiles to PDF in XXE.
    - data is written from entry lc/lx or sense examples, as appropriate
    - If a sound file exists, it is linked in XLP to the data form.
    - There are three report options:
        - Basic, for top ps-profile combos (Menu)
        - Just data as currently filtered (click on C/V "Sort" button)
        - Tone report, with examples (Menu)

## UI
- removed subcheck from main screen, at least until we are using it again

## Bug fixes
- Analysis lang is correctly treated on change (triggering reanalysis)

## Under the hood
- cleaned up report with close() method

# Version 0.5
- made help:about scroll
- fixed multiple sense glosses pulled into CV reports (now senses are sorted individually)
- added linebreaks to tone frame definition window, to keep it on the page

# prioritization
- We now guess analysis language (when unspecified) based on the one with the most appearances.
- User can now distinguish C,N,N#,G, and S as desired, NC and CG can be that, C or CC.

## UI
- Added page to instruct A→Z+T how to distinguish certain segment classes
- removed redo profile analysis from easy temptation
- Second gloss now showing for lc/lx recording page
- C/V check now just outputs filter by ps-profile; buttons no longer cause a crash.

### Under the Hood
- added variables for version number and program name, added to help:about
- Fixed bug where recording settings aren't being reused
- clean up code to organize functions in groups
- removed profile from recording names (so analysis changes don't require file name changes)
- set lc recordings to go on entries, not senses.
- variables to (potentially) distinguish nasals, glides, and other sonorants from other consonants
- Set menus to have 'Redo' set, for advanced things (incl. profile analysis - get this off the beaten path!)
- removed invalid check from profilecheck
- set up log to run by default, working in modules: seems to be working in MS Windows
- added check and warning for fr or en encoded lc/lx data (<10 examples)
- Fine grained logging works now (log.log(1,x))
- Added exceptions to logs, both from python and tkinter
- Analysis language guessing seems to work on various lift files.
- distinguished between segment type distinctions x[N,C,G,S] and segment combination x[CG,NC,NCG,NCS] distinctions, which are non boolean (as xy, as CC, or as C).
  - set up init init, check, and UI to work with new variables
- set getresults to use profile data, so it doesn't pick up <ch> = CC.

# Version 0.4
## new features:
### Functions
- New page ("Record dictionary words") to record and store links in one of the following (the last two have a number of possible names in field[@type={possible name}]; the tool currently guesses from a number of options, based on what is in the lift database):
    - lexical-unit/form[@lang=voicelang]/text
    - citation/form[@lang=voicelang]/text
    - {pluralname}/form[@lang=voicelang]/text
    - {imperativename}/form[@lang=voicelang]/text

### UI
- New `wait` window for longer tasks (reports, recording)
- Record button now works for different contexts, by `self.type`:
    - T: tone report (as was done before)
    - C,V: citation forms (new page? plural, other forms? all <form @lang/>)
- "Record dictionary words" page also accessible through record menu
- added check for parameters before making recording windows
- added button for next group in citation recording pages, distinct from exit.

### Bugs
- fixed problem with dot (.) in directory name

# Version 0.3.1
## new features:
### prioritization
- now assumes *every* setting for initial startup
    - check type should be `Vowel` until selected otherwise
    - assumes most populous ps-profile filter, until another is chosen.
        - new function to determine most populous syllable profile, with its ps
        - runs (and refreshes) with other syllable profiles on certain startups
        - selects most restrictive check available for profile (i.e. CVCV vowel checks start with V1=V2, not V1 or V2)
        - selects most populous V or C to check first
          - for CV checks, asks user which C and V (can't really guess that)
- C, V and profile selection dialogs now sorted by (included) counts, for the user to select based on frequency
    - counts are for valid data by ps, in the whole database

### reports

- CV report now takes most populous syllable profiles, and runs all checks
    - most restrictive (e.g., V1=V2) first
    - includes data only once per Sn (not in V1 or V2 if in V1=V2, nor in C1 or C2 if in C1=C2)
    - repeats data selected for by another Sn (C1 and V1 both is OK, for CV profile)

### Useability
- only question required on first open (for now) is C,V,CV, or T; everything else has an initial assumed value (though still changeable through the menus).
- `Record` button on main window, with unencombered icon
- `checkcheck` picks the most numerous profile, along with it's ps.
- label method to wrap on availablexy
- main window displays number of words in current ps-profile filter
- new (Advanced) menu option to redo syllable profile analysis
- Sort now ask user to affirm "This word is OK in this frame" on first word.
- added second gloss fields to tone frame addition window
- added second gloss (now by iso code) to getframeddata
- Trimmed down settings that are reset by another to a few essentials
    - checkcheck (flash) only when a setting is actually changed.
    - subcheck, if current values are appropriate to selected values.
- Join dialog is now more intuitive: one window with a single reset frame on select, instructions ask user to select two groups (as opposed to one, then the other). The first selection sets the first variable (as before), but leaves text in place, now as a label --other buttons remain.

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
- now guesses:
    - UI language (via gloss, which is in turn guessed from database)
    - Analysis language
    - Gloss languages
- fixed problems with recording settings and file names

### UI
- Added icons to distinguish sort and verify pages, as well as join pages
- resolved `joinT` second window problem with the scrolling frame
- fixed scrolling frame problems
- removed (inappropriate) tone group designation from items on tone up report
- syllable profile and vowel windows now scroll

### Under the hood
- framed script now addresses both senses and examples
- fixed problems that arise from empty form (cut processing of those records)
- group name references now use int() instead of len()
- remove requirement for location key in tone frames
- gloss and form usage removed from self.`toneframes` references in `getframeddata` --now iso codes
- changed `lift.py` functions (`addexamplefields`,`addpronunciationfields`,
  `exampleisnotsameasnew`,`exampleissameasnew`) to work on iso codes
- Changed references to `getframeddata` with ['gloss'] or ['form'] to iso (['formatted'] and ['tonegroup'] OK)
- reworked `addexamplefields` and dependent functions to work with iso gloss/forms
- `self.toneframes` references with form and gloss converted to iso
- fixed references to self.name which iterate. They are now stored and reset (just `name` and `subcheck` in and wordsbypsprofilechecksubcheck, but also `type`, `ps`, and `profile` fixed in basicreport)
- added checks to checkcheck to zero out obsoleted settings (not valid for new setting)
- Fixed iteration reset problems for self.subcheck, other variables

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
