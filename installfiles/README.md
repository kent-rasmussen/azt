#Install a shortcut to A→Z+T in Ubuntu Linux

The azt.desktop file in this folder can likely enable a system shortcut to A→Z+T; place it in `$HOME/.local/share/applications/`, e.g.,
- `cp $HOME/path/to/installfiles/azt.desktop $HOME/.local/share/applications/`

Make sure it is executable, and that the paths in the file point to where your files are (main.py and images folder). Once you have modified it to fit your paths, validate the file format:

- `sudo desktop-file-validate  $HOME/.local/share/applications/azt.desktop`

To update your system so this will be used (you may also need to restart, and maybe marked it as "trusted", or some such):
- `sudo update-desktop-database`

You can also make a link to your desktop, or wherever, for easy access:
- `ln $HOME/.local/share/applications/azt.desktop $HOME/Desktop/`
