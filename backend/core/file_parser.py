# coding=UTF-8
from utilities.utilities import *
from utilities import logsetup, file
from io_put import lift
log=logsetup.getlog(__name__)

from frontend.error_notice import ErrorNotice

def __getattr__(name):
    # Lazy load globals from main
    if name in ('_',):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('_',):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

class FileParser(object):
    """This class parses the LIFT file, once we know which it is."""
    def loaddatabase(self):
        try:
            #This program key will only be available after this finishes
            self.program.db=lift.LiftXML(str(self.filename),getattr(self.program,'analang',None))
        except lift.BadParseError:
            text=_("{filename} doesn't look like a well formed lift file; please "
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
            print(_("Apparently we've run this before today; not backing "
            "up again."))
    def getwritingsystemsinfo(self):
        """This doesn't actually do anything yet, as we can't parse ldml."""
        self.program.db.languagecodes=self.program.db.analangs+self.program.db.glosslangs
        self.program.db.languagepaths=file.getlangnamepaths(self.filename,
                                                    self.program.db.languagecodes)
    def __init__(self,program):
        super(FileParser, self).__init__()
        self.program=program
        self.filename=self.program.filename
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
