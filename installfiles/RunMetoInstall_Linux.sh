#!/bin/bash
# A-Z+T installer for Debian/Ubuntu.
#
#   bash RunMetoInstall_Linux.sh [--no-deps]
#
#   --no-deps   Make env/ but don't download the python packages into it.
#               A-Z+T installs them on its first run instead, which takes
#               several minutes with no explanation.
#
# ─── ONE PLACE FOR THE PYTHON VERSION, AND IT IS A MINOR, NOT A PATCH ───────
# apt already gives the most recent PATCH of whatever minor is named, so there
# is deliberately no third number here to go stale — the same trick the Mac
# script uses for Charis, applied at the granularity where it is safe. That is
# not a tidiness point: python.org WITHDRAWS installers for versions past
# bugfix maintenance, so a hardcoded patch elsewhere in this project has
# already broken a platform's installer outright (Windows, found 2026-09-24).
# apt makes this script immune to that by construction. The MINOR is
# pinned on purpose: wheel availability is per minor version (cp312 vs cp313),
# so "whatever is newest" could land on a python no dependency has built for.
# docs/adr/0005-python-version-floor-and-ceiling.md is where that number is
# decided; change it there first, then here.
PYMINOR=3.12

DO_DEPS=yes
for arg in "$@"; do
    case "$arg" in
        --no-deps) DO_DEPS=no ;;
        --help|-h) sed -n '2,8p' "$0"; exit 0 ;;
        *) echo "I do not understand \"$arg\"." >&2; exit 2 ;;
    esac
done

