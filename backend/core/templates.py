# coding=UTF-8
from io_put.cawl import loadCAWL
# include WordCollection.addCAWLentries
from utilities.i18n import _
from utilities import file,logsetup
import langcodes
from backend import langtags

log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file

class WordListTemplate():
    """
    Base class for wordlist templates. once the template is read, 
    this class contains methods to strip it and load necessary bits 
    to fill it in before writing it to file.
    On error, stop and leave error text in self.error_text
    """
    def verify_code(self,code):
        log.info(f"verify_code: code={code}")
        # self.analang=code
        # if not self.analang:
        #     return
        try:
            self.analang_obj=self.program.languages.get_obj(code)
        except langtags.langcodes.tag_parser.LanguageTagError:
            # log.info(
            return _("self.analang_obj didn't parse.")
        except Exception as e:
            return _("self.analang_obj didn't parse ({e}).").format(e=e)
        if not self.analang_obj.is_valid():
            return (f"It looks like your code ({code}) isn't valid "
                        f"({self.analang_obj.full_display()})")
        if not langtags.tag_is_valid(code):
            # e=ErrorNotice(
            #             ,wait=True)
            return _("That doesn't look like an ethnologue code ({analang})"
                    ).format(analang=code)
        self.db.get_langs(code)
        self.program.settings.save_analang(code)
    def verify_writeable(self):
        dir=file.gethome()
        newfile=file.getnewlifturl(dir,self.db.analang)
        if not newfile:
            return _("Problem creating file; does the directory "
                        "already exist with files in it? ({newfile})").format(newfile=newfile)
        if file.exists(newfile):
            return _("The file {newfile} already exists!").format(newfile=newfile)
        self.db.set_filename(newfile)
        log.info(_("Going to write to {newfile}").format(newfile=newfile))
    def fill_db_images(self):    
        yield from self.db.fill_db_images()
    def __init__(self,analang,program):
        log.info(_("Preparing word list for writing"))
        self.program=program
        self.error_text=None
        self.error_text=self.verify_code(analang) #sets self.db.analang
        if self.error_text:
            return
        self.error_text=self.verify_writeable() #sets self.db.filename
        if self.error_text:
            return
        # self.analang=analang
        # self.db.filename=filename
        self.db.getentries() #this needs analang
        self.db.getsenses()

class CAWL(WordListTemplate):
    """This loads from the Comparative African Word List(CAWL)"""
    def __init__(self,analang,program):
        log.info(f"Loading CAWL for {analang}")
        t=loadCAWL()
        log.info(f"Loaded {t} ({type(t)})")
        if type(t) is str:
            self.error_text=t
            return
        self.db=t
        super().__init__(analang,program)
        log.info(f"Stripping lxlc forms from CAWL")
        if not self.error_text:
            self.db.strip_lxlc_forms()
            # self.db.collect_and_sort_plausible_lang_codes() #depends on lx/lc/ph in database
        
        
