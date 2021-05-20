# Installing A→Z+T

## TL;DR
You need Python 3+ and _one_ dependency ([PyAudio](https://pypi.org/project/PyAudio/)) to run A→Z+T. Download [this repository](https://github.com/kent-rasmussen/azt.git), and run `main.py`.

## Python
If you need to install [Python](https://python.org), you can find it [here](https://python.org).

Note: your python 3+ executable may be called `python` or `python3`. Be sure to use the correct form for your system when following the instructions below.

## Dependencies
- [PyAudio](https://pypi.org/project/PyAudio/): run `python -m pip install pyaudio` to install.
    - On Linux (and Mac?), `pyaudio` may in turn have a dependency of `portaudio19-dev`, which you should install with your package manager (e.g., `sudo apt-get install portaudio19-dev`).

### Installation on Microsoft Windows
For some reason, I have had trouble getting pyaudio installed on Windows machines with most recent versions of Python (3.9). You may have better mileage than I. In any case, I have found that it works smoothly to

- Download and install Python 3.6.8 (e.g., from [here](https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe)).
    - **Be sure to check "add to PATH"** (or whatever options are appropriate), so Windows knows where Python is installed.
    - If you have more than one version of python installed (e.g. 2.7 and 3.6.8), be sure to know how to run version 3 for this program.
- Then, to install the `pyaudio` dependency, open a terminal (e.g., `⊞ win`+`R` then type 'cmd') and run
    - `python -m pip install pyaudio`
- Alternatively (instead of the above two steps), it may work to do the following:
    - `python -m pip install pipwin`
    - `pipwin install pyaudio`

## XLingPaper and the XMLmind XML Editor (XXE)
To make full use of A→Z+T's report output, I strongly advise you to be ready to use [XLingPaper](https://software.sil.org/xlingpaper/), if you are not already. It can be downloaded [here](https://software.sil.org/xlingpaper/download); this page also includes information on downloading [the XMLmind XML Editor (XXE)](http://www.xmlmind.com/xmleditor/), which is critical to most uses of [XLingPaper](https://software.sil.org/xlingpaper/).

## A→Z+T
To get the program:

- `git clone https://github.com/kent-rasmussen/azt.git`
    - You may need to install Git (e.g. [here](https://git-scm.com/download/win) or [here](https://desktop.github.com/)) first, or
- click on the green `code` button on the main page for download options.

If you download an archive (e.g., zip file), extract it so you have a folder of files. Either way, put it somewhere sensible, so you can find it later. If you use `git clone`, you can update in the future with `git pull`, and just download the changes since you last updated.

To run: Assuming your system is configured correctly, just run `main.py`. Depending on your system, that may be just a click on the file (or a link to it on your desktop or wherever), or you may need to type that into a terminal. Your operating system should know to open `main.py` with python, but you can also explicitly tell it to with `python main.py`.

For usage information, see [USAGE](USAGE.md)
