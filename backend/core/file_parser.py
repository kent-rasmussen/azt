# coding=UTF-8
from utilities.utilities import *
from utilities.i18n import _
from utilities import logsetup, file
from io_put import lift
import settings
log=logsetup.getlog(__name__)

from utilities.error_handler import notify_error as ErrorNotice

class FileParser(object):
    """This class parses the LIFT file, once we know which it is.
    Unless, of course, it was loaded in LiftChooser."""
    def loaddatabase(self):
        try:
            #This program key will only be available after this finishes
            self.program.db=lift.LiftXML(str(self.filename),self.program.analang)
        except lift.BadParseError:
            text=_("{filename} doesn’t look like a well formed lift file; please "
                    "try again.").format(filename=self.filename)
            log.info("'lift_url.py' removed.")
            if self.program.tk_root.exitFlag.istrue():
                log.info(text)
                return
            else:
                ErrorNotice(text,title=_('LIFT parse error'),wait=True)
            file.writefilename() #just clear the default
            raise #Then force a quit and retry
        except Exception as e:
            # NEUTRAL ON PURPOSE (Kent, 2026-10-14). Everything raised after a
            # successful parse lands here: program bugs (the `cawln` rename),
            # well-formed content the code can't handle, and settings or
            # environment problems — the exception type doesn't tell them
            # apart. "(non-XML) problem loading your database" read as a fault
            # in the user's file when it was a bug. Until content problems get
            # their own error type (agenda: "LIFT content errors get their own
            # type"), say only what is known: it parsed, reading it failed.
            text=_("{filename} was read as valid XML, but A−Z+T failed while "
                   "reading its contents:\n\n{error}\n\nPlease send the log "
                   "to whoever supports you. I will remove this file as the "
                   "default, so you can open another."
                   ).format(filename=self.filename,
                            error='{}: {}'.format(type(e).__name__, e))
            log.error(text)
            ErrorNotice(text,title=_('LIFT non-parse error'),wait=True)
            file.writefilename()
            raise
    def dailybackup(self):
        """ONE PER RUN, despite the name. `backupfilename` carries a
        timestamp to the second (`xmletfns`), so the existence test below
        never matches an earlier run and this writes on every start. That is
        the intended behaviour — the name is left from when it was daily, and
        is kept only because callers use it. Worth knowing before reading the
        `if` as a guard against frequent writes: it is not one."""
        if not file.exists(self.program.db.backupfilename):
            self.program.db.write(self.program.db.backupfilename)
        else:
            print(_("Apparently we’ve run this before today; not backing "
            "up again."))
    def getwritingsystemsinfo(self):
        """This doesn't actually do anything yet, as we can't parse ldml."""
        self.program.db.languagecodes=self.program.db.analangs+self.program.db.glosslangs
        self.program.db.languagepaths=file.getlangnamepaths(self.filename,
                                                    self.program.db.languagecodes)
    def __init__(self,program):
        super(FileParser, self).__init__()
        self.program=program
        if hasattr(self.program,'db') and isinstance(self.program.db,lift.LiftXML):
            log.info("Using {analang} db already loaded from {filename}"
                    "".format(analang=self.program.db.analang,
                            filename=self.program.db.filename))
        self.filename=self.program.filename
        """I think an ad hoc settings goes here, to load analang.
        Everyone should have this, if available in settings."""
        mgr=settings.SettingsManager(self.filename)
        self.program.analang=mgr.project.get('analang',None)
        log.info(f"Ready to load {self.filename} with {self.program.analang=}")
        # self.analang=self.program.analang
        # splash.progress(15)
        self.loaddatabase()
        # splash.progress(25)
        # if self.program.tk_root.exitFlag.istrue():
        #     return
        self.dailybackup()
        # splash.progress(35)
        # splash.progress(45)
        self.getwritingsystemsinfo()
        # self.dogrid()
        # back=ui.Button(self.outsideframe,text=_("Tasks"),cmd=self.program.taskchooser)
        # self.setfontsdefault()
