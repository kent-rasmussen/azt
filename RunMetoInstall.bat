ECHO OFF
ECHO A→Z+T Install batch file
ECHO Will download and install Python 3.6.8
ECHO Will download and install Git 2.33.0.2
ECHO Will clone/download A→Z+T source to azt directory on your desktop
ECHO Will create a shortcut to run AZT

ECHO Downloading Python 3.6.8...
If exist python-3.6.8-amd64.exe (ECHO python-3.6.8-amd64.exe is there!) ELSE (Invoke-WebRequest 'https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe' -OutFile 'python-3.6.8-amd64.exe')

ECHO Installing Python 3.6.8
ECHO Be sure to check "add to PATH" in the dialog BEFORE you click "Install Now"
ECHO You should be fine with all default options
ECHO At the end of the install, be sure to click on "remove path limitation"
start python-3.6.8-amd64.exe

ECHO Downloading Git 2.33.0.2...
If exist Git-2.33.0.2-64-bit.exe (ECHO Git-2.33.0.2-64-bit.exe is there!) ELSE (Invoke-WebRequest 'https://github.com/git-for-windows/git/releases/download/v2.33.0.windows.2/Git-2.33.0.2-64-bit.exe' -OutFile 'Git-2.33.0.2-64-bit.exe')

ECHO Installing Git 2.33.0.2
ECHO You should be fine with all default options
start Git-2.33.0.2-64-bit.exe

ECHO Cloning A→Z+T source to azt directory on your desktop
cd /d %userprofile%/desktop
git clone https://github.com/kent-rasmussen/azt.git
ECHO making links to AZT and Transcriber tool...
mklink AZT azt/main.py
mklink Transcriber azt/transcriber.py

ECHO Install done! (hopefully!)
