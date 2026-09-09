#Installers in this folder

| File | Platform |
|---|---|
| `RunMetoInstall_Linux.sh` | Debian/Ubuntu: system packages, fonts, clone, desktop shortcut |
| `RunMeAsAdmin-RightClick-toInstall.bat` | Windows |
| `RunMetoInstall_Mac.command` | macOS — **draft, not yet run on a Mac**; see below |
| `azt.desktop` | the Linux shortcut installed by the Linux script |

##macOS

Double-click `RunMetoInstall_Mac.command`, or run it in Terminal to pass
switches — `--help` lists them, and `--dry-run` shows what it would do without
changing anything (worth doing first, while this is still a draft).

It installs git and python **without Xcode**, which is the whole difficulty:
macOS keeps stub shims at `/usr/bin/git`, `/usr/bin/clang` and
`/usr/bin/python3`, and merely running one of those pops the "install command
line developer tools" dialog. The script never touches them, and installs the
real tools from git-scm.com and python.org instead. Homebrew cannot be part of
the answer — it requires those same tools.

Fonts have no package manager here, so Charis SIL is not installed
automatically: download it from <https://software.sil.org/charis/> and re-run
with `--fonts=/path/to/that.zip`, or unzip it and drag the `.ttf` files onto
Font Book.

It also builds `env/` and installs the python packages, rather than leaving
that to the first run as the Linux and Windows installers do. Two reasons: a
first launch that silently downloads for several minutes is not what a user
expects, and — measured — A-Z+T's own first-run relaunch into `env/` **does
not survive a Terminal-based launcher**, because it starts the new process
without waiting and then exits, which ends the Terminal session under it. Both
launchers therefore start `env/bin/python` directly, so no relaunch is needed.
`--no-deps` skips the package install if you want the old behaviour.

You get two launchers. **`A-Z+T.app` on the Desktop** is the one to use; it is
the only form Finder will give a real icon, since a `.command` is a shell
script and always shows the generic script icon. **`A-Z+T.command`**, in the
A-Z+T folder, does the same thing but in Terminal, where you can see
everything the program prints — use that one when something goes wrong.

`--check-wheels` reports whether every dependency has a macOS wheel. That
matters because a Mac without developer tools has no compiler, so anything
lacking a wheel cannot be installed at all — and the fix for that belongs in
`requirements.txt`, not on the user's machine.

#Install a shortcut to A-Z+T in Ubuntu Linux

The azt.desktop file in this folder can likely enable a system shortcut to A-Z+T; place it in `$HOME/.local/share/applications/`, e.g.,
- `cp $HOME/path/to/installfiles/azt.desktop $HOME/.local/share/applications/`

Make sure it is executable, and that the paths in the file point to where your files are (main.py and images folder). Once you have modified it to fit your paths, validate the file format:

- `sudo desktop-file-validate  $HOME/.local/share/applications/azt.desktop`

To update your system so this will be used (you may also need to restart, and maybe marked it as "trusted", or some such):
- `sudo update-desktop-database`

You can also make a link to your desktop, or wherever, for easy access:
- `ln $HOME/.local/share/applications/azt.desktop $HOME/Desktop/`
