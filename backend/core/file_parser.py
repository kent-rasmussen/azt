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
            text=_("There seems to be a (non-XML) problem loading your "
            "database ({filename}); I will remove it as default so you can open "
            "another").format(filename=self.filename)
            log.error(text)
            ErrorNotice(text,title=_('LIFT non-parse error'),wait=True)
            file.writefilename()
            raise
    def dailybackup(self):
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
