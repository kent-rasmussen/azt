#!/usr/bin/env python3
# coding=UTF-8
import sound
import ui_tkinter as ui
import rx
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file

class Transcriber(ui.Frame):
    def addchar(self,x):
        if x in ['','∅'] or self.formfield.get() == '∅':
            self.formfield.delete(0,ui.END)
        if x:
            self.formfield.insert(ui.INSERT,x) #could also do tkinter.END
        if x == '': #if cleared, be ready to type
            self.formfield.focus_set()
        self.updatelabels()
    def updatelabels(self,event=None):
        a=self.newname.get()
        if set(['˥','˦','˧','˨','˩']) & set(a):
            x=self.hash_t.sub('T',self.newname.get())
            y=self.hash_sp.sub('#',x)
            z=self.hash_nbsp.sub('.',y)
            self.namehash.set(z)
        else:
            self.namehash.set('')
        self.labelcompiled=False
    def playbeeps(self,pitches):
        if not self.labelcompiled:
            self.beeps.compile(pitches)
        self.beeps.play()
    def configurebeeps(self,event=None):
        def higher():
            self.beeps.higher()
            self.labelcompiled=False
        def lower():
            self.beeps.lower()
            self.labelcompiled=False
        def wider():
            self.beeps.wider()
            self.labelcompiled=False
        def narrower():
            self.beeps.narrower()
            self.labelcompiled=False
        def shorter():
            self.beeps.shorter()
            self.labelcompiled=False
        def longer():
            self.beeps.longer()
            self.labelcompiled=False
        p=self.parent
        while not (isinstance(p,ui.Window) or isinstance(p,ui.Root)): # windows need window parents
            p=p.parent
        w=ui.Window(p, title=_("Configure Tone Beeps"))
        w.attributes("-topmost", True)
        ui.Button(w.frame,text=_("pitch up"),cmd=higher,
                        row=0,column=0)
        ui.Button(w.frame,text=_("pitch down"),cmd=lower,
                        row=1,column=0)
        ui.Button(w.frame,text=_("more H-L difference"),cmd=wider,
                        row=0,column=1)
        ui.Button(w.frame,text=_("less H-L difference"),cmd=narrower,
                        row=1,column=1)
        ui.Button(w.frame,text=_("slower"),cmd=longer,
                        row=2,column=0)
        ui.Button(w.frame,text=_("faster"),cmd=shorter,
                        row=2,column=1)
    def __init__(self, parent, initval=None, soundsettings=None, **kwargs):
        self.newname=ui.StringVar(value=initval)
        self.namehash=ui.StringVar()
        self.hash_t,self.hash_sp,self.hash_nbsp=rx.tonerxs()
        self.pyaudio=sound.AudioInterface()
        if soundsettings:
            self.soundsettings=soundsettings
        else:
            self.soundsettings=sound.SoundSettings(self.pyaudio)
        self.beeps=sound.BeepGenerator(pyAudio=self.pyaudio,
                                            settings=self.soundsettings)
        if 'chars' in kwargs and kwargs['chars'] and type(kwargs['chars']) is list:
            chars=kwargs.pop('chars')
            if len(chars)> 50:
                root=False #don't make it square, but 4:3
            elif len(chars) >25:
                root=int(len(chars)**(1/2))+2 #make it square
            else:
                root=7 #at least this many columns
            if root and len(chars)%root:
                # log.info("{} indivisible by {}!".format(len(chars),root))
                nrows=len(chars)//root+1
                ncols=len(chars)//nrows+1
            elif root:
                # log.info("{} divisible by {}!".format(len(chars),root))
                ncols=root
                nrows=len(chars)//root
            else: #this isn't the right math, but close enough for now
                x=9
                y=3
                ncols=int((len(chars)*x/y)**(1/2))+1
                nrows=len(chars)//ncols
                log.info("chars: {}; ncols: {}; nrows: {}; x:y={}"
                        "".format(len(chars),ncols,nrows,ncols/nrows))
            chars+=['∅']
        else:
            chars=kwargs.pop('chars',None) #in case it is None/0/False, etc.
            tonechars=['[', '˥', '˦', '˧', '˨', '˩', ']']
            spaces=[' ',' ']
            chars=tonechars+spaces
            ncols=7
            nrows=1
        clear=['']
        ui.Frame.__init__(self, parent, **kwargs)
        buttonframe=ui.Frame(self, row=0, column=0, sticky='new')
        log.info("Transcriber using {} rows, {} columns".format(nrows,ncols))
        for char in chars+clear:
            if char == ' ':
                text=_('syllable break')
                column=0
                columnspan=int(ncols/2)+1
                row=1
            elif char == ' ':
                text=_('word break')
                columnspan=int(ncols/2)
                column=columnspan+1
                row=1
            elif char == '∅':
                text=_('no segments')
                columnspan=ncols
                column=0
                row=nrows+2
            elif char == '':
                text=_('clear entry')
                column=0
                columnspan=ncols
                row=nrows+1
            else:
                column=chars.index(char)%ncols
                text=char
                columnspan=1
                row=chars.index(char)//ncols
            # if char in chars:
            #     log.info("Making Button {} at row={}, column={}".format(chars.index(char),row, column))
            ui.Button(buttonframe,text = text,
                        command = lambda x=char:self.addchar(x),
                        anchor ='c',
                        row=row,
                        column=column,
                        sticky='nsew',
                        # norender=True,
                        columnspan=columnspan
                        )
        fieldframe=ui.Frame(self,
                            row=1,column=0,sticky='new'
                            )
        self.formfield = ui.EntryField(fieldframe,textvariable=self.newname,
                                    row=0,column=0,sticky='new',
                                    font='readbig')
        self.formfield.bind('<KeyRelease>', self.updatelabels) #apply function after key
        self.formfieldplay= ui.Button(fieldframe,text=_('‣'),
                            cmd=lambda:self.playbeeps(self.newname.get()),
                            font='tiny',
                            sticky='ns',
                            row=0, column=1)
        self.formfieldplay.bind('<Button-3>', self.configurebeeps)
        tt=_("Left click to play, \nRight click to configure")
        ui.ToolTip(self.formfieldplay, text=tt)
        self.formhashlabel=ui.Label(fieldframe,
                                textvariable=self.namehash,
                                anchor ='c',
                                row=1,column=0,sticky='new'
                                )
        # fieldframe.grid_columnconfigure(0, weight=1)
        self.updatelabels()
if __name__ == "__main__":
    try:
        _
    except:
        def _(x):
            return x
    r=ui.Root()
    r.title('Transcriber')
    Transcriber(r,initval='˥˥ ˩˩ ˧˧',column=1,row=1)
    r.deiconify()# soundsettings=sound.SoundSettings()
    r.mainloop()
