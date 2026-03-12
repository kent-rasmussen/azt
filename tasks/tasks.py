# coding=UTF-8
from frontend import ui_tkinter as ui
from tasks.base import Task
from backend.core.report_mixins import Multislice, MultisliceS, MultisliceT, Multicheck, Multicheckslice, ByUF, Background
from backend.reporting.generator import Report
from backend.core.lexicon import WordCollection, Parse, Tone, Segments
from backend.core.sorting_engine import Sort
from utilities.utilities import *
from utilities import file, logsetup, rx
from io_put import export
from tasks.alphabet_chart import AlphabetChart
from tasks.alphabet_comparison import AlphabetComparisonPages
from utilities.utilities import LazyGlobal
log = logsetup.getlog(__name__)

def __getattr__(name):
    if name in ('_', 'ErrorNotice', 'nn', 'unlist', 'sysrestart',
                'sysshutdown', 'SortGroupButtonFrame', 'SortGlyphGroupButtonFrame',
                'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame',
                'ResultWindow', 'Alphabet', 'FileParser', 'sound', 'sound_ui',
                'transcriber', 'exampletype', 't'):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

for name in ('_', 'ErrorNotice', 'nn', 'unlist', 'sysrestart',
             'sysshutdown', 'SortGroupButtonFrame', 'SortGlyphGroupButtonFrame',
             'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame',
             'ResultWindow', 'Alphabet', 'FileParser', 'sound', 'sound_ui',
             'transcriber', 'exampletype', 't'):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

class ExportData(ui.Window):
    """docstring for ExportData."""
    def taskicon(self):
        return self.program.theme.photo['USBdrive']
    def tooltip(self):
        return _("This tells you how much data you could export now, and "
                    "allows you to export it.")
    def tasktitle(self):
        return _("Export Data")
    def dobuttonkwargs(self):
        text=_("Export Data")
        tttext=_("This tells you how much data you could export now, and "
                    "allows you to export it.")
        return {'text':text,
                # 'fn':pass,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.taskchooser.theme.photo['USBdrive'],
                'sticky':'ew',
                'tttext':tttext
                }
    def on_quit(self):
        ui.Window.on_quit(self)
        self.program.taskchooser.gettask()
    def switch(self,event=None):
        if self.exportclass == export.Lexicon:
            self.exportclass=export.Examples
        else:
            self.exportclass=export.Lexicon
        self.report_data()
    def do_export(self,event=None):
        self.done_notice=ui.Label(self.frame,
                                    text=_("In Progress..."),
                                    anchor='c',padx=50,
                                    row=4,column=0,columnspan=2,sticky='we'
                                )
        for i in self.export.export():
            self.progress(i*100)
        self.progress(100)
        self.done_notice['text']=_("Done!\n(saved to {dir})").format(dir=self.export.save_dir)
    def report_data(self,check=None,event=None):
        if hasattr(self,'button') and isinstance(self.button,dict):
            for i in self.button.values():
                i.destroy()
            del self.button
        for o in ['info','button',
                    'export_button', 'switch_button',
                    'done_notice']:
            try:
                getattr(self,o).destroy()
            except:
                pass
        self.update()
        self.export=self.exportclass(
                lift=self.program.db,
                analang=self.program.params.analang(),
                audiolang=self.program.params.audiolang(),
                audiodir=self.program.settings.audiodir,
                save_dir=self.program.settings.exportsdir,
                check=check,
                max_rows_total=self.max_rows_total,
                max_rows_per_file=self.max_rows_per_file,
                )
        self.info=ui.Label(self.frame,
            text=_("Checking work done..."),
            anchor='c',padx=50,
            row=0,column=0,sticky='we'
        )
        self.button_frame=ui.Frame(self.frame,
                                    row=2,column=0,
                                    )
        self.progress(0,self.frame,row=3,column=0)
        for i in self.export.report():
            self.progress(i*100)
        self.info['text']=self.export.info
        self.export_button=ui.Button(self.button_frame,
                text=_("Export"),
                anchor='c',padx=50,
                row=0,column=1,sticky='we'
        )
        if self.exportclass == export.Lexicon:
            self.switch_button=ui.Button(self.button_frame,
                    text=_("Check Examples"),
                    anchor='c',padx=50,
                    row=0,column=0,sticky='w'
            )
            if self.slices:
                allchecks=self.program.status.allcheckswCVdata()
                self.button={c:ui.Button(self.button_frame,
                                        text=_("Just {check} data").format(check=c),
                                        anchor='c',padx=50,
                                        row=allchecks.index(c)+1,
                                        column=0,sticky='w'
                                        )
                        for c in allchecks
                            }
                for c in self.button:
                    self.button[c].bind("<Button-1>",
                                        lambda event,x=c: self.report_data(x))

        else:
            self.switch_button=ui.Button(self.button_frame,
                    text=_("Check Lexicon"),
                    anchor='c',padx=50,
                    row=0,column=0,sticky='w'
            )
        self.export_button.bind("<Button-1>",self.do_export)
        self.switch_button.bind("<Button-1>",self.switch)
    def __init__(self, arg):
        self.exportclass=export.Lexicon
        title=(_("{azt} Data Export").format(azt=self.program.name))
        ui.Window.__init__(self,self.program.root, title=title)
        self.slices=False #allow user to output data for each check
        self.max_rows_total=None
        self.max_rows_per_file=None
        self.report_data()
class Sound(object):
    """This holds all the Sound methods, mostly for playing."""
    settings_attrs=['fs', 'sample_format',
                    'audio_card_out']
    def donewpyaudio(self):
        try:
            self.pyaudio.terminate()
        except:
            log.info(_("Apparently self.pyaudio doesn't exist, or isn't initialized."))
    def pyaudiocheck(self):
        try:
            self.pyaudio.pa.get_format_from_width(1) #just check if its OK
        except:
            self.pyaudio=sound.AudioInterface()
    def makesoundsettings(self):
        if not hasattr(self.program.settings,'soundsettings'):
            log.info("Making new soundsettings object")
            self.program.settings.soundsettings=sound.SoundSettings(self.pyaudio,
                        analang_obj=self.program.languages.get_obj(self.analang)
                        )
    def loadsoundsettings(self):
        self.makesoundsettings()
        self.program.settings.loadsettingsfile(setting='soundsettings')
        self.program.soundsettings=self.program.settings.soundsettings
        if self.program.hostname == 'karlap' and (
                        'cache_dir' not in self.program.soundsettings.asr_kwargs
                        ):
            self.program.soundsettings.asr_kwargs[
                                            'cache_dir']='/media/kentr/hfcache'
    def storesoundsettings(self):
        self.program.settings.storesettingsfile(setting='soundsettings')
    def quittask(self):
        self.soundsettingswindow.destroy()
        self.program.taskchooser.gettask()
        self.on_quit()
    def soundsettingscheck(self):
        if not hasattr(self.program.settings,'soundsettings'):
            self.loadsoundsettings()
    def missingsoundattr(self):
        # log.info(dir(self.program.settings.soundsettings))
        ss=self.program.settings.soundsettings
        for s in self.settings_attrs:
            if hasattr(ss,s):
                if s+'s' in ss.hypothetical and (getattr(ss,s)
                                                not in ss.hypothetical[s+'s']):
                    log.info(_("Sound setting {setting} invalid; asking again").format(setting=s))
                    return True
                elif 'audio_card' in s and (getattr(ss,s)
                                                    not in ss.cards['dict']):
                    log.info(_("Sound setting {setting} invalid; asking again").format(setting=s))
                    return True
            else:
                log.info(_("Missing sound setting {setting}; asking again").format(setting=s))
                return True
        self.program.settings.soundsettingsok=True
    def soundcheck(self):
        #just make sure settings are there
        self.soundsettingscheck()
        self.soundsettings=self.program.settings.soundsettings
        self.soundsettings.check()
        if not self.exitFlag.istrue() and self.missingsoundattr():
            self.mikecheck() #if not, get them
            return
    def audioexists(self,relfilename):
        return file.exists(self.audioURL(relfilename))
    def audioURL(self,relfilename):
        return str(file.getdiredurl(self.audiodir,relfilename))
    def hassoundfile(self,node,recheck=False):
        """sets self.audiofileisthere and maybe self.audiofileURL"""
        return node.hassoundfile(recheck)
    def _configure_sound(self,event=None):
        sound_ui.SoundSettingsWindow(self)
    def setcontext(self,context=None):
        if hasattr(super(), 'setcontext'):
            super().setcontext(context)
        self.context.menuitem(_("Sound settings"),self._configure_sound)
        self.analang=self.program.db.analang
    def __init__(self,):
        self.audiodir=self.program.settings.audiodir
        self.audiolang=self.program.params.audiolang()
        self.program=program #make available to sound_ui
        self.soundcheck()
