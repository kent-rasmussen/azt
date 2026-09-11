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
FONT_ZIP=""              # a Charis zip you already downloaded
FONT_URL=""              # exact zip to fetch; overrides everything below
# WHERE THE FONTS COME FROM, in order: this API (which names the current
# release, so nothing here needs editing when SIL publishes 7.001), then the
# pinned URLs below as a fallback. Verified anonymous and listing
# Charis-7.000.zip on 2026-09-09.
FONT_API="https://api.github.com/repos/silnrsi/font-charis/releases/latest"
# ONE fallback, and it is not a version-tracking mechanism — the API above is
# that. This exists for a DIFFERENT failure: api.github.com being unreachable
# (rate-limited behind a shared NAT, or a proxy that permits software.sil.org
# but not GitHub). When that happens, a font one release behind beats no font
# at all, since without Charis the whole layout goes wrong. So it needs no
# urgent updating, and a second, older generation (CharisSIL-6.101.zip, also
# verified) was dropped as redundant: it would only ever be reached in the
# same situation, and brings a different family name for no benefit.
# VERIFIED BY HAND (Kent, 2026-09-09). The pattern is
#     https://software.sil.org/downloads/r/<family>/<Family>-<version>.zip
# and the FILENAME IS CASE-SENSITIVE: `Charis-7.000.zip` serves, while
# `charis-7.000.zip` does not — worth knowing before retyping it.
#
# A `github.com/silnrsi/font-charis/releases/latest/download/<asset>` URL was
# tried and does NOT work, for a reason worth keeping: that form redirects to
# a FIXED asset name within whatever release is latest, so it only works for
# projects whose asset filenames stay the same release to release. This one's
# embed the version (Kent 2026-09-09), so there is no stable name to ask for.
# Don't re-add it in that form. Asking the API what the asset names ARE is the
# way round it, which is what FONT_API above does.
#
# v7 renames the family from "Charis SIL" to "Charis". Safe either way here:
# A-Z+T accepts both names (the missing-font check asks for ['Charis SIL',
# 'Charis']) and the webview font stack lists both aliases. Only ONE
# generation is ever installed — two builds claiming the same family with
# different capabilities is a confusion already met in the tone work.
FONT_URLS="https://software.sil.org/downloads/r/charis/Charis-7.000.zip"
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
  --fonts=PATH           A Charis zip you have already downloaded
  --font-url=URL         Exact Charis zip to download instead
  --no-python            Don't install python, even if none is found
  --no-git               Don't install git, even if none is found
  --no-fonts             Skip the fonts (A-Z+T will lay out with a substitute
                         font, so text may wrap oddly and buttons look wrong)
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
        --font-url=*)       FONT_URL="${arg#*=}" ;;
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

# ONE scratch directory, made once, eagerly. It used to be a lazy tmpdir()
# function called in a command substitution — which cannot work: substitution
# runs in a SUBSHELL, so the assignment never reached this shell, every call
# made ANOTHER mktemp directory, the cleanup trap had nothing to remove, and
# two places that wrote and then read "the" log file were using different
# directories (found 2026-09-09 while chasing the font download).
TMPDIR_AZT="$(mktemp -d -t azt-install)" || die "could not make a temporary folder"
cleanup() { [ -n "${TMPDIR_AZT:-}" ] && [ -d "$TMPDIR_AZT" ] && rm -rf "$TMPDIR_AZT"; }
trap cleanup EXIT

