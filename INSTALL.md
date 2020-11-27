# TL;DR
You need Python 3+ to run A→Z+T. If you need to install this, you can find it on python.org.

Download this repository, and run `main.py`.
# Dependencies
* [pyaudio](https://pypi.org/project/PyAudio/)
# Installation on Microsoft Windows
For some reason, I have had trouble getting pyaudio installed on Windows machines with most recent versions of Python (3.9). You may have better mileage than I. In any case, I have found that it works smoothly to
- Download and install Python 3.6.8 (e.g., from [here](https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe)
  - Be sure to check "add to PATH" (or whatever options are appropriate), so Windows knows where Python is installed.
    - If you have more than one version of python installed (e.g. 2.7 and 3.6.8), be sure to know how to run version 3 for this program.
- Open a terminal (e.g., <font face=Wingdings>&#xff;</font> `⊞`+`R`/`cmd`) and run `python -m pip install pyaudio`
