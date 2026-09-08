# coding=UTF-8
"""Protocol that backend mixins use for UI operations.

Backend code should interact with the UI only through methods on self.ui
(an instance of this protocol). The tkinter implementation is in
frontend/ui_shell.py (TaskDressing). A test stub could provide a headless
implementation.

STATUS (2026-09-08): still UNADOPTED — nothing imports this — but no longer
speculative. The webview backend reached the screen on 2026-09-08 (splash,
LIFT chooser, task chooser and a sort board all rendering under
WebKitGTK), and getting there produced evidence about what this seam has to
say and what it must NOT say. Those findings are written up below as a spec
to grow into, per `agenda/webview_when_to_finish.md` Step 3 ("grow TaskUI by
exactly this page's worth — no more") and the finish-or-kill decision in
`agenda/ui_protocol_finish_or_kill.md`.

WHY THIS MATTERS MORE THAN IT DID: the alternative seam,
`frontend/ui_interface.py`, is Tk's vocabulary written as an ABC — it
*mandates* winfo_screenwidth, winfo_reqwidth, update_idletasks, after,
wait_window, tk_popup. Conformance to it does not buy portability, because
those names carry Tk's model with them. Every item in "WHAT THE PORT TAUGHT
US" below is a case where replaying a Tk concept through a browser produced a
bug, and where naming the INTENT instead would not have.


WHAT THE PORT TAUGHT US
=======================

1. VISIBILITY IS NOT A WINDOW OPERATION, and must not be expressed as one.
   ONE HARD RESULT: a pywebview window created hidden NEVER appears — show()
   does not map it, then or later
   (tests/manual/webview_multiwindow/hide_show.py --start-hidden). A-Z+T
   builds every task window withdrawn and reveals it later, so that model
   cannot be carried across as-is.
       RETRACTED 2026-09-08: an earlier version of this claimed hide-then-show
       "restored a window 2 times in 3" and called it measured. It was one
       run of a probe watched by eye, and the windows that appeared not to
       come back are better explained by two bugs since fixed (widgets
       parented to a window were never appended to the page; show() issued
       before a window's page had loaded was discarded).
       WHERE IT LANDED: hide/show WORKS in every case observed since. The
       app itself is the better sample — a boot hides the root, shows and
       destroys the splash, shows and hides the LIFT chooser, hides and
       re-shows the task chooser, and shows task windows — and all of it
       behaves. Do not record this as "flaky", and do not record it as
       "needs characterising" either: that was a second hedge implying work
       that does not exist.
       STILL OPEN, and about `hidden=` rather than hide/show: does
       created-hidden also fail on EdgeChromium? That is what Windows uses,
       a third backend, and the existing probe answers it unchanged.
       The protocol point stands on its own: it should say "show this WORK
       SURFACE" and let the implementation decide whether that is an OS
       window, a tab, or a DOM view.
       Corollary that IS measured: one window per surface costs a full page
       load, four HTTP round trips and a JS bridge handshake EACH — 408
       queued widget calls waited on one such handshake — so one window with
       many views is cheaper, independently of any reliability claim.

2. WAITING IS ON AN EVENT, NOT ON A WIDGET.
   `wait_for_window(window)` inherits tkinter's `wait_window`, and ~30 call
   sites pass a CANARY WIDGET rather than a window (`w.wait_window(self.l)`
   on a Label) because the label's destruction is the signal. Under webview
   this deadlocked boot: the LIFT chooser was retired by destroy() rather than
   quit, and nothing released the waiter.
       So the protocol wants "wait until this INTERACTION is finished" —
       a future/event the UI resolves — not "block until this object is
       destroyed". Widget destruction is an implementation detail that
       happens to be observable in Tk.

3. LAYOUT INTENT, NOT GRID COORDINATES.
   316 lines of `.grid(row=…, column=…, sticky=…)` live in backend/tasks.
   They translate to CSS Grid — but `sticky` becomes an INLINE `justify-self`,
   and an inline style beats any stylesheet rule short of !important. So a
   page cannot be restyled without fighting per-widget inline CSS written
   from Tk kwargs. Worse, nested Frames each become their own grid container,
   so cells in sibling frames DO NOT ALIGN with each other or with a shared
   header — visible on the first sort board as a staircase of values under
   fixed column headings, where tkinter aligned them because all cells shared
   one master.
       So the protocol wants to say WHAT a page is — "a centred title card",
       "a table of profiles by check", "a row of choices" — and let the
       implementation lay it out. The two real pages so far want opposite
       treatment (the splash centred, a board densely aligned), which a
       coordinate-level API cannot express and a stylesheet can.

4. A SURFACE MUST BE ABLE TO SAY WHAT IT IS.
   Every webview window loads the same base.html, so nothing could tell the
   splash from a sort board — the fix was to stamp the page's identity
   (`document.body.dataset.page`) so CSS could differentiate. That identity is
   exactly the semantic label point 3 wants, and it should come from the
   protocol rather than being inferred from a Python class name.

5. SIZE COMES FROM CONTENT, CAPPED BY THE DISPLAY — NEVER DERIVED FROM IT.
   The Tk side's `availablexy` computes space by subtracting sibling sizes
   from the SCREEN, goes negative by construction, and was floored to 200px —
   a number that then became a real layout value. The webview side started
   with the opposite failure: windows at a hardcoded 800x600 with nothing
   relating that to their contents, so the chooser had to be resized by hand.
       So the protocol should express "this surface should fit its content"
       and leave measurement to the implementation. No caller should be able
       to ask how wide the screen is; that question is what produced both
       bugs.

6. NO-OPS ARE LOAD-BEARING, so the protocol must distinguish "not applicable
   here" from "not implemented yet". Three bugs on 2026-09-07/08 came from
   implementing methods that had been harmless no-ops: `attributes()` doing
   nothing meant `takekioskscreen()` did nothing, and implementing it sent
   every task window fullscreen and undecorated; `hidden=` unsupported meant
   windows were visible, and supporting it made them unmappable.
       So a semantic method needs a documented answer for a backend where it
       is meaningless (a browser wraps text in its box; there is no kiosk
       mode to take), and that answer must be "correct by design", not
       "silently nothing".


DRAFT DIRECTION (not yet code)
==============================
The methods below are the existing Tk-shaped draft, kept because
`drive_work` is the one member the two sides already agree on. What the
findings above point to is a smaller, intent-shaped surface, roughly:

    surface(kind, title)        -> a work surface of a named KIND
                                   ('title-card', 'chooser', 'board', 'form')
    surface.present()           -> make it the thing the user is looking at
    surface.retire()            -> we are done with it (implementation
                                   decides hide vs destroy vs discard view)
    surface.fit()               -> size to content, capped by the display
    interaction() -> awaitable  -> resolved when the user has answered
    progress(value)
    drive_work(generator, on_done=None)

Deliberately absent: screen dimensions, grid coordinates, sticky, window
handles, widget identity, and anything named after a Tk call. Each of those
is a bug from the list above.

DO NOT adopt this piecemeal. The plan of record is to grow it one real page
at a time (Step 3), so that every member exists because a page needed it.
"""


