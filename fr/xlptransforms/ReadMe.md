Les transformations XSL et les DTD de ce dossier proviennent de https://github.com/sillsdev/XLingPap, récupérées le 1er septembre 2021 et depuis. Bien que ce site ne soit pas accompagné d'une licence, il renvoie à software.sil.org/xlingpaper/, qui contient dans son pied de page le texte :

`This software is free to use, modify and redistribute according to the terms of the MIT License`

Ce texte contient un lien vers https://en.wikipedia.org/wiki/MIT_License, qui sous "Conditions de la licence" contient le passe-partout suivant :

Copyright (c) `<year> <copyright holders>`

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

J'ai en outre clarifié avec l'auteur que j'ai la permission de modifier et de redistribuer ce matériel avec ce référentiel plus large.

Les modifications que j'ai apportées jusqu'à présent se limitent à l'implémentation de la fonction nodeset exslt.org, en

- Ajout `xmlns:exsl="http://exslt.org/common"` à la déclaration d'ouverture
- Conversion de fragments d'arbre de résultats XSLT 1.0 comme - select="$childDoc/root/node()" en ensembles de nœuds comme - select="exsl:node-set($childDoc)/root/node()"

Search for ($[^],/=") []+)([/[]+) replace with exsl:node-set(\1)\2 inside normalize-space() is OK There were a few cases requiring more manual work… but mostly incorporated

XLingPapPublisherStylesheetXeLaTeX.xsl XLingPapXeLaTeXCommon.xsl XLingPapPublisherStylesheetXeLaTeXContents.xsl XLingPapPublisherStylesheetCommon.xsl /home/kentr/IT/azt/repo_stable/xlptransforms/XLingPapXeLaTeX1.xsl /home/kentr/IT/azt/repo_stable/xlptransforms/XLingPapRemoveAnyContent.xsl /home/kentr/IT/azt/repo_stable/xlptransforms/XLingPapPublisherStylesheetCommonContents.xsl /home/kentr/IT/azt/repo_stable/xlptransforms/XLingPapCommon.xsl /home/kentr/IT/azt/repo_stable/xlptransforms/XLingPapCannedCommon.xsl /home/kentr/IT/azt/repo_stable/xlptransforms/XLingPapPublisherStylesheetXeLaTeXReferences.xsl /home/kentr/IT/azt/repo_stable/xlptransforms/XLingPapPublisherStylesheetXeLaTeXBookmarks.xsl
