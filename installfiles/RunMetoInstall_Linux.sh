#!/bin/bash
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
echo "python3.12-{tk,dev,venv} libpython3.12 git libportaudio2 texlive-xetex"
echo "with your package manager"
# python3.12-venv carries ensurepip: without it A-Z+T's first run can't create
# its env/ virtual environment (field failure 2026-07-25).
sudo add-apt-repository --yes ppa:deadsnakes/ppa
sudo apt update
sudo apt-get install -y python3.12-{tk,dev,venv} libpython3.12 git libportaudio2 texlive-xetex
echo "The following assumes you have a debian system; if you don't, install"
echo "the SIL package repository manually (instructions at https://packages.sil.org/)"
sudo apt-get install fonts-sil-charis
read -p "Super User stuff is done; the rest of this script should be done \
as a normal user.
If that's you, press Enter to continue.
If you are *not* the \
normal user of this machine, cancel here (Control-C), and have that user run \
this script again." </dev/tty
curl -sS https://bootstrap.pypa.io/get-pip.py |  python3.12
# `pyaudio` dropped from this list 2026-09-11: it is no longer a requirement
# (sounddevice replaced it), and this line installs into the SYSTEM python,
# where a build failure would stop the bootstrap before the clone. A-Z+T's own
# packages go into its venv from requirements.txt, not here.
python3.12 -m pip install six lxml Pillow
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
    python3.12 -c "from PIL import Image; im=Image.open('${ICON_SRC}'); im.thumbnail((${sz},${sz})); im.save('${ICON_DIR}/azt.png')"
done
gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
cd -
