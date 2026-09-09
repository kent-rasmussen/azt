#!/bin/bash
# A-Z+T installer for macOS.  ***DRAFT — never yet run on a Mac.***
#
# Double-clickable: macOS opens a .command in Terminal. Also runnable as
#   bash RunMetoInstall_Mac.command [switches]
# Run with --help for the switch list, or --dry-run to see what it would do
# without changing anything (recommended for the first try).
#
# Parallel to RunMetoInstall_Linux.sh, and it does the same four jobs:
#   1. install python (with Tcl/Tk) and git
#   2. install the Charis SIL fonts
#   3. git clone azt into the home folder
#   4. leave a double-clickable launcher
# It does NOT create env/ or pip-install anything: A-Z+T does that itself on
# first run (utilities/py_modules.py ensure_venv + sync_requirements, which is
# also what keeps every install in sync with requirements.txt). Duplicating it
# here would just fight the stamp logic.
#
# ─── WHY THIS SCRIPT IS SHAPED THE WAY IT IS ────────────────────────────────
# Measured on a real Mac, 2026-09-08: the machine had NO Xcode command-line
# tools and its owner did not want them. macOS ships STUB SHIMS at /usr/bin
# for the developer tools — /usr/bin/git, /usr/bin/clang, /usr/bin/python3 —
# and merely RUNNING one pops the "Install command line developer tools?"
# dialog. That, not any real build step, is almost certainly what was "asking
# at clang and git cloning".
#
# So the hard rule here: NEVER invoke /usr/bin/{git,clang,python3} while the
# command-line tools are absent. safe_tool() below enforces it, and it is why
# the script looks for interpreters by full path instead of asking `which`.
#
# Both tools can be installed without Xcode:
#   * git — the official binary installer from git-scm.com/download/mac
#     (a .dmg carrying a .pkg; installs to /usr/local/git).
#   * python — the python.org .pkg, which bundles Tcl/Tk. Homebrew is NOT an
#     option: brew itself requires the command-line tools.
# After installing git we SYMLINK it into /usr/local/bin, which is already on
# the PATH (it is in /etc/paths, and it is where the python.org installer puts
# its own python3). That matters beyond convenience: backend/core/vcs.py runs
# git as a bare command name, so a git that is only reachable via a PATH line
# in a profile file would be invisible to the program. The profile lines still
# get written — for zsh AND bash, since macOS has defaulted to zsh since
# Catalina and a ~/.bash_profile alone is never read.
#
# ─── THE TWO DOWNLOAD URLS — CHECKED 2026-09-08 ─────────────────────────────
# Both were opened by hand and both serve a file:
#   PYTHON_URL — python.org's ftp pattern is confirmed: the download offered
#     itself as `python-3.13.15-macos11.pkg`. That also confirms 3.13.15 is a
#     real release (the tested Mac reported it), so it is the default here.
#   GIT_URL — SourceForge's "latest release" redirect for git-osx-installer
#     does start a download. BUT the project is marked **Abandoned** there.
#     Consequences to expect, and to check on the first real run:
#       * the git it installs will be YEARS old. That is tolerable for what
#         A-Z+T asks of git (clone, pull, commit, push) but it is not a thing
#         to be pleased about, and it is worth re-checking whether a
#         maintained no-Xcode source has appeared.
#       * those builds are likely Intel-only. On an Apple Silicon Mac that
#         means Rosetta 2 — which macOS offers to install on its own, needing
#         no developer tools, so it is a prompt rather than a wall. UNVERIFIED:
#         nobody has run this on an arm64 Mac yet.
#       * it is not notarised, so a double-click on the .pkg can be refused.
#         `sudo installer` from a script is not subject to that check, which
#         is why the install is done here rather than by telling the user to
#         open the disk image.
# Still unverified: whether every requirement has a macOS wheel for this
# python and this architecture (no compiler = wheels only). --check-wheels
# answers that without installing anything; it is the main open macOS question.

set -u
set -o pipefail

# ─── Settings (switches only — no environment variables) ────────────────────
DEST="$HOME/azt"
REPO="https://github.com/kent-rasmussen/azt.git"
BRANCH=""
PY_VERSION="3.13.15"     # confirmed available as python-3.13.15-macos11.pkg
PYTHON_URL=""            # derived from PY_VERSION unless given
GIT_URL="https://sourceforge.net/projects/git-osx-installer/files/latest/download"
FONT_ZIP=""              # a Charis SIL zip you already downloaded
MIN_MINOR=11             # python 3.11+
DO_PYTHON=yes
DO_GIT=yes
DO_FONTS=yes
DO_SHORTCUT=yes
DO_DEPS=yes
CHECK_WHEELS=no
DRY_RUN=no

