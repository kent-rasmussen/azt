# A-Z+T Changelog

#UW priorities:
- sorting by click and drag
- check recording and transcription tasks are working normally
- ?other comparative wordlists

#Next up:
- rework USAGE.md
- Parsing:
  - Addition of second forms (primary data)
  - Parsing of lexeme forms (analysis)
  - writing of lexical categories (analysis)
  - Store affixes in entry and elsewhere (new settings file?)
  - Clarity for user wrt what is data (i.e. lc, pl, imp), and what is analysis (i.e., lx, ps) —in the presentation of the task itself, and in the documentation
- Migration to working on the appropriate form, synchronizing across frame definitions, etc.
- Catch up on translation
- make singleton reports run not in background, or give user more helpful info, if analysis isn't done.
- ?check on bug with getprofile in reports bringing up taskchooser; fixed in other tasks, but not reports?
- make showoriginalorthographyinreports a UI switch

# Version 0.9.11
- Finished parsing, though not always used. There is now a task to add and parse words in one step, and another to parse words added earlier.
- use of pictures (some from open clipart, first 110 from stability)

# Version 0.9.8
- initial Git integration should now be smooth, with initial clone and init, both for data and a flash drive
- demo database creation now in Choose LIFT database dialog. Can be specific to any gloss language in the stock CAWL.

# Version 0.9.7
- Substantial reworking of reports, which all now run in the background, and with improved initial placement of tables.
- Git integration works, both for updating A-Z+T and for language data. If your data is in a git repository, A-Z+T can make automatic commits for you, as well as pull and push from/to a respository on flash drive for sharing.

# Version 0.9.4
## Zulgo workshop tweaks
- lots of issues surrounding weird interface on their computer. For instance, the square consonant pushes everything off their screen, becausae of large space in buttons...
- A number of additions to make the update process smoother (now you can restart or retry, as appropriate, from the notification window)
- Multiple attempts to fix auto-reboot on Windows —sorry, nothing working yet.

# Version 0.9.3
  - Consonant and vowel sorting and renaming done, **except for renames that change Syllable profiles**
    - If you change syllable profiles (e.g., change o>ou, or iy>i), your results will not be predictable. I recommend if you do this, immediately restart A-Z+T, and redo a syllable profile analysis. I am working to account for this, but am not done yet.

# Version 0.9.2
- Windows batch file now
  - downloads and installs from USER/Downloads
  - gives user indication of download size in advance
  - makes unique names for repo and program link
- Fixed bug where functions called for objects created after wordlist collection, when wordlist collection wasn't done yet.
- If analang is guessed by filename, go back and tell lift object about it (at least for pss dict)
- Guide for OWLs used to FLEx

