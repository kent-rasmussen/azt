@echo off
rem A-Z+T manual test: Keyman input check, tier 1 (zero install).
rem Opens index.html in Microsoft Edge as a chromeless app window. Works from
rem wherever this repo was cloned - no paths to edit. Just double-click it.
setlocal enabledelayedexpansion

set "HTML=%~dp0index.html"
if not exist "!HTML!" (
  echo Could not find index.html next to this script.
  echo Expected: !HTML!
  pause
  exit /b 1
)

rem file:// URLs need forward slashes.
set "URL=file:///!HTML:\=/!"

set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "!EDGE!" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if not exist "!EDGE!" set "EDGE=%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"

if exist "!EDGE!" (
  echo Opening in Edge app window...
  start "" "!EDGE!" --app="!URL!"
) else (
  echo msedge.exe not found in the usual places - trying the shell alias.
  start "" msedge --app="!URL!"
)

rem Nothing to wait for; the window is Edge's.
exit /b 0
