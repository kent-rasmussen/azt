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
class RecordnTranscribeButtonFrame(RecordButtonFrame):
    def _stop(self, event):
        RecordButtonFrame._stop(self)
        if self.soundsettings.asrOK and self.recorder.file_write_OK:
            self.task.wait("Getting transcriptions...")
            self.recorder.get_transcriptions()
            self.task.waitdone()
        else:
            log.info("Not transcribing because asr is not OK!")
        if hasattr(self.recorder,'transcriptions'):
            self.maketranscriptionlabel()
    def _redo(self, event):
        self.remove_transcriptions()
        RecordButtonFrame._redo(self)
    def makebuttons(self):
        RecordButtonFrame.makebuttons(self)
        if (file.exists(self._filenameURL) and
                hasattr(self.recorder, 'transcriptions') and
                not self.shown == 'none'):
            self.maketranscriptionlabel()
    def maketranscriptionlabel(self):
        try:
            self.transcription_var.set(self.recorder.transcriptions)
            self.transcription_ipa_var.set(self.recorder.transcriptions_ipa)
            self.transcription_tone_var.set(self.recorder.tone_melody)
        except Exception as e:
            pass
            # log.info(f"No transcription variables set ({e})")
        self.transcriptionframe=ui.ScrollingFrame(self,row=0,col=3)
        scrolling_content=self.transcriptionframe.content
        c=0
        repos=sorted(set(self.recorder.transcriptions)|set(
                        self.recorder.transcriptions_ipa)) #all keys, keep order
        for trans in ['transcriptions','transcriptions_ipa']:
            # log.info(f"maybe showing {trans}")
            if (hasattr(self,f'show_{trans}') and
                getattr(self,f'show_{trans}') and
                hasattr(self.recorder,trans) and
                getattr(self.recorder,trans)):
                # log.info(f"showing {trans}")
                # log.info(f"showing {trans} now ({toshow[:20]})")
                setattr(self,trans,{})
                r=0
                for i in repos:
                    text=getattr(self.recorder,trans).get(i,'')
                    if text and len(repos) > self.show_repo_name_if_more_than:
                        text=i+': '+text
                    try:
                        assert text
                        getattr(self,trans)[i]=ui.Label(scrolling_content,
                                                    text=text,
                                                    ipadx=20,
                                                    row=r,
                                                    column=c
                                                    )
                    except Exception as e:
                        log.info(f"Probably nothing: {e}")
                    if self.shown == 'first':
                        continue
                    r+=1
                c+=1
        if (hasattr(self,'show_tone') and self.show_tone
                and hasattr(self.recorder,'tone_melody')
            and self.recorder.tone_melody):
            self.tone_melody=ui.Label(scrolling_content,
                                    text=self.recorder.tone_melody,
                                    ipadx=20, #ipady=15,
                                    row=self.grid_size()[1],
                                    column=0, colspan=2
                                    )
        # log.info(f"scrolling_content size: {scrolling_content.grid_size()}")
        if not sum(scrolling_content.grid_size()):
            self.transcriptionframe.destroy()
    def remove_transcriptions(self):
        try:
            self.transcriptionframe.content.destroy()
            self.transcriptionframe.destroy()
            del self.recorder.transcriptions
            del self.recorder.transcriptions_ipa
            self.tone_melody.destroy()
            del self.recorder.tone_melody
        except Exception as e:
            log.info(f"transcription destruction failed ({e})")
            pass
    def configure_this(self):
        ASRModelSelectionWindow(self.program)
    def __init__(self,parent,task,node=None,**kwargs):
        must_haves=['transcription_var','show_transcriptions',
            'transcription_ipa_var','show_transcriptions_ipa',
            'transcription_tone_var','show_tone','shown']
        for f in must_haves:
            setattr(self,f,kwargs.pop(f,False))
        for f in [i for i in must_haves if '_var' in i]:
            if not getattr(self,f):
                setattr(self,f,ui.StringVar())
                log.info(f"Set untracked StringVar for {f}; it won't be "
                    f"available outside this {self.__class__.__name__}")
        self.show_repo_name_if_more_than=1
        super(RecordnTranscribeButtonFrame,self).__init__(parent,task,node,**kwargs)
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
    def setsoundcard_byname(self,name):
        if name in self.soundsettings.cards['dict'].values():
            self.soundsettings.audio_card_in=[n for n,v
                                    in self.soundsettings.cards['dict'].items()
                                    if v == name][0]
        else:
            log.error(f"card {name} not available "
                        f" ({self.soundsettings.cards['dict'].keys()})")
        self.updatesoundcard()
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
                text=self.tasktitle(),
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
        l=_("Plug in your microphone, and make sure ‘record’ and ‘play’ work "
            "well here, before recording real data!")
        caveat=ui.Label(self.content,
                text=l,font='read',
                row=row,column=0)
        caveat.wrap()
        row+=1
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
    def soundcheckrefreshdone(self):
        self.task.storesoundsettings()
        self.on_quit()
    def tasktitle(self):
        return _('Sound Card Settings')
    def __init__(self,task,**kwargs):
        self.refreshdelay=1000 # wait 1s for a refresh check, always mainwindow
        self.program=task.program #needed to find praat
        log.info(f"Theme of task: {task.program['theme']}")
        ui.Window.__init__(self,
                            task, #this show be called from a task now
                            exit=False,
                            title=self.tasktitle(),
                            withdrawn=True
                        )
        self.task=task
        self.soundsettings=self.program['soundsettings']
        self.soundcheckrefresh()
        if not kwargs.get("withdrawn"):
            task.withdraw()
            self.deiconify()