# Version 0.9.1
- SILCAWL now converts template ps to local values
- Set up ps sublcass to use '{}-infl-class'.format(self.kwargs['ps'] trait
- Set up morphtype trait URL
- Use button column variable to give up to three columns for sorting
- fixed bug leaving old sound file links
- removed MS Windows filename illegal characters from sound file names
- fixed scaling problem for smaller screens (had made big buttons)

# Version 0.9
- Rendering works now with Charis 6.0 font name, and more efficiently
- fixed screen scaling
- added new icons to better distinguish tasks
- fixed soundcard bug, removed buggy parameter option
- scroll sound card options, remove from default tasks
- remove wordy messages, move to tooltips
- improve logic for empty or missing data nodes
- added hg ignore functionality, with some defaults

# Version 0.8.9
- Complete rework of UI, now task oriented, with tasks divided by data collection and analysis functions.
- mercurial (if installed) now adds
  - ProfileData.dat
  - ToneFrames.dat
  - VerificationStatus.dat
- put UF fields in form/text nodes
- (non)-default report now more intuitive. If sort since last report, report runs again.
- User also has button to rerun analysis manually.
- Check for sound card now shows on every sound task beginning.

# Version 0.8.7
- changed .py config files to .ini and .dat, with clearer and simpler syntax. This should automatically migrate, but please let me know if it doesn't.
- should put those files into hg repository
- sendpraat should now be working, if installed
- massive changes under the hood:
  - ui.py extracted
  - new objects for examples, parameters
  - Hg should now track all .dat files (not .ini, per user)

# Version 0.8.6
- added referify data for current subgroup
- give warning if user is going to undo analysis regroupings
- mark a sensid to sort again without losing the sound file attached to it.
- major overhaul to LIFT urls, including class to generate them and catalog to store them
- major overhaul to framed data, including class to generate and catalog to store
- Added comparison group button for rename framed group window (to help with transcriptions)
- added actual groups by datapoint for non-default tone reports
- Reworked and multiple improvements to naming groups:
  - playable buttons
  - praat link to sound file
  - comparison button(s)
  - navigation buttons to continue through groups
- added interpretation of glottal stop into sdistinctions.
- added settings for interpretation of trigraphs and digraphs
- multiple fixes to segment interpretation settings
- set up mail of bug report, and links to webpage documentation

# Version 0.8.5
- reworked buttons and UI on transcription window
- comparison option for transcription window
- refresh group buttons now iterate through list (only random on first try)
- context menu to hide group names, in case they are distracting
- status table key and refresh/save settings option in upper left corner
- added rendering field where entries may contain combining characters that don't otherwise show up (in entry fields).
- Added SILCAWL (for later use)
- Prepped addition of XLP transforms
- Improved logic for next frame in transcription window, more sensible, less breaky
- added landscape option for sections, used when summary table is more than 6 columns wide
- split tables over seven columns wide into multiple tables
- call praat in recording buttonframe and in playable groupbutton (with tooltips)
- end cleanly on exit
- new FramedData and related classes
- fix problem with empty tone group node not presented for sorting

# Version 0.8.4
- added number of groups to XLP table
- non-default reports now end with 'mod' in filename
- added table of frame values for join UF groups window
- name groups doesn't crash on no groups selected; guesses
- redo group rename UI, add unsort button
- Various UI and documentation improvements
- Added button to rename groups which pulls a sense from that group (if the analyst decides it doesn't belong, to mark for resorting)

# Version 0.8.3
- fixed wav file link problem; now filename only in LIFT, relative link in reports.
- constrained search for language forms to analang (for multilingual dictionaries)
- don't crash on weird senseids
- fixed error on sound card not found to just not play (instead of crashing)
- fixed error of crash on PIL not installed.
- fixed error on trying data again
- updated documentation
- Made a simple output with characters that make invalid words (and the number of words impacted), so people can see them before noticing that words are just not there.
- Added context menu to make smaller font theme, for where that is helpful.
- set record button frame to notify user (and not make live buttons) where there is not audiolang set.
- only auto-add link if audiolang is specified.
- fixed window exit issues
- fixed numerous crashes on window exit
- removed final "\_" in sound filenames, left in legacy forms
- improved detection of screen resolution
- ratio of actual/expected resolution used to scale fonts an images, so it should look the (more or less) same whatever the resolution is.
- store font image renderings for later use, and use them
- XLP: don't print empty listWords, and don't print examples without at least one listWord
- autorefresh on playable buttons, if there is no sound file to play (up to the number of words to pick from, then give up)

# Version 0.8.2
- moved PyAudio functions to module, improved function
- Added glottal stop distinctions similar to Nasal distinctions
- Added redo status file (will not redo verification status, but will recover groups.)
    - Iterates across profilesbysense entries for ps and profile
    - looks into LIFT file for groups present
- added main_buggy.py and more logging in exception tracker
- cleaned up blipping on wait window
- checked on wait window in verifyT
- added ps and type buttons to all status boards
- fixed pl/imp not appearing on recording screen
- added field name (pl/imp) to filenames
- Every setting now has at least one button
- Context menu working correctly
- fixed but where CV type wouldn't set with ad hoc group as profile (it now resets/guesses the profile)
- New file name schema is working correctly field name (and type if name='field')
- new updatestatuslift, to add verification info to lift file, including removing on unverification, etc. Status is now stored in the LIFT file, for each sense.
- reduced writes to LIFT file, where AZT iterated across multiple changes
- fixed some syntax errors
- fixed MS Windows Unicode issue
- added user accessible switch between labels and buttons on the main screen (via context menu)
- cleaned up exiting fuctions
- fixed recording filename problems
- updated writing to lift file
- updated references to updatestatus with appropriate updatestatuslift calls
   - check name changes on groups and frame names
- removed "different" button from sort page, until at least one button is there
- added window to rename surface groups with a single button (with refresh) for the group, to play sound. This is a modification of the rename while verifying window (but with sound button, and next group button)
- fixed nbsp printing out as code point

# Version 0.8
- set up ad hoc groups to be more permanent:
    - saved to file
    - reloaded after reanalysis
- fixed scrolling window not wide enough in frame dialog
- numerous minor fixes
- set up on different input and output sound cards
- tone frames window now scrolls
- temporary fix for reconfigure scrolling window frame problem
- made function to add link if sound file is there (does nothing if link already there).
    - set up alternation, to accept either sound file nomenclature: w/wo location
- moved check analyses up to point of changing frame or profile (as appropriate), to keep from continuing to run it at other times.
- Set title in add/mod ad hoc group window to indicate if adding or modding
- split and regularized profilecountsValid and profilecountsValidwAdHoc.
- for Join window, don't ask if only one (avoid nonsensical "these are all different").
- Join window now removes second group from groups variable.
- included profile count in status table.
- make refresh example button only appear if there are at least two examples to pick from
- make status table into buttons for cells, which set profile and frame. (from CH)
- fixed sort logic to exit on exit (moved on), including recursive joinT funtions
- toneframetodo is now sensitive to the need to sort, as well as verification.
    - so "next frame" will give you the next frame with unsorted data, even if the known groups are all marked as verified.
- gettonegroups now removes groups from the list of verified groups, if they aren't actually in the lift file.
- observation that joinT page was (at least sometimes) removing an item (at least) from a group (at least), then giving the join page again, resulting in one less group in at least one case (sorting five elements over four groups). The tone report shows a group of [''] for that element, which is no longer in the join list of buttons.
    - This issue was caused by underspecificity in lift.rmexfields()
- Status table scrolls now
- made ps title a button to change ps
- made sort button in largest title case, with more padding
- highlight active cell (or row, if no frame)
- put refresh button on left (to not move)
- On 'finished sorting' window: include profile in title, rework next buttons
- Tooltips added in multiple locations

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
- moved self.tonegroups to self.status[self.type][self.ps][self.profile][self.name]['groups']
- No longer writing ui_lang.py on each run
- Breaking lines importing to XLP (for column headers)
- indicating progress verified/present and sorted status in main window (with !)
- dictionaries written to settings files are now pretty printed, for easier (human) reading.
- conversion to new status schema is now automatic, once any work is done on a ps-profile slice.
- Added logic for manual adjustment of tone groups
  - Separatee out logic to draft tone groups; you can now run tone report with or without analysis (without in advanced menu)
  - Allow creation of reports without auto drafting (in advanced menu)
  - document new tone groups functions

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
- Added page to instruct A-Z+T how to distinguish certain segment classes
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
