# Instructions simples et directes pour l'installation de A→Z+T sur MS Windows

Ce document propose des instructions avec **exactement un jeu d'options** ; pour explorer plus d'options, voir [INSTALLER](INSTALL.md) .

Pour des instructions d'installation simples pour Ubuntu Linux, voir [SIMPLEINSTALL_LINUX](SIMPLEINSTALL_LINUX.md) .

Si l'un des éléments suivants échoue, veuillez [m'écrire](BUGS.md) , y compris vos journaux et copier/coller toutes les erreurs que vous trouvez dans l'e-mail ( [cette page](FINDERRORLOGS.md) peut vous aider à trouver vos journaux).

Avant de pouvoir [configurer A→Z+T pour une utilisation normale](#set-up-azt-for-normal-use) , vous devez faire deux choses :

1. [Installer Python](#install-python)
2. [Installez Git et téléchargez A→Z+T](#install-git-and-download-azt)

## Installer Python

1. Téléchargez et installez Python à partir d' [ici](https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe) . A cette étape :

![Add Python to Path](images/Python_path.png "Ajouter Python au chemin")

**Assurez-vous de cocher "ajouter au PATH"** pendant le processus d'installation. **Si vous ne le faites pas** , vous devrez probablement demander de l'aide à votre support informatique local pour ajouter Python à votre chemin. En attendant le téléchargement, vous pouvez démarrer sur [Install Git et Télécharger A→Z+T](#install-git-and-download-azt) ci-dessous

**Assurez-vous de cliquer sur "supprimer la limitation de chemin"** après ce qui précède, pour éviter certains problèmes avec des noms de fichiers plus longs.

1. **Cela devrait être obsolète; sauter sauf si vous rencontrez des problèmes plus tard** : Ouvrez un terminal (appuyez sur la touche Windows puis tapez `cmd` dans la zone de recherche), et collez chacun d'entre eux (et appuyez sur Entrée) :
    - `python -m pip install --upgrade pip setuptools wheel`
    - `python -m pip install pyaudio`
    - `python -m pip install Pillow lxml` (non requis ; si vous obtenez une erreur ici, ignorez-la simplement)
    - `python -m pip install patiencediff` (non requis à partir de janvier 2022 ; si vous obtenez une erreur ici, ignorez-la simplement)

## Installez Git et téléchargez A→Z+T

### Installer Git ( [site Web](https://git-scm.com/download/win) )

1. Téléchargez et installez Git à partir d' [ici](https://github.com/git-for-windows/git/releases/download/v2.33.0.windows.2/Git-2.33.0.2-64-bit.exe)

### Télécharger A→Z+T

1. Sur votre bureau, cliquez avec le bouton droit de la souris sur `Git-Bash` pour obtenir un terminal (fenêtre noire).
2. Dans le terminal `Git-Bash` , collez `git clone https://github.com/kent-rasmussen/azt.git` et appuyez sur Entrée. Cela vous donnera un dossier `azt` sur votre bureau, où les fichiers du programme A→Z+T resteront.

## Polices

Si vous n'avez pas encore [Charis SIL](https://software.sil.org/charis/) sur votre système, téléchargez et installez la version la plus récente à partir d' [ici](https://software.sil.org/downloads/r/charis/CharisSIL-6.001.zip) .

## Configurer A→Z+T pour une utilisation normale

Once you have completed everything under [Install Python](#install-python) and [Install Git and Download A→Z+T](#install-git-and-download-azt):

1. Cliquez pour ouvrir le dossier `azt` sur votre bureau
2. **Faites un clic droit** sur `main.py` (il peut apparaître comme `main` sur votre système) et sélectionnez "Envoyer vers... Bureau (créer un raccourci)".
3. Cliquez sur le raccourci/lien pour exécuter A→Z+T (si vous n'obtenez rien d'autre qu'un scintillement noir, consultez [cette page](INSTALL_PROBLEMS.md) .)
4. **Célébrez votre accomplissement; vous avez fini d'installer A→Z+T !**
5. Lisez [USAGE](USAGE.md) pour savoir comment utiliser A→Z+T
6. Envoyez-moi des informations sur les [bogues](BUGS.md) que vous trouvez, afin que je puisse vous aider et améliorer le programme pour les autres.

## Étapes importantes supplémentaires pour tirer le meilleur parti de A→Z+T

### Installez Mercurial pour une meilleure collaboration

Téléchargez et installez [ce fichier](https://www.mercurial-scm.org/release/windows/Mercurial-6.0-x64.exe) .

### Praat

- Si vous utilisez Praat, assurez-vous que l'exécutable Praat se trouve dans le chemin de votre système d'exploitation. Vous devrez peut-être demander de l'aide à votre support informatique si vous ne savez pas comment faire (en gros, placez-le dans votre répertoire `Programs (?x86)` ).

### Soyez prêt à créer et à modifier des rapports

Installez le package XLingPaper complet à partir d' [ici](https://software.sil.org/downloads/r/xlingpaper/XLingPaper3-10-1XXEPersonalEditionFullSetup.exe) .

### Mettez à jour A→Z+T à partir du menu Aide, en supposant que vous avez suivi ces instructions.