usage() {
    cat <<'EOF'
Install A-Z+T on macOS, without Xcode.

  --dry-run              Say what would happen; change nothing.
  --dest=PATH            Where to put A-Z+T (default: ~/azt)
  --repo=URL             Repository to clone (default: kent-rasmussen/azt)
  --branch=NAME          Branch to check out (default: the repo's default)
  --python-version=X.Y.Z Python to install if none is usable (default 3.13.15)
  --python-url=URL       Exact python .pkg to install instead
  --git-url=URL          Exact git .dmg/.pkg to install instead
  --fonts=PATH           A Charis SIL zip you have already downloaded
  --no-python            Don't install python, even if none is found
  --no-git               Don't install git, even if none is found
  --no-fonts             Skip the fonts
  --no-shortcut          Don't make the launcher, the app or the Desktop copy
  --no-deps              Make env/ but don't download the python packages
                         into it (A-Z+T will do it on its first run instead,
                         which takes several minutes with no explanation)
  --check-wheels         After cloning, report which requirements have no
                         macOS wheel (needs no compiler, installs nothing)
  --help                 This.

Installing python or git needs an administrator password. Everything else
runs as you. Nothing outside ~/azt, ~/Library/Fonts, ~/Desktop and the two
shell profile files is touched.
EOF
}

for arg in "$@"; do
    case "$arg" in
        --dry-run)          DRY_RUN=yes ;;
        --dest=*)           DEST="${arg#*=}" ;;
        --repo=*)           REPO="${arg#*=}" ;;
        --branch=*)         BRANCH="${arg#*=}" ;;
        --python-version=*) PY_VERSION="${arg#*=}" ;;
        --python-url=*)     PYTHON_URL="${arg#*=}" ;;
        --git-url=*)        GIT_URL="${arg#*=}" ;;
        --fonts=*)          FONT_ZIP="${arg#*=}" ;;
        --no-python)        DO_PYTHON=no ;;
        --no-git)           DO_GIT=no ;;
        --no-fonts)         DO_FONTS=no ;;
        --no-shortcut)      DO_SHORTCUT=no ;;
        --no-deps)          DO_DEPS=no ;;
        --check-wheels)     CHECK_WHEELS=yes ;;
        --help|-h)          usage; exit 0 ;;
        *)  printf 'I do not understand "%s".\n\n' "$arg" >&2; usage >&2; exit 2 ;;
    esac
done
[ -n "$PYTHON_URL" ] || PYTHON_URL="https://www.python.org/ftp/python/${PY_VERSION}/python-${PY_VERSION}-macos11.pkg"

# ─── Output. No colour anywhere: a step's result is in its words. ───────────
say()  { printf '\n== %s\n' "$*"; }
note() { printf '   %s\n' "$*"; }
warn() { printf '   PROBLEM: %s\n' "$*"; }
die()  { printf '\nSTOPPED: %s\n\n' "$*" >&2; exit 1; }
run()  {   # every state-changing command goes through this, so --dry-run works
    if [ "$DRY_RUN" = yes ]; then note "would run: $*"; return 0; fi
    "$@"
}

TMPDIR_AZT=""
cleanup() { [ -n "$TMPDIR_AZT" ] && [ -d "$TMPDIR_AZT" ] && rm -rf "$TMPDIR_AZT"; }
trap cleanup EXIT
tmpdir() {
    [ -n "$TMPDIR_AZT" ] || TMPDIR_AZT="$(mktemp -d -t azt-install)" \
        || die "could not make a temporary folder"
    printf '%s' "$TMPDIR_AZT"
}

# ─── The shim rule ──────────────────────────────────────────────────────────
# True when the Xcode command-line tools are actually installed. When false,
# anything under /usr/bin that belongs to them is a trap, not a program.
CLT_PRESENT=no
xcode-select -p >/dev/null 2>&1 && CLT_PRESENT=yes

safe_tool() {
    # safe_tool <absolute path> — echo it only if it is executable AND not a
    # developer-tools shim we must not touch. Never runs the program.
    local path="$1"
    [ -n "$path" ] && [ -x "$path" ] || return 1
    case "$path" in
        /usr/bin/git|/usr/bin/clang|/usr/bin/cc|/usr/bin/python3|/usr/bin/python*)
            [ "$CLT_PRESENT" = yes ] || return 1 ;;
    esac
    printf '%s' "$path"
}

say "A-Z+T installer for macOS (draft)"
note "macOS:        $(sw_vers -productVersion 2>/dev/null || echo unknown)"
note "processor:    $(uname -m)  (arm64 = Apple Silicon, x86_64 = Intel)"
note "install into: $DEST"
if [ "$CLT_PRESENT" = yes ]; then
    note "Xcode command-line tools: installed (so /usr/bin/git etc. are real)"
else
    note "Xcode command-line tools: NOT installed — and this script will not"
    note "  touch /usr/bin/git, /usr/bin/python3 or /usr/bin/clang, because"
    note "  running one of those is what pops the 'install developer tools'"
    note "  dialog. Nothing here needs them."
