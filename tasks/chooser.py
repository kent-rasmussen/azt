# coding=UTF-8
import sys
import threading
import time
from frontend import ui
from tasks.base import Task
from tasks.tasks import (Sound, SortV,
    ExportData, AlphabetChart, AlphabetComparisonPages,
    ReportCitationBackground, ReportCitationMulticheckBackground,
    ReportCitationMultichecksliceBackground,
    ReportCitationTBackground, ReportCitationTLBackground,
    ReportCitationMultisliceTBackground, ReportCitationMultisliceTLBackground,
    ReportCitationByUFBackground, ReportCitationByUFMulticheckBackground,
    ReportCitationByUFMultichecksliceBackground,
    WordCollectionCitation, WordCollectionCitationwRecordings,
    WordCollectnParse, WordCollectnParsewRecordings, RecordCitation,
    SortSyllables, SortC, SortT, RecordCitationT,
    WordsParse, TranscribeV, TranscribeC, TranscribeT,
    JoinUFgroups, ReportConsultantCheck)
from frontend.ui_shell import LiftChooser
from utilities.utilities import sysrestart, sysshutdown, openweburl
from utilities.i18n import _
from utilities import file
from utilities import logsetup
log=logsetup.getlog(__name__)


from utilities.error_handler import notify_error as ErrorNotice
class TaskChooser(Task):
    """This class stores the hierarchy of tasks to do in A-Z+T, plus the
    minimum and optimum prerequisites for each. Based on these, it presents
    to the user a default (highest in hierarchy without optimum fulfilled)
    task on opening, and allows users to choose others (any with minimum
    prequisites satisfied)."""
    do_not_show_slices=True
    is_chooser=True
    no_leaderboard=True
    def tasktitle(self):
        if self.showreports:
            return _("Run Reports")
        elif self.datacollection:
            return _("Data Collection Tasks")
        else:
            return _("Analysis & Decision Tasks")
    def dobuttonkwargs(self):
        pass
    def choosereports(self):
        self.status.bigbutton.destroy()
        self.showreports=True
        self.i_am_mainwindow()
        self.gettask()
    def guidtriage(self): #obsolete
        # import time
        log.info(_("Doing guid triage and other variables —this takes awhile..."))
        start_time=nowruntime()
        self.guids=self.program.db.guids
        self.guidsinvalid=[] #nothing, for now...
        print(len(self.guidsinvalid),'entries with invalid data found.')
        self.program.db.guidsinvalid=self.guidsinvalid
        self.guidsvalid=[]
        for guid in self.guids:
            if guid not in self.guidsinvalid:
                self.guidsvalid+=[guid]
        print(len(self.guidsvalid),'entries with valid data remaining.')
        self.guidswanyps=self.program.db.get('guidwanyps') #any ps value works here.
        print(len(self.guidswanyps),'entries with ps data found.')
        self.guidsvalidwops=[]
        self.guidsvalidwps=[]
        for guid in self.guidsvalid:
            if guid in self.guidswanyps:
                self.guidsvalidwps+=[guid]
            else:
                self.guidsvalidwops+=[guid]
        self.program.db.guidsvalidwps=self.guidsvalidwps #This is what we'll search
        print(len(self.guidsvalidwops),'entries with valid data but no ps data.')
        print(len(self.guidsvalidwps),'entries with valid data and ps data.')
        # for var in [self.guids, self.guidswanyps, self.guidsvalidwops, self.guidsvalidwps, self.guidsinvalid, self.guidsvalid]:
        #     print(len(var),str(var))
        # for guid in self.guidswanyps:
        #     if guid not in self.formstosearch[self.analangs[0]][None]:
        #         guids+=[guid]
        # print(len(guids),guids)
        logfinished(start_time)
    def guidtriagebyps(self): #obsolete
        log.info(_("Doing guid triage by ps... This also takes awhile?..."))
        self.guidsvalidbyps={}
        """use self.program.db.entriesbyps or self.program.db.sensesbyps"""
        for ps in self.program.db.pss:
            self.guidsvalidbyps[ps]=self.program.db.get('guidbyps',ps=ps)
    def gettask(self,event=None):
        """This function pulls user out of a task, to select from any
        of tasks whose prerequisites are minimally satisfied."""
        self.ui.withdraw()
        self.i_am_mainwindow()
        if self.program.task and self.task.ui.winfo_exists():
            self.program.task.ui.on_quit()
        self.whatsdone()
        if not hasattr(self.ui,'notebook'):
            self.ui._build_chooser_tabs(self.makeoptions_for,self.maketask)
        else:
            self.ui._populate_chooser_tabs()
        # Select the right tab
        if self.showreports:
            self.ui._select_chooser_tab('reports')
            self.showreports=False
            self.showingreports=True
        elif self.showingreports:
            self.showingreports=False
        else:
            self.ui._select_chooser_tab('datacollection')
        self.ui.deiconify()
    def makedefaulttask(self):
        """This function makes the task after the highest optimally
        satisfied task"""
        """The above is prerequisite to the below, so it is here. It could be
        elsewhere, but that led to numerous repetitions."""
        optionlist=self.makeoptions()
        # task,title,icon
        log.info(_("starting from option list {options}").format(options=optionlist))
        optionlist=[i for i in optionlist if not issubclass(i[0],Sound)]
        # log.info("getting default from option list {}".format(
        #                                             [i[1] for i in optionlist]))
        if self.program.testing and hasattr(self.program,'testtask'):
            self.maketask(self.program.testtask)
        else: #we need better logic here
            if SortV in [i[0] for i in optionlist]:
                self.maketask(SortV)
            else:
                self.maketask(self.program.default_task)
                #optionlist[-1][0]) #last item, the code
    def finish_task_ui(self):
        # self.unsetmainwindow() # not redundant; fires without gettask
        try:
            self.program.task.ui.on_quit() #destroy and set flag
            self.program.task=None #don't look for this again
        except AttributeError as e:
            log.info(_("No task, apparently; not destroying {e}.").format(e=e))
    def maketask(self,taskclass,**kwargs): #,filename=None
        if type(taskclass) is str:
            import tasks.tasks
            taskclass=getattr(tasks.tasks, taskclass)
        taskclass(program=self.program,**kwargs) #filename
    def i_am_mainwindow(self):
        if not self.ui.mainwindow:
            self.ui.i_am_mainwindow()
            self.finish_task_ui()
    def makeoptions_for(self,category):
        """Return task tuples for the given category."""
        if category == 'reports':
            tasks=[
                    ExportData,
                    AlphabetChart,
                    AlphabetComparisonPages,
                    ReportCitationBackground,
                    ReportCitationMulticheckBackground,
                    ReportCitationMultichecksliceBackground
                    ]
            if self.doneenough['sortT']:
                tasks.append(ReportCitationTBackground)
                tasks.append(ReportCitationTLBackground)
                tasks.append(ReportCitationMultisliceTBackground)
                tasks.append(ReportCitationMultisliceTLBackground)
            if self.doneenough['analysis']:
                tasks.append(ReportCitationByUFBackground)
                tasks.append(ReportCitationByUFMulticheckBackground)
                tasks.append(ReportCitationByUFMultichecksliceBackground)
        elif category == 'datacollection':
            tasks=[
                    WordCollectionCitation,
                    WordCollectionCitationwRecordings,
                    WordCollectnParse,
                    WordCollectnParsewRecordings,
                    RecordCitation
                    ]
            if self.doneenough['collectionlc']:
                tasks.append(SortSyllables)
                tasks.append(SortV)
                tasks.append(SortC)
                tasks.append(SortT)
                if self.doneenough['sortT']:
                    tasks.append(RecordCitationT)
        else: # analysis
            tasks=[WordsParse]
            if self.doneenough['sort']:
                tasks.append(TranscribeV)
                tasks.append(TranscribeC)
            if self.doneenough['sortT']:
                tasks.append(TranscribeT)
            if self.doneenough['analysis']:
                tasks.append(JoinUFgroups)
            if self.program.me:
                tasks.append(ReportConsultantCheck)
        tasktuples=[]
        photos=self.program.theme.photo
        for task in tasks:
            title=_(task.tasktitle) if task.tasktitle else _("Unnamed {name} Task ({type})"
                    ).format(name=self.program.name,type=task.__name__)
            icon=photos.get(task.taskicon) if task.taskicon else None
            tasktuples.append((task,title,icon))
        log.info(_("Tasks available for \u2018{category}\u2019 ({count}): {tasks}").format(
                    category=category,count=len(tasktuples),
                    tasks=[i[1] for i in tasktuples]))
        return tasktuples
    def makeoptions(self):
        """Returns options for current category. Used by makedefaulttask."""
        self.whatsdone()
        if self.showreports:
            return self.makeoptions_for('reports')
        elif self.datacollection:
            return self.makeoptions_for('datacollection')
        else:
            return self.makeoptions_for('analysis')
    def convertlxtolc(self,window):
        try:
            window.destroy()
            backup=self.program.filename+'_backupBeforeLx2LcConversion'
            self.program.db.write(backup)
            self.program.db.convertlxtolc()
            # self.program.db.write(self.file.name+str(now()))
            self.program.db.write()
            conversionlogfile=logsetup.writelzma()
            ErrorNotice(_("The conversion is done now, so {name} will quit. You may "
                    "want to inspect your current file ({file}) and the backup "
                    "({backup}) to confirm this did what you wanted, before "
                    "opening {name} again. In case there are any issues, the "
                    "log file is also saved in {log}").format(name=self.program.name,
                                                file=self.program.filename,
                                                backup=backup,
                                                log=conversionlogfile),
                    title=_("Conversion Done!"),
                    wait=True)
            self.program.restart()
        except Exception as e:
            ErrorNotice(_("There was a problem converting fields as you asked; you "
                "should fix this before moving on."))
    def asktoconvertlxtolc(self):
        title=_("Convert lexeme field data to citation form fields?")
        url='{}/CITATIONFORMS.md'.format(self.program.docsurl)
        w=ui.Window(self.program.tk_root,title=title,exit=False)
        lexemesdone=list(self.program.db.nentrieswlexemedata.values())#[self.program.settings.analang]
        citationsdone=list(self.program.db.nentrieswcitationdata.values())#[self.program.settings.analang]
        nbtext1=_("You have {lexemes} entries with lexeme data, and only {citations} with "
                "citation data.").format(lexemes=lexemesdone,citations=citationsdone)
        instructions=_("Typically, dictionary work starts by collecting "
                        "citation forms, and later moves to analyzing those "
                        "forms into lexemes (meaningful, but not necessarily "
                        "pronounceable, word parts). Sometimes, people store "
                        "those citation forms in lexeme fields, though this "
                        "is typically in error. {name} can help you analyze your "
                        "citation forms into lexeme forms, but they first need "
                        "to be moved to the correct fields in your database."
                        "").format(name=self.program.name)
        Question=_("Do you want {name} to move data from your lexeme fields to "
                    "citation fields, for each entry with no citation field "
                    "data?").format(name=self.program.name)
        infot=_("See {url} for more information.").format(url=url)
        oktext=_("Move lexeme field data to citation fields")
        noktext=_("No thanks; I’ll manage this myself")
        nbtext=_("N.B.: This is a fairly radical change to your database, "
                "so it would be wise to back up your data.")
        noktttext=_("You will need to do this yourself, either in FLEx, or "
                    "with expert help.")
        lt=ui.Label(w.frame, text=title, font='title',
                    row=0, column=0, columnspan=2)
        nb=ui.Label(w.frame, text=nbtext1, font='default',
                    row=1, column=0, columnspan=2)
        # li=ui.Label(w.frame, text=instructions, font='instructions',
        #             row=2, column=0, columnspan=2)
        lq=ui.Label(w.frame, text=Question, font='read',
                    row=3, column=0, columnspan=2)
        bok=ui.Button(w.frame, text=oktext,
                        font='instructions',
                        cmd=lambda w=w:self.convertlxtolc(w),
                        row=4, column=0)
        bok.tt=ui.ToolTip(bok,instructions)
        bnok=ui.Button(w.frame, text=noktext,
                        font='instructions',
                        cmd=w.destroy, row=4, column=1)
        bnok.tt=ui.ToolTip(bnok, text=noktttext)
        lnb=ui.Label(w.frame, text=nbtext, row=5, column=0, columnspan=2)
        info=ui.Label(w.frame, text=infot, font='default',
                    row=7, column=0, columnspan=2)
        info.tt=ui.ToolTip(info, text=_("go to {url}").format(url=url))
        info.bind('<Button-1>', lambda e: openweburl(url))
        for l in [lt,nb,lq,lnb]:
            l.wrap()
        return w
    def getcawlmissing(self):
        cawls=self.program.db.get('cawlfield/form/text').get('text')
        # log.info("CAWL ({}): {}".format(len(cawls),cawls))
        self.cawlmissing=[]
        for i in range(1700):
            if '{:04}'.format(i+1) not in cawls:
                self.cawlmissing.append(i+1)
        if len(self.cawlmissing) < 10:
            log.info(_("CAWL missing ({count}): {missing}").format(count=len(self.cawlmissing),
                                                        missing=self.cawlmissing))
    def whatsdone(self):
        """I should probably have a roundtable with people to discuss these
        numbers, to see that we agree the decision points are rational."""
        #This should probably not be redone entirely each time a task is done
        self.donew={} # last is default to show user
        self.doneenough={} # which options the user *can* see
        for taskreq in ['collectionlc','parsedlx','collectionplimp',
                    'tonereport',
                    # 'torecord',
                    # 'torecordT',
                    'recorded',
                    'recordedT',
                    'sortT',
                    'sort',
                    'sortlc',
                    'torecord',
                    'torecordT',
                    'analysis'
                    ]:
            self.donew[taskreq]=False
            self.doneenough[taskreq]=False
        nentries=self.program.db.nguids
        lexemesdone=self.program.db.nentrieswlexemedata
        citationsdone=self.program.db.nentrieswcitationdata
        log.info("lexemesdone by lang: {}".format(lexemesdone))
        log.info("citationsdone by lang: {}".format(citationsdone))
        # There should never be more lexemes than citation forms.
        for l in lexemesdone:
            if not self.program.settings.askedlxtolc and (l not in citationsdone
                                or citationsdone[l] < lexemesdone[l]):
                w=self.asktoconvertlxtolc()
                w.wait_window(w) # wait for this answer before moving on
                self.program.settings.askedlxtolc=True
                self.program.settings.storesettingsfile()
                break #just ask this once
        self.getcawlmissing()
        log.info("nfields in db: {}".format(self.program.db.nfields))
        log.info("wannotations in db: {}".format(self.program.db.nfieldswannotations))
        sorts={k:v for (k,v) in self.program.db.nfields.items()
                                            if 'sense/example' in v}
        sorts.update({k:v for (k,v) in self.program.db.nfieldswannotations.items()
                                            if 'sense/example' not in v})
        # log.info("nfields by lang (updated): {}".format(sorts))
        sortsrecorded=self.program.db.nfieldswsoundfiles
        log.info("nfieldswsoundfiles by lang: {}".format(sortsrecorded))
        sortsnotrecorded={}
        log.info(f"sorts: {sorts}")
        if self.program.me:
            enough=0
        else:
            enough=6 #for demonstrating; is 25 a reasonable minimum?
        # log.info("looking at sorts now: {}".format(sorts))
        for l in sorts:
            if self.program.db.audiolang:
                al=self.program.db.audiolang
            else:
                maybeals=[i for i in self.program.db.audiolangs if l in i]
                if maybeals:
                    al=maybeals[0]
                    log.info(_("Using audiolang {audio} for analang {analang}")
                                .format(audio=al,analang=l))
                else:
                    log.info(_("Couldn’t find plausible audiolang (among {audios}) "
                        "for analang {analang}").format(audios=self.program.db.audiolangs,analang=l))
            if al not in sortsrecorded:
                sortsrecorded[al]={}
            sortsnotrecorded[l]={}
            for f in sorts[l]:
                """I don't think I can faithfully distinguish between
                sorting on lc v other fields here, at least not yet"""
                if f == 'sense/example':
                    #sorting is never done; mark when the top slices are done?
                    if sorts[l][f] >= enough: #what is a reasonable number here?
                        self.doneenough['sortT']=True
                else:
                    if sorts[l][f] >= enough: #what is a reasonable number here?
                        self.doneenough['sort']=True
                #This is a bit of a hack, but no analang nor audiolang yet.
                if f not in sortsrecorded[al]:
                    sortsrecorded[al]={f:0}
                sortsnotrecorded[l][f]=sorts[l][f]-sortsrecorded[al][f]
                if f == 'sense/example':
                    if not sortsnotrecorded[l][f]:
                        self.donew['recordedT']=True
                    if sortsrecorded[al][f] >= enough:
                        self.doneenough['recordedT']=True
                    # Needed? Any time sorting is done, show recording
                    # if not sortsrecorded[f][al]:
                    #     self.donew['torecordT']=True
                    if sortsnotrecorded[l][f] < enough:
                        self.doneenough['torecordT']=True
                else:
                    if not sortsnotrecorded[l][f]:
                        self.donew['recorded']=True
                    if sortsrecorded[al][f] >= enough:
                        self.doneenough['recorded']=True
                    #see above
                    if sortsnotrecorded[l][f] < enough:
                        self.doneenough['torecord']=True
                # log.info("Finished looking at [{}]{} field: {}".format(l,f,self.doneenough))
                log.info(_("Finished looking at [{lang}]{field} field: {status}").format(lang=l, field=f, status=self.doneenough))
        # log.info("nfieldswosoundfiles by lang: {}".format(sortsnotrecorded))
        for lang in self.program.db.nentrieswlexemedata:
            remaining=self.program.db.nentrieswcitationdata[lang
                                        ]-self.program.db.nentrieswlexemedata[lang]
            if not remaining:
                self.donew['parsedlx']=True
            if remaining < 100:
                self.doneenough['parsedlx']=True
                break
        for lang in citationsdone:
            if nentries-citationsdone[lang] < 50 and not len(self.cawlmissing):
                self.donew['collectionlc']=True
            if citationsdone[lang] > 200: #was 705
                self.doneenough['collectionlc']=True#I need to think through this
            # log.info("checking '{}'".format(f))
        for f in [i for j in self.program.db.sensefieldnames.values() for i in j]:
            if 'verification' in f:
                # log.info("Found 'verification' in '{}'".format(f))
                #I need to tweak this, it should follow tone (only) reports:
                #maybe read this from status?
                #This ideally follows transcription
                #This should maybe be relevant by slice (analyzed or not yet)
                self.doneenough['analysis']=True
                break
            # log.info("'verification' not in '{}'".format(f))
        log.info(_("Analysis of what you’re done with: {status}").format(status=self.donew))
        log.info(_("You’re done enough with: {status}").format(status=self.doneenough))
    def bulk_transcribe(self):
        """Stage-2 bulk ASR over every recording (Advanced menu)."""
        from tasks.bulk_asr import BulkASR
        BulkASR(self.program).run()
    def changedatabase(self):
        log.debug("Preparing to change database name.")
        try:
            self.program.task.withdraw() #so users don't do stuff while waiting
        except (AttributeError, Exception):
            log.info(_("There doesn’t seem to be a task to hide; moving on."))
        curname = self.program.filename
        log.info(_("Current database: {name}").format(name=curname))
        # window=LiftChooser(self,file.getfilenames())
        window=LiftChooser(self.program)
        # LiftChooser can close itself during setup (e.g. selection made, or the
        # window destroyed); wait_window() on a gone widget raises TclError
        # ("bad window path name") and killed changedatabase. Only wait if it's
        # still alive.
        try:
            if window.winfo_exists():
                window.wait_window(window)
        except Exception as e:
            log.info(_("LiftChooser already closed; not waiting ({e})").format(e=e))
        # LiftChooser stores the selection in program.filename
        # (setfilenameandcontinue); TaskChooser has no filename attribute.
        newname=self.program.filename
        # text=_("{name} will now exit; restart to work with the new database."
        #         "").format(name=self.program.name)
        # ErrorNotice(text,title=_("Change Database"),wait=True)
        # self.program.tk_root.destroy()
        # subprocess.call?
        # __name__
        # main()
        log.info(_("Current database: {name}").format(name=newname))
        if newname and curname != newname:
            log.info(_("User selected a new database; restarting with it."))
            self.program.restart()
        else:
            log.info(_("User didn’t select a new database; continuing."))
            self.program.task.deiconify()
        # self.restart(self.filename)
    def usbcheck(self):
        if self.program.splash.exitFlag.istrue():
            return
        self.program.splash.withdraw()
        for r in self.program.data_repo.values():
            # log.info("checking repo {} for USB drive".format(r))
            #on boot, pull in changes becore committing
            r.share(noclone=True,nocommit=True)
        self.program.splash.draw()
    def on_quit(self,**kwargs):
        super().on_quit(**kwargs)
        self.parent.on_quit(**kwargs)
    # def getinterfacelangs(self):
    # # global i18n
    #     return [{'code':i,'name':self.program.settings.languagenames[i]}
    #             for i in self.program.interfacelangs]
    # # {'code':'fr','name':'Français'},
    # #         {'code':'en','name':'English'},
    # #         {'code':'fub','name':'Fulfulde'}
    # #         ]
    def __init__(self,program):
        self.program=program
        self.program.taskchooser=self
        self.program.task=None #so far; make this attribute there, though
        self.datacollection=True # everyone starts here?
        self.showreports=False
        self.showingreports=False
        assert hasattr(self.program,'settings')
        # self.interfacelangs=self.getinterfacelangs()
        self.program.splash.progress(55)
        # self.program.settings.post_lift_init()
        self.program.splash.progress(65)
        self.whatsdone()
        self.program.splash.progress(80)
        log.info(_("Settings: {settings}").format(settings=self.program.settings))
        super().__init__(self.program, withdrawn=True) #don't show first on boot
        # self.ui.i_am_mainwindow()
        # TaskDressing.__init__(self,parent) #I think this should be after settings
        self.program.profiles.run()
        # self.withdraw()
        self.program.splash.progress(90)
        if self.program.tk_root.exitFlag.istrue():
            return
        # self.guidtriage() #sets: self.guidswanyps self.guidswops self.guidsinvalid self.guidsvalid
        # self.guidtriagebyps() #sets self.guidsvalidbyps (dictionary keyed on ps)
        """Can whatsdone be joined with makedefaulttask? they appear together
        elsewhere."""
        self.program.splash.maketexts() #update for translation change
        self.usbcheck()
        if self.program.nosound:
            e=_("You don’t have the sound module installed. For best use of {name},"
                "you should switch back to the main branch, connect to the "
                "internet, and restart. In the mean time. You won’t be able "
                "to record or play audio!"
                ).format(name=self.program.name)
            ErrorNotice(e)
        self.program.splash.progress(100)
        if self.program.splash.exitFlag.istrue():
            sysshutdown()
        self.program.splash.destroy()
        self.maxprofiles=5 # how many profiles to check before moving on to another ps
        self.maxpss=2 #don't automatically give more than two grammatical categories
        log.info(_("done setting up taskChooser"))
        self.makedefaulttask() #normal default
        # self.gettask() # let the user pick
        """Do I want this? Rather give errors..."""
