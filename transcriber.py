#!/usr/bin/env python3
# coding=UTF-8
try:
    import sound
except ModuleNotFoundError:
    raise
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
        w=ui.Window(self, title=_("Configure Tone Beeps"))
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
            if len(chars)%root:
                # log.info("{} indivisible by {}!".format(len(chars),root))
                nrows=len(chars)//root+1
                ncols=len(chars)//nrows+1
            else:
                # log.info("{} divisible by {}!".format(len(chars),root))
                ncols=root
                nrows=len(chars)//root
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
                        columnspan=columnspan
                        )
        fieldframe=ui.Frame(self,
                            row=1,column=0,sticky='new'
                            )
        self.formfield = ui.EntryField(fieldframe,textvariable=self.newname,
                                    row=0,column=0,sticky='new',
                                    font='readbig')
        self.formfield.bind('<KeyRelease>', self.updatelabels) #apply function after key
        self.formfieldplay= ui.Button(fieldframe,text=_('>'),
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
    w=ui.Root()
    w.title('Transcriber')
    # soundsettings=sound.SoundSettings()
    Transcriber(w,initval='˥˥ ˩˩ ˧˧',column=0,row=0,
    chars=[
    # c['pvd'][2]=[
    'bh','dh','gh','gb',
    'bb','dd','gg', #French
    'gw','dw', 'ɗw', #gnd
    'mb','nd','ŋg',
    #             ]
    # c['pvd'][3]=[
    'ndw', 'ŋgw', #gnd
                # ]
    # c['pvd'][1]=[
    'b','B','d','g','ɡ',
    # ] #,'G' messes with profiles
    # c['p']={}
    # c['p'][2]=[
    'kk','kp','cc','pp','pt','tt','ck',
                'kw','tw',
                # ] #gnd
    # c['p'][1]=[
    'p','P','ɓ','Ɓ','t','ɗ','ɖ','c','k','q',
    # ]
    # c['fvd']={}
    # c['fvd'][2]=[
    'bh','vh','zh',
    # ]
    # c['fvd'][1]=[
    'j','J','v','z','Z','ʒ','ð','ɣ',
    # ] #problems w x?
    # c['f']={}
    # c['f'][3]=[
    'sch',
    # ]
    # c['f'][2]=[
    'ch','ph','sh','hh','pf','bv','ff','sc','ss','th',
                'hw', #gnd
                # ]
    #Assuming x is voiceless, per IPA and most useage...
    # c['f'][1]=[
    'F','f','s','ʃ','θ','x','h',
    # ] #not 'S'
    # c['avd']={}
    # c['avd'][2]=[
    'dj','dz','dʒ',
    # ]
    # c['avd'][3]=[
    'ndz','dzw',
    # ] #gnd
    # c['avd'][4]=[
    'ndzw',
    # ] #gnd
    # c['a']={}
    # c['a'][3]=[
    'chk','tch',
    # ]
    # c['a'][2]=[
    'ts','tʃ',
    # ]
    # c['lfvd']={}
    # c['lfvd'][3]=[
    'zlw',
    # ]
    # c['lfvd'][2]=[
    'zl',
    # ]
    # c['lfvd'][1]=[
    'ɮ',
    # ]
    # c['lf']={}
    # c['lf'][3]=[
    'slw',
    # ]
    # c['lf'][2]=[
    'sl',
    # ]
    # c['lf'][1]=[
    'ɬ',
    # ]
    # c['pn']={}
    'ᵐb','ᵐp','ᵐv','ᵐf','ⁿd','ⁿt','ᵑg','ⁿg','ᵑg','ⁿk','ᵑk',
    'ⁿj','ⁿs','ⁿz',
                # ]
    # x={} #dict to put all hypothetical segements in, by category
    # x['G']=['ẅ','y','Y','w','W']
    # x['N']=['m','M','n','ŋ','ɲ','ɱ'] #'N', messed with profiles
    # x['Ndg']=['mm','ŋŋ','ny','gn','nn']
    # x['Ntg']=["ng'"]
    # """Non-Nasal/Glide Sonorants"""
    # x['S']=['l','r']
    # x['Sdg']=['rh','wh','ll','rr',
    #             'rw','lw' #gnd
    #             ]

    ]
    )#,soundsettings=soundsettings)
    w.mainloop()