fi
[ "$DRY_RUN" = yes ] && note "DRY RUN: nothing will be changed."

# ─── 1. Python ──────────────────────────────────────────────────────────────
# tkinter is checked, not assumed: it is still A-Z+T's default interface, and
# a python without it installs perfectly and then opens no window. The
# python.org build bundles Tcl/Tk; some others do not.
say "Looking for a python A-Z+T can use (3.$MIN_MINOR+, with tkinter)"
PY=""
find_python() {
    local candidate ver minor
    for candidate in \
        /usr/local/bin/python3.14 /usr/local/bin/python3.13 \
        /usr/local/bin/python3.12 /usr/local/bin/python3.11 \
        /usr/local/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
        /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 \
        /opt/homebrew/bin/python3
    do
        candidate="$(safe_tool "$candidate")" || continue
        ver="$("$candidate" -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)" || continue
        case "$ver" in 3.*) minor="${ver#3.}" ;; *) continue ;; esac
        [ "$minor" -ge "$MIN_MINOR" ] 2>/dev/null || continue
        if "$candidate" -c 'import tkinter' >/dev/null 2>&1; then
            PY="$candidate"; note "found $candidate (python $ver, tkinter works)"
            return 0
        fi
        note "skipping $candidate (python $ver): no tkinter"
    done
    return 1
}

if find_python; then
    :
elif [ "$DO_PYTHON" = no ]; then
    die "no usable python, and --no-python says not to install one"
else
    note "no usable python found; installing python $PY_VERSION from python.org"
    note "(NOT Homebrew — brew itself requires the Xcode command-line tools)"
    PKG="$(tmpdir)/python.pkg"
    note "downloading $PYTHON_URL"
    if [ "$DRY_RUN" = no ]; then
        curl -fL --progress-bar -o "$PKG" "$PYTHON_URL" || {
            warn "that download failed — the URL has probably moved."
            note "Get the 'macOS 64-bit universal2 installer' by hand from"
            note "  https://www.python.org/downloads/macos/"
            note "run it, then run this script again."
            die "could not download python"
        }
        file "$PKG" | grep -qi 'xar\|package' \
            || die "what downloaded is not an installer package: $PKG"
    fi
    note "installing it — macOS will ask for your administrator password"
    run sudo installer -pkg "$PKG" -target / || die "the python installer failed"
    # The python.org installer runs a certificate/PATH postinstall step and
    # drops python3 into /usr/local/bin, so re-probe rather than guessing.
    if [ "$DRY_RUN" = no ]; then
        find_python || die "python installed but I still cannot find a usable one"
    else
        PY="/usr/local/bin/python3"; note "would then use $PY"
    fi
fi

# ─── 2. Git ─────────────────────────────────────────────────────────────────
say "Looking for git"
GIT=""
find_git() {
    local candidate
    for candidate in /usr/local/bin/git /usr/local/git/bin/git \
                     /opt/homebrew/bin/git /usr/bin/git
    do
        candidate="$(safe_tool "$candidate")" || continue
        if "$candidate" --version >/dev/null 2>&1; then
            GIT="$candidate"
            note "found $candidate ($("$candidate" --version 2>/dev/null))"
            return 0
        fi
    done
    return 1
}

if find_git; then
    :
elif [ "$DO_GIT" = no ]; then
    die "no git, and --no-git says not to install one"
else
    note "no usable git found; installing the stand-alone binary git-scm.com"
    note "points at. It is an OLD git (that project is abandoned), but it is"
    note "the one way to get git here without the Xcode tools, and it does"
    note "everything A-Z+T asks of git."
    DMG="$(tmpdir)/git.dmg"
    note "downloading $GIT_URL"
    if [ "$DRY_RUN" = no ]; then
        curl -fL --progress-bar -o "$DMG" "$GIT_URL" || {
            warn "that download failed — the URL has probably moved."
            note "Get the 'Binary installer' by hand from"
            note "  https://git-scm.com/download/mac"
            note "run it, then run this script again."
            die "could not download git"
        }
        MOUNT="$(tmpdir)/gitmount"
        mkdir -p "$MOUNT"
        hdiutil attach "$DMG" -nobrowse -quiet -mountpoint "$MOUNT" \
            || die "could not open the git disk image"
        GITPKG="$(find "$MOUNT" -maxdepth 2 -name '*.pkg' -print -quit)"
        if [ -z "$GITPKG" ]; then
            hdiutil detach "$MOUNT" -quiet 2>/dev/null
            die "no installer package inside the git disk image"
        fi
        note "installing $(basename "$GITPKG") — administrator password needed"
        # The git-osx-installer package is not notarised, so a plain
        # double-click can be refused by Gatekeeper; `installer` from the
        # command line is not subject to that check, which is another reason
        # to do this here rather than tell the user to open the .dmg.
        sudo installer -pkg "$GITPKG" -target / ; rc=$?
        hdiutil detach "$MOUNT" -quiet 2>/dev/null
        [ "$rc" -eq 0 ] || die "the git installer failed"
    else
        note "would mount it and run: sudo installer -pkg <the .pkg> -target /"
    fi

    if [ "$DRY_RUN" = no ]; then
        find_git || die "git installed but I still cannot find it"
    else
        GIT=/usr/local/git/bin/git
    fi
