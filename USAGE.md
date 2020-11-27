# Practical prerequisites
In case it isn't obvious, in order to use this program to actually do anything, one needs a LIFT database to check. Fortunately these are not hard to generate; LIFT is an open XML specification for storing lexical data ([https://code.google.com/archive/p/lift-standard/]). You can create a LIFT database by a number of routes:
- collecting words in WeSay ([https://software.sil.org/wesay/],[https://software.sil.org/wesay/download/])
  - while you're installing things, I highly recommend the excellent library of images that works with WeSay, the Art of Reading ([https://bloomlibrary.org/artofreading])
- building a dictionary in FLEx, and exporting to LIFT/WeSay.
- store your data in some other form (text, spreadsheet, database) and convert it to LIFT (*PLEASE* don't do this unless you *really* know what you're doing, and have a *good* reason to; the above are much easier, and less likely to result in data corruption)

# Tell A→Z+T where to find your database
The first time you run A→Z+T, you will need to select your LIFT database. Results and some preferences will be stored in that directory.
A→Z+T stores this location in `lift_url.py`, so you won't have to do this again. But if you need to check a different database, delete `lift_url.py`, and A→Z+T will ask where your database is again.
