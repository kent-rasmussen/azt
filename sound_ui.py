#!/usr/bin/env python3
# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import ui_tkinter as ui
import sound
import file
from utilities import *
import executables
class RecordButtonFrame(ui.Frame):
    """This is not implemented yet!!"""
    def _start(self, event):
        log.log(3,"Asking PA to record now")
        self.recorder.start()
    def _stop(self, event):
        try:
            self.recorder.stop()
        except Exception as e:
            log.info("Couldn't stop recorder; was it on? ({})".format(e))
        """This is done in advance of recording now:"""
        self.b.destroy()
        self.makeplaybutton()
        self.makedeletebutton()
        self.addlink()
    def _redo(self, event):
        log.log(3,"I'm deleting the recording now")
        self.p.destroy()
        self.makerecordbutton()
        self.r.destroy()
    def makebuttons(self):
        if file.exists(self._filenameURL):
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
        tryrun(self.player.play)
    def makeplaybutton(self):
        self.p=ui.Button(self, text='‣', command=self._play,
                        font='readbig',
                        ipadx=20, ipady=0
                        )
        #Not using these for now
        # self.p.bind('<ButtonPress>', self._play)
        # self.p.bind('<ButtonRelease>', self.function)
        self.p.grid(row=0, column=1,sticky='w')
        pttext=_("Click to hear")
        if 'praat' in self.soundsettings.program:
            pttext+='; '+_("right click to open in praat")
            self.p.bind('<Button-3>',
                        lambda x: executables.praatopen(
                                                    self.soundsettings.program,
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
        self.soundsettings.program['db'].addmediafields(self.node,self.filename,
                                self.soundsettings.program['params'].audiolang,
                                # ftype=ftype,
                                write=False)
        self.task.maybewrite()
        self.soundsettings.program['status'].last('recording',update=True)
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
        if not hasattr(task,'soundsettings'):
            if not hasattr(self.soundsettings.program['settings'],
                            'soundsettings'):
                task.loadsoundsettings()
            self.soundsettings=self.soundsettings.program['settings'].soundsettings
        else:
            self.soundsettings=task.soundsettings
        self.callbackrecording=True
        self.chunk = 1024  # Record in chunks of 1024 samples (for block only)
        self.channels = 1 #Always record in mono
        self.test=kwargs.pop('test',None)
        if node:# and framed.framed != 'NA':
            task.makeaudiofilename(node) #should fill out the following
            self.filename=node.textvaluebylang(
                            self.soundsettings.program['params'].audiolang)
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
        if not self.test and not self.soundsettings.program['settings'].audiolang:
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
        window.destroy()
    def setsoundcardindex(self,choice,window):
        # log.info("setsoundcardindex: {}".format(choice))
        self.soundsettings.audio_card_in=choice
        window.destroy()
    def setsoundcardoutindex(self,choice,window):
        # log.info("setsoundcardoutindex: {}".format(choice))
        self.soundsettings.audio_card_out=choice
        window.destroy()
    def setsoundhz(self,choice,window):
        self.soundsettings.fs=choice
        window.destroy()
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
        if dict == dictnow:
            self.parent.after(self.refreshdelay,
                                self.soundcheckrefresh,
                                dictnow)
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
        ss=self.soundsettings
        ss.check() #make defaults if not valid options
        for varname, dict, cmd in [
            ('audio_card_in', ss.cards['dict'], self.getsoundcardindex),
            ('fs',ss.hypothetical['fss'], self.getsoundhz),
            ('sample_format', ss.hypothetical['sample_formats'],
                                                         self.getsoundformat),
            ('audio_card_out', ss.cards['dict'], self.getsoundcardoutindex),
                                                    ]:
            text=_("Change")
            var=getattr(ss,varname)
            log.debug("{} in {}".format(var,dict))
            l=dict[var]
            if cmd == self.getsoundcardindex:
                l=_("Microphone: ‘{}’").format(l)
            if cmd == self.getsoundcardoutindex:
                l=_("Speakers: ‘{}’").format(l)
            l=ui.Label(self.content,text=l,
                    row=row,column=0)
            l.bind('<ButtonRelease-1>',cmd) #getattr(self,str(cmd)))
            row+=1
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
        self.soundcheckrefresh(dictnow)
    def soundcheckrefreshdone(self):
        self.task.storesoundsettings()
        self.destroy()
    def __init__(self,program,task,**kwargs):
        self.refreshdelay=1000 # wait 1s for a refresh check, always mainwindow
        ui.Window.__init__(self, parent, exit=False,
        ui.Window.__init__(self, program['root'], exit=False,
                            title=_('Select Sound Card Settings'))
        self.task=task
        self.soundsettings=task.soundsettings
        self.soundsettings.program=program
        self.soundcheckrefresh()
class Task():
    def quittask(self):
        print("Not actually quitting task")
    def storesoundsettings(self):
        print("Not actually storing settings")
    def __init__(self):
        self.pyaudio=sound.AudioInterface()
        #any sound task should find settings at self.soundsettings:
        self.soundsettings=sound.SoundSettings(self.pyaudio)
        self.audiolang=True
if __name__ == "__main__":
    try:
        _
    except:
        def _(x):
            return x
    r=ui.Root()
    r.program['praat']='/home/kentr/bin/praat'
    program=r.program
    r.title('Sound UI')
    # program['settings']
    task=Task()
    ssw=SoundSettingsWindow(r.program,task)
    ssw.wait_window(ssw)
    ui.Label(r,text="test Frame",row=0,column=0)
    RecordButtonFrame(r,task,test=True,row=1,column=0)
    r.deiconify()# soundsettings=sound.SoundSettings()
    r.mainloop()