fi

# ─── 2b. Make a bare `git` resolve to THIS git, not the Xcode stub ──────────
# This runs whether or not we did the installing, because a git put there by
# an earlier attempt has exactly the same problem.
#
# It is not cosmetic. backend/core/vcs.py finds git through
# utilities/file.py::findexecutable(), which on Darwin shells out to
# `which git` — so A-Z+T uses whatever PATH offers, not what we found above.
# /usr/bin/git EXISTS as a file whether or not the developer tools do, so
# `which git` happily returns the stub, and A-Z+T would pop the "install
# developer tools" dialog from inside the program. macOS PATH order (from
# /etc/paths) puts /usr/local/bin BEFORE /usr/bin, so a symlink there wins.
if [ -n "$GIT" ] && [ "$GIT" != /usr/local/bin/git ]; then
    if [ -e /usr/local/bin/git ]; then
        note "/usr/local/bin/git already exists; leaving it as it is"
    else
        note "linking $GIT into /usr/local/bin, so \`which git\` finds it"
        note "and not the /usr/bin/git stub"
        run sudo mkdir -p /usr/local/bin
        run sudo ln -sf "$GIT" /usr/local/bin/git
    fi
fi
# Belt and braces for interactive shells, and ONLY when it buys something:
# the git we settled on has to live somewhere the default PATH does not
# already cover. Writing a PATH line unconditionally (as this did briefly)
# appends /usr/local/git/bin to both profiles even on a Mac whose git is
# /usr/bin/git — a directory that does not exist, in a file the user has to
# live with.
# BOTH files when it does apply: macOS has defaulted to zsh since Catalina, so
# writing only ~/.bash_profile (the advice you still find online) achieves
# nothing on a current Mac — CONFIRMED on the Mac tested 2026-09-08, which was
# running zsh.
GIT_DIR_ON_PATH=""
case "$(dirname "$GIT" 2>/dev/null)" in
    /usr/local/bin|/usr/bin|/bin|.|"") : ;;  # already on the default PATH
    *) GIT_DIR_ON_PATH="$(dirname "$GIT")" ;;
esac
if [ -n "$GIT_DIR_ON_PATH" ]; then
    for profile in "$HOME/.zprofile" "$HOME/.bash_profile"; do
        if [ -f "$profile" ] && grep -q "$GIT_DIR_ON_PATH" "$profile" 2>/dev/null; then
            note "$(basename "$profile") already mentions it; leaving it alone"
        elif [ "$DRY_RUN" = yes ]; then
            note "would add $GIT_DIR_ON_PATH to PATH in $profile"
        else
            printf '\n# added by A-Z+T installer: real git, not the Xcode stub\nPATH=%s:$PATH\n' \
                "$GIT_DIR_ON_PATH" >> "$profile"
            note "added $GIT_DIR_ON_PATH to PATH in $(basename "$profile")"
        fi
    done
fi

# ─── 2c. Is this git new enough? ────────────────────────────────────────────
# The stand-alone installer's git is from 2015 (2.6.2 as of 2026-09-08). What
# A-Z+T asks of git is mostly ancient and safe — clone, pull, commit, push,
# `git -C` (1.8.5), `--single-branch` (1.7.10), `--depth`, `--ff-only`. One
# thing is not:
#   `git init --initial-branch=main` needs git 2.28 (2020). vcs.py::init()
#   already handles the refusal (it retries as plain `git init` when it sees
#   "unknown option"), so nothing crashes — but plain `git init` creates
#   **master**, while the rest of the program says **main** (`git pull u
#   main`, switchbranches(), etc.). So on an old git, a repository A-Z+T
#   CREATES lands on the wrong branch name. Cloning an existing repo is
#   unaffected: clone follows the remote's own HEAD.
GIT_VERSION=""
if [ -n "$GIT" ] && [ "$DRY_RUN" = no ]; then
    GIT_VERSION="$("$GIT" --version 2>/dev/null | awk '{print $3}')"
    gmaj="${GIT_VERSION%%.*}"
    grest="${GIT_VERSION#*.}"; gmin="${grest%%.*}"
    if [ -n "$gmaj" ] && [ -n "$gmin" ] 2>/dev/null &&
       { [ "$gmaj" -lt 2 ] 2>/dev/null ||
         { [ "$gmaj" -eq 2 ] && [ "$gmin" -lt 28 ] 2>/dev/null; }; }; then
        warn "this git is $GIT_VERSION, older than 2.28."
        note "Everything A-Z+T does with an EXISTING repository works. But if"
        note "A-Z+T ever creates a new one here, it will be on a branch called"
        note "'master' where the program expects 'main', because this git has"
        note "no --initial-branch. Tell the developer if you hit that; a newer"
        note "git without Xcode is possible (see the notes in"
        note "agenda/rework_install_procedure.md)."
    fi
