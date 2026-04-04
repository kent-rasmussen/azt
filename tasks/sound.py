import backend.core.sound
from frontend import sound_ui, ui_shell as ui
from utilities import logsetup as log
from io_put import lift

class Sound(backend.core.sound.Sound):
    """UI task mixin for audio settings and configuration."""
    is_sound_task=True
    def _configure_sound(self,event=None):
        sound_ui.SoundSettingsWindow(self)

    def setcontext(self,context=None):
        if hasattr(super(), 'setcontext'):
            super().setcontext(context)
        self.context.menuitem("Sound settings",self._configure_sound)

    def soundcheck(self):
        if super().soundcheck(): # If backend says settings are missing
             self.mikecheck()

    def mikecheck(self):
        self.ui.withdraw()
        self.pyaudiocheck()
        self.soundsettingswindow=sound_ui.SoundSettingsWindow(self)
        self.soundsettingswindow.protocol("WM_DELETE_WINDOW", self.quittask)
        if not self.soundsettingswindow.exitFlag.istrue():
            self.soundsettingswindow.wait_window(self.soundsettingswindow)
        self.donewpyaudio()
        self.ui.deiconify()
        if not self.ui.exitFlag.istrue() and self.soundsettingswindow.winfo_exists():
            self.soundsettingswindow.destroy()

    def _configure_transcription(self,event=None):
        sound_ui.ASRModelSelectionWindow(self)

    def setcontext(self,context=None):
        backend.core.sound.Sound.setcontext(self) # Need to handle which context?
        # Re-applying context logic from tasks.py
        if hasattr(super(), 'setcontext'):
            super().setcontext(context)
        self.context.menuitem("Transcription settings",
                                    self._configure_transcription)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.soundcheck()