class Record(Sound): #TaskDressing
    """This holds all the Sound methods specific for Recording."""
    settings_attrs=['audio_card_in']+Sound.settings_attrs
    def makelabelsnrecordingbuttons(self,parent,node,r,c):
        # log.info("Making buttons for {} (in {})".format(node,parent))
        t=node.formatted(self.analang,self.glosslangs)
        lxl=ui.Label(parent, text=t,row=r,column=c+1,sticky='w')
        lcb=sound_ui.RecordButtonFrame(parent,self,node,
                                        row=r,column=c,sticky='w')
    def cleanup_pa(self,parentframe):
        import gc
        for w in parentframe.content.winfo_children():
            if type(w) is sound_ui.RecordButtonFrame:
                w.recorder.streamclose()
                w.player.streamclose()
        parentframe.destroy() #for now, at least
        gc.collect()
    def showentryformstorecordpage(self):
        #The info we're going for is stored above sense, hence guid.
        if self.runwindow.exitFlag.istrue():
            log.info(_('no runwindow; quitting!'))
            return
        if not self.runwindow.frame.winfo_exists():
            log.info(_('no runwindow frame; quitting!'))
            return
        self.runwindow.resetframe()
        ps=self.program.slices.ps()
        profile=self.program.slices.profile()
        count=self.program.slices.count()
        text=_("Record {profile} {ps} Words: click ‘Record’, talk, "
                "and release ({count} words)").format(profile=profile,ps=ps,
                                                count=count)
        log.info(text)
        instr=ui.Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        senses=self.program.slices.senses(ps=ps,profile=profile)
        if not senses: #i.e., no profile analysis yet
            senses=self.program.db.senses
        nperpage=5
        pages=[senses[i:i+nperpage] for i in range(0,len(senses),nperpage)]
        log.info(_("pages: {pages}").format(pages=pages))
        for page in pages:
            if self.runwindow.exitFlag.istrue():
                return
            self.runwindow.wait(thenshow=True)
            buttonframes=ui.ScrollingFrame(self.runwindow.frame,
                                            row=1,column=0,sticky='w')
            row=0
            done=list()
            # log.info("Looking through entries now")
            for row,entry in enumerate([i.entry for i in page]):
                self.runwindow.column=0
                if entry.guid in done: #only the first of multiple senses
                    continue
                else:
                    done.append(entry.guid)
                """These following two have been shifted down a level, and will
                now return a list of form elements, each. Something will need to be
                adjusted here..."""
                ftypes=['lc','pl','imp']
                # for f in ftypes:
                #     log.info(f"{f}: {entry.sense.nodebyftype(f)}, "
                #                 f"{type(entry.sense.nodebyftype(f))}")
                for node in [entry.sense.nodebyftype(f) for f in ftypes
                                if entry.sense.nodebyftype(f)]:
                    self.runwindow.column+=2
                    # sense['nodetoshow']=sense[node]
                    self.makelabelsnrecordingbuttons(buttonframes.content,node,
                        row,self.runwindow.column)
                # row+=1
            # log.info("Done iterating for one page")
            ui.Button(buttonframes.content,column=1,row=row,
                        text=_("Next {count} words").format(count=nperpage),
                        cmd=lambda x=buttonframes:self.cleanup_pa(x))
            # log.info("Showing waitwindow now")
            self.runwindow.waitdone()
            buttonframes.wait_window(buttonframes)
        if not self.runwindow.exitFlag.istrue():
            self.runwindow.wait_window(self.runwindow.frame)
    def showentryformstorecord(self,justone=False):
        # Save these values before iterating over them
        #Convert to iterate over local variables
        self.getrunwindow()
        if justone or not self.program.slices.valid():
            self.showentryformstorecordpage()
        else:
            #store for later
            ps=self.program.slices.ps()
            profile=self.program.slices.profile()
            for psprofile in self.program.slices.valid(): #self.profilecountsValid:
                if self.runwindow.exitFlag.istrue():
                    return 1
                self.program.slices.ps(psprofile[1])
                self.program.slices.profile(psprofile[0])
                nextb=ui.Button(self.runwindow,text=_("Next Group"),
                                        cmd=self.runwindow.resetframe) # .frame.destroy
                nextb.grid(row=0,column=1,sticky='ne')
                self.showentryformstorecordpage()
            #return to initial
            self.program.slices.ps(ps)
            self.program.slices.profile(profile)
        self.donewpyaudio()
    def showsenseswithexamplestorecord(self,senses=None,progress=None,skip=False):
        def setskip(event):
            self.runwindow.frame.skip=True
            entryframe.destroy()
        self.getrunwindow()
        if self.exitFlag.istrue() or self.runwindow.exitFlag.istrue():
            return
        log.debug("Working with skip: {}".format(skip))
        if skip == 'skip':
            self.runwindow.frame.skip=True
        else:
            self.runwindow.frame.skip=skip
        text=_("Words and phrases to record: click ‘Record’, talk, and release")
        instr=ui.Label(self.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w',columnspan=2)
        if (getattr(self.program.settings, 'entriestoshow', None) is None) and (senses is None):
            ui.Label(self.runwindow.frame, anchor='w',
                    text=_("Sorry, there are no entries to show!")).grid(row=1,
                                    column=0,sticky='w')
            return
        if self.runwindow.frame.skip == False:
            skipf=ui.Frame(self.runwindow.frame)
            skipb=ui.Button(skipf,
                        text=rx.linebreakwords(_("Skip to next undone")),
                        cmd=skipf.destroy)
            skipf.grid(row=1,column=1,sticky='w')
            skipb.grid(row=0,column=0,sticky='w')
            skipb.bind('<ButtonRelease-1>', setskip)
        if senses is None:
            senses=self.program.settings.entriestoshow
        for sense in senses:
            log.debug("Working on {} with skip: {}".format(sense.id,
                                                    self.runwindow.frame.skip))
            examples=list(sense.examples.values())
            if examples == []:
                log.debug(_("No examples! Add some, then come back."))
                continue
            if ((self.runwindow.frame.skip == True) and
                (lift.atleastoneexamplehaslangformmissing(examples,
                                    self.program.settings.audiolang) == False)):
                continue
            row=0
            if self.runwindow.exitFlag.istrue():
                return 1
            entryframe=ui.Frame(self.runwindow.frame)
            entryframe.grid(row=1,column=0)
            if progress is not None:
                progressl=ui.Label(self.runwindow.frame, anchor='e',
                    font='small',
                    text='({} {}/{})'.format(*progress)
                    )
                progressl.grid(row=0,column=2,sticky='ne')
            """This is the title for each page: isolation form and glosses."""
            text=sense.formatted(self.analang,self.glosslangs)
            if not text:
                entryframe.destroy() #is this ever needed?
                continue
            ui.Label(entryframe, anchor='w', font='read',
                    text=text).grid(row=row,
                                    column=0,sticky='w')
            """Then get each sorted example"""
            self.runwindow.frame.scroll=ui.ScrollingFrame(entryframe)
            self.runwindow.frame.scroll.grid(row=1,column=0,sticky='w')
            examplesframe=ui.Frame(self.runwindow.frame.scroll.content)
            examplesframe.grid(row=0,column=0,sticky='w')
            # examples.reverse()
            for example in examples:
                if (skip == True and
                    lift.examplehaslangform(example,self.program.settings.audiolang) == True):
                    continue
                # """These should already be framed!"""
                text=example.formatted(self.analang,self.glosslangs)
                if not text:
                    #Don't show the whole dictionary of frames here:
                    log.info(_("Not showing example with text {text}").format(text=text))
                    continue
                row+=1
                """If I end up pulling from example nodes elsewhere, I should
                probably make this a function, like getframeddata"""
                if not text:
                    exit()
                rb=sound_ui.RecordButtonFrame(examplesframe,self,example)
                rb.grid(row=row,column=0,sticky='w')
                ui.Label(examplesframe, anchor='w',text=text
                                        ).grid(row=row, column=1, sticky='w')
            row+=1
            d=ui.Button(examplesframe, text=_("Done/Next"),command=entryframe.destroy)
            d.grid(row=row,column=0)
            self.runwindow.waitdone()
            examplesframe.wait_window(entryframe)
            if self.runwindow.exitFlag.istrue():
                return 1
            if self.runwindow.frame.skip == True:
                return 'skip'
    def showtonegroupexs(self):
        def next():
            self.program.status.nextprofile()
            self.runwindow.on_quit()
            self.showtonegroupexs()
        if (not(hasattr(self,'examplespergrouptorecord')) or
            (type(self.examplespergrouptorecord) is not int)):
            self.examplespergrouptorecord=100
            self.program.settings.storesettingsfile()
        self.makeanalysis()
        self.analysis.donoUFanalysis()
        torecord=self.analysis.sensesbygroup
        ntorecord=len(torecord) #number of groups
        nexs=len([k for i in torecord for j in torecord[i] for k in j])
        nslice=self.program.slices.count()
        log.info(_("Found {analyzed} analyzed of {total} examples in slice").format(analyzed=nexs, total=nslice))
        skip=False
        if ntorecord == 0:
            log.error(_("How did we get no UR tone groups? {profile}-{ps}"
                    "\nHave you run the tone report recently?"
                    "\nDoing that for you now...").format(
                            profile=self.program.slices.profile(),
                            ps=self.program.slices.ps()
                                                         ))
            self.analysis.do()
            self.showtonegroupexs()
            return
        batch={}
        # log.info(f"self.program.db.sensedict ({len(self.program.db.sensedict)}): "
        #         f"{self.program.db.sensedict}")
        for i in range(self.examplespergrouptorecord):
            batch[i]=[]
            for ufgroup in torecord:
                print(i,len(torecord[ufgroup]),ufgroup,torecord[ufgroup])
                if len(torecord[ufgroup]) > i: #no done piles.
                    # sense=[self.program.db.sensedict[torecord[ufgroup][i]]] #list of one
                    sense=torecord[ufgroup][i] #list of one
                else:
                    print("Not enough examples, moving on:",i,ufgroup)
                    continue
                log.info(_('Giving user the number {count} example from tone '
                        'group {group}').format(count=i,group=ufgroup))
                exited=self.showsenseswithexamplestorecord([sense],
                            (ufgroup, i+1, self.examplespergrouptorecord),
                            skip=skip)
                if exited == 'skip':
                    skip=True
                if exited == True:
                    return
        if not (self.runwindow.exitFlag.istrue() or self.exitFlag.istrue()):
            self.runwindow.waitdone()
            self.runwindow.resetframe()
            ui.Label(self.runwindow.frame, anchor='w',font='read',
            text=_("All done! Sort some more words, and come back.")
            ).grid(row=0,column=0,sticky='w')
            ui.Button(self.runwindow.frame,
                    text=_("Continue to next syllable profile"),
                    command=next).grid(row=1,column=0)
        self.donewpyaudio()
    def filenameoptions(self,node):
        # This depends on self.analang and self.program.slices.profile; otherwise, it
        # could be moved to a FieldParent method
        """This should generate possible filenames, with preferred (current
        schema) last, as that will be used if none are found."""
        log.info(_("Looking for file names for {node} ({tag})").format(node=node, tag=node.tag))
        ps=self.program.slices.ps()
        print("ps:",ps)
        if ps:
            pslocopts=[ps]
        else:
            pslocopts=[]
        # Except for data generated early in 2021, profile should not be there,
        # because it can change with analysis. But we include here to pick up
        # old files, in case they are there but not linked.
        # First option (legacy):
        # pslocopts.insert(0,ps+'_'+self.parent.taskchooser.slices.profile())
        profile=self.program.slices.profile()
        if ps and profile:
            pslocopts.insert(0,ps+'_'+profile)
        fieldlocopts=[None] #none is OK
        try:
            l=node.locationvalue()
            #the last option is taken, if none are found
            pslocopts.insert(0,ps+'-'+l) #the first option.
            fieldlocopts.append(l) #make this the last option.
        except AttributeError:
            # log.info(_("doesn't look like an example node; not offering location"))
            pass
                    # Yes, these allow for location to be present twice, but
                # that should never be found, nor offered
        if not pslocopts:
            pslocopts=[None] #make this an iterable, none is OK
        filenames=[]
        """We iterate over lots of filename schemas, to preserve legacy data.
        This is only really needed (and so could be removed at some point) when
        data has been recorded but no link is in place, for whatever reason.
        If there is a link to a real sound file, that is covered above.
        If there is no sound file, then the below will result in the default
        (current) schema."""
        form=node.textvaluebylang(self.analang)
        if not form:
            log.error(_("filenameoptions: no {ana} analang in "
                "{id}! (OK if recording first; "
                "forms: {forms})").format(ana=self.analang,
                id=node.sense.id,
                forms=node.textvaluedict()))
        # log.info("forms at this point: {}".format(self.forms))
        for pslocopt in pslocopts:
            for fieldlocopt in fieldlocopts: #for older name schema
                for legacy in ['_', None]:
                    for tags in [ None, 1 ]:
                        args=[node.sense.id]
                        if tags:
                            args+=[node.tag]
                            if node.tag == 'field':
                                args+=[node.ftype]
                        args+=[form] #[self.ftype]]
                        for l in self.glosslangs:
                            args+=[node.glossbylang(l)]
                        optargs=args[:]
                        optargs.insert(0,pslocopt) #put first
                        optargs.insert(3,fieldlocopt) #put after self.node.tag
                        # log.info("optargs: {}".format(optargs))
                        wavfilename='_'.join([x for x in optargs if x])
                        if legacy == '_': #There was a schema that had an extra '_'.
                            wavfilename+='_'
                        wavfilename=rx.urlok(wavfilename) #one character check
                        filenames+=[wavfilename+'.wav']
        return filenames
    def makeaudiofilename(self,node):
        """If node is already marked with sound file attributes, we're done"""
        if self.hassoundfile(node):
            return
        """Otherwise, generate prioritized list of name options"""
        filenames=self.filenameoptions(node)
        """if any of the generated filenames are there, stop at the first one"""
        for f in filenames:
            if self.audioexists(f):
                log.info(_("Audiofile {file} found at {url}").format(file=f, url=self.audioURL(f)))
                node.textvaluebylang(lang=self.program.params.audiolang(),value=f)
                if self.hassoundfile(node,recheck=True):
                    log.info("file {} linked in LIFT".format(node.audiofileURL))
                break
        """If none found, be ready to write with last/highest priority option"""
        f=filenames[-1]
        log.debug(_("No audio file found, but ready to record: "
                    )+"{file}; {url_label}:{url}".format(file=f, url_label=_("url"), url=self.audioURL(f)))
        """Should be able to just send f"""
        node.audiofilenametoput=f #don't write this until we actually record
        node.audiofileURL=self.audioURL(f)
        log.info(_("Finishing makeaudiofilename with {file} "
                "and {url}").format(file=node.audiofilenametoput, url=node.audiofileURL))
    def mikecheck(self):
        """This starts and stops the UI"""
        self.withdraw()
        self.pyaudiocheck()
        #will need to add sound_ui in here, once generalized:
        self.soundsettingswindow=sound_ui.SoundSettingsWindow(self)
        self.soundsettingswindow.protocol("WM_DELETE_WINDOW", self.quittask)
        if not self.soundsettingswindow.exitFlag.istrue():
            self.soundsettingswindow.wait_window(self.soundsettingswindow)
        self.donewpyaudio()
        self.deiconify()
        if not self.exitFlag.istrue() and self.soundsettingswindow.winfo_exists():
            self.soundsettingswindow.destroy()
    def _configure_transcription(self,event=None):
        sound_ui.ASRModelSelectionWindow(self)
    def setcontext(self,context=None):
        Sound.setcontext(self)
        self.context.menuitem(_("Transcription settings"),
                                    self._configure_transcription)
    def __init__(self,parent):
        Sound.__init__(self)
        self.soundsettings.load_ASR() #after file settings are loaded
class Transcription(object):
    def _configure_transcription(self,event=None):
        # sound_ui.ASRModelSelectionWindow(self)
        pass # Placeholder for whatever user was adding
    def setcontext(self,context=None):
        if hasattr(super(), 'setcontext'):
            super().setcontext(context)
        self.context.menuitem(_("Transcription settings"),
                                    self._configure_transcription)
    def __init__(self):
        pass
class WordCollectionwRecordings(WordCollection,Record):
    def getinstructions(self):
        return _("Record a word in your language that goes with these "
                "meanings."
                "\nGive just a single word (not a phrase) wherever possible."
                # "\nClick-Speak-Release on the record button."
                )
    def set_up_transcription(self):
        self.set_transcription_fields()
        self.set_transcription_frame(row=3,column=0,colspan=2) #instructions2
    def set_transcription_fields(self,**kwargs):
        ftype=kwargs.pop('ftype',self.ftype)
        self.transcription_var=ui.StringVar()
        self.transcription_ipa_var=ui.StringVar()
        self.transcription_tone_var=ui.StringVar()
        self.transcription_var.trace_add('write', self.show_drafts)
        self.transcription_ipa_var.trace_add('write', self.store_phonetic)
        self.transcription_tone_var.trace_add('write', self.store_tone)
        if ftype not in self.entry.fields: #Need this to record to
            if ftype == 'lx':
                self.entry.lx=lift.Lexeme(self.entry)
            elif ftype == 'lc':
                self.entry.lx=lift.Citation(self.entry)
            else:
                self.entry.fields[ftype]=lift.Field(self.entry,ftype=ftype)
    def set_transcription_frame(self,**kwargs):
        ftype=kwargs.pop('ftype',self.ftype)
        try:
            self.wordframe.recordFrame.destroy()#don't leave this around!
        except:
            pass
        log.info(f"setting frame with settings: {self.soundsettings}")
        self.wordframe.recordFrame=sound_ui.RecordnTranscribeButtonFrame(
                        self.wordframe,
                        self, #task
                        self.entry.fields[ftype],#node,
                        transcription_var=self.transcription_var,
                        transcription_ipa_var=self.transcription_ipa_var,
                        transcription_tone_var=self.transcription_tone_var,
                        # show_transcriptions=True, #this typically in Entry
                        # show_transcriptions_ipa=True,
                        show_tone=True,
                        shown='none',
                        sticky='ew',
                        **kwargs
                    )
    def show_drafts(self,*args):
        # log.info(f"show_drafts got args {args}")
        instructions2=(_("click on the best option(s) above"),
                        _("correct the consonants and vowels below."))
        try:
            self.wordframe.draftFrame.destroy()
        except:
            pass
        content=self.wordframe.recordFrame.recorder.transcriptions
        log.info(f"Recorder returned {len(content)} transcriptions")
        if len(content) == 1:
            self.var.set(list(content.values())[0]) #value of first (only) option
            return
        c,r=self.wordframe.recordFrame.grid_size()
        self.wordframe.draftFrame=ui.Frame(self.wordframe.recordFrame,
                                            column=c,
                                            row=0
                                        )
        self.wordframe.toneFrame=ui.Label(self.wordframe.recordFrame,
                                            column=c,
                                            row=1
                                        )
        # log.info(f"{content=}")
        content=sorted(content.items(),key=lambda x: len(x[1]))
        # log.info(f"{content=}")
        aspect=3/4 #float OK
        nrows=max(3,int((len(content)*aspect)**.5))
        buttons=0
        max_len=20 #don't want words kicking buttons off the page...
        for repo,line in content:
            ui.Button(self.wordframe.draftFrame,
                text=line[:max_len],
                command=lambda x=repo,y=line:self.draft_entry(x,y),
                column=buttons//nrows,
                row=buttons%nrows,
            )
            buttons+=1
        self.instructions2['text']='\n'.join(instructions2)
        if self.transcription_tone_var.get():
            self.wordframe.toneFrame['text']=self.transcription_tone_var.get()
        else:
            self.wordframe.toneFrame['text']=''
    def draft_entry(self,repo,value,*args):
        # This just fills in the visible field. Dictionary may be
        # overwritten on confirmation later
        # This is only called when a user clicks on a button, not
        # automatically, so it should always overwrite the entry field
        self.program.soundsettings.tally_asr_repo(repo)
        self.var.set(value)
        self.update_idletasks()
        self.program.settings.storesettingsfile(setting='soundsettings')
        log.info(self.program.soundsettings.asr_repo_tally())
    def store_phonetic(self,*args):
        #Need to fix this; format isn't correct
        self.entry.fieldvalue(self.ftype,
                        self.program.db.phoneticlangname(machine=True),
                        value=self.transcription_ipa_var.get().split('\n')[0]
                        )
    def store_tone(self,*args):
        self.entry.fieldvalue(self.ftype,
                        self.program.db.tonelangname(machine=True),
                        value=self.transcription_tone_var.get()
                        )
    def __init__(self, parent):
        Record.__init__(self,parent)
        WordCollection.__init__(self,parent)
class WordCollectionLexeme(Task,WordCollection):
    def tooltip(self):
        return _("Don't use this task.")
    def tasktitle(self):
        return _("Word Collection for Lexeme Forms")
    def __init__(self, parent): #frame, filename=None
        """This should never really be used, though I made it first, so I've
        left it"""
        self.ftype=self.program.params.ftype('lx') #lift.Entry.citationformnodeofentry
        Task.__init__(self,parent)
        WordCollection.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.getwords()
class WordCollectionCitation(Task,WordCollection):
    def tooltip(self):
        return _("This task helps you collect words in citation form.")
    def tasktitle(self):
        return _("Add Words") # for Citation Forms
    def __init__(self, parent): #frame, filename=None
        self.ftype=self.program.params.ftype('lc') #lift.Entry.citationformnodeofentry
        Task.__init__(self,parent)
        WordCollection.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        self.getwords()
class WordCollectionCitationwRecordings(WordCollectionwRecordings,Task):
    def tooltip(self):
        return _("This task helps you collect words in citation form through "
                "recordings with automatic transcription drafts.")
    def tasktitle(self):
        return _("Add Words with Audio") # for Citation Forms
    def __init__(self, parent): #frame, filename=None
        self.ftype=self.program.params.ftype('lc') #lift.Entry.citationformnodeofentry
        Task.__init__(self,parent)
        WordCollectionwRecordings.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        self.getwords()
class WordCollectionPlural(Task,WordCollection):
    def tooltip(self):
        return _("This task helps you collect plural word forms.")
    def tasktitle(self):
        return _("Add plural forms")
    def __init__(self, parent):
        self.ftype=self.program.params.ftype('pl')
        Task.__init__(self,parent)
        WordCollection.__init__(self,parent)
        if not self.program.settings.secondformfieldsOK():
            ErrorNotice(_("To collect Plural forms, you must first "
                            "define which fields should contain those forms"),
                            wait=True)
            self.shutdowntask()
            return
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        # self.nodetag='citation' #lift.Entry.citationformnodeofentry
        self.getwords()
class WordCollectionImperative(Task,WordCollection):
    def tooltip(self):
        return _("This task helps you collect imperative word forms.")
    def tasktitle(self):
        return _("Add imperative forms")
    def __init__(self, parent):
        self.ftype=self.program.params.ftype('imp')
        Task.__init__(self,parent)
        WordCollection.__init__(self,parent)
        if not self.program.settings.secondformfieldsOK():
            ErrorNotice(_("To collect Imperative forms, you must first "
                            "define which fields should contain those forms"),
                            wait=True)
            self.shutdowntask()
            return
        log.info("Initializing {}".format(self.tasktitle()))
        #Status frame is 0,0
        # self.nodetag='citation' #lift.Entry.citationformnodeofentry
        self.getwords()
class ParseWords(Parse,Task):
    def taskicon(self):
        return self.program.theme.photo['iconWord']
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "automatically and with confirmation.")
    def dobuttonkwargs(self):
        fn=self.getparses
        text=_("Parse!")
        tttext=_("{azt} tries to do as much as possible automatically, and "
                "according to the level you have set for confirmation."
                ).format(azt=self.program.name)
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Parse Words")
    def __init__(self, parent): #frame, filename=None
        log.info("Initializing {}".format(self.tasktitle()))
        Task.__init__(self,parent)
        Parse.__init__(self,parent)
        # self.checkeach=True #confirm each word
