# Digraphs and Trigraphs in [A-Z+T]

When [A-Z+T] encounters new potential digraphs or trigraphs in your data, it will ask you to indicate which are actually digraphs or trigraphs in your data. That is, where two or three letters refer to just one sound.

## Initial Assumptions
[A-Z+T] initially assumes that all possible polygraphs (that I've told it about) _found in the data_ are actually polygraphs; this is what you see on the window with all the boxes ticked. If any one of those is actually a sequence of sounds in your language, untick that box, and AZT will treat it as a sequence of sounds in the syllable profile analysis.

If you are unsure about this, it is _probably_ safe to just leave them all checked, and see how the analysis works out.

If you go to this settings window intentionally but don't see anything to do, it may be because [A-Z+T] hasn't seen any potential digraphs or trigraphs in your data yet. Just come back after you have added more data; this shouldn't matter until you start sorting.

## Problems with Digraph and Trigraph settings
If there is a problem with your digraph settings, you should notice that some words don't fit in the syllable profile where they have been put, based on their pronunciations. Some words may have an extra (or missing) syllable, or a longer (or shorter) vowel, or a heavier (or lighter) syllable.

You should **check for this early**, as everything [A-Z+T] does is based on groupings of words by syllable profile, so changing syllable profiles will likely mean more work for you, as you will have to redo some of the sortings.

## Changing Digraph and Trigraph settings
To change these settings,
- First, make sure the [menus are shown](MENUS.md)
- Then select `Advanced`, then `Digraph and Trigraph settings`.
- Read the instructions (ask if something doesn't make sense)
- (un)select digraphs and trigraphs as appropriate, for each language
- Click `OK` to use these changes, or `Exit [A-Z+T] with no changes` if you want to start over.
- If you made changes, [A-Z+T] will automatically:
  - restart
  - redo the syllable profile analysis

[A-Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[CAWL]: http://www.comparalex.org/resources/SIL%20Comparative%20African%20Word%20List.pdf
