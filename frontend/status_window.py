# coding=UTF-8
"""The ONE status window (Kent 2026-07-29).

`notify_user(text)` APPENDS a message to a single window for the whole session,
instead of building a new Toplevel per message the way `ErrorNotice` does.
`ErrorNotice` stays exactly as it is for the notices that SHOULD block —
boot warnings, decisions, hard failures. Everything merely worth saying comes
here.

Why appending rather than a new window each time: every `ErrorNotice` is a fresh
Toplevel that **withdraws its parent**, builds, sets `-topmost`, deiconifies,
runs a synchronous `update_idletasks()`, optionally `wait_window()`s, then
deiconifies the parent again. That withdraw/deiconify cycle around a synchronous
paint is what costs ~a second per message on a field machine, and under XWayland
it is the shape that wedges. So this window:

  - is created ONCE per session, lazily, on the first message;
  - never touches the parent window;
  - never sets `-topmost`, never grabs, never waits;
  - is parented to the app ROOT, not to a task — so it outlives the task that
    happened to speak first, instead of dying with it and being rebuilt.

The one exception Kent named: if the window has been KILLED (the user closed
it), the next message may draw it again — and that one becomes the live one.
That is also the ONLY way messages are cleared: they accumulate for the whole
session, and Close is the deliberate act that ends the list (Kent 2026-08-25).
"""
from utilities.i18n import _
from utilities import logsetup
log = logsetup.getlog(__name__)
from frontend import ui

_window = None  # the ONE status window for this session (may be dead)