class WordCollectnParse(Parse,WordCollection,Task):
    """This task collects words, from the SIL CAWL, or one by one.
    First in citation form, then pl or imperativewith Parse"""
    def taskicon(self):
        return self.program.theme.photo['iconWord']
    def tooltip(self):
        return _("This task helps you collect and parse words.")
    def dobuttonkwargs(self):
        if self.program.taskchooser.cawlmissing:
            fn=self.addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren't already in your database "
                    "(you are missing {count} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(count=len(self.program.taskchooser.cawlmissing))
        else:
            text=_("Add a Word")#?
            fn=self.addmorpheme#?
            tttext=_("This adds any word, but is best used after filling out a "
                    "wordlist, if the word you want to add isn't there "
                    "already.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Add and Parse Words") # for Citation Forms
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=self.program.params.ftype('lc') #always correct?
        # self.nodetag='citation'
        Task.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollection.__init__(self,parent)
        self.program.taskchooser.withdraw()
        fn=self.getwords()#?
class WordCollectnParsewRecordings(Parse,WordCollectionwRecordings,Task):
    """This task collects words, from the SIL CAWL, or one by one.
    First in citation form, then pl or imperativewith Parse"""
    def taskicon(self):
        return self.program.theme.photo['iconWordRec']
    def tooltip(self):
        return _("This task helps you collect and parse words by recording "
                "them, with an automatic draft.")
    def dobuttonkwargs(self):
        if self.program.taskchooser.cawlmissing:
            fn=self.addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren't already in your database "
                    "(you are missing {} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(count=len(self.program.taskchooser.cawlmissing))
        else:
            text=_("Add a Word")#?
            fn=self.addmorpheme#?
            tttext=_("This adds any word, but is best used after filling out a "
                    "wordlist, if the word you want to add isn't there "
                    "already.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['WordRec'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Add and Parse Words with Audio") # for Citation Forms
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=self.program.params.ftype('lc') #always correct?
        # self.nodetag='citation'
        Task.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollectionwRecordings.__init__(self,parent)
        self.program.taskchooser.withdraw()
        fn=self.getwords()#?
class WordsParse(Parse,WordCollection,Task):
    def taskicon(self):
        return self.program.theme.photo['iconWord']
    def tooltip(self):
        return _("This task helps you parse words you collected earlier.")
    def tasktitle(self):
        return _("Parse Already Collected Words") # for Citation Forms
    def dobuttonkwargs(self):
        pass
    def __init__(self, parent):
        log.info("Initializing {}".format(self.tasktitle()))
        self.ftype=self.program.params.ftype('lc') #always correct?
        # self.nodetag='citation'
        Task.__init__(self,parent)
        Parse.__init__(self,parent)
        WordCollection.__init__(self,parent)
        # if not self.program.settings.secondformfieldsOK():
        #     ErrorNotice(_("To parse, you must first define which fields "
        #                     "should contain secondary forms"),
        #                     wait=True)
        #     self.shutdowntask()
        #     return
        self.dodone=True #give me words with citation done
        self.checkeach=True #confirm each word (not default)
        self.dodoneonly=True #don't give me other words
        self.userresponse=Object()
        self.program.taskchooser.withdraw()
        #This should either be adapted to use parse or not by keyword, or have
        # another method for addnParse
        # if me:
        #     self.downloadallCAWLimages()
        fn=self.getwords()#?
class ParseSlice(Parse):
    def tasktitle(self):
        return _("Parse One Slice")
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "for one slice(?PS??!?) of the dictionary at a time.")
    def __init__(self, parent): #frame, filename=None
        Parse.__init__(self,parent)
        self.byslice=True #give me words in a selected slice (make this selectable?)
class ParseSliceWords(ParseSlice):
    def tasktitle(self):
        return _("Parse One Slice, word by word")
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "for one slice of the dictionary at a time.")
    def __init__(self, parent): #frame, filename=None
        ParseSlice.__init__(self,parent)
        self.checkeach=True #confirm each word
class Placeholder(Task):
    """Fake check, placeholder for now."""
    def taskicon(self):
        return self.program.theme.photo['icon']
    def tooltip(self):
        return _("Tooltip here.")
    def dobuttonkwargs(self):
        fn=self.addCAWLentries
        text=_("Add remaining CAWL entries")
        tttext=_("This will add entries from the Comparative African "
                "Wordlist (CAWL) which aren't already in your database "
                "(you are missing {} CAWL tags). If the appropriate "
                "glosses are found in your database, CAWL tags will be "
                "merged with those entries."
                "\nDepending on the number of entries, this may take "
                "awhile.").format(count=len(self.program.taskchooser.cawlmissing))
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['icon'],
                'sticky':'ew',
                'tttext':tttext
                }
    def tasktitle(self):
        return _("Placeholder Check2")
    def __init__(self, parent): #frame, filename=None
        Task.__init__(self,parent)
        log.info("Initializing {}".format(self.tasktitle()))
        for r in range(5):
            ui.Label(self.frame,
                    text=_("This is a check placeholder."),
                    row=r, column=0)
