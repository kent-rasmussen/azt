#!/usr/bin/env python3
# coding=UTF-8
import sys
import platform
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
# logsetup.setlevel('DEBUG',log) #for this file
log.info("Importing ui_tkinter.py")
import unicodedata
import tkinter #as gui
import tkinter.font
import tkinter.scrolledtext
import tkinter.ttk
import file #for image pathnames
from random import randint #for theme selection
import datetime
try: #translation
    _
except:
    def _(x):
        return x
try: #PIL
    import PIL.ImageFont
    import PIL.ImageTk
    import PIL.ImageDraw
    import PIL.Image
    pilisactive=True
    log.info("PIL loaded OK")
except Exception as e:
    log.error("Error loading PIL: {}".format(e))
    pilisactive=False
# import tkintermod
# tkinter.CallWrapper = tkintermod.TkErrorCatcher
"""Variables for use without tkinter"""
END=tkinter.END
INSERT=tkinter.INSERT
N=tkinter.N
S=tkinter.S
E=tkinter.E
W=tkinter.W
RIGHT=tkinter.RIGHT
LEFT=tkinter.LEFT
"""These classes have no dependencies"""
class ObectwArgs(object):
    """ObectwArgs just allows us to throw away unused args and kwargs."""

    def __init__(self, *args, **kwargs):
        log.info("ObectwArgs args: {};{}".format(args,kwargs))
        super(ObectwArgs, self).__init__()
class NoParent(object):
    """docstring for NoParent."""
    def __init__(self, *args, **kwargs):
        if args:
            args=list(args)
            args.remove(args[0])
        super(NoParent, self).__init__(*args, **kwargs)