class Record(backend.core.sound.Record, Sound):
    """UI task mixin for recording widgets and session windows."""
    is_record_task=True
    icon_leaderboard=True
    def makelabelsnrecordingbuttons(self,parent,node,r,c):
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
        parentframe.destroy()
        gc.collect()

    def showentryformstorecordpage(self):
        if self.ui.runwindow.exitFlag.istrue():
            return
        if not self.ui.runwindow.frame.winfo_exists():
            return
        self.ui.runwindow.resetframe()
        ps=self.program.slices.ps()
        profile=self.program.slices.profile()
        count=self.program.slices.count()
        text="Record {profile} {ps} Words: click 'Record', talk, and release ({count} words)".format(profile=profile,ps=ps,count=count)
        log.info(text)
        instr=ui.Label(self.ui.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w')
        senses=self.program.slices.senses(ps=ps,profile=profile)
        if not senses:
            senses=self.program.db.senses
        nperpage=5
        pages=[senses[i:i+nperpage] for i in range(0,len(senses),nperpage)]
        for page in pages:
            if self.ui.runwindow.exitFlag.istrue():
                return
            self.ui.runwindow.wait(thenshow=True)
            buttonframes=ui.ScrollingFrame(self.ui.runwindow.frame,
                                            row=1,column=0,sticky='w')
            row=0
            done=list()
            for row,entry in enumerate([i.entry for i in page]):
                self.ui.runwindow.column=0
                if entry.guid in done:
                    continue
                else:
                    done.append(entry.guid)
                ftypes=['lc','pl','imp']
                for node in [entry.sense.nodebyftype(f) for f in ftypes
                                if entry.sense.nodebyftype(f)]:
                    self.ui.runwindow.column+=2
                    self.makelabelsnrecordingbuttons(buttonframes.content,node,
                        row,self.ui.runwindow.column)
            ui.Button(buttonframes.content,column=1,row=row,
                        text="Next {count} words".format(count=nperpage),
                        cmd=lambda x=buttonframes:self.cleanup_pa(x))
            self.ui.runwindow.waitdone()
            buttonframes.wait_window(buttonframes)
        if not self.ui.runwindow.exitFlag.istrue():
            self.ui.runwindow.wait_window(self.ui.runwindow.frame)

    def showentryformstorecord(self,justone=False):
        self.ui.getrunwindow()
        if justone or not self.program.slices.valid():
            self.showentryformstorecordpage()
        else:
            ps=self.program.slices.ps()
            profile=self.program.slices.profile()
            for psprofile in self.program.slices.valid():
                if self.ui.runwindow.exitFlag.istrue():
                    return 1
                self.program.slices.ps(psprofile[1])
                self.program.slices.profile(psprofile[0])
                nextb=ui.Button(self.ui.runwindow,text="Next Group",
                                        cmd=self.ui.runwindow.resetframe)
                nextb.grid(row=0,column=1,sticky='ne')
                self.showentryformstorecordpage()
            self.program.slices.ps(ps)
            self.program.slices.profile(profile)
        self.donewpyaudio()

    def showsenseswithexamplestorecord(self,senses=None,progress=None,skip=False):
        def setskip(event):
            self.ui.runwindow.frame.skip=True
            entryframe.destroy()
        self.ui.getrunwindow()
        if self.ui.exitFlag.istrue() or self.ui.runwindow.exitFlag.istrue():
            return
        if skip == 'skip':
            self.ui.runwindow.frame.skip=True
        else:
            self.ui.runwindow.frame.skip=skip
        text="Words and phrases to record: click 'Record', talk, and release"
        instr=ui.Label(self.ui.runwindow.frame, anchor='w',text=text)
        instr.grid(row=0,column=0,sticky='w',columnspan=2)
        if senses is None:
            senses=self.program.settings.entriestoshow
        for sense in senses:
            examples=list(sense.examples.values())
            if examples == []:
                continue
            if ((self.ui.runwindow.frame.skip == True) and
                (lift.atleastoneexamplehaslangformmissing(examples,
                                     self.program.settings.audiolang) == False)):
                continue
            row=0
            if self.ui.runwindow.exitFlag.istrue():
                return 1
            entryframe=ui.Frame(self.ui.runwindow.frame)
            entryframe.grid(row=1,column=0)
            if progress is not None:
                progressl=ui.Label(self.ui.runwindow.frame, anchor='e',
                    font='small',
                    text='({} {}/{})'.format(*progress)
                    )
                progressl.grid(row=0,column=2,sticky='ne')
            text=sense.formatted(self.analang,self.glosslangs)
            if not text:
                entryframe.destroy()
                continue
            ui.Label(entryframe, anchor='w', font='read',
                    text=text).grid(row=row,
                                    column=0,sticky='w')
            self.ui.runwindow.frame.scroll=ui.ScrollingFrame(entryframe)
            self.ui.runwindow.frame.scroll.grid(row=1,column=0,sticky='w')
            examplesframe=ui.Frame(self.ui.runwindow.frame.scroll.content)
            examplesframe.grid(row=0,column=0,sticky='w')
            for example in examples:
                if (skip == True and
                    lift.examplehaslangform(example,self.program.settings.audiolang) == True):
                    continue
                text=example.formatted(self.analang,self.glosslangs)
                if not text:
                    continue
                row+=1
                rb=sound_ui.RecordButtonFrame(examplesframe,self,example)
                rb.grid(row=row,column=0,sticky='w')
                ui.Label(examplesframe, anchor='w',text=text
                                        ).grid(row=row, column=1, sticky='w')
            row+=1
            d=ui.Button(examplesframe, text="Done/Next",command=entryframe.destroy)
            d.grid(row=row,column=0)
            self.ui.runwindow.waitdone()
            if self.ui.runwindow.exitFlag.istrue():
                return 1
            if self.ui.runwindow.frame.skip == True:
                return 'skip'

    def showtonegroupexs(self):
        def next_p():
            self.program.status.nextprofile()
            self.ui.runwindow.on_quit()
            self.showtonegroupexs()
        self.makeanalysis()
        self.analysis.donoUFanalysis()
        torecord=self.analysis.sensesbygroup
        if not torecord:
             self.analysis.do()
             self.showtonegroupexs()
             return
        skip=False
        for i in range(self.examplespergrouptorecord):
            for ufgroup in torecord:
                if len(torecord[ufgroup]) > i:
                    sense=torecord[ufgroup][i]
                    exited=self.showsenseswithexamplestorecord([sense],
                                (ufgroup, i+1, self.examplespergrouptorecord),
                                skip=skip)
                    if exited == 'skip': skip=True
                    if exited == True: return
        if not (self.ui.runwindow.exitFlag.istrue() or self.ui.exitFlag.istrue()):
            self.ui.runwindow.waitdone()
            self.ui.runwindow.resetframe()
            ui.Label(self.ui.runwindow.frame, anchor='w',font='read',
            text="All done! Sort some more words, and come back."
            ).grid(row=0,column=0,sticky='w')
            ui.Button(self.ui.runwindow.frame,
                    text="Continue to next syllable profile",
                    command=next_p).grid(row=1,column=0)
        self.donewpyaudio()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
