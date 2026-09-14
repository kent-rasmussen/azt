#!/usr/bin/env python3
# coding=UTF-8
"""What display stack is this process ACTUALLY on?

NO GUI DEPENDENCY — the invariant this module was created with, and it still
holds: import-time code is env vars only, "so both frontend and backend can
import it". `toolkit()` asks GDK or Qt only when they are ALREADY in
sys.modules, so asking the question never pulls a toolkit into a process that
was not using one.

USING_WAYLAND is the original reason the module exists. Under GNOME/Wayland
the Tk app runs through XWayland, where synchronous X round-trips
(update/update_idletasks) made while a window is transitioning (mapping a
dialog/popup, deiconify, -fullscreen toggle) can deadlock with mutter and
freeze the app. The central UI.update/update_idletasks override checks
USING_WAYLAND to skip those synchronous calls there (invisible on
X11/Windows, where users run). See docs/wayland_freeze_audit.md.

The rest of this module was added 2026-09-14 to answer a question that flag
cannot: WHICH stack each backend actually got. Kent, on my saying I did not
know whether pywebview-Qt was running under XWayland: "I'm astounded. I
thought the whole point of these changes was to NOT use XWayland. So if
you're not sure if we're using it or not, let's establish that now. and
document it in the logs, so we're clear going forward."

He is right that this should be readable off a log rather than reasoned about
from toolkit defaults. It bears directly on
`agenda/wayland_freeze_audit.md`: the alphabet chart takes 37-42s to build on
tkinter and ~0s on both webview engines, and whether that indicts XWayland or
merely Tk's round-trip volume depends on which of them share a stack.

TWO SOURCES, weaker then stronger:

  * **environment** — what the session advertises and what the toolkits were
    told. Available before any window exists, and it is what a toolkit will
    probably honour, not what it did.
  * **the toolkit** — GDK's display CLASS, Qt's platform name, Tk's server
    string. Authoritative, but only once it has a display open.

A THIRD SOURCE WAS TRIED AND REMOVED: reading which display socket the
process has open, from /proc. It cannot work, and the reason is worth keeping
so nobody rebuilds it — **a connected client socket has no path in
/proc/net/unix.** Only listening and bound sockets are named there, so a
client's end of the X11 or Wayland connection shows as an unnamed inode and
the scan reported "no display socket open yet" even with Tk fully up (Kent's
log, 2026-09-14). `lsof` has the same limitation for the same reason;
resolving a socket's peer needs the sock_diag netlink interface, which is
more machinery than this question is worth when the toolkit will simply say.

Never raises: this is a diagnostic, and a diagnostic that breaks startup costs
more than the answer is worth.
"""
import os
import sys

from utilities import logsetup
log = logsetup.getlog(__name__)
logsetup.setlevel('INFO', log)

# ── USING_WAYLAND: the original contents of this module ──────────────────
#
# Restored VERBATIM from git on 2026-09-14 after I overwrote this file without
# reading it first, which broke every tkinter run
# (`from utilities.display import USING_WAYLAND`, ui_tkinter.py:53). My
# reconstruction from the call sites also got the test wrong — it dropped
# `WAYLAND_DISPLAY`, which would have turned the update guard OFF on any
# machine where the session type is unset but a Wayland display is named.
# Nothing below is inferred; it is the committed code.
def using_wayland():
    return (os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'
            or bool(os.environ.get('WAYLAND_DISPLAY')))


USING_WAYLAND = using_wayland()

ENV_VARS = ('XDG_SESSION_TYPE', 'WAYLAND_DISPLAY', 'DISPLAY',
            'GDK_BACKEND', 'QT_QPA_PLATFORM', 'PYWEBVIEW_GUI')


def environment():
    """What the session advertises, and what the toolkits were told.

    A dict of the set variables only — an unset variable and an empty one mean
    different things to the toolkits, and printing `DISPLAY=` for "unset"
    would hide which we had.
    """
    return {k: os.environ[k] for k in ENV_VARS if k in os.environ}


