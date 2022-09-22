# Lisez-moi des traductions

<!-- Two spaces at the end of a line gives a linebreak, but three ticks (```) -->

<!-- gives better overall format, with shading -->

En raison de la façon dont nous effectuons les traductions (dans les limites de Python), il y a quelques points auxquels nous devrions tous prêter attention :

- Il ne semble pas y avoir de différence dans l'utilisation de la syntaxe `_("").format()` ou de la syntaxe `_("".format())`

- La meilleure pratique peut être de mettre un mot-clé sémantiquement utile pour chaque variable, comme ceci :

    ```
    ```
    _("{name} Dictionary and Orthography Checker").format(name=self.program['name'])
    ```
    ```

- Sinon, il ne semble pas y avoir de moyen d'intégrer les éléments de format dans la traduction, nous sommes donc coincés, espérons-le, à comprendre plus ou moins ce que signifie chaque `{}` .

- Les formats suivants fonctionnent :

    - chaîne formatée sur une ligne :

        ```
        _("Language with code [{}]").format(xyz)
        ```

    - chaînes formatées, avec format en ligne après référence

        ```
        _("{} doesn't look like a well formed lift file; please "
        "try again.").format(filename)`
        ```

    - chaînes formatées avec plusieurs références au même élément de format, donné à la fin

        ```
        _("Your regular expressions look OK for {0} (there are "
        "no segments in your {0} data that are not in a regex). "
        "Note, this doesn't \nsay anything about digraphs or "
        "complex segments which should be counted as a single "
        "segment --those may not be covered by \n"
        "your regexes.".format(lang))`
        ```