class Theme(object):
    """docstring for Theme."""
    def startruntime(self):
        self.start_time=datetime.datetime.utcnow()
        log.info("starting at {}".format(self.start_time))
    def nowruntime(self):
        #this returns a delta!
        return datetime.datetime.utcnow()-self.start_time
    def logfinished(self,msg=None):
        log.info("logging finish now")
        run_time=self.nowruntime()
        # if type(start) is datetime.datetime: #only work with deltas
        #     start-=self.start_time
        if msg:
            msg=str(msg)+' '
        else:
            msg=''
        text=_("Finished {}at {} ({:1.0f}m, {:2.3f}s)"
                "").format(msg,now(),*divmod((run_time).total_seconds(),60))
        log.info(text)
        return text
    def setimages(self):
        # Program icon(s) (First should be transparent!)
        scale=self.program['scale'] #just reading this here
        self.scalings=[]
        self.photo={}
        #do these once:
        if scale-1: #x != y: #should be the same as scale != 1
            log.info("Maybe scaling images; please wait...")
            scaledalreadydir='images/scaled/'+str(scale)+'/'
            file.makedir(file.fullpathname(scaledalreadydir)) #in case not there
        def mkimg(name,filename):
            relurl=file.getdiredurl('images/',filename)
            # log.info("scale: {}".format(scale))
            if scale-1: #x != y:
                scaledalready=file.getdiredurl(scaledalreadydir,filename)
                # log.info("Looking for {}".format(scaledalready))
                if file.exists(file.fullpathname(scaledalready)):
                    # log.info("scaled image exists for {}".format(filename))
                    relurl=scaledalready
                # log.info("Dirs: {}?={}".format(scaledalready,relurl))
                if scaledalready != relurl: # should scale if off by >2% either way
                    # log.info("Scaling {}".format(relurl)) #Just do this once!
                    try:
                        assert self.fakeroot.winfo_exists()
                    except:
                        program=self.program.copy()
                        program['theme']=None
                        self.fakeroot=Root(program,
                                            noimagescaling=True)
                        self.fakeroot.ww=Wait(parent=self.fakeroot,
                                        msg="Scaling Images (Just this once)")
                    if not self.scalings:
                        maxscaled=100
                    else:
                        maxscaled=int(sum(self.scalings)/len(self.scalings)+10)
                    for y in range(maxscaled,10,-5):
                        # Higher number is better resolution (x*y/y), more time to process
                        #10>50 High OK, since we do this just once now
                        #lower option if higher fails due to memory limitations
                        # y=int(y)
                        x=int(scale*y)
                        # log.info("Scaling {} @{} resolution".format(relurl,y)) #Just do this once!
                        try:
                            img = Image(file.fullpathname(relurl))
                            # keep these at full size, for now
                            if 'openclipart.org' not in filename:
                                img.scale(scale,pixels=img.maxhw(),resolution=y)
                                self.photo[name]=img.scaled
                            else:
                                self.photo[name]=img
                            # log.info("scaledalready.parent: {}".format(scaledalready.parent))
                            # log.info("parent: {}".format(scaledalreadydir != scaledalready.parent))
                            if scaledalready.parent != scaledalreadydir:
                                file.makedir(scaledalready.parent,silent=True)
                            self.photo[name].write(
                                                file.fullpathname(scaledalready)
                                                    )
                            self.scalings.append(y)
                            if file.exists(scaledalready):
                                log.info("Scaled {} {} @{} resolution: {}"
                                        "".format(name,relurl,y,_("OK")))
                            # else:
                            #     log.info("Problem Scaling {} {} @{} resolution"
                            #             "".format(name,relurl,y,_("OK"))
                            return #stop when the first/best works
                        except tkinter.TclError as e:
                            # log.info(e)
                            if ('not enough free memory '
                                'for image buffer' in str(e)):
                                continue
            # log.info("Using {}".format(relurl))
            self.photo[name] = Image(file.fullpathname(relurl))
            # log.info("Compiled {} {}".format(name,relurl))
        imagelist=[ ('transparent','AZT stacks6.png'),
                            ('tall','AZT clear stacks tall.png'),
                            ('small','AZT stacks6_sm.png'),
                            ('icon','AZT stacks6_icon.png'),
                            ('icontall','AZT clear stacks tall_icon.png'),
                            ('iconT','T alone clear6_icon.png'),
                            ('iconC','Z alone clear6_icon.png'),
                            ('iconV','A alone clear6_icon.png'),
                            ('iconCV','ZA alone clear6_icon.png'),
                            ('iconWord','ZAZA clear stacks6_icon.png'),
                            ('iconWordRec','ZAZA Rclear stacks6_icon.png'),
                            ('iconTRec','T Rclear stacks6_icon.png'),
                            ('iconReport','Report_icon.png'),
                            ('iconReportLogo','Generic AZT Reports_icon.png'),
                            ('iconTRep','T Report_icon.png'),
                            ('iconCVRep','ZA Report_icon.png'),
                            ('iconTranscribe','Transcribe Tone_icon.png'),
                            ('iconTranscribeC','Consonant Choice_icon.png'),
                            ('iconTranscribeV','Vowel Choice_icon.png'),
                            ('iconJoinUF','Join Tone_icon.png'),
                            ('iconTRepcomp','T Report Comprehensive_icon.png'),
                            ('iconVRepcomp','A Report Comprehensive_icon.png'),
                            ('iconCRepcomp','Z Report Comprehensive_icon.png'),
                            ('iconCVRepcomp','ZA Report Comprehensive_icon.png'),
                            ('iconVCCVRepcomp','AZZA Report Comprehensive_icon.png'),
                            ('USBdrive','USB drive.png'),
                            ('T','T alone clear6.png'),
                            ('C','Z alone clear6.png'),
                            ('V','A alone clear6.png'),
                            ('CV','ZA alone clear6.png'),
                            ('Word','ZAZA clear stacks6.png'),
                            ('WordRec','ZAZA Rclear stacks6.png'),
                            ('TRec','T Rclear stacks6.png'),
                            ('Report','Report.png'),
                            ('ReportLogo','Generic AZT Reports.png'),
                            ('TRep','T Report.png'),
                            ('CVRep','ZA Report.png'),
                            ('Transcribe','Transcribe Tone.png'),
                            ('TranscribeC','Consonant Choice.png'),
                            ('TranscribeV','Vowel Choice.png'),
                            ('JoinUF','Join Tone.png'),
                            ('TRepcomp','T Report Comprehensive.png'),
                            ('VRepcomp','A Report Comprehensive.png'),
                            ('CRepcomp','Z Report Comprehensive.png'),
                            ('CVRepcomp','ZA Report Comprehensive.png'),
                            ('VCCVRepcomp','AZZA Report Comprehensive.png'),
                            ('backgrounded','AZT stacks6.png'),
                            #Set images for tasks
                            ('verify','Verify List.png'),
                            ('sort','Sort List.png'),
                            ('join','Join List.png'),
                            ('record','Microphone alone_sm.png'),
                            ('change','Change Circle_sm.png'),
                            ('checkedbox','checked.png'),
                            ('uncheckedbox','unchecked.png'),
                            ('NoImage','toselect/Image-Not-Found.png'),
                            ('Order!','toselect/order!.png'),
                        ]
        ntodo=len(imagelist)
        self.startruntime()
        for n,(name,filename) in enumerate(imagelist):
            try:
                #Can't hyperthread here!
                mkimg(name,filename)
            except Exception as e:
                log.info("Image {} ({}) not compiled ({})".format(
                            name,filename,e
                            ))
            try:
                self.fakeroot.ww.progress(n*100/ntodo)
            except:
                pass
        try:
            self.logfinished("Image compilation")
            self.fakeroot.ww.close()
            self.fakeroot.destroy()
            self.program['theme'].unbootstraptheme()
        except Exception as e:
            # log.info("Something happened: {}".format(e))
            # raise
            pass
    def settheme(self):
        if not self.name:
            defaulttheme='greygreen'
            multiplier=99 #The default theme will be this more frequent than others.
            pot=list(self.themes.keys())+([defaulttheme]*
                                            (multiplier*len(self.themes)-1))
            self.name='Kent' #for the colorblind (to punish others...)
            self.name='highcontrast' #for low light environments
            self.name=pot[randint(0, len(pot))-1] #mostly defaulttheme
            try:
                if platform.uname().node == 'CS-477':
                    self.name='pink'
                if (platform.uname().node == 'karlap' and
                        not self.program.get('production')):
                    self.name='Kim' #for my development
            except Exception as e:
                log.info("Assuming I'm not working from main ({}).".format(e))
        elif self.name not in self.themes:
            print("Sorry, that theme doesn't seem to be set up. Pick from "
            "these options:",self.themes.keys())
            exit()
        for k in self.themes[self.name]:
            setattr(self,k,self.themes[self.name][k])
        self.themettk = tkinter.ttk.Style()
        self.themettk.theme_use('clam')
        self.themettk.configure("Progressbar",
                                troughcolor=self.activebackground,
                                background=self.background,
                                # bordercolor=self.background,
                                # darkcolor=self.background,
                                # lightcolor=self.background
                                )
    def setthemes(self):
        self.themes={'lightgreen':{
                            'background':'#c6ffb3',
                            'activebackground':'#c6ffb3',
                            'offwhite':None,
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'}, #lighter green
                    'green':{
                            'background':'#b3ff99',
                            'activebackground':'#c6ffb3',
                            'offwhite':None,
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'pink':{
                            'background':'#ff99cc',
                            'activebackground':'#ff66b3',
                            'offwhite':None,
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'lighterpink':{
                            'background':'#ffb3d9',
                            'activebackground':'#ff99cc',
                            'offwhite':None,
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'evenlighterpink':{
                            'background':'#ffcce6',
                            'activebackground':'#ffb3d9',
                            'offwhite':'#ffe6f3',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'purple':{
                            'background':'#ffb3ec',
                            'activebackground':'#ff99e6',
                            'offwhite':'#ffe6f9',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'Howard':{
                            'background':'green',
                            'activebackground':'red',
                            'offwhite':'grey',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'Kent':{
                            'background':'red',
                            'activebackground':'green',
                            'offwhite':'grey',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'Kim':{
                            'background':'#ffbb99',
                            'activebackground':'#ffaa80',
                            'offwhite':'#ffeee6',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'yellow':{
                            'background':'#ffff99',
                            'activebackground':'#ffff80',
                            'offwhite':'#ffffe6',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'greygreen1':{
                            'background':'#62d16f',
                            'activebackground':'#4dcb5c',
                            'offwhite':'#ebf9ed',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'lightgreygreen':{
                            'background':'#9fdfca',
                            'activebackground':'#8cd9bf',
                            'offwhite':'#ecf9f4',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'greygreen':{
                            'background':'#8cd9bf',
                            'activebackground':'#66ccaa', #10% darker than the above
                            'offwhite':'#ecf9f4',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'}, #default!
                    'highcontrast':{
                            'background':'white',
                            'activebackground':'#e6fff9', #10% darker than the above
                            'offwhite':'#ecf9f4',
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'},
                    'tkinterdefault':{
                            'background':None,
                            'activebackground':None,
                            'offwhite':None,
                            'highlight': 'red',
                            'menubackground': 'white',
                            'white': 'white'}
                    }
    def setfonts(self,fonttheme='default'):
        scale=self.program['scale'] #just reading this here
        log.info("Setting fonts with {} theme".format(fonttheme))
        if fonttheme == 'smaller':
            default=int(12*scale)
        else:
            default=int(18*scale)
        title=bigger=int(default*2)
        big=int(default*5/3)
        normal=int(default*4/3)
        default=int(default)
        small=int(default*2/3)
        tiny=int(default*1/2)
        log.info("Using default font size: {}".format(default))
        andika="Andika"# not "Andika SIL"
        charis="Charis SIL"
        self.fonts={
                'title':tkinter.font.Font(family=charis, size=title), #Charis
                'instructions':tkinter.font.Font(family=charis,
                                            size=normal), #Charis
                'report':tkinter.font.Font(family=charis, size=small),
                'reportheader':tkinter.font.Font(family=charis, size=small,
                                                    # underline = True,
                                                    slant = 'italic'
                                                    ),
                'read':tkinter.font.Font(family=charis, size=big),
                'readbig':tkinter.font.Font(family=charis, size=bigger,
                                            weight='bold'),
                'small':tkinter.font.Font(family=charis, size=small),
                'tiny':tkinter.font.Font(family=charis, size=tiny),
                'default':tkinter.font.Font(family=charis, size=default),
                'fixed':tkinter.font.Font(family='TkFixedFont', size=small)
                    }
        """additional keyword options (ignored if font is specified):
        family - font family i.e. Courier, Times
        size - font size (in points, |-x| in pixels)
        weight - font emphasis (NORMAL, BOLD)
        slant - ROMAN, ITALIC
        underline - font underlining (0 - none, 1 - underline)
        overstrike - font strikeout (0 - none, 1 - strikeout)
        """
    def setscale(self):
        program=self.program #reading and setting here
        root=tkinter.Tk() #just to get these values
        h = program['screenh'] = root.winfo_screenheight()
        w = program['screenw'] = root.winfo_screenwidth()
        wmm = root.winfo_screenmmwidth()
        hmm = root.winfo_screenmmheight()
        root.destroy()
        #this computer as a ratio of mine, 1080 (286mm) x 1920 (508mm):
        hx=h/1080
        wx=w/1920
        hmmx=hmm/286
        wmmx=wmm/508
        log.info("screen height: {} ({}mm, ratio: {}/{})".format(h,hmm,hx,hmmx))
        log.info("screen width: {} ({}mm, ratio: {}/{})".format(w,wmm,wx,wmmx))
        xmin=min(hx,wx,hmmx,wmmx)
        xmax=max(hx,wx,hmmx,wmmx)
        if xmax-1 > 1-xmin:
            program['scale']=xmax
        else:
            program['scale']=xmin
        if program['scale'] < 1.02 and program['scale'] > 0.98:
            log.info("Probably shouldn't scale in this case (scale: {})".format(
                                                        program['scale']))
            program['scale']=1
        # program['scale']=0.75 #for testing
        log.info("Largest variance from 1:1 ratio: {} (this will be used to scale "
                "stuff.)".format(program['scale']))
    def setpads(self,**kwargs):
        for kwarg in ['ipady','ipadx','pady','padx']:
            if kwarg in kwargs:
                setattr(self,kwarg,kwargs[kwarg])
    def unbootstraptheme(self):
        """This is for when you have bootstrapped your main theme, to show some
        UI while your theme is being made. Once it is made, revert here.
        """
        self.program['theme']=self.originaltheme
    def __init__(self,program,**kwargs):
        self.program=program
        """This can be accessed elsewhere in this module
        through widget._root().theme.program"""
        if kwargs.get('noimagescaling'):
            self.originaltheme=self.program['theme']
            self.name=None
        else:
            if 'theme' not in self.program:
                self.name=None
            elif isinstance(self.program['theme'],str):
                self.name=self.program['theme']
            elif isinstance(self.program['theme'],Theme):
                log.error("Asked to make a theme attribute, with "
                "program['theme']={} ({})".format(self.program['theme'],
                                                type(self.program['theme'])))
                log.error("Stopping theme creation here.")
                return #only do the following only once per run
        self.program['theme']=self #this theme needs to be in use, either way
        # log.info("making theme with program {}".format(self.program))
        # I should allow a default theme here, so I can display GUI without
        # any of this already done
        self.setpads(**kwargs)
        self.setthemes()
        if kwargs.get('noimagescaling'):
            self.program['scale']=1
        else:
            self.setscale()
        self.settheme()
        log.info("Using {} theme ({})".format(self.name,self.program))
        self.setimages()
        self.setfonts()
        super(Theme, self).__init__()
        # log.info("self.photo keys: {}".format(list(self.photo)))
        # log.info("Theme initialized: {}".format(self))
class ExitFlag(object):
    def istrue(self):
        # log.debug("Returning {} exitflag".format(self.value))
        return self.value
    value=get=istrue
    def true(self):
        self.value=True
    def false(self):
        self.value=False
    def __init__(self):
        self.false()
class Renderer(ObectwArgs):
    def __init__(self,test=False,**kwargs):
        global pilisactive
        if pilisactive:
            self.isactive=True
        else:
            log.info("Seems like PIL is not installed; inactivating Renderer.")
            # self.img=None
            self.isactive=False
        self.renderings={}
        self.imagefonts={}
    def gettextsize(self, img, text, font, fspacing):
        # w, h = draw.multiline_textsize(text, font=font, spacing=fspacing)
        l, t, r, b = img.multiline_textbbox((0,0), text, font=font, spacing=fspacing)
        # w,h = r-l,b-t
        # log.info("width: {}, height: {}".format(w,h))
        return r-l,b-t
    def render(self,**kwargs):
        if not self.isactive:
            return
        self.img=None #clear past work
        fontkey=font=kwargs['font'].actual() #should always be there
        xpad=ypad=fspacing=font['size']
        fname=font['family']
        fsize=int(font['size']*1.33)
        fspacing=10
        text=kwargs['text'] #should always be there
        text=text.replace('\t','    ') #Not sure why, but tabs aren't working.
        wraplength=kwargs['wraplength'] #should always be there
        log.log(2,"Rendering ‘{}’ text with font: {}".format(text,font))
        if (('justify' in kwargs and
                        kwargs['justify'] in [tkinter.LEFT,'left']) or
            ('anchor' in kwargs and
                        kwargs['anchor'] in [tkinter.E,"e"])):
            align="left"
        else:
            align="center" #also supports "right"
        if str(font) not in self.imagefonts:
            log.info("Making image font: {}".format(str(fontkey)))
            fonttype=''
            if font['weight'] == 'bold':
                fonttype+='B'
            if font['slant'] == 'italic':
                fonttype+='I'
            if fonttype == '':
                fonttype='R'
            """make room for GentiumPlus and GentiumBookPlus, with same
            attributes:
            'Gentium Plus' and 'Gentium Book Plus'
            Bold
            BoldItalic
            Italic
            Regular
            """
            fonttypewords=fonttype.replace('B','Bold').replace('I','Italic'
                            ).replace('R','Regular')
            """Each of these is in a list, in priority order (newer, then older,
            hide staves, then don't), use the first found."""
            if fname in ["Andika","Andika SIL"]:
                files=['Andika-tstv-{}.ttf'.format(fonttypewords)]
                files+=['Andika-{}.ttf'.format(fonttypewords)]
                fonttype='R' #There's only this one for these
                files+=['Andika-tstv-{}.ttf'.format(fonttype)]
                files+=['Andika-{}.ttf'.format(fonttype)]
            elif fname in ["Charis","Charis SIL"]:
                files=['CharisSIL-tstv-{}.ttf'.format(fonttypewords)]
                files+=['CharisSIL-tstv-{}.ttf'.format(fonttype)]
                files+=['CharisSIL-{}.ttf'.format(fonttypewords)]
                files+=['CharisSIL-{}.ttf'.format(fonttype)]
            elif fname in ["Gentium","Gentium SIL","Gentium Plus"]:
                files=['GentiumPlus-tstv-{}.ttf'.format(fonttypewords)]
                files+=['GentiumPlus-{}.ttf'.format(fonttypewords)]
                if fonttype == 'B':
                    fonttype='R'
                if fonttype == 'BI':
                    fonttype='I'
                files+=['Gentium-{}.ttf'.format(fonttype)]
                files+=['Gentium-tstv-{}.ttf'.format(fonttype)]
            elif fname in ["Gentium Book Basic","Gentium Book Basic SIL",
                                                "Gentium Book Plus"]:
                files=['GentiumBookPlus-tstv-{}.ttf'.format(fonttypewords)]
                files+=['GentiumBookPlus-{}.ttf'.format(fonttypewords)]
                files+=['GenBkBas{}.ttf'.format(fonttype)]
                files+=['GenBkBas-tstv-{}.ttf'.format(fonttype)]
            elif fname in ["DejaVu Sans"]:
                fonttype=fonttype.replace('B','Bold').replace('I','Oblique'
                                                    ).replace('R','')
                if len(fonttype)>0:
                    fonttype='-'+fonttype
                files=['DejaVuSans-tstv-{}.ttf'.format(fonttype)]
                files+=['DejaVuSans{}.ttf'.format(fonttype)]
            else:
                log.error("Sorry, I have no info on font {}".format(fname))
                return
            for file in files:
                try:
                    font = PIL.ImageFont.truetype(font=file, size=fsize)
                    self.imagefonts[str(fontkey)]=font
                    log.info("Using font file {}".format(file))
                    break
                except OSError as e:
                    if e == 'cannot open resource':
                        log.debug("no file {}, checking next".format(file))
        else: #i.e., if it was done before
            # log.info("Using image font: {}".format(str(fontkey)))
            font=self.imagefonts[str(fontkey)]
        if str(fontkey) not in self.imagefonts: #i.e., neither before nor now
            log.error("Cannot find font file for {}; giving up".format(fname))
            self.img=None
            return
        img = PIL.Image.new("1", (10,10), 255)
        draw = PIL.ImageDraw.Draw(img)
        w, h = self.gettextsize(draw, text, font, fspacing)
        textori=text
        lines=textori.split('\n') #get everything between manual linebreaks
        for line in lines:
            li=lines.index(line)
            words=line.split(' ') #split by words/spaces
            nl=x=y=0
            while y < len(words):
                y+=1
                l=' '.join(words[x+nl:y+nl])
                w, h = self.gettextsize(draw, l, font, fspacing)
                log.log(2,"Round {} Words {}-{}:{}, width: {}/{}".format(y,x+nl,
                                                y+nl,l,w,wraplength))
                if wraplength and w>wraplength:
                    words.insert(y+nl-1,'\n')
                    x=y-1
                    nl+=1
            line=' '.join(words) #Join back words
            lines[li]=line
        text='\n'.join(lines) #join back sections between manual linebreaks
        w, h = self.gettextsize(draw, text, font, fspacing)
        log.log(2,"Final size w: {}, h: {}".format(w,h))
        black = 'rgb(0, 0, 0)'
        white = 'rgb(255, 255, 255)'
        img = PIL.Image.new("RGBA", (w+xpad, h+ypad), (255, 255, 255,0 )) #alpha
        draw = PIL.ImageDraw.Draw(img)
        draw.multiline_text((0+xpad//2, 0+ypad//4), text,font=font,fill=black,
                                                                align=align)
        self.img = PIL.ImageTk.PhotoImage(img)
class Exitable(object):
    """This class provides the method and init to make things exit normally.
    Hence, it applies to roots and windows, but not frames, etc."""
    def killall(self):
        self.destroy()
        sys.exit()
    def cleanup(self):
        pass
    def exittoroot(self):
        if hasattr(self,'parent') and not isinstance(self.parent,Root):
            self.parent.exittoroot()
            return
        elif hasattr(self,'parent'):
            self.parent.exitFlag.true()
    def on_quit(self):
        """Do this when a window closes, so any window functions can know
        to just stop, rather than trying to build graphic components and
        throwing an error. This doesn't do anything but set the flag value
        on exit, the logic to stop needs to be elsewhere, e.g.,
        `if self.exitFlag.istrue(): return`"""
        if hasattr(self,'exitFlag'): #only do this if there is an exitflag set
            log.info("Setting window ({}) exit flag True!".format(self))
            self.exitFlag.true()
        if self.mainwindow: #exit afterwards if main window
            self.exittoroot()
            self.killall()
        else:
            if (hasattr(self,'parent') and
                    self.parent.winfo_exists() and
                    not isinstance(self.parent,Root)):
                if not self.parent.iswaiting():
                    self.parent.deiconify()
                # else:
                #     self.parent.waitunpause()
                    # self.ww.paused=True
                # log.info("Going to deiconify {}".format(self.parent))
            # log.info("Going to cleanup {}".format(self))
            self.cleanup()
            self.destroy() #do this for everything
    def __init__(self):
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
class Gridded(ObectwArgs):
    def dogrid(self):
        if self._grid:
            log.log(4,"Gridding at r{},c{},rsp{},csp{},st{},padx{},pady{},"
                    "ipadx{},ipady{}".format(self.row,
                                self.column,
                                self.rowspan,
                                self.columnspan,
                                self.sticky,
                                self.padx,
                                self.pady,
                                self.ipadx,
                                self.ipady,
                                ))
            self.grid(
                        row=self.row,
                        column=self.column,
                        sticky=self.sticky,
                        padx=self.padx,
                        pady=self.pady,
                        ipadx=self.ipadx,
                        ipady=self.ipady,
                        columnspan=self.columnspan,
                        rowspan=self.rowspan
                        )
    def lessgridkwargs(self,**kwargs):
        for opt in self.gridkwargs:
            if opt in kwargs:
                del kwargs[opt]
            if 'b'+opt in kwargs:
                del kwargs['b'+opt]
        return kwargs
    def gridbkwargs(self,**kwargs):
        # preserve some of these for buttons
        for opt in self.gridkwargs:
            if 'b'+opt in kwargs:
                kwargs[opt]=kwargs['b'+opt]
                del kwargs['b'+opt]
        return kwargs
    def bindchildren(self,bind,command):
        self.bind(bind,command)
        for child in self.winfo_children():
            try:
                child.bindchildren(bind,command)
            except Exception as e:
                log.info("Exception in Gridded binding: {}".format(e))
                pass
    def __init__(self, *args, **kwargs): #because this is used everywhere.
        """this removes gridding kwargs from the widget calls"""
        self.gridkwargs=['sticky',
                            'row','rowspan',
                            'column','columnspan',
                            'padx','pady','ipadx','ipady']
        self._grid=False
        if set(kwargs) & set(self.gridkwargs):
            self._grid=True
            self.sticky=kwargs.pop('sticky',"ew")
            self.row=kwargs.pop('row',kwargs.pop('r',0))
            self.column=kwargs.pop('column',kwargs.pop('col',kwargs.pop('c',0)))
            self.columnspan=kwargs.pop('columnspan',1)
            self.rowspan=kwargs.pop('rowspan',1)
            self.padx=kwargs.pop('padx',0)
            self.pady=kwargs.pop('pady',0)
            self.ipadx=kwargs.pop('ipadx',0)
            self.ipady=kwargs.pop('ipady',0)
        else:
            log.log(4,"Not Gridding! ({})".format(kwargs))
class Childof(object):
    def inherit(self,parent=None,attr=None):
        """This function brings these attributes from the parent, to inherit
        from the root window, through all windows, frames, and scrolling frames, etc
        """
        # log.info("inheriting")
        if not parent and hasattr(self,'parent') and self.parent:
            parent=self.parent
        elif parent:
            self.parent=parent
        if not attr:
            attrs=['theme',
                    # 'fonts', #in theme
                    # 'debug',
                    'wraplength',
                    # 'photo', #in theme
                    'renderer',
                    # 'program',
                    'exitFlag']
        else:
            attrs=[attr]
        for attr in attrs:
            if hasattr(parent,attr):
                setattr(self,attr,getattr(parent,attr))
                # log.info("inheriting {} from parent {} (to {})"
                #         "".format(attr,type(parent),type(self)))
            else:
                log.debug("parent {} (of {}) doesn't have attr {}, skipping inheritance"
                        "".format(parent,type(self),attr))
    def __init__(self, parent): #because this is used everywhere.
        self.parent=parent
        self.inherit()
class UI(ObectwArgs):
    """docstring for UI, after tkinter widgets are initted."""
    def wait(self,msg=None,cancellable=False):
        if self.iswaiting():
            log.debug("There is already a wait window: {}".format(self.ww))
            return
        self.withdraw()
        self.ww=Wait(self,msg,cancellable=cancellable)
    def iswaiting(self):
        return hasattr(self,'ww') and self.ww.winfo_exists()
    def waitprogress(self,x):
        self.ww.progress(x)
    def waitpause(self):
        self.ww.withdraw()
        self.ww.paused=True
    def waitunpause(self):
        self.ww.deiconify()
        self.ww.paused=False
    def waitcancel(self):
        self.waitcancelled=True
        log.info("Wait cancel registered; waiting to cancel")
    def waitdone(self):
        try:
            self.ww.close()
            self.deiconify()
        except tkinter.TclError:
            pass
        except AttributeError:
            log.info("Seem to have tried stopping waiting, when I wasn't...")
    def __init__(self): #because this is used everywhere.
        # log.info("UI self._root(): {} ({})".format(self._root(),type(self._root())))
        # log.info("UI self._root() dir: {}".format(dir(self._root())))
        # log.info("self.parent: {} ({})".format(self.parent,type(self.parent)))
        # log.info("self.parent._root(): {} ({})".format(self.parent._root(),type(self.parent._root())))
        # self.theme=self._root().program['theme']
        # log.info("UI {}.theme({}).photo keys: {}".format(self,self.theme,
        #                                                 list(self.theme.photo)))
        for a in ['background','bg','troughcolor']:
            if a in self.keys():
                self[a]=self.theme.background
        for a in ['ipady','ipadx','pady','padx']:
            if a in self.keys() and hasattr(self.theme,a):
                self[a]=getattr(self.theme,a)
        for a in ['activebackground','selectcolor']:
            if a in self.keys():
                self[a]=self.theme.activebackground
        self.waitcancelled=False
            # try:
            #     self['background']=self.theme.background
            #     self['bg']=self.theme.background
            #     # self['foreground']=self.theme.background
            #     self['troughcolor']=self.theme.background
            #     self['activebackground']=self.theme.activebackground
            # except TypeError as e:
            #     log.info("TypeError {}".format(e))
            # except tkinter.TclError as e:
            #     log.info("TclError {}".format(e))
        # super(UI, self).__init__(*args, **kwargs)
class Image(tkinter.PhotoImage):
    def biggerby(self,x):
        #always do this one first, if doing both, to start from scratch
        # log.info(f"scaling bigger by {x}")
        self.scaled=self.zoom(x,x)
    def smallerby(self,x):
        # log.info(f"scaling smaller by {x}")
        try:
            self.scaled=self.scaled.subsample(x,x)
        except AttributeError:
            self.scaled=self.subsample(x,x)
    def maxhw(self,scaled=False):
        if scaled:
            return max(self.scaled.width(),self.scaled.height())
        else:
            return max(self.width(),self.height())
    def scale(self,scale,pixels=100,resolution=5):
        """'resolution*r' and 'resolution' here express a float scaling ratio
        as two integers, so r = 0.7 = 7/10, because the zoom and subsample fns
        only work on integers. To not waste computation, resolution starts
        small and increases to what is needed to keep both integers positive"""
        # log.info("Scaling with these args: scale {}, pixels {}, resolution {}"
        #         "".format(scale,pixels,resolution))
        s=pixels*scale #the number of pixels, scaled
        r=s/self.maxhw() #the ratio we need to reduce actual pixels by
        # log.info("scaled pixels: {} (of {})".format(s,pixels))
        if not r:
            r=1 #don't scale for pixels=r=0
        while not int(resolution*r): #This must be >=1 (True)
            resolution=resolution*2
        # log.info(f"scaling with {int(resolution*r)}/{int(resolution)}="
        #         f"{int(resolution*r)/int(resolution)} as a proxy for "
        #         f"{s}/{self.maxhw()}={r}")
        self.biggerby(int(resolution*r))
        # log.info("Image: {} ({})".format(self.scaled, self.maxhw(scaled=True)))
        self.smallerby(int(resolution))
        # self[pixels]=self.scaled
        # log.info("Image: {} ({})".format(self.scaled, self.maxhw(scaled=True)))
    def __init__(self,filename):
        # self.name=filename
        try:
            super(Image, self).__init__(file=filename)#,*args, **kwargs)
        except tkinter.TclError as e:
            # log.info("Error: {} ({})".format(e.args,type(e)))
            if "couldn't recognize data in image file" in e.args[0]:
                raise #this is processed elsewhere
            elif 'value for "-file" missing' in e.args[0]:
                raise #this is processed elsewhere
            else:
                log.info("Image error: {}".format(e))
        self.biggerby(1)
class IntVar(tkinter.IntVar):
    def __init__(self, *args, **kwargs):
        super(tkinter.IntVar, self).__init__(*args, **kwargs)
class StringVar(tkinter.StringVar):
    def __init__(self, *args, **kwargs):
        super(tkinter.StringVar, self).__init__(*args, **kwargs)
class BooleanVar(tkinter.BooleanVar):
    def __init__(self, *args, **kwargs):
        super(tkinter.BooleanVar, self).__init__(*args, **kwargs)
"""below here has UI"""
class Root(Exitable,tkinter.Tk):
    """this is the root of the tkinter GUI."""
    def __init__(self, program={}, *args, **kwargs):
        """specify theme name in program['theme']"""
        """bring in program here, send it to theme, everyone accesses scale from there."""
        """"Some roots aren't THE root, e.g., contextmenu. Furthermore, I'm
        currently not showing the root, so the user will never exit it."""
        # log.info("Root called with program dict {}".format(program))
        self.program=program
        if 'root' not in self.program:
            self.program['root']=self
        self.mainwindow=False
        self.exitFlag = ExitFlag()
        tkinter.Tk.__init__(self)
        self.withdraw() #this is almost always correct
        try:
            assert not kwargs.get('noimagescaling') #otherwise, make copy theme
            assert isinstance(self.program['theme'],Theme) #use what's there
            self.theme=self.program['theme']
        except (KeyError,AssertionError):
            self.theme=Theme(self.program, **kwargs)
        self.renderer=Renderer()
        Exitable.__init__(self)
        UI.__init__(self)
        # log.info("self.theme.photo keys: {}".format(list(self.theme.photo)))
        # log.info("self.theme({}).photo keys: {}".format(self.theme,list(self.theme.photo)))
        log.info("Root initialized")
"""These have parent (Childof), but no grid"""
class Toplevel(Childof,Exitable,tkinter.Toplevel,UI): #NoParent
    """This and all Childof classes should have a parent, to inherit a common
    theme. Otherwise, colors, fonts, and icons will be incongruous."""
    def __init__(self, parent, *args, **kwargs):
        self.mainwindow=False
        Childof.__init__(self,parent)
        tkinter.Toplevel.__init__(self)
        # log.info("Toplevel._root(): {} ({})".format(self._root(),type(self._root())))
        # log.info("Toplevel.parent._root(): {} ({})".format(self.parent._root(),type(self.parent._root())))
        Exitable.__init__(self)
        UI.__init__(self)
        self.protocol("WM_DELETE_WINDOW", lambda s=self: Window.on_quit(s))
class Menu(Childof,tkinter.Menu): #not Text
    def pad(self,label):
        w=5 #Make menus at least w characters wide
        if len(label) <w:
            spaces=" "*(w-len(label))
            label=spaces+label+spaces
        return label
    def add_command(self,label,command):
        # log.info("Menu opts: {}".format((self,label,command)))
        label=self.pad(label)
        tkinter.Menu.add_command(self,label=label,command=command)
    def add_cascade(self,label,menu):
        # log.info("Cascade opts: {}".format((self,label,menu)))
        label=self.pad(label)
        tkinter.Menu.add_cascade(self,label=label,menu=menu)
    def __init__(self,parent,**kwargs):
        Childof.__init__(self,parent)
        self.theme=parent.theme
        tkinter.Menu.__init__(self,parent,
                                font=self.theme.fonts['default'],
                                **kwargs)
        UI.__init__(self)
        self['background']=self.theme.menubackground
class Progressbar(Gridded,Childof,tkinter.ttk.Progressbar):
    def current(self,value):
        if 0 <= value <= 100:
            self['value']=value
        self.update_idletasks() #updates just geometry
    def __init__(self, parent, **kwargs):
        # log.info("Initializing Progressbar object")
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        if 'orient' not in kwargs:
            kwargs['orient']='horizontal' #or 'vertical'
        if 'mode' not in kwargs:
            kwargs['mode']='determinate' #or 'indeterminate'
        tkinter.ttk.Progressbar.__init__(self,parent,**kwargs)
        UI.__init__(self)
        self.dogrid()
class Text(Childof,ObectwArgs):
    """This converts kwargs 'text', 'image' and 'font' into attributes which are
    default where not specified, and rendered where appropriate for the
    characters in the text."""
    def wrap(self):
        availablexy(self)
        if not hasattr(self,'wraplength'):
            wraplength=self.maxwidth
        else:
            wraplength=min(self.wraplength,self.maxwidth)
        self.config(wraplength=wraplength)
        log.log(3,'self.maxwidth (Label class): {}'.format(self.maxwidth))
    def render(self, **kwargs):
        if not self.renderer.isactive:
            return
        style=(self.font['family'], # from kwargs['font'].actual()
                self.font['size'],self.font['weight'],
                self.font['slant'],self.font['underline'],
                self.font['overstrike'])
        if style not in self.renderer.renderings:
            self.renderer.renderings[style]={}
        if kwargs['wraplength'] not in self.renderer.renderings[style]:
            self.renderer.renderings[style][kwargs['wraplength']]={}
        thisrenderings=self.renderer.renderings[style][kwargs['wraplength']]
        if (self.text in thisrenderings and
                thisrenderings[self.text] is not None):
            log.log(5,"text {} already rendered with {} wraplength, using."
                    "".format(self.text,kwargs['wraplength']))
            self.image=thisrenderings[self.text]
            self.text=''
        elif self.image:
            log.error("You gave an image and tone characters in the same "
            "label? ({},{})".format(self.image,self.text))
            return
        else:
            log.log(5,"Sticks found! (Generating image for label)")
            self.renderer.render(
                        text=self.text,
                        font=self.font,
                        # wraplength=kwargs['wraplength'],
                        **kwargs)
            self.tkimg=self.renderer.img
            if self.tkimg is not None:
                thisrenderings[self.text]=self.image=self.tkimg
                self.text=''
    def lesstextkwargs(self, **kwargs):
        for opt in self.textkwargs:
            if opt in kwargs:
                del kwargs[opt]
        return kwargs
    def __init__(self,parent,**kwargs):
        Childof.__init__(self,parent)
        self.textkwargs=['text','image','font','norender']
        self.text=kwargs.pop('text','')
        # self.renderings=parent.renderings
        self.anchor=kwargs.pop('anchor',"w")
        if 'font' in kwargs:
            if isinstance(kwargs['font'],tkinter.font.Font):
                # log.info("Found font {}; using as is".format(kwargs['font']))
                self.font=kwargs['font']
            elif kwargs['font'] in self.theme.fonts: #if font key (e.g., 'small')
                self.font=self.theme.fonts[kwargs['font']] #change key to font
            else:
                log.error("Unknown font specification: {}".format(kwargs['font']))
            del kwargs['font']
        else:
            self.font=self.theme.fonts['default']
        # log.info(getattr(self,'wraplength',0))
        self.wraplength=kwargs['wraplength']=kwargs.get('wraplength',
                                        getattr(self,'wraplength',0))
        # log.info("Text wraplength: {}".format(kwargs['wraplength']))
        # self.wraplength=kwargs.get('wraplength',defaultwr) #also for ButtonLabel
        self.norender=kwargs.pop('norender',False)
        self.image=kwargs.pop('image',None)
        if isinstance(self.image,str) and self.image in self.theme.photo:
            self.image=self.theme.photo[self.image]
        d=set(["̀","́","̂","̌","̄","̃", "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉"])
        sticks=set(['˥','˦','˧','˨','˩',' '])
        if (hasattr(self.text, '__iter__')
                    and set(self.text) & (sticks|d)
                    and not self.norender):
            self.render(**kwargs)
            # log.info("text and image: {} - {}".format(self.text,self.image))
        else:
            self.text=nfc(self.text)
        # log.info(getattr(self,'wraplength',0))
        # log.info("Text wraplength: {}".format(kwargs['wraplength']))
        # log.info(parent)
        # super(Text,self).__init__(
        #                             text=self.text,
        #                             image=self.image,
        #                             **kwargs)
"""These have parent (Childof) and grid (Gridded)"""
class Frame(Gridded,Childof,tkinter.Frame):
    def columns(self):
        return self.grid_size()[0]
    def rows(self):
        return self.grid_size()[1]
    def windowsize(self):
        if not hasattr(self,'configured'):
            self.configured=0
        if self.configured>10:
            return
        availablexy(self)
        contentrw=self.winfo_reqwidth()
        contentrh=self.winfo_reqheight()
        if ((self.winfo_width() < contentrw)
                or (self.winfo_width() > self.maxwidth)):
                self.config(width=min(self.maxwidth,contentrw))
        if ((self.winfo_height() < contentrh)
                or (self.winfo_height() > self.maxheight)):
            self.config(height=min(self.maxheight,contentrh))
        self.configured+=1
    def __init__(self, parent, **kwargs):
        # log.info("Initializing Frame object")
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        tkinter.Frame.__init__(self,parent,**kwargs)
        UI.__init__(self)
        self.dogrid()
class Label(Gridded,Text,tkinter.Label): #,tkinter.Label
    def __init__(self, parent, **kwargs):
        # log.info("Label Parent: {}".format(type(parent)))
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        Text.__init__(self,parent,**kwargs)
        kwargs=self.lesstextkwargs(**kwargs)
        """These shouldn't need to be here..."""
        # log.info("{}; {}; {}; {}; {}".format(
        #                         parent,
        #                         self.text,
        #                         self.image,
        #                         self.font,
        #                         kwargs
        #                         )
        #         )
        tkinter.Label.__init__(self,
                                parent,
                                text=self.text,
                                image=self.image,
                                font=self.font,
                                **kwargs)
        i=self.grid_info()
        if i and self.text:
            self.wrap()
        UI.__init__(self)
        self.dogrid()
class Message(Gridded,Text,tkinter.Message): #,tkinter.Label
    """I'm not sure if this will ever have value, but here it is."""
    def __init__(self, parent, **kwargs):
        # log.info("Label Parent: {}".format(type(parent)))
        kwargs['norender']=True
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        Text.__init__(self,parent,**kwargs)
        kwargs=self.lesstextkwargs(**kwargs)
        """These shouldn't need to be here..."""
        # log.info("{}; {}; {}; {}; {}".format(
        #                         parent,
        #                         self.text,
        #                         self.image,
        #                         self.font,
        #                         kwargs
        #                         )
        #         )
        tkinter.Message.__init__(self,
                                parent,
                                text=self.text,
                                image=self.image,
                                font=self.font,
                                **kwargs)
        i=self.grid_info()
        if i and self.text:
            self.wrap()
        UI.__init__(self)
        self.dogrid()
class Button(Gridded,Text,tkinter.Button):
    def nofn(self):
        pass
    def __init__(self, parent, choice=None, window=None, command=None, **kwargs):
        """Usta include column=0, row=1, norender=False,"""
        # log.info("Button Parent: {}".format(type(parent)))
        # log.info("button kwargs: {}".format(kwargs))
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        Text.__init__(self,parent,**kwargs)
        kwargs=self.lesstextkwargs(**kwargs)
        kwargs=self.gridbkwargs(**kwargs)
        # `command` is my hacky command specification, with lots of args added.
        # cmd is just the command passing through.
        if 'cmd' in kwargs and kwargs['cmd'] is not None:
            cmd=kwargs['cmd']
            del kwargs['cmd'] #we don't want this going to the button as is.
        elif command is None:
            cmd=self.nofn
        else:
            """This doesn't seem to be working, but OK to avoid it..."""
            if window is not None:
                if choice is not None:
                    cmd=lambda w=window:command(choice,window=w)
                else:
                    cmd=lambda w=window:command(window=w)
            else:
                if choice is not None:
                    cmd=lambda :command('choice')
                else:
                    cmd=lambda :command()
        tkinter.Button.__init__(self,
                                parent,
                                command=cmd,
                                text=self.text,
                                image=self.image,
                                font=self.font,
                                **kwargs)
        UI.__init__(self)
        self.dogrid()
class EntryField(Gridded,Text,UI,tkinter.Entry):
    def renderlabel(self,grid=False,event=None):
        v=self.get()
        if hasattr(self,'rendered'): #Get grid info before destroying old one
            mygrid=self.rendered.grid_info()
            grid=True
            self.rendered.destroy()
        self.rendered=Label(self.parent,text=v)
        d=["̀","́","̂","̌","̄","̃", "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉",
            "˥", "˦", "˧", "˨", "˩",
            ]
        if set(d) & set(v):
            if grid:
                self.rendered.grid(**mygrid)
            elif hasattr(self,'rendergrid'):
                self.rendered.grid(**self.rendergrid)
            else:
                log.error("Help! I have no idea what happened!")
            if hasattr(self,'rendergrid'):
                delattr(self,'rendergrid')
        elif grid:
                self.rendergrid=mygrid
    def __init__(self, parent, render=False, **kwargs):
        # log.info("grid kwargs: {}".format(kwargs))
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        # log.info("text kwargs: {}".format(kwargs))
        Childof.__init__(self,parent)
        Text.__init__(self, parent, **kwargs)
        # log.info("textless kwargs: {}".format(kwargs))
        kwargs=self.lesstextkwargs(**kwargs)
        # log.info("font: {}".format(self.font))
        tkinter.Entry.__init__(self,parent,
                                font=self.font,
                                text=self.text,
                                **kwargs)
        if render is True:
            self.bind('<KeyRelease>', self.renderlabel)
            self.renderlabel()
        UI.__init__(self)
        self['background']=self.theme.offwhite #because this is for entry...
        self.dogrid()
class RadioButton(Gridded,Childof,tkinter.Radiobutton):
    def __init__(self, parent, **kwargs):
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        self.parent=parent
        if 'font' not in kwargs:
            kwargs['font']=self.theme.fonts['default']
        tkinter.Radiobutton.__init__(self,parent,**kwargs)
        UI.__init__(self)
        self.dogrid()
class CheckButton(Gridded,Childof,tkinter.Checkbutton):
    def __init__(self, parent, **kwargs):
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        tkinter.Checkbutton.__init__(self,
                                parent,
                                image=self.theme.photo['uncheckedbox'],
                                selectimage=self.theme.photo['checkedbox'],
                                indicatoron=False,
                                compound='left',
                                font=self.theme.fonts['read'],
                                anchor='w',
                                **kwargs
                                )
        UI.__init__(self)
        self.dogrid()
class Scrollbar(Gridded,Childof,tkinter.Scrollbar):
    """Scrollbar for scrolling frames."""
    def __init__(self, parent, *args, **kwargs):
        """set this befor gridded call"""
        if 'orient' in kwargs and kwargs['orient']==tkinter.HORIZONTAL:
            kwargs['sticky']=kwargs.get('sticky',tkinter.E+tkinter.W)
        else:
            kwargs['sticky']=kwargs.get('sticky',tkinter.N+tkinter.S)
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        # yscrollbar.config(background=self.theme.background)
        # yscrollbar.config(activebackground=self.theme.activebackground)
        # yscrollbar.config(troughcolor=self.theme.background)
        tkinter.Scrollbar.__init__(self,parent,
                                    **kwargs
                                    )
        """after theme is inherited:"""
        UI.__init__(self)
        self.dogrid()
"""These classes don't call tkinter classes directly"""
class Window(Toplevel):
    def resetframe(self):
        if self.parent.exitFlag.istrue():
            return
        if self.winfo_exists(): #If this has been destroyed, don't bother.
            if hasattr(self,'frame') and type(self.frame) is Frame:
                self.frame.destroy()
            for rc in [0,2]:
                self.outsideframe.grid_rowconfigure(rc, weight=3)
                self.outsideframe.grid_columnconfigure(rc, weight=3)
            self.frame=Frame(self.outsideframe,
                            row=1, column=1, sticky='nsew'
                            )
    def __init__(self, parent, backcmd=False, exit=True, title="No Title Yet!",
                choice=None, *args, **kwargs):
        # self.parent=parent
        # self.theme=parent.theme
        """Things requiring tkinter.Window below here"""
        Toplevel.__init__(self, parent) #no title attr for Toplevel
        # self.config(className="azt")
        # self['background']=self.theme.background
        # self['background']=self.theme.background
        """Is this section necessary for centering on resize?"""
        for rc in [0,2]:
            self.grid_rowconfigure(rc, weight=3)
            self.grid_columnconfigure(rc, weight=3)
        self.outsideframe=Frame(self,
                                row=1, column=1,sticky='we',
                                padx=(25,0),
                                pady=(0,25)
                                )
        """Give windows some margin"""
        # log.info("Theme: {}".format(self.theme))
        # log.info("Theme.photo: {}".format(self.theme.photo))
        self.iconphoto(False, self.theme.photo['icon']) #don't want this transparent
        self.title(title)
        self.resetframe()
        self.exitFlag=ExitFlag() #This overwrites inherited exitFlag
        if exit:
            e=(_("Exit")) #This should be the class, right?
            self.exitButton=Button(self.outsideframe, width=10, text=e,
                                command=self.on_quit,
                                font='small',
                                padx=(0,25),
                                            )
            self.exitButton.grid(column=2,row=2)
        else:
            self.outsideframe['padx']=25
        if backcmd is not False: #This one, too...
            b=(_("Back"))
            cmd=lambda:backcmd(parent, window, check, entry, choice)
            self.backButton=Button(self.outsideframe, width=10, text=b,
                                command=cmd,
                                            )
            self.backButton.grid(column=3,row=2)
        UI.__init__(self)
        # self.dogrid()
class ContextMenu(Childof):
    def updatebindings(self):
        self.parent.bind('<Motion>', self._bind_to_makemenus)
        self.parent.bind('<Leave>', self._unbind_to_makemenus) #parent only
    def undo_popup(self,event=None):
        if hasattr(self,'menu'):
            log.log(2,"undo_popup Checking for ContextMenu.menu: {}".format(
                                                            self.menu.__dict__))
            try:
                self.root.destroy() #Tk()
                log.log(3,"popup parent/root destroyed")
            except:
                log.log(3,"popup parent/root not destroyed!")
            finally:
                self.parent.unbind_all('<Button-1>')
    def menuinit(self):
        """redo menu on context change"""
        self.menu = Menu(self.root, tearoff=0)
        try:
            log.info("menuinit done")#: {}".format(self.menu.__dict__))
        except:
            log.error("Problem initializing context menu")
    def menuitem(self,msg,cmd):
        try:
            self.menu.add_command(label=msg,command=cmd)
        except AttributeError:
            self.menuinit()
            self.menu.add_command(label=msg,command=cmd)
    def dosetcontext(self):
        # You need to have a setcontext() method for the
        # parent of this context menu, to set menu
        # items under appropriate conditions
        # There is a default 'show menus only' one in HasMenus()
        try:
            # log.info("setcontext: {}".format(self.parent.setcontext))
            self.parent.setcontext(context=self.context)
        except Exception as e:
            log.error(_("Exception in dosetcontext: {}").format(e))
    def do_popup(self,event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        except:
            log.log(4,"Problem with self.menu.tk_popup; setting context")
            self.getroot()
            self.dosetcontext()
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release() #allows click on main window
    def _bind_to_makemenus(self,event): #all needed to cover all of window
        self.parent.bind_all('<Button-3>',self.do_popup) #_all
        self.parent.bind_all('<Button-1>',self.undo_popup)
    def _unbind_to_makemenus(self,event):
        self.parent.unbind_all('<Button-3>')
    def getroot(self):
        # log.info("parent: {}".format(self.parent))
        # log.info("parent._root(): {}".format(self.parent._root()))
        # log.info("parent._root().program: {}".format(self.parent._root().program))
        # log.info("parent._root().program['theme']: {}".format(self.parent._root().program['theme']))
        self.root=Root(self.parent._root().program) #self.parent._root().program #tkinter.Tk()
        self.root.withdraw()
        self.root.parent=self.parent
        Childof.inherit(self.root,self.parent)
    def __init__(self,parent,context=None):
        Childof.__init__(self,parent)
        self.getroot()
        super(ContextMenu,self).__init__(parent)
        self.parent.context=self
        self.context=context #where the menu is showing (e.g., verifyT)
        # self.menuinit() #can't redo after context change
        # self.inherit()
        self.updatebindings()
        # UI.__init__(self)
"""These have gridding (not Window or ContextMenu, above)"""
class ButtonFrame(Frame):
    def __init__(self,parent,**kwargs):
        # Gridded.__init__(self,**kwargs)
        # Childof.__init__(self,parent)
        optionlist=kwargs.pop('optionlist')
        command=kwargs.pop('command')
        window=kwargs.pop('window',None)
        # log.info("Buttonframe option list: {} ({})".format(optionlist,command))
        Frame.__init__(self,parent,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        # for kwarg in ['row', 'column']: #done with these
        #     if kwarg in kwargs:
        #         del kwargs[kwarg]
        gimmenull=False # When do I want a null option added to my lists? ever?
        # self['background']=self.theme.background
        i=0
        """Make sure list is in the proper format: list of dictionaries"""
        if type(optionlist) is not list:
            print("optionlist is Not a list!",optionlist,type(optionlist))
            return
        elif (optionlist is None) or (len(optionlist) == 0):
            print("list is empty!",type(optionlist))
            return
            """Assuming from here on that the first list item represents
            the format of the whole list; hope that's true!"""
        elif type(optionlist[0]) is dict:
            # log.info("looks like options are already in dictionary format.")
            pass
        else: #tuple, str or int
            if None in optionlist:
                log.error(_("Having None as a list is fine, but you need to "
                "put it in a tuple, with a second argument to display, so "
                "users know what it means when they select it."))
                return
            log.info("first optionlist item: {}".format(optionlist[0]))
            optionlist = [(
                            {'code':optionlist[i], 'name':optionlist[i]}
                            if type(optionlist[i]) is not tuple
                            else {'code':optionlist[i][0],
                                'name':optionlist[i][1]}
                            if type(optionlist[i][1]) is str
                            else {'code':optionlist[i][0],
                                'description':optionlist[i][1]}
                            ) for i in range(0, len(optionlist))]
        if not 'name' in optionlist[0]: #duplicate name from code.
            for i in range(0, len(optionlist)):
                log.info("optionlist item: {}".format(optionlist[i]))
                optionlist[i]['name']=str(optionlist[i]['code'])
        if gimmenull == True:
            optionlist.append(({code:"Null",name:"None of These"}))
        # log.info("These are the options going to the set of buttons: {}".format(
        #                                                             optionlist))
        for choice in optionlist:
            if choice['name'] == ["Null"]:
                command=newvowel #come up with something better here..…
            if 'description' in choice:
                text=choice['name']+' ('+str(choice['description'])+')'
            else:
                text=choice['name']
            """commands are methods, so this normally includes self (don't
            specify it here). x= as a lambda argument allows us to assign the
            variable value now (in the loop across choices). Otherwise, it will
            maintain a link to the variable itself, and give the last value it
            had to all the buttons... --not what we want!
            """
            if window:
                cmd=lambda x=choice['code'], w=window:command(x,window=w)
                kwargs['window']=window
            else:
                cmd=lambda x=choice['code']:command(x)
            b=Button(self,text=text,choice=choice['code'],
                    cmd=cmd,#width=self.width,
                    row=i,
                    **kwargs
                    )
            i=i+1
        UI.__init__(self)
class ScrollingFrame(Frame):
    def _bound_to_mousewheel(self, event):
        # with Windows OS
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheelMS)
        # with Linux OS
        self.canvas.bind_all("<Button-5>", self._on_mousewheelup)
        self.canvas.bind_all("<Button-4>", self._on_mousewheeldown)
    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
    def _on_mousewheelMS(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def _on_mousewheelup(self, event):
        self.canvas.yview_scroll(1,"units")
    def _on_mousewheeldown(self, event):
        self.canvas.yview_scroll(-1,"units")
    def _configure_interior(self, event=None):
        log.log(4,"_configure_interior, on content change")
        self.update_idletasks()
        size = (self.content.winfo_reqwidth(), self.content.winfo_reqheight())
        self.canvas.config(scrollregion="0 0 %s %s" % size)
        """This makes sure the canvas is as large as what you put on it"""
        self.windowsize() #this needs to not keep running
        self.update_idletasks()
        #     self.configured+=1
        # if self.winfo_width() < self.canvas.winfo_width():
        #     log.info("self width less than canvas!")
        #     self.canvas.config(width=self.winfo_width())
        # if self.winfo_height() < self.content.winfo_height():
        #     log.info("self height less than content; ok!")
        #     self.config(width=self.content.winfo_width())
        # if self.winfo_width() > self.canvas.winfo_width():
        #     log.info("self width greater than canvas; ok!")
        #     self.canvas.config(width=self.winfo_width())
        # if self.winfo_height() > self.content.winfo_height():
        #     log.info("self height greater than content!")
        #     self.config(width=self.content.winfo_width())
        # if self.content.winfo_reqwidth() > self.content.winfo_width():
        #     # update the canvas's width to fit the inner frame
        #     self.content.config(width=self.content.winfo_reqwidth())
        if self.content.winfo_reqwidth() != self.canvas.winfo_width():
            # update the canvas's width to fit the inner frame
            self.canvas.config(width=self.content.winfo_reqwidth())
        if self.content.winfo_reqheight() != self.canvas.winfo_height():
            # update the canvas's width to fit the inner frame
            self.canvas.config(height=self.content.winfo_reqheight())
        log.log(4,"_configure_interior done.")
        self._configure_canvas() #bc we changed the canvas
        self.hwinfo(event)
    def hwinfo(self,event=None):
        return #unless needed for debugging
        if event is not None:
            log.info("event.widget.winfo_height={}, width={}".format(
                event.widget.winfo_height(),
                event.widget.winfo_width()
                ))
            log.info("event.height={}, width={}".format(
                                    event.height, event.width))
        log.info("self.reqheight={}, reqwidth={}".format(
                self.winfo_reqheight(), self.winfo_reqwidth()))
        log.info("self.height={}, width={}".format(
                self.winfo_height(), self.winfo_width()))
        log.info("self.content.reqheight={}, reqwidth={}".format(
                self.content.winfo_reqheight(), self.content.winfo_reqwidth()))
        log.info("self.content.height={}, width={}".format(
                self.content.winfo_height(), self.content.winfo_width()))
        log.info("self.canvas.reqheight={}, reqwidth={}".format(
                self.canvas.winfo_reqheight(), self.canvas.winfo_reqwidth()))
        log.info("self.canvas.height={}, width={}\n".format(
                self.canvas.winfo_height(), self.canvas.winfo_width()))
    def windowsize(self, event=None):
        availablexy(self) #>self.maxheight, self.maxwidth
        """This section deals with the content on the canvas (self.content)!!
        This is how much space the contents of the scrolling canvas is asking
        for. We don't need the scrolling frame to be any bigger than this."""
        self.content.update_idletasks()
        contentrw=self.content.winfo_reqwidth()+self.yscrollbarwidth
        contentrh=self.content.winfo_reqheight()
        # for child in self.content.winfo_children():
        #     log.log(3,"parent h: {}; child: {}; w:{}; h:{}".format(
        #                                 self.content.winfo_reqheight(),
        #                                 child,
        #                                 child.winfo_reqwidth(),
        #                                 child.winfo_reqheight()))
        #     contentrw=max(contentrw,child.winfo_reqwidth())
        #     contentrh+=child.winfo_reqheight()
        #     log.log(2,"{} ({})".format(child.winfo_reqwidth(),child))
        #     for grandchild in child.winfo_children():
        #         log.log(3,"child h: {}; grandchild: {}; w:{}; h:{}".format(
        #                             child.winfo_reqheight(),
        #                             grandchild,
        #                             grandchild.winfo_reqwidth(),
        #                             grandchild.winfo_reqheight()))
        #         contentrw=max(contentrw,grandchild.winfo_reqwidth())
        #         contentrh+=grandchild.winfo_reqheight()
        #         for greatgrandchild in grandchild.winfo_children():
        #             log.log(3,"grandchild h: {}; greatgrandchild: {}; w:{}; h:{}".format(
        #                                 grandchild.winfo_reqheight(),
        #                                 greatgrandchild,
        #                                 greatgrandchild.winfo_reqwidth(),
        #                                 greatgrandchild.winfo_reqheight()))
        #             contentrw=max(contentrw,greatgrandchild.winfo_reqwidth())
        #             contentrh+=greatgrandchild.winfo_reqheight()
        log.log(2,contentrw)
        log.log(2,self.parent.winfo_children())
        log.log(2,'self.winfo_width(): {}; contentrw: {}; self.maxwidth: {}'
                    ''.format(self.winfo_width(),contentrw,self.maxwidth))
        """This section deals with the outer scrolling frame (self)!!
        If the current scrolling frame dimensions are smaller than the
        scrolling content, or else pushing the window off the screen, then make
        the scrolling window the smaller of
            -the scrolling content or
            -the max dimensions, from above."""
        #This should maybe be pulled out to another method?
        #scrolling window width
        if contentrw > self.maxwidth: #self.winfo_width() <
            width=self.maxwidth
        else:
            width=contentrw #self.config(width=contentrw)
        # if self.winfo_width() > self.maxwidth:
        #     self.config(width=self.maxwidth)
        #scrolling window height
        if contentrh > self.maxheight:
            height=self.maxheight #self.config(height=self.maxheight)
        else: #if self.winfo_height() < contentrh:
            height=contentrh# self.config(height=contentrh)
        self.config(height=height, width=width)
        log.log(4,"height={}, width={}".format(height, width))
        # if self.winfo_height() > self.maxheight:
        #     self.config(height=self.maxheight)
    def _configure_canvas(self, event=None):
        log.log(4,"_configure_canvas on canvas change")
        #this configures self.canvas
        self.update_idletasks()
        # if self.content.winfo_reqwidth() != self.content.winfo_width():
        #     log.info("self.content reqwidth not same as width! ({}≠{})".format(
        #     self.content.winfo_reqwidth(),self.content.winfo_width()
        #     ))
        #     self.content.configure(width=self.content.winfo_reqwidth())
        if self.content.winfo_reqwidth() != self.canvas.winfo_width():
            log.log(4,"self.content reqwidth differs from canvas; fixing.")
            # update the inner frame's width to fill the canvas
            # self.content_id.config(width=self.content.winfo_reqwidth())
            self.canvas.itemconfigure(self.content_id,
                                        width=self.content.winfo_reqwidth())
        if self.content.winfo_reqheight() != self.canvas.winfo_height():
            log.log(4,"self.content reqheight differs from canvas; fixing.")
            self.canvas.itemconfigure(self.content_id,
                                        height=self.content.winfo_reqheight())
        # self.canvas.config(scrollregion=self.canvas.bbox("all"))
        log.log(4,"_configure_canvas done.")
        self.hwinfo(event)
        # if self.winfo_height() > self.maxheight:
        #     self.config(height=self.maxheight)
    def tobottom(self):
        self.update_idletasks()
        self.canvas.yview_moveto(1)
    def totop(self):
        self.update_idletasks()
        self.canvas.yview_moveto(0)
    def __init__(self,parent,xscroll=False,**kwargs):
        # Gridded.__init__(self,**kwargs)
        # Childof.__init__(self,parent)
        """Make this a Frame, with all the inheritances, I need"""
        Frame.__init__(self, parent, **kwargs)
        """Not sure if I want these... rather not hardcode."""
        # log.debug(self.parent.winfo_children())
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        """With or without the following, it still scrolls through..."""
        self.grid_propagate(0) #make it not shrink to nothing

        """We might want horizonal bars some day? (also below)"""
        if xscroll == True:
            xscrollbar = Scrollbar(self, orient=tkinter.HORIZONTAL,
                                            row=1, column=0
                                            )
        yscrollbar = Scrollbar(self, row=0, column=1)
        """Should decide some day which we want when..."""
        self.yscrollbarwidth=50 #make the scrollbars big!
        self.yscrollbarwidth=0 #make the scrollbars invisible (use wheel)
        self.yscrollbarwidth=15 #make the scrollbars useable, but not obnoxious
        yscrollbar.config(width=self.yscrollbarwidth)
        self.canvas = tkinter.Canvas(self)
        self.canvas.parent = self.canvas.master
        """make the canvas inherit these values like a frame"""
        self.canvas['background']=parent['background']
        for attr in ['fonts','theme','debug','wraplength','photo','renderer',
                # 'program',
                'exitFlag']:
            if hasattr(self.canvas.parent,attr):
                setattr(self.canvas,attr,getattr(self.canvas.parent,attr))
        # inherit(self.canvas)
        """create a frame inside the canvas which will be scrolled with it
        Everthing that should scroll should be a child of this frame"""
        self.content = Frame(self.canvas)
        """This is needed for _configure_canvas"""
        self.content_id = self.canvas.create_window(0, 0, window=self.content,
                                           anchor=tkinter.NW)
        self.canvas.config(bd=0) #no border
        self.canvas.config(yscrollcommand=yscrollbar.set)
        if xscroll == True:
            self.canvas.config(xscrollcommand=xscrollbar.set)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        """Make all this show up, and take up all the space in parent"""
        # self.grid(row=0, column=0,sticky='nsew') # should be done outside
        self.canvas.grid(row=0, column=0,sticky='nsew')
        # self.content.grid(row=0, column=0,sticky='nsew')
        """We might want horizonal bars some day? (also above)"""
        if xscroll == True:
            xscrollbar.config(width=self.yscrollbarwidth)
            xscrollbar.config(background=self.theme.background)
            xscrollbar.config(activebackground=self.theme.activebackground)
            xscrollbar.config(troughcolor=self.theme.background)
            xscrollbar.config(command=self.canvas.xview)
        yscrollbar.config(command=self.canvas.yview)
        """Bindings so the mouse wheel works correctly, etc."""
        self.canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbound_to_mousewheel)
        self.canvas.bind('<Destroy>', self._unbound_to_mousewheel)
        # self.canvas.bind('<Configure>', self._configure_canvas) #called by:
        self.content.bind('<Configure>', self._configure_interior)
        self.bind('<Visibility>', self.windowsize)
        # UI.__init__(self)
        # self.dogrid()
class ScrollingButtonFrame(ScrollingFrame,ButtonFrame):
    """This needs to go inside another frame, for accurrate grid placement"""
    def __init__(self,parent,**kwargs):
        # Gridded.__init__(self,**kwargs)
        # Childof.__init__(self,parent)
        optionlist=kwargs.pop('optionlist')
        command=kwargs.pop('command')
        window=kwargs.pop('window',None)
        ScrollingFrame.__init__(self,parent,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        # for kwarg in ['row', 'column']: #done with these
        #     if kwarg in kwargs:
        #         del kwargs[kwarg]
        self.bf=ButtonFrame(parent=self.content,
                            optionlist=optionlist,
                            command=command,
                            window=window,
                            row=0,
                            column=0,
                            **kwargs)
        UI.__init__(self)
        self.dogrid()
class RadioButtonFrame(Frame):
    def __init__(self, parent, horizontal=False,**kwargs):
        # Gridded.__init__(self,**kwargs)
        # Childof.__init__(self,parent)
        for vars in ['var','opts']:
            if (vars not in kwargs):
                print('You need to set {} for radio button frame!').format(vars)
            else:
                setattr(self,vars,kwargs[vars])
                del kwargs[vars] #we don't want this going to the button.
        column=0
        sticky='w'
        # self.parent=parent
        Frame.__init__(self, parent, **kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        # kwargs['background']=self.theme.background
        # kwargs['activebackground']=self.theme.activebackground
        row=0
        for opt in self.opts:
            value=opt[0]
            name=opt[1]
            log.log(3,"Value: {}; name: {}".format(value,name))
            RadioButton(self,variable=self.var, value=value, text=nfc(name),
                                                column=column,
                                                row=row,
                                                sticky=sticky,
                                                indicatoron=0,
                                                **kwargs)
            if horizontal:
                column+=1
            else:
                row+=1
        UI.__init__(self)
        self.dogrid()
class ToolTip(object):
    """
    create a tooltip for a given widget
    modified from https://stackoverflow.com/, originally from
    www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
    Modified to include a delay time by Victor Zaccardo, 25mar16
    """
    def __init__(self, widget, text=_("change this")):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.dispx = 25
        self.dispy = 20
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.widget.bind("<Destroy>", self.hidetip)
        self.id = None
        self.tw = None
    def enter(self, event=None):
        # print('enteringwidget')
        self.event=event
        self.schedule()
    def entertip(self, event=None):
        # print('enteringtip')
        self.dispx=-self.dispx
        self.dispy=-self.dispy
    def leave(self, event=None):
        # print('leavingwidget')
        self.unschedule()
        self.hidetip()
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)
    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)
    def showtip(self, event=None):
        self.widget.unbind("<Leave>")
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        # #based on widgets (flashy):
        # x += self.widget.winfo_rootx() + self.dispx
        # y += self.widget.winfo_rooty() + self.dispy
        #based on mouse click (much better):
        x += self.event.x_root +5 #+ self.dispx
        y += self.event.y_root #+ self.dispy
        # creates a toplevel window
        self.tw = Toplevel(self.widget)
        self.tw.bind("<Enter>", self.entertip)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text, justify='left', font='small',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label['background']="#ffffff"
        label.pack(ipadx=1)
        self.widget.bind("<Leave>", self.leave)
    def hidetip(self, event=None):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
"""Move back to main"""
class Wait(Window): #tkinter.Toplevel?
    def close(self):
        self.update_idletasks()
        if not isinstance(self.parent,Root) and self.parentwasvisible:
            #Don't show a root window, nor one that was hidden before
            self.parent.deiconify()
        self.on_quit()
    def progress(self,value):
        # between 0 and 100
        try:
            self.progressbar.current(value)
        except AttributeError:
            self.progressbar=Progressbar(self.outsideframe,
                                    orient='horizontal',
                                    mode='determinate', #or 'indeterminate'
                                    row=4,column=0)
            self.progress(value)
    def cancel(self):
        self.parent.waitcancel()
        log.info("Sent Wait Cancel")
    def __init__(self, parent, msg=None, cancellable=False):
        super(Wait, self).__init__(parent,exit=False)
        self.paused=False
        self.withdraw() #don't show until we're done making it
        self.parentwasvisible=parent.winfo_viewable()
        parent.withdraw()
        self['background']=parent['background']
        self.attributes("-topmost", True)
        title=(_("Please Wait! {name} Dictionary and Orthography Checker "
                "in Process").format(name=self._root().program['theme'].name))
        self.title(title)
        text=_("Please Wait...")
        self.l=Label(self.outsideframe, text=text,
                font='title',anchor='c',
                row=0,column=0,sticky='we')
        if msg is not None:
            self.l1=Label(self.outsideframe, text=msg,
                font='default',anchor='c',row=1,column=0,sticky='we')
            self.l1.wrap()
        self.l2=Label(self.outsideframe,
                        image=self.theme.photo['small'],
                        text='',
                        row=2,column=0,sticky='we',padx=50,pady=50)
        if cancellable:
            self.cancelbutton=Button(self.outsideframe,text='Cancel',
                                    cmd=self.cancel,
                                    row=3,column=0,sticky='e')
        self.deiconify() #show after the window is built
        #for some reason this has to follow the above, or you get a blank window
        self.update_idletasks() #updates just geometry
"""unclassed functions"""
def now():
    return datetime.datetime.utcnow().isoformat()#[:-7]+'Z'
def availablexy(self,w=None):
    def padstoint(p):
        """Pads can be expressed as integers or (before,after) tuples"""
        if str(p) == '1m':
            return 5
        try:
            r=int(str(p))*2
        except:
            # log.info(p)
            p=tuple(p)
            r=int(p[0])+int(p[-1])
        # log.info("Returning pad {}".format(r))
        return r
    if w is None: #initialize a first run
        w=self
        self.otherrowheight=0
        self.othercolwidth=0
    parentclasses=['Toplevel','Tk','Wait','Window','Root',
                    tkinter.Canvas,
                    'ScrollingFrame']
    if not w.grid_info():
        # (hasattr(w,'parent.parent') and
        # hasattr(w.parent,'parent') and
        # w.parent.parent.winfo_class() == ScrollingFrame):
        return
    try: #Any kind of error making a widget often shows up here
        wrow=w.grid_info()['row']
    except KeyError:
        log.error("Problem with grid on {} widget, with these siblings: {}"
                    "".format(w.winfo_class(),w.parent.winfo_children()))
        raise{}
    wcol=w.grid_info()['column']
    wrowmax=wrow+w.grid_info()['rowspan']
    wcolmax=wcol+w.grid_info()['columnspan']
    wrows=set(range(wrow,wrowmax))
    wcols=set(range(wcol,wcolmax))
    log.log(2,'wrow: {}; wrowmax: {}; wrows: {}; wcol: {}; wcolmax: {}; '
            'wcols: {} ({})'.format(wrow,wrowmax,wrows,wcol,wcolmax,wcols,w))
    rowheight={}
    colwidth={}
    for sib in w.parent.winfo_children(): #one of these should be sufficient
        if (sib.winfo_class() not in parentclasses and
            sib.parent.winfo_class() not in [tkinter.Canvas,'ScrollingFrame']):
            if hasattr(w.parent,'grid_info') and 'row' in sib.grid_info():
                sib.row=sib.grid_info()['row']
                sib.col=sib.grid_info()['column']
                sib.pady=sib.grid_info()['pady']
                sib.padx=sib.grid_info()['padx']
                # These are actual the row/col after the max in span,
                # but this is what we want for range()
                sib.rowmax=sib.row+sib.grid_info()['rowspan']
                sib.colmax=sib.col+sib.grid_info()['columnspan']
                sib.rows=set(range(sib.row,sib.rowmax))
                sib.cols=set(range(sib.col,sib.colmax))
                if wrows & sib.rows == set(): #the empty set
                    sib.reqheight=sib.winfo_reqheight()
                    # log.info("sib {} reqheight: {}".format(sib,sib.reqheight))
                    # log.info("sib {} pady: {}".format(sib,sib.pady))
                    # log.info("sib {} pady: {}".format(sib,padstoint(sib.pady)))
                    """Give me the tallest cell in this row"""
                    if ((sib.row not in rowheight) or (sib.reqheight >
                                                            rowheight[sib.row])):
                        rowheight[sib.row]=sib.reqheight
                        if 'pady' in sib.grid_info():
                            # log.info(rowheight[sib.row])
                            # log.info(sib.reqheight)
                            rowheight[sib.row]+=padstoint(sib.pady)
                            # log.info(rowheight[sib.row])
                if wcols & sib.cols == set(): #the empty set
                    sib.reqwidth=sib.winfo_reqwidth()
                    # log.info("sib {} width: {}".format(sib,sib.reqwidth))
                    # log.info("sib {} padx: {}".format(sib,sib.padx))
                    # log.info("sib {} padx: {}".format(sib,padstoint(sib.padx)))
                    """Give me the widest cell in this column"""
                    if ((sib.col not in colwidth) or (sib.reqwidth >
                                                            colwidth[sib.col])):
                        colwidth[sib.col]=sib.reqwidth
                        if 'padx' in sib.grid_info():
                            # log.info(colwidth[sib.col])
                            # log.info(sib.reqwidth)
                            colwidth[sib.col]+=padstoint(sib.padx)
                            # log.info(colwidth[sib.col])
    for row in rowheight:
        self.otherrowheight+=rowheight[row]
    for col in colwidth:
        self.othercolwidth+=colwidth[col]
    log.log(3,"self.othercolwidth: {}; self.otherrowheight: {}".format(
                self.othercolwidth,self.otherrowheight))
    log.log(3,"w.parent.winfo_class: {}".format(w.parent.winfo_class()))
    if hasattr(w.parent,'grid_info') and w.parent.grid_info():
        # winfo_class() not in parentclasses:
        # if hasattr(w.parent,'grid_info'): #one of these should be sufficient
            availablexy(self,w.parent)
    else:
        """This may not be the right way to do this, but this set of adjustments
        puts the window edge widgets on the edge of the screen. This calculation
        is done on the toplevel widget, after the above recursive function is
        done across all the other widgets (so we just get window decoration)."""
        titlebarHeight = 50 #not working: self.winfo_rooty() - self.winfo_y()
        borderSize= 50 #not working: self.winfo_rootx() - self.winfo_x()
        self.othercolwidth+=borderSize*2
        self.otherrowheight+=titlebarHeight+100
        self.maxheight=self.winfo_screenheight()-self.otherrowheight
        self.maxwidth=self.winfo_screenwidth()-self.othercolwidth #+600
        log.log(2,"self.winfo_rootx(): {}".format(self.winfo_rootx()))
        log.log(2,"self.winfo_x(): {}".format(self.winfo_x()))
        log.log(2,"titlebarHeight: {}".format(titlebarHeight))
        log.log(2,"borderSize: {}".format(borderSize))
    log.log(2,"height: {}; width: {}; self.maxheight: {}; self.maxwidth: {}"
                "".format(
                                self.parent.winfo_screenheight(),
                                self.parent.winfo_screenwidth(),
                                self.maxheight,
                                self.maxwidth))
    log.log(2,"cols: {}".format(colwidth))
    log.log(2,"rows: {}".format(rowheight))
def nfc(x):
    #This makes (pre)composed characters, e.g., vowel and accent in one
    return unicodedata.normalize('NFC', str(x))
def nfd(x):
    #This makes decomposed characters. e.g., vowel + accent (not used yet)
    return unicodedata.normalize('NFD', str(x))
def testapp(program):
    def progress(event):
        import time
        for i in range(101):
            for p in bars:
                if p[1]<2:
                    bars[p].current(100-i)
                else:
                    bars[p].current(i)
            time.sleep(.02)
    def textchange(event):
        l['text']="new text ˥˥˦˦˧"
    def textadd(x):
        l['text']+=str(x)
    r=Root(program=program)
    log.info("root is {}".format(r))
    r.withdraw()
    w=Window(r)
    log.info("window is {}".format(w))
    sf=ScrollingFrame(w.outsideframe,row=0,column=0)
    Label(sf.content,text="Seems to work!",font='title',
            row=0,column=0,
            borderwidth=1,relief='raised')
    l=Label(sf.content,text="At least this much",
            row=1,column=0,
            borderwidth=1,relief='raised')
    # log.info("l dir is {}".format(dir(l)))
    log.info("l _root is {}".format(l._root()))
    log.info("Image dict: {}".format(r.theme.photo))
    # img=r.theme.photo['transparent']
    img=r.theme.photo['NoImage']
    log.info("Image: {} ({})".format(img, Image.maxhw(img)))
    log.info("Image dir: {}".format(dir(img)))
    img.scale(program['scale'],pixels=100,resolution=10)
    log.info("Image: {} ({})".format(img.scaled, Image.maxhw(img,scaled=True)))
    l['image']=img.scaled
    l['compound']="bottom"
    ToolTip(l,"this image has a tooltip")
    for c,cls in enumerate([Message,Label]):
        cname=cls.__name__
        cls(sf.content,text="This is a {} ˥˥˦˦˨".format(cname),row=2, column=c,
                borderwidth=1,relief='raised')
        # cls(w.outsideframe,text="This is a long {}".format(cname),row=3, column=c)
        cls(sf.content,text="This is a very long {}".format(cname),row=4, column=c,
                borderwidth=1,relief='raised')
        cls(sf.content,text="This is a very very long {}".format(cname),
            row=5, column=c,
            borderwidth=1,relief='raised')
        cls(sf.content,text="This is a very very very very long {}"
                    "".format(cname),
                    row=6, column=c,
                    borderwidth=1,relief='raised')
        lll=cls(sf.content,text="This is a very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "long {}".format(cname),row=7, column=c,
                    borderwidth=1,relief='raised')
        if cls == Label:
            # lll['wraplength']=20
            lll.config(wraplength=120)
            # lll.wrap()
    # m=tkinter.Label(sf.content,text="This is a Label", row=3, column=0)
    bars={}
    for orient in ['horizontal','vertical']:
        for row in [0,2]:
            if orient=='horizontal':
                col=1
                colspan=1
                rowspan=1
            else:
                col=row
                row=1
                colspan=1
                rowspan=1
            bars[(orient,row+col)]=Progressbar(w, orient=orient,
                                            mode='determinate',
                                            row=row, column=col,
                                            columnspan=colspan,
                                            rowspan=rowspan,sticky='nesw')
    w.bind('<ButtonRelease-1>',textchange)
    w.bind('<ButtonRelease-1>',progress,add=True)
    w.bind('<Up>',lambda event,x='^':textadd(x),add=True)
    w.bind('<Prior>',lambda event,x='^':textadd(x),add=True) #page up button
    w.bind('<Down>',lambda event,x='v':textadd(x),add=True)
    w.bind('<Next>',lambda event,x='v':textadd(x),add=True) #page down button
    w.bind('<Left>',lambda event,x='<—':textadd(x),add=True)
    w.bind('<Right>',lambda event,x='—>':textadd(x),add=True)
    # parent.winfo_viewable()
    log.info(dir(w))
    log.info(w.bindtags())
    log.info(w.wm_state())
    log.info(w.state())
    # w.withdraw()
    # log.info(w.wm_state())
    # log.info(w.state())
    r.mainloop()
if __name__ == '__main__':
    program={'name':'tkinter UI module',
            'url':'https://github.com/kent-rasmussen/azt',
            'Email':'kent_rasmussen@sil.org',
            'theme':'Kim'
            }
    """To Test:"""
    # loglevel='Debug'
    testapp(program)
