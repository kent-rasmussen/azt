# coding=UTF-8
"""The splash, rendered by a webview CHILD process. See `frontend/served.py`.

Run by the parent as `python -m frontend.served_splash --webview`; the
`--webview` is what makes `from frontend import ui` resolve to `ui_webview`
in this process, through the one selector that decides that question.

**RUNNABLE BY HAND**, which matters because the parent path is hard to
exercise deliberately:

    cd /home/kentr/bin/AZT/azt && echo '{"kind":"view","view":{"title":"A-Z+T","version":"Version: 1.15.21","updated":"updated to today","loading":"Your dictionary database is loading...","description":"A-Z+T accelerates community-based language development.","image":"transparent","progress":10}}' | ../env/bin/python -m frontend.served_splash --webview

A splash should appear. Then it waits on stdin, so Ctrl-D closes it.

WHY THE SPLASH FIRST. Kent, 2026-09-14: "How about we learn from the last
experience, and just serve the splash first, under this new paradigm?" — the
last experience being that starting the in-process port at the splash rather
than the chooser was what separated visibility from layout. It is the same
argument again, and the splash is unusually well suited to it: its view model
is six strings, an image name and an integer, with no live objects at all, and
`progress()` is the only update. So this exercises parent→child streaming and
the whole supervise/timeout/fall-back machinery with **no action protocol**.

The one interaction the Tk splash has — clicking the version line runs
`updateazt` — is deliberately NOT carried here yet. It needs child→parent
results, which is the next page's problem, and losing it costs a user nothing
they cannot get from the menu.
"""
import json
import sys

from frontend import served


def _say(kind, **fields):
    """One protocol line to the parent, on stdout."""
    try:
        sys.stdout.write(json.dumps(dict(kind=kind, **fields)) + '\n')
        sys.stdout.flush()
    except Exception:
        pass        # the parent is gone; nothing here can fix that


def _log(text):
    """A log line, on STDERR. The parent relays these into the log the
    visibility watchdogs are read from (ADR 0004), so nothing here opens the
    log file itself and two processes never interleave writes to it."""
    try:
        sys.stderr.write('{}\n'.format(text))
        sys.stderr.flush()
    except Exception:
        pass


def _read():
    """One message from the parent, or None at EOF."""
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line)
    except Exception:
        _log('unparseable line from parent: {!r}'.format(line[:200]))
        return {}


def build(view):
    """Render the splash from the view model. Returns (root, widgets).

    The layout mirrors `ui_shell.Splash` row for row, deliberately: this must
    look like the splash users know, and a row-for-row copy is the version
    that is obviously right or obviously wrong rather than subtly different.
    """
    from frontend import ui
    root = ui.Root()                    # no program: dummy.App stands in
    win = ui.Window(root, exit=0)
    f = win.frame
    widgets = {
        'title': ui.Label(f, text=view.get('title', ''), font='title',
                          anchor='c', padx=25, pady=10,
                          row=0, column=0, sticky='we'),
        'version': ui.Label(f, text=view.get('version', ''), anchor='c',
                            padx=25, row=1, column=0, sticky='we'),
        'updated': ui.Label(f, text=view.get('updated', ''), anchor='c',
                            padx=25, row=2, column=0, sticky='we'),
        'image': ui.Label(f, image=view.get('image', 'transparent'), text='',
                          row=3, column=0, sticky='we'),
        'loading': ui.Label(f, text=view.get('loading', ''), padx=50,
                            row=4, column=0, sticky='we'),
        'description': ui.Label(f, text=view.get('description', ''), padx=50,
                                font='italic', row=6, column=0, sticky='we'),
    }
    # No wraplength: the browser wraps to the cell. The Tk splash computes
    # `winfo_screenwidth()/2` for these two labels; that arithmetic is exactly
    # what does not cross the seam (ADR 0004 D3).
    widgets['progress'] = ui.Progressbar(f, orient='horizontal',
                                         mode='determinate',
                                         row=5, column=0)
    widgets['progress'].current(int(view.get('progress', 0) or 0))
    try:
        win.title(view.get('title', ''))
    except Exception as e:
        _log('could not set the title ({!r})'.format(e))
    return root, win, widgets


def apply(widgets, fields):
    """Apply an update. Unknown keys are logged, not ignored silently — a
    field the parent thinks it is sending and the child drops is the kind of
    gap that only shows up as 'the bar never moved'."""
    for key, value in (fields or {}).items():
        if key == 'progress':
            try:
                widgets['progress'].current(int(value or 0))
            except Exception as e:
                _log('progress {!r} rejected ({!r})'.format(value, e))
        elif key in widgets:
            try:
                widgets[key]['text'] = value
            except Exception as e:
                _log('{} text {!r} rejected ({!r})'.format(key, value, e))
        else:
            _log('no widget for updated field {!r}'.format(key))