class ToneFrameDrafter(ui.Window):
    def addback(self,lang,event=None):
        self.forms[lang]={
                        'before':'',
                        'after':''
                        }
        self.status()
    def skiplang(self,lang,event=None):
        del self.forms[lang]
        self.status()
    def analangftypecode(self):
        return '_'.join([self.analang,self.forms['field']])
    def stripftypecode(self,x):
        return x.removesuffix('_'+self.forms['field'])
    def status(self):
        if self.exitFlag.istrue():
            return
        try:
            self.fds.destroy()
            self.exf.destroy()
        except AttributeError:
            # log.info("First status frame, or no example yet ({}).".format(e))
            pass
        self.fds=ui.Frame(self.content,row=1,column=0)
        if 'field' not in self.forms:
            d=self.program.params.ftype()
            log.info("Didn't find field type; setting current ({}).".format(d))
            self.forms['field']=d
        if 'name' not in self.forms:
            log.info("Didn't find a name; prompting.")
            self.promptwindow()
            if ('name' not in self.forms or #not started
                    isinstance(self.forms['name'],ui.StringVar) #i.e., not saved
                    or not self.forms['name']): # empty
                log.info("Name form not entered. Exiting. ({})"
                        "".format(self.forms['name']))
                self.on_quit()
            # log.info(self.forms)
            # log.info(self.exitFlag.istrue())
            return
        # log.info("Found name")
        # log.info("Starting status with self.form: {}".format(self.forms))
        text=self.forms['name']
        if text == '':
            text=_("Give a frame name!")
        nametext=_("Frame name:")
        # log.info("Frame name: {}".format(text))
        relief='raised' #flat, raised, sunken, groove, and ridge
        frameparams=ui.Frame(self.fds,columnspan=4,column=0,row=0,pady=50,
                            # highlightthickness=5,
                            # highlightbackground=self.theme.activebackground
                            )
        nameframe=ui.Frame(frameparams,columnspan=2,column=0,row=0,padx=50)
        namelabel=ui.Label(nameframe,text=nametext,column=0,row=0)
        namebutton=ui.Button(nameframe, relief=relief,
                            cmd=self.promptwindow,
                            text=text,column=1,row=0)
        ui.ToolTip(namebutton,text=_("Set the frame name for status table and reports"))
        fieldname=_("Field to frame:")
        ftypeframe=ui.Frame(frameparams,column=2,row=0)
        ftypelabel=ui.Label(ftypeframe,text=fieldname,column=0,row=0)
        ftypebutton=ui.Button(ftypeframe,text=self.fieldtypename(),
                            cmd=self.getfieldtype,
                            relief=relief,
                            column=1,row=0)
        ui.ToolTip(ftypelabel)
        self.forms['field']
        #order glosslangs first, then other options:
        self.langs=[self.analangftypecode()]+self.program.settings.glosslangs+[
                                    l for l in self.program.db.glosslangs
                                    if l not in self.program.settings.glosslangs]
        for l in [self.analangftypecode()]+self.program.settings.glosslangs: #actually selected
            try:
                self.forms[l]['after']=self.forms[l].get('after','')
            except KeyError: #i.e., if no l in self.forms
                self.forms[l]={'after':''}
            self.forms[l]['before']=self.forms[l].get('before','')
        # log.info("Langs done: {}".format(langs))
        # log.info("self.langs: {}".format(self.langs))
        # log.info("Langs in process: {}".format(langsbeforeonly))
        # log.info("Langs langstodo: {}".format(langstodo))
        nothing='______'
        for n,l in enumerate(self.langs):
            langname=self.program.settings.languagenames[self.stripftypecode(l)]
            if l in self.forms:
                log.info("Working on {}".format(langname))
                if l == self.stripftypecode(l): #no change means gloss
                    tintro=_("Gloss in {lang}:").format(lang=langname)
                    if l in self.program.settings.glosslangs:
                        ltttext=_("current gloss language")
                    else:
                        ltttext=_("additional gloss language")
                        b=ui.Button(self.fds,text='X',
                                    cmd=lambda l=l:self.skiplang(l),
                                    column=0,row=n+1,sticky='e')
                        b.tt=ui.ToolTip(b, _("Skip {lang}").format(lang=langname))
                else:
                    tintro=_("{lang}:").format(lang=langname)
                    ltttext=_("analysis language")
                li=ui.Label(self.fds,text=tintro,column=1,row=n+1)
                li.tt=ui.ToolTip(li, ltttext)
                lineframe=ui.Frame(self.fds,column=2,row=n+1)
                if 'Language ' in langname:
                    tword=_("<word>")
                else:
                    tword=_("<{lang} word>").format(lang=langname)
                try:
                    text=self.forms[l]['before']
                    if text == '':
                        text=nothing
                except KeyError:
                    try:
                        self.forms[l]={'before':''}
                        text=nothing
                    except:
                        text='<'+_("No {lang} frame info").format(
                                lang=self.program.settings.languagenames[l])+'>'
                button=ui.Button(lineframe,text=text,
                                relief=relief,
                                cmd=lambda l=l, context='before':
                                        self.promptwindow(l,context),
                                column=1,row=0,padx=0,ipadx=0)
                ui.ToolTip(button)
                if l not in self.forms:
                    continue
                ui.Label(lineframe,text=tword,column=2,row=0,padx=0,ipadx=0)
                try:
                    text=self.forms[l]['after']
                    if text == '':
                        text=nothing
                except KeyError:
                    if 'before' in self.forms[l]:
                        self.forms[l]={'after':''} #in case it got deleted
                        text=nothing
                button=ui.Button(lineframe,text=text,
                                relief=relief,
                                cmd=lambda l=l, context='after':
                                        self.promptwindow(l,context),
                                column=3,row=0,padx=0,ipadx=0)
                ui.ToolTip(button)
            else:
                text=_("Add {lang} gloss").format(lang=langname)
                button=ui.Button(self.fds,text=text,
                                relief=relief,
                                font='small',
                                cmd=lambda l=l: self.addback(l),
                                columnspan=2,column=0,row=n+1,padx=0,ipadx=0)
                ui.ToolTip(button,_("Add {lang} values for this frame").format(
                                    lang=langname
                                    ))
        text=_("Get Example")
        exemplify=ui.Button(self.fds,text=text,cmd=self.exemplified,
                            columnspan=2,column=0,row=n+2)
        exemplify.update_idletasks()
        self.parent.withdraw() #just in case it's visible
    def setfieldtype(self,choice,window):
        self.forms['field']=choice
        window.on_quit()
        self.status()
    def fieldtypename(self):
        return [i[1] for i in self.fieldtypes()
                    if i[0] == self.forms['field']][0]
    def fieldtypes(self):
        # try:
        #     log.info("{}".format(self.program.settings.pluralname))
        #     log.info("{}".format(self.program.settings.imperativename))
        #     log.info("{}".format(self.program.settings.secondformfield[self.program.settings.verbalps]))
        #     log.info("{}".format(self.program.settings.secondformfield[self.program.settings.nominalps]))
        # except Exception as e:
        #     log.error("Exception in ps-land:{}".format(e))
        opts=[
                ('lc', _("Citation form")),
                ('lx', _("Lexeme form")),
                ]
        """These should maybe be switched over to just pl and imp"""
        if self.ps == self.program.settings.nominalps:
            opts.append((self.program.settings.pluralname, _("Plural form")))
        elif self.ps == self.program.settings.verbalps:
            opts.append((self.program.settings.imperativename, _("Imperative form")))
        return [(i,j) for (i,j) in opts if i]
    def getfieldtype(self,event=None):
        w=ui.Window(self,
                        # row=1,column=0,
                        # sticky='ew',
                        padx=25,pady=25)
        w.title(_("Select which field to frame"))
        ui.ButtonFrame(w.frame,optionlist=self.fieldtypes(),
                        command=self.setfieldtype,
                        window=w,
                        row=0,column=0)
    def exemplified(self,event=None):
        log.info("Giving example now")
        checktoadd=self.forms['name']
        if hasattr(self,'exf'):
            self.exf.destroy()
        self.exf=ui.Frame(self.content,row=2,column=0,sticky='w')
        if checktoadd in ['', None]:
            text=_('Sorry, empty name! \nPlease provide at least \na frame '
                'name, to distinguish it \nfrom other frames.')
            log.error(rx.delinebreak(text))
            l1=ui.Label(self.exf,
                        text=text,
                        font='read',
                        justify=ui.LEFT,anchor='w',
                        row=0,column=0,
                        sticky='w')
            return
        #don't give exs w/o all glosses
        """Define the new frame"""
        checkdefntoadd={'field':self.forms['field']}
        log.info("Ready to add frame with this form info: {}".format(self.forms))
        # log.info("Ready to add frame with this lookingfor info: {}".format(self.lookingfor))
        for lang in [i for i in self.forms #self.lookingfor
                            if 'before' in self.forms[i]
                            if 'after' in self.forms[i]
                ]: #just the defined languages
            before=self.forms[lang]['before']
            after=self.forms[lang]['after']
            checkdefntoadd[lang]=str(before+'__'+after)
        formdict=self.gimmesenseformdictwftypengloss(checkdefntoadd)
        #This should only pull from current ps
        # log.info('formdict result: {}'.format(formdict))
        padx=50
        pady=10
        row=0
        text=_("Examples for {name} {field} tone frame").format(name=checktoadd,
                                                        field=self.fieldtypename())
        lt=ui.Label(self.exf,
                text=text,
                font='readbig',
                justify=ui.LEFT,anchor='w',
                row=row,column=0,
                sticky='w',#columnspan=2,
                padx=padx,pady=pady)
        if not formdict:
            l1=ui.Label(self.exf,
                    text=_("None!"),
                    font='read',
                    justify=ui.LEFT,anchor='w',
                    row=row,column=0,
                    sticky='w',
                    padx=padx,pady=pady)
            return
        for lang,forms in formdict.items():
            row+=1
            text=('[{}]: {}'.format(lang,forms))#framed.forms.framed[lang]))
            l1=ui.Label(self.exf,
                    text=text,
                    font='read',
                    justify=ui.LEFT,anchor='w',
                    row=row,column=0,
                    sticky='w',
                    padx=padx,pady=pady)
            log.info('langlabel:{}'.format(text))
        """toneframes={'Nom':
                        {'name/location (e.g.,"By itself")':
                            {'analang.xyz': '__',
                            'glosslang.xyz': 'a __'},
                            'glosslang2.xyz': 'un __'},
                    }   }
        """
        row+=1
        stext=_('Use {name} tone frame').format(name=checktoadd)
        subframe=ui.Frame(self.exf,row=row,column=0,sticky='w')
        sub_btn=ui.Button(subframe,text = stext,
                          command = lambda x=checkdefntoadd,
                                            n=checktoadd: self.submit(x,n),
                          row=0,column=0,
                          )
        ui.Label(subframe, text=_("<= No changes after this! \nPlease check that "
                                "the above looks good on several examples!"),
                                justify='left', row=0, column=1, padx=15)
        # log.info('sub_btn:{}'.format(stext))
        sub_btn.update_idletasks()
    def promptstrings(self,lang=None,context=None):
        #None of this changes in editing. Is that what we want?
        if lang:
            lname=self.program.settings.languagenames[self.stripftypecode(lang)]
            text=_("Fill in the {lang} frame forms below.\n(include a "
                "space to separate word forms)"
                ).format(lang=lname)
            if lang != self.stripftypecode(lang): #i.e., analang
                kind=_('form')
                ok=_('Use this form')
            else:
                kind=_('gloss')
                ok=_("Use this {lang} form {context} the dictionary gloss").format(lang=lname,
                                context=_(context))
                self.glosslangs.append(lang)
            if context == 'before':
                text+='\n'+_("What text goes *before* \n<==the {lang} word *{kind}* "
                        "\nin the frame?").format(lang=lname,kind=kind)
            elif context == 'after':
                text+='\n'+_("What text goes *after* \nthe {lang} word *{kind}*==> "
                        "\nin the frame?").format(lang=lname,kind=kind)
        else:
            text=_("What do you want to call this new {ps} tone frame for {lang}?"
                    ).format(ps=self.ps,
                            lang=self.program.settings.languagenames[self.analang])
            ok=_("Use this name")
        return {'lang':lang, 'prompt':text, 'ok':ok}
    def promptwindow(self,lang=None,context=None,event=None):
        def submitform(event=None):
            log.info("context: {}; lang: {}".format(context,lang))
            log.info("Form: {}".format(self.forms))
            clearNull()
            if lang and context:
                log.info("Form.get: {}".format(v.get()))
                log.info("type: {}".format(type(v)))
                log.info("value: {}".format(v.__dict__))
                self.forms[lang][context]=v.get()
            else:
                log.info("name.get: {}".format(v.get()))
                self.forms['name']=v.get()
            log.info("Forms: {}".format(self.forms))
            self.w.on_quit()
            self.status()
        def clearNull(event=None):
            if v.get() == null:
                v.set('')
        def setNull(event=None):
            if v.get() == '':
                v.set(null)
        log.info("context: {}; lang: {}".format(context,lang))
        strings=self.promptstrings(lang,context)
        self.w=ui.Window(self,
                        # row=1,column=0,
                        # sticky='ew',
                        padx=25,pady=25)
        if lang and context:
            self.w.title('{} {}'.format(context,lang))
        else:
            self.w.title(_("New {ps} Tone frame for {lang}: Name the Frame").format(
                        ps=self.ps,lang=self.program.settings.languagenames[self.analang]))
        self.withdraw() #Don't show status when asking for a value
        getform=ui.Label(self.w.frame,text=strings['prompt'],
                        font='read',row=0,column=0,
                        wraplength=self.program.root.wraplength/2,
                        padx=self.padx,
                        pady=self.pady)
        #field rendering is better in another frame, with no sticky!:
        eff=ui.Frame(self.w.frame,row=1,column=0,sticky='')
        null=initval='<no content>'
        if lang and context:
            try:
                initval=self.forms[lang][context]
                v=ui.StringVar(self,initval)
            except KeyError:
                v=ui.StringVar(self,initval)
                try:
                    self.forms[lang][context]=v
                except KeyError:
                    self.forms[lang]={context:v} #because this isn't there yet
        else:
            try:
                initval=self.forms['name']
                v=ui.StringVar(self,initval)
            except KeyError:
                v=self.forms['name']=ui.StringVar(self,initval)
        formfield = ui.EntryField(eff, render=True,
                                text=v,
                                row=1,column=0,
                                sticky='')
        formfield.focus_set()
        formfield.bind('<Return>',submitform)
        formfield.bind('<FocusIn>',clearNull)
        formfield.bind('<FocusOut>',setNull)
        formfield.rendered.grid(row=2,column=0,sticky='new')
        sub_btn=ui.Button(self.w.frame,text = strings['ok'],
                            command = submitform,
                            anchor ='c',row=2,column=0,sticky='')
        sub_btn.wait_window(formfield) #then move to next step
        if not self.exitFlag.istrue():
            self.deiconify()
    def submit(self,checkdefntoadd,checktoadd,event=None):
        log.info("Submitting {} frame with these values: {}".format(
                                                checktoadd,checkdefntoadd
                                                ))
        # Having made and unset these, we now reset and write them to file.
        self.program.toneframes.addframe(self.ps,checktoadd,checkdefntoadd)
        self.program.status.renewchecks() #renew (not update), because of new frame
        # log.info("object: {}".format(self.program.toneframes))
        self.program.settings.storesettingsfile(setting='toneframes')
        self.program.settings.setcheck(checktoadd) #assume we will use this now
        self.task.deiconify()
        self.destroy()
    def gimmesense(self,sense=None,next=False,**kwargs):
        sensesbyps=self.program.db.sensesbyps[self.ps]
        if next and sense:
            # log.info("trying {} sense {}/{}".format(self.ps,
            #                                     sensesbyps.index(sense)+1,
            #                                     len(sensesbyps)))
            try:
                return sensesbyps[sensesbyps.index(sense)+1]
            except IndexError:
                return sensesbyps[0]
        else:
            sense=sensesbyps[randint(0, len(sensesbyps)-1)]
            # log.info("returning random {} sense {}".format(self.ps,sense.id))
            return sense
    def gimmesenseformdictwftypengloss(self,framedef,**kwargs):
        tried=0
        langs=[i for i in framedef if i not in ['name','field']]
        glosslangs=[i for i in langs if i == self.stripftypecode(i)]
        # log.info("checking for these langs: {}".format(langs))
        # log.info("checking for this frame: {}".format(framedef))
        ftype=framedef['field']
        while not tried or None in f.values():
            f={lang:None for lang in langs} #start each with a clean slate
            if tried > self.program.db.nsenses*1.5: #give up looking randomly
                sense=self.gimmesense(sense,next=True)
            else:
                sense=self.gimmesense()
            f.update(sense.formatteddictbylang(self.analang, #This is xyz_ftype
                                        glosslangs,
                                        # self.program.settings.glosslangs,
                                        frame=framedef
                                            ))
            # log.info("Analang form found: {}".format(f[self.analang]))
            tried+=1
            log.info("Values found: {}".format(f))
            if tried> self.program.db.nsenses*3.5:
                errortext=_("I've tried (randomly, then through each) {count} "
                "times, and not found one "
                "of your {total} senses with data in each of these languages: "
                "{langs}. \nAre you asking for gloss "
                "languages which actually have data in your database? \nOr, are "
                "you missing gloss fields (i.e., you have only 'definition' "
                "fields)?").format(count=tried,total=self.program.db.nsenses,langs=langs)
                log.error(errortext)
                return #errortext
        log.debug("Found entry {} with glosses {}".format(sense.id,f))
        return f
    def __init__(self,parent):
        ui.Window.__init__(self,parent)
        self.task=parent #this should always be called by a window task
        self.analang=parent.analang
        self.ps=self.program.slices.ps()
        self.forms={}
        # we want to start this net wide, to cover future usage
        # At some point, I may want to distinguish the analang from its gloss
        # in the same language code. They have different values in LIFT, and
        # there might be reason to distinguish them in the frame definitions.
        # But until I figure out how i want to do that, each language should
        # just appear once.
        self.glosslangs=list()
        self.padx=50
        self.pady=10
        title=_("Define a New {ps} Tone Frame for {lang}").format(ps=self.ps,
                        lang=self.program.settings.languagenames[self.analang])
        self.title(title)
        t(f"Add {self.ps} Tone Frame for {self.program.settings.languagenames[self.analang]}")#+'\n'?
        ui.Label(self.frame,text=t,font='title',row=0,column=0)
        self.scroll=ui.ScrollingFrame(self.frame,row=1,column=0)
        self.content=self.scroll.content
        self.status()

    def store(self):
        log.info(_("Saving toneframes dict to file"))
        self.program.settings.storesettingsfile('toneframes')

