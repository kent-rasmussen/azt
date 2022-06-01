# [A→Z+T](https://github.com/kent-rasmussen/azt) User Interface Guide
[A→Z+T](https://github.com/kent-rasmussen/azt) aims to address a wide range of users, including people with no experience whatsoever in using a computer. In doing so, I have made some decisions that might be confusing or unintuitive to people who are more familiar with other computer programs. Hopefully this page will help with that.

## Guess and check
There are by design few irretrievable user errors in [A→Z+T](https://github.com/kent-rasmussen/azt). If you accidentally open a window to change a setting, just close it. If you accidentally change a setting, just change it back. If you accidentally added a word to the wrong group, remove it in the next step. If you accidentally removed a word from a group, sort it back into the same group, etc. Typically, the worst that will happen is that you will lose some time while [A→Z+T](https://github.com/kent-rasmussen/azt) does what you accidentally asked it to. This may be several minutes, in the case of reports or a syllable profile analysis, but in most cases much less.

So, if you want to know what clicking somewhere does, try it and see. If you do this and think you made an irretrievable error, please write me, and I'll help you figure out how to proceed. But I haven't seen this yet, and don't think it will happen to you.

## Hover to get a tool tip
If you hover over a setting, you will likely see a short description appear, which will tell you what will happen if you click there.

## Click to Change a Setting
There are no menus by default in [A→Z+T](https://github.com/kent-rasmussen/azt). Rather, click wherever a setting is displayed to change it. So, if you want to change
  - the interface language: click on where it says "Using \<interface language\>".
  - a gloss language: click on the line where it says "Meanings in \<gloss language\>...".
    - If that line ends with "only," click on that to add a second gloss language.
    - If it shows a second gloss language, click on that to change or remove it (by selecting "just use \<first gloss language\>")
  - the current syllable profile: click on the syllable profile in the line that says "Looking at \<syllable profile\> \<lexical category\> words (\<count\>)" (the count is calculated, not a setting you can change…)
  - the current lexical category: click on the lexical category in the above line.
    - you can also click on the lexical category in the title "\<\> progress for \<lexical category\>", on the right.

### You can have buttons, if you really want them
Some people have expressed concern with the above, because they want to know exactly what is clickable before clicking on it. Pretty much everything is clickable. But if you _really_ want buttons, you can have them by right-clicking on the main window (almost anywhere), and selecting "Show Buttons."

## Navigate syllable profile and check/frame through the status table
The status table (which appears after you have done some work) is organized in rows by syllable profile, and in columns by segmental check or tone frame (as appropriate). Click on any cell to move to analyzing that slice of data by that check/frame (in this way, you can change both at the same time, or either as you like).

Both axes on this table also have "Next" buttons, to allow quick navigation to a profile or check that is not already on the table.

### Some advanced functions are in a menu
I have deliberately hidden the menu, to keep people from being distracted by it, but also to keep advanced functions for advanced users. Some of the functions there are needed, but not by most people, and certainly not most of the time.

Right click almost anywhere on the main screen to get a context menu, and select "Show Menus", and they will appear.

The Advanced menu items should all be recoverable (Even "Change to another database"), but it might not be obvious how to do that, especially if a user has already selected one of these menu items in error.

The menu items above the line impact how [A→Z+T](https://github.com/kent-rasmussen/azt) looks at your database:
  - which database it is analyzing (this should only be needed if you work on more than one database)
  - what valid digraphs and trigraphs are in the language (this is run automatically if [A→Z+T](https://github.com/kent-rasmussen/azt) finds a new plausible digraph or trigraph, but if you find your settings aren't correct, you may need to run this manually)
  - how to interpret various segment types (e.g, nasals, depressors, other sonorants). If you want to use this function, you should really know what you're doing, and the consequences for sorting before and after this change (as words will move from one syllable profile to another).
  - redo the syllable profile analysis or status file (no harm doing either of these, but they each take time)

The menu items below the line have more to do with the sorting process:
  - ad hoc sort groups (to analyze specific words, without respect to syllable profile)
  - restart the sorting process
    - for words previously skipped
    - for a group previously verified
    - for groups previously marked distinct
