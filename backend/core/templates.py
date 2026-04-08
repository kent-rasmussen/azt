# coding=UTF-8
from io_put.cawl import loadCAWL
# include WordCollection.addCAWLentries
from utilities import file
import langcodes

class WordListTemplate():
    """
    Base class for wordlist templates. once the template is read, 
    this class contains methods to strip it and load necessary bits 
    to fill it in before writing it to file.
    On error, stop and leave error text in self.error_text
    """
    def verify_code(self,code):
        # self.analang=code
        # if not self.analang:
        #     return
        try:
            self.analang_obj=self.program.languages.get_obj(code)
        except langcodes.tag_parser.LanguageTagError:
            # log.info(
            return f"{self.analang_obj} didn't parse."
        if not self.analang_obj.is_valid():
            return (f"It looks like your code ({code}) isn't valid "
                        f"({self.analang_obj.full_display()})")
        if not langtags.tag_is_valid(code):
            # e=ErrorNotice(
            #             ,wait=True)
            return _("That doesn't look like an ethnologue code ({analang})"
                    ).format(analang=code)
        self.db.analang=code
    def verify_writeable(self):
        # dir=file.gethome()
        # newfile=file.getnewlifturl(dir,self.code)
        if not newfile:
            # ErrorNotice(_("Problem creating file; does the directory "
            #             "already exist?"),wait=True)
            return _("Problem creating file; does the directory "
                        "already exist?")
        if file.exists(newfile):
            # ErrorNotice(_("The file {newfile} already exists!").format(newfile=newfile),
            #                                                     wait=True)
            return _("The file {newfile} already exists!").format(newfile=newfile)
        self.db.filename=newfile
        # self.newdirname=newfile.parent
    def fill_db_images(self):    
        yield from self.db.fill_db_images()
    def __init__(self,analang,filename):
        # self.error_text=None
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
    def __init__(self,analang,filename):
        t=loadCAWL()
        if type(t) is str:
            self.error_text=t
        else:
            self.db=t
            super().__init__(analang,filename)
            self.db.strip_lxlc_forms()
        
        
