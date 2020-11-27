# Practical prerequisites (LIFT file to check)
In case it isn't obvious, in order to use this program to actually do anything, one needs a [LIFT](https://code.google.com/archive/p/lift-standard/) database to check. Fortunately these are not hard to generate; [LIFT](https://code.google.com/archive/p/lift-standard/) is an open XML specification for storing lexical data. You can create a LIFT database by a number of routes:
- collecting words in [WeSay](https://software.sil.org/wesay/) ([Download here](https://software.sil.org/wesay/download/)).
  - WeSay uses LIFT natively, so the same repository can be used for WeSay and A→Z+T (though I wouldn't reccomend you have them both open at the same time).
  - WeSay is [Chorus](https://software.sil.org/chorushub/) enabled, which allows easy tracking of changes and off-site archiving.
  - While you're installing things, I highly recommend the excellent library of images that works with WeSay, [the Art of Reading](https://bloomlibrary.org/artofreading)
- building a dictionary in [FLEx](https://software.sil.org/fieldworks/), and exporting to LIFT/WeSay.
  - assuming you want to get the checked database *back* into FLEx, you want to use send/receive for WeSay. Import/Export (a different process) can work, but there is no protection against overwriting your data, without doing backups yourself.
  - there is an active [list of users](https://groups.google.com/g/flex-list) to help with problems doing this.
- store your data in some other form (text, spreadsheet, database) and convert it to LIFT (*PLEASE* don't do this unless you *really* know what you're doing, and have a *good* reason to; the above are much easier, and less likely to result in data corruption)

LIFT databases can be minimal or very complex. For the purposes of running A→Z+T, you just need the following:
- citation or lexeme forms (tagged with your language code, of course)
- glosses or definitions in at least one language (again coded for gloss language)
- part of speech indication (whatever ps names are in your database is what you will select from to study, and entries with no ps will be left out).

Sorting information will be placed in entry/sense node, under an example node for each context/frame:
- form
- sound file name
- translation
- frame name
- subgrouping name

Results of analysis of multiple frame groupings is placed in a separate entry/sense/field[@type='tone'], as this is a summary/analysis of the values contained in the example nodes.

# Tell A→Z+T where to find your database
The first time you run A→Z+T, you will need to select your LIFT database. Results and some preferences will be stored in that directory.
A→Z+T stores this location in `lift_url.py`, so you only have to do this once. But if you need to check a different database, delete `lift_url.py`, and A→Z+T will ask again where your database is.

# First Run: Be Patient and Orient yourself
If you open A→Z+T without a saved syllable profile analysis file, it will first open your database (once it knows where it is) and go through the entries there, and sort them by syllable profile and part of speech (CVC v CVCV for each of Nouns and Verbs, for example). This can take a couple minutes. If you have a terminal open, you should see it's progress.

If you open A→Z+T without a saved configuration file, you will be greeted with a number of windows asking what you want. Some assumptions the program makes for you (based on your LIFT file), others (at least for now) it asks you for.

On the main screen, each of these settings are indicated:
 - interface language
 - analysis language
 - gloss language(s)
 - part of speech
 - syllable profile
 - type of check (i.e., C, V, or T) and current stage

The main window menu allows each of these to be changed as needed.

#Subsequent Runs: Sort, and Follow Directions
Once you have done any sorting, to the right on the main window you will see a status pane, with groupings by syllable profile and check stage (for one part of speech and check type at a time). To see progress for another check type or part of speech, switch to that check type or part of speech.

The program is designed to step through the process relatively automatically; once things are set up, you should just have to open the program, and click `Sort`. If you need a break, click quit, and your progress should be there when you return.
You will, of course from time to time want to move to another part of speech or syllable profile, or check type. That can again be done on the main window menus, and the next time you click `Sort`, the appropriate checks will be launched.

If any of the directions are unclear or inappropriate in any way, please let me know so I can fix them.

The UI is currently in French and English; if you want to translate it into another langauge, please let's talk!
