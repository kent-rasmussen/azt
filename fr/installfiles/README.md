#Installer un raccourci vers A→Z+T dans Ubuntu Linux

Le fichier azt.desktop dans ce dossier peut probablement activer un raccourci système vers A→Z+T ; placez-le dans `$HOME/.local/share/applications/` , par exemple,

- `cp $HOME/path/to/installfiles/azt.desktop $HOME/.local/share/applications/`

Assurez-vous qu'il est exécutable et que les chemins d'accès dans le fichier pointent vers l'endroit où se trouvent vos fichiers (dossier main.py et images). Une fois que vous l'avez modifié pour l'adapter à vos chemins, validez le format du fichier :

- `sudo desktop-file-validate  $HOME/.local/share/applications/azt.desktop`

Pour mettre à jour votre système afin qu'il soit utilisé (vous devrez peut-être également redémarrer, et peut-être le marquer comme "de confiance", ou quelque chose du genre):

- `sudo update-desktop-database`

Vous pouvez également créer un lien vers votre bureau, ou n'importe où, pour un accès facile :

- `ln $HOME/.local/share/applications/azt.desktop $HOME/Desktop/`
