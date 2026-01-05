#!/usr/bin/env python3
# coding=UTF-8
program={'name':'azt',
        'translationdir':'translations',
        'lang':'fr_FR',
        'podir':'LC_MESSAGES'
        }
# pototranslate='azt.po'
import polib
import ui_tkinter as ui
import file
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import urls
import htmlfns
import webbrowser
try: #translation
    _
except NameError:
    def _(x):
        return x
class Catalog(object):
    """docstring for Catalog."""
    def allentries(self):
        return self.po
    def validentries(self):
        self.validentries = [e for e in self.po if not e.obsolete]
    def translated(self):
        return self.po.translated_entries()
    def untranslated(self):
        return self.po.untranslated_entries()
    def fuzzy(self):
        return self.po.fuzzy_entries()
    def percentdone(self):
        return self.po.percent_translated()
    def __init__(self):
        super(Catalog, self).__init__()
        self.transdir=file.getfile(program['translationdir'])
        self.pot = self.transdir.joinpath(program['name']).with_suffix('.pot')
        self.file = self.transdir.joinpath(program['lang'],program['podir'],
                                            program['name']).with_suffix('.po')
        self.mo = self.file.with_suffix('.mo')
        log.info("pot: {}".format(self.pot))
        log.info("po: {}".format(self.file))
        log.info("mo: {}".format(self.mo))
        self.po = polib.pofile(self.file)
        self.pot
class Entry(polib.POEntry):
    """docstring for Translation."""

    def __init__(self, entry):
        super(Entry, self).__init__()
        self.msgid = entry.msgstr
        self.msgstr = entry.msgstr

class EntryFrame(ui.Frame):
    """docstring for Translation."""
    def bt(self,text):
        kwargs={
                'sl':'en', #search language
                'tl':'fr',  #translate to language
                'op':'translate', #operation?
                'text':text
                }
        terms=urls.urlencode(kwargs)
        url='https://translate.google.com/?'+terms
        try:
            webbrowser.open_new(url)
            # html=htmlfns.getdecoded(url)
        except urls.MaxRetryError as e:
            msg=_("Problem downloading webpage; check your "
                        "internet connection!\n\n{}".format(e))
            log.error(msg)
            ErrorNotice(msg)
            return
        # self.parent.scraper.feed(html)
        # https://translate.google.com/?sl=en&tl=fr&text=text&op=translate
    def save(self):
        self.msgstr=self.transvar.get()
        log.info("saved {}".format(self.msgstr))
    def __init__(self, parent, entry, **kwargs):
        super(EntryFrame, self).__init__(parent, **kwargs)
        self.entry=Entry(entry)
        self.msgid = entry.msgstr
        self.msgstr = entry.msgstr
        self.transvar=ui.StringVar(self,entry.msgstr)
        l=ui.Label(self,text=self.msgid,row=0,column=0)
        e=ui.EntryField(self,textvariable=self.transvar,
                        width=len(self.transvar.get()),
                        row=0,column=1)
        e.bind('<Return>',self.save)
        l.wrap()
        l.bind('<MouseButton-1>',self.bt)
class EntryWindow(ui.Window):
    """docstring for TranslationWindow."""
    def getentries(self):
        # self.entries=self.catalog.translated()
        self.entries=self.catalog.untranslated()
    def __init__(self, parent, catalog):
        self.catalog=catalog
        self.scraper=htmlfns.TranslationScraper()
        super(EntryWindow, self).__init__(parent)
        sf=ui.ScrollingFrame(self.frame,row=0, column=0)
        self.getentries()
        for n,entry in enumerate(self.entries):
            EntryFrame(sf.content,entry,row=n,column=0)
            # print(entry.msgid, entry.msgstr)
            # self.parent = parent

def App():
    global program
    c=Catalog()
    # for entry in c.po.translated_entries():
    #     print(entry.msgid, entry.msgstr)
    # exit()
    r=ui.Root(program=program)
    # r.withdraw()
    EntryWindow(r,c)
    r.mainloop()
    sysexit()

if __name__ == '__main__':
    App()
