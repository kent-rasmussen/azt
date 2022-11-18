<a href="fr/FLEX_COLLABORATION.md">Français</a>
# Does [A→Z+T] work with [FLEx]?

This is perhaps the most frequently asked question I get when introducing people to [A→Z+T], so I'll try to answer it here.

Unfortunately, people seem to come to this question from a couple different angles, so I'll try to lay those out, too:

## Assumption #1: I need [FLEx] for my work
Some people seem to think that a particular computer particular tool is needed for their work, without having actually engaged in the question of what their work requires. I've heard this kind of thing said about [FLEx], MS Office, Adobe, and other tools.

But I like to think of computer tools _like any other tool_, in that their usefulness depends on their usefulness in helping me **perform some task**. It is not the _tool_ that should determine what _work_ I should do, but the other way around.

So if you think you need [FLEx], I would ask you _what do you need it for?_ [FLEx] is designed for building dictionaries on the basis of texts collected in a segmental orthography (IPA or working, but nothing autosegmental). If that's what you want to do, and if [FLEx]'s complexity doesn't bother/scare you, then [FLEx] is probably the tool for you.

But I work in languages where the writing system isn't already established, and I work in tone languages. So I need to be able to represent and store primary data to build/justify an orthography. That representation must include both the segments _and the phonetic pitch_ of an utterance, as well as some searchable indication of the context where that utterance was observed —neither of which FLEx was designed to do.

It was this inability of [FLEx] to _store and manipulate primary tone data_ that led me to ask for (and ultimately start designing) another tool. This isn't necessarily a problem with [FLEx], it is just something it wasn't designed for —and I think it is helpful to be realistic about that. Yes, you can make [FLEx] do some of the things that I want, but after all the arm twisting to try to make it work, you basically have a very complex spreadsheet.

So [A→Z+T] is trying to be something else. A tool to store primary data in a way that respects the nature of tone. But also a tool that enables communities to get involved in the collection and analysis of their language. Which may not be what you need for your work.

## Assumption #2: [A→Z+T] is a bad tool if it doesn't interoperate seamlessly with [FLEx].

Despite the fact that [FLEx] and [A→Z+T] are not trying to do the same thing, many people hope/expect them to read and write the same database seamlessly.  This isn't bad; they are both editing lexical data, and both claim to read and write [LIFT]. In fact, FLEx interoperability was one of my primary reasons for choosing [LIFT] as the [A→Z+T] database format. Whatever it's imperfections, it is _the best open and publicly available standard for storing and sharing lexical data._ But [A→Z+T] and [FLEx] don't use [LIFT] in the same way.

[A→Z+T] stores data in examples, which contain the necessary segmental and pitch information, as well as the context where that surface form occurs. But these aren't the kind of examples one would normally put in a dictionary, so they look a bit weird in a [FLEx] database, and [FLEx] is not built to track them well (e.g., if you change a tone transcription, [A→Z+T] will know this, but [FLEx] may think you created a new example).

[FLEx], on the other hand, doesn't modify [LIFT] directly, but rather imports and exports it to [FLEx]'s own proprietary XML under the hood. So any weirdness in interpreting the [LIFT] standard (either in reading it or writing to it) happens internally to [FLEx], away from my ability to observe or control.

Furthermore, FLEx is designed to track and share incremental changes to a database using Chorus, which is so far inaccessible to a tool like [A→Z+T]. But even for [WeSay] (which is built on the same technology as Chorus), interoperability through Chorus is not seamless. Decisions it makes are not always made clear to the user, nor IMHO correct (for instance, some decisions prefer the data from the tool of the newer version, which may not be the newest data).

Given that [FLEx] developers just don't have the resources to develop new features, it isn't surprising that using FLEx to collaborate with a tool that didn't exist three years ago is a non-trivial agenda item.

## Assumption #3: A good workflow would involve synchronization between FLEx and [A→Z+T] on a regular basis.

Some people seem to think that bringing data in and out of [FLEx] on a daily (or at least regular) basis would be a good idea. While this theoretically shouldn't be a problem (given the above assumptions are clear), I think it betrays a misconception of the workflow that [A→Z+T] is designed to facilitate —namely, a community sorting process, rather than a traditional elicitation process. That said, there are times where a particular kind of edit is better done in [FLEx], though this is not the kind of edit I would expect most [A→Z+T] users to make without help —and I'm working to make the need for these fewer and fewer.

Assuming you have decided that you really do need [FLEx], and that you accept that some of the synchronization problems between [FLEx] and [A→Z+T] are due to [FLEx]'s maintenance mode development, it isn't necessary that you should open yourself to encountering those problems on a regular basis.

I don't know of any current hurdles to exchanging data on LIFT import and export (that's what Lexical Interchange Format is for); most of the problems I have heard of relate to the tracking of incremental changes. So, if you have data in FLEx, and you export to LIFT, then read/write that LIFT file for some months, then import it back into FLEx, then you should have problems fewer in frequency and kind.

One consequence of this work flow (as I understand [FLEx]'s current operation) is that a new project would be created on [LIFT] import. I don't know that [FLEx] allows importing a [LIFT] file back into a project from which it was exported, without either having those incremental changes tracked, or else serious problems in duplicating data (entries, senses, or examples). This would mean that any links between your lexicon and texts would need to be re-established, which may not be acceptable to you, if you work heavily in [FLEx] outside the lexicon.

[A→Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[CAWL]: http://www.comparalex.org/resources/SIL%20Comparative%20African%20Word%20List.pdf
