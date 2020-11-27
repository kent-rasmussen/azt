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
- part of speech indication:
  - stored in `sense/grammatical-info@[value]`
  - whatever ps names (e.g., 'Noun', 'Nom', 'Njina', 'noun', 'n', etc) are in your database is what you will select from to study, so name them appropriately for your work
  - entries with no ps value will be left out

A→Z+T will place sorting information in the `entry/sense` node, under an example node for each context/frame:
- form
- sound file name
- translation
- frame name
- subgrouping name

Results of the analysis of multiple frame groupings (e.g., from the Tone Report) is placed in a separate `entry/sense/field[@type='tone']`, as this is a summary/analysis of the values contained in the example nodes.

# Tell A→Z+T where to find your database
The first time you run A→Z+T, you will need to select your LIFT database. Results and some preferences will be stored in that directory.
A→Z+T stores this location in `lift_url.py`, so you only have to do this once. But if you need to check a different database, delete `lift_url.py`, and A→Z+T will ask again where your database is.

# First Run: Be Patient and Orient yourself
### Syllable Profile Analysis
If you open A→Z+T without a saved syllable profile analysis file, it will first open your database (once it knows where it is) and go through the entries there, and sort them by syllable profile and part of speech (CVC v CVCV for each of Nouns and Verbs, for example). This can take a couple minutes. If you have a terminal open, you should see its progress.

### Configuration File
If you open A→Z+T without a saved configuration file, you will be greeted with a number of windows asking what you want to check, and how. Some assumptions the program makes for you (based on your LIFT file), others (at least for now) it asks you for.

### The Main Window
On the upper left of the main window, each of these settings are indicated:
 - interface language
 - analysis language
 - gloss language(s)
 - part of speech
 - syllable profile
 - type of check (i.e., C, V, or T) and current stage

The main window menu allows each of these to be changed as needed.

### Tone Frames
Assuming you don't have any tone frames set up yet, you should do that in the Advanced menu. Note the *name* is important, as this is how you will refer to this frame, and how it will be identified in your database in the future (until/unless you change that). So if you're testing the plural form, something like "Pl" or "Plural", or "Pluriel" might be appropriate --but this is just a name, so make it distinct but useful to your workflow.

I hope this window is otherwise clear. The frame calculator is not particularly smart; it just puts content before and after the form and gloss for each word, so you need to give it that information. If that information (in the form or gloss) alternates in agreement or harmony with the lexicon word forms, you should think through how you want to resolve potential clashes, e.g., by including all options in the frame, or allowing for ungrammaticality:
- `pl form: '__s/z/ɪz'` (with all possible forms in your example)
- `pl form: '__s'` (knowing that dʒədʒ+pl will come out 'dʒədʒs', not 'dʒədʒɪz')

Once you have the form and gloss content in the appropriate boxes, click on 'see it on a word from the dictionary', and you will get the frame as you have defined it applied to some word (in the filter you have currently set). You can try this on a number of words by continuing to click that button, to see how it will look on different entries. There is no easy way to change this frame after you define it, so I encourage you to get it right before moving on. when you are happy with the frame, click on "use this tone frame".

If you absolutely regret a tone frame you have set up, all your frames are stored in `<lift filename>_ToneFrames.py` next to your lift file. Careful editing this, though, you may need to redefine all your frames if you corrupt this file.

# Subsequent Runs: Sort, and Follow Directions
Once you have done any sorting, to the right on the main window you will see a status pane, with groupings by syllable profile and check stage (for one part of speech and check type at a time). To see progress for another check type or part of speech, switch to that check type or part of speech.

The program is designed to step through the process relatively automatically; once things are set up, you should just have to open the program, and click `Sort`. If you need a break, click quit, and your progress should be there when you return.
You will, of course from time to time want to move to another part of speech or syllable profile, or check type. That can again be done on the main window menus, and the next time you click `Sort`, the appropriate checks will be launched.

If any of the directions are unclear or inappropriate in any way, please let me know so I can fix them.

The UI is currently in French and English; if you want to translate it into another language, please let's talk!

# Advanced Usage: Reports and Recordings
Once you have done some sortings, it makes sense to run a report. The tone report will show your groupings in just one frame, if that's all you have done, but its real value lies in comparing values across multiple frames, so you'll want to check a couple tone frames before doing much with the tone report.

Recording can be done at any point where at least one frame has been at least partially sorted, but when a word is presented for recording, each example (sorting context) is presented for recording. So if you sort one field, then record, then sort the next, you will see your earlier recordings again. Recordings seem to move rather quickly, so I recommend putting them last in your workflow, and do them all at once —at least once you've tested that they're working correctly with your sound card, etc.

Sound card settings can be adjusted and tested in the advanced menu —be sure to record and play at the settings you want, to make sure your sound card can handle them.
