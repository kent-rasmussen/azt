# coding=UTF-8
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)
from frontend.ui_shell import TaskDressing
from backend.core.lexicon import Tone, Segments #for makecvtok

class Task(TaskDressing):
    """Things that need to be, if not set elsewhere:"""
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
    def makecvtok(self):
        """Should these not be done locally, in Tone and Segments?"""
        # log.info("cvt: {}".format(self.program.params.cvt()))
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
            self.makecvtok() #this uses self, the following are just any sane
            self.ftype=self.program.params.ftype() #sets default if not
            self.program.slices.makepsok() #may not succeed, if no pss yet
            self.program.slices.makeprofileok() #may not succeed, if no profiles yet
            self.program.status.makecheckok() #this is intentionally broad: *any* check
        except AttributeError as e:
            log.info(_("Maybe status/slices aren't set up yet."))
        # self.program.status.makegroupok(wsorted=True)
    def __init__(self, program):
        self.program = program
        if hasattr(self,'cvt'):
            self.program.params.cvt(self.cvt)
        # self.makecvtok() #this just enforces a good cvt value
        if self.program.taskchooser == self:
            parent=self.program.tk_root
        else:
            self.program.task = self
            parent=self.program.taskchooser
        self.analang=self.program.db.analang
        self.min_to_multicolumn=6 #don't use buttoncolumns with less
        self.makeeverythingok()
        TaskDressing.__init__(self, parent) #window
        log.info(f"Done initializing {self.__class__.__name__}."
                 f"(base: {self.program.task_base()})")
