# Bounty description for install executable for MS Windows

I believe most of this is now covered by [this script](../installfiles/RunMeAsAdmin-RightClick-toInstall.bat?raw=true)

A−Z+T installation would be greatly helped by having a simpler install process. Most of what is needed can be found in [this page](SIMPLEINSTALL.md), or in [this script](../installfiles/RunMetoInstall.bat?raw=true). This page will describe explicitly and in prioritized order what an install process (presumably using a single executable) should do.

1. The executable should be as general and future-proof as possible.
  - I hope that one executable file will work for the foreseeable future, so solutions that are specific to one version of Windows should be avoided, where possible.
  - Multiple versions could be acceptable, if necessary, but they should be minimal, and explicit for which applies to which case.
  - Work requiring updates is not acceptable, with the possible exception that support for such updates is included in this bounty.

2. As much as possible should be done invisibly to the user.
  - I have worked in the past to help the user navigate these installs, but this approach doesn't seem to help. so
    - The executable should just pick reasonable default options wherever possible, without asking or informing the user for each.
    - The executable should contain a single notice upfront that it will do so, with an option to exit (and a link to the [Simple Install](SIMPLEINSTALL.md) online doc) if that isn't wanted.
  - Capture any errors transparently, and send them to

3. Confirm the presence of (or install) Python.
  - Automate adding python to the system path, as in this image: ![Add Python to Path](images/Python_path.png "Add Python to Path")
  - Trigger the "remove path limitation" option in the Python install.
  - Currently between 3.9 and 3.12!!
  ~~At least version 3.6.8~~, though this is negotiable. Some install problems have been minimized in the past by using this version, rather than a newer version. If other solutions (e.g., pipwin) resolve these problems, any recent version may be OK.
    - https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe
    - https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe

  - This can happen concurrently with Git install, as they shouldn't depend on each other.

4. Confirm the presence of (or install) Git.
  - https://git-scm.com/download/win

5. Clone the A−Z+T repository
  - Normally, with `git clone https://github.com/kent-rasmussen/azt.git` from the desktop.
  - Cloning (not just downloading) is important here, because A−Z+T will update by updating this repository.
  - This may need git-bash, or the cmd or powershell —I'm frankly not sure what is the best way to do this given above priorities.
  - *The desktop* may not be the best place to store this repository. If it makes more sense to put it elsewhere (e.g., with other apps), let's discuss the rationale for the change. Most importantly, A−Z+T/Git must have permission to modify the contents of this repo.

6. Install a Desktop shortcut to `main.py` in the repository, and name it `A−Z+T`.

7. Check for (and maybe install) [Charis SIL](https://software.sil.org/charis/).

Install python module `pyaudio` and dependencies.
  - This has caused the largest number of install problems, so it would be nice if we could just get this out of the way, even though A−Z+T can do this for us, in at least some cases.
  - This may be a solved issue, if pipwin now works in A−Z+T.





convers
