<a href="https://gitlocalize.com/repo/7965/fr?utm_source=badge"></a><img src="https://gitlocalize.com/repo/7965/fr/badge.svg"> <a href="../README.md">Read this page in English</a>

## [Je veux commencer à utiliser A→Z+T et obtenir l'aide d'un conseiller](HELP_PREREQUISITES.md)

## Pour automatiser au maximum sur MS Windows, téléchargez et exécutez [ce fichier](RunMetoInstall.bat?raw=true) en tant qu'administrateur

## ou consultez [cette page](SIMPLEINSTALL.md) pour des instructions d'installation simples

## Si vous utilisez actuellement FLEx et souhaitez comprendre ce qu'est A→Z+T, consultez [cette page](OWL_GUIDE.md) .

# A→Z+T ![CV](images/AZT%20stacks6_icon.png "AZT")

[A→Z+T](https://github.com/kent-rasmussen/azt) est conçu pour accélérer le développement linguistique communautaire, complété par (et non en remplacement de) une formation linguistique formelle. Pour ce faire, il vérifie systématiquement un dictionnaire (et donc un système d'écriture), en se concentrant initialement sur la collecte de données pour les langues tonales. Des fonctionnalités supplémentaires sont encore en développement. Le travail [A→Z+T](https://github.com/kent-rasmussen/azt) aboutit à une base de données lexicale vérifiée sauvegardée avec des enregistrements, qui peuvent tous être visualisés et modifiés dans [WeSay](https://software.sil.org/wesay/) ou importés dans [FLEx](https://software.sil.org/fieldworks/) .

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
