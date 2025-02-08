# Known Issues

## Microsoft Windows Specific Issues

### Window Scaling
Some MS Windows installations have the display scaling set as high as 175% (that I have seen). While this is a matter of personal preference, note that this changes the calculation for window sizes, and this information is not available to python (in my knowledge, at least). So you will probably have a much better experience if you reduce this scaling to 100% while using [A-Z+T].

### Soft Keyboard Usage
N.B.ː this is fixed, at least on my computer. If you have problems with soft keyboard input, please write meǃ
I don't understand why, but on at least some MS Windows installs, soft keyboards (e.g., Tevaultesoft Keyman, or MSKLC keyboards) don't seem to play well with tkinter input, resulting in '?' in place of characters that should result from multiple keystrokes. This is not a large issue for [A-Z+T], which does not heavily rely on keyboard input. However, there are times (e.g., when defining frames), where one aught to be able to type characters as appropriate for the language. As a workaround, I recommend typing into a text editor, then copying and pasting into [A-Z+T].  

[A-Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[CAWL]: http://www.comparalex.org/resources/SIL%20Comparative%20African%20Word%20List.pdf
