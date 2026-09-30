#!/usr/bin/env python3
# coding=UTF-8
"""`--help`: the list of command-line switches, and what they do.

THIS IS A HAND-WRITTEN LIST, NOT A PARSER. The app has no `argparse` and no
parser of any other kind: every switch is an independent membership test
against `sys.argv`, made by whichever module cares, wherever it cares —
`utilities.ui_backend`, `frontend.ui_webview._switch`, `main.py`,
`utilities.duplicates`. Nothing checks the command line as a whole.

Two consequences the help text says out loud, because a user who assumes
argparse will be wrong about both:

  * **An unrecognised switch is ignored, not refused.** A typo does nothing
    and says nothing. There is no "unrecognized arguments" error to warn you.
  * **Order and combination are not validated.** `--tkinter --webview`
    together is not an error; whichever test runs first decides.

Keeping it a list rather than adopting argparse is deliberate. Several
switches are passed THROUGH rather than consumed — `--restart` is appended by
the restart path itself (`utilities.utilities`), `--no-install` is read during
the venv bootstrap before most of the app exists, and the test harnesses set
their own argv — so a parser that rejected unknown arguments would break
callers that are working today. `utilities.ui_backend` notes the same
property: the app "only logs" argv, "so an unrecognised flag is ignored".

SO THIS FILE CAN GO STALE, and that is the one cost of the approach. It is
stdlib-only and imported before anything heavy, so `--help` answers instantly
and without building a venv; the price is that adding a switch means adding a
line here. `tests/test_switches_documented.py` is what stops that being
forgotten: it reads the switches out of the source and fails when one is
missing from this list.

Written 2026-09-30, from the inventory in the code. It replaces a block in
`azt/CLAUDE.md` which was the only list that existed, was not visible to
users at all, and had drifted — it was missing `--no-window-focus`,
`--gtk-theme=`, `--no-install` and `--restart`.
"""
import sys

# (switch, argument or None, one-line description)
# Grouped for reading; the groups are only headings in the output.
SWITCHES = [
    ("Which interface", [
        ('--tkinter', None,
         "Use the tkinter interface. This is the current default."),
        ('--webview', None,
         "Use the webview interface. Needs pywebview and a host toolkit "
         "this python can see; if either is missing it says why and falls "
         "back to tkinter."),
        ('--engine=', 'NAME',
         "Which webview engine: gtk, qt, cef, edgechromium or mshtml. "
         "Only relevant for Linux, which has a real choice between gtk and qt."),
        ]),
    ("Running it", [
        ('--user', None,
         "Run a development copy the way a user's copy runs: real error "
         "screens, log zipping on, no test file and no auto-opened task. "
         "Otherwise a checkout inside a folder called AZT gets developer "
         "settings, and this switch is the only way to opt out."),
        ('--no-splash', None,
         "Skip the splash screen. Useful when it is in the way."),
        ('--no-install', None,
         "Never install anything and never touch the network. A missing "
         "dependency is reported instead of fetched."),
        ('--restart', None,
         "Marks a process the app started to replace itself. Added "
         "automatically; you do not type it."),
        ]),
    ("Webview windows", [
        ('--no-kiosk', None,
         "Do not make task windows fullscreen. Fullscreen is intended — it "
         "keeps the work free of distractions — so this is for looking at "
         "layout problems."),
        ('--no-page-wait', None,
         "Show the shared Please Wait dialog over a fullscreen page, "
         "instead of the page showing its own."),
        ('--console', None,
         "Open the developer console. Off unless asked for, by anything. "
         "Known to crash the qt engine; honoured there anyway, with a "
         "warning."),
        ('--no-window-focus', None,
         "Create windows without taking focus, where the toolkit allows it."),
        ('--webview-hidden', None,
         "Create windows hidden and show them afterwards. KNOWN BROKEN on "
         "WebKitGTK: the windows are created and every show is requested, "
         "and nothing appears."),
        ('--window-size=', 'WxH',
         "Create windows at this size instead of the default, e.g. 640x480."),
        ('--keep-window-size', None,
         "Put a window's size back when the compositor changes it. The app "
         "no longer argues with that by default; the page scrolls instead."),
        ('--no-frame-inset', None,
         "Size windows in client units rather than frame units. For "
         "measuring against the frame-inset fix."),
        ('--dmabuf', None,
         "Turn WebKitGTK's accelerated buffer handoff back on. Off by "
         "default because it intermittently draws the window in diagonal "
         "black bands."),
        ]),
    ("Which display stack, and theme", [
        ('--gdk-backend=', 'wayland|x11',
         "Force the GTK engine's transport. Separates 'which toolkit' from "
         "'which display server'."),
        ('--qt-platform=', 'wayland|xcb',
         "The same for the qt engine."),
        ('--gtk-theme=', 'NAME',
         "Force a GTK theme, to test whether a theme is causing flicker."),
        ]),
    ("Diagnostics", [
        ('--log-resizes', None,
         "Log every resize sample with the window's frame and client boxes. "
         "One line per frame of a drag."),
        ('--log-heights', None,
         "Log the ancestor chain of every scroller on a page, to find where "
         "a height stopped propagating."),
        ]),
    ]

_PREAMBLE = """A-Z+T — dictionary and orthography checker.

    python main.py [switches]

THIS IS A LIST, NOT A PARSER. A-Z+T does not parse its command line: each
switch below is checked for independently by the part of the program that
cares about it. So:

  * a switch it does not know is IGNORED, not refused — a typo does nothing
    and says nothing;
  * switches that contradict each other are not an error;
  * there are no short forms, and no `--switch value` — a switch that takes
    a value is written `--switch=value`.
"""

_CLOSING = """Run with no switches for the normal interface.
"""


def help_text():
    """The whole `--help` output, as one string."""
    out = [_PREAMBLE]
    for heading, rows in SWITCHES:
        out.append('{}:'.format(heading))
        for switch, arg, description in rows:
            name = switch + (arg or '')
            # Wrap the description under a fixed-width name column, by hand:
            # textwrap is stdlib but this runs before anything else and the
            # shape is simple enough to keep obvious.
            words, line, lines = description.split(), '', []
            for w in words:
                if len(line) + len(w) + 1 > 52:
                    lines.append(line)
                    line = w
                else:
                    line = (line + ' ' + w).strip()
            lines.append(line)
            out.append('  {:<24}{}'.format(name, lines[0]))
            for extra in lines[1:]:
                out.append('  {:<24}{}'.format('', extra))
        out.append('')
    out.append(_CLOSING)
    return '\n'.join(out)


def names():
    """Every documented switch name, without its `=` or argument.

    For `tests/test_switches_documented.py`, which compares this against the
    switches the source actually tests for."""
    return {switch.rstrip('=') for _, rows in SWITCHES for switch, _a, _d in rows}


def maybe_help(argv=None):
    """Print the switches and exit, if asked. Otherwise do nothing.

    CALLED BEFORE ANYTHING HEAVY — before the duplicate gate and before
    `utilities.py_modules`, which builds the venv and can install packages.
    Asking a program what its switches are should not cost a venv, and must
    work on a machine where the dependencies are not there yet."""
    argv = sys.argv if argv is None else argv
    if '--help' in argv or '-h' in argv:
        print(help_text())
        sys.exit(0)
