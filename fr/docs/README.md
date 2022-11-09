<a href="https://gitlocalize.com/repo/7965/fr?utm_source=badge"> <img src="https://gitlocalize.com/repo/7965/fr/badge.svg"> </a> <a href="fr/README.md">Français</a>

## Installation la plus simple sur [MS Windows](SIMPLEINSTALL.md) ou [Linux](SIMPLEINSTALL_LINUX.md)

## Si vous souhaitez l'aide d'un consultant, voir également [cette page](HELP_PREREQUISITES.md)

# A→Z+T ![CV](../images/AZT%20stacks6_icon.png "AZT")

[A→Z+T](https://github.com/kent-rasmussen/azt) is designed to accelerate community-based language development, supplemented by (not as a replacement for) formal linguistic training. It does this by systematically checking a dictionary (and thus a writing system), with respect to consonants, vowels, and tone.

Vous pouvez collecter une liste de mots à partir de zéro dans [A→Z+T](https://github.com/kent-rasmussen/azt) , si vous n'en avez pas déjà créé ailleurs, mais l'analyse des racines est toujours en développement, donc pour l'instant vous devriez le faire ailleurs (par exemple, [FLEx](https://software.sil.org/fieldworks/) ou [WeSay](https://software.sil.org/wesay/) ) si votre les formes de citation ont l'apposition obligatoire.

Le travail [A→Z+T](https://github.com/kent-rasmussen/azt) aboutit à une base de données lexicales qui est vérifiée, sauvegardée avec des fichiers sonores et stockée sous [LIFT](https://code.google.com/archive/p/lift-standard/), un format XML ouvert et conçu pour le partage de données lexicales. Cette base de données doit donc être compatible avec d'autres outils capables de lire [LIFT](https://code.google.com/archive/p/lift-standard/), par exemple [WeSay](https://software.sil.org/wesay/) et [FLEx](https://software.sil.org/fieldworks/) .

## If you currently use FLEx, and want to understand what A→Z+T is and decide if you should use it, please see [this page](OWL_GUIDE.md).

<!-- It is designed to *supplement* (not replace) formal training, on the one hand, and *facilitate* a particular kind of language development on the other, so it may not do what you want —it certainly does not do everything. If you want to get as many people involved in the development of their own language as possible, in a manner that results in a checked lexical database backed up by sound files, then this tool is for you. -->

## Pourquoi

Voir [JUSTIFICATION](RATIONALE.md) pour plus d'informations sur pourquoi on devrait utiliser cet outil ; voir [Pourquoi travailler avec des ordinateurs](WHYCOMPUTERS.md) pour voir [A→Z+T](https://github.com/kent-rasmussen/azt) par rapport aux méthodes participatives carte et crayon. Voir [Pourquoi travailler avec des communautés](WHYCOMMUNITIES.md) pour voir [A→Z+T](https://github.com/kent-rasmussen/azt) par rapport aux méthodes plus traditionnelles

## Quoi

[A→Z+T](https://github.com/kent-rasmussen/azt) est écrit en [Python](https://python.org) (3+) et [Tkinter](https://docs.python.org/3/library/tkinter.html) , avec [PyAudio](https://pypi.org/project/PyAudio/) pour l'enregistrement et la lecture de fichiers audio. [A→Z+T](https://github.com/kent-rasmussen/azt) produit des rapports à l'écran, des fichiers en texte brut et des documents [XLingPaper](https://software.sil.org/xlingpaper/) XML, qui peuvent à leur tour être facilement convertis en PDF et HTML, chacun avec des liens cliquables vers des fichiers audio.

## Comment

Pour obtenir le programme, exécutez `git clone https://github.com/kent-rasmussen/azt.git` dans un terminal, ou téléchargez via le bouton de `code` vert sur la page principale.

Pour exécuter : `python main.py` (ou `python3 main.py` , selon la version (3+) de python sur votre système)

Voir [INSTALLER](INSTALL.md) pour plus d'aide sur l'installation ; voir [UTILISATION](USAGE.md) pour savoir comment utiliser cet outil.

Voir [CHANGELOG](CHANGELOG.md) pour voir les fonctionnalités par version, et [ROADMAP](ROADMAP.md) pour voir ce sur quoi je travaille ensuite.

## bogues

Voir [BOGUES](BUGS.md) pour les informations à m'envoyer si vous rencontrez des problèmes ; voir [PROBLÈMES CONNUS](KNOWNISSUES.md) avec des solutions de contournement recommandées pour quelques problèmes connus.
