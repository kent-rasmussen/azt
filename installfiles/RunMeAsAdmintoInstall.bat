@ECHO OFF
whoami /groups | find "S-1-16-12288" >NUL 2>&1
if errorlevel 1 goto NotAdmin
ECHO Looks like I'm running As Administrator.

set pythonversion=3.12.4
set pythonfilename=python-%pythonversion%-amd64.exe
set pythonsize="^(25.5322 Megabyte^(s^); 26772456 bytes^)"
set pythonurl=https://www.python.org/ftp/python/3.12.4/%pythonfilename%
set gitversion=2.45.2
set gitfilename=Git-%gitversion%-64-bit.exe
set gitsize="^(68.1 MB; 68,131,584 bytes^)"
set giturl=https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/%gitfilename%
set praatversion=6413
set praatfilename=praat%praatversion%_win-intel64.zip
set praaturl=https://www.fon.hum.uva.nl/praat/%praatfilename%
set xlpversion=3-10
set xlpfilename=XLingPaper%xlpversion%-1XXEPersonalEditionFullSetup.exe
set xlpurl=https://software.sil.org/downloads/r/xlingpaper/%xlpfilename%
set hgversion=6.0
set hgfilename=Mercurial-%hgversion%-x64.exe
set hgurl=https://www.mercurial-scm.org/release/windows/%hgfilename%
ECHO:
ECHO:
ECHO:
ECHO:
ECHO A-Z+T Install batch file
ECHO This script installs stuff --it must be run **As Administrator**! It will:
ECHO,  +Will download and install Python %pythonversion%
ECHO,  +Will download and install Git %gitversion%
ECHO,  +Create another file (also **run as administrator**) that will
ECHO,    +Will clone/download A-Z+T source to azt directory on your desktop
ECHO,    +Will create a shortcut to run AZT on your desktop
echo:
pause
::ECHO moving to %~dp0 ^(where you downloaded the script^)
cd /d %~dp0

If exist %pythonfilename% (
ECHO %pythonfilename% is there!
) ELSE (
ECHO Downloading Python %pythonversion% %pythonsize:"=%...
ECHO Check that your internet is on and
pause
powershell.exe -noprofile -command "Invoke-WebRequest %pythonurl% -OutFile %pythonfilename%"
)

ECHO Installing Python %pythonversion%
::ECHO checking for longfilenames first, for debug ^(the following is not generalized!^)
::reg query HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled
::reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /d 0 /f
::reg query HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled

::do one of these three (/wait allows user to see whatever before going on):

::this shows the user "Install: use settings preselected by your administrator"
::start /wait %pythonfilename% SimpleInstall=1 SimpleInstallDescription="Installing Python %pythonversion%" PrependPath=1 Include_pip=1 InstallAllUsers=1 Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0

::this shows the user nothing
::start /wait %pythonfilename% /quiet PrependPath=1 Include_pip=1 InstallAllUsers=1 Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0

::this shows the user progress with a cancel button
start /wait %pythonfilename% /passive PrependPath=1 Include_pip=1 InstallAllUsers=1 Include_launcher=1 InstallLauncherAllUsers=1 Include_test=0

echo python installed; path test next
set var=LongPathsEnabled
set longpathsOK=
set regkey=HKLM
::This list of registries should be in priority order; the first found is used.
for %%k in (HKLM,HKCU,HKCR,HKU,HKCC) do (
  ::reg query %%k\SYSTEM\CurrentControlSet\Control\FileSystem /v %var%
  for /f "tokens=3" %%i in ('reg query %%k\SYSTEM\CurrentControlSet\Control\FileSystem /v %var%') do (
    set longpathsOK=%%i
    set regkey=%%k
    goto :next
    )
  )
:next
::echo python path test done here
if %longpathsOK%==1 (
echo Long paths are OK ^(already^).
) else (
reg add %regkey%\SYSTEM\CurrentControlSet\Control\FileSystem /v %var% /d 1 /f
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
)

If exist %gitfilename% (ECHO %gitfilename% is there!) ELSE (
  ECHO Downloading Git %gitversion% %gitsize:"=%...
  ECHO Check that your internet is on and
  pause
  powershell.exe -noprofile -command "Invoke-WebRequest %giturl% -OutFile %gitfilename%"
  )

ECHO Installing Git %gitversion%
::Pick one of these; VERYSILENT is not visible to the user, SILENT shows progress
start /wait %gitfilename% /SILENT /NORESTART /NOCANCEL /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\shellhere,assoc,assoc_sh"
::start /wait %gitfilename% /VERYSILENT /NORESTART /NOCANCEL /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\shellhere,assoc,assoc_sh"

