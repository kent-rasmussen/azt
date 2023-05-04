#!/bin/bash
(wget -O- https://packages.sil.org/keys/pso-keyring-2016.gpg | sudo tee /etc/apt/trusted.gpg.d/pso-keyring-2016.gpg)&>/dev/null
(. /etc/os-release && sudo tee /etc/apt/sources.list.d/packages-sil-org.list>/dev/null <<< "deb http://packages.sil.org/$ID $VERSION_CODENAME main")
sudo apt update
sudo apt-get install git python3-tk python3-pip portaudio19-dev texlive-xetex && python3 -m pip install pyaudio lxml Pillow
cd;git clone https://github.com/kent-rasmussen/azt.git;cd -
echo "The following assumes you have a debian system; if you don't, install"
echo "the SIL package repository manually (instructions at https://packages.sil.org/)"
sudo apt-get install fonts-sil-charis
# wget https://github.com/kent-rasmussen/azt/blob/main/installfiles/azt.desktop?raw=true -O azt.desktop
cp ${HOME}/azt/installfiles/azt.desktop $HOME/.local/share/applications/
sed -i "s|~|${HOME}|" $HOME/.local/share/applications/azt.desktop
sudo desktop-file-validate $HOME/.local/share/applications/azt.desktop
sudo update-desktop-database
gio set $HOME/.local/share/applications/azt.desktop metadata::trusted true
chmod a+x $HOME/.local/share/applications/azt.desktop
ln $HOME/.local/share/applications/azt.desktop $HOME/Desktop/
cd -
