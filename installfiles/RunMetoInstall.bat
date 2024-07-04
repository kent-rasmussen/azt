@ECHO OFF
set pythonversion=3.12.4
set pythonfilename=python-%pythonversion%-amd64.exe
set pythonsize=^(25.5322 Megabyte^(s^); 26772456 bytes^)
set pythonurl=https://www.python.org/ftp/python/3.12.4/%pythonfilename%
set gitversion=2.45.2
set gitfilename=Git-%gitversion%-64-bit.exe
set gitsize=^(68.1 MB; 68,131,584 bytes^)
set giturl=https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/%gitfilename%
ECHO:
ECHO:
ECHO:
ECHO:
ECHO A-Z+T Install batch file
ECHO This script installs stuff --it must be run **As Administrator**! It will:
ECHO \tWill download and install Python %pythonversion%
ECHO \tWill download and install Git %gitversion%
ECHO \tCreate another file (also **run as administrator**) that will
ECHO \t\tWill clone/download A-Z+T source to azt directory on your desktop
ECHO \t\tWill create a shortcut to run AZT on your desktop
ECHO Error Level is %errorlevel%
whoami /groups | find "S-1-16-12288"
if errorlevel 1 goto NotAdmin
ECHO Looks like I'm running As Administrator.
ECHO Using user profile %userprofile%
ECHO moving to %~dp0 (where you downloaded the script)
cd /d %~dp0

If exist %pythonfilename% (
ECHO %pythonfilename% is there!
) ELSE (
ECHO Downloading Python %pythonversion% %pythonsize%...
ECHO Check that your internet is on and
pause
powershell.exe -noprofile -command "Invoke-WebRequest %pythonurl% -OutFile %pythonfilename%"
)

ECHO Installing Python %pythonversion%
::ECHO checking for longfilenames first, for debug ^(the following is not generalized!^)
::reg query HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled
::reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /d 0 /f
::reg query HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled
ECHO:
::ECHO ATTENTION!!
::ECHO            vvvvvvvvvvvvvvvvvvv
::ECHO Be sure to check "add to PATH" in the dialog BEFORE you click "Install Now"
::ECHO            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::ECHO ALSO:
::ECHO        vvvvvvvvvvvvvvvvvv                      vvvvvvvvvvvvvvvvvvvvvvvv
::ECHO At the end of the install, be sure to click on "remove path limitation"
::ECHO        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                      ::^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::ECHO If you forget to do either of these, you should run python-3.12.4-amd64.exe
::ECHO If you forget to do this, you should run %pythonfilename%
::ECHO again manually (maybe select "Fix install") to set these options.
::ECHO:
::ECHO Otherwise, you should be fine with all default options
::ECHO:
REM start %pythonfilename% /?

::do one of these (/wait allows user to see whatever before going on):
::this shows the user what?
start /wait %pythonfilename% SimpleInstall=1 SimpleInstallDescription="Installing Python %pythonversion%" PrependPath=1 Include_pip=1 InstallAllUsers=1 Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0

::this shows the user nothing
::start /wait %pythonfilename% /quiet PrependPath=1 Include_pip=1 InstallAllUsers=1 Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0

::this shows the user progress with a cancel button
::start /wait %pythonfilename% /passive PrependPath=1 Include_pip=1 InstallAllUsers=1 Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0

echo python installed; path test next
set var=LongPathsEnabled
set longpathsOK=
::This list of registries should be in priority order; the first found is used.
for %%k in (HKLM,HKCU,HKCR,HKU,HKCC) do (
  reg query %%k\SYSTEM\CurrentControlSet\Control\FileSystem /v %var%
  for /f "tokens=3" %%i in ('reg query %%k\SYSTEM\CurrentControlSet\Control\FileSystem /v %var%') do (
    set longpathsOK=%%i
    set regkey=%%k
    goto :next
    )
  )