fi

# ─── 3. Fonts ───────────────────────────────────────────────────────────────
# The Linux script gets these from the SIL package repository
# (fonts-sil-charis). macOS has no equivalent, so: use a zip if we were given
# one or can find one already downloaded, otherwise say plainly what to do.
# Not fatal — A-Z+T runs with substituted fonts, it just renders worse.
if [ "$DO_FONTS" = no ]; then
    say "Fonts: skipped (--no-fonts)"
    FONTS=skipped
else
    say "Charis SIL fonts"
    FONTS=no
    if [ -z "$FONT_ZIP" ]; then
        FONT_ZIP="$(find "$HOME/Downloads" -maxdepth 1 -iname '*charis*.zip' -print -quit 2>/dev/null)"
        [ -n "$FONT_ZIP" ] && note "found $FONT_ZIP in your Downloads"
    fi
    if [ -n "$FONT_ZIP" ] && [ -f "$FONT_ZIP" ]; then
        UNZ="$(tmpdir)/fonts"
        if [ "$DRY_RUN" = yes ]; then
            note "would unpack $FONT_ZIP and copy its .ttf files to ~/Library/Fonts"
            FONTS="would install"
        elif unzip -q -o "$FONT_ZIP" -d "$UNZ"; then
            mkdir -p "$HOME/Library/Fonts"
            n=0
            while IFS= read -r ttf; do
                cp "$ttf" "$HOME/Library/Fonts/" && n=$((n+1))
            done < <(find "$UNZ" -iname '*.ttf' -print)
            if [ "$n" -gt 0 ]; then
                note "installed $n font files into ~/Library/Fonts"
                FONTS="yes ($n files)"
            else
                warn "no .ttf files inside $FONT_ZIP"
            fi
        else
            warn "could not unpack $FONT_ZIP"
        fi
    else
        note "No Charis SIL zip found. A-Z+T will run, but tone and IPA text"
        note "will render with substituted fonts. To fix it:"
        note "  1. download the fonts from https://software.sil.org/charis/"
        note "  2. re-run this script with --fonts=/path/to/that.zip"
        note "     (or just unzip it and drag the .ttf files onto Font Book)"
    fi
fi

# ─── 4. The program itself ──────────────────────────────────────────────────
say "Getting A-Z+T into $DEST"
# Shallow, per the decided item in agenda/rework_install_procedure.md
# ("Shallow cloning everywhere", Kent 2026-07-27): ~2 GB → ~50 MB, and an
# install has no use for history. The pull below is also depth-limited, since
# a plain `git pull` against a shallow clone starts deepening it again.
if [ -d "$DEST/.git" ]; then
    note "already a clone here; updating it instead"
    run "$GIT" -C "$DEST" pull --depth 1 --ff-only \
        || warn "could not fast-forward; your local changes are untouched"
elif [ -e "$DEST" ]; then
    die "$DEST exists and is not a git clone — move it aside, or use --dest="
else
    # A clone failure here is also the real test of whether a 2015-era git can
    # still talk to GitHub: GitHub requires TLS 1.2 and has dropped the weak
    # ciphers such a build may have been made against. Nothing else in this
    # script can tell us that, so the message says so rather than leaving a
    # bare "clone failed".
    clone_failed() {
        warn "the clone failed."
        note "If the message above mentions SSL, TLS or 'gnutls', that is the"
        note "old git (${GIT_VERSION:-unknown version}) being unable to"
        note "negotiate with GitHub, not a problem with your network. Options:"
        note "  * install a newer git any way you can, then re-run this"
        note "  * or ask the developer for a downloadable archive instead"
        die "could not get A-Z+T"
    }
    if [ -n "$BRANCH" ]; then
        run "$GIT" clone --depth 1 --single-branch --branch "$BRANCH" \
            "$REPO" "$DEST" || clone_failed
    else
        run "$GIT" clone --depth 1 --single-branch "$REPO" "$DEST" \
            || clone_failed
    fi
    note "cloned $REPO (shallow)"
fi

