#!/bin/bash
(wget -O- https://packages.sil.org/keys/pso-keyring-2016.gpg | sudo tee /etc/apt/trusted.gpg.d/pso-keyring-2016.gpg)&>/dev/null
(. /etc/os-release && sudo tee /etc/apt/sources.list.d/packages-sil-org.list>/dev/null <<< "deb http://packages.sil.org/$ID $VERSION_CODENAME main")
pafile=pa_stable_v190700_20210406.tgz
# wget https://files.portaudio.com/archives/${pafile}
# tar -xf ${pafile}
# cd portaudio && ./configure && make && sudo make install
sudo add-apt-repository --yes ppa:deadsnakes/ppa
sudo apt update
sudo apt-get install -y python3.12-{tk,dev} libpython3.12 git portaudio19-dev texlive-xetex
# python3-tk python3-pip python3-pyaudio
curl -sS https://bootstrap.pypa.io/get-pip.py |  python3.12
python3.12 -m pip install six pyaudio lxml Pillow
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
