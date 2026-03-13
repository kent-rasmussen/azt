# coding=UTF-8
import gettext
_ = gettext.gettext
from utilities import logsetup
log=logsetup.getlog(__name__)
from frontend.ui_shell import TaskDressing

class Task(TaskDressing):
    def makecvtok(self):
        # log.info("cvt: {}".format(self.program.params.cvt()))
        if isinstance(self,Tone) and not self.program.params.cvt() == 'T':
            self.program.settings.setcvt('T')
        if isinstance(self,Segments) and (self.program.params.cvt()
                                                    not in ['V','C','CV']):
            self.program.settings.setcvt('V')
    def makeeverythingok(self):
        try:
            self.makecvtok() #this uses self, the following are just any sane
            self.program.slices.makepsok()
            self.program.slices.makeprofileok()
            self.program.status.makecheckok() #this is intentionally broad: *any* check
        except KeyError as e:
            _log.info(_("Maybe status/slices aren't set up yet."))
        # self.program.status.makegroupok(wsorted=True)
    def __init__(self, program, _parent=None):
        self.program = program
        self.makecvtok() #this just enforces a good cvt value
        parent = _parent if _parent is not None else self.program.taskchooser
        TaskDressing.__init__(self, parent) #window