class SortSyllables(Sort,Segments,Task):
    def taskicon(self):
        return self.program.theme.photo['iconWord']
    def tasktitle(self):
        return _("Sort Word Syllables") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by whole "
                "word syllable profiles.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['Word'], #self.cvt
                'sticky':'ew'
                }
    def presortgroups(self):
        """organize all the words that belong to the top X syllable profiles,
        and mark them belonging to groups defined by profile"""
        """These groups should be sorted into and out of as for others"""
        """cvprofilevalue should have set value on boot, so we shouldn't
        recalculate it here. but once sorted, we shouldn't override on each
        boot.
        We should likely store different values, one that is calculated,
        the other is user data
        """
        ps=self.program.slices.ps()
        for sense in self.program.db.sensesbyps[ps]:
            valuelist=[k for k in self.program.settings.profilesbysense[ps]
                        if sense in self.program.settings.profilesbysense[ps][k]]
            if valuelist:
                sense.cvprofilevalue(self.program.params.ftype(),valuelist[0])
    def runcheck(self):
        self.program.settings.storesettingsfile()
        log.info("Running check...")
        cvt=self.program.params.cvt()
        check=self.program.params.check()
        profiles=self.program.slices.profiles()
        """further specify check check in maybesort, where you can send the user
        on to the next setting"""
        self.presortgroups()
        self.updatesortingstatus() # Not just tone anymore
        self.maybesort(firstrun=True)
    def __init__(self, parent):
        self.program.params.cvt('S') #syllable
        Task.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
class SortCV(Sort,Segments,Task):
    """docstring for SortCV."""
    def __init__(self, parent):
        Task.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
class SortV(Sort,Segments,Task):
    def taskicon(self):
        return 'iconV'#self.program.theme.photo['iconV']
    def tasktitle(self):
        return _("Sort Vowels") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by vowels.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['V'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent, **kwargs):
        self.program.params.cvt('V')
        Task.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        if g:=kwargs.get("redo_glyph"):
            self.redo_joinglyphs(g)
        elif g:=kwargs.get("sort_immediately"):
            self.runcheck()
class SortC(Sort,Segments,Task):
    def taskicon(self):
        return 'iconC'#self.program.theme.photo['iconC']
    def tasktitle(self):
        return _("Sort Consonants") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by consonants.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['C'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent, **kwargs):
        self.program.params.cvt('C')
        Task.__init__(self,parent)
        Sort.__init__(self, parent)
        Segments.__init__(self,parent)
        if g:=kwargs.get("redo_glyph"):
            self.redo_joinglyphs(g)
        elif g:=kwargs.get("sort_immediately"):
            self.runcheck()
class SortT(Sort,Tone,Task):
    def taskicon(self):
        return 'iconT'#self.program.theme.photo['iconT']
    def tasktitle(self):
        return _("Sort Tone") #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form tone frames.")
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['T'], #self.cvt
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self)
        Task.__init__(self,parent)
        self.program.params.cvt('T')
        Sort.__init__(self, parent)
        # log.info("status: {}".format(type(self.program.status)))
        # Not sure what this was for (XML?):
        self.pp=pprint.PrettyPrinter()
        """Are we OK without these?"""
        log.info("Done initializing check.")
        """Testing Zone"""
    def addtonefieldpron(self,guid,framed): #unused; leads to broken lift fn
        sense=None
        self.program.db.addpronunciationfields(
                                    guid,sense.id,self.analang,self.glosslangs,
                                    lang='en',
                                    forms=framed,
                                    fieldtype='tone',location=check,
                                    fieldvalue=self.groupselected,
                                    ps=None
                                    )
    def marksortedguid(self,guid):
        """I think these are only valuable during a check, so we don't have to
        constantly refresh sortingstatus() from the lift file."""
        """These four functions should be generalizable"""
        self.guidssorted.append(guid)
        self.guidstosort.remove(guid)
    def marktosortguid(self,guid):
        self.guidstosort.append(guid)
        self.guidssorted.remove(guid)
    """Doing stuff"""
