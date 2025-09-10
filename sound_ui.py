#!/usr/bin/env python3
# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import ui_tkinter as ui
import sound
import file
import utilities as utils
import executables
class RecordButtonFrame(ui.Frame):
    """This is not implemented yet!!"""
    def _start(self, event=None):
        log.log(3,"Asking PA to record now")
        self.recorder.start()
    def _stop(self, event=None):
        try:
            self.recorder.stop()
            # log.info(f"self.recorder: {hasattr(self,'recorder')}")
        except Exception as e:
            log.info("Couldn't stop recorder; was it on? ({})".format(e))
        """This is done in advance of recording now:"""
        if self.recorder.file_write_OK:
            self.b.destroy()
            self.makeplaybutton()
            self.makedeletebutton()
            self.addlink()
    def _redo(self, event=None):
        log.log(3,"I'm deleting the recording now")
        self.p.destroy()
        self.makerecordbutton()
        self.r.destroy()
    def makebuttons(self):
        if self.soundsettings.file_ok(self._filenameURL):
            self.makeplaybutton()
            self.makedeletebutton()
            self.addlink()
        else:
            self.makerecordbutton()
    def makerecordbutton(self):
        # if not hasattr(self,'recorder'):
        #     log.debug(f"PA recorder init ({vars(self)})")
        #     self.recorder=sound.SoundFileRecorder(self._filenameURL,self.pa,
        #                                     self.soundsettings)
        #     log.debug(f"PA recorder ({type(self.recorder)}) init ({vars(self)})")
        # log.debug("PA recorder made OK")
        self.b=ui.Button(self, command=self.function,
                        image='record',
                        ipadx=20, ipady=15
                        )
        self.b.grid(row=0, column=0,sticky='w')
        self.b.bind('<ButtonPress-1>', self._start)
        self.b.bind('<ButtonRelease-1>', self._stop)
        self.bt=ui.ToolTip(self.b,_("press-speak-release"))
    def _play(self,event=None):
        log.debug("Asking PA to play now")
        utils.tryrun(self.player.play)
    def makeplaybutton(self):
        self.p=ui.Button(self, text='‣', command=self._play,
                        font='readbig',
                        ipadx=20, ipady=0
                        )
        #Not using these for now
        # self.p.bind('<ButtonPress>', self._play)
        # self.p.bind('<ButtonRelease>', self.function)
        self.p.grid(row=0, column=1,sticky='nsw')
        pttext=_("Click to hear")
        if 'praat' in self.program:
            pttext+='; '+_("right click to open in praat")
            self.p.bind('<Button-3>',
                        lambda x: executables.praatopen(
                                                    self.program,
                                                    self._filenameURL))
        self.pt=ui.ToolTip(self.p,pttext)
    def makedeletebutton(self):
        self.r=ui.Button(self,text='×',font='read',command=self.function,
                        row=0, column=2, sticky='nsw')
        self.r.bind('<ButtonRelease-1>', self._redo)
        self.rt=ui.ToolTip(self.r,_("Try again"))
        self.r.update_idletasks()
    def function(self):
        pass
    def addlink(self):
        if self.test:
            return
        self.program['db'].addmediafields(self.node,self.filename,
                                self.program['params'].audiolang(),
                                # ftype=ftype,
                                write=False)
        self.task.maybewrite()
        self.program['status'].last('recording',update=True)
    def __init__(self,parent,task,node=None,**kwargs): #filenames
        """Uses node to make framed data, just for soundfile name"""
        """Without node, this just populates a sound file, with URL as
        provided. The LIFT link to that sound file should already be there."""
        # This class needs to be cleanup after closing, with check.donewpyaudio()
        """Originally from https://realpython.com/playing-and-recording-
        sound-python/"""
        self.id=id
        self.task=task
        try:
            task.pyaudio.get_format_from_width(1) #get_device_count()
        except:
            task.pyaudio=sound.AudioInterface()
        self.pa=task.pyaudio
        if not hasattr(task,'soundsettings') or not hasattr(task,'program'):
            log.error("task missing a settings attr? "
                        f"(soundsettings:{hasattr(task,'soundsettings')}; "
                        f"program:{hasattr(task,'program')})")
            exit()
        self.soundsettings=task.soundsettings
        self.program=task.program
        # log.info("RecordButtonFrame found program settings "
        #         f"{self.program}")
        # log.info("RecordButtonFrame started with soundsettings "
        #         f"{vars(self.soundsettings)}")
        self.callbackrecording=True
        self.chunk = 1024  # Record in chunks of 1024 samples (for block only)
        self.channels = 1 #Always record in mono
        self.test=kwargs.pop('test',None)
        # log.info(f"Working with node: {node} "
        #         f"({node.tag if node is not None else ''})"
        #         f": {vars(node) if node is not None else ''}")
        if node is not None and node.isnode():
            task.makeaudiofilename(node) #should fill out the following
            self.filename=node.textvaluebylang(
                                            self.program['params'].audiolang())
            if not self.filename: #should have above or below
                self.filename=node.audiofilenametoput
            self._filenameURL=node.audiofileURL
            self.node=node
        elif self.test:
            self.filename=self._filenameURL='test_{}_{}.wav'.format(
                                self.soundsettings.fs,
                                self.soundsettings.sample_format)
        else:
            t=_("No framed value, nor testing; can't continue...")
            log.error(t)
            ui.Label(self,text=t,borderwidth=1,font='default',
                    relief='raised').grid(row=0,column=0)
        # Just do these each once, since their dependencies don't change
        self.recorder=sound.SoundFileRecorder(self._filenameURL,self.pa,
                                        self.soundsettings)
        self.player=sound.SoundFilePlayer(self._filenameURL,self.pa,
                                            self.soundsettings)
        ui.Frame.__init__(self,parent, **kwargs)
        """These need to happen after the frame is created, as they
        might cause the init to stop."""
        if not self.test and not self.program['settings'].audiolang:
            tlang=_("Set audio language to get record buttons!")
            log.error(tlang)
            ui.Label(self,text=tlang,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        if None in [self.soundsettings.fs,
                    self.soundsettings.sample_format,
                    self.soundsettings.audio_card_in,
                    self.soundsettings.audio_card_out]:
            text=_("Set all sound card settings"
                    "\n(Do|Recording|Sound Card Settings)"
                    "\nand a record button will be here.")
            log.debug(text)
            ui.Label(self,text=text,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        self.makebuttons()
class SoundSettingsWindow(ui.Window):
    def setsoundformat(self,choice,window):
        self.soundsettings.sample_format=choice
        self.updatesoundformat()
        window.destroy()
    def updatesoundformat(self):
        self.labeltext['sample_format'].set(self.soundformatlabel())
    def soundformatlabel(self):
        self.soundsettings.check()
        cur=self.soundsettings.hypothetical['sample_formats'][
                                            self.soundsettings.sample_format]
        return _(f"{cur}")
    def setsoundcardindex(self,choice,window):
        # log.info("setsoundcardindex: {}".format(choice))
        self.soundsettings.audio_card_in=choice
        self.updatesoundcard()
        window.destroy()
    def updatesoundcard(self):
        self.labeltext['audio_card_in'].set(self.soundcardlabel())
    def soundcardlabel(self):
        self.soundsettings.check()
        cur=self.soundsettings.cards['dict'][self.soundsettings.audio_card_in]
        return _(f"Microphone: ‘{cur}’")
    def setsoundcardoutindex(self,choice,window):
        # log.info("setsoundcardoutindex: {}".format(choice))
        self.soundsettings.audio_card_out=choice
        self.updatesoundcardoutindex()
        window.destroy()
    def updatesoundcardoutindex(self):
        self.labeltext['audio_card_out'].set(self.soundcardoutindexlabel())
    def soundcardoutindexlabel(self):
        self.soundsettings.check()
        cur=self.soundsettings.cards['dict'][self.soundsettings.audio_card_out]
        return _(f"Speakers: ‘{cur}’")
    def setsoundhz(self,choice,window):
        self.soundsettings.fs=choice
        self.updatesoundhz()
        window.destroy()
    def updatesoundhz(self):
        self.labeltext['fs'].set(self.soundhzlabel())
    def soundhzlabel(self):
        self.soundsettings.check()
        cur=self.soundsettings.hypothetical['fss'][self.soundsettings.fs]
        return _(cur)
    def getsoundcardindex(self,event=None):
        log.info("Asking for input sound card...")
        window=ui.Window(self,
                    title=_('Select Input Sound Card'))
        ui.Label(window.frame, text=_('What sound card do you '
                                    'want to record sound with with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['in']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.setsoundcardindex,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundcardoutindex(self,event=None):
        log.info("Asking for output sound card...")
        window=ui.Window(self,
                title=_('Select Output Sound Card'))
        ui.Label(window.frame, text=_('What sound card do you '
                                    'want to play sound with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['out']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.setsoundcardoutindex,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundformat(self,event=None):
        log.info("Asking for audio format...")
        window=ui.Window(self,
                        title=_('Select Audio Format'))
        ui.Label(window.frame, text=_('What audio format do you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        l=list()
        ss=self.soundsettings
        for sf in ss.cards['in'][ss.audio_card_in][ss.fs]:
            name=ss.hypothetical['sample_formats'][sf]
            l+=[(sf, name)]
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.setsoundformat,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundhz(self,event=None):
        log.info("Asking for sampling frequency...")
        window=ui.Window(self,
                        title=_('Select Sampling Frequency'))
        ui.Label(window.frame, text=_('What sampling frequency you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        l=list()
        ss=self.soundsettings
        for fs in ss.cards['in'][ss.audio_card_in]:
            name=ss.hypothetical['fss'][fs]
            l+=[(fs, name)]
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.setsoundhz,
                                    window=window,
                                    column=0, row=1
                                    )
    def soundcheckrefresh(self,dict=None):
        self.soundsettings.makedefaultifnot()
        dictnow={
                'audio_card_in':self.soundsettings.audio_card_in,
                'fs':self.soundsettings.fs,
                'sample_format': self.soundsettings.sample_format,
                'audio_card_out': self.soundsettings.audio_card_out
                }
        """Call this just once. If nothing changed, wait; if changes, run,
        then run again."""
        if self.exitFlag.istrue() or self.exitFlag.istrue():
            self.on_quit()
            self.on_quit()
            return
        log.info("sound settings dict: {}".format(dict))
        self.resetframe()
        self.scroll=ui.ScrollingFrame(
                                                self.frame,
                                                row=0,column=0)
        self.content=self.scroll.content
        row=0
        ui.Label(self.content, font='title',
                text=_("Confirm Sound Card Settings"),
                row=row,column=0)
        row+=1
        ui.Label(self.content, #font='title',
                text=_("(click any to change)"),
                row=row,column=0)
        row+=1
        self.labeltext={}
        for varname, cmd in [
            ('audio_card_in', self.getsoundcardindex),
            ('fs', self.getsoundhz),
            ('sample_format', self.getsoundformat),
            ('audio_card_out', self.getsoundcardoutindex),
                                                    ]:
            text=_("Change")
            self.labeltext[varname]=ui.StringVar()
            l=ui.Label(self.content,text=self.labeltext[varname],
                        row=row,column=0)
            l.bind('<ButtonRelease-1>',cmd) #getattr(self,str(cmd)))
            row+=1
        self.updatesoundcard()
        self.updatesoundhz()
        self.updatesoundformat()
        self.updatesoundcardoutindex()
        br=RecordButtonFrame(self.content,self,test=True)
        br.grid(row=row,column=0)
        row+=1
        # l=_("You may need to change your microphone "
        #     "\nand/or speaker sound card to get the "
        #     "\nsampling and format you want.")
        # ui.Label(self.soundsettingswindow.content,
        #         text=l).grid(row=row,column=0)
        # row+=1
        l=_("Plug in your microphone, and make sure ‘record’ and ‘play’ work "
            "well here, before recording real data!")
        caveat=ui.Label(self.content,
                text=l,font='read',
                row=row,column=0)
        caveat.wrap()
        row+=1
        # l=_("See also note in documentation about verifying these "
        #     "recordings in an external application, such as Praat.")
        # caveat2=ui.Label(self.soundsettingswindow.content,
        #         text=l,font='instructions',
        #         row=row,column=0)
        # caveat2.wrap()
        # row+=1
        play=_("Play")
        l=_("If Praat is installed in your OS path, right click on ‘{}’ above "
            "to open in Praat.".format(play))
        caveat3=ui.Label(self.content,
                text=l,font='default',
                row=row,column=0)
        caveat3.wrap()
        row+=1
        bd=ui.Button(self.content,
                    text=_("Done"),
                    cmd=self.soundcheckrefreshdone,
                    # anchor='c',
                    row=row,column=0,
                    sticky=''
                    )
        bd=ui.Button(self.content,
                    text=_("Quit Task"),
                    # cmd=program['root'].on_quit,
                    cmd=self.task.quittask,
                    # anchor='c',
                    row=row,column=1
                    )
    def soundcheckrefreshdone(self):
        self.task.storesoundsettings()
        self.destroy()
    def __init__(self,program,task,**kwargs):
        self.refreshdelay=1000 # wait 1s for a refresh check, always mainwindow
        ui.Window.__init__(self, program['root'], exit=False,
                            title=_('Select Sound Card Settings'))
        self.task=task
        self.soundsettings=self.program['soundsettings']
        self.soundcheckrefresh()
class Task():
    def quittask(self):
        print("Not actually quitting task")
    def storesoundsettings(self):
        print("Not actually storing settings")
    def __init__(self):
        self.pyaudio=sound.AudioInterface()
        #any sound task should find settings at self.soundsettings:
        self.soundsettings=program['soundsettings'] #Each task with sound should have this
        self.pyaudio=program['soundsettings'].pyaudio
        self.audiolang=True
if __name__ == "__main__":
    try:
        _
    except:
        def _(x):
            return x
    r=ui.Root()
    r.program['praat']='/home/kentr/bin/praat'
    r.program['hostname']='karlap'
    r.program['name']='A−Z+T'
    r.program['analang']='tbt-CD'
    import langtags
    r.program['languages']=langtags.Languages()
    #This will normally pass self.pyaudio from task to SoundSettings, to keep
    # one pyaudio instance, but if not, settings will create one.
    language=r.program['languages'].get_obj(r.program['analang'])
    r.program['soundsettings']=sound.SoundSettings(analang_obj=language)
    log.info(f"asr_kwargs: {r.program['soundsettings'].asr_kwargs}")
    r.title('Test Sound UI')
    task=Task(program=r.program)
    if r.program['hostname'] == 'karlap':
        r.program['soundsettings'].asr_kwargs['cache_dir']='/media/kentr/hfcache'
    ssw=SoundSettingsWindow(task,withdrawn=True)
    ssw.setsoundcard_byname('default')
    ssw.destroy() #since not waiting
    log.info(f"asr_kwargs: {r.program['soundsettings'].asr_kwargs}")
    # ssw.wait_window(ssw) #only if need to change stuff
    ssw=ASRModelSelectionWindow(task)
    log.info(f"asr_kwargs: {r.program['soundsettings'].asr_kwargs}")
    ui.Label(r,text="Record sound to test Automatic Speech Recognition engines",row=0,column=0)
    RecordnTranscribeButtonFrame(r,task,test=True,
        show_transcriptions=True, #this typically in Entry
        show_tone=True,
        shown='all',
        row=2,column=0)
    r.deiconify()
    r.mainloop()