class ASRModelSelectionWindow(ui.Window):
    def language_entry(self):
        self.language_frame=ui.Frame(self.languages_frame,
                                    row=0,column=0,
                                    sticky='new')
        self.sister_frame=ui.Frame(self.languages_frame,
                                    row=0,column=1,
                                    sticky='ew')
        ui.Label(self.language_frame,text=_("Language:"),ipadx=10,row=0,column=0)
        self.lang=ui.StringVar()
        ef=ui.EntryField(self.language_frame,textvariable=self.lang,
                        row=1, sticky='ew')
        self.langs_possible_var=ui.StringVar()
        ui.Label(self.language_frame,textvariable=self.langs_possible_var,
                font='small', ipadx=10, row=3)
        self.bind('<Return>', self.language_selection)
        self.bind('<Tab>', self.language_selection)
        self.bind('<Button-1>', self.language_selection)
        self.lang.trace_add('write', self.language_selection)
    def language_selection(self,*args):
        if hasattr(self,'lang_cur') and self.lang_cur == self.lang.get():
            return
        try:
            self.language_info.destroy()
        except:
            pass
        try:
            self.lang_cur=self.lang.get()
            log.info(f"Getting language info for input {self.lang_cur}")
            display=self.languages.get_obj(self.lang_cur).full_display()
            possibles=self.languages.get_codes(self.lang_cur)
            displays=[self.languages.get_obj(j).full_display()
                                                    for j in possibles]
            log.info(f"Looking for languages related to {display}")
        except Exception as e:
            log.error(f"Language display error: {e}")
            self.lang_display_var.set(f"Error: ‘{self.lang_cur}’ not found")
            self.sister_options=[_("Nothing")]
            self.update_n_sisters()
            self.sisters_listbox.delete(0, "end")
            return
        self.lang_display_var.set(display)
        self.langs_possible_var.set('\n'.join(displays))
        self.get_sister_options()
    def get_sister_options(self,*args):
        self.language=self.languages.get_obj(self.lang_cur)
        self.sister_options=[self.alllangs]
        self.sister_options.extend(
                self.language.supported_ancestor_objs_prioritized()
                                )
        self.update_n_sisters()
        self.sisters_listbox.delete(0, "end")
        for i in self.sister_options:
            self.sisters_listbox.insert("end", i if isinstance(i,str)
                                                else i.full_display())
        max_value_len=max([len(self.sisters_listbox.get(i)) for i in range(len(self.sisters_listbox.get(0,'end')))])
        self.sisters_listbox.configure(width=min(max_value_len,60))
        self.save_sister() #since it is showing, anyway.
    def save_sister(self,event=None):
        log.info("Saving sister language now")
        if (0 in self.sisters_listbox.curselection() and
                len(self.sisters_listbox.curselection())>1):
            #Force user to pick all(0) or some, not both
            if 0 in self.last_selection_indexes:
                self.sisters_listbox.select_clear(0)
            else:
                self.sisters_listbox.select_clear(1,'end')
        displays=[self.sisters_listbox.get(i) for i #indexed displays
                     in self.sisters_listbox.curselection()]
        lobjs=[self.sister_options[i] for i #indexed objs
                     in self.sisters_listbox.curselection() if i != 0]
        codes=[i.iso() for i in lobjs]
        displays_from_codes=[i.full_display() for i in lobjs]
        print(displays,[i.full_display() for i in self.sister_options
                                            if i != self.alllangs])
        if codes:
            log.info(f"Selected {codes}, {displays}")
        else:
            codes=[i.iso() for i in self.sister_options if i != self.alllangs]
            log.info(f"No language selected; using all: {codes}")
        self.kwarg_vars['sister_languages'].set(codes)
        self.save_kwarg_to_soundsettings('sister_languages',codes)
        self.last_selection_indexes=self.sisters_listbox.curselection()
    def update_n_sisters(self):
        n=len(self.sister_options)-1
        if n:
            self.n_sisters['text']=f"Related Languages with ASR support ({n}):"
            self.sister_frame.grid()
        else:
            self.sister_frame.grid_remove()
    def sister_selection(self):
        self.n_sisters=ui.Label(self.sister_frame,text='',
                                    ipadx=10,row=0,column=0)
        self.sisters_listbox=ui.ListBox(self.sister_frame,
                command=self.save_sister,
                font='default',
                selectmode='multiple',
                optionlist=[], #If analang later, populate then
                row=1,column=0,
                sticky='ew'
                )
    def make_kwargVars(self):
        log.info(f"making kwargVars for {self.soundsettings.asr_kwargs}")
        for k in self.soundsettings.asr_kwargs:
            # log.info(f"Looking at {k}")
            if k not in self.kwarg_vars: #if it is there, leave it alone!
                if isinstance(self.soundsettings.asr_kwargs[k],bool):
                    self.kwarg_vars[k]=ui.BooleanVar()
                elif isinstance(self.soundsettings.asr_kwargs[k],str):
                    self.kwarg_vars[k]=ui.StringVar()
                else:
                    self.kwarg_vars[k]=ui.Variable()
                self.kwarg_vars[k].set(self.soundsettings.asr_kwargs[k])
    def get_vars(self):
        self.kwarg_vars={}
        self.make_kwargVars()
        self.lang_display_var=ui.StringVar()
        self.asr_settings_w={}
    def save_kwargs_to_soundsettings(self):
        for k,v in self.kwarg_vars.items():
            self.save_kwarg_to_soundsettings(k,v)
    def save_kwarg_to_soundsettings(self,k,v):
        if isinstance(v,ui.Variable):
            value=v.get()
        else:
            value=v
        # log.info(f"Starting Value: {value} ({type(value)})")
        try:
            assert self.soundsettings.asr_kwargs[k] == value
        except (AssertionError,KeyError):
            log.info(f"Changing {k} from "
                    f"{self.soundsettings.asr_kwargs.get(k,None)} "
                    f"to {value}")
            self.soundsettings.asr_kwargs[k]=value
        # This runs once before the ASR boots, when the above will suffice.
        if k in ['sister_languages'] and hasattr(self.soundsettings,'asr'):
            setattr(self.soundsettings.asr,k,value)
    def report_settings_strings(self):
        for k,v in self.kwarg_vars.items():
            if k in ['sister_languages']:
                row=self.strings_frame.grid_size()[1],
                ui.Label(self.strings_frame, text=f"{k}:", row=row, column=0)
                self.asr_settings_w[k]=ui.Label(self.strings_frame,
                                                textvariable=v,
                                                wraplength='50%',
                                                anchor='w',
                                                ipadx=10,
                                                row=row,
                                                borderwidth=1,
                                                column=1
                                                )
    def report_settings_bool(self,columns):
        self.boolean_frame_process=ui.Frame(self.boolean_frame,sticky='ew',
                                                                pady=10,r=0,c=0)
        self.boolean_frame_models=ui.Frame(self.boolean_frame,sticky='ew',
                                                                pady=10,r=1,c=0)
        self.boolean_frame_repos=ui.Frame(self.boolean_frame,sticky='ew',
                                                                rowspan=2,
                                                                pady=20,
                                                                padx=20,
                                                                r=0,c=1)
        m_buttons=p_buttons=-1
        for k,v in [(k,v) for k,v in self.kwarg_vars.items()
                        if isinstance(v,ui.BooleanVar)]:
            text=k
            if k in self.soundsettings.asr.repo_modelnames:
                if k in ["return_ipa"]:
                    continue
                parent=self.boolean_frame_models
                m_buttons+=1
                buttons=m_buttons
                if (self.soundsettings.asr.repo_modelnames[k]
                                    in self.soundsettings.asr_repos):
                    count=self.soundsettings.asr_repos[
                                    self.soundsettings.asr.repo_modelnames[k]]
                    text=f"k ({count})"
            else:
                parent=self.boolean_frame_process
                p_buttons+=1
                buttons=p_buttons
            self.asr_settings_w[k]=ui.CheckButton(parent,
                                        text = k,
                                        # no_default_indicator_images=True,
                                        variable = self.kwarg_vars[k],
                                        onvalue = True, offvalue = False,
                                        ipadx=10,
                                        sticky='ew',
                                        font='default',
                                        row=buttons//columns,
                                        column=buttons%columns
                                        )
        for frame in self.boolean_frame.winfo_children():
            for c in range(columns):
                frame.grid_columnconfigure(c, weight=1, uniform="uniwide")
        repos=sorted(self.soundsettings.asr_repos.items(),key=lambda x:-x[1])
        kwargs={'font':'small','sticky':'ew'}
        for n,(k,v) in enumerate(repos):
            ui.Label(self.boolean_frame_repos,text=k,r=n,**kwargs)
            ui.Label(self.boolean_frame_repos,text=v,r=n,c=1,**kwargs)
    def report_settings(self):
        self.settings_title=ui.Label(self.reload_frame,
                                    textvariable=self.lang_display_var,
                                    row=0,
                                    column=0,
                                    ipadx=10,
                                    anchor='w',
                                    sticky='we'
                                )
        self.report_settings_strings()
        self.report_settings_bool(columns=3)
        self.reload=ui.Button(self.reload_frame, text=_("Reload Model"),
                            command=self.reload_model,
                            row=0,column=1,
                            anchor='e',sticky='ew')
    def settings_grid(self):
        self.title=ui.Label(self,text=self.page_title,font='title',
                                                    row=0,column=1)
        self.option_frame=ui.Frame(self,row=1,column=1)
        self.reload_frame=ui.Frame(self.option_frame,row=0,column=0,sticky='ew')
        self.languages_frame=ui.Frame(self.option_frame,
                                    row=1,column=0,
                                    sticky='ew')
        self.strings_frame=ui.Frame(self.option_frame,
                                    row=2,column=0,
                                    colspan=2,
                                    ipady=20,
                                    sticky='ew')
        self.boolean_frame=ui.Frame(self.option_frame,
                                    row=3,column=0,
                                    columnspan=2,
                                    ipady=10,
                                    sticky='ew')
        self.language_entry()
        self.sister_selection()
        self.report_settings()
    def changed_kwargs(self):
        return self.soundsettings.changed_kwargs()
    def reload_model(self):
        self.save_kwargs_to_soundsettings()
        #Decide if we reload entirely, or just change adaptors
        r=self.soundsettings.get_changed_kwargs()
        if not r:
            changed_kwargs=self.soundsettings.changed_kwargs
            if not changed_kwargs['all']: #.asr exists; no changes since loaded
                log.info(f"Didn't find any changed kwargs ({changed_kwargs})")
                log.info(f"kwargs is ({self.soundsettings.asr_kwargs})")
                return
        # changed_kwargs doesn't exist if r...
        # Only count models that will be loaded (not offloaded):
        if r or [i for i in changed_kwargs['repos'].values() if i]:
            self.wait(_("Reloading ASR model(s)")+'\n'+_(
                        "(This may require a large download)"),
                        thenshow=True)
        elif changed_kwargs: #any other values
            log.info("Changing settings (or dropping ASR models; not loading)")
            log.info(f"changed_kwargs: {changed_kwargs['all']} "
                        f"({bool(changed_kwargs['all'])})")
        log.info(f"asr_kwargs: {self.soundsettings.asr_kwargs}")
        self.soundsettings.load_ASR()
        self.waitdone()
    def modify(self):
        self.soundsettings.asr_kwargs['sister_languages']=['zmg']
        self.soundsettings.asr_kwargs['simplify_length']=False
    def __init__(self,task,**kwargs):
        window_title=_('Select ASR Settings')
        self.page_title=_('Settings for Transcription Model')
        log.info(f"Theme of task: {task.theme}")
        ui.Window.__init__(self,
                            task,
                            exit=False,
                            title=window_title,
                            withdrawn=True
                            )
        self.program=task.program #needed to find praat
        self.soundsettings=self.program['soundsettings']
        if 'cache_dir' in self.soundsettings.asr_kwargs and not file.exists(self.soundsettings.asr_kwargs['cache_dir']):
            log.error(f"Cache dir {self.soundsettings.asr_kwargs['cache_dir']} "
                    "not found; exiting.")
            exit()
        self.languages=self.program.get('languages')
        try:
            self.analang=self.program.get('params').analang()
        except:
            self.analang=self.program.get('analang') #for testing
        self.alllangs=_("All of the below")
        self.get_vars()
        self.reload_model()
        self.make_kwargVars() #after ASR loaded, with full defaults
        self.settings_grid()
        if self.analang:
            self.lang.set(self.analang)
            self.get_sister_options() #Not on every change, but on boot
        self.save_kwargs_to_soundsettings()
        if not kwargs.get("withdrawn"):
            task.withdraw()
            self.deiconify()
class Task(ui.Window):
    def wait(self,x):
        print(x)
    def waitdone(self):
        pass
    def quittask(self):
        print("Not actually quitting task")
    def storesoundsettings(self):
        print("Not actually storing settings")
    def __init__(self,program):
        self.program=program
        self.theme=program['theme']
        window_title=_('Test Task (Does nothing)')
        ui.Window.__init__(self,
                            program['root'],
                            # program['root'],
                            exit=False,
                            title=window_title,
                            withdrawn=True
                            # state='withdrawn'
                            )
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
