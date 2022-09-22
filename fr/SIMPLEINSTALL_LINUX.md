# Instructions simples et directes pour l'installation de A→Z+T sur Ubuntu Linux

Ce document propose des instructions avec **exactement un jeu d'options** ; pour explorer plus d'options, voir [INSTALLER](INSTALL.md) .

Pour des instructions d'installation simples pour MS Windows, voir [SIMPLEINSTALL](SIMPLEINSTALL.md) .

Si l'un des éléments suivants échoue, veuillez [m'écrire](BUGS.md) en copiant/collant toutes les erreurs que vous trouvez dans l'e-mail.

Pour exécuter ces commandes, ouvrez un terminal et copiez/collez la commande, puis appuyez sur Entrée. Vous devrez peut-être saisir votre mot de passe sudo/administrateur.

## Installer les packages système et python

Exécutez les commandes suivantes :

1. `sudo apt-get install git python3-tk python3-pip portaudio19-dev texlive-xetex` . (Ce dernier est un gros téléchargement)
2. `python3 -m pip install pyaudio lxml Pillow`
3. `cd;git clone https://github.com/kent-rasmussen/azt.git;cd -`

### Polices

Vérifiez que vous avez [Charis SIL](https://software.sil.org/charis/) sur votre système en exécutant la commande suivante : `fc-list|grep Charis`

Si cela ne renvoie aucun résultat, exécutez la commande suivante : `sudo apt-get install fonts-sil-charis`

Si cela génère une erreur, vous devrez peut-être d'abord installer le [référentiel de packages SIL](https://packages.sil.org/)

## Télécharger A→Z+T

Exécutez cette commande : `cd;git clone https://github.com/kent-rasmussen/azt.git` .

## Configurer A→Z+T pour une utilisation normale

1. Téléchargez [ce fichier](installfiles/azt.desktop?raw=true) . Si vous y êtes invité, enregistrez-le dans votre dossier "Téléchargements".
2. Exécutez les commandes suivantes :

- `cp $HOME/Downloads/azt.desktop $HOME/.local/share/applications/`
- `sudo desktop-file-validate  $HOME/.local/share/applications/azt.desktop`
- `sudo update-desktop-database`
- `ln $HOME/.local/share/applications/azt.desktop $HOME/Desktop/`

1. Cliquez sur le lien sur votre bureau pour exécuter A→Z+T
2. **Célébrez votre accomplissement; vous avez fini d'installer A→Z+T !**
3. Lisez [USAGE](USAGE.md) pour savoir comment utiliser A→Z+T
4. Envoyez-moi des informations sur les [bogues](BUGS.md) que vous trouvez, afin que je puisse vous aider et améliorer le programme pour les autres.

## Étapes importantes supplémentaires pour tirer le meilleur parti de A→Z+T

### Installez Mercurial pour une meilleure collaboration

exécutez cette commande : `sudo apt-get install mercurial`

### Soyez prêt à créer et à modifier des rapports

Demandez à quelqu'un de vous aider à installer l'éditeur XML XMLmind (XXE) (voir [INSTALLER](INSTALL.md) ).

### Mettre à jour A→Z+T (pour être sûr d'utiliser la version la plus récente)

Exécutez la commande `cd $HOME/azt;git pull;cd -` .