def toolkit(which=None, widget=None):
    """What the toolkit itself says, or None if it cannot be asked.

    `which` is 'gtk', 'qt' or 'tk'; None asks whichever are already imported,
    so this never pulls in a toolkit that the run is not using — importing Qt
    to ask about GTK would be its own bug. `widget` is any live Tk widget,
    needed only for 'tk'.
    """
    if which == 'tk':
        # Tk 8.6 has no Wayland backend, so on a Wayland session it is
        # XWayland with no way to be otherwise. `winfo_server()` is asked
        # anyway, because it PROVES a connection exists rather than assuming
        # one, and its vendor/release string is worth having in the log.
        said = 'Tk: X11 only'
        try:
            if widget is not None:
                said += ' — server says {!r}'.format(widget.winfo_server())
        except Exception as e:
            said += ' — could not ask the server ({!r})'.format(e)
        return said     # the X11-vs-XWayland reading is verdict()'s job
    if which in (None, 'gtk'):
        # NEVER IMPORT Gdk HERE — read it only if something else already has.
        #
        # This asked `from gi.repository import Gdk` behind an `'gi' in
        # sys.modules` guard, which is not the same question: `gi` can be
        # loaded without `Gdk`, and an unversioned `Gdk` import defaults to
        # 4.0. On a Qt run that pulled GTK4's Gdk into a process that already
        # had GTK3's types registered, and the gi type system came apart —
        # "cannot register existing type 'GdkDisplay'", then a cascade of
        # g_type assertions, and no root window at all (Kent, 2026-09-14).
        # A diagnostic must not change what it measures, let alone break it.
        gdk = sys.modules.get('gi.repository.Gdk')
        if gdk is not None:
            try:
                d = gdk.Display.get_default()
                if d is not None:
                    # GdkWaylandDisplay / GdkX11Display — the class IS the
                    # answer.
                    return 'GTK: {}'.format(type(d).__name__)
            except Exception as e:
                log.log(3, "cannot ask GDK for its display (%s)", e)
    if which in (None, 'qt'):
        for mod in ('PyQt6.QtGui', 'PySide6.QtGui',
                    'PyQt5.QtGui', 'PySide2.QtGui'):
            if mod not in sys.modules:
                continue
            try:
                app = sys.modules[mod].QGuiApplication.instance()
                if app is not None:
                    # 'xcb' means XWayland on a Wayland session.
                    return 'Qt: platformName={}'.format(app.platformName())
            except Exception as e:
                log.log(3, "cannot ask %s for its platform (%s)", mod, e)
    return None


def verdict(said):
    """X11, Wayland or unknown, from what the toolkit answered.

    The toolkit's own words are the evidence; this is just the reading of
    them, kept separate so the log always carries both.
    """
    if not said:
        return 'stack UNKNOWN — no toolkit has a display yet'
    # SUBSTRINGS, case-insensitive, because the class names are not
    # consistent: GDK's Wayland display arrives as `GdkWaylandDisplay` but
    # its X11 one as plain `X11Display` (different introspection
    # namespaces). Matching the full names missed the X11 case and reported
    # "toolkit answered something unrecognised" on a run that had correctly
    # been forced onto X11 (Kent, 2026-09-14).
    low = said.lower()
    if 'wayland' in low:
        return '=> NATIVE WAYLAND, no X server involved'
    if 'x11' in low or 'xcb' in low:
        return '=> XWAYLAND' if USING_WAYLAND else '=> X11 (no Wayland session)'
    return 'stack UNKNOWN — toolkit answered {!r}'.format(said)


def describe(which=None, widget=None):
    """One log line: the environment, the toolkit's answer, and the reading of
    it. Weakest evidence first, so the last term is the one to believe."""
    env = environment()
    said = toolkit(which, widget)
    bits = ['env ' + (' '.join('{}={}'.format(k, v)
                               for k, v in env.items()) or '(none set)')]
    if said:
        bits.append(said)
    bits.append(verdict(said))
    return ' | '.join(bits)


def report(where, which=None, widget=None):
    """Log the line. `where` names the moment, because the answer changes: no
    toolkit has a display before the GUI starts, so a pre-GUI call reports
    intent and a post-GUI call reports fact."""
    try:
        log.info("display stack (%s): %s", where, describe(which, widget))
    except Exception as e:
        log.info("display stack (%s): could not be determined (%r)", where, e)
