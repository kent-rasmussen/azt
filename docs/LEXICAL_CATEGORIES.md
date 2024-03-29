# Lexical Categories

Grammar studies abound with different terms for how to divide up different kinds of words and word parts. Given the variety of terms like *part of speech*, *grammatical category*, and *word class*, I thought it best to make a note here of what I do and don't mean by *lexical category*.

## Other Options
First of all, I have used the term *part of speech* mostly because it is known, not because it has a good theoretical basis, nor because how people use it corresponds well to a useful linguistic concept. But as I looked at the popular usage of this term recently, I think it is rather more harmful than helpful, so I will be moving away from it.  This is particularly because it evokes a prescriptive view of language, where I think it is best suited (e.g., "What are the eight parts of speech?"), but also because the divisions between the parts of speech that are known are not really what we're after. Case in point, the distribution of a pronoun is the same as that of a noun phrase. For many people, this means that pronouns have the same syntactic properties as a (whole!) noun phrase, e.g., noun, modifiers, and determiner.

I looked at using *word class*, but found other problems. Namely, whereas grammar books like talking about _words_, I typically deal in meaningful word _parts_, or lexemes. So to describe a noun stem/root as having a "word class" of noun, makes less sense to me than it aught.

I have also used the term *grammatical category* in the past, perhaps to the befuddlement of some. In at least one theoretical orientation, this term describes exactly what I am after: the categorization of a morpheme on the basis of distributional and inflectional properties. unfortunately, in half an hour of internet searchings, I couldn't find this in popular use anywhere (even among "popular" linguists), whereas I did find several uses of this term to mean something completely different: what might otherwise be called inflectional (incl perhaps derivational) categories.

## Issues at Stake for [A-Z+T] (functional and practical)
So there two issues important to me, in the use of lexeme categorization: one _functional_, the other _practical_. Functionally, it is obligatory that the words we compare have comparable morphosyntactic properties (Snider 2014). To accomplish this, we must compare words built on roots of the same class (whatever we call them), with the same inflectional and derivational affixes (whatever we call them). So the first, functionally important aspect of the category we need is that it controls for distribution, at least, if not also inflectional properties.  

So if you have a category that you call "pronoun", some of which only occur preverbally, and others of which only occur postverbally, then that category doesn't help you constrain the distribution of your data. On the other hand, most Bantu nouns are subclassed into groups that take separate affixes and agreement, while otherwise having the same syntactic distribution. Given that the affixes are not the same across subclasses, they _cannot_ appear in identical environments, in terms of morphology, though they otherwise do in their syntax —so this can be something of a judgment call to organize these either at the class/noun level or at the subclass/noun class level.

Which brings me to the *practical* consideration. Whatever term your prefer for this kind of categorization, and however you decide to organize your lexicon, you must put something in the 'value' attribute of the 'grammatical-info' tag (\<grammatical-info value="HERE"\>) for each sense in your [LIFT] lexical database. Whatever you put there (and however well or badly it is organized and principled in terms of your system as a whole), that will be used to organize work on your data in [A-Z+T]. So if you have "pronouns" with two different distributions (as above), you can give them _different_ grammatical-info/@value labels (and [A-Z+T] will treat them as _different lexical categories_), or you can give them the _same_ grammatical-info/@value labels (and [A-Z+T] will treat them as the _same lexical category_). And the same applies to a class of nouns that is subclassed into noun classes.

## Implications
In case the *practical implications* of the above are not clear, tone frames are a particular, defined syntactic context (in [A-Z+T] and elsewhere), so [A-Z+T] defines and organizes them by lexical category (as I assume this is constrained by distribution, at least). So, if you define a _pronoun_ tone frame of the form "__ V", whereas you have preverbal and postverbal pronouns together in that category, that frame will provide nonsense for the postverbal pronouns (which should have frames that look more like "V __").

For cases like noun (sub)classes, a frame can be designed to include the obligatory affixes on the noun (e.g., "__ V"), which has pros and cons (e.g., if you are trying to study the root, with an hypothesis that prefixes do not have all the same tone value). If your frame contains agreement morphology (e.g., "__ sm-V" or "__ agr-Adj"), then you will have to deal with that according to the options laid out [elsewhere](USAGE.md#tone-frames).

[A-Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[CAWL]: http://www.comparalex.org/resources/SIL%20Comparative%20African%20Word%20List.pdf
