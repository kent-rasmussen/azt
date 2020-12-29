# TL;DR
You need Python 3+ to run A→Z+T. If you need to install it, you can find it [here](https://python.org).

Download this repository, and run `python main.py`. Your python 3+ executable may be called `python3`, i.e., run `python3 main.py`.
# Dependencies
* [pyaudio](https://pypi.org/project/PyAudio/): run `python -m pip install pyaudio` to install
  * On Linux (and Mac?), `pyaudio` may in turn have a dependency of `portaudio19-dev`, which you should install with your package manager.
## Installation on Microsoft Windows
For some reason, I have had trouble getting pyaudio installed on Windows machines with most recent versions of Python (3.9). You may have better mileage than I. In any case, I have found that it works smoothly to
- Download and install Python 3.6.8 (e.g., from [here](https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe))
  - Be sure to check "add to PATH" (or whatever options are appropriate), so Windows knows where Python is installed.
    - If you have more than one version of python installed (e.g. 2.7 and 3.6.8), be sure to know how to run version 3 for this program.
- Open a terminal (e.g., `⊞ win`+`R` then type 'cmd') and run `python -m pip install pyaudio`
# ATZ
To get the program: `git clone https://github.com/kent-rasmussen/azt.git`, or click on the green `code` button on the main page for download options. If you download an archive (e.g., zip file), extract it so you have a folder of files. Either way, put it somewhere sensible, so you can find it later. If you use `git clone`, you can update in the future with `git pull`, and just download the changes.

To run: `python main.py` (The python 3+ executable may be called `python3`.) You may have a better experience (and avoid a terminal) if you tell your operating system to open `main.py` with python (and/or make `main.py` executable) —at that point, you should be able to make a link `main.py` on your desktop or wherever.

For usage information, see [USAGE.md](USAGE.md)
