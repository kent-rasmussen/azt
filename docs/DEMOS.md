# Demonstrating [A→Z+T] (or just trying it out)

You may want to try out [A→Z+T] with real language data without having a database yourself, that you are willing to make changes to. This may help you better understand [A→Z+T] yourself, or show it to others.

## Create a Demo Database
To **create** a demo database,
- Open the `Select LIFT Database` dialog, either by
  - Opening [A→Z+T] without a LIFT file (e.g., for the first time), or
  - Open the dialog from another project:
    - make sure the [menus are shown](MENUS.md)
    - Then select `Advanced`, then `Change to another Database (Restart)`.
- In the `Select LIFT Database` dialog, select `Make a demo database to try out [A→Z+T]`.
- Select a language to analyze (from the glossing languages in the stock [CAWL])
  - you may select to keep that language as a glossing language, as well.
- [A→Z+T] will automatically:
  - Make a copy of the stock CAWL database
  - Put stock gloss information for that language in [citation form fields](CITATIONFORMS.md)
  - write that file to a new `Demo_<lang>` directory your home folder
  - restart with that file.

## Use a Demo Database
To **use** a demo database:
- On creation (above): it should appear automatically
- Afterwards: select it from the list of databases on your computer, in the `Select LIFT Database` dialog

[A→Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[CAWL]: http://www.comparalex.org/resources/SIL%20Comparative%20African%20Word%20List.pdf