# ─── 4b. The virtual environment — BUILT HERE, ON PURPOSE ───────────────────
# A-Z+T can make its own env/ on first run (utilities/py_modules.py
# ensure_venv), and on Linux and Windows it does. On macOS that path is
# BROKEN, measured 2026-09-08:
#
#   ensure_venv() starts the venv python with `subprocess.Popen(...)` and then
#   immediately `sys.exit(0)` (py_modules.py:461-466) — fire and forget. Under
#   a .command launcher the exiting process IS the .command, so Terminal (which
#   appends `; exit;` to whatever it runs) ends the shell session, tears down
#   the tty, and SIGHUPs the orphaned grandchild before it prints anything. The
#   symptom is exactly "Relaunching inside the virtual environment: …" followed
#   by silence and "[Process completed]", with the app never appearing.
#
# Making env/ here removes the hop entirely: the launcher below starts the venv
# python directly, so ensure_venv() sees it is already inside a venv
# (py_modules.py:318) and returns without relaunching anything. Nothing about
# the app changes; it simply never has to fork on this platform.
say "Building the python environment in $DEST/env"
VENV="$DEST/env"
VPY="$VENV/bin/python"
if [ -x "$VPY" ]; then
    note "env/ already exists; leaving it alone"
elif [ "$DRY_RUN" = yes ]; then
    note "would run: $PY -m venv $VENV"
else
    "$PY" -m venv "$VENV" || die "could not create the environment at $VENV"
    [ -x "$VPY" ] || die "the environment was made but has no python"
    # A venv with no pip cannot be filled — by this script or by A-Z+T later.
    if "$VPY" -m pip --version >/dev/null 2>&1; then
        note "made $VENV (with pip)"
    else
        die "the environment has no pip; A-Z+T could not install anything into it"
    fi
fi

# ─── 4c. The python packages ────────────────────────────────────────────────
# Doing this here rather than on first run, per Kent 2026-09-08: "installing
# modules on first load is unexpected for most users". It also means a
# dependency that cannot be installed is reported NOW, to somebody who is
# still watching, instead of during a silent first launch.
#
# --only-binary :all: is not optional on macOS: with no compiler present, a
# package that needs building must FAIL AND SAY SO rather than invoke a clang
# that is not there. Two entries need care first:
#   torch==2.7.1+cpu  — that '+cpu' local version is built only for Linux and
#                       Windows. macOS wheels are plain 2.7.1, CPU-only anyway.
#   PyAudio           — historically needed portaudio and a compiler (the Linux
#                       script installs portaudio19-dev for exactly that), so
#                       it is attempted on its own: sound is optional in the
#                       program (program['nosound']) and everything else should
#                       not fail with it.
# allosaurus already carries `sys_platform == "linux"`, so it is not our problem.
#
# The STAMP at the end is what makes this actually save the user time.
# sync_requirements() (py_modules.py:491) skips its own install when
# <venv>/azt_requirements.stamp holds the sha256 of requirements.txt, so
# writing it here means first run starts straight away. Written ONLY on a
# clean install of the unfiltered file's hash — if anything was held back or
# failed, the stamp is left off deliberately so A-Z+T still tries on startup.
DEPS=skipped
SOUND=unknown   # set under set -u before any branch can skip it
if [ "$DO_DEPS" = no ]; then
    say "Python packages: skipped (--no-deps); A-Z+T will install them on first run"
elif [ "$DRY_RUN" = yes ]; then
    say "Python packages"
    note "would install requirements.txt into env/ with --only-binary :all:"
else
    say "Installing the python packages (several minutes, needs the internet)"
    REQ="$DEST/requirements.txt"
    [ -f "$REQ" ] || die "no requirements.txt in $DEST"
    "$VPY" -m pip install --quiet --upgrade pip wheel >/dev/null 2>&1 \
        || note "could not update pip in the new env; carrying on"
    FILTERED="$(tmpdir)/requirements-macos.txt"
    sed -e 's/^torch==2\.7\.1+cpu/torch==2.7.1/' -e '/^PyAudio/d' "$REQ" > "$FILTERED"
    note "torch pin relaxed to 2.7.1 (there is no +cpu build for macOS)"
    note "PyAudio held back for a separate attempt (sound is optional)"
    if "$VPY" -m pip install --only-binary :all: -r "$FILTERED"; then
        DEPS=yes
        note "packages installed"
    else
        DEPS="incomplete"
        warn "at least one package would not install."
        note "On a Mac with no compiler the only cure is a wheel, and that has"
        note "to be fixed in requirements.txt — not on this machine. Send the"
        note "lines above to the developer. A-Z+T may still start."
    fi
    # PyAudio on its own: sound is optional, so its failure is not the
    # install's failure.
    if "$VPY" -m pip install --only-binary :all: PyAudio >/dev/null 2>&1; then
        SOUND=yes
        note "PyAudio installed — recording and playback should work"
    else
        SOUND=no
        note "PyAudio would not install: A-Z+T will run WITHOUT sound."
        note "Recording and playback will be unavailable; nothing else changes."
    fi
    # The stamp, only if the WHOLE file went in as written.
    if [ "$DEPS" = yes ] && [ "$SOUND" = yes ]; then
        STAMP="$("$VPY" -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$REQ" 2>/dev/null)"
        if [ -n "$STAMP" ]; then
            printf '%s' "$STAMP" > "$VENV/azt_requirements.stamp" \
                && note "recorded the requirements stamp, so first run starts straight away"
        fi
    else
        note "not recording the requirements stamp (something is missing), so"
        note "A-Z+T will try the rest itself on startup"
    fi
