# coding=UTF-8
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)
from backend.core.lexicon import Tone, Segments #for makecvtok

class TaskBase:
    """Pure logic base for tasks. No window, no UI dependency.

    Holds class-level flags, makecvtok/makeeverythingok logic, and
    program wiring. Unknown attribute access delegates to self.ui
    (the TaskWindow) via __getattr__, so backend mixins can call
    window methods transparently.
    """
    is_chooser=False
    is_report=False
    is_record_task=False
    uses_second_forms=False
    do_not_show_slices=False
    multislice_max=False
    multicheck_scope=False
    do_not_show_cvt=False
    show_parser_ui=False
    no_leaderboard=False
    icon_leaderboard=False
    glyph_leaderboard=False
    cvt_sensitive=False
    show_second_fields=False
    show_buttoncolumnsline=False

    def __getattr__(self, name):
        """Delegate unknown attributes to self.ui (the TaskWindow).

        This lets backend mixins call window methods (withdraw, frame,
        runwindow, context, etc.) without importing frontend code.
        Only fires when normal attribute lookup fails.
        """
        # Prevent recursion: if ui isn't set yet, stop
        try:
            ui = object.__getattribute__(self, 'ui')
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}' "
                f"(ui not yet initialized)")
        if ui is None:
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}' "
                f"(ui is None)")
        # Per-instance recursion guard
        try:
            guard = object.__getattribute__(self, '_getattr_guard')
        except AttributeError:
            guard = set()
            object.__setattr__(self, '_getattr_guard', guard)
        if name in guard:
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}'")
        guard.add(name)
        try:
            return getattr(ui, name)
        finally:
            guard.discard(name)

    # -- Delegation methods for super() chains --
    # These exist because __getattr__ doesn't intercept super() calls.
    # Concrete tasks override setcontext/on_quit and chain via super().

    def setcontext(self):
        """Terminator for the task-mixin setcontext chain.

        TaskDressing populates window-chrome items and then calls
        ``self.task.setcontext()``, which walks the mixin MRO. Each
        mixin's ``setcontext`` should call ``super().setcontext()``
        before adding its own items; this base method ends the chain.
        """
        pass

    # ── Being finished, as a FACT rather than an inference ────────────
    # WHY THIS EXISTS. Long builds ask "should I still be doing this?" and
    # the answer used to be inferred from the WINDOW —
    # `Senses._window_is_there()`, i.e. `winfo_exists()`. That was a reliable
    # proxy only because tkinter's `on_quit` ends in `destroy()`. The webview
    # backend HIDES windows instead (see `_close_native_window`: freeing a
    # pywebview window at the wrong moment crashes Qt, and this app reuses
    # windows anyway), so a closed task's window is alive and the proxy says
    # "carry on".
    #
    # AND THE LOOPS ARE NOT INTERRUPTED ANY MORE. `lexicon.py:2101`'s comment
    # describes the tkinter world exactly: "`waiting()` + `waitprogress`
    # drain the event loop, so the click is serviced HERE". One event loop,
    # one flow, so the window died mid-iteration and the guard caught it.
    # Under webview every page event arrives on its OWN THREAD
    # (`webview/util.py:_call`, visible in every faulthandler dump), so
    # clicking Tasks does not interrupt the affix loop — it runs beside it.
    # Two task flows, concurrently, neither aware of the other. That is what
    # Kent saw as the parser still working after an unrelated task had
    # started (2026-09-16): "the parser work shouldn't be continuing AFTER
    # another unrelated task is already started. That wait shouldn't appear
    # at all."
    #
    # SO ASK THE TASK, NOT THE WINDOW. A task that has been closed knows it;
    # nothing has to be deduced. `program.task is self` is already the
    # codebase's idiom for the same question — see `hide_chooser` — and a
    # FLAG needs no handle, which answers this item's own objection to
    # close-time cancellation ("half 1 can only cancel work whose handle the
    # window holds"): a synchronous build ten frames down can read a flag.
    #
    # See agenda/webview_flows_run_concurrently.md.
    _closed = False

    def still_wanted(self):
        """Should work belonging to this task keep going?

        False once this task has been closed, or once the program has moved
        on to another one. Never raises: a build asking this question is
        mid-flight, and an exception here would replace the fault it exists
        to prevent."""
        if self._closed:
            return False
        try:
            live = getattr(self.program, 'task', None)
            # `None` means the chooser cleared it (`chooser.py:163`) and no
            # task is live — which is also a reason to stop. A DIFFERENT
            # task means the user moved on.
            if live is not None and live is not self:
                return False
        except Exception:
            return True
        return True

    def _on_close(self, why=''):
        """Record that this task is finished, and drop what it is holding.

        Called from `on_quit` and from `_dismiss_unshown` — the two ways a
        task ends — so a task cannot be closed without its work being told.
        Concrete tasks override to add their own teardown and should call
        `super()._on_close(why)` first, so the flag is set even if their own
        cleanup raises.

        Idempotent: both exits can run for one task, and a second close must
        not undo the first or log twice."""
        if self._closed:
            return
        self._closed = True
        log.info("task %s closed%s — work belonging to it should stop",
                 type(self).__name__, ' ({})'.format(why) if why else '')
        # WHAT THE TASK ITSELF HOLDS. `cancel_drive_work` is the one handle
        # the window has, and tkinter's `on_quit` has always called it
        # (`ui_tkinter.py:1420`); anything else a task holds belongs in its
        # own override.
        for attr in ('cancel_drive_work',):
            fn = getattr(self, attr, None)
            if callable(fn):
                try:
                    fn()
                except Exception as e:
                    log.info("task %s: %s failed on close (%r)",
                             type(self).__name__, attr, e)

    def on_quit(self, **kwargs):
        """Delegate to the window's on_quit (ui.Window)."""
        self._on_close('on_quit')
        self.ui.waitdone()
        self.ui.on_quit(**kwargs)

    def _dismiss_unshown(self):
        """Quietly tear down this task's still-withdrawn window WITHOUT reviving
        the parent chooser or quitting to root (both of which on_quit would do).
        Used when the open-time syllable-profile offer sends the user to a
        different task: that task is already open, so this board must just go."""
        # THE OTHER WAY A TASK ENDS, so it records the same fact. Without
        # this a task dismissed by the profile offer would leave its loops
        # believing they were still wanted. See `_on_close`.
        self._on_close('dismissed unshown')
        try:
            self.ui.exitFlag.true()
            self.ui.cleanup()
            self.ui.destroy()
        except Exception as e:
            log.info(f"_dismiss_unshown: {e}")

    def makecvtok(self):
        """Should these not be done locally, in Tone and Segments?"""
        if isinstance(self,Tone):
            self.checktypename='frame'
            self.cvt='T'
        if isinstance(self,Segments):
            self.checktypename='check'
            # 'S' (SortSyllables) inherits Segments for shared helpers but is a
            # whole-word syllable-profile sort; don't reset it to 'V'.
            if self.cvt not in ['V','C','CV','S']:
                self.cvt='V'
        self.cvt=self.program.params.cvt(self.cvt)

    def i_am_the_task(self):
        self.program.task=self
        self.program.status.task(self)

    def hide_chooser(self):
        """Withdraw the task chooser — UNLESS the user has gone back to it.

        Tasks hide the chooser behind the page they have just built. But the
        chooser's Tasks button can fire DURING that build (a slow affix load
        drains the event loop), and `gettask()` then quits this task and
        re-reveals the chooser. Withdrawing unconditionally on the way out
        hid it again, leaving the user with NO WINDOW AT ALL — Kent,
        2026-09-14, clicking Tasks during a page load.

        `gettask` clears `program.task` (chooser.py:163), so that is the
        test. Returns False when it declined, which is also the caller's
        signal to stop building a page nobody is waiting for.
        """
        if getattr(self.program,'task',None) is not self:
            log.info("not hiding the task chooser: %s is no longer the live "
                     "task, so the user has asked to be back there",
                     type(self).__name__)
            return False
        self.program.taskchooser.withdraw()
        return True

    def makeeverythingok(self):
        """The value of this method is unclear. This may be better
        done elsewhere."""
        try:
            self.makecvtok()
            self.ftype=self.program.params.ftype()
            self.program.slices.makepsok()
            self.program.slices.makeprofileok()
            self.program.status.makecheckok()
        except AttributeError as e:
            log.info(_("Maybe status/slices aren’t set up yet."))

class Task(TaskBase):
    """Task with a separate TaskWindow. Creates the window on init."""
    ui_kwargs={"withdrawn"}
    def __init__(self, program, **kwargs):
        self.program = program
        if hasattr(self,'cvt'):
            self.program.params.cvt(self.cvt)
        if not hasattr(self,'ftype'):
            self.ftype=self.program.params.ftype('lc')
        if self.program.taskchooser == self:
            parent=self.program.tk_root
        else:
            self.i_am_the_task()
            parent=self.program.taskchooser.ui
        self.analang=self.program.db.analang
        self.min_to_multicolumn=6
        self.makeeverythingok()
        from frontend.task_window import TaskWindow
        ui_kwargs={k:v for k,v in kwargs.items() if k in self.ui_kwargs}
        self.ui = TaskWindow(self, parent, **ui_kwargs)
        log.info(f"Done initializing {self.__class__.__name__} "
                 f"(base: {self.program.task_base()})")
