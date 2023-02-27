# Changing Syllable Profiles

Occasionally in the process of analysis, one comes across a situation where one wants to make **a change that impacts the syllable profile analysis.**

For instance, you may do the initial transcription, resulting in words of the shape CVC, CVCV and VCV (among other profiles, where C is a consonant, and V is a vowel). Then in the sorting process, you might
- sort CVC words, and find that some actually end (or begin) with a *vowel* differently than the others
- sort VCV words, and find that some actually end (or begin) with a *consonant* differently than the others
- sort CVCV words, and find that some have differently long first (or second) vowels (or consonants) than others.

## Different endings, beginnings, or length
**Differently** above is important, because you may have a consonant that starts *all* words you wrote as VCV, such as a glottal stop. This is actually very common in the world's languages, as it is physically difficult to produce a vowel initial word without some kind of onset.

Again, you might have the same vowel showing up at the end of *every* consonant final word, perhaps a shwa or some other default vowel. This is again not uncommon, due to the physical difficulty of producing words without some kind of vocalic release.

Similarly, you might notice that one of the vowels in CVCV words is longer than the other. This may be a more natural way of pronouncing words in a language, and may happen the same across all CVCV words.

In any of the above cases, if native speakers of the language didn't transcribe these newly discovered sounds initially, they can probably continue to be left off.

On the other hand, if you notice a consonant or vowel (either quality or length) for the first time in sorting words of a syllable profile, and it occurs on some words but not others, *you probably should write it*, and you will need the following instructions for **how to address this in [A-Z+T].**

## How to address new syllable profile contrasts discovered in sorting
During the sorting process, [A-Z+T] assumes that the syllable profile analysis is correct. Whether you use digraphs (e.g., `<ng>`) and trigraphs (e.g., `<ng'>`) or not, [A-Z+T] assumes it knows how to analyze words into a sequence of consonants and vowel sounds, so it can analyze words of the same syllable profile against each other. Because of this, in consonant or vowel sorting, [A-Z+T] will normally assume one vowel or consonant grouping is split from another, or joined with another, or renamed —but not changed into more or fewer vowels or consonants. Operations that change *the number of vowel or consonant sounds* necessarily change the syllable profile of a word, so they would result in words being compared against words of multiple syllable profiles —which would be a bad thing for these comparisons.

So, when a difference is discovered in sorting (which wasn't noticed in transcription), you must treat that situation carefully, as this is not normally expected in the [A-Z+T] sorting process. I have tried to make these instructions straightforward, but if they look too complex for you, please get help. **There is a real possibility of making mistakes that will cause a lot of work to recover from, if you don't fully understand what is happening here.** The process is essentially the same as the normal sort and rename process for [A-Z+T], except that we will pretend for a bit that *the new sound is part of a digraph of an adjacent sound*:
1. Sort as normal, making new ("different") groups for each thing that is different:
   - If you have CVC with both CVp and CVpə, they should sort into different groups for the C2 test (i.e., `<p>` and `<pə>`). This needs to be done wherever you see the vowel both present and absent for a given C2.
   - If you have VCV with both ʔaCV and aCV, they should sort into different groups for the V1 test (i.e., `<a>` and `<ʔa>`). This needs to be done wherever you see the consonant both present and absent for a given V1.
   - If you have CVCV with both CaːCV and CaCV, they should sort into different groups for the V1 test (i.e., `<aː>` and `<a>`). This needs to be done wherever you see different length for a given V1.
   - For each of the above, if you find that some groups (vowel or consonant) have only one of the two cases (extra consonant or not, extra vowel or not, long or short), then you don't need to split groups for that consonant or vowel. e.g., if all your `<i>` vowels are long, and all your `<a>` vowels are short, that difference can be taken care of in the next step.
2. In the appropriate *transcription* task (for either consonants or vowels)ː
   - Select the appropriate test (e.g. C1 or V2) to find *the groups you need to change.*
   - Select a group you created above that needs to be changed. New groups will be labeled as numbers at this point. So if you made a new group for the words that end with `<pə>`, or begin with `<ʔa>`, or have a long `<a>`, *it may well be called '1' or '2', etc., in the list of groups.*
   - Confirm that you are looking at the correct set of words by cycling through the words in this sort group in the example button, and by listening to the recordings, assuming you have made them.
   - Give the group a name that includes the syllable profile change that is needed as appropriate, e.g., `<pə>`, `<ʔa>` or `<aa>`. Note that this may imply an orthographic decision, if the sound contrast is not already in your writing system (e.g., [ʔ], [ə] or length). If so, **it would be wise to spend time discussing how you want to write this**, at least until a larger or more authoritative group can discuss it.
   - Note the warning dialog from [A-Z+T] about a syllable profile change, and understand its implications. You should not need to make any changes to digraph/trigraph settings yet, though you may want to note what has been added, as you will need to remove it later. This is because up to this point, [A-Z+T] thinks that `<pə>` is a digraph for *a single consonant sound*, or `<ʔa>` (or `<aː>`) is a digraph for *a single vowel sound*. This will be corrected later.
   - Repeat these instructions for each new group you created in #1 above. If you have groups as described in the last step (above, e.g., `<ʔa>` and `<a>`, and `<?e>` but no `<e>`, and/or `<i>` but no `<ʔi>`), then make sure that each of your singleton groups are appropriately named (e.g., initial `<ʔ>` in all the groups that have words with that sound), as well as your groups with and without the new sound.
3. Go into your digraph and polygraph settings (right click to get a menu to show the menus), and remove all the *apparent* digraphs and polygraphs that are not *actual* digraphs or polygraphs (i.e., `<pə>`, `<ʔa>`, and `<aa>` should not be marked as digraphs). This would be a good time to confirm that all your other digraph and trigraphs are correctly represented in [A-Z+T]. When you quit this page, [A-Z+T] will restart and redo the syllable profile analysis.
4. Confirm that words that contain the newly written  sound contrasts are now in the correct syllable profiles, i.e.:
   - CVp should be in CVC and CVpə should be in CVCV.
   - ʔaCV should be in CVCV and aCV should be in VCV.
   - CaːCV should be in CVVCV and CaCV should be in CVCV (assuming you distinguish vowel length in the [segment interpretation settings](USAGE.md#segment-interpretation), otherwise they should both be in CVCV)
5. If you get anything else, or if you run into any trouble with this process, [submit a bug](BUGS.md) and ask for help.

[A-Z+T]:  https://github.com/kent-rasmussen/azt