def serve(root, win, widgets):
    """Announce readiness, then follow the parent until it says stop.

    Runs in the thread `mainloop(setup_callback=…)` provides, which fires
    once the page has LOADED — so `ready` means "the user can see it", not
    "the process started". The parent's whole fallback decision rests on that
    distinction.
    """
    # SIZE IT BEFORE SAYING READY. pywebview creates windows at a fixed
    # 800x600 and nothing relates that to their content, so the first served
    # splash came up with a scrollbar and its progress bar and description
    # below the fold (Kent, 2026-09-14: "ugly, but there"). `fit_to_content`
    # grows to fit and centres in one pass; it exists because the chooser had
    # the same problem in-process. Before `ready` because `ready` means "the
    # user can see it", and a window that is about to jump and resize is not
    # yet that.
    for step in ('fit_to_content', 'lift'):
        fn = getattr(win, step, None)
        if not callable(fn):
            _log('window has no {}()'.format(step))
            continue
        try:
            fn()
        except Exception as e:
            _log('{}() failed ({!r})'.format(step, e))
    _say(served.MSG_READY)
    while True:
        msg = _read()
        if msg is None:
            _log('parent closed the pipe; exiting')
            break
        kind = msg.get('kind')
        if kind == served.MSG_CLOSE:
            break
        elif kind == served.MSG_UPDATE:
            apply(widgets, msg.get('fields'))
        elif kind == served.MSG_VIEW:
            apply(widgets, msg.get('view'))     # a whole fresh view model
        else:
            _log('unknown message {!r}'.format(kind))
    _shut_down(root, win)


def _shut_down(root, win):
    """End this process, promptly and for certain.

    `Toplevel.destroy()` in the webview backend deliberately only HIDES the
    window — "reused, not rebuilt, and freeing a pywebview window at the
    wrong moment is what crashes Qt" — so it cannot end the event loop. With
    only that, the child stayed alive after being told to close and the
    parent killed it two seconds later, on every boot (Kent, 2026-09-14:
    "served splash: did not exit in 2s; killing").

    So: hide, ask pywebview to tear its own windows down, then `os._exit`.
    That is the right brutality HERE and nowhere else — this process exists
    to render one page, it has no unsaved state, and the alternative is
    contending with pywebview's teardown, which is precisely where the Qt
    garbage-collection crash lives. Streams are flushed first because
    `os._exit` skips that.
    """
    import os
    hide = getattr(win, 'withdraw', None)
    if callable(hide):
        try:
            hide()      # off screen first, so teardown is not watched
        except Exception as e:
            _log('withdraw failed ({!r})'.format(e))
    try:
        import webview
        for w in list(getattr(webview, 'windows', [])):
            try:
                w.destroy()
            except Exception as e:
                _log('pywebview window destroy failed ({!r})'.format(e))
    except Exception as e:
        _log('could not reach pywebview to tear down ({!r})'.format(e))
    _log('exiting')
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except Exception:
            pass
    os._exit(0)


def _route_logs_to_stderr():
    """Every log line in this process goes to STDERR, never to the log FILE.

    Two reasons, and both bite:

    * **The parent owns the file.** `logsetup` takes its runid from an
      inherited environment variable, so a child that installed a file
      handler would open the very same part files and roll against the
      parent — two writers on the log the visibility watchdogs are read
      from.
    * **Without this, INFO vanishes.** The child never runs main.py's log
      setup, so the root logger has no handler and Python falls back to
      `lastResort`: stderr, at WARNING and above. Every INFO line the child
      produces — including `display stack (pywebview … running)`, which is
      the whole point of having asked — would be dropped silently.

    The parent's stderr reader relays these into the one log
    (`served.ServedPage._read_stderr`), prefixed with the page name.
    """
    import logging
    root = logging.getLogger()
    # DON'T DOUBLE UP. logsetup already puts a console handler on stderr, so
    # adding a second unconditionally printed every child line twice — once
    # bare, once with name and level (Kent's log, 2026-09-14).
    have_stream = any(isinstance(h, logging.StreamHandler)
                      and not isinstance(h, logging.FileHandler)
                      for h in root.handlers)
    if not have_stream:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter('%(name)s: %(levelname)s: '
                                               '%(message)s'))
        root.addHandler(handler)
    # And never write the log FILE from here: logsetup's runid comes from an
    # inherited environment variable, so a file handler in this process would
    # open the parent's own part files and roll against them.
    for h in [h for h in root.handlers if isinstance(h, logging.FileHandler)]:
        root.removeHandler(h)
        log_only = getattr(h, 'baseFilename', '?')
        _log('detached this child from the log file {}'.format(log_only))
    root.setLevel(logging.INFO)


def main():
    _route_logs_to_stderr()     # BEFORE importing any module that logs
    first = _read()
    if not first or first.get('kind') != served.MSG_VIEW:
        _log('no view model on stdin (got {!r}); nothing to render'
             ''.format(first))
        return 2
    from frontend import backend
    if backend != 'webview':
        # Refuse rather than render a Tk splash in a child, which would be a
        # second Tk mainloop and no use to anyone.
        _log('this child resolved to the {!r} backend, not webview; pass '
             '--webview'.format(backend))
        return 3
    root, win, widgets = build(first.get('view') or {})
    root.mainloop(setup_callback=lambda: serve(root, win, widgets))
    return 0


if __name__ == '__main__':
    sys.exit(main())
