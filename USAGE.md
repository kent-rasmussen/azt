# Practical prerequisites
In case it isn't obvious, in order to use this program to actually do anything, one needs a [LIFT](https://code.google.com/archive/p/lift-standard/) database to check. Fortunately these are not hard to generate; [LIFT](https://code.google.com/archive/p/lift-standard/) is an open XML specification for storing lexical data . You can create a LIFT database by a number of routes:
- collecting words in [WeSay](https://software.sil.org/wesay/) ([Download here](https://software.sil.org/wesay/download/)).
  - WeSay uses LIFT natively, so the same repository can be used for WeSay and A→Z+T (though I wouldn't reccomend you have them both open at the same time).
  - WeSay is [Chorus](https://software.sil.org/chorushub/) enabled, which allows easy tracking of changes and off-site archiving.
  - While you're installing things, I highly recommend the excellent library of images that works with WeSay, [the Art of Reading](https://bloomlibrary.org/artofreading)
- building a dictionary in [FLEx](https://software.sil.org/fieldworks/), and exporting to LIFT/WeSay.
  - there is an active [list of users](flex-list@googlegroups.com) to help with problems doing this.
- store your data in some other form (text, spreadsheet, database) and convert it to LIFT (*PLEASE* don't do this unless you *really* know what you're doing, and have a *good* reason to; the above are much easier, and less likely to result in data corruption)

# Tell A→Z+T where to find your database
The first time you run A→Z+T, you will need to select your LIFT database. Results and some preferences will be stored in that directory.
A→Z+T stores this location in `lift_url.py`, so you only have to do this once. But if you need to check a different database, delete `lift_url.py`, and A→Z+T will ask where your database is again.
