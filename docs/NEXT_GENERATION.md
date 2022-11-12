# A→Z+T 2.0

It occurs to me that A→Z+T could be superseded by a superior modeling of the card sorting process on a client-server model.

Such a model would probably need to happen in javascript, at least on the client side, with a web server (either in python or javascript, I assume) running perhaps on a raspberry pi.

Practically, such a server would run headlessly off of a 5V power supply for continued operation through power cuts.

Clients would run in multiple mobile phones, attached to the server through wifi —which would not need to be otherwise connected to the internet.

This would allow for the "multiple and contradictory input" I described as currently impossible in my book chapter.

The sort process would then look like this:
- Server side:
  - A word is assigned to a client whenever a client doesn't have one assigned (e.g., on startup, or when sorts a word), if an unsorted word exists.
    - a word/card should be in only one person's hand at a time, to avoid it being sorted into two different groups at a time. This accurately models pen and paper methodology.
  - When all words are sorted (or even just assigned?), a group is assigned to a client for verification whenever a client doesn't have one assigned (e.g., on startup, or whenever a group is verified), until all groups are verified.
  - When asked, assign a group to a user for verification.
    - a group can be assigned to multiple clients at a time. Update each's list with unsorting done by the other. If each unsorts the same word before such an update completes from the other, be cool.
  - at all times:
    - mark (un)sorted words
    - mark (un)verified groups (e.g., whenever a word is sorted into it)
- Client side:
  - When assigned a word, a client sees the word segments and gloss, and scrolls through a list of groups already there:
    - short press on a group to sort into that group
    - long press on a group to click-and-drag it into another group (i.e., make `sort` and `join` operable on one page)
    - maintain edge button to cycle through example words.
    - press 'new group' or 'skip' as needed (?no long press value).
    - unassign/give back word for someone else to sort (unsort)
  - When assigned a group to verify, user scrolls through a list of words with segments and glosses:
    - click on any that don't belong to unsort it.
    - click "these are all the same" when that applies.
  - When not assigned, may select a group to verify (again).