class StatusWindow(ui.Window):
    """Append-only message list, NEWEST FIRST.

    Newest-first is done by gridding each message at a DESCENDING row number
    (empty rows collapse to nothing in Tk), so the message that just arrived is
    at the top of the content and visible with no scrolling — without re-laying
    out the messages already there, and without fighting the scroll canvas for
    its position. That keeps the per-message cost to one Label."""
    FIRST_ROW = 9999      # counts DOWN from here; also the message cap
    # AMBIENT: not a work surface. TaskDressing.guardvisible asks "is anything
    # viewable?" before warning that every window is hidden, and it counts the
    # app root plus ALL of the root's children — which includes this window,
    # parented to the root and (by design) left open for the whole session. So
    # from the first notify onward the guard found this and returned silently:
    # no NO WINDOW line ever appeared, through the entire 2026-08 hunt, even
    # when the user was looking at no window at all (Kent 2026-08-27). A wait
    # dialog or a real modal SHOULD suppress the guard — the user is being told
    # something is happening. A message list the user can neither work in nor
    # dismiss the problem from should not.
    guard_ambient = True
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title=_("Messages"), exit=False,
                        withdrawn=True)
        if hasattr(self, 'theme'):
            self['background'] = self.theme.background
        self.scroll = ui.ScrollingFrame(self.frame, row=0, column=0,
                                        sticky='nsew')
        # This window is not a fullscreen kiosk page, so the scroll viewport must
        # size to THIS WINDOW rather than to the screen — see _fill_parent in
        # ScrollingFrame._do_configure_interior.
        self.scroll._fill_parent = True
        # Theme the CANVAS. Filling the parent means the canvas is now taller than
        # its content, so the empty area below the messages is visible for the
        # first time — and it came up black, because nothing had ever needed to
        # paint it (Kent 2026-08-25). Before _fill_parent the canvas was exactly
        # content-height, so none of it ever showed.
        try:
            self.scroll.canvas['background'] = self.theme.background
            self.scroll.canvas['highlightthickness'] = 0
        except Exception as e:
            log.info("status window canvas theming failed: %s", e)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        # Let the content FILL the window. `Window.post_tk_init` centers the
        # r=c=1 frame by giving rows/columns 0 and 2 weight=3 and row 1 none — so
        # without this the messages sit in a small block in the MIDDLE of a
        # resized window (Kent 2026-08-25) instead of using it. Same override
        # build_verify_layout does for the kiosk pages.
        try:
            self.grid_rowconfigure(1, weight=1)
            self.grid_columnconfigure(1, weight=1)
        except Exception as e:
            log.info("status window fill-weights failed: %s", e)
        # SIZE IT (Kent 2026-08-25). ScrollingFrame sets grid_propagate(0), so it
        # never grows to fit its content — with no geometry the window shrank to
        # about one line, and every message after the first looked like it had
        # OVERWRITTEN the last. The messages were always there; there was just
        # nowhere to scroll to. Big enough to read a session's worth, short of
        # fullscreen: this window must never cover the work.
        self._width = int(self.winfo_screenwidth() * 0.55)
        try:
            self.geometry('{}x{}'.format(self._width,
                                        int(self.winfo_screenheight() * 0.6)))
        except Exception as e:
            log.info("status window geometry failed: %s", e)
        # Re-wrap on resize: wraplength is fixed per Label at creation, so without
        # this a window made wider keeps the old messages at the old width.
        self.bind('<Configure>', self._on_resize, add='+')
        # A manual Close is still not REQUIRED: messages accumulate for
        # the session, and closing is the only thing that clears them (the next
        # message then opens a fresh window). exit=False means there is no Exit
        # button, so without this the user is obliged to us the OS window dressing,
        # which we assume he is more than competent to do.
        # ui.Button(self.frame, text=_("Close"), cmd=self.on_quit,
        #          font='instructions', row=1, column=0, sticky='e')
        self._row = self.FIRST_ROW
        self._surface() # once, for the first message — not per message
        # The first message is wrapped from the width we ASKED for, since nothing
        # is mapped yet. Re-wrap once the window is actually on screen, so the
        # user doesn't have to resize it by hand to make the first notice legible.
        self.after(120, self._rewrap)
    def _surface(self):
        """Bring the window to the front WITHOUT holding it there.

        The app's pages are FULLSCREEN kiosk windows (`Window.takekioskscreen`), so
        a plain new toplevel is created BEHIND them and is simply invisible — which
        is why the first notices "weren't appearing" at all (Kent 2026-07-30).
        `ErrorNotice` sets `-topmost` for exactly this reason. A status window that
        STAYS on top would cover the work, so pulse it: raise, then release. Still
        no grab and no wait — it must never block.

        NO lift(): `-topmost` below already raises the window, so lift() was a
        SECOND window-manager round trip for the same effect — and it is the one
        that hung, blocked in `tkraise` while being called from this window's own
        constructor (Kent's faulthandler dump, 2026-08-25). Raising a window is a
        WM round trip, and under XWayland those are exactly the calls that wedge;
        see azt/agenda/wayland_freeze_audit.md. One call, and it is the one that
        also makes the window visible over a fullscreen kiosk page."""
        try:
            if not self.winfo_viewable():
                self.deiconify()
            self.attributes('-topmost', True)
            self.after(1200, self._release_topmost)
        except Exception as e:
            log.info("status window surface failed: %s", e)
    def _wraplength(self):
        """Wrap to THIS WINDOW's width, not the screen's.

        `Label.wrap()` sizes from `availablexy()`, i.e. screen width minus
        siblings — right for a fullscreen kiosk page, wrong here: messages wrapped
        at nearly screen width and the overflow was simply clipped, since there is
        no horizontal scrollbar (Kent 2026-08-26). Exactly the vertical bug that
        `_fill_parent` fixed, one axis over.

        MEASURE ONLY WHEN MAPPED. Before the window is on screen, winfo_width()
        does not report the geometry we asked for — a ScrollingFrame carries
        grid_propagate(0) and sits at some small default, so the FIRST message
        was wrapping to a fraction of the eventual width and only came right when
        the window was resized by hand (Kent 2026-08-27). The width we asked for
        is the better estimate until reality is available.

        THE WINDOW FIRST, AND 120px IS NOT A PLAUSIBLE WIDTH. This asked
        `self.scroll` before `self`, which is backwards: the ScrollingFrame is
        the one widget here carrying grid_propagate(0), so it is exactly the
        thing that sits at a small default, while the window's own width comes
        from the geometry we asked for. And the `> 120` floor accepted that
        default as reality — ~140px passes, returns 100, and the first message
        wrapped to one word per line (Kent 2026-09-03, twice). A Messages window
        is never legitimately narrower than a few hundred pixels, so anything
        that small is a default being misread as a measurement."""
        try:
            if self.winfo_ismapped():
                for w in (self.winfo_width(), self.scroll.winfo_width()):
                    if w and w > 400:
                        return w - 40 # scrollbar + a little breathing room
        except Exception as e:
            log.info("status window width probe failed: %s", e)
        return max(200, self._width - 40)
    def _on_resize(self, event=None):
        if event is not None and getattr(event, 'widget', None) is not self:
            return
        size = (self.winfo_width(), self.winfo_height())
        if size == getattr(self, '_last_size', None):
            return # our own geometry changes re-fire this; don't loop
        self._last_size = size
        job = getattr(self, '_rewrap_job', None)
        if job:
            try:
                self.after_cancel(job)
            except Exception:
                pass
        self._rewrap_job = self.after(200, self._rewrap)
    def _rewrap(self):
        """Re-wrap every message to the new width. Debounced by _on_resize: a
        drag-resize is a stream of Configures and this touches every Label."""
        self._rewrap_job = None
        if not self.winfo_exists():
            return
        n = self._wraplength()
        try:
            for w in self.scroll.content.winfo_children():
                try:
                    # Directly, NOT via wrap() — see the note in add(). wrap()
                    # takes min(wraplength, maxwidth), so it re-clobbers the
                    # window-derived figure with the screen-derived one, which
                    # is why this re-wrap could never rescue the first message
                    # it exists for.
                    w.wraplength = n
                    w.config(wraplength=n)
                except Exception:
                    continue # not a wrappable Label; leave it alone
            self.scroll.reflow()
        except Exception as e:
            log.info("status window re-wrap failed: %s", e)
    def _release_topmost(self):
        try:
            if self.winfo_exists():
                self.attributes('-topmost', False)
        except Exception as e:
            log.info("status window topmost release failed: %s", e)
    def add(self, text, title=None):
        """Append one message. Cheap by design: one Label, one scroll reflow."""
        if self._row <= 1:
            return # cap reached; the log has everything anyway
        line = '{}: {}'.format(title, text) if title else str(text)
        self._row -= 1
        l = ui.Label(self.scroll.content, text=line, anchor='w',
                    row=self._row, column=0, sticky='ew')
        try:
            # SET IT DIRECTLY; DO NOT GO THROUGH wrap(). The old code set the
            # attribute and then called wrap(), on the reasoning that "wrap()
            # takes min(self.wraplength, maxwidth), so this bounds it to the
            # window instead of the screen" — but min() does not bound it to the
            # window, it takes WHICHEVER IS SMALLER. So availablexy's
            # screen-minus-siblings maxwidth still wins whenever it is the
            # smaller of the two, which is precisely what happens here as the
            # list grows: this window gains a sibling per message, maxwidth
            # walks down, and later messages wrap narrower and narrower.
            # Kent's screenshot 2026-09-03: one message wrapped at three words
            # ("An empty / page was / skipped:") while others on the same window
            # wrapped near full width. Messages stack NEWEST ON TOP, so the bad
            # one was the FIRST — which picks the second of the two causes
            # status_window_narrow_wrap.md offered: not accumulation of siblings
            # (that would make LATER messages worse), but TIMING. It is the
            # symptom _wraplength's own docstring describes: before the window
            # is mapped, a ScrollingFrame carries grid_propagate(0) and sits at
            # some small default, so the first message wraps to a fraction of
            # the eventual width.
            #   _rewrap() exists to repair exactly that once the window IS
            # mapped — and could not, because it called wrap() too and so
            # re-clobbered its own good figure every time. Both are fixed the
            # same way.
            #   NB not covered by the maxwidth_measured guard added the same
            # day: that rescues a measurement which falls BELOW
            # MIN_AVAILABLE=200; an unmapped ScrollingFrame's default width is
            # wrong but plausible, so the floor never engages. A
            # plausible-but-wrong number needs the caller to stop asking.
            #   _wraplength() is already the honest figure (this window's own
            # width, measured only when mapped); wrap() can only make it worse.
            # The attribute is still set, so anything that later reads
            # .wraplength sees the same value.
            l.wraplength = self._wraplength()
            l.config(wraplength=l.wraplength)
            # AND RE-WRAP ONCE GEOMETRY HAS SETTLED. Setting it correctly here
            # is not enough for the FIRST message: at that moment the window may
            # not be mapped, or may be mapped at a default, so _wraplength falls
            # back to an estimate. _rewrap exists to repair that — but it only
            # ran from _on_resize, i.e. on a real <Configure> whose size
            # DIFFERED from the last one, so a window that reaches its size and
            # stays there never triggered it and the first message kept its
            # estimate for the life of the session (Kent 2026-09-03).
            #   Debounced through the same _rewrap_job as _on_resize, so a burst
            # of messages collapses to one pass over the labels.
            job=getattr(self,'_rewrap_job',None)
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
            self._rewrap_job=self.after_idle(self._rewrap)
        except Exception as e:
            log.info("status message wrap failed: %s", e)
        try:
            # A REAL reflow, but scheduled — not called inline. `reflow()` settles
            # geometry itself before recomputing, which the debounced
            # `_configure_interior()` does not: that one reads the content's
            # requested height while the just-added Label's wrap() is still
            # pending, so the canvas ends up sized to a stale (too small) content
            # and clips the very message that arrived (Kent 2026-08-25 — text cut
            # off top and bottom). It also re-reads the AVAILABLE size, which is
            # what makes a hand-resized window take effect.
            #   Scheduled via after_idle because reflow() flushes synchronously
            # (update() under Wayland, which drains events): a status message can
            # arrive mid-teardown of the window that produced it, and re-entering
            # the event loop there is the one thing this window must never do.
            #   SURFACE FIRST, REFLOW SECOND — do NOT reorder these (tried and
            # reverted 2026-08-28). Laying out before raising looks right (a
            # ScrollingFrame's children are invisible until reflow, so the raise
            # briefly shows an empty window), but reflow() drains synchronously
            # and XWayland DEADLOCKS draining a render backlog into a window
            # that is not mapped yet — the hazard spelled out at
            # ui_tkinter.py:1411-1415, and it wedged the app inside
            # _configure_canvas→update_idletasks within minutes. Map first, then
            # drain, exactly as waitdone() does for the same reason.
            self.after_idle(self.scroll.reflow)
        except Exception as e:
            log.info("status window reflow failed: %s", e)
        # Raise it for the new message: minimised by the user, or (the usual case)
        # sitting behind a fullscreen kiosk page. Still no new window.
        self._surface()


def notify_user(text, title=None, **kwargs):
    """Append a message to the one status window, creating it only when there
    isn't a live one. Never blocks. `wait`/`parent` are accepted and IGNORED so
    an ErrorNotice call site converts by changing only the name — in particular
    `parent`: the status window belongs to the app root, so a task closing can't
    take the session's messages with it."""
    global _window
    if not text:
        return
    log.info("NotifyUser: %s%s", (str(title) + ': ') if title else '', text)
    try:
        alive = _window is not None and _window.winfo_exists()
    except Exception:
        alive = False
    if not alive:
        root = ui.default_root()
        if root is None:
            return # no UI yet — the log line above is the whole record
        try:
            _window = StatusWindow(root)
        except Exception as e:
            log.error("Couldn’t open the status window (%s); message was: %s",
                    e, text)
            _window = None
            return
    try:
        _window.add(text, title=title)
    except Exception as e:
        # A status message must never take down the work that produced it.
        log.info("status window append failed: %s", e)
