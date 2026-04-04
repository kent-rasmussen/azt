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
    ischooser=False
    isreport=False
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
        return getattr(ui, name)

    # -- Delegation methods for super() chains --
    # These exist because __getattr__ doesn't intercept super() calls.
    # Concrete tasks override setcontext/on_quit and chain via super().

    def setcontext(self, context=None):
        """Delegate to the window's setcontext (TaskDressing)."""
        self.ui.setcontext(context)

    def on_quit(self, **kwargs):
        """Delegate to the window's on_quit (ui.Window)."""
        self.ui.on_quit(**kwargs)

    def makecvtok(self):
        """Should these not be done locally, in Tone and Segments?"""
        if isinstance(self,Tone):
            self.checktypename='frame'
            self.cvt='T'
        if isinstance(self,Segments):
            self.checktypename='check'
            if self.cvt not in ['V','C','CV']:
                self.cvt='V'
        self.cvt=self.program.params.cvt(self.cvt)

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
            log.info(_("Maybe status/slices aren't set up yet."))

class Task(TaskBase):
    """Task with a separate TaskWindow. Creates the window on init."""
    def __init__(self, program):
        self.program = program
        if hasattr(self,'cvt'):
            self.program.params.cvt(self.cvt)
        if self.program.taskchooser == self:
            parent=self.program.tk_root
        else:
            self.program.task = self
            parent=self.program.taskchooser.ui
        self.analang=self.program.db.analang
        self.min_to_multicolumn=6
        self.makeeverythingok()
        from frontend.task_window import TaskWindow
        self.ui = TaskWindow(self, parent)
        log.info(f"Done initializing {self.__class__.__name__}."
                 f"(base: {self.program.task_base()})")
