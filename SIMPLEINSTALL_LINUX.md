# Simple and Straightforward Instructions for Installing A→Z+T on Ubuntu Linux

This document offers instructions with **exactly one set of options**; to explore more options, see [INSTALL](INSTALL.md).

For simple install instructions for MS Windows, see [SIMPLEINSTALL](SIMPLEINSTALL.md).

If any of the following fails, please [write me](BUGS.md), copy/pasting all errors you find into the Email.

To run these commands, open a terminal, and copy/paste the command, then hit enter.You may need put in your sudo/administrator password.

## Install system and python packages
Run the following commands: 
1. `sudo apt-get install git python3-tk python3-pip portaudio19-dev texlive-xetex`. (This last one is a large download)
2. `python3 -m pip install pyaudio tkinter lxml Pillow`
3. `cd;git clone https://github.com/kent-rasmussen/azt.git;cd -`

## Download A→Z+T
Run this command: `cd;git clone https://github.com/kent-rasmussen/azt.git`.

## Set up A→Z+T for normal use
1. Download [this file](installfiles/azt.desktop). If asked, save it to your "Downloads" folder.
2. Run the following commands:
- 1. `cp $HOME/Downloads/azt.desktop $HOME/.local/share/applications/`
- 2. `sudo desktop-file-validate  $HOME/.local/share/applications/azt.desktop`
- 3. `sudo update-desktop-database`
- 4. `ln $HOME/.local/share/applications/azt.desktop $HOME/Desktop/`
3. Click on the link on your desktop to run A→Z+T
4. **Celebrate your accomplishment; you're done installing A→Z+T!**
5. Read [USAGE](USAGE.md) for how to use A→Z+T
6. Send me information on any [bugs](BUGS.md) you find, so I can help you and improve the program for others.

## Additional Important Steps to get the most out of A→Z+T
### Be ready to make and edit reports
Ask someone to help you install the XMLmind XML Editor (XXE) (see [INSTALL](INSTALL.md)).

### Update A→Z+T (to be sure you're using the most recent version)
Run the command `cd $HOME/azt;git pull;cd -`. 