# Does a file contain a match? NOT `... | grep -q`: under `set -o pipefail`
# (on, above) grep -q exits at its first match, the writer upstream dies of
# SIGPIPE with 141, and pipefail hands that back as the pipeline's status — so
# the test reports FALSE precisely when the match was found. That is what
# rejected every good font download (2026-09-09): the zip arrived, `unzip -l`
# listed its .ttf files, and the check failed anyway. grep reads a file here,
# with no pipe to break.
has_match() { # has_match <pattern> <file>
    grep -qi "$1" "$2" 2>/dev/null
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
    PKG="$TMPDIR_AZT/python.pkg"
    note "downloading $PYTHON_URL"
    if [ "$DRY_RUN" = no ]; then
        curl -fL --progress-bar -o "$PKG" "$PYTHON_URL" || {
            warn "that download failed — the URL has probably moved."
            note "Get the 'macOS 64-bit universal2 installer' by hand from"
            note "  https://www.python.org/downloads/macos/"
            note "run it, then run this script again."
            die "could not download python"
        }
        # Same pipefail/grep -q trap as the font check — see has_match().
        file "$PKG" > "$TMPDIR_AZT/pkg.type" 2>/dev/null
        has_match 'xar\|package' "$TMPDIR_AZT/pkg.type" \
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
    DMG="$TMPDIR_AZT/git.dmg"
    note "downloading $GIT_URL"
    if [ "$DRY_RUN" = no ]; then
        curl -fL --progress-bar -o "$DMG" "$GIT_URL" || {
            warn "that download failed — the URL has probably moved."
            note "Get the 'Binary installer' by hand from"
            note "  https://git-scm.com/download/mac"
            note "run it, then run this script again."
            die "could not download git"
        }
        MOUNT="$TMPDIR_AZT/gitmount"
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
# NOTHING BELOW RUNS unless the git we settled on is somewhere the default
# PATH does not already reach. That test is the whole gate, for both the
# symlink and the profile lines, and it is what keeps this script's hands off
# a Mac that is already in good order: with the developer tools installed,
# /usr/bin/git is a REAL git and already first-class on PATH, so there is
# nothing to fix — creating /usr/local/bin/git there would be pointless sudo,
# and worse, that is exactly where Homebrew puts its own git on an Intel Mac.
GIT_DIR_ON_PATH=""
case "$(dirname "$GIT" 2>/dev/null)" in
    /usr/local/bin|/usr/bin|/bin|.|"") : ;;  # already on the default PATH
    *) GIT_DIR_ON_PATH="$(dirname "$GIT")" ;;
esac
if [ -z "$GIT_DIR_ON_PATH" ]; then
    note "git is already where the system looks for it; nothing to adjust"
else
    if [ -e /usr/local/bin/git ]; then
        note "/usr/local/bin/git already exists; leaving it as it is"
    else
        note "linking $GIT into /usr/local/bin, so \`which git\` finds it"
        note "and not the /usr/bin/git stub"
        run sudo mkdir -p /usr/local/bin
        run sudo ln -sf "$GIT" /usr/local/bin/git
    fi
    # Belt and braces for interactive shells. BOTH files: macOS has defaulted
    # to zsh since Catalina, so writing only ~/.bash_profile (the advice you
    # still find online) achieves nothing on a current Mac — CONFIRMED on the
    # Mac tested 2026-09-08, which was running zsh.
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
    # Download it, like python and git. Charis is not optional decoration: the
    # program lays its screens out with it, and without it Tk substitutes
    # '.AppleSystemUIFont', whose metrics differ from every other machine — so
    # text wraps oddly and buttons come out the wrong size (measured on this
    # Mac 2026-09-08; A-Z+T says so itself in a "Missing font!" notice).
    #
    # The URLs are verified (see FONT_URLS), but they are still VERSIONED, so
    # they will go stale when SIL publishes 7.001. Hence: try each in turn,
    # and check the download really contains .ttf files before installing
    # anything — a 404 page saved as charis.zip must not count as success.
    # `--font-url=` overrides the list; the manual path below still applies if
    # every candidate has moved.
    # Ask GitHub what the current release actually is, so this does not need
    # editing every time SIL publishes. Verified 2026-09-09: the endpoint is
    # anonymous for a public repo and lists Charis-<version>.zip among its
    # assets. curl does the fetching (system TLS, and it does not depend on
    # whether python's certificates were ever installed — the python.org
    # installer leaves that to a separate step); python only parses what
    # arrives, which it can do without a network or a cert store.
    LATEST_URL=""
    if [ -z "$FONT_ZIP" ] && [ -z "$FONT_URL" ] && [ "$DRY_RUN" = no ]; then
        note "asking GitHub which Charis release is current"
        API_JSON="$(curl -fsS "$FONT_API" 2>/dev/null)" || API_JSON=""
        if [ -n "$API_JSON" ]; then
            LATEST_URL="$(printf '%s' "$API_JSON" | "$PY" -c 'import json,sys
