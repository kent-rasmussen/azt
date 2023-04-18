ECHO OFF
ECHO:
ECHO:
ECHO:
ECHO:
ECHO A-Z+T Install batch file
ECHO This script installs stuff --it must be run **As Administrator**!
ECHO Will download and install Python 3.6.8
ECHO Will download and install Git 2.33.0.2
ECHO Will clone/download A-Z+T source to azt directory on your desktop
ECHO Will create a shortcut to run AZT
ECHO Error Level is %errorlevel%
whoami /groups | find "S-1-16-12288"
if errorlevel 1 goto NotAdmin
ECHO Looks like I'm running As Administrator.
ECHO Using user profile %userprofile%
ECHO not moving to "%userprofile%/Downloads"
ECHO moving to %~dp0 (where you downloaded the script)
cd /d %~dp0

If exist python-3.6.8-amd64.exe (
ECHO python-3.6.8-amd64.exe is there!
) ELSE (
ECHO "Downloading Python 3.6.8 (31830944; 30M)..."
ECHO Check that your internet is on and
pause
powershell.exe -noprofile -command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe' -OutFile 'python-3.6.8-amd64.exe'"
)

ECHO Installing Python 3.6.8
ECHO:
ECHO ATTENTION!!
ECHO            vvvvvvvvvvvvvvvvvvv
ECHO Be sure to check "add to PATH" in the dialog BEFORE you click "Install Now"
ECHO            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ECHO ALSO:
ECHO        vvvvvvvvvvvvvvvvvv                      vvvvvvvvvvvvvvvvvvvvvvvv
ECHO At the end of the install, be sure to click on "remove path limitation"
ECHO        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ECHO If you forget to do either of these, you should run python-3.6.8-amd64.exe
ECHO again manually (maybe select "Fix install") to set these options.
ECHO:
ECHO Otherwise, you should be fine with all default options
ECHO:
start python-3.6.8-amd64.exe /passive PrependPath=1 Include_pip=1 InstallAllUsers=1
If exist Git-2.33.0.2-64-bit.exe (
ECHO Git-2.33.0.2-64-bit.exe is there!
) ELSE (
ECHO Downloading Git 2.33.0.2 (50101024; 48M^)...
ECHO Check that your internet is on and
pause
powershell.exe -noprofile -command "Invoke-WebRequest 'https://github.com/git-for-windows/git/releases/download/v2.33.0.windows.2/Git-2.33.0.2-64-bit.exe' -OutFile 'Git-2.33.0.2-64-bit.exe'"
)

ECHO waiting for you to finish installing Python 3.6.8
pause

ECHO Installing Git 2.33.0.2
ECHO You should be fine with all default options
ECHO ATTENTION!!
ECHO                     vvvvvvvvvvvvvvvvvvvvvvv
ECHO Wait until you have finished installing Git before moving on with this script.
ECHO                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ECHO     vvvvvvv
ECHO You need it for the next step!
ECHO     ^^^^^^^^^^^^^^
start Git-2.33.0.2-64-bit.exe

pause

ECHO Cloning A-Z+T source to '%userprofile%/desktop/azt'
cd /d "%userprofile%/desktop"
FOR /F "tokens=* USEBACKQ" %%F IN (`where git`) DO (
SET GitExe=%%F
)
$str={
""%GitExe%"" clone ""https://github.com/kent-rasmussen/azt.git"" ""%userprofile%/desktop/azt"""
}
ECHO Running $str
REM ""%GitExe%"" clone ""https://github.com/kent-rasmussen/azt.git"" ""%userprofile%/desktop/azt"""
powershell.exe -noprofile -ExecutionPolicy Bypass -command $str
REM """%GitExe%"" clone ""https://github.com/kent-rasmussen/azt.git"" ""%userprofile%/desktop/azt"""
ECHO making links to AZT and Transcriber tool...
mklink "%userprofile%/desktop/A>Z+T" "%userprofile%/desktop/azt/main.py"
mklink "%userprofile%/desktop/Transcriber" "%userprofile%/desktop/azt/transcriber.py"
ECHO WshShell = CreateObject("Wscript.shell")
ECHO strDesktop = WshShell.SpecialFolders("Desktop")
ECHO oMyShortcut = WshShell.CreateShortcut(strDesktop + "\Sample.lnk")
ECHO oMyShortcut.WindowStyle = 3 &&Maximized 7=Minimized 4=Normal
ECHO oMyShortcut.IconLocation = "C:\myicon.ico"
ECHO OMyShortcut.TargetPath = "%windir%\notepad.exe"
ECHO oMyShortCut.Hotkey = "ALT+CTRL+F"
ECHO oMyShortCut.Save

ECHO "Install done! (hopefully!)"

ECHO I'll pause now; cancel now to be finished, or press any key to continue
ECHO to install XLingPaper, Praat and Mercurial, to get the most out of A-Z+T.
pause

cd /d "%userprofile%/Downloads"

If exist XLingPaper3-10-1XXEPersonalEditionFullSetup.exe (
ECHO XLingPaper3-10-1XXEPersonalEditionFullSetup.exe is there!
) ELSE (
ECHO Downloading XLingPaper 3.10...
powershell.exe -noprofile -command "Invoke-WebRequest 'https://software.sil.org/downloads/r/xlingpaper/XLingPaper3-10-1XXEPersonalEditionFullSetup.exe' -OutFile 'XLingPaper3-10-1XXEPersonalEditionFullSetup.exe'"
)

ECHO Installing XLingPaper 3.10
start XLingPaper3-10-1XXEPersonalEditionFullSetup.exe

If exist praat6218_win64.zip (
ECHO praat6218_win64.zip is there!
) ELSE (
ECHO Downloading Praat 6218...
powershell.exe -noprofile -command "Invoke-WebRequest 'https://www.fon.hum.uva.nl/praat/praat6218_win64.zip' -OutFile 'praat6218_win64.zip'"
)
ECHO Program files in %ProgramFiles%
ECHO installing Praat to %ProgramFiles%
tar -xvf praat6218_win64.zip -C "%ProgramFiles%"
setx path "%path%;%ProgramFiles%"

If exist Mercurial-6.0-x64.exe (
ECHO Mercurial-6.0-x64.exe is there!
) ELSE (
ECHO Downloading Mercurial 6.0...
powershell.exe -noprofile -command "Invoke-WebRequest 'https://www.mercurial-scm.org/release/windows/Mercurial-6.0-x64.exe' -OutFile 'Mercurial-6.0-x64.exe'"
)

ECHO Installing Mercurial 6.0
start Mercurial-6.0-x64.exe

echo Stopping here just in case you need to read anything above; we're done!
Pause
goto end
:NotAdmin
ECHO This doesn't seem to be running as administrator.
ECHO Trying to start an admin command prompt. If that doesn't work, please
ECHO run this bat file as administrator yourself.
if runas /env /user:domain\Administrator %~0 (
ECHO Worked!
) ELSE (
runas /env /user:Administrator %~0
)
echo Stopping here just in case you need to read anything above; we're done!
Pause
:end
