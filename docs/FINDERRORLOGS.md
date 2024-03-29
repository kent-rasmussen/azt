# Find your Error Logs

## [A-Z+T] Log types
[A-Z+T] creates two kinds of logs:
- Each time you **run** [A-Z+T], it logs information for that **run** to a file named `log_<date>.text`, where <date> is Year-Month-Day, e.g., "log_2021-10-05.txt" for a file created on October 5, 2021.
  This is overwritten each time A-Z+T runs on that day, so if you need to keep it, e.g., to send it to me, to report behavior that did not cause an exception (below), **rename it before starting [A-Z+T] again**.
- Each time [A-Z+T] has an **exception** (a serious problem with the program, which causes it to exit, not just unexpected behavior), it will compress the above log and name it `log_<dateTime>.xz`, where <dateTime> is Year-Month-DayTHour-Minute-Second, e.g., "log_2021-09-25T11-49-27Z.xz" for a file made on September 25, 2021, at 11:49:27. This enables A-Z+T to easily save the log of each exception, as compressed text files ready to [Email to me](BUGS.md). Any time you get one of these, please send it to me; this is the best way I can help you get moving again when you have a problem.

## Finding the [A-Z+T] logs (search for "userlogs" folder)
The trickiest part of getting me the information I need to help you is finding where your system is putting [A-Z+T] logs.
They should be going into your working directory, which means the directory from which you launched python.
If you launch python via clicking a link to main.py, the location of your logs may depend on how your operating system is configured. I recommend

- Looking in the same directory/folder as main.py (i.e., the [A-Z+T] repository copy on your computer)
- Looking in that repository's parent (the directory/folder which contains that directory/folder), or somewhere else.
- Searching for the files by filename (e.g., "log_2021-"), using your operating system search tools.

  In any case, they should now all be found in a "userlogs" folder, so they don't clutter and are easier to find.

## I Really Have no Logs
If you think you really have no logs whatsoever, this indicates a very serious problem in starting up [A-Z+T], where it crashes before the logs initialize. Most cases that cause this should already be avoided, but here is a proceedure to get some error messaging from [A-Z+T] without finding a log:

- Open a command terminal (`⊞ win+R`/search then type 'cmd' in Windows).
- type your python executable name (e.g., python3, python, Python.exe, it may take some experimentation to figure this out), then
- type `<space>` and the path to main.py in the azt folder (e.g., C:\Users\<Your Name>\Desktop\azt\main.py), then
- hit `<Enter>`.

This should run [A-Z+T]  with a terminal window that should stay open even after a crash.
- Trigger the crash (e.g., wait, if it is crashing on startup)
- copy all the text from the terminal
- paste the text into [an email to me](BUGS.md).

[A-Z+T]:  https://github.com/kent-rasmussen/azt
[WeSay]:  https://software.sil.org/wesay/
[FLEx]: https://software.sil.org/fieldworks/
[LIFT]: https://code.google.com/archive/p/lift-standard/
[CAWL]: http://www.comparalex.org/resources/SIL%20Comparative%20African%20Word%20List.pdf