class Transcribe(Sound,Sort,Task):
    def updateerror(self):
        newvalue=self.transcriber.formfield.get()
        if newvalue == '':
            noname=_("Give a name for this group!")
            log.debug(noname)
            self.errorlabel['text'] = noname
            return 1
        elif newvalue != self.group and newvalue in self.groups:
            deja=[_("Sorry, there is already a group with that label"),
                _("see comparison below.")]
            log.debug('; '.join(deja))
            self.errorlabel['text'] = ';\n '.join(deja)
            self.setgroup_comparison(newvalue)
            return 1
        self.errorlabel['text'] = ''
    def updateform(self,*args):
        self.set_ok_w_form(self.updateerror())
    def refresh_status_buttons(self,*args):
        for i in [args]:
            if (i in self.status.glyphbuttons 
                    and self.status.glyphbuttons[i].winfo_exists()):
                self.status.glyphbuttons[self.group].destroy()
                self.status.glyphbuttons[new].destroy()
    def switchgroups(self,comparison=None):
        #this doesn't save!
        if (not hasattr(self,'group') or not hasattr(self,'group_comparison')
            and not comparison):
            log.error(_("Missing either group or comparison, without value "
                        "specified; can't switch them."))
            return
        log.info(_("Swtiching groups; using ‘{comp}’ for "
                "‘{group}’").format(comp=self.group_comparison, group=self.group))
        #actually change the data, not the group settings:
        #This method should go somewhere more reasonable:
        g=self.add_int_group(self) #Don't merge groups!
        if self.cvt == 'T':
            fn=self.rename_group
        else:
            fn=self.rename_macrogroup
        fn(self.group,g,updatestatus=False)
        fn(self.group_comparison,self.group,updatestatus=False)
        fn(g,self.group_comparison)
        self.refresh_status_buttons(g,self.group_comparison)
        # self.program.settings.setgroup(gc)
        self.runwindow.on_quit()
        self.makewindow() #The other group needs a name, too!
    def submitandswitch(self):
        if hasattr(self,'group_comparison'):
            comparison=self.group_comparison
        else:
            self.errorlabel['text'] = _("Sorry, pick a comparison first!")
            return 1
        error=self.submitform()
        if not error:
            self.switchgroups(comparison)
    def updategroups(self):
        # Update locals group, groups, and othergroups from objects
        self.groups=self.program.status.groups(wsorted=True)
        # log.info("self.groups: {}".format(self.groups))
        self.groupsdone=self.program.status.verified()
        self.group=self.program.status.group()
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        if not self.groups:
            ErrorNotice(_("No groups in that slice; try another!"))
            return
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        if self.group is None or self.group not in self.groups:
            w=self.getgroup(wsorted=True, guess=True, intfirst=True)
            if w.winfo_exists():
                w.wait_window(w)
            self.group=self.program.status.group()
            if not self.group:
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        self.othergroups=self.groups[:]
        try:
            self.othergroups.remove(self.group)
        except ValueError:
            log.error(_("current group ({group}) doesn't seem to be in list of "
                "groups: ({groups})\n\tThis may be because we're looking for data "
                "that isn't there, or maybe a setting is off.").format(
                                                    group=self.group, groups=self.groups))
            return
        return 1
    def unsubmit(self,event=None):
        log.info("Undoing...")
        self.mistake=True
    def polygraphwarn(self,newvalue):
        if len(newvalue) != 1 or len(self.group) != 1:
            warning=[_("This name change (‘{group}’ > ‘{new}’) impacts your "
                        "digraph and trigraph settings."
                        ).format(group=self.group,new=newvalue)]
            if len(newvalue) > 1:
                warning.append(_("{azt} will add ‘{new}’ to those settings."
                            ).format(azt=self.program.name,new=newvalue))
                if newvalue not in self.program.settings.polygraphs[self.analang][self.cvt]:
                    self.program.settings.polygraphs[self.analang][self.cvt][newvalue]=True
                    self.program.settings.storesettingsfile('profiledata')
            if len(self.group) > 1:
                warning.append(_("{azt} will *not* remove ‘{group}’ from "
                            "those settings, because you may still be "
                            "using it elsewhere."
                            ).format(azt=self.program.name,group=self.group))
            warning.extend(['',_("**If this isn't what you wanted, "
                        "fix and confirm your digraph and "
                        "trigraph settings in the menu "
                        "\n(this will make {azt} restart and redo "
                        "the syllable profile analysis)."
                        ).format(azt=self.program.name)])
            title=_("Syllable profile change?")
            #Just state this and move on to making changes:
            log.info('\n'.join(warning))
            # self.err=ErrorNotice(warning,parent=self,title=title)
    def submitform(self):
        newvalue=self.transcriber.formfield.get()
        if self.program.params.cvt() != 'T': #Warning only on segmental changes
            self.polygraphwarn(newvalue)
            #These should each make one change only, checking for overwrites
            self.rename_macrogroup(self.group,newvalue)
            self.program.alphabet.glyph(newvalue)
            self.refresh_status_buttons(self.group,newvalue)
        else:
            """updateforms=True doesn't seem to be working for segments"""
            self.updatebygroupsense(self.group,newvalue,updateforms=True)
            #NO: this should update formstosearch and profile data.
            # log.info("Doing renamegroup: {}>{}".format(self.group,newvalue))
            self.program.status.renamegroup(self.group,newvalue) #status file only
            # log.info("Doing updategroups")
            self.updategroups() #updates self.groups self.group self.othergroups self.groupsdone
            self.program.settings.storesettingsfile(setting='status')
            """Update regular expressions here!!"""
        self.maybewrite()
        self.ok_done=True
        # update forms, even if group doesn't change:
        if hasattr(self,'group_comparison'):
            delattr(self,'group_comparison') # in either case
        self.runwindow.on_quit()
    def next(self):
        log.debug("running next group")
        error=self.submitform()
        if not error:
            # log.debug("group: {}".format(group))
            ints=[i for i in self.program.status.groups(wsorted=True)
                    if i.isdigit()]
            if ints:
                log.info("Found integer groups: {ints}".format(ints=ints))
                self.program.status.group(str(min(ints)))#Look for integers first
            else:
                log.info("Didn't Find integer groups: {groups}".format(
                    groups=self.program.status.groups(wsorted=True)))
                self.program.status.nextgroup(wsorted=True)
            # log.debug("group: {}".format(group))
            self.makewindow()
    def nextcheck(self):
        log.debug("running next check")
        error=self.submitform()
        if not error:
            # log.debug("check: {}".format(check))
            self.program.status.nextcheck(wsorted=True)
            # log.debug("check: {}".format(check))
            self.makewindow()
    def nextprofile(self):
        log.debug("running next profile")
        error=self.submitform()
        if not error:
            # log.debug("profile: {}".format(profile))
            self.program.status.nextprofile(wsorted=True)
            # log.debug("profile: {}".format(profile))
            self.makewindow()
    def setgroup_comparison(self,group=None,**kwargs):
        if group:
            self.program.settings.set('group_comparison',group)
        else:
            #this returns its window:
            w=self.getglyph(comparison=True,**kwargs)
            if w and w.winfo_exists(): #This window may be already gone
                log.info("Waiting for {w}".format(w=w))
                w.wait_window(w)
        log.info(_("Groups: {group} (of {groups}); "
                "{comp}?").format(group=self.group, groups=self.groups, comp=self.program.settings.group_comparison))
        if hasattr(self.program.settings,'group_comparison'):
            self.group_comparison=self.program.settings.group_comparison
        if self.errorlabel['text'] == _("Sorry, pick a comparison first!"):
            self.updateerror()
        self.comparisonbuttons()
    def comparisonbuttons(self):
        try: #successive runs
            self.compframe.compframeb.destroy()
            log.info("Comparison frameb destroyed!")
        except: #first run
            log.info("Problem destroying comparison frame, making...")
        self.compframe.compframeb=ui.Frame(self.compframe)
        self.compframe.compframeb.grid(row=1,column=0)
        t=_('Compare with another group')
        if (hasattr(self, 'group_comparison')
                and self.group_comparison in self.groups and
                self.group_comparison != self.group):
            log.info("Making comparison buttons for group {group} now".format(
                                                group=self.group_comparison))
            t=_('Compare with another group ({group})').format(
                                                group=self.group_comparison)
            self.compframe.bf2=SortGlyphGroupButtonFrame(
                                    self.compframe.compframeb,
                                    self,
                                    group=self.group_comparison,
                                    showtonegroup=True,
                                    playable=True,
                                    unsortable=False, #no space, bad idea
                                    alwaysrefreshable=True,
                                    font='default',
                                    wraplength=self.buttonframew
                                    )
            self.compframe.bf2.grid(row=0, column=0, sticky='w')
            self.compframe.b2=ui.Button(self.compframe.compframeb,
                                        text=self.switch_text,
                                        cmd=self.switchgroups,
                                        row=0, column=1, sticky='w')
            self.compframe.b2tt=ui.ToolTip(self.compframe.b2, self.switch_tt)
            # self.maybeswitchmenu=ui.ContextMenu(self.compframe)
            # self.maybeswitchmenu.menuitem(_("Switch to this group"),
            #                                 self.switchgroups)
        elif not hasattr(self, 'group_comparison'):
            log.info("No comparison found !")
        elif self.group_comparison not in self.groups:
            log.info("Comparison ({comp}) not in group list ({groups})"
                        "".format(comp=self.group_comparison,groups=self.groups))
        elif self.group_comparison == self.group:
            log.info("Comparison ({comp}) same as subgroup ({group}); not showing."
                        "".format(comp=self.group_comparison,group=self.group))
        else:
            log.info(_("This should never happen (renamegroup/"
                        "comparisonbuttons)"))
        self.sub_c['text']=t
    def __init__(self,parent): #frame, filename=None
        Task.__init__(self, parent)
        self.program.settings.makeeverythingok()
        self.ftype=self.program.params.ftype()
        self.mistake=False #track when a user has made a mistake
        self.analang=self.program.params.analang()
        self.program.status.makecheckok()
        Sound.__init__(self)