::The problem at this point is that we can't find the git executable.
::I think because the path cannot be updated at this point in the script.
::So we need to call git from a second script, at this point

::Put this logic here; `do` causes problems in the echo script...
::This is for local ^(USB^) repo install
echo Looking for a USB with the azt repo on it ^(there may be 'not found' errors^)
set azt=
for /f %%d in ('wmic logicaldisk get deviceid') do (
	@IF NOT %%f==DeviceID (
		for /f %%f in ('dir /b /a:d %%d\*azt.git') do (
			echo looking for %%d^\%%f
			@IF EXIST %%d\%%f (
				set azt=%%d\%%f
				goto :foundaztrepo
				) else (echo Didn't find %%d\%%f)
			)
		)
	)
:foundaztrepo
if defined azt (
  echo azt is defined ^(local repo found^): %azt%
  ) else (
  echo Local file not found; using github
  set azt=https://github.com/kent-rasmussen/azt.git
  )

::This may also be useless:
::ECHO ::WshShell = CreateObject("Wscript.shell")
::ECHO ::strDesktop = WshShell.SpecialFolders("Desktop")
::ECHO ::oMyShortcut = WshShell.CreateShortcut(strDesktop + "\A-Z+T.lnk")
::ECHO ::oMyShortcut.WindowStyle = 3 &&Maximized 7=Minimized 4=Normal
::ECHO ::oMyShortcut.IconLocation = "%userprofile%/desktop/azt/AZT stacks6_icon.png"
::ECHO ::OMyShortcut.TargetPath = "%userprofile%/desktop/azt/main.py"
::ECHO ::oMyShortCut.Hotkey = "ALT+CTRL+F"
::ECHO ::oMyShortCut.Save

echo writing the second script ^(%~dpn0-2%~x0^)
(
echo @echo off
echo ECHO Cloning A-Z+T source to '%userprofile%\desktop\azt'
echo echo going to run git clone %%azt%% ^"%userprofile%/desktop/azt^"
echo git config --global --add safe.directory %%azt%%
echo git clone %azt% ^"%userprofile%/desktop/azt^"
echo echo errorlevel=%%errorlevel%%
echo IF not errorlevel==0 (
echo,  echo confirm this is what you want^, then
echo,  echo pause
echo,  )
echo del %~dpn0-2%~x0
) >%~dpn0-2%~x0
::Call the script we just made from a new shell for a new path, but as a basic user
::runas /showtrustlevels
runas /trustlevel:0x20000 %~dpn0-2%~x0

:: these seem to work before the location exists
echo making links to AZT and Transcriber tool...
mklink "%userprofile%/desktop/A-Z+T" "%userprofile%/desktop/azt/main.py"
mklink "%userprofile%/desktop/Transcriber" "%userprofile%/desktop/azt/transcriber.py"

::echo Right-click on %~dpn0-2%~x0 and run it As Administrator ^(or has it?^)
::pause
ECHO Install done! ^(hopefully!^)

ECHO I'll pause now; cancel now to be finished, or press any key to continue
ECHO to install XLingPaper^, Praat and Mercurial^, to get the most out of A-Z+T.
pause

::cd /d "%userprofile%/Downloads"

If exist %xlpfilename% (
ECHO %xlpfilename% is there!
) ELSE (
ECHO Downloading XLingPaper %xlpversion%...
powershell.exe -noprofile -command "Invoke-WebRequest %xlpurl% -OutFile %xlpfilename%"
)

ECHO Installing XLingPaper %xlpversion%
start /wait %xlpfilename% /silent

If exist %praatfilename% (
ECHO %praatfilename% is there!
) ELSE (
ECHO Downloading Praat %praatversion%...
powershell.exe -noprofile -command "Invoke-WebRequest %praaturl% -OutFile %praatfilename%"
)
::ECHO Program files in %ProgramFiles%
ECHO installing Praat to %ProgramFiles%
tar -xvf %praatfilename% -C "%ProgramFiles%"
setx path "%path%;%ProgramFiles%"

If exist %hgfilename% (
ECHO %hgfilename% is there!
) ELSE (
ECHO Downloading Mercurial %hgversion%...
powershell.exe -noprofile -command "Invoke-WebRequest %hgurl% -OutFile %hgfilename%"
)

ECHO Installing Mercurial %hgversion%
start /wait %hgfilename% /silent

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
:eof