fi

# ─── 5. Launchers ───────────────────────────────────────────────────────────
# TWO of them, for different jobs. The macOS counterpart of azt.desktop is
# really the .app; the .command is kept because it shows output.
#
#   A-Z+T.app      — what goes on the Desktop. A .app is the only thing Finder
#                    will give a real icon: a .command is a shell script, so it
#                    always shows the generic script icon no matter what is
#                    done to it (which is why the Desktop copy looked wrong,
#                    2026-09-08). It is a plain folder — Info.plist, a shell
#                    script, an .icns — so no developer tools are needed.
#   A-Z+T.command  — kept in the A-Z+T folder for when something goes wrong:
#                    Terminal shows everything the program prints, which is how
#                    the venv-relaunch failure above was diagnosed at all.
#
# BOTH set PATH themselves rather than relying on the profile files. That is
# essential for the .app: launchd hands a GUI app a bare PATH
# (/usr/bin:/bin:/usr/sbin:/sbin) and never reads ~/.zprofile, so `which git`
# inside A-Z+T would find the /usr/bin stub. BOTH also start the venv python
# DIRECTLY, so ensure_venv() never has to relaunch (see 4b).
LAUNCHER="$DEST/A-Z+T.command"
APPDIR="$HOME/Desktop/A-Z+T.app"
if [ "$DO_SHORTCUT" = no ]; then
    say "Launchers: skipped (--no-shortcut)"
else
    say "Making the launchers"
    # The line both launchers run. Prefer the venv python; fall back to the
    # base python if env/ ever goes missing, so a broken env still starts the
    # program (which will then rebuild it) rather than doing nothing at all.
    if [ "$DRY_RUN" = yes ]; then
        note "would write $LAUNCHER and $APPDIR"
    else
        cat > "$LAUNCHER" <<EOF
#!/bin/bash
# Run A-Z+T, showing everything it prints. Written by RunMetoInstall_Mac.command.
cd "$DEST" || exit 1
# A-Z+T finds git with \`which git\`, so the real git must come before
# /usr/bin, whose git may be only an Xcode stub.
PATH=${GIT_DIR_ON_PATH:+$GIT_DIR_ON_PATH:}/usr/local/bin:\$PATH
export PATH
# The venv python directly: A-Z+T then has no need to relaunch itself, which
# does not survive a Terminal session ending (see the installer's section 4b).
if [ -x "./env/bin/python" ]; then
    exec "./env/bin/python" main.py "\$@"
fi
exec "$PY" main.py "\$@"
EOF
        chmod +x "$LAUNCHER" || warn "could not make $LAUNCHER executable"
        note "made $LAUNCHER"

        # ── The .app bundle ──
        mkdir -p "$APPDIR/Contents/MacOS" "$APPDIR/Contents/Resources"
        cat > "$APPDIR/Contents/MacOS/A-Z+T" <<EOF
#!/bin/bash
# Written by RunMetoInstall_Mac.command.
cd "$DEST" || exit 1
PATH=${GIT_DIR_ON_PATH:+$GIT_DIR_ON_PATH:}/usr/local/bin:\$PATH
export PATH
if [ -x "./env/bin/python" ]; then
    exec "./env/bin/python" main.py "\$@"
fi
exec "$PY" main.py "\$@"
EOF
        chmod +x "$APPDIR/Contents/MacOS/A-Z+T"
        cat > "$APPDIR/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>            <string>A-Z+T</string>
    <key>CFBundleDisplayName</key>     <string>A-Z+T</string>
    <key>CFBundleExecutable</key>      <string>A-Z+T</string>
    <key>CFBundleIdentifier</key>      <string>org.atoznback.azt</string>
    <key>CFBundlePackageType</key>     <string>APPL</string>
    <key>CFBundleIconFile</key>        <string>azt.icns</string>
    <key>NSHighResolutionCapable</key> <true/>
