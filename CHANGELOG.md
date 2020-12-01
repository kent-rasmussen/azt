# In Process

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
