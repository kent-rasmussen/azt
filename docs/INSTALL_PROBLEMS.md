# Problems Running A→Z+T
Probably the most frustrating situation when trying to run [A→Z+T](https://github.com/kent-rasmussen/azt.git) is getting a _brief flicker of a black window_, then nothing. This page will address what to do to move on.

The problem is that the terminal flashed the error too quickly for you to see. To see the error message (in order to copy it to me), you can do one of two things:

1. [Find an error log](FINDERRORLOGS.md) and send it to me, assuming it was created (this you will likely have/want to do in the future, so not a bad thing to figure out now).
2. Run A→Z+T _from a terminal_, then copy and paste the outcome to me. You should NOT normally have to do this, though many problems may require this, if the setup was not finished correctly (especially if not enough of the program ran to start an error log).  To do this,
    - Get a terminal in whatever way know know best (e.g., type 'cmd' in your start box).
    - In the terminal, type "python C:\whatever\your\path\is\to\main.py", replacing "whatever\your\path\is\to" with the appropriate text for where you put the A→Z+T repsitory. The point here is to **make sure python can find main.py**, and there are many ways to do it (so you might need local IT help at this point, depending on how your computer is set up), but hopefully this will be enough for you.
    - Take a quick look at the error message(s):
      - "No such file or directory": check that the path to your file is correct, and try again; python can't run a file it can't find.
      - Anything mentioning `pyaudio`, `Pillow`, or `lxml` not found: go back to that line of the instructions, and make sure those modules got installed. If there was any error, please [report them to me](https://github.com/kent-rasmussen/azt/blob/main/BUGS.md).
      - Anythning else: copy and paste the errors you get into an [Email to me](https://github.com/kent-rasmussen/azt/blob/main/BUGS.md), and I'll tell you where to go next.