</dict>
</plist>
EOF
        # The icon. `sips` is base-system (/usr/bin/sips), NOT part of the
        # developer tools, so it can do this here; `iconutil` would have been
        # the obvious tool and is exactly what we cannot rely on. It wants a
        # square source, so the logo is padded to one first. Best effort: with
        # no .icns the app still gets Finder's generic APPLICATION icon, which
        # is already better than a script icon.
        ICON_SRC="$DEST/images/AZT green stacks_transparent_sm.png"
        if [ -f "$ICON_SRC" ]; then
            SQ="$(tmpdir)/azticon.png"
            if sips --padToHeightWidth 512 512 --padColor FFFFFF \
                    "$ICON_SRC" --out "$SQ" >/dev/null 2>&1 &&
               sips -s format icns "$SQ" \
                    --out "$APPDIR/Contents/Resources/azt.icns" >/dev/null 2>&1
            then
                note "gave it the A-Z+T icon"
            else
                note "could not build the icon; the app will show the generic"
                note "application icon (harmless — tell the developer)"
            fi
        else
            note "no icon image at $ICON_SRC; using the generic one"
        fi
        # Finder caches by bundle mtime; touching it makes the new icon show
        # without a logout.
        touch "$APPDIR"
        note "made $APPDIR"
    fi
fi

# ─── 6. Optional: do the requirements have macOS wheels? ────────────────────
# The open macOS question. --only-binary :all: makes pip refuse anything that
# would need compiling, and --dry-run makes it resolve without installing, so
# this reports the answer without touching the machine or needing a compiler.
# Two entries in requirements.txt are known to need care here:
#   torch==2.7.1+cpu  — that '+cpu' local version is built only for Linux and
#                       Windows. macOS wheels are plain 2.7.1 (and CPU-only
#                       anyway), so the pin as written cannot resolve.
#   PyAudio           — historically needed portaudio and a compiler; the
#                       Linux script installs portaudio19-dev for exactly
#                       that. Checked on its own because sound is optional in
#                       the program (program['nosound']).
# allosaurus already carries a `sys_platform == "linux"` marker, so it is not
# a macOS problem.
if [ "$CHECK_WHEELS" = yes ]; then
    say "Checking which requirements have macOS wheels (installing nothing)"
    if [ "$DRY_RUN" = yes ]; then
        note "would resolve requirements.txt with pip --dry-run --only-binary :all:"
    else
        REQ="$DEST/requirements.txt"
        [ -f "$REQ" ] || die "no requirements.txt in $DEST"
        WORK="$(tmpdir)/wheelcheck"
        "$PY" -m venv "$WORK" || die "could not make a scratch venv"
        WPY="$WORK/bin/python"
        "$WPY" -m pip install --quiet --upgrade pip >/dev/null 2>&1
        FILTERED="$(tmpdir)/requirements-macos.txt"
        sed -e 's/^torch==2\.7\.1+cpu/torch==2.7.1/' -e '/^PyAudio/d' "$REQ" > "$FILTERED"
        note "torch pin relaxed to 2.7.1 for this check (no +cpu build for macOS)"
        note "PyAudio checked separately below"
        if "$WPY" -m pip install --dry-run --only-binary :all: -r "$FILTERED" >"$(tmpdir)/wheels.log" 2>&1; then
            note "RESULT: every other requirement has a macOS wheel."
        else
            warn "RESULT: at least one requirement has no macOS wheel."
            note "The lines below name it. That is a packaging problem to fix"
            note "at the source — a wheel, or a platform marker like the one"
            note "allosaurus already has — NOT a reason to install Xcode on a"
            note "user's machine."
            tail -n 25 "$(tmpdir)/wheels.log"
        fi
        if "$WPY" -m pip install --dry-run --only-binary :all: PyAudio >/dev/null 2>&1; then
            note "PyAudio: has a macOS wheel, so recording should work."
        else
            note "PyAudio: no macOS wheel. A-Z+T will run without sound;"
            note "  recording and playback will be unavailable."
        fi
    fi
fi

# ─── 7. What happened ───────────────────────────────────────────────────────
say "Done"
note "A-Z+T:    $DEST"
note "python:   $PY"
note "git:      $GIT${GIT_VERSION:+ (version $GIT_VERSION)}"
note "fonts:    $FONTS"
note "packages: $DEPS"
note "sound:    $SOUND"
if [ "$DO_SHORTCUT" = no ]; then
    note "start it with: cd $DEST && ./env/bin/python main.py"
else
    printf '\n   Start it by double-clicking A-Z+T on your Desktop.\n'
    printf '   If it misbehaves, run %s instead:\n' "$(basename "$LAUNCHER")"
    printf '   it is in %s and shows everything the program prints.\n' "$DEST"
fi
if [ "$DEPS" = yes ]; then
    cat <<'EOF'

   The packages are already installed, so the first run should start without
   a long wait.
EOF
else
    cat <<'EOF'

   Some packages are NOT installed, so A-Z+T will try to finish the job when
   it starts — that takes several minutes and needs the internet. If it
   reports something it cannot install, send that to the developer: on a Mac
   with no compiler the only cure is a wheel, and that has to be fixed in
   requirements.txt, not on this machine.
EOF
fi