try:
    assets=json.load(sys.stdin).get("assets") or []
except Exception:
    sys.exit(1)
for a in assets:
    u=a.get("browser_download_url") or ""
    if u.endswith(".zip"):      # .tar.xz and .asc are also published
        print(u); break' 2>/dev/null)" || LATEST_URL=""
        fi
        if [ -n "$LATEST_URL" ]; then
            note "current release: $LATEST_URL"
        else
            note "couldn't ask GitHub; falling back to the known links"
        fi
    fi
    if [ -z "$FONT_ZIP" ] && [ "$DO_FONTS" = yes ]; then
        for url in ${FONT_URL:-${LATEST_URL:-} $FONT_URLS}; do
            [ "$DRY_RUN" = yes ] && { note "would try $url"; continue; }
            cand="$TMPDIR_AZT/charis.zip"
            note "trying $url"
            if ! curl -fL --silent --show-error -o "$cand" "$url"; then
                note "that download didn't work; trying the next"
                rm -f "$cand"
                continue
            fi
            # Listing to a FILE, then searching the file: see has_match().
            unzip -l "$cand" > "$TMPDIR_AZT/charis.list" 2>/dev/null
            if has_match '\.ttf' "$TMPDIR_AZT/charis.list"; then
                note "downloaded the fonts"
                FONT_ZIP="$cand"
                break
            fi
            note "what arrived has no .ttf files in it; trying the next"
            rm -f "$cand"
        done
    fi
    if [ -n "$FONT_ZIP" ] && [ -f "$FONT_ZIP" ]; then
        UNZ="$TMPDIR_AZT/fonts"
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
        note "Could not get the Charis fonts automatically. A-Z+T will run, but"
        note "text will be laid out with a substitute font, so words may wrap"
        note "oddly and buttons may look wrong. To fix it:"
        note "  1. download the fonts from https://software.sil.org/charis/"
        note "  2. re-run this script with --fonts=/path/to/that.zip"
        note "     (or just unzip it and drag the .ttf files onto Font Book)"
        note "If you know the direct link, --font-url=<URL> also works, and"
        note "telling the developer what it is lets everyone skip this."
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

