#!/usr/bin/env python3
# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import ui_tkinter as ui
import sound
import file
from utilities import *

class RecordButtonFrame(ui.Frame):
    def _start(self, event):
        log.log(3,"Asking PA to record now")
        self.recorder=sound.SoundFileRecorder(self._filenameURL,self.pa,
                                            self.soundsettings)
        log.debug("PA recorder made OK")
        self.recorder.start()
    def _stop(self, event):
        try:
            self.recorder.stop()
        except:
            log.info("Couldn't stop recorder; was it on?")
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
        self.player=sound.SoundFilePlayer(self._filenameURL,self.pa,
                                            self.soundsettings)
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
        if 'praat' in program:
            pttext+='; '+_("right click to open in praat")
            self.p.bind('<Button-3>',lambda x: praatopen(self._filenameURL))
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
        program['db'].addmediafields(self.node,self.filename,
                                program['params'].audiolang,
                                # ftype=ftype,
                                write=False)
        self.task.maybewrite()
        program['status'].last('recording',update=True)
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
            if not hasattr(program['settings'],'soundsettings'):
                task.loadsoundsettings()
            self.soundsettings=program['settings'].soundsettings
        else:
            self.soundsettings=task.soundsettings
        self.callbackrecording=True
        self.chunk = 1024  # Record in chunks of 1024 samples (for block only)
        self.channels = 1 #Always record in mono
        self.test=kwargs.pop('test',None)
        if node:# and framed.framed != 'NA':
            task.makeaudiofilename(node) #should fill out the following
            self.filename=node.textvaluebylang(program['params'].audiolang)
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
        ui.Frame.__init__(self,parent, **kwargs)
        """These need to happen after the frame is created, as they
        might cause the init to stop."""
        if not self.test and not program['settings'].audiolang:
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
class Task():
    def __init__(self):
        self.pyaudio=sound.AudioInterface()
        self.soundsettings=sound.SoundSettings(self.pyaudio)
        self.audiolang=True
if __name__ == "__main__":
    try:
        _
    except:
        def _(x):
            return x
    r=ui.Root()
    program=r.program
    r.title('Sound UI')
    # program['settings']
    task=Task()
    ui.Label(r,text="test Frame",row=0,column=0)
    RecordButtonFrame(r,task,test=True,row=1,column=0)
    r.deiconify()# soundsettings=sound.SoundSettings()
    r.mainloop()
