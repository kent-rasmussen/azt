<a href="fr/COLLABORATION_AND_BACKUP.md">Français</a>
# Collaboration and Data Backup

As described in the [usage page](USAGE.md#collaboration-and-archival), being able to store and share data is critical to any serious research project. This page orients you to the way [A→Z+T] can help you do that.

## Normal usage
Each time [A→Z+T] opens and closes, it attempts to store changes in a repository (the folder with your [LIFT] file), as well as send and receive between that repository and one or more on attached media (USB drives).

If it finds a drive with a repository it has used before, it will do that send/receive out of view of the user.

## Reminders
If USB backup is known but not connected at open/close, [A→Z+T] notifies the user so a drive can be plugged in for the send/receive (once per open or close).

If the project has never been used with USB backup before, the user will get just one message each time [A→Z+T] opens. I trust that this minimal engagement will not be burdensome for those who have decided against backing up their data, for whatever reason.

## Copy to a USB drive
Any time [A→Z+T] doesn't find a USB drive attached, the message window contains a button allowing the user to copy the data repository to a new USB drive. Click the button, then tell [A→Z+T] where to put the new repository folder copy (e.g., select a USB drive).

If you use a USB drive normally, but want to make another, just unplug the first while [A→Z+T] is opening or closing, and this menu will appear.

## Start a project from a USB drive
When the user selects to change databases (or on [A→Z+T]'s first boot), one option is "Copy work from a USB drive". When selected, [A→Z+T] will ask where the repository is found (in which folder, on which drive), then copy that repository to your home folder for future use.

[A→Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[Praat]: https://www.fon.hum.uva.nl/praat/
