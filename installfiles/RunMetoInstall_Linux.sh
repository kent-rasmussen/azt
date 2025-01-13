#!/bin/bash
echo "This script will ask for your sudo password to install repositories and programs"
echo "If a super user has already done that, just press control-C when asked for \
a sudo password, and it will continue"
(wget -O- https://packages.sil.org/keys/pso-keyring-2016.gpg | sudo tee /etc/apt/trusted.gpg.d/pso-keyring-2016.gpg)&>/dev/null
(. /etc/os-release && sudo tee /etc/apt/sources.list.d/packages-sil-org.list>/dev/null <<< "deb http://packages.sil.org/$ID $VERSION_CODENAME main")
pafile=pa_stable_v190700_20210406.tgz
# wget https://files.portaudio.com/archives/${pafile}
# tar -xf ${pafile}
# cd portaudio && ./configure && make && sudo make install
echo "The following assumes you have a debian system; if you don't, install"
echo "python3.12-{tk,dev} libpython3.12 git portaudio19-dev texlive-xetex"
echo "with your package manager"
sudo add-apt-repository --yes ppa:deadsnakes/ppa
sudo apt update
sudo apt-get install -y python3.12-{tk,dev} libpython3.12 git portaudio19-dev texlive-xetex
# python3-tk python3-pip python3-pyaudio
echo "The following assumes you have a debian system; if you don't, install"
echo "the SIL package repository manually (instructions at https://packages.sil.org/)"
sudo apt-get install fonts-sil-charis
read -p $"Super User stuff is done; the rest of this script should be done \
as a normal user. \nIf that's you, press Enter to continue. \nIf you are *not* the \
normal user of this machine, cancel here (Control-C), and have that user run \
this script again." </dev/tty
curl -sS https://bootstrap.pypa.io/get-pip.py |  python3.12
python3.12 -m pip install six pyaudio lxml Pillow
cd;git clone https://github.com/kent-rasmussen/azt.git;cd -
# wget https://github.com/kent-rasmussen/azt/blob/main/installfiles/azt.desktop?raw=true -O azt.desktop
cp ${HOME}/azt/installfiles/azt.desktop $HOME/.local/share/applications/
sed -i "s|~|${HOME}|" $HOME/.local/share/applications/azt.desktop
desktop-file-validate $HOME/.local/share/applications/azt.desktop
update-desktop-database
gio set $HOME/.local/share/applications/azt.desktop metadata::trusted true
chmod a+x $HOME/.local/share/applications/azt.desktop
ln -f $HOME/.local/share/applications/azt.desktop $HOME/Desktop/
cd -
