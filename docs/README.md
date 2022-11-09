<a href="https://gitlocalize.com/repo/7965/fr?utm_source=badge"> <img src="https://gitlocalize.com/repo/7965/fr/badge.svg" /> </a>
<a href="fr/README.md">Français</a>
## Simplest install on [MS Windows](SIMPLEINSTALL.md) or [Linux](SIMPLEINSTALL_LINUX.md)
## If you want consultant help, see also [this page](HELP_PREREQUISITES.md)

# A→Z+T ![CV](../images/AZT%20stacks6_icon.png "AZT")

[A→Z+T][AZT] is designed to accelerate community-based language development, supplemented by (not as a replacement for) formal linguistic training. It does this by systematically checking a dictionary (and thus a writing system), with respect to consonants, vowels, and tone.

You can collect a wordlist from scratch in [A→Z+T][AZT], if you don't already have one created elsewhere, but parsing roots is still in development, so for now you should do that elsewhere (e.g., [FLEx][FLEx] or [WeSay][WeSay]) if your citation forms have obligatory affixation.

[A→Z+T][AZT] work results in a lexical database which is checked, backed up with sound files, and stored as [LIFT][LIFT], an open XML format designed for sharing lexical data. So this database should be forward compatible with other tools that can read [LIFT][LIFT], e.g., [WeSay][WeSay] and [FLEx][FLEx].

## If you currently use FLEx, and want to understand what A→Z+T is and decide if you should use it, please see [this page](OWL_GUIDE.md).

<!-- It is designed to *supplement* (not replace) formal training, on the one hand, and *facilitate* a particular kind of language development on the other, so it may not do what you want —it certainly does not do everything. If you want to get as many people involved in the development of their own language as possible, in a manner that results in a checked lexical database backed up by sound files, then this tool is for you. -->
## Why
See [RATIONALE](RATIONALE.md) for more information on why one should use this tool; see [Why Work with Computers](WHYCOMPUTERS.md) to see [A→Z+T][AZT] compared with pen and paper participatory methods. See [Why Work with Communities](WHYCOMMUNITIES.md) to see [A→Z+T][AZT] compared with more traditional field methods

## What
[A→Z+T][AZT] is written in [Python](https://python.org) (3+) and [Tkinter](https://docs.python.org/3/library/tkinter.html), with [PyAudio](https://pypi.org/project/PyAudio/) for recording and playing sound files. [A→Z+T][AZT] produces reports to the screen, plain text files, and [XLingPaper](https://software.sil.org/xlingpaper/) XML documents —which can in turn be easily converted to PDF and HTML, each with clickable links to sound files.

## How
To get the program, run `git clone https://github.com/kent-rasmussen/azt.git` in a terminal, or download through the green `code` button on the main page.

To run: `python main.py` (or `python3 main.py`, as appropriate for the (3+) version of python on your system)

See [INSTALL](INSTALL.md) for more help installing; see [USAGE](USAGE.md) for how to use this tool.

See [CHANGELOG](CHANGELOG.md) to see features by version, and [ROADMAP](ROADMAP.md) to see what I'm working on next.

## Bugs
See [BUGS](BUGS.md) for information to send me if you have problems; see [KNOWNISSUES](KNOWNISSUES.md) with recommended work-arounds to a couple known issues.
[AZT]: https://github.com/kent-rasmussen/azt
[WeSay]: https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