class TaskUI:
    """Abstract interface for task UI operations.

    Tk-shaped draft, retained as the current state of the art rather than as
    the target — see WHAT THE PORT TAUGHT US in the module docstring for where
    each of these leaks Tk's model."""

    def show_run_window(self, msg=None, title=None):
        """Create and show a secondary work window. Returns a window handle.

        LEAKS: "window" and a handle. Finding 1 — the caller should ask for a
        work SURFACE and not care whether it is an OS window."""
        raise NotImplementedError

    def clear_run_window(self):
        """Destroy the current run window if it exists.

        LEAKS: "destroy". Finding 1 — destroying a pywebview window crashes
        QtWebEngine and throws away a page load; retiring it is the intent."""
        raise NotImplementedError

    def hide(self):
        """Hide the task window.

        LEAKS: window visibility as a caller-driven operation. Finding 1 —
        measured unreliable on pywebview/GTK."""
        raise NotImplementedError

    def show(self):
        """Show the task window. Same caveat as hide()."""
        raise NotImplementedError

    def wait_for_window(self, window):
        """Block until window is destroyed.

        LEAKS: destruction as the signal. Finding 2 — ~30 sites pass a canary
        WIDGET, and this deadlocked webview boot."""
        raise NotImplementedError

    def show_progress(self, value):
        """Update progress indicator."""
        raise NotImplementedError

    def drive_work(self, generator, on_done=None):
        """Consume a work generator one yield at a time, letting the
        event loop paint between chunks. Calls waitdone() on completion,
        then on_done() if provided.

        THE ONE MEMBER BOTH SIDES ALREADY AGREE ON, and the model for the
        rest: it names an intention (drive this work, stay responsive) and
        says nothing about how the event loop achieves it."""
        raise NotImplementedError

    @property
    def run_window(self):
        """The current secondary work window, or None.

        LEAKS: the worst offender. `self.ui.runwindow.<raw Tk>` chains appear
        on 73 lines across 5 files — a named hole in the abstraction rather
        than an abstraction."""
        raise NotImplementedError

    @property
    def exit_requested(self):
        """Whether the user has requested exit."""
        raise NotImplementedError
