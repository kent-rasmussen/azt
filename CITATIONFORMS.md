# Using Citation Forms
You may stumble across a notice in A→Z+T with the title "Convert lexeme field data to citation form fields?" and wonder what is up, so I'll try to give some basic background here.

The development of a dictionary can be seen as primarily involving two major pieces of data:
- citation forms:
  - often the response to the question "What is this?"
  - fully pronounceable
- lexeme forms:
  - meaningful word _parts_, which cannot be further divided and maintain meaning
  - not necessarily pronounceable

Typically, dictionary work starts by collecting *citation forms*, and gradually analyzes those forms into *lexeme forms*.
Sometimes, people store those _citation forms_ in _lexeme_ fields in a database, though this is typically in error.

Through the end of 2021, A→Z+T did not leverage this distinction, using lexeme fields when citation fields are not present. But as A→Z+T prepares to automate and facilitate word parsing, it will become more and more important to maintain this distinction. So it is important when working with A→Z+T that we keep fully pronounceable citation forms in the citation field, and analyzed word parts in the lexeme field.

If your database contains a mixture of both
- entries which have already been analyzed into a combination of lexeme and citation fields, and
- entries which have only fully pronounceable (and unanalyzed) data in the lexeme field (i.e., no or empty citation field)
The entries with only lexeme fields should have those lexeme fields converted to citation fields. Once this is done, your database will have only analyzed data in lexeme fields, and only pronounceable data in citation fields.

If this is an issue for your database (specifically, if you have more filled lexeme fields than citation fields), A→Z+T will offer to move the data for you. If you see this window, *please consider the decision carefully*. If you click
- "Move lexeme field data to citation fields":
  - A→Z+T will back up your database file with a name ends with `_backupBeforeLx2LcConversion`. You may want to make your own backup first, if you have any concern of this failing.
  - A→Z+T then iterates across all your entries, finding all that have `lexical-unit` (lexeme) tags which contain text.
  - for each of the above, it finds (or creates, if not there) a citation field.
  - if the citation field is empty (including newly created), it
    - copies the lexeme information to the citation field, then
    - deletes the lexeme field information.
  - You can compare this with your current lift file to the backup to see what changes A→Z+T made, and confirm that it made all and only changes you want.
- "No thanks":
  - You will eventually need to make the conversion yourself, either in FLEx, or with expert help.
  - You may get away with continuing to use A→Z+T without doing anything about this for some time, but
    - I have no intention of announcing this further (i.e., this is your last warning, in Feb 2022), and
    - I can't guarantee what kinds of errors you will see first, nor what you will need to do to resolve them.