:next
::echo longpathsOK is %longpathsOK%
::echo python path test done here
if %longpathsOK%==1 (
echo Long paths are OK ^(already^).
) else (
reg add %regkey%\SYSTEM\CurrentControlSet\Control\FileSystem /v %var% /d 1 /f
::reg query %regkey%\SYSTEM\CurrentControlSet\Control\FileSystem /v %var%'
::unset because we want current values:
set longpathsOK=
for %%k in (HKLM,HKCU,HKCR,HKU,HKCC) do (
  ::reg query %%k\SYSTEM\CurrentControlSet\Control\FileSystem /v %var%
  for /f "tokens=3" %%i in ('reg query %%k\SYSTEM\CurrentControlSet\Control\FileSystem /v %var%') do (
    set longpathsOK=%%i
    goto :finalokcheck
    )
  :finalokcheck
  echo longpathsOK=%longpathsOK%
  if %longpathsOK%==1 (echo Long paths are now OK.) else (echo longpathsOK=%longpathsOK%)
)

If exist %gitfilename% (ECHO %gitfilename% is there!) ELSE (
  ECHO Downloading Git %gitversion% %gitsize%...
  ECHO Check that your internet is on and
  pause
  powershell.exe -noprofile -command "Invoke-WebRequest %giturl% -OutFile %gitfilename%"
  )

ECHO Installing Git %gitversion%
ECHO You should be fine with all default options
ECHO ATTENTION!!
ECHO                     vvvvvvvvvvvvvvvvvvvvvvv
ECHO Wait until you have finished installing Git before moving on with this script.
ECHO                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ECHO     vvvvvvv
ECHO You need it for the next step!
ECHO     ^^^^^^^^^^^^^^
REM start Git-2.45.2-64-bit.exe /?
REM start Git-2.45.2-64-bit.exe /silent

::/SP- not needed?
::Pick one of these; VERYSILENT is not visible to the user, SILENT shows progress
start %gitfilename% /SILENT /NORESTART /NOCANCEL /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\shellhere,assoc,assoc_sh"
::start %gitfilename% /VERYSILENT /NORESTART /NOCANCEL /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\shellhere,assoc,assoc_sh"

::The above line should be commented out to try this block:
::(echo [Setup]
::echo PathOption=Cmd
::Don't use the following indented lines unless necessary:
::echo Lang=default
::echo Dir=%installDir%
::echo Group=Git
::echo NoIcons=0
::echo SetupType=default
::echo Components=icons,ext\reg\shellhere,assoc,assoc_sh
::echo Tasks=
::echo PathOption=Cmd
::echo SSHOption=OpenSSH
::echo CRLFOption=CRLFAlways
::echo BashTerminalOption=ConHost
::echo PerformanceTweaksFSCache=Enabled
::echo UseCredentialManager=Enabled
::echo EnableSymlinks=Disabled
::echo EnableBuiltinDifftool=Disabled
::)> git_config.inf
::uncomment to try inf (and comment above git install)
::start %gitfilename% /SILENT /LOADINF="git_config.inf" /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS
::Once this is working, uncomment
::del git_config.bat
::ECHO Wait to finish installing Git %gitversion%, then
::pause
::The problem at this point is that we can't find the git executable,
::I think because the path cannot be updated at this point in the script. So we need to call git from a second script, at this point

::This is the second script
(
echo @echo off
echo ECHO Cloning A-Z+T source to '%userprofile%/desktop/azt'
echo ::This is for local ^(USB^) repo install
echo set azt=
echo for /R %%f in (azt.git) do @IF EXIST %%f set azt=%%~dpnxf
echo if defined azt (
echo echo azt is defined ^(local repo found^): %azt%
echo ) else (
echo echo Local file not found; using github
echo set azt=https://github.com/kent-rasmussen/azt.git
echo git clone %azt% ^"%userprofile%/desktop/azt^"
echo echo confirm this is what you want, then
echo ECHO making links to AZT and Transcriber tool...
echo mklink "%userprofile%/desktop/A-Z+T" "%userprofile%/desktop/azt/main.py"
echo mklink "%userprofile%/desktop/Transcriber" "%userprofile%/desktop/azt/transcriber.py"
ECHO ::WshShell = CreateObject("Wscript.shell")
ECHO ::strDesktop = WshShell.SpecialFolders("Desktop")
ECHO ::oMyShortcut = WshShell.CreateShortcut(strDesktop + "\A-Z+T.lnk")
ECHO ::oMyShortcut.WindowStyle = 3 &&Maximized 7=Minimized 4=Normal
ECHO ::oMyShortcut.IconLocation = "%userprofile%/desktop/azt/AZT stacks6_icon.png"
ECHO ::OMyShortcut.TargetPath = "%userprofile%/desktop/azt/main.py"
ECHO ::oMyShortCut.Hotkey = "ALT+CTRL+F"
ECHO ::oMyShortCut.Save
echo pause
echo del %~dpn0-2%~x0
) >%~dpn0-2%~x0



ECHO Install done! ^(hopefully!^)

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
start /wait XLingPaper3-10-1XXEPersonalEditionFullSetup.exe

If exist praat6413_win-intel64.zip (
ECHO praat6413_win-intel64.zip is there!
) ELSE (
ECHO Downloading Praat 6413...
powershell.exe -noprofile -command "Invoke-WebRequest 'https://www.fon.hum.uva.nl/praat/praat6413_win-intel64.zip' -OutFile 'praat6218_win64.zip'"
)
ECHO Program files in %ProgramFiles%
ECHO installing Praat to %ProgramFiles%
tar -xvf praat6413_win-intel64.zip -C "%ProgramFiles%"
setx path "%path%;%ProgramFiles%"

If exist Mercurial-6.0-x64.exe (
ECHO Mercurial-6.0-x64.exe is there!
) ELSE (
ECHO Downloading Mercurial 6.0...
powershell.exe -noprofile -command "Invoke-WebRequest 'https://www.mercurial-scm.org/release/windows/Mercurial-6.0-x64.exe' -OutFile 'Mercurial-6.0-x64.exe'"
)

ECHO Installing Mercurial 6.0
start /wait Mercurial-6.0-x64.exe

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