# ─── 4a. Make the shallow clone able to see the branches a user needs ───────
# `--depth 1` implies `--single-branch`, which writes a refspec covering ONLY
# the cloned branch. The clone then LOOKS normal but `git checkout testing`
# fails with "did not match any file(s) known to git", because no ref for it
# can ever arrive (Kent, 2026-09-09, on this Mac).
#
# NAMED BRANCHES, NOT '*' (Kent 2026-09-09: "we could just fetch main and
# program.testversionname; those should be the only branches a normal user
# would need"). That is exactly right, and the code agrees: vcs.py:1126
# toggles `testversionname if self.branch=='main' else 'main'` — those two
# names are the whole of what the update/test-version feature can reach. A '*'
# refspec would also drag in every work branch on the remote, which no user
# has any use for.
#
# The name is READ FROM main.py rather than hardcoded, so this keeps step with
# program['testversionname'] if it ever changes.
#
# A-Z+T's own branch switching does not depend on any of this:
# fetch_tracking_branch() (vcs.py:1200) fetches
# `<branch>:refs/remotes/origin/<branch>` explicitly for exactly this reason.
# This is for working on the clone BY HAND, which is how it was found.
if [ -d "$DEST/.git" ] && [ "$DRY_RUN" = no ]; then
    TESTBRANCH="$(sed -n "s/.*'testversionname' *: *'\([^']*\)'.*/\1/p" \
                    "$DEST/main.py" 2>/dev/null | head -1)"
    if [ -z "$TESTBRANCH" ]; then
        TESTBRANCH=testing
        note "couldn't read testversionname from main.py; assuming '$TESTBRANCH'"
    fi
    # set-branches REPLACES the list, so the cloned branch has to go back in
    # too — otherwise asking for main and testing would strip a --branch=dev
    # clone of its own refspec.
    "$GIT" -C "$DEST" remote set-branches origin main 2>/dev/null
    for b in "$TESTBRANCH" ${BRANCH:-}; do
        [ "$b" = main ] && continue
        "$GIT" -C "$DEST" remote set-branches --add origin "$b" 2>/dev/null
    done
    note "refspec now covers main and $TESTBRANCH${BRANCH:+ and $BRANCH}"
    "$GIT" -C "$DEST" fetch -q --depth 1 origin \
        && note "fetched those branch tips (still shallow)" \
        || note "could not fetch them; \`git fetch --depth 1\` will retry"
elif [ -d "$DEST/.git" ]; then
    note "would point the refspec at main plus the test-version branch and fetch"
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
# WHEELS-ONLY, BUT ONLY WHEN THERE IS NO COMPILER. With no developer tools, a
# package that needs building must FAIL AND SAY SO rather than invoke a clang
# that is not there — measured 2026-09-08, when an unconstrained pip put a
# modal "The ˋclangˊ command requires the command line developer tools" dialog
# in front of the user mid-boot, and cryptography got as far as downloading
# its own rustup and cargo. But on a Mac that HAS the tools, building is
# legitimate and works, exactly as on Linux, so the constraint is lifted:
# refusing source builds there would silently under-install (no sound, no
# collab crypto) on a machine that could have had them.
#
# PyAudio is attempted on its own either way: sound is optional in the program
# (program['nosound']), so its failure must not fail everything else. The
# Linux script installs portaudio19-dev precisely because it can need a
# compiler.
#
# torch needs nothing here any more: requirements.txt now carries the marker
# split (`+cpu` for non-Darwin, plain 2.7.1 for Darwin), because `+cpu` is
# built only for Linux/Windows and made the whole -r fail on this Mac.
# allosaurus was already excluded by its own `sys_platform == "linux"`.
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
    note "would install requirements.txt into env/"