echo "This script will ask for your sudo password to install repositories and programs"
echo "If a super user has already done that, just press control-C when asked for \
a sudo password, and it will continue"
(wget -O- https://packages.sil.org/keys/pso-keyring-2016.gpg | sudo tee /etc/apt/trusted.gpg.d/pso-keyring-2016.gpg)&>/dev/null
(. /etc/os-release && sudo tee /etc/apt/sources.list.d/packages-sil-org.list>/dev/null <<< "deb http://packages.sil.org/$ID $VERSION_CODENAME main")
# PortAudio: libportaudio2, NOT portaudio19-dev (changed 2026-09-11 with the
# sounddevice port, agenda/pyaudio_to_sounddevice.md). `-dev` supplies HEADERS,
# which were needed only because PyAudio compiled against them. sounddevice
# binds PortAudio at runtime with cffi, so the RUNTIME library is all that is
# wanted and no compiler is involved. Machines that ran the older version of
# this script already have it: portaudio19-dev depends on libportaudio2.
#   The hand-built-from-source lines that used to sit here went with it; there
# was never a reason to build PortAudio on a user's machine, and now there is
# not even a header to build against.
echo "The following assumes you have a debian system; if you don't, install"
echo "python${PYMINOR}-{tk,dev,venv} libpython${PYMINOR} git libportaudio2 texlive-xetex"
echo "with your package manager"
# python*-venv carries ensurepip: without it neither this script nor A-Z+T's
# first run can create the env/ virtual environment (field failure 2026-07-25).
sudo add-apt-repository --yes ppa:deadsnakes/ppa
sudo apt update
sudo apt-get install -y python${PYMINOR}-{tk,dev,venv} libpython${PYMINOR} git libportaudio2 texlive-xetex
echo "The following assumes you have a debian system; if you don't, install"
echo "the SIL package repository manually (instructions at https://packages.sil.org/)"
sudo apt-get install fonts-sil-charis
read -p "Super User stuff is done; the rest of this script should be done \
as a normal user.
If that's you, press Enter to continue.
If you are *not* the \
normal user of this machine, cancel here (Control-C), and have that user run \
this script again." </dev/tty
PY="python${PYMINOR}"
curl -sS https://bootstrap.pypa.io/get-pip.py |  "$PY"
# `pyaudio` dropped from this list 2026-09-11: it is no longer a requirement
# (sounddevice replaced it), and this line installs into the SYSTEM python,
# where a build failure would stop the bootstrap before the clone. A-Z+T's own
# packages go into its venv from requirements.txt, not here.
"$PY" -m pip install six lxml Pillow
cd;git clone https://github.com/kent-rasmussen/azt.git;cd -
# wget https://github.com/kent-rasmussen/azt/blob/main/installfiles/azt.desktop?raw=true -O azt.desktop
cp ${HOME}/azt/installfiles/azt.desktop $HOME/.local/share/applications/
sed -i "s|~|${HOME}|g" $HOME/.local/share/applications/azt.desktop
desktop-file-validate $HOME/.local/share/applications/azt.desktop
update-desktop-database $HOME/.local/share/applications
gio set $HOME/.local/share/applications/azt.desktop metadata::trusted true
chmod a+x $HOME/.local/share/applications/azt.desktop
ln -f $HOME/.local/share/applications/azt.desktop $HOME/Desktop/
# Install icon into the hicolor theme so GNOME/KDE can find it by name (Icon=azt)
ICON_SRC="${HOME}/azt/images/AZT green stacks_transparent_sm.png"
for sz in 16 32 48 64 128 256; do
    ICON_DIR="${HOME}/.local/share/icons/hicolor/${sz}x${sz}/apps"
    mkdir -p "${ICON_DIR}"
    "$PY" -c "from PIL import Image; im=Image.open('${ICON_SRC}'); im.thumbnail((${sz},${sz})); im.save('${ICON_DIR}/azt.png')"
done
gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
cd -

# ─── The virtual environment and its packages — BUILT HERE, ON PURPOSE ──────
# DECIDED 2026-09-23 (agenda/update_install_non-windows-specific.md). Kent: "I
# don't like people on any platform thinking they have installed, only to find
# that on first run there's a bunch more to install." A-Z+T can still do all of
# this itself on first run — that path is NOT going away, because it is how a
# change to requirements.txt reaches every EXISTING install — but a fresh
# install should be finished when it says it is finished, and any package that
# will not install should be reported now, to somebody who is still watching.
#
# It is LAST in this script deliberately. Everything above is quick and
# reliable; this is several minutes of downloading and the only step likely to
# fail. Putting it here means a failure leaves a complete, launchable install
# behind, which A-Z+T then finishes for itself on first run.
#
# THREE PIECES, and the third is the one that is easy to miss:
#   1. create env/ with the base python, and check it has pip;
#   2. pip install -r requirements.txt into it;
#   3. write <venv>/azt_requirements.stamp with the sha256 of requirements.txt.
# Without (3), sync_requirements() (utilities/py_modules.py) sees no matching
# stamp and re-resolves the whole file on first run anyway, so the upfront
# install would have bought the user nothing at all.
AZTDIR="$HOME/azt"
VENV="$AZTDIR/env"
VPY="$VENV/bin/python"
REQ="$AZTDIR/requirements.txt"
DEPS=skipped

echo
echo "== Building the python environment in $VENV"
if [ ! -f "$REQ" ]; then
    echo "   PROBLEM: no requirements.txt in $AZTDIR — did the clone above work?"
    echo "   Skipping; A-Z+T will try to sort itself out on first run."
elif [ -x "$VPY" ]; then
    echo "   env/ already exists; leaving it alone"
else
    "$PY" -m venv "$VENV"
    if [ ! -x "$VPY" ]; then
        echo "   PROBLEM: could not create $VENV."
        echo "   The usual cause is a missing python${PYMINOR}-venv package,"
        echo "   which carries ensurepip. Install it and run this script again."
    elif ! "$VPY" -m pip --version >/dev/null 2>&1; then
        echo "   PROBLEM: $VENV was made but has no pip, so nothing can be"
        echo "   installed into it. Install python${PYMINOR}-venv and re-run."
    else
        echo "   made $VENV (with pip)"
    fi
fi

if [ "$DO_DEPS" = no ]; then
    echo "== Python packages: skipped (--no-deps); A-Z+T will install them on first run"
elif [ -x "$VPY" ] && [ -f "$REQ" ]; then
    echo
    echo "== Installing the python packages (several minutes, needs the internet)"
    "$VPY" -m pip install --quiet --upgrade pip wheel >/dev/null 2>&1 \
        || echo "   could not update pip in the new env; carrying on"
    # `-f modulestoinstall` mirrors sync_requirements(), which looks there
    # first so an install can be completed from a USB stick with no network.
    # Unlike sync_requirements() this does not do a separate offline-only pass:
    # someone is watching a progress display here, so one pass that prefers the
    # local wheels and falls back to PyPI is the whole of it.
    # NO --only-binary. That constraint is the Mac's, and it is there because a
    # Mac may have no compiler at all; this script has already apt-installed
    # python${PYMINOR}-dev, so building from source is available and correct.
    if "$VPY" -m pip install -f "$AZTDIR/modulestoinstall" -r "$REQ"; then
        DEPS=yes
        echo "   packages installed"
    else
        DEPS=incomplete
        echo "   PROBLEM: at least one package would not install."
        echo "   A-Z+T will still start, and will try the rest itself. Send the"
        echo "   pip output above to the developer if it keeps happening."
    fi
    # The stamp, and ONLY if the whole unfiltered file went in as written. If
    # anything failed, withholding it is deliberate: A-Z+T must still try.
    if [ "$DEPS" = yes ]; then
        STAMP="$("$VPY" -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$REQ" 2>/dev/null)"
        if [ -n "$STAMP" ]; then
            printf '%s' "$STAMP" > "$VENV/azt_requirements.stamp" \
                && echo "   recorded the requirements stamp, so first run starts straight away"
        fi
    else
        echo "   not recording the requirements stamp, so A-Z+T will try the"
        echo "   rest of the packages itself when it starts"
    fi
fi

echo
echo "== Done"
echo "   A-Z+T:    $AZTDIR"
echo "   python:   $PY"
echo "   packages: $DEPS"
if [ "$DEPS" = yes ]; then
    echo
    echo "   The packages are already installed, so the first run should start"
    echo "   without a long wait. Launch A-Z+T from your desktop or menu."
else
    echo
    echo "   Some packages are NOT installed, so A-Z+T will finish the job when"
    echo "   it starts — that takes several minutes and needs the internet."
fi
