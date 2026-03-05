# coding=UTF-8
import sys
import collections
import re
import datetime
# import tkinter as tk
from frontend import ui_tkinter as ui
from backend.core.analysis import Analysis
from utilities.utilities import *
from utilities import file, logsetup, htmlfns
from io_put import lift
# import time
# import webbrowser
# import os
# import platform
# import subprocess
# import threading
# import json
# import itertools
# import inspect
# import multiprocessing

log=logsetup.getlog(__name__)

def __getattr__(name):
    # Lazy load globals from main
    if name in ('program', 'counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Tone', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('program', 'counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Tone', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

class Senses(object):
    """docstring for Senses."""
    def groups(self,**kwargs): #toverify=True
        return program['status'].groups(**kwargs)
    def group(self,value=None,**kwargs):#get/set
        return program['status'].group(value,**kwargs)
    def notdonewarning(self):
        buttontxt=_("Sort!")
        text=_("Hey, you're not done with {ps} {profile} words by {check}!"
                "\nCome back when you have time; restart where you left "
                "off by pressing ‘{button}’").format(ps=self.ps,profile=self.profile,check=self.check,
                                                button=buttontxt)
        # self.withdraw()
        if not program['Demo']: #Should anyone see this?
            ErrorNotice(text=text,title=_("Not Done!"),parent=self,wait=True)
        # self.deiconify()
    def checktosort(self):
        return program['status'].checktosort() #bool tosort on cur check
    def itemstosort(self):
        return program['status'].sensestosort()
    def itemssorted(self):
        return program['status'].sensessorted()
    def tosort(self):
        return program['status'].tosort() #returns bool
    def updatesortingstatus(self,**kwargs):
        return program['settings'].updatesortingstatus(**kwargs)
    def verificationcode(self,**kwargs):
        check=kwargs.get('check',program['params'].check())
        group=kwargs.get('group',program['status'].group())
        # log.info("about to return {}={}".format(check,group))
        return check+'='+group
    def __init__(self):
        super().__init__()

class Segments(Senses):
    """docstring for Segments."""
    def buildregex(self,**kwargs):
        """include profile (of those available for ps and check),
        and subcheck (e.g., a: CaC\2)."""
        """Provides self.regex"""
        profile=kwargs.get('profile',program['slices'].profile())
        if profile is None:
            log.info(_("You haven't picked a syllable profile yet."))
            return
        self.regex=self.rxdict.makeprofileforcheck(
                        profile=profile,
                        check=kwargs.get('check',program['params'].check()),
                        group=kwargs.get('group',program['status'].group()),
                        groupcomparison=getattr(self,'groupcomparison',False)
                                                    )
    def buildregexnocheck(self,**kwargs):
        """This is the same as above, but should get all senses of a profile, regardless of check and value"""
        profile=kwargs.get('profile',program['slices'].profile())
        self.regex=self.rxdict.fromCV(profile,
                            word=True, compile=True, caseinsensitive=True)
    def ifregexadd(self,regex,form,id):
        # This fn is just to make this threadable
        if regex.search(form):
            self.output+=id
    def formspsprofile(self,**kwargs):
        """I think I want to move away from this"""
        log.info(_("Asked for forms to search for a data slice (only do once!)"))
        ps=kwargs.get('ps',program['slices'].ps())
        d=program['settings'].formstosearch[ps] #{form:sense}
        # log.info("Looking at {} entries".format(len(d)))
        return {k:d[k] for k in d
                        if set(d[k]) & set(program['slices'].senses(**kwargs))}
    def sensesbyforminregex(self,regex,**kwargs):
        """This function takes in a compiled regex,
        and outputs a list of senses."""
        ps=kwargs.get('ps',program['slices'].ps())
        # log.info("Kwargs keys: {} (formstosearch n={})".format(kwargs.keys(),
        #                                 len(kwargs['formstosearch'])))
        # log.info("Reduced to {} entries".format(len(dicttosearch)))
        # log.info("Looking for senses by regex {}".format(regex))
        self.output=[s for s in program['slices'].senses(**kwargs)
                                                    # program['db'].senses
                        if s.ftypes[self.ftype].textvaluebylang(self.analang)
                        if regex.search(
                        s.ftypes[self.ftype].textvaluebylang(self.analang)
                                        )
                    ]
        # log.info("Found senses: {}".format(self.output))
        return self.output
    def presortgroups(self,**kwargs):
        if program['status'].presorted(**kwargs):
            log.info(_("Presorting for this check/slice already done! ({args})"
                        "").format(args=kwargs))
            return
        log.info(_("Presorting"))
        cvt=kwargs.get('cvt',program['params'].cvt())
        ps=kwargs.get('ps',program['slices'].ps())
        profile=kwargs.get('profile',program['slices'].profile())
        # check=kwargs.get('check',program['params'].check())
        groups=program['status'].groups(wsorted=True,**kwargs)
        groups=program['status'].groups(cvt=cvt)
        #multiprocess from here?
        msg=_("Presorting ({check}={groups})").format(check=program['params'].check(),groups=groups)
        log.info(msg)
        w=self.getrunwindow(msg=msg)
        program['status'].renewsensestosort([],[]) #will repopulate
        # test this before implementing it:
        # kwargs['formstosearch']=self.formsthisprofile(**kwargs)
        """Find all relevant senseids, remove sorted ids for each group,
        them mark the remaining senses NA, then offer them to user in
        a modified verify page (new instructions, for those that DON'T
        fit the test)"""
        self.buildregexnocheck()
        # log.info(f"(presortgroups-buildregexnocheck) "
        #         f"cvt: {cvt}, profile: {profile}, "
        #         f"check: {check}; self.regex: {self.regex}")
        unsortedids=set(self.sensesbyforminregex(self.regex,ps=ps))
        for group in [i for i in groups if not i.isdigit()]:
            self.buildregex(group=group,cvt=cvt,profile=profile)
            # log.info(f"(presortgroups-buildregex) group: {group}, cvt: {cvt}, "
            #         f"profile: {profile}, "
            #         f"check: {check}; self.regex: {self.regex}")
            s=set(self.sensesbyforminregex(self.regex,ps=ps))
            if s: #senses just for this group
                self.presort(list(s),group)
                unsortedids-=s
        log.info(_("unsortedids ({count}): {ids}").format(
                                        count=len(unsortedids),
                                        ids=unsortedids
                                        ))
        if unsortedids:
            self.presort(unsortedids,group='NA')
            program['status'].group('NA')
            self.verify() #do this here, just this once.
        program['status'].presorted(True)
        program['status'].store() #after all the above
        self.maybewrite()
        self.runwindow.waitdone()
    def presort(self,senses,group):
        ftype=program['params'].ftype()
        for sense in senses:
            t = threading.Thread(target=self.marksortgroup,
                            args=(sense,group),
                            kwargs={#'check':check,
                                    # 'ftype':ftype,
                                    })
            t.start()
        t.join()
        # program['status'].marksensesorted(sense) #now in marksortgroup
        self.updatestatus(group=group) # marks the group unverified.
    def check_with_conflicting_value(self,annodict,check):
        """This tests for data where two checks should have the same value
        (e.g., V1 or V2 and V1=V2), but don't.
        Any piece overlapping is a problem, e.g., C1=C2 must agree with C2=C3.
        """
        not_conflicting=[None, 'NA'] #these values don't conflict; move on
        if annodict[check] in not_conflicting:
            return
        checkbits=check.split('=')
        for key in [i for i in annodict.keys() if i != check]:
            if annodict[key] in not_conflicting:
                continue
            keybits=key.split('=')
            """At least one must have 2+ elements, and they must share 1+
            element, but not their value."""
            if (len(keybits+checkbits) > 2 and set(keybits)&set(checkbits) and
                                    annodict[check] != annodict[key]):
                return True
    def updateformtoannotations(self,sense,check=None,write=False):
        """This should take a sense and check, in normal usage.
        provide self.ftype prior to this
        If we want to update forms to *all* annotations, don't give check.
        Iterate across a few or many senses.
        Iterate also across ftypes, to catch them all...
        that would likely need more smarts for affix and root distinction."""
        def maybe_add_polygraph(pg):
            sc=program['params'].cvt()
            scvalue=program['settings'].polygraphs[self.analang][sc][value]
            if not scvalue:
                scvalue=True
                program['settings'].setupCVrxs() #costly; only when needed!
        def do_not_do_these(value,check=None):
            return value in ['NA',None] or (check and check.isdigit()) or value.isdigit()
        form_ori=formvalue=sense.textvaluebyftypelang(self.ftype,self.analang)
        if not formvalue:
            log.info(_("updateformtoannotations didn't return a form value for "
                    "{id}, {check}, {ftype}, {ana}").format(id=sense.id, check=check, ftype=self.ftype, ana=self.analang))
            return
        # log.info("fnode: {}; text: {}".format(fnode,t.text))
        annodict=sense.annotationvaluedictbyftypelang(self.ftype,self.analang)
        conflict_text=_("Not updating ‘{form}’ (conflict in {anno}.").format(form=formvalue, anno=annodict)
        error_nb=_("Check the log for any further conflicts")
        error=False
        if check: #just update to this annotation
            value=annodict[check]
            if value is None or value.isdigit(): #don't update to unnamed groups
                # log.info(f"Not updating {sense.id} form {formvalue} to "
                #         f"{check}={value}")
                return
            elif self.check_with_conflicting_value(annodict,check):
                if not self.updateconflictwarned:
                    ErrorNotice('\n'.join([conflict_text,error_nb]))
                    self.updateconflictwarned=True
                else:
                    log.error(conflict_text)
                return
            elif not do_not_do_these(value,check): 
                #value not in [None, 'NA']: #should I act on ''?
                formvalue=self.rxdict.update(formvalue,check,value)
                #This should update formstosearch:
                if formvalue != f:
                    program['settings'].addtoformstosearch(sense,f,formvalue)
                if len(value)>1:
                    maybe_add_polygraph(value)
        else: #update to all annotations
            for check,value in annodict.items():
                if do_not_do_these(value,check):
                    continue #don't make changes for NA checks
                elif self.check_with_conflicting_value(annodict,check):
                    if not self.updateconflictwarned:
                        ErrorNotice('\n'.join([conflict_text,error_nb]))
                        self.updateconflictwarned=True
                    else:
                        log.error(conflict_text)
                    error=True
                else:
                    log.info(f"updateformtoannotations {check}={value},{formvalue}")
                    formvalue=self.rxdict.update(formvalue,check,value)
                    log.info(f"updateformtoannotations {check}={value},{formvalue}")
        if not error:
            sense.textvaluebyftypelang(self.ftype,self.analang,formvalue)
            if form_ori != formvalue:
                key=max([int(i) for i in annodict.keys() if i.isdigit()]+[-1])+1
                sense.annotationvaluebyftypelang(self.ftype,self.analang,
                                                    str(key),form_ori)
        if write:
            self.maybewrite()
    def setitemgroup(self,item,check,group,**kwargs):
        # log.info(_("Setting segment sort group"))
        item.annotationvaluebyftypelang(self.ftype,self.analang,check,group)
    def updateformsallchecks(self):
        log.info(_("updateformsallchecks"))
        for sense in program['db'].senses: #do the whole dictionary
            self.updateformtoannotations(sense)
        #     u = threading.Thread(target=self.updateformtoannotations,
        #                         args=(sense), # w/o check, all done
        #                         )
        #     u.start()
        # try:
        #     u.join()
        # except:
        #     pass
        self.maybewrite()#after iteration
    def updateformsbycheck(self):
        for sense in self.getsensesincheck():
            u = threading.Thread(target=self.updateformtoannotations,
                                args=(sense,self.check), # w/o check, all done
                                )
            u.start()
        try:
            u.join()
        except:
            pass
        self.maybewrite()#after iteration
    def update_annotations_to_glyphs(self):
        return [i for i in [self.update_annotations_by_glyph(k)
                    for k in program['alphabet'].glyph_members()] if i]
    def update_annotations_by_glyph(self,glyph):
        """Once all sorting into groups and macrogroups is done, align groups to
        macrogroups.
        I need to think how to do this without risking merging groups:
        Go through glyph_members, and for each item with glyph≠group, change.
            if the new item exists already, rename it (int) first.
            int() groups will be renamed in iteration, since glyph≠group
        this may be more efficiently done with verification fields.
        
        This method does more than just annotations:
        
        LIFT verification,
        form data

        """
        def newform(x): #move this to alphabet
            return '_'.join(x.split('_')[:4]+[glyph])
        # log.info("update_annotations_by_glyph: checking if it is safe to "
        #         f"update items in ‘{glyph}’")
        gm=program['alphabet'].glyph_members()
        """If an annotation change would effectively join groups, e.g., Noun_CVCVC_lc_V1_ea
        would become Noun_CVCVC_lc_V1_ee, which already exists, stop. 
        """
        for item in gm[glyph]:
            #groups must be sorted before then can belong to a glyph:
            if item.split('_')[-1] in ['NA']: 
                continue
            if (item.split('_')[-1] != glyph and
                newform(item) in [i for j in gm.values() for i in j]):
                txt=_("Conflict: cannot rename ‘{item}’ to ‘{glyph}’; "
                    "‘{new}’ already exists.").format(item=item, glyph=glyph, new=newform(item))
                log.error(txt)
                return txt
        log.info(_("update_annotations_by_glyph safely: ‘{members}’ to ‘{glyph}’").format(members=gm[glyph], glyph=glyph))
        for item in list(gm[glyph]):
            kwargs=program['alphabet'].parse_verificationcode(item)
            senses=program['slices'].inslice(
                            self.getsensesincheckgroup(**kwargs),
                            **kwargs)
            # log.info(f"Found {len(senses)} senses for {item}: {[i.id for i in senses]}")
            for sense in senses: #ps-profile only
                thread_name='_'.join([sense.id,glyph])
                u = threading.Thread(target=self.marksortgroup,
                                    args=(sense,glyph),
                                    kwargs={**{k:v for k,v in kwargs.items()
                                            if k != 'group'},
                                    # remove for testing this fn:
                                    # 'nocheck': True, #no lift verify
                                            'thread_name':thread_name,
                                            'not_sorting':True,
                                            'updateverification':True,
                                            'updateforms':False}) 
                                            #update all annotations first, then forms 
                self.track_thread(thread_name) #don't race the thread
                u.start()
            program['status'].renamegroup(kwargs.pop('group'),glyph,**kwargs)
            #above should rename throughout status 
            program['alphabet'].rename_glyph_member(item,newform(item))
        self.thread_update()
        try:
            u.join()
            log.info(_("Finished update_annotations_by_glyph threads for ‘{glyph}’").format(glyph=glyph))
        except UnboundLocalError: #if u.start() never happened...
            pass
        log.info(_("update_annotations_by_glyph done with ‘{members}’ to ‘{glyph}’").format(members=gm[glyph], glyph=glyph))
    def default_glyphs(self):
        return [i for i in 
                program['alphabet'].glyphdict()[program['params'].cvt()]
                if i.isdigit()]
    def name_new_glyphs(self):
        """Everything referenced here needs to refer to macrogroups ONLY.
        Users should never be changing the name of an individual sort group.
        This method is for default named groups (int), to see that they have
        some name, and is automatically enforced.
        Changes requested by the user are handled in TranscribeC/V
        """
        glyphs=self.default_glyphs()
        program['alphabet'].glyphdict()[program['params'].cvt()]
        if program['params'].cvt() == 'C':
            transcribe=TranscribeC
        elif program['params'].cvt() == 'V':
            transcribe=TranscribeV
        else:
            log.error(_("Not sure what to do with this glyph "
                "({cvt}; {glyphs})").format(cvt=program['params'].cvt(), glyphs=glyphs))
        w=transcribe(self)
        self.withdraw()
        w.waitdone()
        problems=[]
        while digits := self.default_glyphs():
            glyph=digits[0]
            log.info(_("working on {glyph} of {digits}").format(glyph=glyph, digits=digits))
            w.makewindow(glyph)
            if w.window_failed:
                #This removes verification, thus to do status:
                program['alphabet'].mark_glyph_not_done(glyph)
                problems.append(glyph)
            elif not w.ok_done: #user exits without 'OK'
                break
        w.destroy() #just this window, not parent
        self.deiconify()
        if digits or problems:
            log.error(_("User exited with work still to do: {digits} {problems}").format(digits=digits, problems=problems))
        return not bool(digits)
    def rename_macrogroup(self,x,y,updatestatus=False):
        for item in list(program['alphabet'].glyph_members()[x]):
            kwargs=program['alphabet'].parse_verificationcode(item)
            log.info(_("Updating verification from ‘{old}’ to ‘{new}’ for {args}").format(old=x, new=y, args=kwargs))
            self.rename_group_verification(x,y,**kwargs)
        #Do the above first, before glyph_members changes
        program['alphabet'].rename_glyph(x,y)
        self.update_annotations_by_glyph(y)
        if updatestatus: #only update status if forms
            program['settings'].reloadstatusdata()
    def getsensesincheck(self):
        return [
                i for i in program['db'].senses
                if i.ftypes[self.ftype].annotationkeyinlang(self.check)
                ]
    def getsensesingroup(self,check,group):
        ftype=program['params'].ftype()
        lang=program['params'].analang()
        return [
                i for i in program['db'].senses
                if i.ftypes[ftype].annotationvaluebylang(lang,check) == group
                ]
    def getitemgroup(self,item,check):
        # ftype=program['params'].ftype() #not helpful for Tone.getitemgroup
        return item.annotationvaluebyftypelang(self.ftype,self.analang,check)
    def __init__(self, parent):
        self.updateconflictwarned=False
        self.dodone=True
        self.dodoneonly=False #don't give me other words
        self.ftype=program['params'].ftype()
        self.rxdict=program['settings'].rxdict

class WordCollection(Segments):
    """This task collects words, from the SIL CAWL, or one by one."""
    def taskicon(self):
        return program['theme'].photo['iconWord']
    def dobuttonkwargs(self):
        if program['taskchooser'].cawlmissing:
            fn=self.addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren't already in your database "
                    "(you are missing {} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(count=len(program['taskchooser'].cawlmissing))
        else:
            text=_("Add a Word")
            fn=self.addmorpheme
            tttext=_("This adds any word, but is best used after filling out a "
                    "wordlist, if the word you want to add isn't there "
                    "already.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':program['taskchooser'].theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def getlisttodo(self,**kwargs):
        """Whichever field is being asked for (self.nodetag), this fn returns
        which are left to do."""
        if hasattr(self,'byslice') and self.byslice:
            log.info(_("Limiting segment work to this slice"))
            all=[i.entry for i in program['slices'].senses()]
        else:
            all=program['db'].entries
        if program['settings'].start_at_entry:
            log.info("Starting at entry {}".format(program['settings'].start_at_entry))
            if not program['settings'].end_at_entry:
                log.info("end_at_entry not found; finishing to the end")
                program['settings'].end_at_entry=len(all)
            else:
                log.info("Ending at entry {}".format(program['settings'].end_at_entry))
            all=all[program['settings'].start_at_entry:program['settings'].end_at_entry]
            log.info("Working on {} entries".format(len(all)))
        else:
            log.info("start_at_entry not found")
        if self.dodone and not self.dodoneonly: #i.e., all data
            return all
        done=[i for i in all
                    if i.sense.textvaluebyftypelang(self.ftype,self.analang)]
        if self.dodone: #i.e., dodoneonly
            return done
        # At this point, done isn't wanted
        todo=[x for x in all if x not in done] #set-set may be better
        log.info(_("To do: ({count}) First 5: {items}").format(count=len(todo),items=todo[:5]))
        return todo
    def getinstructions(self):
        return _("Type the word in your language that goes with these meanings."
                "\nGive a single word (not a phrase) wherever possible."
                "\nJust type consonants and vowels; don't worry about tone "
                "for now.")
    def getwords(self):
        self.entries=self.getlisttodo()
        self.nentries=len(self.entries)
        self.index=0
        self.wordsframe=ui.Frame(self.frame,row=1,column=1,sticky='ew')
        self.instructions=ui.Label(self.wordsframe,
                                    text=self.getinstructions(),
                                    row=0, column=0)
        self.dirfn=self.nextword
        r=self.getword()
    def promptstrings(self,lang):
        if lang == self.analang:
            text=_("What is the form of the new "
                    "morpheme in {name} \n(consonants and vowels only)?"
                    "").format(name=program['settings'].languagenames[lang])
            ok=_('Use this form')
            skip=None
        else:
            text=_("What does ‘{form}’ mean in {lang}?").format(
                            form=self.runwindow.form[self.analang],
                            lang=program['settings'].languagenames[lang])
            ok=_("Use this {lang} gloss for ‘{form}’").format(
                            lang=program['settings'].languagenames[lang],
                            form=self.runwindow.form[self.analang])
            self.runwindow.glosslangs.append(lang)
            skip = _("Skip {lang} gloss").format(lang=program['settings'].languagenames[lang])
        return {'lang':lang, 'prompt':text, 'ok':ok, 'skip':skip}
    def submitform(self,lang):
        self.runwindow.form[lang]=self.runwindow.form[lang].get()
        self.runwindow.frame2.destroy()
    def promptwindow(self,lang):
        def skipform(event=None):
            del self.runwindow.form[lang]
            self.runwindow.frame2.destroy() #Just move on.
        strings=self.promptstrings(lang)
        self.runwindow.frame2=ui.Frame(self.runwindow.frame,
                                        row=1,column=0,
                                        sticky='ew',
                                        padx=25,pady=25)
        getform=ui.Label(self.runwindow.frame2,text=strings['prompt'],
                        font='read',row=0,column=0,
                        padx=self.runwindow.padx,
                        pady=self.runwindow.pady)
        #field rendering is better in another frame:
        eff=ui.Frame(self.runwindow.frame2,row=1,column=0)
        #variable and field for entry:
        self.runwindow.form[lang]=ui.StringVar()
        formfield = ui.EntryField(eff, render=True,
                                    text=self.runwindow.form[lang],
                                    font='readbig',
                                    row=1,column=0,
                                    sticky='')
        formfield.focus_set()
        formfield.bind('<Return>',lambda event,l=lang:self.submitform(l))
        formfield.rendered.grid(row=2,column=0,sticky='new')
        sub_btn=ui.Button(self.runwindow.frame2,text = strings['ok'],
                            command = self.submitform,
                            anchor ='c',row=2,column=0,sticky='')
        if strings['skip']:
            sub_btnNo=ui.Button(self.runwindow.frame2,
                                text = strings['skip'],
                                command = skipform,
                                row=1,column=1,sticky='')
        self.runwindow.lift()
        self.runwindow.waitdone()
        sub_btn.wait_window(self.runwindow.frame2) #then move to next step
    def addmorpheme(self):
        self.getrunwindow()
        self.runwindow.form={}
        self.runwindow.glosslangs=list()
        form={}
        self.runwindow.padx=50
        self.runwindow.pady=10
        self.runwindow.title(_("Add Morpheme to Dictionary"))
        title=_("Add {lang} morpheme to the dictionary").format(
                            lang=program['settings'].languagenames[self.analang])
        ui.Label(self.runwindow.frame,text=title,font='title',
                justify=ui.LEFT,
                anchor='c',sticky='ew',
                row=0,column=0,
                padx=self.runwindow.padx,
                pady=self.runwindow.pady)
        # Run the above script (makewindow) for each language, analang first.
        # The user has a chance to enter a gloss for any gloss language
        # already in the datbase, and to skip any as needed/desired.
        for lang in [self.analang]+program['db'].glosslangs:
            if lang in self.runwindow.form:
                continue #Someday: how to do monolingual form/gloss here
            if not self.runwindow.exitFlag.istrue():
                x=self.promptwindow(lang)
                if x:
                    return
        """get the new sense back from this function, which generates it"""
        if not self.runwindow.exitFlag.istrue(): #don't do this if exited
            self.runwindow.withdraw() #or wait?
            sense=program['db'].addentry(ps='',analang=self.analang,
                            glosslangs=self.runwindow.glosslangs,
                            form=self.runwindow.form)
            # Update profile information in the running instance, and in the file.
            self.runwindow.on_quit()
            """The following are useless without ps information, so they will
            have to come later."""
    def addCAWLentries(self):
        text=_("Adding CAWL entries to fill out, in established database.")
        self.wait(msg=text)
        log.info(text)
        self.cawldb=loadCAWL()
        added=[]
        modded=[]
        for n in program['taskchooser'].cawlmissing:
            log.info(_("Working on SILCAWL line #{line:04}.").format(line=n))
            e=self.cawldb.get('entry', path=['cawlfield'],
                                    cawlvalue='{:04}'.format(n),
                                    ).get('node')[0] #certain to be there
            try:
                eps=self.cawldb.get('sense/ps',node=e,
                                    # showurl=True
                                    ).get('node')[0]
                #This is reading values from template, which are 'Noun' & 'Verb'
                epsv=eps.get('value')
            except IndexError:
                log.info(_("line {line} w/o lexical category; leaving.").format(line=n))
                eps=epsv=None
            if epsv == 'Noun': #don't translate!
                log.info(_("Found a noun, using {ps}").format(ps=program['settings'].nominalps))
                eps.set('value',program['settings'].nominalps)
            elif epsv == 'Verb': #don't translate!
                log.info(_("Found a verb, using {ps}").format(ps=program['settings'].verbalps))
                eps.set('value',program['settings'].verbalps)
            else:
                log.error(_("Not sure what to do with ps {ps} ({node})").format(ps=epsv,node=eps))
            entry=None #in case no selected glosslangs in CAWL
            for lang in self.glosslangs:
                g=e.findall("sense/gloss[@lang='{}']/text".format(lang))
                if not g:
                    continue #don't worry about glosslangs not in CAWL
                else:
                    g=g[0].text
                """any entry with a matching gloss"""
                entry=program['db'].get('entry',gloss=g,glosslang=lang,
                                        ).get('node') #maybe []
                if entry:
                    log.info(_("Found gloss of SILCAWL line #{line:04} ({gloss}); "
                            "adding info to that entry.").format(line=n,gloss=g))
                    program['db'].fillentryAwB(entry[0],e)
                    modded.append(n)
                    break
            if not entry: #i.e., no match for any self.glosslangs gloss
                tnodes=e.findall('lexical-unit/form/text')
                for tn in tnodes:
                    tn.text=''
                log.info(_("Gloss of SILCAWL line #{line:04} ({gloss}) not found; "
                        "copying over that entry.").format(line=n,gloss=g))
                program['db'].nodes.append(e)
                added.append(n)
        if added or modded:
            program['db'].write()
            title=_("Entries Added!")
            text=_("Added {count} entries from the SILCAWL").format(count=len(added))
            if len(added)<100:
                text+=': ({})'.format(added)
            text+=_("\nModded {count} entries with new information from the "
                    "SILCAWL").format(count=len(modded))
            if len(modded)<100:
                text+=': ({})'.format(modded)
            program['taskchooser'].getcawlmissing()
            self.dobuttonkwargs()
        else:
            title=_("Error trying to add SILCAWL entries")
            text=_("We seem to have not added or modded any entries, which "
                    "shouldn't happen! (missing: {missing})"
                    "").format(missing=program['taskchooser'].cawlmissing)
        self.waitdone()
        log.info(text)
        ErrorNotice(text,title=title)
    def nextword(self,nostore=False):
        self.dirfn=self.nextword
        # log.info("running nextword (nostore = {})".format(nostore))
        if not nostore:
            # log.info("storing nextword (nostore = {})".format(nostore))
            self.storethisword()
        else:
            log.info(_("Not storing {id}, by request").format(id=self.sense.id))
        if self.index < len(self.entries)-1:
            self.index+=1
        else:
            self.index=1
        self.getword()
    def backword(self,nostore=True):
        self.dirfn=self.backword
        if not nostore:
            self.storethisword()
        else:
            log.info(_("Not storing {id}, by request").format(id=self.sense.id))
        if self.index == 0:
            self.index=len(self.entries)-1
        else:
            self.index-=1
        self.getword()
    def storethisword(self):
        log.info(_("WordCollection trying to store {value} ({type})").format(value=self.var.get(),type=self.ftype))
        try:
            if self.ftype in ['lc','lx']:
                self.sense.textvaluebyftypelang(self.ftype,
                                            self.analang,
                                            self.var.get())
            elif self.ftype == 'pl':
                self.entry.plvalue(
                    program['settings'].secondformfield[program['settings'].nominalps],
                    self.var.get())
                # lift.prettyprint(self.entry.pl)
            elif self.ftype == 'imp':
                self.entry.fieldvalue(
                        program['settings'].secondformfield[program['settings'].verbalps],
                        self.var.get())
            # self.entry.lc.textvaluebylang(self.analang,self.var.get())
            self.maybewrite() #only if above is successful
            # lift.prettyprint(self.entry)
        # except KeyError:
        except AttributeError as e:
            log.info(f"Not storing word (WordCollection): {e}")
        except AssertionError as e:
            log.info(f"Not storing empty value (WordCollection): {e} {self.var=} "
                    f"{type(self.var)=}")
        except Exception as e:
            log.info(f"Exception storing word (WordCollection): {e}")
    def markimage(self,url,w=None):
        """return to file, LIFT"""
        log.info("Selected image {}".format(url))
        if w:
            w.on_quit()
        filename=self.sense.imagename() #new file name
        saveimagefile(url,filename)
        self.sense.illustrationvalue(filename)
        self.maybewrite()
        self.wordframe.pic.reloadimage()
        self.updatereturnbind()
    def selectlocalimage(self,w=None,event=None):#w is window to close on OK
        log.info(_("Select a local image"))
        title = _("Select Example Image File"),
        filetypes=[
                ("PNG Image File",'.[Pp][Nn][Gg]'),
                ("GIF Image File",'.[Gg][Ii][Ff]'),
                ("BMP Image File",'.[Bb][Mm][Pp]'),
                ]
        f=file.askopenfilename(title=title,filetypes=filetypes)
        if f and file.exists(f):
            self.markimage(f,w)
    def showimagestoselect(self,files):
        self.imagecolumns=3
        self.imagepixels=0
        pixelopts=range(200,1000,100)
        colopts=range(1,9)
        def makegrid(cols=0,pixels=0):
            if cols:
                self.imagecolumns=iteratelistitem(colopts,
                                                    self.imagecolumns,cols)
            if pixels:
                if not self.imagepixels: #allows native resolution until tweaked
                    self.imagepixels=pixelopts[int(len(pixelopts)/2)]
                self.imagepixels=iteratelistitem(pixelopts,
                                                    self.imagepixels,pixels)
            if hasattr(self.selectionwindow,'sf'):
                self.selectionwindow.sf.destroy()
            self.selectionwindow.sf=ui.ScrollingFrame(
                        self.selectionwindow.frame,row=2,column=0)
            for n,f in enumerate(files):
                # log.info("Using row {}, col {}".format(n//cols,n%cols))
                    i=ImageFrame(self.selectionwindow.sf.content,url=f,
                                pixels=self.imagepixels,
                                row=n//self.imagecolumns,
                                column=n%self.imagecolumns,
                                sticky='nsew')
                    if i.image:
                        i.bindchildren('<ButtonRelease-1>',
                                        lambda event,x=f,w=self.selectionwindow:
                                                self.markimage(x,w))
            """activate and inactivate buttons as appropriate"""
            for t in bdict:
                if t == pixelopts:
                    val=self.imagepixels
                else:
                    val=self.imagecolumns
                for v in bdict[t]:
                    if not val or t.index(val)+v in range(0,len(t)):
                        bdict[t][v]["state"] = "normal"
                    else:
                        bdict[t][v]["state"] = "disabled"
            self.selectionwindow.update_idletasks()
        log.info(_("Select from these images: \n{files}").format(files='\n'.join(
                                                    [str(i) for i in files])))
        self.selectionwindow=ui.Window(self)
        title=_("Select a good image for {glosses}").format(glosses=self.glossesthere)
        self.selectionwindow.title(title)
        t=ui.Label(self.selectionwindow.frame,text=title, font='title',
                    row=0,column=0)
        currentimage=scaleimageifthere(self.sense)
        if currentimage:
            t['image']=currentimage
            t['compound']='right'
        imageparameters=ui.Frame(self.selectionwindow.frame,
                                row=1, column=0, sticky='e')
        fontsize='small'
        parameterseparation=10
        ui.Button(imageparameters,text=_("Browse"), font='small',
            command=lambda x=self.selectionwindow:self.selectlocalimage(w=x),
            ipady=0,row=0,column=imageparameters.ncolumns())
        ui.Label(imageparameters,text="", font=fontsize,
                    width=parameterseparation,
                    row=0,column=imageparameters.ncolumns())
        bdict={pixelopts:{},colopts:{}}
        bdict[pixelopts][-1]=ui.Button(imageparameters,text='-', font=fontsize,
                            command=lambda x=-1:makegrid(pixels=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        ui.Label(imageparameters,text=_("Image Size"), font=fontsize, padx=2,
                    row=0,column=imageparameters.ncolumns())
        bdict[pixelopts][1]=ui.Button(imageparameters,text='+', font=fontsize,
                            command=lambda x=1:makegrid(pixels=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        ui.Label(imageparameters,text="", font=fontsize,
                    width=parameterseparation,
                    row=0,column=imageparameters.ncolumns())
        bdict[colopts][-1]=ui.Button(imageparameters,text='-', font=fontsize,
                            command=lambda x=-1:makegrid(cols=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        ui.Label(imageparameters,text=_("Columns"), font=fontsize, padx=2,
                    row=0,column=imageparameters.ncolumns())
        bdict[colopts][1]=ui.Button(imageparameters,text="+", font=fontsize,
                            command=lambda x=1:makegrid(cols=x),ipady=0,
                            width=1,row=0,column=imageparameters.ncolumns())
        makegrid()
    def getimagefiles(self):
        dir=file.fullpathname(self.sense.imgselectiondir)
        if file.exists(dir):
            return dir,[i for i in file.getfilesofdirectory(dir)
                                if "terms.txt" not in str(i)]
        else:
            log.info(_("{dir} doesn't seem to exist.").format(dir=dir))
    def selectimageormoveon(self,event=None):
        if self.selectimage():
            self.nextword(nostore=False)
    def selectimage(self,event=None):
        dir,files=self.getimagefiles()
        n=len(files)
        if n >50:
            ErrorNotice(_("There are too many images to show! ({count})").format(count=n))
            files=files[:10]
        if not files:
            log.info(_("{dir} seems there, but empty.").format(dir=dir))
            self.getopenclipart()
            dir,files=self.getimagefiles()
        if files:
            self.showimagestoselect(files)
        else:
            log.info(_("There don't seem to be any images to show."))
            return 1
    def downloadallCAWLimages(self):
        for self.sense in program['db'].senses:
            if not file.exists(self.sense.imgselectiondir):
                self.getopenclipart(nogui=True)
    def getopenclipart(self,event=None,nogui=False):
        log.info(_("Not getting from openclipart.org"))
        return #this isn't really what we want right now
        if not self.sense.collectionglosses:
            log.info(_("No English glosses to search OpenClipart.org! ({glosses})").format(glosses=self.sense.glosses))
            if self.sense.imgselectiondir:
                # logic to pull English terms from folder names
                self.sense.collectionglosses=[i for i in
                                        str(self.sense.imgselectiondir).split('/')[-1].split('_')
                                        if not isinteger(i)]
        self.wait(msg=_("Dowloading images from OpenClipart.org\n{glosses}"
                        "").format(glosses=" ".join(self.sense.collectionglosses)),
                    cancellable=True)
        log.info(_("Glosses: {glosses}").format(glosses=self.sense.collectionglosses))
        scraper=htmlfns.ImageScraper()
        for gloss in self.sense.collectionglosses:
            kwargs={'per_page':50,
                    'query':gloss #just one word at a time is less restrictive
                    }
            terms=urls.urlencode(kwargs)
            url='https://openclipart.org/search/?'+terms
            # https://publicdomainvectors.org/en/search/head
            # These two are more full-colored images, rather than line drawings:
            # https://pixabay.com/images/search/head/
            # https://pxhere.com/en/photos?q=head&search=had
            try:
                html=htmlfns.getdecoded(url)
            except urls.MaxRetryError as e:
                self.waitdone()
                msg=_("Problem downloading webpage; check your "
                            "internet connection!\n\n{error}").format(error=e)
                log.error(msg)
                ErrorNotice(msg)
                return
            scraper.feed(html)
            logo=[i for i in scraper.images
                                    if 'openclipart-logo-2019.svg' in i['src']]
            # log.info("scraper.images: ({})".format(scraper.images))
            # log.info("logo: ({})".format(logo))
            if logo and logo[0] in scraper.images:
                # log.info("found logo! ({})".format(logo[0]))
                scraper.images.remove(logo[0])
        self.images=[]
        for i in scraper.images:
            if i not in self.images:
                self.images.append(i)
        log.info(_("Found {count} images: {images}").format(count=len(self.images),images=self.images))
        if self.images:
            file.makedir(self.sense.imgselectiondir)
        problems=0
        for i in self.images:
            if self.waitcancelled:
                break
            url=htmlfns.imgurl(i['src'])
            num=i['src'].split('/')[-1]
            i['filename']='_'.join([num,rx.urlok(i.get('alt','noalt'))])
            # log.info("{} ({})".format(url,i['filename']))
            log.info("{}".format(i['filename']))
            try:
                pic=htmlfns.getbinary(url, timeout=10)
                # log.info("response data type: {}".format(type(response.data)))
                i['fqdn']=file.getdiredurl(self.sense.imgselectiondir,
                                        i['filename'])
                with open(i['fqdn'],'wb') as d:
                    d.write(pic)
            except urls.MaxRetryError as e:
                log.error(_("Problem downloading image: {error}").format(error=e))
                problems+=1
            self.waitprogress(self.images.index(i)*100/len(self.images))
        if (me and not nogui) or len(self.images) < 5:
            text=_("Found {count} images!").format(count=len(self.images))
            if problems:
                text+=_("\nProblems downloading {count} images").format(count=problems)
            ErrorNotice(text,
                        button=(_("Select local image"),self.selectlocalimage))
        self.waitdone()
    def killwordframe(self):
        f=getattr(self,'wordframe',None)
        if isinstance(f,ui.Frame) and f.winfo_exists():
            # log.info("Destroying word frame")
            f.destroy()
            # log.info("Destroy done")
        # else:
        #     log.info("Not destroying word frame {}".format(isinstance(f,ui.Frame)))
        #     log.info("word frame: {}".format(f))
        #     if f:
        #         log.info("word frame exists: {}".format(f.winfo_exists()))
    def dowordframe(self):
        f=getattr(self,'wordframe',None)
        if isinstance(f,ui.Frame) and f.winfo_exists():
            # log.info("Skipping word frame; already exists!")
            return
        log.info(_("doing word frame"))
        self.wordframe=ui.Frame(self.wordsframe,row=1,column=0,sticky='ew')
        self.prog=ui.Label(self.wordframe, text='', row=1, column=3,
                            font='small')
        self.glossesline=ui.Label(self.wordframe, text='',
                                    font='read',
                                    row=1, column=0, columnspan=3, sticky='ew')
        back=ui.Button(self.wordframe,text=_("Back"),cmd=self.backword,
                        row=4, column=0, sticky='w',anchor='w')
        self.instructions2=ui.Label(self.wordframe,text='',font='small',
                        row=4, column=1, sticky='ew',anchor='c')
        next=ui.Button(self.wordframe,text=_("Next"),cmd=self.nextword,
                        row=4, column=2, sticky='e',anchor='e')
        self.var=ui.StringVar()
        self.lxenter=ui.EntryField(self.wordframe,textvariable=self.var,
                                font='readbig',
                                row=5,column=0,columnspan=3,
                                sticky='ew')
        if isinstance(self.task,Parse):
            self.parsebutton=ui.Label(self.wordframe,
                                        text=self.cparsetext,
                                        row=6, column=1,
                                        sticky='w',
                                        anchor='w')
        next.bind_all('<Up>',lambda event: self.backword(nostore=True))
        next.bind_all('<Prior>',lambda event: self.backword(nostore=True))
        next.bind_all('<Down>',lambda event: self.nextword(nostore=True))
        next.bind_all('<Next>',lambda event: self.nextword(nostore=True))
    def updatereturnbind(self):
        log.info(_("Updating binding ({state})").format(state=self.state()))
        if self.state() == 'withdrawn':
            self.unbind_all('<Return>')
        else: #only bind to non-withdrawn window
            # try: #re-institute this section once pics have good defaults
            #     assert self.wordframe.pic.hasimage
            self.lxenter.bind_all('<Return>',
                                lambda event: self.nextword(nostore=False))
            #     log.info("Return now moves to next word")
            # except AssertionError:
            #     self.wordframe.pic.bind_all('<Return>',
            #                                         self.selectimageormoveon)
            #     log.info("Return now selects image, or moves on")
    def set_up_transcription(self):
        pass
    def getword(self):
        program['taskchooser'].withdraw()# not sure why necessary
        # log.info("sensetodo: {}".format(getattr(self,'sensetodo',None)))
        # log.info("wordframe: {}".format(getattr(self,'wordframe',None)))
        # log.info("index: {}".format(self.index))
        if getattr(self,'sensetodo',None) is not None:
            # log.info("Sense to do: {}".format(self.sensetodo))
            # log.info("self.sensetodo.entry: {}".format(self.sensetodo.formatted(self.analang,self.glosslangs)))
            self.entry=self.sensetodo.entry
            self.sensetodo=None
            try:
                self.index=self.entries.index(self.entry)
            except Exception as e:
                log.info(_("self.entry doesn't seem to be in entries; OK for now"))
            self.instructions['text']=self.getinstructions() #in case changed
            self.dowordframe()
        elif not self.entries:
            text=_("It looks like you're done filling out the empty "
            "entries in your database! Congratulations! \nYou can still add words "
            "through the button on the left ({text})."
            "").format(text=self.dobuttonkwargs()['text'])
            self.killwordframe()
            self.instructions['text']=text
            self.instructions.wrap()
            return
        else:
            self.dowordframe()
            self.entry=self.entries[self.index]
        log.info(_("sensetodo: {todo}").format(todo=getattr(self,'sensetodo',None)))
        log.info(_("wordframe: {frame}").format(frame=getattr(self,'wordframe',None)))
        self.prog['text']='({}/{})'.format(self.index+1,self.nentries)
        # log.info("entries: {}".format(self.entries))
        log.info(_("index: {index}").format(index=self.index))
        self.sense=self.entry.sense
        glosses={}
        for g in set(self.glosslangs) & set(self.sense.glosses):
            glosses[g]=', '.join(self.sense.formattedgloss(g,quoted=True))
        self.glossesthere=' — '.join([glosses[i] for i in glosses if i])
        # log.info("glosses there: {}".format(self.glossesthere))
        if not self.glossesthere:
            log.info(_("entry {id} doesn't have glosses; not showing.").format(id=self.entry.get('id')))
            self.dirfn(nostore=True)
        self.glossesline['text']=self.glossesthere
        self.glossesline.wrap()
        if isinstance(getattr(self.wordframe,'pic',None),ImageFrame):
            self.wordframe.pic.changesense(self.sense)
        else:
            self.wordframe.pic=ImageFrame(self.wordframe, self.sense,
                                            pixels=300,
                                            row=2, column=0,
                                            columnspan=3, sticky='')
        self.updatereturnbind()
        """I don't want this on every ImageFrame, just here"""
        self.wordframe.pic.bindchildren('<ButtonRelease-1>', self.selectimage)
        default=self.sense.textvaluebyftypelang(self.ftype,self.analang)
        if not default:
            default=''
        self.var.set(default)
        self.set_up_transcription() #for tasks with it
        if isinstance(self.task,Parse):
            log.info(self.currentformsforuser(entry=self.entry))
            self.updateparseUI()
            if self.cparsetext.get():
                self.parsebutton.bind('<ButtonRelease-1>',
                                        lambda event,
                                        entry=self.entry:self.parse_foreground(
                                        entry=entry))
            else:
                self.parsebutton.unbind('<ButtonRelease-1>')
        self.lxenter.focus_set()
        self.frame.grid_columnconfigure(1,weight=1)
        self.deiconify()
        self.lift()
        self.wordframe.update_idletasks()
    def setcontext(self,context=None):
        TaskDressing.setcontext(self)
        self.context.menuitem(_("Show Report"),self.show_report)
    def __init__(self, parent):
        Segments.__init__(self,parent)
        self.dodone=False

class Parse(Segments):
    """docstring for Parse."""
    def getgloss(self,ftype=None):
        return ', '.join([', '.join(self.parser.sense.formattedgloss(l,
                                                            ftype=ftype,
                                                            quoted=True))
                        for l in self.glosslangs])
    def userconfirmation(self,*args):
        log.info("asking for user confirmation")
        # Return True or False only
        def do(x):
            log.info("doing {}".format(x))
            if type(x) is ui.StringVar:
                log.info("Found StringVar: {}".format(x.get()))
                self.fixroot(x.get())
                #keep userresponse.value 'False'
                self.userresponse.rootchange=True
            else:
                #The only True value here should be for "good parse, continue".
                self.userresponse.value=x
            self.l.destroy()
            # log.info("self.l destroyed")
        def enterroot():
            # log.info("Building extra root fields")
            ui.Label(self.responseframe,
                        text=_("root:"),
                        row=0,column=3,padx=(10,0),sticky='ew')
            roottext = ui.StringVar(self.responseframe, value=lx)
            self.roottextfield=ui.EntryField(self.responseframe,
                                                text=roottext,
                                                row=0,column=4,sticky='ew')
            ui.Button(self.responseframe,
                        text=_("OK"),
                        command=lambda x=roottext: do(x),
                        row=0,column=5,padx=(10,0),sticky='ew')
            self.roottextfield.bind('<Return>', lambda event,
                                                            x=roottext: do(x))
            # log.info("Extra root fields built")
            # log.info("Waiting (again)")
        def undosf():
            log.info("Running undosf")
            log.info(self.currentformnotice())
            if self.sense.psvalue() == self.nominalps: #unset value
                self.entry.plvalue(program.settings.pluralname, value=False)
            elif self.sense.psvalue() == self.verbalps:
                self.entry.fieldvalue(program.settings.imperativename,
                                            self.analang, value=False) #unset value
            program.db.write()
            log.info(self.currentformnotice())
            do(False)
        level, lx, lc, sf, ps, afxs = args
        if self.exitFlag.istrue():
            return
        w=ui.Window(self,exit=False)
        w.title(_("Confirm this combination of affixes?"))
        self.userresponse.value=False
        self.userresponse.rootchange=False
        # gloss=self.getgloss()
        # text=_("Parse looks good ({level}):").format(level=self.parser.levels()[level])
        # text+=("\n{} {}"
        #         "\n{} {}"
        #         "\n{} {}: {} ({})"
        #         ).format(#self.parser.levels()[level],
        #                 lc,afxs[0],sf,afxs[1],
        #                 ps,_("root"),lx,gloss,
        #                 )
        glosslc=self.getgloss()
        if ps == self.nominalps:
            ftype='pl'
        elif ps == self.verbalps:
            ftype='imp'
        glosssf=self.getgloss(ftype=ftype)
        self.presentationframe=ui.Frame(w.frame,row=1,column=0,sticky='ew')
        self.lcframe=ui.Frame(self.presentationframe,
                                row=0,column=0,
                                padx=10,
                                sticky='ew')
        lcmorphs=list(afxs[0])
        lcmorphs.insert(1,lx)
        self.l=ui.Label(self.lcframe,
                text='-'.join([i for i in lcmorphs if i]),font='title',
                row=0,column=0)
        ImageFrame(self.lcframe,self.sense,
                    row=1,column=0,sticky='')
        ui.Label(self.lcframe,
                text=glosslc,font='readbig',
                row=2,column=0)
        self.sfframe=ui.Frame(self.presentationframe,
                                row=0,column=1,
                                padx=10,
                                sticky='ew')
        sfmorphs=list(afxs[1])
        sfmorphs.insert(1,lx)
        ui.Label(self.sfframe,
                text='-'.join([i for i in sfmorphs if i]),font='title',
                row=0,column=1)
        ImageFrame(self.sfframe,self.sense,ftype=ftype,
                    row=1,column=1,sticky='')
        ui.Label(self.sfframe,
                text=glosssf,font='readbig',
                row=2,column=1)
        self.responseframe=ui.Frame(w.frame,row=2,column=0,sticky='ew')
        ui.Button(self.responseframe,
                    text=_("Yes!"),
                    command=lambda x=True: do(x),
                    ipadx=10,
                    row=0,column=0,sticky='nsew')
        ui.Button(self.responseframe,
                    text=_("No!"),
                    command=lambda x=False: do(x),
                    ipadx=10,
                    row=0,column=1,sticky='nsew')
        self.correctframe=ui.Frame(self.responseframe,
                                    row=0,column=2,
                                    sticky='ew',padx=(10,0))
        ui.Button(self.correctframe,
                    text=_("wrong root!"),
                    command=enterroot,
                    row=0,column=0,sticky='ew')
        ui.Button(self.correctframe,
                    text=_("wrong {field}!").format(field=self.secondformfield[self.sense.psvalue()]),
                    command=undosf,
                    row=1,column=0,sticky='ew')
        self.noticeframe=ui.Frame(w.frame,row=3,column=0)
        t=_("This parse looks good ({level})\n").format(level=self.parser.levels()[level])
        ui.Label(self.noticeframe,text=t+self.currentformnotice(),
                    font='small',justify='l',
                    row=0,column=0)
        if self.iswaiting():
            # log.info("Window almost built; unpausing")
            self.waitpause()
        # log.info("exit flag for w({}):{}; self({}):{}"
        #         "".format(w,w.exitFlag,self,self.exitFlag))
        # log.info("Window built; waiting")
        w.wait_window(self.l) #canary on label, not window
        if w.exitFlag.istrue():
            # log.info("Exited parse! (self.userresponse.value:{})"
            #         "".format(self.userresponse.value))
            self.waitdone()
            self.exited=True
        else:
            # log.info("Didn't exit parse! (self.userresponse.value:{})"
            #         "".format(self.userresponse.value))
            # w.on_quit()
            w.destroy()
            if self.iswaiting():
                self.waitunpause()
            if self.userresponse.rootchange:
                self.trythreeforms() #kick this back up a level
            else:
                # log.info("User responded {}".format(self.userresponse.value))
                return self.userresponse.value
    def selectsffromlist(self,l):
        def formattuple(l):
            pfx,sfx=l[-1]
            root=l[2]
            return '-'.join([i for i in [pfx,root,sfx] if i])
            if pfx:
                pfx+='-'
            if sfx:
                sfx='-'+sfx
            if pfx or sfx:
                rootafxs=[root,'affixes:',pfx,sfx]
            else:
                rootafxs=[root]
            return "{} ({} root: {})".format(*l[:2],' '.join(rootafxs))
        def neither():
            # These count askparsed; evaluated and moving on
            self.parsecatalog.addneither(self.parser.sense.id)
            #don't leave 'neither' with ps indication
            self.parser.sense.rmpsnode()
            # self.parser.rmpssubclassnode() #leave this for posterity?
            t.destroy()
        # log.info("Selecting from option list: {}".format(l))
        if self.exitFlag.istrue():
            return
        if self.iswaiting():
            self.waitpause()
        ln=[(i,formattuple(i)) for i in l if i[1] == self.nominalps
                        if len(i[-1]) == 2] #each must have (only) pfx and sfx
        ln+=[('ON',_("Other {field}").format(field=self.secondformfield[self.nominalps]))]
        # log.info("noun option list: {}".format(ln))
        lv=[(i,formattuple(i)) for i in l if i[1] == self.verbalps
                         if len(i[-1]) == 2] #each must have (only) pfx and sfx
        lv+=[('OV',_("Other {field}").format(field=self.secondformfield[self.verbalps]))]
        # log.info("verb option list: {}".format(lv))
        w=ui.Window(self)
        w.title(_("Select second form"))
        t=ui.Label(w.frame,
                    text=_("What is the {sfname} or {sfname2} of \n‘{lc}’ ({gloss})?"
                        "").format(
                        sfname=self.secondformfield[self.nominalps],
                        sfname2=self.secondformfield[self.verbalps],
                        lc=self.parser.entry.lcvalue(),
                        gloss=self.getgloss()
                                ),
                    font='title',
                    row=0,column=0,columnspan=2)
        t.wrap()
        if ln:
            noun=ui.Frame(w.frame, row=1, column=0, sticky='n')
            ImageFrame(noun,self.sense,ftype='pl',row=0,column=0, sticky='')
            ui.Label(noun,
                    text=_("Select {field} form").format(
                                        field=self.secondformfield[self.nominalps]),
                    row=1,column=0,
                    columnspan=2)
            bfn=ui.ScrollingButtonFrame(noun, optionlist=ln, window=t,
                                        command=self.parser.dooneformparse,
                                        row=2, column=0,
                                        columnspan=2
                                        )
        if lv:
            verb=ui.Frame(w.frame, row=1, column=1, sticky='n')
            ImageFrame(verb,self.sense,ftype='imp',row=0,column=0, sticky='')
            ui.Label(verb,
                    text=_("Select {field} form").format(
                                        field=self.secondformfield[self.verbalps]),
                    row=1,column=0)
            bfv=ui.ScrollingButtonFrame(verb, optionlist=lv, window=t,
                                        command=self.parser.dooneformparse,
                                        row=2, column=0)
        neitherb=ui.Button(w.frame, text=_("Neither"),
                        command=neither,
                        row=1, column=2, sticky='ns')
        ui.Label(w.frame,text=self.currentformnotice(),
                    font='small',justify='l',
                    row=2,column=0,columnspan=3)
        w.bind_all('<Escape>', lambda event:w.on_quit)
        w.wait_window(t)
        if w.exitFlag.istrue():
            self.exited=True
        # w.on_quit()
        w.destroy()
        if self.iswaiting():
            self.waitunpause()
    def asksegmentsnops(self):
        for ps in [self.nominalps, self.verbalps]:
            r=self.asksegments(ps=ps)
            if r in [None,1] or self.exited: #i.e., returned OK or not this ps
                break
    def asksegmentsotherps(self):
        pss=[i for i in [self.nominalps, self.verbalps]
                    if i != self.parser.sense.psvalue()]
        for ps in pss:
            self.asksegments(ps=ps)
    def updateparseUI(self):
        self.cparsetext.set(self.currentformsforuser(entry=self.entry))
    def currentformsforuser(self,entry=None):
        if entry is not None:
            self.parser.entry=entry
            self.parser.sense=entry.sense
        lx,lc,pl,imp = self.parser.texts()
        if lx:
            return _("{root}: {forms} ({ps}), {sfname}: {forms2}"
                ).format(root_val=lx,
                        forms=''.join([i for i in [pl,imp] if i]),
                        forms2=''.join([i for i in [pl,imp] if i]), # Wait, this logic was weird in original: ''.join([i for i in [pl,imp] if i]) was used for the second {}
                        root=_("Root"),
                        ps=self.parser.sense.psvalue(),
                        sfname=self.secondformfield[self.nominalps] if pl
                        else self.secondformfield[self.verbalps]
                        )
        if lc and (pl or imp):
            return _("Citation: {citation}, {sfname}: {forms}"
                ).format(citation=lc,
                        forms=''.join([i for i in [pl,imp] if i]),
                        # root=_("root"),
                        # ps=self.parser.sense.psvalue(),
                        sfname=self.secondformfield[self.nominalps] if pl
                        else self.secondformfield[self.verbalps]
                        )
        if lc:
            return _("Citation: {citation}").format(citation=lc)
        else:
            return ""
    def currentformnotice(self):
        lx, lc, pl, imp = self.parser.texts()
        return _("currently: ")+("{lx} ({ps} {root}), {lc}, {pl} ({pl_name}), {imp} ({imp_name})"
                ).format(lx=lx, lc=lc, pl=pl, imp=imp,
                        root=_("root"),
                        ps=self.parser.sense.psvalue(),
                        pl_name=self.secondformfield[self.nominalps],
                        imp_name=self.secondformfield[self.verbalps]
                        )
    def asksegments(self,ps=None):
        def do(event=None):
            self.parser.sense.psvalue(ps)
            if ps == self.nominalps:
                # tag='pl'
                fn=self.parser.entry.plvalue
            elif ps == self.verbalps:
                # tag='imp'
                fn=self.parser.entry.impvalue
            # lift.prettyprint(self.parser.entry.imp)
            # lift.prettyprint(self.parser.entry.pl)
            # log.info("value: {}".format(segments.get()))
            # lift.prettyprint(self.parser.entry.imp)
            # lift.prettyprint(self.parser.entry.pl)
            fn(self.secondformfield[ps],segments.get())
            # log.info("v: {}".format(fn(self.secondformfield[ps],self.analang)))
            # self.parser.nodetextvalue(tag,segments.get())
            b.destroy()
        def next(event=None):
            segments.set("")
            b.destroy()
            # w.on_quit()
        if self.exitFlag.istrue():
            return
        if not ps:
            return asksegmentsnops()
        log.info("asking for second form segments for ‘{}’ ps: {} ({}; {})"
                "".format(self.parser.entry.lcvalue(),
                            ps,self.parser.sense.id,
                            self.parsecatalog.parsen()))
        sfname=self.secondformfield[ps]
        if self.iswaiting():
            self.waitpause()
        w=ui.Window(self)
        w.title(_("Type second form"))
        l=ui.Label(w.frame,
                text=_("What {sfname} form goes with ‘{lc}’ ({gloss})?"
                    "").format(sfname=sfname,
                            lc=self.parser.entry.lcvalue(),
                            gloss=self.getgloss()),
                font='title',
                row=0,column=0,columnspan=2)
        l.wrap()
        if ps == self.nominalps:
            ftype='pl'
        elif ps == self.verbalps:
            ftype='imp'
        ImageFrame(w.frame,self.parser.sense,ftype=ftype,row=0,column=2)
        segments=ui.StringVar()
        segments.set(self.parser.entry.lcvalue())
        e=ui.EntryField(w.frame,text=segments,
                        row=2,column=0)
        b=ui.Button(w.frame,text=_("OK"),cmd=do,
                        row=3,column=0, sticky='e')
        ui.Button(w.frame,text=_("Not a {ps}").format(ps=ps),cmd=next,
                        row=3,column=1, sticky='e')
        ui.Label(w.frame,text=self.currentformnotice(),
                    font='small',justify='l',
                    row=4,column=0,columnspan=2)
        e.focus_set()
        e.bind('<Return>',do)
        w.wait_window(b)
        if w.exitFlag.istrue():
            self.exited=True
        if self.iswaiting():
            self.waitunpause()
        segments_ok=bool(segments.get())
        w.destroy()
        if not segments_ok:
            return 1
        elif not self.exited:
            self.trytwoforms()
    def done(self):
        lx, lc, pl, imp = self.parser.texts()
        ps=self.parser.sense.psvalue()
        log.info("Currently working with lx: {}, lc: {}, pl: {}, imp: {}, ps: "
                "{}".format(lx,lc,pl,imp,ps))
        log.info("Done: {}".format(bool(lx)&bool(lc)&(
                                    bool(pl)|bool(imp))&
                                    bool(ps)))
        return bool(lx)&bool(lc)&(bool(pl)|bool(imp))&bool(ps)
    def tryoneform(self):
        log.info("Asking for second form selected (parse w/one form)")
        r=self.parser.oneform()
        # log.info("r: {}".format(r))
        # log.info("psvalue: {}".format(self.parser.sense.psvalue()))
        if r:
            self.selectsffromlist(r)
            log.info("Done selecting from {}".format(r))
        #User responding "neither noun nor verb" gives no psvalue, so stop here.
        if not self.exited and not self.done() and self.parser.sense.psvalue():
            self.tryaskform()
    def trytwoforms(self):
        log.info("Trying for parse with two forms")
        r=self.parser.twoforms()
        # return level, lx, lc, sf, self.ps, afxs #from self.parser.twoforms
        if not r:
            log.info("Auto parsed {} with two forms".format(self.sense.id))
            return
        elif isinstance(r,tuple) and self.userconfirmation(*r):
            self.parser.doparsetolx(r[1],*r[4:]) #pass root, too
        elif not isinstance(r,tuple) and r > 1:
            log.info("I need to figure out what to do with suppletive forms!")
            return
        if (not self.exited and
            not self.done() and
            # rootchange kicks back, so just finish here on rootchange:
            not self.userresponse.rootchange):
            self.tryoneform()
    def trythreeforms(self):
        log.info("Trying for parse with three forms")
        r=self.parser.threeforms()
        #This gives r= tuple to check, or 1 if skipped. no UI = no self.exit set
        # log.info("reponse: {} ({})".format(r,type(r)))
        if not r:
            log.info("Auto parsed {} with three forms (returned {})"
                    "".format(self.sense.id,r))
            return
        elif isinstance(r,tuple) and self.userconfirmation(*r):
                # return level, lx, lc, sf, self.ps, afxs #from self.parser.threeforms
            log.info("Confirmed parsing of ‘{}’ root from ‘{}’ and ‘{}’ as {}"
                        "".format(*r[1:5]))
            log.info("adding {} affix set {}".format(*r[4:]))
            self.parser.addaffixset(*r[4:])#self.ps,afxs)
            self.parser.sense.pssubclassvalue(r[-1])
            return
        else:
            log.info(f"No parse (trythreeforms).")
        log.info(f"{self.exited=}")
        log.info(f"{self.done()=}")
        log.info(f"{self.userresponse.rootchange=}")
        if (not self.exited and
            not self.done() and
            # rootchange kicks back, so just finish here on rootchange:
            not self.userresponse.rootchange):
            self.trytwoforms()
        log.info("Finished trying three forms")
    def fixroot(self,root):
        log.info("Fixing Root {} > {}".format(
                            self.parser.entry.lxvalue(),
                            root))
        self.parser.entry.lxvalue(root) #setting
        self.updateparseUI()
    def parse_foreground(self,**kwargs):
        self.withdraw()
        self.updatereturnbind()
        self.userresponse.rootchange=False #reset for each root
        self.parse(**kwargs)
        self.updateparseUI()
        if self.iswaiting():
            self.waitdone()
        if self.winfo_exists():
            self.deiconify()
            self.updatereturnbind()
    def parse(self,**kwargs):
        # These functions return nothing when the parse goes through, 1 when
        # not done. If the user exits, self.exited is set
        self.exited=False
        r=True #i.e., do the next fn
        if not kwargs:
            kwargs={
                'sense':self.sense
                }
        self.parser.parseentry(**kwargs) #sets entry, sense, and sense.id for parser
        log.info("lx: {}, lc: {}, pl: {}, imp: {}".format(*self.parser.texts()))
        if min(self.parser.auto, self.parser.ask) <= 4:# and not badps:
            r=self.trythreeforms() #other functions will be triggered from here.
        else:
            log.info("Not parsing; auto: {}, ask: {}".format(self.parser.auto,
                                                            self.parser.ask))
        # badps is OK here, but don't do twoforms if threeforms worked
            # log.info("trytwoforms returned {}".format(r))
            # log.info("tryoneform returned {}".format(r))
            # log.info("Asking for second form typed")
    def tryaskform(self):
        try:
            r=self.asksegments(ps=self.parser.sense.psvalue())
            if r == 1:
                r=self.asksegmentsotherps()
                assert r != 1
        except Exception as e:
            log.info("Exeption: {}".format(e))
            self.asksegmentsnops()
        if not self.exited:
            self.submitparse()
    def submitparse(self):
        try:
            self.parsecatalog.addparsed(self.sense.id)
        except: #upgrade to this
            self.parsecatalog.addparsed(kwargs['entry'].sense.id)
        self.maybewrite()
    def initsensetodo(self):
        try:
            r=self.sensetodo
            self.sensetodo=None
        except AttributeError:
            if hasattr(self,'sensetodo'):
                log.info("self.sensetodo: {}".format(self.sensetodo.id))
            r=self.sensetodo=None
        if r:
            return [r] #only return this once.
        else:
            return [] #list, either way
    def sensestoparse(self,senses=None,all=False,n=-1): #n/limit=-1#1000
        s=self.initsensetodo()# This returns and resets
        if s:
            return s
        if not senses:
            senses=program.db.senses[:n]
        if all:
            return senses #if provided, assume all
        else:
            try:
                return set(senses)-set(self.parsecatalog.parsed)
            except AttributeError:
                return set(senses)
    def getparses(self,**kwargs):
        log.info("parses already tried: {}".format(self.parsecatalog.parsen()))
        self.wait(_("Parsing (ask: {ask} auto: {auto})").format(ask=self.parser.ask,
                                                        auto=self.parser.auto
                                                    ))
        senses=self.sensestoparse(**kwargs)
        todo=len(senses)
        for n,self.sense in enumerate(senses):
            self.parse() #this can add to lists
            if self.exited:
                break
            if self.iswaiting():
                self.waitprogress(100*n//todo)
            # else:
            #     break
        self.waitdone()
        # log.info("total parses tried: {}".format(self.parsecatalog.parsen()))
        self.parsecatalog.report()
    def nextparserasklevel(self):
        auto=self.parser.auto
        ask=self.parser.ask
        if ask:
            ask-=1 #start a new level with user confirmations
        log.info("Moving to parser levels auto: {} ask: {}".format(auto,ask))
        self.parser.setlevels(auto=auto,ask=ask)
    def nextparserautolevel(self):
        auto=self.parser.auto
        ask=self.parser.ask
        if auto:
            auto-=1 #catch up automation (stop asking at this level)
        log.info("Moving to parser levels auto: {} ask: {}".format(auto,ask))
        self.parser.setlevels(auto=auto,ask=ask)
    def initparsecatalog(self):
        # like if there is a bad affix making bad autoparses...
        self.pss=program.db.pss
        self.parsecatalog=self.parent.parsecatalog=parser.Catalog(self)
        collector=parser.AffixCollector(self.parsecatalog,program.db)
        if self.loadfromlift:
            self.wait(_("Loading Affixes"))
            # for i in collector.do():
            for i in collector.getfromlift():
                # log.info("Progress: {}".format(i))
                self.waitprogress(i)
            self.parsecatalog.report()
            self.waitdone()
    def showwhenready(self):
        try:
            assert self.status.winfo_exists()
            log.info("showing")
            self.deiconify()
        except:
            log.info("not showing")
            self.after(1,self.showwhenready)
    def storethisword(self):
        log.info(_("Parse trying to store {value} ({type})").format(value=self.var.get(),type=self.ftype))
        try:
            v=self.var.get()
            assert v
            self.entry.fields[self.ftype].textvaluebylang(self.analang,v)
            if not self.done():
                self.parse_foreground(entry=self.entry)
            self.maybewrite() #only if above is successful
            self.updateparseUI()
            log.info(f"Storing word: {self.sense.id} ({self.analang}:{v})")
        except AssertionError as e:
            log.info(f"Not storing empty value (Parse): {e} {self.var=} "
                    f"{type(self.var)=}")
        except AttributeError as e:
            log.info(f"Not storing word (Parse): {e}")
        except Exception as e:
            log.info(f"Exception storing word (Parse): {e}")
    def waitforOKsecondfields(self):
        while not program.settings.secondformfieldsOK():
            after(10*100,callback=self.waitforOKsecondfields) # wait a second
    def __init__(self, parent): #frame, filename=None
        self.byslice=False
        self.initsensetodo()
        Segments.__init__(self,parent)
        self.parent=parent
        self.secondformfield=program.settings.secondformfield
        self.nominalps=program.settings.nominalps
        self.verbalps=program.settings.verbalps
        self.loadfromlift=True
        # program.settings.makesecondformfieldsOK() #do elsewhere
        if hasattr(parent,'parsecatalog'):
            self.parsecatalog=parent.parsecatalog
        else:
            self.initparsecatalog()
        if hasattr(parent,'parser'):
            self.parser=parent.parser
        else:
            self.parser=parent.parser=parser.Engine(self.parsecatalog,self)
            #These should come from settings
            self.parser.autolevel(5) #no auto
            self.parser.asklevel(0)
        self.ftype=program.params.ftype('lc') #Is this always correct?
        # self.ftype=program.params.ftype('lx') #I think once we parse, we want this
        # self.nodetag='citation'
        self.dodone=True #give me words with citation done
        self.checkeach=False #don't confirm each word (default)
        self.dodoneonly=True #don't give me other words
        self.userresponse=Object(rootchange=False,value=False)
        self.cparsetext=ui.StringVar() #store UI parse info here
        self.showwhenready()

class Tone(Senses):
    """This keeps stuff used for Tone checks."""
    def makeanalysis(self,**kwargs):
        """was, now iterable, for multiple reports at a time:"""
        if not hasattr(self,'analysis'):
            self.analysis=Analysis(self.program, **kwargs)
        else:
            self.analysis.setslice(**kwargs)
    def checkforsensestosort(self,cvt=None,ps=None,profile=None,check=None):
        """This method just asks if any sense in the given slice is unsorted.
        It stops when it finds the first one."""
        """use if sorting sense lists aren't needed"""
        """This is redundant with updatesortingstatus()"""
        if cvt is None:
            cvt=program.slices.cvt()
        if ps is None:
            ps=program.slices.ps()
        if profile is None:
            profile=program.slices.profile()
        if check is None:
            check=program.slices.check()
        senses=program.slices.senses(ps=ps,profile=profile)
        vts=False
        for sense in senses:
            if sense.tonevaluebyframe(self,frame):
                vts=True
                break #This is just a True/False for the group, not lists
        program.status.dictcheck(cvt=cvt,ps=ps,profile=profile,check=check)
        program.status.tosort(vts,cvt=cvt,ps=ps,profile=profile,check=check)
    def settonevariablesiterable(self,cvt='T',ps=None,profile=None,check=None):
        """This is currently called in iteration, but doesn't refresh groups,
        so it probably isn't useful anymore."""
        self.checkforsensestosort(cvt=cvt,ps=ps,profile=profile,check=check)
    def settonevariables(self):
        """This is currently called before sorting. This is a waste, if you're
        not going to sort afterwards –unless you need the groups."""
        self.updatesortingstatus() #this gets groups, too
    def addframe(self,**kwargs):
        if 'window' in kwargs:
            kwargs['window'].destroy() #in any case; if fails, try again.
        self.withdraw()
        t=ToneFrameDrafter(self)
        if not t.exitFlag.istrue():
            self.wait_window(t)
    def aframe(self):
        self.runwindow.on_quit()
        self.addframe()
        self.addwindow.wait_window(self.addwindow)
        self.runcheck()
    def presortgroups(self):
        #simpler than calling and uncalling..…
        pass
    def updateformtoannotations(self,*args,**kwargs):
        #simpler than calling and uncalling..…
        pass
    def setitemgroup(self,item,check,group,**kwargs):
        """ftype should be set at the beginning of work and not changed often,
        so shouldn't need to be specified here
        """
        # """here kwargs should include framed, if you want this to update the
        # form information in the example"""
        ps=item.psvalue()
        # log.info("Setting tone sort group")
        # if not ftype:
        #     log.error("No field type!")
        #     return
        try:
            """Fine if check isn't there; will be caught with exception"""
            # providing both ftype and frame isn't necessary, but allows check
            # that they align:
            assert check in item.examples
            f=item.formattedform(self.analang,self.ftype,
                                program.toneframes[ps][check])
            # log.info("Setting form to {}".format(f))
            item.examples[check].textvaluebylang(
                                    lang=self.analang,
                                    value=f)
            log.info("Setting tone sort group to ‘{}’".format(group))
            item.examples[check].tonevalue(group)
            for g in (set(self.glosslangs)& #selected
                        set(program.toneframes[ps][check])& #defined
                        set(item.ftypes[self.ftype])): # form in lexicon
                for f in item.formattedgloss(g,
                                        program.toneframes[ps][check])[:1]:
                    # log.info("Setting {} translation to {}".format(g,f))
                    item.examples[check].translationvalue(g,f)
            item.examples[check].lastAZTsort()
        except (KeyError,AssertionError) as e:
            # log.info(f"Adding a new example to store ‘{check}’ values ({e})")
            item.newexample(check,
                            program.toneframes[ps][check],
                            self.analang,
                            self.glosslangs,
                            group)
        # log.info("Done setting tone sort group")
    def getsensesinUFgroup(self,group):
        return [
                i for i in program.db.senses
                if i.uftonevalue() == group
                ]
    def getsensesingroup(self,check,group):
        return [
                i for i in program.db.senses
                if i.tonevaluebyframe(check) == group
                ]
    def getitemgroup(self,item,check):
        """This works without ftype, as each frame only has one"""
        return item.tonevaluebyframe(check)
    def getUFgroupofsense(self,sense):
        return sense.uftonevalue()
    def name_new_glyphs(self):
        pass
    def __init__(self,program):
        self.program=program

