# Changelog

## In Process
- fix analang detection problem?
- make recordbuttons pass recordcheck, which verifies that settings are plausible.
- look at how to break lines importing to XLP (for column headers)
- include checks on empty or repeated XLP nodes
- convert basic report to XLP table function

## Issues from Zulgo March 2021 workshop

## Issues from Chufie' workshop (Feb 2021)
+ zero form silently doesn't make a button
- verify screen doesn't make button
- set current visible on numbers to record
- extra space being added for None forms in Frame construction
- give error message if crashing because selecting part of speech that isn't populated in profile analysis.
- fix zip problem on Windows: "OSError: [Errno 22] Invalid argument: 'log_-:.7z'"
- for addframe, add button/menu to allow viewing all frames already done, to help with consistency across frames.
- remove invalid characters from character names
- TIME:set up syllable profile analysis to allow for empty segments, assuming there is tone.
- ?cycle through tone groups to record based on volume of the group.
- set up summary table for XLP tone export
- record button makes a window in addmodd, if it is open (and it shouldn't, but they both use runwindow)
- record window exit doesn't exit process (so it is the same as done/next)
- widen "Do" menu item

- setup question: is <VN> [Ṽ] or [VN] (hopefully not both!)? —This is important for tone.
    - set lift.s['V'] distinct from, lift.v['V:'], and lift.v['Ṽ'] or lift.v['VN']?
- done? Update regex functions a=to allow for C(V)C\1, CVC(V)C\1, and C(V)C\1C\1, for vowel and consonant reports and checks

## Consider
- ways to change a frame after the fact... this seems to be a common problem

### Verify Problem
- ?put next undone buttons in dictionary recording pages, too
- fix multiple links to the same recording
- check that changes to S regexs don't break too much.
- diagnose pl/imp not appearing on recording screen
    - not really there?
    - pushed off the screen?
- Report not showing all examples in profile and sorting (50ish of 139 CV in bfj)

### Next Features
- add C and V sorting (and CV?)
- model form construct with fields for CV info and tone info, which may contain variables (HAB,CONT) in addition to H, L, etc.

### Some Day, if possible
- rectify (scrolling) Frame redundant windowsize fn
- have automatic choice of ps-profile go through all defined frames, then next most populous ps-profile
- include tone grouping in recording pages?
- XLP export (these are not likely to happen)
    - run dotexpdf (once you figure out where that is) to generate pdf?
    - run script to generate html?
    - figure out window specific variations (with Andy?)
- set tone report to ignore NA, if there is only one other value in that position (given the other values for the other frames).
- Fix 'ŋ' display problem in entry fields in MS windows (working fine in Linux)
    [x] noted issue in USAGE.md
- Make Wait window show background color and label message in MS Windows (working fine in Linux)

### For specific databases
    - fix key 7 problem for sxw
    -? figure out why multiple fuŋ entries aren't showing for recording on bfj
        - '6e2a67cb-6695-4536-bc55-423fad4f019b',<+
        - '7cdcddfc-5b9f-44bf-bfe5-d5ce164720cd',

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

# Version 0.7
- truncate definitions after three words or before parentheses
- group names in status table now listed if any is non-integer; otherwise counts
- skip verification if zero or one item in group.
- kicked quit up to tone recording
- quit after ten scroll frame configurations
- For recording windows, added a "skip to next undone"
- basic report includes co-ocurrance tables
- fixed addframe button not showing up with longer defninitions (moved to left)
- removed underlining in table headers (to italics)
- Removed invalid from prioritized lists (of words to record, profiles to select)
- removed function which was creating duplicate references to the same recording
- Sortǃ Now selects frame and continues, rather than making user hit sort again.
- CV gui report now making its own runwindow (not trying to reuse old one)
- change frame menu should be like change profile
- prioritized group and frame ordering on tone output, according to new function for comparing sets of dictionaries.
    - similar groups in each axis should now be more or less together.
- Added explanation with explicit statement of structured ordering of groups to XLP output.

# Version 0.6.2
- Added new digraphs and trigraphs for idiosyncratic Chufie' orthography
- made crash logs zipped and ready to send
- reports now exclude final N if appropriate to settings.
- store and reuse examples for tone groups, assuming they remain relevant.
    - unless removed by refresh button
    - relevance is determined by presence in group to check, so all will be reset on ps-profile and/or frame change.
- frame names now included in recording filenames

### UI
- New buttons to allow user to ask for a different comparison word for tone group
    - These seem to be working
    - with icon
- added thin themed vertical scrollbars
- clarified instructions when there is no tone frame yet.
- Added distinction for recording of dictionary words:
    - Record button gives slice of data as indicated on the main screen (selected ps-profile)
    - Menu (Do/Recording/Record Dictionary words...) gives a page for each slice, starting with largest
- made troughs on scrollbar follow theme (at least on Linux)
- Improved join page visibility (button to label, not button recreated)
- Added wait window to page creation and page final processing functions
- Fixed/improved JoinT appearance and function
- Added window with error message if tone group rename function attempts to use a name already in use.
- windows now (mostly?) on the screen for MS Windows
- Fixed problem where skipping first word in sort created a group button
- reverse selection of examples for recording; they now appear most recent first.
- put recording buttons on the left, so they would never be pushed off the screen
- pulled words submenu, made ps and profile selection in main "change" menu
- New Add/Modify Ad Hoc sorting pages
    - multiple tweaks to form
- New (Advanced) window to set user option for number of tone examples to record (1,5,100, or 1000)
- Add Frame window now removed check session (on bottom) on any keypress, in any field on the page (this should keep users from changing the information in the fields, then submitting before those changes are checked.)
- buttons for next CV profile on done screens:
    - Recording: next CV profile  
    - Sorting: next Frame or new frame, next CV profile or ps   
- show count of batch numbers on recording screen (x/y), where y is the total number per group you asked for.
- now resolve automatically conflicts between profile and type of check.
    - ad hoc sort group definition/modification/selection sets check type to Tone.
    - Selecting anything other than Tone in the menu changes to a CV profile.

### Under the Hood
- fixed problem with empty examples and tonevalues
- improved calculation of column width inside scrolling frame (not great, but better)
- cleaned up exit on a couple functions
- set file write to a .part file, until finished, before overwriting lift
- fixed some internals that were causing crashes on particular data.
- fixed sound card settings window overwriting settings
- converted ww=Wait(parent) to window method (with self.ww=Wait(self))
- implemented double canary system, to allow for joinT to progress without destroying and remaking page
+ Added treatment of long vowels, similar to consonant distinctions/interpretation
    + lift.s['VV'] includes xx for x in lift.s['V'] (though there is no VV regex made, as it would be superfluous)
    + lift.s['Vː'] includes x:, and xː (if both ':' and 'ː' are in the database) for x in lift.s['V'].
    -? Long vowels (lift.s['Vː'] or VV>V) require the same V formulation on both Vs:
        - VdVd and dVdV are OK, but not dVVd and VddV.
    + lift.s['V'] includes lift.s['d'], if present
    + lift.s['VV'] is interpretable as V, VV, or Vː
    + These lists test what is actually there before making the regexs...
    + diacritics now in vowel variables
- add tone frame shouldn't add the frame anywhere until final check completed
- Add morpheme now allows skipping any gloss language, and doesn't create gloss or definition nodes, as appropriate.
- Function to remove extra example fields (added by Chorus?), running now on each load

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