else
    say "Installing the python packages (several minutes, needs the internet)"
    REQ="$DEST/requirements.txt"
    [ -f "$REQ" ] || die "no requirements.txt in $DEST"
    "$VPY" -m pip install --quiet --upgrade pip wheel >/dev/null 2>&1 \
        || note "could not update pip in the new env; carrying on"
    # See the note above: wheels-only ONLY when there is no compiler to use.
    WHEELS_ONLY=""
    if [ "$CLT_PRESENT" = yes ]; then
        note "developer tools are present, so packages needing a build may build"
    else
        WHEELS_ONLY="--only-binary=:all:"
        note "no developer tools, so installing from wheels only: anything that"
        note "would need compiling is reported instead of prompting for Xcode"
    fi
    # NO FILTERING, AND NO SEPARATE SOUND ATTEMPT (2026-09-11). Both existed
    # for PyAudio, which needed a compiler this machine may not have, so it
    # was held out of `-r` and tried on its own where its failure could be
    # survived. `sounddevice` replaced it (agenda/pyaudio_to_sounddevice.md)
    # and ships PortAudio in a universal2 wheel, so sound now installs like
    # everything else and the special case is not just unnecessary, it was
    # actively harmful:
    #   1. `sed '/^PyAudio/d'` deleted nothing — PyAudio left requirements.txt
    #      2026-09-09 — so the filtered file was a pointless copy;
    #   2. `pip install PyAudio` then tried to BUILD PyAudio from source on a
    #      Mac, the exact failure the port removed, and told the user
    #      "A-Z+T will run WITHOUT sound" on a machine where sound works;
    #   3. worst, the stamp below was gated on `SOUND = yes`, so that
    #      guaranteed failure withheld the requirements stamp and A-Z+T ran
    #      pip again on EVERY startup. Kent asked why ("should finish the
    #      install and no rerun pip on each open?"); this was why.
    if "$VPY" -m pip install ${WHEELS_ONLY:+"$WHEELS_ONLY"} -r "$REQ"; then
        DEPS=yes
        SOUND=yes   # sounddevice is in requirements.txt; no separate step
        note "packages installed"
    else
        DEPS="incomplete"
        SOUND=unknown
        warn "at least one package would not install."
        note "On a Mac with no compiler the only cure is a wheel, and that has"
        note "to be fixed in requirements.txt — not on this machine. Send the"
        note "lines above to the developer. A-Z+T may still start."
    fi
    # The stamp, only if the WHOLE file went in as written.
    if [ "$DEPS" = yes ]; then
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
    <!-- REQUIRED FOR RECORDING. macOS 10.14+ gates the microphone behind
         TCC, and an app that asks for it WITHOUT this key is denied
         outright rather than prompting — so recording would fail with no
         dialog and no obvious reason. The string is what the system shows
         the user when it asks. (A-Z+T launched from Terminal borrows
         Terminal's permission instead, which is why the .command launcher
         can record when the .app cannot — an inconsistency worth knowing
         when a field report says "it works one way and not the other".) -->
    <key>NSMicrophoneUsageDescription</key>
    <string>A-Z+T records words spoken by language speakers, so it needs the microphone.</string>
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
            SQ="$TMPDIR_AZT/azticon.png"
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
# allosaurus already carries a `sys_platform == "linux"` marker, so it is not
# a macOS problem.
#
# PyAudio used to be checked separately here, because it needed a compiler and
# sound is optional in the program (program['nosound']). It is gone from
# requirements.txt (replaced by sounddevice, 2026-09-09), so there is nothing
# to check separately: sounddevice ships PortAudio in a universal2 wheel and
# is answered by the ordinary `-r` resolve below like anything else.
if [ "$CHECK_WHEELS" = yes ]; then
    say "Checking which requirements have macOS wheels (installing nothing)"
    if [ "$DRY_RUN" = yes ]; then
        note "would resolve requirements.txt with pip --dry-run --only-binary :all:"
    else
        REQ="$DEST/requirements.txt"
        [ -f "$REQ" ] || die "no requirements.txt in $DEST"
        WORK="$TMPDIR_AZT/wheelcheck"
        "$PY" -m venv "$WORK" || die "could not make a scratch venv"
        WPY="$WORK/bin/python"
        "$WPY" -m pip install --quiet --upgrade pip >/dev/null 2>&1
        # --only-binary stays unconditional HERE, unlike the install above:
        # the question this switch answers is "does a wheel exist", and that
        # does not change because the machine happens to own a compiler.
        if "$WPY" -m pip install --dry-run --only-binary :all: -r "$REQ" >"$TMPDIR_AZT/wheels.log" 2>&1; then
            note "RESULT: every requirement has a macOS wheel."
        else
            warn "RESULT: at least one requirement has no macOS wheel."
            note "The lines below name it. That is a packaging problem to fix"
            note "at the source — a wheel, or a platform marker like the one"
            note "allosaurus already has — NOT a reason to install Xcode on a"
            note "user's machine."
            tail -n 25 "$TMPDIR_AZT/wheels.log"
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
note "sound:    $SOUND (sounddevice, installed with the rest)"
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
