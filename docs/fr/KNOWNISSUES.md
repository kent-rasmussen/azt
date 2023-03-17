# Problèmes connus

## Problèmes spécifiques à Microsoft Windows

### Mise à l'échelle de la fenêtre

Certaines installations MS Windows ont une mise à l'échelle de l'affichage réglée jusqu'à 175% (que j'ai vu). Bien que ce soit une question de préférence personnelle, notez que cela modifie le calcul des tailles de fenêtre et que cette information n'est pas disponible pour python (à ma connaissance, du moins). Vous aurez donc probablement une bien meilleure expérience si vous réduisez cette mise à l'échelle à 100 % tout en utilisant A-Z+T.

### Utilisation du clavier logiciel

Je ne comprends pas pourquoi, mais sur au moins certaines installations MS Windows, les claviers logiciels (par exemple, Tevaultesoft Keyman ou les claviers MSKLC) ne semblent pas bien jouer avec l'entrée tkinter, ce qui entraîne '?' à la place des caractères qui devraient résulter de plusieurs frappes. Ce n'est pas un gros problème pour A-Z+T, qui ne dépend pas beaucoup de la saisie au clavier. Cependant, il y a des moments (par exemple, lors de la définition de cadres), où l'on peut être capable de taper des caractères appropriés pour la langue. Comme solution de contournement, je recommande de taper dans un éditeur de texte, puis de copier et coller dans A-Z+T.
