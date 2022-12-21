# Prerequisites for Consultancy Help

I want to help as many people as I can get the most out of A-Z+T, and move forward the collection and analysis of consonant, vowel and tone data across Africa. To facilitate this goal, if you want help from me, I have drawn up a list of things you should do, below. These are not required to work with A-Z+T; you can do all kinds of work with A-Z+T under different terms, and I hope you do, if that's what you want. But I must keep my work organized, or I will have to help fewer people. So, if you take this list seriously, it will help me take you seriously. So here goes:

## Get set up on languagedepot.org
  - **do this first**, as it may take awhile to finish
  - You will need an account (username and password) for yourself first, which you can sign up for [here](http://public.languagedepot.org/account/register).
  - Once you have an account, sign in, and you will see instructions on the main page to ask for an repository for your language data. Basically, you will write an Email to admin@languagedepot.org, requesting an account with five lines of information. You want a **Dictionary** repository to work with A-Z+T; everything else should be straightforward.
  - **Wait** for a response from admin@languagedepot.org, which will give you your project id. It should be something like `<ethnologue_code>-dictionary`. If it isn't, please [forward the Email to me](<mailto:kent_rasmussen@sil.org?subject=Languagedepot-A-Z+T problem>) and I'll advise you how to proceed.
  - While you wait, install [Mercurial (Hg)](https://www.mercurial-scm.org/wiki/Download) so A-Z+T can make changes to your repository for you.

## Prepare your LIFT database
  - If **you have a database but not in LIFT** (i.e., in FLEx, or a spreadsheet, or an electronic or paper document), then you must get help converting it. Some conversions are easier than other (e.g., from FLEx); others are very difficult (e.g., typing from a handwritten notebook).
  - If **you don't already have a database**, and don't already use FLEx, ~~download WeSay and follow [the WeSay from Scratch directions](WESAY_FROM_SCRATCH.md) to set up your project in WeSay set up your project there.~~ start a new project in A-Z+T (you will need your language's ISO code)
  - Take a look at the [practical prerequisites](USAGE.md#practical-prerequisites) for your database, and see that yours has what it needs.
    - If you ~~followed the `WeSay from Scratch` directions~~ started your project in A-Z+T as above, you should be OK.

## Install [A-Z+T]
- Run [this file](RunMetoInstall.bat?raw=true) (or use the simple instructions [here](SIMPLEINSTALL.md)). If you have any problems with the batch file, please let me know, and consider moving to the [simple instructions](SIMPLEINSTALL.md). If you use the simple instructions, please work all the way down this page, and do everything on it. Don't stop unless you really can't continue. If you get stuck, please [Email me](<mailto:kent_rasmussen@sil.org?subject=Please help with [A-Z+T] Installation>) with specific questions or problems.

#Develop and Define Tone Frames in process (to do)

## Collect data in [A-Z+T]
- **Organize a meeting** of more (3+) speakers, for them to sort and record data together in A-Z+T. You can organize this as you like, but expect at **least two weeks** of full time work for everyone.
- At the meeting:
  - **Sort** data in [A-Z+T]:
    - As you sort,
      - each surface group should have **just one** pitch melody for the whole utterance, for each word in the group.
        -  if not, remove the different ones on the "Verify" page.
      - each surface group should have a **different** pitch melody than _every other group_.
        - Take the time to compare **each group** with _every other group_!
        - if some are the same, join them on the "Review Groups" page.
      - keep going, around and around, until the each group is just one thing, and each is different from each other.
    - Start with:
      - largest 2-3 syllable profiles for Nouns in each of four **tonally different** frames
      - largest 2-3 syllable profiles for Verbs in each of four **tonally different** frames
      - There is a lot more sorting you can do, but this should be the right place to start, and will be a good beginning to understand your tone system.
      - **Tonally different**: if you don't know what this means, plan on getting help from a linguist near you, or sorting on at least eight frames (You should have this sorted out above, before starting a workshop).

  - **Record** all sorted data in [A-Z+T]
    - Please pay attention to
      - **speak as naturally as possible**, without unnecessary pauses. Pauses may break your recording into multiple phonological phrases, making your recordings useless for tone study.
        - if the syntactic context of a frame requires a significant pause (>150ms), you should probably use a different frame.
      - include **the whole utterance** in the recording (don't clip the first or last syllable)
      - **not** include **extra space** before or after the utterance
        - In case this last one sounds petty, extra space in the recording wastes computer space, internet bandwidth, and time in listening. For instance, if you have utterances that are one (1) second long, but you record three (3) seconds for each, then you are taking up three times as much space as you need, all of which needs to be stored on a computer, and shared across the internet. And you are asking your listener (me, other collaborators, a dictionary user) to spend that extra time listening to each file without reason. Two seconds wasted may not seem like much, but across thousands of recordings, it adds up.
  - **Record** citation forms for at least the above (largest 2-3 syllable profiles for Nouns and Verbs)

## Collaborate and Get Help
- Once you have data you want feedback on, give me permission to read your languagedepot.org repository (Settings/Members/New Member), and [send me your questions](<mailto:kent_rasmussen@sil.org?subject=Please%20help%20with%20A-Z+T>)!

[A-Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[CAWL]: http://www.comparalex.org/resources/SIL%20Comparative%20African%20Word%20List.pdf
