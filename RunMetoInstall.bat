ECHO OFF
ECHO A→Z+T Install batch file
ECHO Will download and install Python 3.6.8
ECHO Will download and install Git 2.33.0.2
ECHO Will clone/download A→Z+T source to azt directory on your desktop
ECHO Will create a shortcut to run AZT

ECHO Downloading Python 3.6.8...
If exist python-3.6.8-amd64.exe (ECHO python-3.6.8-amd64.exe is there!) ELSE (powershell.exe -noprofile -command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe' -OutFile 'python-3.6.8-amd64.exe'")

ECHO Installing Python 3.6.8
ECHO Be sure to check "add to PATH" in the dialog BEFORE you click "Install Now"
ECHO You should be fine with all default options
ECHO At the end of the install, be sure to click on "remove path limitation"
start python-3.6.8-amd64.exe

ECHO Downloading Git 2.33.0.2...
If exist Git-2.33.0.2-64-bit.exe (ECHO Git-2.33.0.2-64-bit.exe is there!) ELSE (powershell.exe -noprofile -command "Invoke-WebRequest 'https://github.com/git-for-windows/git/releases/download/v2.33.0.windows.2/Git-2.33.0.2-64-bit.exe' -OutFile 'Git-2.33.0.2-64-bit.exe'")

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

ECHO I'll pause now; cancel now to be finished, or press any key to continue
ECHO to install XLingPapper and Praat, to get the most out of A→Z+T.
pause

ECHO Downloading XLingPaper 3.10...
If exist XLingPaper3-10-1XXEPersonalEditionFullSetup.exe (ECHO XLingPaper3-10-1XXEPersonalEditionFullSetup.exe is there!) ELSE (powershell.exe -noprofile -command "Invoke-WebRequest 'https://software.sil.org/downloads/r/xlingpaper/XLingPaper3-10-1XXEPersonalEditionFullSetup.exe' -OutFile 'XLingPaper3-10-1XXEPersonalEditionFullSetup.exe'")

ECHO Installing XLingPaper 3.10
start XLingPaper3-10-1XXEPersonalEditionFullSetup.exe

ECHO Downloading Praat 6211...
If exist praat6211_win64.zip (ECHO praat6211_win64.zip is there!) ELSE (powershell.exe -noprofile -command "Invoke-WebRequest 'https://www.fon.hum.uva.nl/praat/praat6211_win64.zip' -OutFile 'praat6211_win64.zip'")
tar -xvf praat6211_win64.zip -C %ProgramFiles%
setx path "%path%;%ProgramFiles%"

#powershell.exe -nologo -noprofile -command "& { $shell = New-Object -COM Shell.Application; $target = $shell.NameSpace('C:\extractToThisDirectory'); $zip = $shell.NameSpace('C:\extractThis.zip'); $target.CopyHere($zip.Items(), 16); }"