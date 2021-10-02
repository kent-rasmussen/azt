# Simple and Straightforward Instructions for Installing A→Z+T on MS Windows
This document offers instructions with **exactly one set of options**; to explore more options, see [INSTALL](INSTALL.md).

For simple install instructions for Ubuntu Linux, see [SIMPLEINSTALL_LINUX](SIMPLEINSTALL_LINUX.md).

If any of the following fails, please [write me](BUGS.md), copy/pasting all errors you find into the Email.

Before you can [Set up A→Z+T for normal use](#set-up-azt-for-normal-use), you need to do two things:
1. [Install Python](#install-python)
2. [Install Git and Download A→Z+T](#install-git-and-download-azt)

## Install Python
1. Download Python from [here](https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe). While you are waiting, you can start on [Install Git and Download A→Z+T](#install-git-and-download-azt) below
2. Click the download to install Python, and **be sure to check "add to PATH"** during the install process. **If you don't do this**, you will likely need to ask your local IT support for help.
3. Open a terminal (type `cmd` in the start box), and paste `python -m pip install pyaudio Pillow lxml` and hit enter.

## Install Git and Download A→Z+T

### Install Git
1. Download [Git](https://git-scm.com/download/win) from [here](https://github.com/git-for-windows/git/releases/download/v2.33.0.windows.2/Git-2.33.0.2-64-bit.exe)
2. Click the download to install Git

### Download A→Z+T
1. Decide where you want to put (and leave) A→Z+T (e.g., in your home folder).
2. In that folder, right click select `Git-Bash` to get a terminal (black window).
3. In the terminal, paste `git clone https://github.com/kent-rasmussen/azt.git` and hit enter.

## Set up A→Z+T for normal use
Once you have completed everything under [Install Python](#install-python) and [Install Git and Download A→Z+T](#install-git-and-download-azt):
1. Make a link from `main.py` (in the folder where you put A→Z+T) to your desktop.
2. Click on the link to run A→Z+T
3. **Celebrate your accomplishment; you're done installing A→Z+T!**
4. Read [USAGE](USAGE.md) for how to use A→Z+T
5. Send me information on any [bugs](BUGS.md) you find, so I can help you and improve the program for others.

## Additional Important Steps to get the most out of A→Z+T

### Be ready to make and edit reports
1. ask someone to help you install XeLaTeX (see [INSTALL](INSTALL.md)).
2. ask someone to help you install the XMLmind XML Editor (XXE) (see [INSTALL](INSTALL.md)).

### Update A→Z+T (to be sure you're using the most recent version)
1. In the folder where you put A→Z+T (see above), right click select `Git-Bash` to get a terminal (black window).
2. In the terminal, paste `git pull` and hit enter.
