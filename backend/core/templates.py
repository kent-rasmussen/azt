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
            return _("self.analang_obj didn’t parse.")
        except Exception as e:
            return _("self.analang_obj didn’t parse ({e}).").format(e=e)
        if not self.analang_obj.is_valid():
            return (f"It looks like your code ({code}) isn't valid "
                        f"({self.analang_obj.full_display()})")
        if not langtags.tag_is_valid(code):
            # e=ErrorNotice(
            #             ,wait=True)
            return _("That doesn’t look like an ethnologue code ({analang})"
                    ).format(analang=code)
        # self.db.get_langs(analang=code) #This sets self.db.analang
        self.analang=code
        # self.program.settings.save_analang(code)
    def verify_writeable(self,**kwargs):
        dir=file.gethome()
        if kwargs.get('demo'):
            filename_code='Demo_'+self.analang
        else:
            filename_code=self.analang
        self.filename=file.getnewlifturl(dir,filename_code)
        #Any return here means that the file will not be written.
        if not self.filename:
            return _("Problem creating file name from {dir=}, {filename_code=}"
                    "").format(dir=dir,filename_code=filename_code)
        #I don't think I care so much about this. If the folder is there, but the 
        #file is not (else below is true) I'll just write it into the existing 
        # directory.
        # # if file.exists_and_not_empty(self.filename.parent):
        #     return _("The directory {newfile} already exists and isn't empty!").format(newfile=self.filename.parent)
        if file.exists(self.filename):
            return _("The file {newfile} already exists!").format(newfile=self.filename)
        self.db.set_filename(self.filename) #This was done once on template load; now to new location.
        log.info(_("Going to write to {newfile}").format(newfile=self.filename))
    def fill_db_images(self):    
        yield from self.db.fill_db_images()
    def convertglosstocitation(self,analang):
        self.db.convertglosstocitation(analang)
    def __init__(self,program,**kwargs):
        log.info(_("Preparing word list for writing"))
        self.program=program
        self.error_text=None
        if analang:=kwargs.pop('analang',None): #otherwise, do this later, manually.
            self.init_w_code_and_filename(analang,**kwargs)
        log.info(_("Word list initialized"))
    def init_w_code_and_filename(self,analang,**kwargs):
        self.error_text=self.verify_code(analang) #sets self.db.analang
        if self.error_text:
            return
        self.error_text=self.verify_writeable(**kwargs) #sets self.db.filename
        if self.error_text:
            return
        # self.analang=analang
        # self.db.filename=filename
        self.db.init_post_analang(self.analang)

class CAWL(WordListTemplate):
    """This loads from the Comparative African Word List(CAWL)"""
    def __init__(self,program,**kwargs):
        log.info(f"Loading CAWL")
        t=loadCAWL()
        log.info(f"Loaded {t} ({type(t)})")
        if type(t) is str:
            self.error_text=t
            return
        self.db=t
        super().__init__(program,**kwargs)
        if not self.error_text:
            log.info(f"Stripping lxlc forms from CAWL")
            self.db.strip_lxlc_forms() #OK for demo; forms come from glosses
            # self.db.collect_and_sort_plausible_lang_codes() #depends on lx/lc/ph in database
        log.info("Done initializing CAWL")
        
