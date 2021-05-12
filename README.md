# A→Z+T

A→Z+T is designed to accelerate community-based language development, supplemented by (not as a replacement for) formal linguistic training. It does this by systematically checking a dictionary (and thus a writing system), with initial focus on data collection for tonal languages.
Additional features are still in development. A→Z+T work results in a checked lexical database backed up with sound files, all of which can be viewed and edited in [WeSay](https://software.sil.org/wesay/) or imported into [FLEx](https://software.sil.org/fieldworks/).

<!-- It is designed to *supplement* (not replace) formal training, on the one hand, and *facilitate* a particular kind of language development on the other, so it may not do what you want —it certainly does not do everything. If you want to get as many people involved in the development of their own language as possible, in a manner that results in a checked lexical database backed up by sound files, then this tool is for you. -->
## Why
See [RATIONALE](RATIONALE.md) for more information on why one should use this tool; see [Why Work with Computers](WHYCOMPUTERS.md) to see A→Z+T compared with pen and paper participatory methods. See [Why Work with Communities](WHYCOMMUNITIES.md) to see A→Z+T compared with more traditional field methods

## What
A→Z+T is written in [Python](https://python.org) (3+) and [Tkinter](https://docs.python.org/3/library/tkinter.html), with [PyAudio](https://pypi.org/project/PyAudio/) for recording and playing sound files. A→Z+T produces reports to the screen, plain text files, and [XLingPaper](https://software.sil.org/xlingpaper/) XML documents —which can in turn be easily converted to PDF and HTML, each with clickable links to sound files.

## How
To get the program: `git clone https://github.com/kent-rasmussen/azt.git` (or download through `code` button)

To run: `python main.py` (or `python3 main.py`, as appropriate for the (3+) version of python on your system)

See [INSTALL](INSTALL.md) for more help installing; see [USAGE](USAGE.md) for how to use this tool.

See [CHANGELOG](CHANGELOG.md) to see features by version, and [ROADMAP](ROADMAP.md) to see what I'm working on next.

## Bugs
See [BUGS](BUGS.md) for information to send me if you have problems; see [KNOWNISSUES](KNOWNISSUES.md) with recommended work-arounds to a couple known issues.