class TranscribeS(Transcribe,Segments):
    macrosort=True
    def done(self):
        log.info("Transcribe done")
        self.submitform()
        self.program.alphabet.save_settings()
        self.donewpyaudio()
    def go_back(self):
        log.info("Transcribe done for now (going back)")
        self.runwindow.on_quit()
        self.donewpyaudio()
        self.program.taskchooser.maketask(f"Sort{self.program.params.cvt()}",
                                        redo_glyph=self.group)
    def set_ok_w_form(self,error=False):
        form=self.transcriber.formfield.get()
        self.oktext.set(_("OK: Add the letter ‘{form}’ {newline}to my alphabet "
                        "{newline}for this sound").format(form=form,newline="\n"))
        if form and not error:
            self.ok_button['state'] = 'normal'
        else:
            self.ok_button['state'] = 'disabled'
    def makewindow(self, glyph=None, event=None):
        self.pyaudiocheck() # seems to dissapear sometimes
        self.ok_done=False
        if glyph:
            self.group=self.program.alphabet.glyph(glyph)
        else:
            self.group=self.program.alphabet.glyph()
        if not isinstance(self.group, str):
            log.info("Group not a string! ({group}, {type})".format(group=self.group, type=type(self.group)))
        cvt=self.program.params.cvt()
        self.groups=self.program.alphabet.glyphs()
        # self.groups=self.program.status.all_groups_verified_for_cvt()
        self.otherglyphs=set(self.groups)-{self.group}
        padx=50
        if self.program.settings.lowverticalspace:
            log.info("Using low vertical space setting")
            pady=0
        else:
            pady=10
        self.buttonframew=int(self.program.screenw()/3.5)
        title=[self.program.params.cvtdict()[cvt]['sg'],_("letter")]
        getformtext=[_("What letter(s) will you use for this {sg} "
                        "group?").format(sg=self.program.params.cvtdict()[cvt]['sg'])]
        if self.group.isdigit():
            title.insert(0,_("Name New"))
            # getformtext.append(_("Because this is a new group, you need to give it "
            #                 "some name now."))
            initval=''
        else:
            title.insert(0,_("Rename"))
            title.append(f"‘{self.group}’")
            initval=self.group
        self.getrunwindow(title=title)
        titlel=ui.Label(self.runwindow.frame,text=' '.join(title),
                        font='title',
                        row=0,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getform=ui.Label(self.runwindow.frame,
                        text='\n'.join(getformtext),
                        font='read',
                        norender=True,
                        row=1,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getform.wrap()
        inputfeedbackframe=ui.Frame(self.runwindow.frame,
                            row=2,column=0,sticky=''
                            )
        self.transcriber=transcriber.Transcriber(inputfeedbackframe,
                                initval=initval,
                                soundsettings=self.soundsettings,
                                chars=self.glyphspossible,
                                row=0,column=0,sticky=''
                                )
        self.transcriber.newname.trace_add('write', self.updateform)
        infoframe=ui.Frame(inputfeedbackframe,
                            row=0,column=1,sticky=''
                            )
        """Make this a pad of buttons, rather than a label, so users can
        go directly where they want to be"""
        g=nn(self.otherglyphs,perline=len(self.otherglyphs)//3)
        # log.info("groups={groups}, otherglyphs={other}, g={g}".format(groups=self.groups, other=self.otherglyphs, g=g))
        glyphslabel=ui.Label(infoframe,
                            text='\n'.join([_("Don't use Other Groups:"),g]),
                            column=1,
                            sticky='new',
                            padx=padx,
                            rowspan=2
                            )
        self.errorlabel=ui.Label(infoframe,text='',
                            fg='red',
                            wraplength=int(self.frame.winfo_screenwidth()/3),
                            row=2,column=1,sticky='nsew'
                            )
        ui.Button(infoframe, #don't make this too wide
                    text=_("Go back and join \nwith one of\n← these groups"),
                    command=self.go_back,
                    column=2,
                    rowspan=2,
                    sticky='nsew'
                    )
        examplesframe=ui.Frame(self.runwindow.frame,
                                row=4,column=0,sticky='',
                                # border=1
                                )
        # self.oktext=_("OK")
        self.oktext=ui.StringVar()
        # self.transcriber.formfield
        self.ok_button=ui.Button(examplesframe, 
                                # text=self.oktext,
                                textvariable=self.oktext,
                                font='title',
                                row=0,
                                column=1,
                                sticky='ns',
                                padx=padx,
                                ipadx=30,
                                ipady=20,
                                pady=20,
                                command=self.done
        )
        self.updateform() #updates button state
        cmd=lambda x=self.group:self.transcriber.set_value(x)
        b=SortGlyphGroupButtonFrame(examplesframe, self,
                                group=self.group,
                                showtonegroup=True,
                                on_select=cmd,
                                playable=True,
                                alwaysrefreshable=True,
                                row=0, column=0, sticky='w',
                                wraplength=self.buttonframew
                                )
        self.window_failed=False
        if not b.hasexample:
            self.clear_runwindow()
            self.window_failed=True
            return
        self.compframe=ui.Frame(examplesframe,
                    highlightthickness=10,
                    highlightbackground=self.frame.theme.white,
                    pady=20, row=1, column=0, sticky='',
                    columnspan=2
                    ) #no hlfg here
        t=_('Compare with another group')
        fn=self.setgroup_comparison
        self.sub_c=ui.Button(self.compframe,
                            text = t,
                            command = lambda:fn(),
                            row=0,column=0
                            )
        self.comparisonbuttons()
        self.runwindow.waitdone()
        self.sub_c.wait_window(self.runwindow) #then move to next step
        if hasattr(self,'status'): #i.e., working from Transcribe task directly
            self.status.updateglyphbuttons()
        """Store these variables above, finish with (destroying window with
        local variables):"""
    def __init__(self, parent):
        self.switch_text=_("Switch letters with this group")
        self.switch_tt=_("This switches letters for the two groups, and "
                            "updates each of them")
        Transcribe.__init__(self,parent)
        Segments.__init__(self,parent)
class TranscribeV(TranscribeS):
    def tasktitle(self):
        return _("Vowel Letters")
    def tooltip(self):
        return _("This task helps you decide on your vowel letters.")
    def taskicon(self):
        return self.program.theme.photo['iconTranscribeV']
    def __init__(self, parent): #frame, filename=None
        self.glyphspossible=[ #'a','e','i','o','u','ɛ','ɔ','ɨ','ʉ']
        #tilde (decomposed):
        'ã', 'ẽ', 'ɛ̃', 'ə̃', 'ɪ̃', 'ĩ', 'õ', 'ɔ̃', 'ũ', 'ʊ̃',
        #Combining Greek Perispomeni (decomposed):
        'a͂', 'i͂', 'o͂', 'u͂',
        #single code point vowels:
        'a', 'e', 'i', 'ə', 'o', 'u',
        # 'A', 'E', 'I', 'Ə', 'O', 'U',
        'ɑ', 'ɛ', 'ɨ', 'ɔ', 'ʉ', 'ɩ',
        'æ', 'ʌ', 'ɪ', 'ï', 'ö', 'ʊ',
        #for those using precomposed letters:
        # 'à', 'è', 'ì', 'ò', 'ù',
        # # 'À', 'È', 'Ì', 'Ò', 'Ù',
        # 'á', 'é', 'í', 'ó', 'ú',
        # # 'Á', 'É', 'Í', 'Ó', 'Ú',
        # 'â', 'ê', 'î', 'ô', 'û',
        # # 'Â', 'Ê', 'Î', 'Ô', 'Û',
        # 'ã', 'ẽ', 'ĩ', 'õ', 'ũ'
        ]
        self.cvt=self.program.params.cvt('V')
        super().__init__(parent)
class TranscribeC(TranscribeS):
    def tasktitle(self):
        return _("Consonant Letters")
    def tooltip(self):
        return _("This task helps you decide on your consonant letters.")
    def taskicon(self):
        return self.program.theme.photo['iconTranscribeC']
    def __init__(self, parent): #frame, filename=None
        self.glyphspossible=[#'p','b','k','g','d','t',]
        'bh','dh','gh','gb',
        'b',#'B',
        'd','g','ɡ', #,'G' messes with profiles
        'kk','kp',
        'p',#'P',
        'ɓ',#'Ɓ',
        't','ɗ','ɖ','c','k','q',
        'vh','zh',
        'j',#'J',
        'v','z',#'Z',
        'ʒ','ð','ɣ',
        'ch','ph','sh','hh','pf','bv',
        # 'F',
        'f','s','ʃ','θ','x','h', #not 'S'
        'dj','dz','dʒ',
        'chk',
        'ts','tʃ',
        'zl',
        'ɮ',
        'sl',
        'ɬ',
        'ʔ',
                "ꞌ", #Latin Small Letter Saltillo
                "'", #Tag Apostrophe
                'ʼ', #modifier letter apostrophe
        'ẅ','y',#'Y',
        'w',#'W',
        'm',#'M',
        'n','ŋ','ɲ','ɱ', #'N', messed with profiles
        'mm','ŋŋ','ny',
        "ng'",
        # """Non-Nasal/Glide Sonorants"""
        'l','r',
        'rh','wh',
        ]
        self.cvt=self.program.params.cvt('C')
        super().__init__(parent)
class TranscribeT(Transcribe,Tone):
    def tasktitle(self):
        return _("Transcribe Tone")
    def tooltip(self):
        return _("This task helps you transcribe your surface groups, giving "
                "them meaniningful names (e.g., [˥˥ ˨˨]) instead of numbers.")
    def dobuttonkwargs(self):
        return {'text':_("Transcribe Surface Tone Groups"),
                'fn':self.makewindow,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['Transcribe'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return self.program.theme.photo['iconTranscribe']
    def done(self):
        log.info("Transcribe done")
        self.submitform()
        self.donewpyaudio()
    def set_ok_w_form(self):
        pass #maybe use some day?
    def makewindow(self, group=None, event=None):
        if group:
            self.group=self.program.status.group(group)
        """Go through this and tease apart what is needed for tone complexity,
        and move that to tone.
        Note to user: you can't pick these group names (switch later, not here)
        Make another function to switch letters between groups."""
        # log.info("Making transcribe window")
        def changegroupnow(event=None):
            w=self.program.taskchooser.getgroup(wsorted=True)
            self.runwindow.wait_window(w)
            if not w.exitFlag.istrue():
                self.runwindow.on_quit()
                self.makewindow()
        cvt=self.program.params.cvt()
        ps=self.program.slices.ps()
        profile=self.program.slices.profile()
        check=self.program.params.check()
        self.buttonframew=int(self.program.screenw/3.5)
        if not check:
            self.getcheck(guess=True)
            if check is None:
                # log.info("I asked for a check name, but didn't get one.")
                return
        if not self.program.status.groups(wsorted=True):
            log.error(_("I don't have any sorted data for check: {check}, "
                        "ps-profile: {ps}-{profile},").format(check=check,ps=ps,profile=profile))
            return
        groupsok=self.updategroups()
        if not groupsok:
            log.error("Problem with log; check earlier message.")
            return
        padx=50
        if self.program.settings.lowverticalspace:
            log.info("Using low vertical space setting")
            pady=0
        else:
            pady=10
        title=_("Rename {ps} {profile} {noun_sg} group ‘{group}’ in ‘{check}’ frame"
                        ).format(ps=ps,profile=profile,
                        noun_sg=self.program.params.cvtdict()[cvt]['sg'],
                        group=self.group,check=check)
        self.getrunwindow(title=title)
        titlel=ui.Label(self.runwindow.frame,text=title,font='title',
                        row=0,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getformtext=[_("What new name do you want to call this {sg} "
                        "group?").format(sg=self.program.params.cvtdict()[cvt]['sg'])]
        if cvt == 'T':
            getformtext.append(_("A label that describes the surface tone form "
                        "in this context would be best, like ‘[˥˥˥ ˨˨˨]’"))
        getform=ui.Label(self.runwindow.frame,
                        text='\n'.join(getformtext),
                        font='read',
                        norender=True,
                        row=1,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getform.wrap()
        inputfeedbackframe=ui.Frame(self.runwindow.frame,
                            row=2,column=0,sticky=''
                            )
        self.transcriber=transcriber.Transcriber(inputfeedbackframe,
                                initval=self.group,
                                soundsettings=self.soundsettings,
                                chars=self.glyphspossible,
                                row=0,column=0,sticky=''
                                )
        self.transcriber.formfield.bind('<KeyRelease>', self.updateerror)
        infoframe=ui.Frame(inputfeedbackframe,
                            row=0,column=1,sticky=''
                            )
        """Make this a pad of buttons, rather than a label, so users can
        go directly where they want to be"""
        g=nn(self.othergroups,perline=len(self.othergroups)//5)
        # log.info("There: {}, NTG: {}; g:{}".format(self.groups,
        #                                             self.othergroups,g))
        groupslabel=ui.Label(infoframe,
                            text='\n'.join([_('Other Groups:'),g]),
                            row=0,column=1,
                            sticky='new',
                            padx=padx,
                            rowspan=2
                            )
        groupslabel.bind('<ButtonRelease-1>',changegroupnow)
        self.errorlabel=ui.Label(infoframe,text='',
                            fg='red',
                            wraplength=int(self.frame.winfo_screenwidth()/3),
                            row=2,column=1,sticky='nsew'
                            )
        responseframe=ui.Frame(self.runwindow.frame,
                                row=3,
                                column=0,
                                sticky='',
                                padx=padx,
                                pady=pady,
                                )
        self.oktext=_('Use this name and go to:')
        column=0
        sub_lbl=ui.Label(responseframe,text = self.oktext, font='read',
                        row=0,column=column,sticky='ns'
                        )
        buttons=[
                (_('main screen'), self.done),
                (_('next group'), self.next)]
        if cvt == 'T':
            buttons+=[(_('next tone frame'), self.nextcheck)]
        else:
            buttons+=[(_('next check'), self.nextcheck)]
        buttons+=[(_('next syllable profile'), self.nextprofile),
                (_('comparison group'), self.submitandswitch)
                ]
        for button in buttons:
            column+=1
            ui.Button(responseframe,text = button[0], command = button[1],
                                anchor ='c',
                                row=0,column=column,sticky='ns'
                                )
        examplesframe=ui.Frame(self.runwindow.frame,
                                row=4,column=0,sticky=''
                                )
        b=SortGroupButtonFrame(examplesframe, self,
                                group=self.group,
                                showtonegroup=True,
                                # canary=entryview,
                                playable=True,
                                unsortable=True,
                                alwaysrefreshable=True,
                                row=0, column=0, sticky='w',
                                wraplength=self.buttonframew
                                )
        self.compframe=ui.Frame(examplesframe,
                    highlightthickness=10,
                    highlightbackground=self.frame.theme.white,
                    row=0,column=1,sticky='e'
                    ) #no hlfg here
        t=_('Compare with another group')
        self.sub_c=ui.Button(self.compframe,
                        text = t,
                        command = self.setgroup_comparison,
                        row=0,column=0
                        )
        self.comparisonbuttons()
        self.runwindow.waitdone()
        self.sub_c.wait_window(self.runwindow) #then move to next step
        """Store these variables above, finish with (destroying window with
        local variables):"""
    def __init__(self, parent): #frame, filename=None
        self.switch_text=_("Switch transcriptions with this group")
        self.switch_tt=_("This doesn't save the curent group")
        Tone.__init__(self)
        self.glyphspossible=None
        Transcribe.__init__(self,parent)
        self.program.params.cvt('T')
class JoinUFgroups(Tone,Task):
    """docstring for JoinUFgroups."""
    def tasktitle(self):
        return _("Join Underlying Form Groups")
    def tooltip(self):
        return _("This task helps you join hypersplit UF groups, as well as "
                "giving them meaniningful names (e.g., High or Low).")
    def dobuttonkwargs(self):
        return {'text':_("Join draft UF Groups"),
                'fn':self.tonegroupsjoinrename,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['JoinUF'], #self.cvt
                'sticky':'ew'
                }
    def taskicon(self):
        return self.program.theme.photo['iconJoinUF']
    def tonegroupsjoinrename(self,**kwargs):
        def clearerror(event=None):
            errorlabel['text'] = ''
        def submitform():
            clearerror()
            uf=named.get()
            if uf == '':
                noname=_("Give a name for this UF tone group!")
                log.debug(noname)
                errorlabel['text'] = noname
                return
            groupsselected=[]
            for group in groupvars: #all group variables
                groupsselected+=[group.get()] #value, name if selected, 0 if not
            groupsselected=[x for x in groupsselected if x != '']
            log.info(f"groupsselected:{groupsselected}")
            if uf in self.analysis.orderedUFs and uf not in groupsselected:
                deja=_("That name is already there! (did you forget to include "
                        "the ‘{uf}’ group?)").format(uf=uf)
                log.debug(deja)
                errorlabel['text'] = deja
                return
            for group in groupsselected:
                if group in self.analysis.sensesbygroup: #selected ones only
                    log.debug(_("Changing values from {group} to {uf} for the "
                            "following sense.ids: {ids}").format(group=group,uf=uf,
                            ids=[i.id for i in self.analysis.sensesbygroup[group]]))
                    for sense in self.analysis.sensesbygroup[group]:
                        sense.uftonevalue(uf)
            self.maybewrite()
            self.runwindow.on_quit()
            self.program.status.last('joinUF',update=True)
            self.tonegroupsjoinrename() #call again, in case needed
        self.makeanalysis()
        def redo(timestamps=_("By manual request")):
            self.wait(_("Redoing Tone Analysis")+'\n'+timestamps)
            self.analysis.do()
            self.waitdone()
            # self.runwindow.on_quit()
            self.tonegroupsjoinrename(redo=True) #call again, in case needed
        def done():
            self.runwindow.on_quit()
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        analysisOK,joinedsince,timestamps=self.program.status.isanalysisOK(**kwargs) #Should specify which lasts...
        if not analysisOK:
            if not kwargs.get('redo'):
                #otherwise, the user will almost certainly be upset to have to do it later
                redo(timestamps)
            else:
                txt=_("The analysis still isn't OK after retrying; "
                        "Check your settings and try again (e.g., "
                        "{ps} {profile} checks: {checks})").format(ps=ps, profile=profile, checks=self.program.status.checks())
                ErrorNotice(txt,wait=True,parent=self)
            return
        self.getrunwindow(msg=_("Preparing to join draft underlying form groups"
                                "")+'\n'+timestamps)
        self.update()
        title=_("Join/Rename Draft Underlying {ps}-{profile} tone groups").format(
                                                        ps=ps,profile=profile)
        self.runwindow.title(title)
        padx=50
        pady=10
        rwrow=gprow=qrow=0
        t=ui.Label(self.runwindow.frame,text=title,font='title')
        t.grid(row=rwrow,column=0,sticky='ew')
        redotext=_("Redo the analysis;\nstart these groups over")
        text=_("This page allows you to join the {ps}-{profile} draft underlying tone "
                "groups created for you by {program}, \nwhich are almost certainly "
                "too small for you. \nLooking at a draft report, and making "
                "your own judgement about which groups belong together, select "
                "all the groups that belong together in one group, and "
                "give that new group "
                "a name. You can then repeat this for other groups "
                "that should be joined. \nIf for any reason you want to undo "
                "the groups you create here, you can start over with an new "
                "analysis by pressing the ‘{redo}’ button. \nOtherwise, these "
                "joined groups will be reflected in reports until you sort "
                "more data.").format(ps=ps,profile=profile,program=self.program.name,
                                                redo=redotext.replace('\n',' '))
        rwrow+=1
        i=ui.Label(self.runwindow.frame,text=text,
                    row=rwrow,column=0,sticky='ew')
        i.wrap()
        ui.Button(self.runwindow.frame,text=redotext, cmd=redo,
                    row=rwrow,column=1,sticky='ew')
        rwrow+=1
        qframe=ui.Frame(self.runwindow.frame)
        qframe.grid(row=rwrow,column=0,sticky='ew')
        text=_("What do you want to call this UF tone group for {ps}-{profile} words?"
                "").format(ps=ps,profile=profile)
        qrow+=1
        q=ui.Label(qframe,text=text,
                    row=qrow,column=0,sticky='ew',pady=20
                    )
        q.wrap()
        named=ui.StringVar() #store the new name here
        namefield = ui.EntryField(qframe,text=named)
        namefield.grid(row=qrow,column=1)
        namefield.bind('<Key>', clearerror)
        errorlabel=ui.Label(qframe,text='',fg='red')
        errorlabel.grid(row=qrow,column=2,sticky='ew',pady=20)
        text=_("Select the groups below that you want in this {ps} group, then "
                "click ==>").format(ps=ps)
        qrow+=1
        d=ui.Label(qframe,text=text)
        d.grid(row=qrow,column=0,sticky='ew',pady=20)
        sub_btn=ui.Button(qframe,text = _("OK"), command = submitform, anchor ='c')
        sub_btn.grid(row=qrow,column=1,sticky='w')
        done_btn=ui.Button(qframe,text = _("Done —no change"), command = done,
                                                                    anchor ='c')
        done_btn.grid(row=qrow,column=2,sticky='w')
        groupvars=list()
        rwrow+=1
        scroll=ui.ScrollingFrame(self.runwindow.frame)
        scroll.grid(row=rwrow,column=0,sticky='ew')
        self.analysis.donoUFanalysis()
        nheaders=0
        if not self.analysis.orderedUFs:
            self.runwindow.waitdone()
            self.runwindow.on_quit()
            ErrorNotice(title=_("No draft UF groups found for {ps} words!"
                                "").format(ps=ps),
                        text=_("You don't seem to have any analyzed {ps} groups "
                        "to join/rename. Have you done a tone analyis for {ps} "
                        "words?").format(ps=ps)
                        )
            return
        # ufgroups= # order by structured groups? Store this somewhere?
        for group in self.analysis.orderedUFs: #make a variable and button to select
            idn=self.analysis.orderedUFs.index(group)
            if idn % 5 == 0: #every five rows
                col=1
                for check in self.analysis.orderedchecks:
                    col+=1
                    cbh=ui.Label(scroll.content, text=check, font='small')
                    cbh.grid(row=idn+nheaders,
                            column=col,sticky='ew')
                nheaders+=1
            groupvars.append(ui.StringVar())
            n=len(self.analysis.sensesbygroup[group])
            buttontext=f'{group} ({n})'
            cb=ui.CheckButton(scroll.content, text = buttontext,
                                variable = groupvars[idn],
                                onvalue = group, offvalue = 0,
                                )
            cb.grid(row=idn+nheaders,column=0,sticky='ew')
            # analysis.valuesbygroupcheck[group]:
            col=1
            for check in self.analysis.orderedchecks:
                col+=1
                if check in self.analysis.valuesbygroupcheck[group]:
                    cbl=ui.Label(scroll.content,
                        text=unlist(
                                self.analysis.valuesbygroupcheck[group][check]
                                    )
                            )
                    cbl.grid(row=idn+nheaders,column=col,sticky='ew')
        self.runwindow.waitdone()
        self.runwindow.wait_window(scroll)
    def __init__(self, parent):
        Tone.__init__(self)
        Task.__init__(self, parent)
class RecordCitation(Record,Segments):
    def tooltip(self):
        return _("This task helps you record words in isolation forms.")
    def dobuttonkwargs(self):
        return {'text':_("Record Dictionary Words"),
                'fn':self.showentryformstorecord,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['WordRec'],
                'sticky':'ew'
                }
    def tasktitle(self):
        return _("Record Words") #Citation Forms
    def taskicon(self):
        return self.program.theme.photo['iconWordRec']
    def __init__(self, parent): #frame, filename=None
        Segments.__init__(self,parent)
        # ui.Window.__init__(self,parent)
        # Task.__init__(self,parent)
        Record.__init__(self,parent)
class RecordCitationT(Record,Tone):
    def tooltip(self):
        return _("This task helps you record words in tone frames, in citation form.")
    def dobuttonkwargs(self):
        return {'text':_("Record Words in Tone Frames"),
                'fn':self.showtonegroupexs,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['TRec'],
                'sticky':'ew'
                }
    def taskicon(self):
        return self.program.theme.photo['iconTRec']
    def tasktitle(self):
        return _("Record Tone") #Citation Form Sorting in Tone Frames
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self)
        Record.__init__(self,parent)
class ReportCitation(Report,Segments,Task):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report (Not background)") # on One Data Slice
    def taskicon(self):
        return self.program.theme.photo['iconReport']
    def tooltip(self):
        return _("This report gives you reports for one lexical "
                "category, in one syllable profile. \nIt does "
                "one of three sets of reports: \n- Vowel, \n- Consonant, or "
                "\n- Consonant-Vowel Correspondence")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['Report'],
                'sticky':'ew'
                }
    def runcheck(self):
        """This needs to get stripped down and updated for just this check"""
        self.program.settings.storesettingsfile()
        t=(_('Run Check'))
        log.info("Running report...")
        log.info("Using these regexs: {rx}".format(rx=self.rxdict))
        # exit() #for testing
        i=0
        cvt=self.program.params.cvt()
        if cvt == 'T':
            w=self.program.taskchooser.getcvt()
            w.wait_window(w)
            cvt=self.program.params.cvt()
            if cvt == 'T':
                ErrorNotice(_("Pick Consonants, Vowels, or CV for this report."))
                return
        ps=self.program.slices.ps()
        if not ps:
            self.getps()
        check=self.program.params.check()
        profile=self.program.slices.profile()
        if not profile:
            self.getprofile()
        if not profile or not ps:
            window=ui.Window(self)
            text=_('Error: please set Ps-Profile first! ({ps}/{check}/{profile})').format(
                                                     ps=ps,check=check,profile=profile)
            ui.Label(window,text=text).grid(column=0, row=i)
            i+=1
            return
        log.info(_('Ps-Profile-Check OK; doing getresults! ({ps}/{check}/{profile})').format(
                                                 ps=ps,check=check,profile=profile))
        self.getresults()
    def __init__(self, parent): #frame, filename=None
        self.program.params.ftype('lc')
        Segments.__init__(self,parent)
        self.do=self.getresults
        self.program.status.group(None) #default to reports with all groups
        Task.__init__(self,parent)
        Report.__init__(self)
class ReportCitationBackground(Background,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self,parent)
        Background.__init__(self)
        """Does the above not work? was turned off..."""
        # self.do=lambda fn=self.getresults:self.background(fn)
        # self.status.redofinalbuttons() #because the fns changed
class ReportCitationMulticheckBackground(Multicheck,Background,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report (checks)") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self,parent)
        Multicheck.__init__(self)
        Background.__init__(self)
class ReportCitationMultichecksliceBackground(Multicheckslice,Background,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report (slices/checks)") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self,parent)
        Multicheckslice.__init__(self)
        Background.__init__(self)
class ReportCitationByUF(ByUF,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone group (not background)") # on One Data Slice
    def __init__(self, parent):
        ReportCitation.__init__(self, parent)
        ByUF.__init__(self)
class ReportCitationByUFMulticheckBackground(Multicheck,Background,ReportCitationByUF):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone group (checks)") # on One Data Slice
    def __init__(self, parent):
        ReportCitationByUF.__init__(self, parent)
        Multicheck.__init__(self)
        Background.__init__(self)
class ReportCitationByUFMultichecksliceBackground(Multicheckslice,Background,ReportCitationByUF):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone Group (slices/checks)") # on One Data Slice
    def __init__(self, parent):
        ReportCitationByUF.__init__(self,parent)
        Multicheckslice.__init__(self)
        Background.__init__(self)
class ReportCitationByUFBackground(ByUF,ReportCitationBackground):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Alphabet Report by Tone group") # on One Data Slice
    def __init__(self, parent):
        ReportCitationBackground.__init__(self, parent)
        ByUF.__init__(self)
class ReportCitationMultislice(MultisliceS,ReportCitation):
    """docstring for ReportCitation."""
    def tasktitle(self):
        return _("Multislice Alphabet Report") # on Citation Forms
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['VCCVRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        ReportCitation.__init__(self,parent)
        self.cvtstodo=['V','C','CV']
        MultisliceS.__init__(self)
class ReportConsultantCheck(Report,Tone,Task):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Consultant Check")
    def taskicon(self):
        return self.program.theme.photo['icontall']
    def tooltip(self):
        return _("This task automates work normally done before a consultant "
                "check: \n- reloads status data, and \n- runs comprehensive tone "
                "reports, \n  - by location and \n  - by lexeme sense.")
    def dobuttonkwargs(self):
        return {'text':'\n'.join([_("Start!"),_("Profiles first!")]),
                'fn':self.consultantcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['icontall'],
                'sticky':'ew'
                }
    def __init__(self, parent): #frame, filename=None
        Tone.__init__(self)
        Task.__init__(self,parent)
        Report.__init__(self)
class ReportCitationT(Report,Tone,Task):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report (not backgrounded)")
    def taskicon(self):
        return self.program.theme.photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['TRep'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        Tone.__init__(self)
        self.do=self.tonegroupreport
        Task.__init__(self,parent)
        Report.__init__(self)
        self.bylocation=False
class ReportCitationTBackground(Background,ReportCitationT):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report")
    def taskicon(self):
        return self.program.theme.photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['TRep'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationT.__init__(self,parent)
        Background.__init__(self)
class ReportCitationTL(ReportCitationT):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report (by frames, not backgrounded)")
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by frame.")
    def __init__(self, parent):
        ReportCitationT.__init__(self,parent)
        self.bylocation=True
class ReportCitationTLBackground(Background,ReportCitationTL):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Tone Report (by frames)")
    def taskicon(self):
        return self.program.theme.photo['iconTRep']
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by frame.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['TRep'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationTL.__init__(self,parent)
        Background.__init__(self)
class ReportCitationMultisliceT(MultisliceT,ReportCitationT):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Multislice Tone Report (not background)")
    def taskicon(self):
        return self.program.theme.photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['TRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationT.__init__(self,parent)
        MultisliceT.__init__(self)
class ReportCitationMultisliceTL(MultisliceT,ReportCitationTL):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Multislice Tone Report (not background)")
    def taskicon(self):
        return self.program.theme.photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['TRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationTL.__init__(self,parent)
        MultisliceT.__init__(self)
class ReportCitationMultisliceTBackground(Background,ReportCitationMultisliceT):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Multislice Tone Report")
    def taskicon(self):
        return self.program.theme.photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['TRepcomp'],
                'sticky':'ew'
                }
    def __init__(self, parent):
        ReportCitationMultisliceT.__init__(self,parent)
        Background.__init__(self)
class ReportCitationMultisliceTLBackground(Background,ReportCitationMultisliceTL):
    """docstring for ReportCitationT."""
    def tasktitle(self):
        return _("Multislice Tone Report (by location)")
    def taskicon(self):
        return self.program.theme.photo['iconTRepcomp']
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def __init__(self, parent):
        ReportCitationMultisliceTL.__init__(self,parent)
        Background.__init__(self)