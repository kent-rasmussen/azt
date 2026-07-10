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

    def on_quit(self, **kwargs):
        """Delegate to the window's on_quit (ui.Window)."""
        self.ui.waitdone()
        self.ui.on_quit(**kwargs)

    def _dismiss_unshown(self):
        """Quietly tear down this task's still-withdrawn window WITHOUT reviving
        the parent chooser or quitting to root (both of which on_quit would do).
        Used when the open-time syllable-profile offer sends the user to a
        different task: that task is already open, so this board must just go."""
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
