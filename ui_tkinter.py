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
import tkinter.dnd
import file #for image pathnames
from random import randint #for theme selection
import datetime
try: #translation
    _
except NameError:
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
MULTIPLE=tkinter.MULTIPLE
EXTENDED=tkinter.EXTENDED
SINGLE=tkinter.SINGLE
Variable=tkinter.Variable
IntVar=tkinter.IntVar
StringVar=tkinter.StringVar
BooleanVar=tkinter.BooleanVar
"""These classes have no dependencies"""
class Theme(object):
    """docstring for Theme."""
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
                        ('C1','Z alone 1.png'),
                        ('C2','Z alone 2.png'),
                        ('C3','Z alone 3.png'),
                        ('C4','Z alone 4.png'),
                        ('C5','Z alone 5.png'),
                        ('C6','Z alone 6.png'),
                        ('V','A alone clear6.png'),
                        ('V1','A alone 1.png'),
                        ('V2','A alone 2.png'),
                        ('V=','A alone equals.png'),
                        ('V1=V2','A alone 1=2.png'),
                        ('V2=V3','A alone 2=3.png'),
                        ('V3=V4','A alone 3=4.png'),
                        ('V3','A alone 3.png'),
                        ('V4','A alone 4.png'),
                        ('V5','A alone 5.png'),
                        ('V6','A alone 6.png'),
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
                        ('verifyglyphs','Verify Group List.png'),
                        ('sort','Sort List.png'),
                        ('sortglyphs','Sort List Stack Groups.png'),
                        ('join','Join List.png'),
                        ('join_same','Join List same.png'),
                        ('join_different','Join List different.png'),
                        ('joinglyphs','Join Stack Groups.png'),
                        ('joinglyphs_same','Join Stack Groups same.png'),
                        ('joinglyphs_different','Join Stack Groups different.png'),
                        ('record','Microphone alone_sm.png'),
                        ('change','Change Circle_sm.png'),
                        ('checkedbox','checked.png'),
                        ('uncheckedbox','unchecked.png'),
                        ('checkedbox_sm','checked_sm.png'),
                        ('uncheckedbox_sm','unchecked_sm.png'),
                        ('alpha_chart','Alphabet_ChartZ.png'),
                        ('alpha_icon','Alphabet_ChartZ_icon.png'),
                        ('NoImage','toselect/Image-Not-Found.png'),
                        ('Order!','toselect/order!.png'),
                    ]
    def startruntime(self):
        """/home/kentr/bin/raspy/azt/ui_tkinter.py:95: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
        self.start_time=datetime.datetime.utcnow()"""
        self.start_time=datetime.datetime.now(datetime.UTC)
        log.info("starting at {}".format(self.start_time))
    def nowruntime(self): #this returns a delta!
        return datetime.datetime.now(datetime.UTC)-self.start_time
    def logfinished(self,msg=None):
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
        """with PIL.ImageTk, this should probably be largely culled."""
        # Program icon(s) (First should be transparent!)
        scale=self.program['scale'] #just reading this here
        self.scalings=[]
        self.photo={}
        #do these once:
        if scale-1: #x != y: #should be the same as scale != 1
            log.info("Maybe scaling images; please wait...")
            scaledalreadydir=file.fullpathname('images/scaled/'+str(scale)+'/')
            file.makedir(scaledalreadydir) #in case not there
        def mkimg(name,filename):
            imgurl=file.fullpathname(
                            file.getdiredurl('images/',filename))
            # log.info("scale: {}".format(scale))
            # log.info(f"making image {name} ({filename}) with imgurl {imgurl}")
            if scale-1: #x != y:
                scaledalready=file.getdiredurl(scaledalreadydir,filename)
                # log.info("Looking for {}".format(scaledalready))
                if file.exists(scaledalready):
                    # log.info(f"scaled image exists for {filename} ({scaledalready})")
                    imgurl=scaledalready
                else:
                    try:
                        assert self.fakeroot.winfo_exists()
                    except:
                        program=self.program.copy()
                        program['theme']=None
                        self.fakeroot=Root(program, withdrawn=True,
                                            noimagescaling=True)
                        self.fakeroot.wait(msg="Scaling Images (Just this once)")
                    if not self.scalings:
                        maxscaled=100
                    else:
                        maxscaled=int(sum(self.scalings)/len(self.scalings)+10)
                    for y in range(maxscaled,10,-5):
                        """Higher number is better resolution (x*y/y), more
                        time to process. as much as 10>50 High OK, since we do
                        this just once now. Lower this if higher fails
                        due to memory limitations x=int(scale*y)"""
                        # log.info("Scaling {} @{} resolution".format(imgurl,y))
                        try:
                            self.photo[name] = Image(imgurl)
                            # keep these at full size, for now
                            if 'openclipart.org' not in filename:
                                # pixels=self.photo[name].maxhw() #max here only
                                """If this seems to fail inexplicably, check that
                                the image isn't too large (>800x800 pixels)?"""
                                self.photo[name].scale(scale, pixels=0,
                                                        resolution=y)
                                # self.photo[name]=self.photo[name]
                            if scaledalready.parent != scaledalreadydir:
                                file.makedir(scaledalready.parent,silent=True)
                            # log.info(f"writing {name} to {scaledalready}")
                            self.photo[name].scaled_img.save(scaledalready)
                            self.scalings.append(y)
                            if file.exists(scaledalready):
                                log.info("Scaled {} {} @{} resolution: {}"
                                        "".format(name,imgurl,y,_("OK")))
                            # else:
                            #     log.info("Problem Scaling {} {} @{} resolution"
                            #             "".format(name,imgurl,y))
                            return #stop when the first/best works
                        except tkinter.TclError as e:
                            if ('not enough free memory '
                                'for image buffer' in str(e)):
                                continue
                        except Exception as e:
                            log.error(f"Other exception making image at {imgurl} ({e})")
            self.photo[name] = Image(imgurl)
            # log.info("Compiled {} {}".format(name,imgurl))

        ntodo=len(Theme.imagelist)
        self.startruntime()
        for n,(name,filename) in enumerate(Theme.imagelist):
            try:
                #Can't hyperthread here!
                mkimg(name,filename)
            except Exception as e:
                log.info("Image {} ({}) not compiled ({})".format(
                            name,filename,e
                            ))
            try: #self.fakeroot is only there if scaled not found
                self.fakeroot.waitprogress(n*100/ntodo)
            except Exception as e:
                # log.info("Something happened: {}".format(e))
                # raise
                pass
        try:
            self.logfinished("Image compilation")
            self.fakeroot.waitdone() #won't die if not waiting
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
        self.themettk.configure("TProgressbar", #T+class.name
                                troughcolor=self.activebackground,
                                background=self.background,
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
                'normal':tkinter.font.Font(family=charis,
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
                'italic':tkinter.font.Font(family=charis, size=default, slant='italic'),
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
        super().__init__()
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
class Renderer():
    def __init__(self,test=False,**kwargs):
        global pilisactive
        if pilisactive:
            self.isactive=True
        else:
            log.info("Seems like PIL is not installed; inactivating Renderer.")
            self.isactive=False
        self.renderings={}
        self.imagefonts={}
    def gettextsize(self, img, text, font, fspacing):
        l, t, r, b = img.multiline_textbbox((0,0), text, font=font, spacing=fspacing)
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
        black = 'rgb(0, 0, 0)'
        white = 'rgb(255, 255, 255)'
        img = PIL.Image.new("RGBA", (w+xpad, h+ypad), (255, 255, 255,0 )) #alpha
        draw = PIL.ImageDraw.Draw(img)
        draw.multiline_text((0+xpad//2, 0+ypad//4), text,font=font,fill=black,
                                                                align=align)
        self.img = PIL.ImageTk.PhotoImage(img)
class Childof():
    def pre_tk_init(self,**kwargs):
        try:
            kwargs=super().pre_tk_init(**kwargs)
        finally:
            return kwargs
    def post_tk_init(self):
        try:
            super().post_tk_init()
        except:
            pass
    def inherit(self,parent=None,attr=None):
        """This function brings these attributes from the parent, to inherit
        from the root window, through all windows, frames, and scrolling frames, etc
        """
        if not parent and hasattr(self,'parent') and self.parent:
            parent=self.parent
        elif parent:
            self.parent=parent
        if not attr:
            attrs=['theme',
                    'wraplength',
                    'renderer',
                    'exitFlag']
        else:
            attrs=[attr]
        for attr in attrs:
            if hasattr(parent,attr):
                setattr(self,attr,getattr(parent,attr))
                # log.info(f"inheriting {attr} from parent {type(parent)} "
                #         f"(to {type(self)})")
            # else:
            #     log.info(f"parent {type(parent)} (of {type(self)}) doesn't "
            #             f"have attr {attr}, skipping inheritance")
    def __init__(self, parent, *args, **kwargs): #because this is used everywhere.
        self.parent=parent
        self.inherit()
        super().__init__(*args, **kwargs)
class Gridded():
    gridkwargs={'sticky',
                        'row','rowspan',
                        'column','columnspan','colspan',
                        'r','c','col',
                        'padx','pady','ipadx','ipady',
                        'gridwait','draggable','droppable'
                    }
    gridkwargs_for_child_buttons={'b'+i for i in gridkwargs}
    def pre_tk_init(self,**kwargs):
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self):
        self.dogrid()
        super().post_tk_init()
    def dogrid(self):
        if self._grid:
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
            self.grid_remove()
            if self.gridwait: #just skip the first one
                self.gridwait=False
                return
            self.grid()
        if self.draggable:
            self.draggable_bindings()
        if self.draggable or self.droppable:
            self.dnd_bindings()
    def bindchildren(self,bind,command):
        self.bind(bind,command)
        for child in self.winfo_children():
            try:
                child.bindchildren(bind,command)
            except Exception as e:
                log.info("Exception in Gridded binding: {}".format(e))
                pass
    """The following are for draggable widgets"""
    def draggable_bindings(self):
        self.bind("<ButtonPress-1>", self.on_drag_start)
        self.bind("<Enter>", self.dnd_focus_on)
        self.bind("<Leave>", self.dnd_focus_off)
    def dnd_bindings(self):
        self.initial_widget=False
    def on_drag_start(self,event):
        """Stores the widget and initial position when dragging starts."""
        event.widget.pointer_startX = event.x
        event.widget.pointer_startY = event.y
        event.widget.startX = event.widget.winfo_x()
        event.widget.startY = event.widget.winfo_y()
        tkinter.dnd.dnd_start(self,event)
        event.widget.initial_widget=True
        event.widget.dnd_focus_on()
    def on_drag_motion(self,event):
        """Not in use; compare with dnd_motion"""
        """Moves the widget to the new position while dragging."""
        widget=event.widget._root()._DndHandler__dnd.initial_widget
        try:
            x = event.widget.winfo_x() + (event.x - widget.pointer_startX)
            y = event.widget.winfo_y() + (event.y - widget.pointer_startY)
            widget.place(x=x, y=y)
        except Exception as e:
            log.info(f"{e}: {[i['text'].split('\n')[0]
                                        for i in (widget,event.widget)]}")
        event.widget._root()._DndHandler__dnd.initial_widget.on_motion(event)
    def dnd_end(self, target, event):
        self.initial_widget=False
        if target and hasattr(target,'dnd_focus_off'):
            target.dnd_focus_off()
        self.dnd_focus_off()
    def dnd_putback(self,target, event):
        if target:
            target.dnd_leave(self, event)
        event.widget.grid()
    """The following are for droppable widgets (which can be dropped upon)"""
    def dnd_accept(self, source, event):
        if self.droppable:
            return self
    def dnd_focus_on(self,event=None):
        if self.initial_widget:
            self['highlightbackground']='black'
            self['highlightthickness']=1
        self['background']=self.theme.activebackground
    def dnd_focus_off(self,event=None):
        self['background']=self.theme.background
        self['highlightthickness']=0
    def dnd_enter(self, source, event):
        self.dnd_focus_on()
    def dnd_motion(self, source, event):
        """For whatever reason, this can move with the widget UNDER other
        widgets, or it will block those widgets from becoming targets, neither
        of which work for me"""
        return
        x = event.widget.winfo_x() + (event.x - widget.pointer_startX)
        y = event.widget.winfo_y() + (event.y - widget.pointer_startY)
        widget.place(x=x, y=y)
        event.widget.update_idletasks()
    def dnd_leave(self, source, event):
        if not self.initial_widget:
            self.dnd_focus_off()
    def dnd_commit(self, source, event):
        """I may need to sort out how this and dnd_end relate"""
        try:
            super().dnd_commit(source, event)
        except:
            source.dnd_putback(self, event)
            # log.info(f"Drag and Drop landed on {self} ({type(self)})")
            # try:
            #     print("Target Text:",self.text)
            # except:
            #     print(f"no target Text ({self}; source: {source.text})")
    def __init__(self, *args, **kwargs):
        """this removes gridding kwargs from the widget calls"""
        self._grid=False
        if bool(set(kwargs) & (self.gridkwargs)):
            self._grid=True
            self.sticky=kwargs.pop('sticky',"ew")
            self.row=kwargs.pop('row',kwargs.pop('r',0))
            self.column=kwargs.pop('column',kwargs.pop('col',kwargs.pop('c',0)))
            self.columnspan=kwargs.pop('columnspan',kwargs.pop('colspan',1))
            self.rowspan=kwargs.pop('rowspan',1)
            self.padx=kwargs.pop('padx',0)
            self.pady=kwargs.pop('pady',0)
            self.ipadx=kwargs.pop('ipadx',0)
            self.ipady=kwargs.pop('ipady',0)
            self.gridwait=kwargs.pop('gridwait',False)
        self.draggable=kwargs.pop('draggable',False)
        self.droppable=kwargs.pop('droppable',False)
        self.super_kwargs=kwargs #whenever we make a change
        super().__init__(*args, **kwargs)
class GridinGridded(Gridded):
    def pre_tk_init(self,**kwargs):
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self):
        super().post_tk_init()
    def remove_gridbkwargs(self,**kwargs):
        return {k:v for k,v in kwargs.items()
                    if k not in Gridded.gridkwargs_for_child_buttons}
    def promotegridbkwargs(self,**kwargs):
        """For grid kwargs that were passed down from a parent, now make them
        available to the child, typically a button"""
        return {opt[1:] if opt in Gridded.gridkwargs_for_child_buttons else opt
                :kwargs[opt] for opt in kwargs}
    def __init__(self, *args, **kwargs):
        self.super_kwargs=kwargs #whenever we make a change
        super().__init__(*args, **self.promotegridbkwargs(**kwargs))
class UI():
    """docstring for UI, after tkinter widgets are initted."""
    backgrounds=['background','bg','troughcolor']
    pads=['ipady','ipadx','pady','padx']
    active_color=['activebackground','selectcolor','highlightcolor']
    def pre_tk_init(self,**kwargs):
        return kwargs
    def post_tk_init(self):
        """Here we want to use explicit values where present; otherwise the
        theme value"""
        for a in self.backgrounds:
            if a in self.keys(): #only set where appropriate
                self[a]=getattr(self,'background',self.theme.background)
        for a in self.pads:
            if a in self.keys() and hasattr(self.theme,a):
                self[a]=getattr(self,a,getattr(self.theme,a))
        for a in self.active_color:
            if a in self.keys():
                self[a]=getattr(self,'activebackground',
                                self.theme.activebackground)
        if self.withdrawn:
            self.withdraw()
    def __init__(self, *args, **kwargs):
        """This is always the last of my methods, after which tkinter is called.
        because of this, we need to restore the parent so tkinter can see it"""
        for k in self.backgrounds+self.pads+self.active_color:
            try:
                setattr(self,k,kwargs.pop(k))
            except:
                pass
        self.withdrawn=kwargs.pop("withdrawn",True if isinstance(self,Root)
                                                    else False)
        kwargs=self.pre_tk_init(**kwargs)
        if self.parent:
            super().__init__(self.parent, *args, **kwargs)
        else: #Don't send for Root
            super().__init__(*args, **kwargs)
        self.post_tk_init()
        self.waitcancelled=False
class Exitable():
    """This class provides the method and init to make things exit normally.
    Hence, it applies to roots and windows, but not frames, etc."""
    def pre_tk_init(self,**kwargs):
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self):
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        super().post_tk_init()
    def killall(self):
        self.destroy()
        sys.exit()
    def cleanup(self):
        pass
    def exittoroot(self):
        """This is just for toplevel windows — Root and Toplevel(Windows).
        It doesn't actually kill anything, just marks the windows as exiting,
        so functions can check the flag and exit nicely."""
        if self.parent: #Toplevel
            self.parent.exittoroot()
            return
        else: #Root
            self.parent.exitFlag.true()
    def on_quit(self,to_root=False):
        """Do this when a window closes, so any window functions can know
        to just stop, rather than trying to build graphic components and
        throwing an error. This doesn't do anything but set the flag value
        on exit, the logic to stop needs to be elsewhere, e.g.,
        `if self.exitFlag.istrue(): return`"""
        # log.info(f"Quitting window {self}")
        self.exitFlag.true()
        if (to_root or self.mainwindow) and self.parent:
            self.parent.on_quit(to_root=True)
        elif isinstance(self,Root): #exit afterwards if main window
            self.killall()
        else:
            if (self.parent and
                self.parent.winfo_exists() and
                not isinstance(self.parent,Root)):
                if not self.parent.iswaiting():
                    self.parent.deiconify()
            self.cleanup()
            self.destroy() #do this for everything
    def __init__(self, *args, **kwargs):
        self.exitFlag = ExitFlag()
        super().__init__(*args, **kwargs)
class Waitable(Exitable):
    """docstring for Waitable."""
    def wait(self,msg=None,cancellable=False,thenshow=False):
        if self.iswaiting():
            # log.debug("There is already a wait window: {}".format(self.ww))
            if msg:
                self.ww.msg(msg) #update msg, even if not new wait window
            if cancellable:
                self.ww.make_cancellable()
            if thenshow:
                self.showafterwait=True
            return
        log.info(f"updating wait: {self.winfo_viewable()|thenshow=} "
                f"{self.winfo_viewable()=} {thenshow=} ")
        self.showafterwait=self.winfo_viewable()|thenshow
        if self.showafterwait:
            self.withdraw()
        self.ww=Wait(self,msg,cancellable=cancellable)
    def iswaiting(self):
        return hasattr(self,'ww') and self.ww.winfo_exists()
    def waitpause(self):
        self.ww.withdraw()
        self.ww.paused=True
    def waitunpause(self):
        self.ww.deiconify()
        self.ww.paused=False
    def waitprogress(self,x):
        # log.info(f"updating wait to {x}")
        try:
            self.ww.progress(x,r=4)
        except Exception as e:
            log.info(f"Couldn't change wait progress ({e})")
    def waitcancel(self):
        self.waitcancelled=True
        log.info("Wait cancel registered; waiting to cancel")
    def waitdone(self):
        try:
            self.ww.close()
        except (tkinter.TclError,AttributeError) as e:
            # pass
        # except AttributeError:
            log.info(f"{self} seems to have tried stopping waiting? {e}")
        finally:
            if not self.exitFlag.istrue():
                if self.showafterwait:
                    # log.info(f"Prepping show after wait {self.state()=}")
                    # self.state('withdrawn')
                    # log.info(f"Showing after wait {self.state()=}")
                    r=self.update()
                    rr=self.deiconify()
                    # log.info(f"Showed after wait {self.state()=} {r=} {rr=}")
                # else:
                #     log.info(f"Not showing after wait {self.state()=}")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.showafterwait=True #in case never waited, do this anyway
class Image(): #PIL.ImageTk.PhotoImage is for display
    def biggerby(self,x):
        #always do this one first, if doing both, to start from scratch
        try:
            self.scaled=self.transparency.zoom(x,x)
        except AttributeError:
            self.scaled=self.zoom(x,x)
        # except Exception as e:
        #     log.info(f"Exception in biggerby: {e}")
    def smallerby(self,x):
        # transparency is managed in biggerby
        try:
            self.scaled=self.scaled.subsample(x,x)
        except AttributeError:
            self.scaled=self.subsample(x,x)
        # except Exception as e:
        #     log.info(f"Exception in smallerby: {e}")
    def maxhw(self,scaled=False):
        if scaled:
            return max(self.scaled_img.width,self.scaled_img.height)
        else:
            return max(self.base_img.width,self.base_img.height)
    def scale_height(self,scale,pixels=100,resolution=5):
        self.scale(scale,pixels=100,resolution=resolution,scaleto='height')
    def scale_width(self,scale,pixels=100,resolution=5):
        self.scale(scale,pixels=100,resolution=resolution,scaleto='width')
    def compile(self):
        self.scaled=PIL.ImageTk.PhotoImage(getattr(self,'scaled_img',
                                                self.base_img)) #scaled or not
    def scale(self,scale,pixels=100,resolution=5,scaleto='both'):
        """'resolution*r' and 'resolution' here express a float scaling ratio
        as two integers, so r = 0.7 = 7/10, because the zoom and subsample fns
        only work on integers. To not waste computation, resolution starts
        small and increases to what is needed to keep both integers positive"""
        # def r_off_by(): #how far off does this integer division push this?
        #     return abs(r-(int(resolution*r)/int(resolution)))/r
        # log.info("Scaling with these args: scale {}, pixels {}, resolution {}"
        #         "".format(scale,pixels,resolution))
        if pixels:
            s=pixels*scale #the number of pixels, scaled
            if scaleto == 'both':
                standard=self.maxhw()
            elif scaleto == 'height':
                standard=self.base_img.height
            elif scaleto == 'width':
                standard=self.base_img.width
            r=s/standard #the ratio we need to reduce actual pixels by
        else:
            r=scale #keep aspect, just scale for screen
        # if not r:
        #     r=1 #don't scale for pixels=r=0
        # int(resolution*r) must be >=1 (True) for biggerby
        # r_off_by is precision
        # If the resolution gets too high, we run out of memory...
        # while (not int(resolution*r) or r_off_by() > .02) and resolution < 100:
        #     resolution=resolution*2
        aspect=(int(self.base_img.width*r), int(self.base_img.height*r))
        self.scaled_img=self.base_img.resize(aspect)
        # log.info(f"{self.base_img.height=}")
        # log.info(f"{self.base_img.width=}")
        # log.info(f"{self.scaled_img.height=}")
        # log.info(f"{self.scaled_img.width=}")
        self.compile()
        # self.biggerby(int(resolution*r))
        # self.smallerby(int(resolution))
        # self.crop_to_exact_scale(scaleto,s)
        return self.scaled # for where needed
    def crop_to_exact_scale(self,scaleto,scaled_pixels):
        """center crop, should be minor, just for display"""
        left=upper=0 #make sure everything is defined
        right=w = self.scaled.width()
        lower=h = self.scaled.height()
        if scaleto in ['height','both']:
            upper=(h-scaled_pixels)//2
            lower=upper+scaled_pixels #avoid rounding errors
        if scaleto in ['width','both']:
            left=(w-scaled_pixels)//2
            right=left+scaled_pixels
        self.scaled.crop([ left, upper, right, lower])
    def transparent(self):
        log.info("Running transparent")
        return
        tkinter.PhotoImage(file=self.filename)
        self.transparency=tkinter.PhotoImage(file=self.filename)
        log.info(f"self.transparency type: {type(self.transparency)}")
        log.info(f"self.transparency width: {self.transparency.width()}")
        log.info(f"self.transparency height: {self.transparency.height()}")
        for x in range(self.transparency.width()):
            for y in range(self.transparency.height()):
                if self.transparency.get(x,y) == (255,255,255):
                    self.transparency.put(x,y) == (0,0,0)
                # log.info(f"{x},{y} pixel: {self.transparency.get(x,y)}")
        return
        newData = []
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                # replacing it with a transparent value
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        self.transparency.putdata(newData)
        return self.transparency
    def __init__(self,filename):
        """This class uses three different images:
        self.base_img: the original image as loaded from file (PIL.Image.Image)
        self.scaled_img: the image as modified for use (PIL.Image.Image)
        self.scaled: the version to display in tkinter (PIL.ImageTk.PhotoImage)
        we keep these because the same image may be scaled differently for
        different uses.
        """
        self.filename=filename
        with PIL.Image.open(filename) as self.base_img:
            self.base_img.load()
        # try:
        #     PIL.ImageTk.PhotoImage.__init__(self.base_img)
        # except tkinter.TclError as e:
        #     if "couldn't recognize data in image file" in e.args[0]:
        #         raise #this is processed elsewhere
        #     elif 'value for "-file" missing' in e.args[0]:
        #         raise #this is processed elsewhere
        #     else:
        #         log.info("Image error: {}".format(e))
        self.compile()
"""below here has UI"""
class Root(Waitable,UI,tkinter.Tk):
    """this is the root of the tkinter GUI."""
    def post_tk_init(self,**kwargs):
        """This needs Tk to be instantiated already, but must precede UI
        application"""
        try:
            assert not self.noimagescaling #otherwise, make copy theme
            assert isinstance(self.program['theme'],Theme) #use what's there
            self.theme=self.program['theme']
        except (KeyError,AssertionError) as e:
            log.info(f"Theme error: {e}")
            self.theme=Theme(self.program,
                            **{**kwargs,'noimagescaling':self.noimagescaling})
        super().post_tk_init()
    def __init__(self, program={}, *args, **kwargs):
        """specify theme name in program['theme']
        bring in program here, send it to theme, everyone accesses scale
        from there.
        Some roots aren't THE root, e.g., contextmenu.
        Furthermore, I'm currently not showing the root, so the user will
        never exit it --though this is managed in UI.
        """
        # log.info("Root called with program dict {}".format(program))
        self.program=program
        self.parent=None
        if 'root' not in self.program:
            self.program['root']=self
        self.mainwindow=False
        self.noimagescaling=kwargs.pop('noimagescaling',False)
        super().__init__(*args, **kwargs)
        self.post_tk_init(**kwargs) #Theme needs Tk to exist by now
        self.renderer=Renderer()
        # log.info("Root initialized")
"""These have parent (Childof), but no grid"""
class Toplevel(Childof,Waitable,UI,tkinter.Toplevel): #
    """This and all Childof classes should have a parent, to inherit a common
    theme. Otherwise, colors, fonts, and icons will be incongruous."""
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, parent, *args, **kwargs):
        self.mainwindow=False
        super().__init__(parent, *args, **kwargs)
        self.post_tk_init()
class Menu(Childof,tkinter.Menu): #not Text
    def post_tk_init(self):
        # log.info("Running Menu post_tk_init")
        self['background']=self.theme.menubackground
        super().post_tk_init()
    def pad(self,label):
        w=5 #Make menus at least w characters wide
        if len(label) <w:
            spaces=" "*(w-len(label))
            label=spaces+label+spaces
        return label
    def add_command(self,label,command):
        label=self.pad(label)
        tkinter.Menu.add_command(self,label=label,command=command)
    def insert_cascade(self,label,menu,index):
        label=self.pad(label)
        tkinter.Menu.insert_cascade(self,label=label,menu=menu,index=index)
    def add_cascade(self,label,menu):
        label=self.pad(label)
        tkinter.Menu.add_cascade(self,label=label,menu=menu)
    def __init__(self,parent,**kwargs):
        kwargs['font']=kwargs.get('font','default')
        super().__init__(parent,**kwargs)
        self.post_tk_init()
class Progressbar(Childof,Gridded,UI,tkinter.ttk.Progressbar):
    def post_tk_init(self):
        super().post_tk_init()
    def current(self,value):
        if type(value) is not int and 0 <= value <= 1:
            value=int(value*100)
        if 0 <= value <= 100:
            self['value']=value
        # self.update_idletasks() #updates just geometry
    def __init__(self, parent, *args, **kwargs):
        if 'orient' not in kwargs:
            kwargs['orient']='horizontal' #or 'vertical'
        if 'mode' not in kwargs:
            kwargs['mode']='determinate' #or 'indeterminate'
        super().__init__(parent, *args, **kwargs)
        self.post_tk_init()
class TextBase():
    """no image for Message, ComboBox, EntryField, RadioButton, ListBox """
    textkwargs={'text','textvariable','font'}
    tk_textkwargs=textkwargs #all OK for Tk
    def reserve_kwargs(self,**kwargs):
        """This method pulls kwargs out of the kwarg dict when this class is
        not a subclass of the instantiated class (e.g. Button is not a subclass
        of ButtonFrame), to keep those kwargs out of the way
        of super()__init__().
        Because of this, it should pull out all kwargs reserved for this class
        and its subclasses.
        """
        for k in set(kwargs)&TextBase.textkwargs: #any kwarg used on TextBase
            if hasattr(self,k) and getattr(self,k) != kwargs[k]:
                log.info(f"TextBase attr found! {k}:{getattr(self,k)}")
                exit() #this should never happen
            setattr(self,k,kwargs.pop(k))
        return kwargs
    def restore_kwargs(self,**kwargs):
        """This restores kwargs needed for the tkinter classes"""
        for k in TextBase.textkwargs: #all, not just those OK for Tk
            if hasattr(self,k):
                kwargs[k]=getattr(self,k)
        return kwargs
    def my_tk_kwargs(self,**kwargs):
        return {k:v for k,v in kwargs.items()
                if k not in TextBase.textkwargs or k in TextBase.tk_textkwargs
                }
    def pre_tk_init(self,**kwargs):
        """This is called at UI init, just before tkinter """
        kwargs=TextBase.restore_kwargs(self,**kwargs) #add back to kwargs
        kwargs=TextBase.my_tk_kwargs(self,**kwargs) #then limit
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self,**kwargs):
        super().post_tk_init(**kwargs)
    def __init__(self,*args,**kwargs):
        kwargs=TextBase.restore_kwargs(self,**kwargs)
        t=self.textvariable=self.text='' #clear now, not all labels/buttons use
        self.text=kwargs.pop('text','')
        tv=kwargs.get('textvariable',None)
        for i in [self.text, tv]:
            if i and isinstance(i, tkinter.Variable):
                self.textvariable=i
                self.text=''
                # log.info(f"{self.textvariable.__class__} {self.textvariable.get()=}")
                break
        self.text=nfc(self.text) #ok empty
        # log.info(f"TextBase found {self.textvariable} ({self.textvariable.__class__}) "
        #             f"{self.text} ({self.text.__class__})")
        self.anchor=kwargs.pop('anchor',"w")
        if 'font' in kwargs:
            if isinstance(kwargs['font'],tkinter.font.Font):
                self.font=kwargs['font']
            elif kwargs['font'] in self.theme.fonts: #if font key (e.g., 'small')
                self.font=self.theme.fonts[kwargs['font']] #change key to font
            else:
                log.error("Unknown font specification: {}".format(kwargs['font']))
            del kwargs['font']
        else:
            self.font=self.theme.fonts['default']
        self.super_kwargs=kwargs
        super().__init__(*args,**kwargs)
class Text(TextBase):
    """This converts kwargs 'text', 'image' and 'font' into attributes which are
    default where not specified, and rendered where appropriate for the
    characters in the text. tk_textkwargs are passed back for tkinter"""
    # tk_textkwargs=TextBase.tk_textkwargs|{'image','compound','wraplength'}
    # textkwargs=TextBase.textkwargs|tk_textkwargs|{'norender'}
    tk_textkwargs={'image','compound','wraplength'}
    textkwargs=TextBase.textkwargs|tk_textkwargs|{'norender','image_pixels',
                                                'image_scaleto'}
    d=set(["̀","́","̂","̌","̄","̃", "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉"])
    sticks=set(['˥','˦','˧','˨','˩',' '])
    def reserve_kwargs(self,**kwargs):
        """This method pulls kwargs out of the kwarg dict when this class is
        not a subclass of the instantiated class (e.g. Button is not a subclass
        of ButtonFrame), to keep those kwargs out of the way
        of super()__init__().
        Because of this, it should pull out all kwargs reserved for this class
        and its subclasses.
        """
        kwargs=TextBase.reserve_kwargs(self,**kwargs)
        # log.info(f"reserve_kwargs: {kwargs}")
        for k in set(kwargs)&Text.tk_textkwargs: #any kwarg used on text
            if hasattr(self,k) and getattr(self,k) != kwargs[k]:
                log.info(f"Text attr found! {k}:{getattr(self,k)}")
                exit() #this should never happen
            setattr(self,k,kwargs.pop(k))
        return kwargs
    def restore_kwargs(self,**kwargs):
        """This restores kwargs needed for the tkinter classes"""
        kwargs=TextBase.restore_kwargs(self,**kwargs)
        # log.info(f"restore_kwargs: {kwargs}")
        for k in Text.textkwargs: #all, not just those OK for Tk
            if hasattr(self,k):
                kwargs[k]=getattr(self,k)
        return kwargs
    def my_tk_kwargs(self,**kwargs):
        kwargs=TextBase.my_tk_kwargs(self,**kwargs)
        # log.info(f"my_tk_kwargs: {kwargs}")
        return {k:v for k,v in kwargs.items()
                if k not in Text.textkwargs or k in Text.tk_textkwargs
                }
    def pre_tk_init(self,**kwargs):
        """This restores kwargs needed for the tkinter classes"""
        if (hasattr(self.text, '__iter__')
                    and set(self.text) & (Text.sticks|Text.d)
                    and not self.norender):
            self.render(**{k:v for k,v in kwargs.items()
                                        if k not in self.textkwargs})
        kwargs=Text.restore_kwargs(self,**kwargs) #add back to kwargs
        kwargs=Text.my_tk_kwargs(self,**kwargs) #then limit
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self,**kwargs):
        super().post_tk_init(**kwargs)
        i=self.grid_info()
        if i and self.text:
            self.wrap()
    def wrap(self):
        availablexy(self)
        if not hasattr(self,'wraplength'):
            wraplength=self.maxwidth
        else:
            wraplength=min(self.wraplength,self.maxwidth)
        self.config(wraplength=wraplength)
    def render(self, **kwargs):
        # log.info(f"Calling render {kwargs=}")
        if not self.renderer.isactive:
            # log.info("Aborting render (inactive)")
            return
        try:
            text=kwargs.get('textvariable',self.textvariable).get()
        except:
            text=self.text
        style=(self.font['family'],
                self.font['size'],self.font['weight'],
                self.font['slant'],self.font['underline'],
                self.font['overstrike'])
        if style not in self.renderer.renderings:
            self.renderer.renderings[style]={}
        if self.wraplength not in self.renderer.renderings[style]:
            self.renderer.renderings[style][self.wraplength]={}
        thisrenderings=self.renderer.renderings[style][self.wraplength]
        if (text in thisrenderings and thisrenderings[text] is not None):
            self.image=thisrenderings[text]
            self.text=''
        elif self.image and self.image not in thisrenderings.values():
            log.error("You gave an image and tone characters in the same "
                        f"label? ({self.image},{text})")
            return
        else:
            self.renderer.render(
                        text=text,
                        font=self.font,
                        wraplength=self.wraplength,
                        **kwargs)
            self.tkimg=self.renderer.img
            if self.tkimg is not None:
                thisrenderings[text]=self.image=self.tkimg
                self.text=''
    def __init__(self,*args,**kwargs):
        kwargs=Text.restore_kwargs(self,**kwargs)
        self.wraplength=kwargs.pop('wraplength', getattr(self,'wraplength',0))
        if isinstance(self.wraplength, str) and '%' in self.wraplength:
            percent=float(self.wraplength.strip('%'))/100
            self.wraplength=self.parent.winfo_screenwidth()*percent
        for reste in ['norender', 'image_pixels', 'image_scaleto']:
            setattr(self,reste,kwargs.pop(reste,False))
        self.image=kwargs.pop('image',None) #pull image by name:
        if isinstance(self.image,str) and self.image in self.theme.photo:
            self.image=self.theme.photo[self.image]
        if self.image_pixels:
            img_kwargs={'pixels':self.image_pixels}
            if (self.image_scaleto and
                self.image_scaleto in ['both','height','width']):
                img_kwargs['scaleto']=self.image_scaleto
            self.image=self.image.scale(
                        self.theme.program['scale'], #obligatory, non-kwarg
                        **img_kwargs
                        ) #tk ready
        elif isinstance(self.image,Image):
            self.image=self.image.scaled #tk ready
        elif isinstance(self.image,PIL.ImageTk.PhotoImage):
            name=[k for k,v in self.theme.photo.items()
                    if self.image in [v,v.scaled]]
            log.error(f"Found precompiled {self.image=} ({name}); OK?!")
        elif self.image:
            log.error(f"Found {self.image=} of type {type(self.image)}!")
        self.compound=kwargs.pop('compound','left')
        self.super_kwargs=kwargs
        super().__init__(*args,**kwargs)
"""These have parent (Childof) and grid (Gridded)"""
class Frame(Childof,Gridded,UI,tkinter.Frame):
    def post_tk_init(self):
        super().post_tk_init()
    def iswaiting(self):
        return self.parent.iswaiting()
    def deiconify(self):
        return self.parent.deiconify()
    def ncolumns(self):
        return self.grid_size()[0]
    def nrows(self):
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
    def __init__(self, parent, *args, **kwargs):
        # log.info("Initializing Frame object")
        if kwargs.get('border'):
            kwargs['highlightbackground']='black'
            kwargs['highlightthickness']=int(kwargs.pop('border'))
        super().__init__(parent, *args, **kwargs)
        """This class is subclassed a lot; make sure the parent class methods
        are used, if there."""
        if self.__class__.__mro__[0] is Frame:
            self.post_tk_init()
        else:
            super().post_tk_init()
class Label(Childof,Gridded,Text,UI,tkinter.Label):
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.post_tk_init()
class Message(Childof,Gridded,TextBase,UI,tkinter.Message):
    """I'm not sure if this will ever have value, but here it is."""
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.post_tk_init()
class Button(Childof,GridinGridded,Text,UI,tkinter.Button):
    tk_buttons={'command'}
    buttons=Gridded.gridkwargs_for_child_buttons|Text.textkwargs|tk_buttons|{
                                                    'cmd', 'window', 'choice'}
    def reserve_kwargs(self,**kwargs):
        """This method pulls kwargs out of the kwarg dict when this class is
        not a subclass of the instantiated class (e.g. Button is not a subclass
        of ButtonFrame), to keep those kwargs out of the way
        of super()__init__().
        Because of this, it should pull out all kwargs reserved for this class
        and its subclasses.
        """
        for k in set(kwargs)&Button.buttons: #any kwarg used on buttons
            if hasattr(self,k) and getattr(self,k) != kwargs[k]:
                log.info(f"Button attr already! {k}:{getattr(self,k)}")
                exit() #this should never happen
            setattr(self,k,kwargs.pop(k))
        kwargs=Text.reserve_kwargs(self,**kwargs)
        return kwargs
    def restore_kwargs(self,**kwargs):
        """This method restores kwargs which have been reserved, so that a
        second level of super().__init__() can access them, e.g., for a Button
        or ButtonFrame called inside the init of a ButtonFrame or
        ScrollingButtonFrame.
        Because of this, it should restore all kwargs needed for it and
        its subclasses.
        """
        for k in Button.buttons: #all, not just those OK for Tk
            if hasattr(self,k):
                # log.info(f"Button restore_kwargs found {k}:{getattr(self,k)}")
                kwargs[k]=getattr(self,k)
        kwargs=Text.restore_kwargs(self,**kwargs)
        return kwargs
    def my_tk_kwargs(self,**kwargs):
        kwargs=Text.my_tk_kwargs(self,**kwargs)
        return {k:v for k,v in kwargs.items()
                if k not in Button.buttons or k in Button.tk_buttons
                }
    def build_command(self):
        """x= as a lambda argument allows us to assign the
        variable value now (in the loop across choices). Otherwise, it will
        maintain a link to the variable itself, and give the last value it
        had to all the buttons... --not what we want!
        """
        if hasattr(self,'command'):
            command=self.command #this needs to refer to this value, not future...
            if self.command:
                if hasattr(self,'choice') and hasattr(self,'window'):
                    cmd=lambda x=self.choice, w=self.window:command(x,window=w)
                elif hasattr(self,'choice'):
                    cmd=lambda x=self.choice:command(x)
                else:
                    cmd=command
            else:
                log.error(f"Not sure what to do to make command ({vars(self)=})")
                cmd=None
        else:
            cmd=None
        self.command=getattr(self,'cmd',cmd) #in case a value was provided earlier
    def pre_tk_init(self,**kwargs):
        """This restores kwargs needed for the tkinter classes, notably
        excluding those used for building my subclassing of them."""
        self.build_command() #doesn't need kwargs
        kwargs=Button.restore_kwargs(self,**kwargs) #add back to kwargs
        kwargs=Button.my_tk_kwargs(self,**kwargs) #then limit
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self):
        super().post_tk_init()
    def nofn(self):
        pass
    def __init__(self, parent, **kwargs):
        kwargs=Button.restore_kwargs(self,**kwargs)
        kwargs=self.reserve_kwargs(**kwargs)
        super().__init__(parent, **kwargs)
        self.post_tk_init()
class EntryField(Childof,Gridded,TextBase,UI,tkinter.Entry):
    def post_tk_init(self):
        if self.render is True:
            # log.info("Preparing to render EntryField")
            self.bind('<KeyRelease>', self.renderlabel)
            self.rendered=Label(self.parent,text='') #make a place only
        super().post_tk_init()
        if hasattr(self,'textvariable'): #For some reason, this isn't already assigned...
            self['textvariable']=self.textvariable
    def renderlabel(self,grid=False,event=None):
        if (Text.d|Text.sticks) & set(self.get()):
            self.rendered.render(textvariable=self.textvariable)
            self.rendered['image']=self.rendered.image
            self.rendered.grid()
        else:
            self.rendered.grid_remove()
    def __init__(self, parent, *args, **kwargs):
        kwargs=TextBase.reserve_kwargs(self,**kwargs)
        # kwargs=self.reserve_kwargs(**kwargs)
        self.render=kwargs.pop('render',False)
        # Always use a variable for this class, even if not passed one:
        kwargs['textvariable']=kwargs.get('textvariable',StringVar())
        kwargs['background']=kwargs.get('background',parent.theme.white)
        super().__init__(parent, *args, **kwargs)
        super().post_tk_init()
class RadioButton(Childof,Gridded,TextBase,UI,tkinter.Radiobutton):
    rb_kwargs={'variable','indicatoron'}
    def reserve_kwargs(self,**kwargs):
        for k in set(kwargs)&RadioButton.rb_kwargs: #any kwarg used on buttons
            if hasattr(self,k):
                log.info(f"RadioButton attr already! {k}:{getattr(self,k)}")
                exit() #this should never happen
            log.info(f"RadioButton reserving {k}:{kwargs[k]}")
            setattr(self,k,kwargs.pop(k))
        return kwargs
    def restore_kwargs(self,**kwargs):
        for k in RadioButton.rb_kwargs: #just those OK for Tk
            if hasattr(self,k):
                kwargs[k]=getattr(self,k)
        return kwargs
    def pre_tk_init(self,**kwargs):
        kwargs=self.restore_kwargs(**kwargs)
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        super().post_tk_init()
class CheckButton(Childof,Gridded,Text,UI,tkinter.Checkbutton):
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, parent, *args, **kwargs):
        """If no values are passed for image and selectimage, default checkboxes
        will be used. If you don't want that, pass None.
        If selectimage is None, there will be no alternation, with image present
        at all times (i.e., while selected and notselected).
        If there is no image alternation (image=selectimage=None), the text can
        render to an image like for other Text classes. This will fail if
        an image is provided, in the same manner as for other Text classes.
        """
        kwargs['font']=kwargs.get('font','read')
        kwargs['indicatoron']=kwargs.get('indicatoron',False)
        img_names=['uncheckedbox','checkedbox']
        if not kwargs.pop('large_images',False):
            img_names=[f'{i}_sm' for i in img_names]
        kwargs['selectimage']=kwargs.get('selectimage',
                                        parent.theme.photo[img_names[1]].scaled)
        if kwargs.get('selectimage'):
            kwargs['image']=kwargs.get('image',
                        parent.theme.photo[img_names[0]].scaled)
            kwargs['norender']=True #This creates self.image
        super().__init__(parent, *args, **kwargs)
        kwargs=self.super_kwargs
        self.post_tk_init()
class ListBox(Childof,Gridded,UI,tkinter.Listbox): #TextBase?
    tk_textkwargs=TextBase.tk_textkwargs|{'listvariable'}
    def pre_tk_init(self,**kwargs):
        """This restores kwargs needed for the tkinter classes"""
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self):
        try:
            assert not hasattr(self['listvariable'].get(), '__iter__')
            self['listvariable'].set(self.optionlist) #even if empty, make this iter
        except:
            self['listvariable']=tkinter.Variable(value=self.optionlist)
        self.bind('<<ListboxSelect>>', self.command)
        self.dogrid()
        super().post_tk_init()
    def __init__(self, parent, *args, **kwargs):
        """selectmode can be
        tkinter.BROWSE – allows a single selection. This is the default.
        tkinter.EXTENDED – select any adjacent group of items at once by clicking the first item and dragging to the last line.
        tkinter.SINGLE – allow you to select one line and you cannot drag the mouse.
        tkinter.MULTIPLE – select any number of lines at once. Clicking on any line toggles whether it is selected or not."""
        if 'textvariable' in kwargs:
            log.error("Listbox doesn't take 'textvariable'. "
                "This module can create a default 'listvariable' and fill it "
                "with 'optionlist' contents, if you don't provide a "
                "'listvariable' with contents set to a list.")
        self.optionlist=kwargs.pop('optionlist',[])
        self.command=kwargs.pop('command')
        #selectforeground is font color for selected items
        kwargs['selectbackground']=kwargs.get('selectbackground',
                                            parent.theme.activebackground)
        super().__init__(parent, *args, **kwargs)
        self.post_tk_init()
class SearchableComboBox(Childof,Gridded,Text,UI):
    """Adapted from https://coderslegacy.com/searchable-combobox-in-tkinter/"""
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, options) -> None:
        self.dropdown_id = None
        self.options = options
        # Create a Text widget for the entry field
        wrapper = tk.Frame(root)
        wrapper.pack()

        self.entry = tk.Entry(wrapper, width=24)
        self.entry.bind("<KeyRelease>", self.on_entry_key)
        self.entry.bind("<FocusIn>", self.show_dropdown)
        self.entry.pack(side=tk.LEFT)

        # Dropdown icon/button
        self.icon = ImageTk.PhotoImage(Image.open("dropdown_arrow.png").resize((16,16)))
        tk.Button(wrapper, image=self.icon, command=self.show_dropdown).pack(side=tk.LEFT)

        # Create a Listbox widget for the dropdown menu
        self.listbox = tk.Listbox(root, height=5, width=30)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        for option in self.options:
            self.listbox.insert(tk.END, option)
        self.show_at_least_n=3
    def on_entry_key(self, event):
        if len(self) <= self.show_at_least_n:
            return
        typed_value = event.widget.get().strip().lower()
        if not typed_value:
            # If the entry is empty, display all options
            self.listbox.delete(0, tk.END)
            for option in self.options:
                self.listbox.insert(tk.END, option)
        else:
            # Filter options based on the typed value
            self.listbox.delete(0, tk.END)
            filtered_options = [option for option in self.options if option.lower().startswith(typed_value)]
            for option in filtered_options:
                self.listbox.insert(tk.END, option)
        self.show_dropdown()
    def on_select(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_option = self.listbox.get(selected_index)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, selected_option)
    def show_dropdown(self, event=None):
        self.listbox.place(in_=self.entry, x=0, rely=1, relwidth=1.0, anchor="nw")
        self.listbox.lift()
        # Show dropdown for 2 seconds
        if self.dropdown_id: # Cancel any old events
            self.listbox.after_cancel(self.dropdown_id)
        self.dropdown_id = self.listbox.after(2000, self.hide_dropdown)
    def hide_dropdown(self):
        self.listbox.place_forget()
class Combobox(Childof,Gridded,TextBase,UI,tkinter.ttk.Combobox):
    """docstring for Combobox."""
    def post_tk_init(self):
        self._handle_popdown_font()
        self.bind('<<ComboboxSelected>>', self.command)
        super().post_tk_init()
    def _handle_popdown_font(self):
        """ Handle popdown font
        Note: https://github.com/nomad-software/tcltk/blob/master/dist/library/ttk/combobox.tcl#L270
        """
        #   grab (create a new one or get existing) popdown
        popdown = self.tk.eval('ttk::combobox::PopdownWindow %s' % self)
        #   configure popdown font
        self.tk.call('%s.f.l' % popdown, 'configure', '-font', self['font'])
    def configure(self, cnf=None, **kw):
        """Configure resources of a widget. Overridden!
        The values for resources are specified as keyword
        arguments. To get an overview about
        the allowed keyword arguments call the method keys.
        """
        #   default configure behavior
        self._configure('configure', cnf, kw)
        #   if font was configured - configure font for popdown as well
        if 'font' in kw or (cnf and 'font' in cnf):
            self._handle_popdown_font()
    def __init__(self, parent, *args, **kwargs):
        kwargs['values']=kwargs.pop('optionlist')
        self.command=kwargs.pop('command')
        super().__init__(parent, *args, **kwargs)
        self.post_tk_init()
class Scrollbar(Childof,Gridded,UI,tkinter.Scrollbar):
    """Scrollbar for scrolling frames."""
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, parent, *args, **kwargs):
        """set this befor gridded call"""
        if 'orient' in kwargs and kwargs['orient']==tkinter.HORIZONTAL:
            kwargs['sticky']=kwargs.get('sticky',tkinter.E+tkinter.W)
        else:
            kwargs['sticky']=kwargs.get('sticky',tkinter.N+tkinter.S)
        super().__init__(parent, *args, **kwargs)
        """after theme is inherited:"""
        self.post_tk_init()
"""These classes don't call tkinter classes directly"""
class Window(Toplevel):
    def post_tk_init(self):
        """This centers the r=c=1 frame"""
        for rc in [0,2]:
            self.grid_rowconfigure(rc, weight=3)
            self.grid_columnconfigure(rc, weight=3)
        try:
            self.iconphoto(False, self.parent.theme.photo['icon'].scaled) #!transparent
        except Exception as e:
            log.info(f"{e} self.theme.photo: {self.theme.photo}")
        super().post_tk_init()
    def progress(self,value,parent=None,**kwargs):
        # between 0 and 100
        try:
            self.progressbar.current(value)
            # log.info(f"Window progress updated to {value}")
        except AttributeError:
            print("making new progressbar")
            if not parent:
                parent=self.outsideframe
            self.progressbar=Progressbar(parent,
                                    orient='horizontal',
                                    mode='determinate', #or 'indeterminate'
                                    **kwargs)
            self.progress(value)
        except Exception as e:
            log.info(f"Exception updating progress: {e}")
    def resetframe(self):
        if self.parent.exitFlag.istrue():
            return
        if self.winfo_exists(): #If this has been destroyed, don't bother.
            if hasattr(self,'frame') and type(self.frame) is Frame:
                self.frame.destroy()
            for rc in [0,2]:
                self.outsideframe.grid_rowconfigure(rc, weight=3)
                self.outsideframe.grid_columnconfigure(rc, weight=3)
            self.frame=Frame(self.outsideframe, #border=5,
                            row=1, column=1, sticky='nsew',
                            )
    def __init__(self, parent, backcmd=False, exit=True, title="No Title Yet!",
                choice=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.post_tk_init()
        self.title(title)
        self.outsideframe=Frame(self, # border=True,
                                row=1, column=1, sticky='nsew',
                                )
        self.resetframe()
        # self.exitFlag=ExitFlag() #This overwrites inherited exitFlag
        if exit:
            e=(_("Exit")) #This should be the class, right?
            self.exitButton=Button(self.outsideframe, width=10, text=e,
                                command=self.on_quit,
                                font='small',
                                column=2,row=2
                                            )
        if backcmd is not False: #This one, too...
            b=(_("Back"))
            cmd=lambda:backcmd(parent, window, check, entry, choice)
            self.backButton=Button(self.outsideframe, width=10, text=b,
                                command=cmd,
                                column=3,row=2
                                            )
class ContextMenu(Childof):
    def post_tk_init(self):
        super().post_tk_init()
    def updatebindings(self):
        self.parent.bind('<Motion>', self._bind_to_makemenus)
        self.parent.bind('<Leave>', self._unbind_to_makemenus) #parent only
    def undo_popup(self,event=None):
        if hasattr(self,'menu'):
            log.log(2,"undo_popup Checking for ContextMenu.menu: {}".format(
                                                            self.menu.__dict__))
            try:
                self.root.destroy()
                log.log(3,"popup parent/root destroyed")
            except:
                log.log(3,"popup parent/root not destroyed!")
            finally:
                self.parent.unbind_all('<Button-1>')
    def menuinit(self):
        """redo menu on context change"""
        try:
            self.menu = Menu(self.root, tearoff=0)
        except Exception as e:
            log.error(f"Problem initializing context menu: {e}")
            raise
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
            self.menu.bind('<Leave>',self.undo_popup) #_all
            self.menu.grab_release() #allows click on main window
    def _bind_to_makemenus(self,event): #all needed to cover all of window
        self.parent.bind_all('<Button-3>',self.do_popup) #_all
        self.parent.bind_all('<Button-1>',self.undo_popup)
    def _unbind_to_makemenus(self,event):
        self.parent.unbind_all('<Button-3>')
    def getroot(self):
        self.root=Root(self.parent._root().program)
        self.root.withdraw()
        log.info("Ad hoc inherit")
        Childof.inherit(self.root,self.parent)
        log.info("Ad hoc inherit done")
    def __init__(self,parent,context=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.getroot()
        self.post_tk_init()
        self.parent.context=self
        self.context=context #where the menu is showing (e.g., verifyT)
        self.updatebindings()
"""These have gridding (not Window or ContextMenu, above)"""
class ButtonFrame(Frame):
    bf_kwargs={'optionlist'}
    bf_kwargs|=Button.buttons #not for Tk —Frame!
    tk_bf_kwargs={}
    def reserve_kwargs(self,**kwargs):
        kwargs=Button.reserve_kwargs(self,**kwargs)
        for k in set(kwargs)&ButtonFrame.bf_kwargs: #any kwarg used on buttons
            if hasattr(self,k) and getattr(self,k) != kwargs[k]:
                log.info(f"ButtonFrame found {k}:{getattr(self,k)} ({kwargs[k]=})")
                exit() #this should never happen
            # log.info(f"ButtonFrame reserving {k}:{kwargs[k]}")
            setattr(self,k,kwargs.pop(k))
        return kwargs
    def restore_kwargs(self,**kwargs):
        kwargs=Button.restore_kwargs(self,**kwargs) #not a subclass
        for k in ButtonFrame.bf_kwargs: #all, not just those OK for Tk
            if hasattr(self,k):
                # log.info(f"ButtonFrame restore_kwargs found {k}:{getattr(self,k)}")
                kwargs[k]=getattr(self,k)
        return kwargs
    def my_tk_kwargs(self,**kwargs):
        kwargs=Button.my_tk_kwargs(self,**kwargs) #super?
        return {k:v for k,v in kwargs.items()
                if k not in self.bf_kwargs or k in self.tk_bf_kwargs
                }
    def pre_tk_init(self,**kwargs):
        """This restores kwargs needed for the tkinter classes"""
        kwargs=ButtonFrame.restore_kwargs(self,**kwargs) #add back to kwargs
        kwargs=ButtonFrame.my_tk_kwargs(self,**kwargs) #then limit
        kwargs=super().pre_tk_init(**kwargs) #self.kwargs?
        return kwargs
    def post_tk_init(self):
        super().post_tk_init()
    def regularize_choice(self,choice):
        if type(choice) in [str,int]: #most popular
            choice={'code':choice, 'name':choice}
        elif type(choice) is dict:
            #Whatever is in a dict; this assures 'code' and 'name'.
            if choice['code'] in [None,'Null','None']:
                choice['name']=choice.get('name',"None of These")
            else:
                choice['name']=choice.get('name',str(choice['code']))
        elif type(choice) is tuple:
            if len(choice) == 4:
                choice={'code':choice[0], 'name':choice[1],
                        'description':choice[2], 'image':choice[3]}
            elif len(choice) == 3:
                choice={'code':choice[0], 'name':choice[1],
                        'description':choice[2]}
            elif len(choice) == 2:
                choice={'code':choice[0], 'name':choice[1]}
            else:
                log.error(f"I don't know how to process tuple {choice=}")
                return
        else:
            log.info(f"Problem setting up {choice=} ({type(choice)=})")
            return
        #For historical reasons, I used 'code' here, but 'choice' for button.
        kwargs={'choice':choice['code'],
                'text':choice['name']}
        if 'image' in choice:
            kwargs['image']=choice['image']
        if 'description' in choice:
            kwargs['text']+=f' ({str(choice['description'])})'
        # log.info(f"returning one button {kwargs=}")
        return kwargs
    def __init__(self,parent,**kwargs):
        """optionlist can be specified as a simple iterable, or as a list of
        options specifying 'code', 'name', 'description', and 'image'.
        A tuple is interpreted as those items, in that order, so 'code' will
        always be taken, while 'image' only will if all four items are there.
        Dictionary items should be keyed with those names.
        If 'name' is missing, it is taken from 'code'.
        if 'description' is present, it is added to the name for button display,
        in parentheses. This is often used for an item count.
        If present, 'image' should appear according to the normal button rules
        for images.
        """
        #Because there may be button/Text kwargs, which shouldn't go to Frame
        kwargs=ButtonFrame.restore_kwargs(self,**kwargs)
        kwargs=ButtonFrame.reserve_kwargs(self,**kwargs)
        super().__init__(parent,**kwargs)
        kwargs=self.super_kwargs #don't forward frame args
        """Make sure list is in the proper format: list of dictionaries"""
        if isinstance(self.optionlist, str):
            log.info(f"options is string! {self.optionlist=} "
                        f"({type(self.optionlist)=})")
            return
        if not hasattr(self.optionlist, '__iter__'):
            log.info(f"options Not iterable! {self.optionlist=} "
                        f"({type(self.optionlist)=})")
            return
        if (self.optionlist is None) or (len(self.optionlist) == 0):
            log.info("list is empty!",type(self.optionlist))
            return
        self.buttons=dict()
        kwargs=Button.restore_kwargs(self,**kwargs)
        # log.info(f"returning buttonFrame with {kwargs=}")
        for choice in self.optionlist:
            choice_kwargs=self.regularize_choice(choice)
            if not choice:
                continue
            self.buttons[choice_kwargs['choice']]=Button(self,
                                                row=len(self.winfo_children()),
                                                **choice_kwargs,
                                                **kwargs
                                                )
class ScrollingFrame(Frame):
    def post_tk_init(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        """With or without the following, it still scrolls through..."""
        self.grid_propagate(0) #make it not shrink to nothing
        super().post_tk_init()
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
    def update(self):
        self._configure_canvas()
        # self._configure_interior()
    def _configure_interior(self, event=None):
        log.log(4,"_configure_interior, on content change")
        self.update_idletasks()
        size = (self.content.winfo_reqwidth(), self.content.winfo_reqheight())
        self.canvas.config(scrollregion="0 0 %s %s" % size)
        """This makes sure the canvas is as large as what you put on it"""
        # self.windowsize() #this needs to not keep running
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
        if contentrw > self.maxwidth and not self.ignore_maxwidth:
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
    def __init__(self, parent, xscroll=False, *args, **kwargs):
        self.ignore_maxwidth=kwargs.pop('ignore_maxwidth',False)
        """Make this a Frame, with all the inheritances, I need"""
        super().__init__(parent, *args, **kwargs)
        self.post_tk_init()
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
        self.canvas.grid(row=0, column=0,sticky='nsew')
        """We might want horizonal bars some day? (also above)"""
        if xscroll == True:
            xscrollbar.config(width=self.yscrollbarwidth)
            xscrollbar.config(background=self.theme.background)
            xscrollbar.config(activebackground=self.theme.activebackground)
            xscrollbar.config(troughcolor=self.theme.background)
            xscrollbar.config(command=self.canvas.xview)
        yscrollbar.config(command=self.canvas.yview)
        """Bindings so the mouse wheel works correctly, etc."""
        w=self.winfo_toplevel()
        self.bind('<Enter>', self._bound_to_mousewheel)
        self.bind('<Leave>', self._unbound_to_mousewheel)
        self.canvas.bind('<Destroy>', self._unbound_to_mousewheel)
        # self.canvas.bind('<Configure>', self._configure_canvas) #called by:
        self.content.bind('<Configure>', self._configure_interior)
        self.bind('<Visibility>', self.windowsize)
class ScrollingButtonFrame(ScrollingFrame):
    """This needs to go inside another frame, for accurrate grid placement"""
    def reserve_kwargs(self,**kwargs):
        kwargs=ButtonFrame.reserve_kwargs(self,**kwargs)
        return kwargs
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self,parent,**kwargs):
        # log.info(f"Calling ScrollingButtonFrame {kwargs=}")
        kwargs=self.reserve_kwargs(**kwargs)
        super().__init__(parent,**kwargs)
        kwargs=self.super_kwargs
        self.post_tk_init()
        kwargs=ButtonFrame.restore_kwargs(self,**kwargs)
        self.bf=ButtonFrame(parent=self.content,
                            row=0,
                            column=0,
                            **kwargs)
        # log.info(f"ScrollingButtonFrame ButtonFrame complete {kwargs=}")
class RadioButtonFrame(Frame):
    rbf_kwargs={'optionlist'}
    def reserve_kwargs(self,**kwargs):
        kwargs=RadioButton.reserve_kwargs(self,**kwargs)
        for k in set(kwargs)&RadioButtonFrame.rbf_kwargs: #any button kwarg
            if hasattr(self,k):
                log.info(f"RadioButtonFrame found {k}:{getattr(self,k)}")
                exit() #this should never happen
            # log.info(f"RadioButtonFrame reserving {k}:{kwargs[k]}")
            setattr(self,k,kwargs.pop(k))
        return kwargs
    def pre_tk_init(self,**kwargs):
        """Not Tk kwargs to add here"""
        kwargs=super().pre_tk_init(**kwargs)
        return kwargs
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, parent, *args, **kwargs):
        horizontal=kwargs.pop('horizontal',False) #only for this init
        column=row=0
        sticky=kwargs.pop('sticky','w')
        kwargs=self.reserve_kwargs(**kwargs)
        super().__init__(parent, *args, **kwargs)
        kwargs=self.super_kwargs
        self.post_tk_init()
        for opt in self.optionlist:
            if type(opt) is tuple and len(opt) == 2:
                value=opt[0]
                name=opt[1]
            else:
                name=value=opt
            log.log(3,"Value: {}; name: {}".format(value,name))
            kwargs=RadioButton.restore_kwargs(self,**kwargs)
            RadioButton(self,value=value, text=nfc(name),
                                                column=column,
                                                row=row,
                                                sticky=sticky,
                                                **kwargs
                                                )
            if horizontal:
                column+=1
            else:
                row+=1
class ToolTip(object):
    """
    create a tooltip for a given widget
    modified from https://stackoverflow.com/, originally from
    www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
    Modified to include a delay time by Victor Zaccardo, 25mar16
    """
    def post_tk_init(self):
        super().post_tk_init()
    def __init__(self, widget, text=_("change this")):
        self.waittime = 500     #miliseconds before showing tip
        self.showtime = 2000    #miliseconds to show tip
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
        self.widget.after(self.showtime, self.hidetip)
    def hidetip(self, event=None):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
"""Move back to main"""
class Wait(Window): #tkinter.Toplevel?
    def post_tk_init(self):
        super().post_tk_init()
    def close(self):
        # log.info("Wait window disappears")
        self.on_quit()
    def cancel(self):
        self.parent.waitcancel()
        log.info("Sent Wait Cancel")
    def make_cancellable(self):
        self.cancelbutton=Button(self.outsideframe,text='Cancel',
                                cmd=self.cancel,
                                row=3,column=0,sticky='e')
    def msg(self,msg):
        log.info(f"Waiting: {msg}")
        self.l1['text']=msg
        self.l1.wrap()
    def __init__(self, parent, msg=None, cancellable=False, *args, **kwargs):
        kwargs['exit']=False
        super().__init__(parent, *args, **kwargs)
        self.paused=False
        self.withdraw() #don't show until we're done making it
        self['background']=parent['background']
        self.attributes("-topmost", True)
        title=(_("Please Wait! {name} Dictionary and Orthography Checker "
                "in Process").format(name=self._root().program['name']))
        self.title(title)
        text=_("Please Wait...")
        self.l=Label(self.outsideframe, text=text,
                font='title',anchor='c',
                row=0,column=0,sticky='we')
        self.l1=Label(self.outsideframe, text='',
                        font='default',anchor='c',row=1,column=0,sticky='we')
        # if msg is not None:
        if msg is None:
            msg="No Particular Reason"
        self.msg(msg)
        if not isinstance(self.parent,Root) or not self.parent.noimagescaling:
            self.l2=Label(self.outsideframe,
                        image='small',
                        text='',
                        row=2,column=0,sticky='we',padx=50,pady=50)
        if cancellable:
            self.make_cancellable()
        log.info("Wait window appears")
        try:
            self.deiconify() #show after the window is built
            log.info("Wait window deiconified")
            #for some reason this has to follow the above, or you get a blank window
            # self.update_idletasks() #updates just geometry
            log.info("Wait window creation done")
        except Exception as e:
            log.info(f"Wait window Exception: {e}")
"""unclassed functions"""
def now():
    return datetime.datetime.now(datetime.UTC).isoformat()#[:-7]+'Z'
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
def testapp2(program):
    r=Root(program=program)
    # frame=Frame(r,r=0,c=0)
    w=Window(r) #,withdrawn=True
    w.mainwindow=True
    w.title(f"Testing Drag and Drop with {w.theme.name} theme")
    droppable=False
    draggable=True
    cols=2
    for i in range(6):
        Label(w.frame,
                    text=f"Label {i}\ndrag:{draggable} \ndrop: {droppable}",
                    font='title',
                    row=i//cols, column=i%cols,
                    draggable=True,
                    droppable=droppable,
                    borderwidth=1,relief='raised')
        #switch after first
        draggable=False
        droppable=True
    w.mainloop()
def testapp3(program):
    r=Root(program=program)
    # frame=Frame(r,r=0,c=0)
    w=Window(r) #,withdrawn=True
    w.mainwindow=True
    w.title(f"Testing with {w.theme.name} theme")
    sf=ScrollingFrame(w.frame,row=1,column=1)
    i=0
    for p in [r,w,w.frame,sf.content,w.outsideframe]:
        label1=Button(p,
                        text=f"Seems to work \n({p};{i}!",
                        font='title',
                        command=w.frame.winfo_children()[-1].destroy,
                        row=0,column=0,#draggable=True,
                        borderwidth=1,relief='raised')
        i+=1
        log.info(f"Finished with {p}")
    log.info(f"w children: {w.winfo_children()}")
    log.info(f"r children: {r.winfo_children()}")
    log.info(f"r MRO: {r.__class__.__mro__}")
    for text in [("Pictured Only", ),
                            ("Show All", )]:
        Button(w.frame, text=text, command=w.frame.winfo_children()[-1].destroy,
                    r=w.frame.grid_size()[1], c=0)
    Button(w.frame, text="Print", command=w.frame.winfo_children()[-1].destroy,
                r=w.frame.grid_size()[1], c=0)# # w.outsideframe.grid()
    r.deiconify()
    # w.deiconify()
    w.mainloop()
def testapp4(program):
    def textadd(x):
        l['text']+=str(x)
    def printed(*args,window=None):
        for x in args:
            print(str(x)+'ed')
        if window:
            window.destroy()
    r=Root(program=program)
    log.info("root is {}".format(r))
    # r.withdraw()
    print(r.theme,r.theme.name)
    w=Window(r) #,withdrawn=True
    w.mainwindow=True
    log.info(f"window is {w=}, children {w.winfo_children()=} {w._root()=}")
    log.info(f"root is {r=}, children {r.winfo_children()=} {r._root()=}")
    # sf=ScrollingFrame(w.outsideframe,row=0,column=0)
    test_frame=Frame(w.frame,row=1,column=1)
    sbf1=ScrollingButtonFrame(test_frame,
                    optionlist=range(6,11),
                    command=printed,
                    window=w,
                    image='icon',
                    compound='right',
                    bsticky='ew',
                    sticky='',
                    row=0,column=0)
    l=Label(sbf1.content,text="testing SBF",
                            row=1)#len(sbf1.content.winfo_children()))
    sbfb=Button(sbf1.content,
                text="testing SBF",
                cmd=lambda x='.':textadd(x),
                row=2)#len(sbf1.content.winfo_children()))
    r.mainloop()
def testapp(program):
    def print_vars(*args):
        log.info(f"{var.__class__} {var.get()=}")
        for i in (l,entry):
            # log.info(f"{i.get()=}")
            try:
                log.info(f"{i.__class__} {i.get()=}")
            except Exception as e:
                log.info(f"exception ({i.__class__}): {e}")
            for v in ['text','textvariable']:
                log.info(f"{i.__class__} {v} {i[v]=}")
                try:
                    log.info(f"{i.__class__} {v} {i[v].get()=}")
                except Exception as e:
                    log.info(f"exception ({i.__class__},{v}): {e}")
    r=Root(program=program)
    log.info("root is {}".format(r))
    # r.withdraw()
    print(r.theme,r.theme.name)
    w=Window(r) #,withdrawn=True
    w.mainwindow=True
    log.info(f"window is {w=}, children {w.winfo_children()=} {w._root()=}")
    log.info(f"root is {r=}, children {r.winfo_children()=} {r._root()=}")
    # sf=ScrollingFrame(w.outsideframe,row=0,column=0)
    test_frame=Frame(w.frame,row=1,column=1)
    var=StringVar(value='default')
    var.trace_add('write',print_vars)
    l=Label(test_frame,textvariable=var,
                            row=1)#len(sbf1.content.winfo_children()))
    entry=EntryField(test_frame,
                textvariable=var,
                render=True,
                row=2)#len(sbf1.content.winfo_children()))
    print_vars()
    r.mainloop()
def testappX(program):
    def progress(event):
        # print('running progress')
        import time
        for i in range(101):
            for p in bars:
                if p[1]<2:
                    bars[p].current(100-i)
                else:
                    bars[p].current(i)
            time.sleep(.002)
    def textchange(event):
        l['text']="new text ˥˥˦˦˧"
    def textadd(x):
        l['text']+=str(x)
    r=Root(program=program)
    log.info("root is {}".format(r))
    # r.withdraw()
    print(r.theme,r.theme.name)
    w=Window(r) #,withdrawn=True
    w.mainwindow=True
    log.info(f"window is {w=}, children {w.winfo_children()=} {w._root()=}")
    log.info(f"root is {r=}, children {r.winfo_children()=} {r._root()=}")
    # sf=ScrollingFrame(w.outsideframe,row=0,column=0)
    test_frame=Frame(w.frame,row=1,column=1)
    sbf1=ScrollingButtonFrame(test_frame,
                    optionlist=range(6,11),
                    command=print,
                    row=0,column=0)
    sbfl=Label(sbf1.content,text="testing SBF",
                            row=1)#len(sbf1.content.winfo_children()))
    sf=ScrollingFrame(test_frame,row=1,column=0)
    # class DragLabel(Label):
    #     def dnd_end(self,target,event):
    #         print(target)
    #         print(target['text'])
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    firstFrame=Frame(sf.content,row=0,column=0)
    label1=Label(firstFrame,text="Seems to work!",font='title',
            row=0,column=0,draggable=True,image='icon',#compound='left',
            borderwidth=1,relief='raised')
    button1=Button(firstFrame,text="Seems to work!",font='title',
            row=0,column=1,draggable=True,image='icon',#compound='left',
            command=lambda: sf.content.winfo_children()[-1].destroy(), borderwidth=1,relief='raised')
    entry=EntryField(firstFrame,render=True,row=1,column=0,colspan=2)
    rb_var=StringVar()
    def printvar(x):
        print()
    rb1=RadioButton(firstFrame,text="RadioButton 1",
                    variable=rb_var,
                    value=1,
                    row=2,column=0)
    rb2=RadioButton(firstFrame,text="RadioButton 1 (no indicatoron)",
                    variable=rb_var,
                    value=2,
                    row=2,column=1,indicatoron=0)
    rb_var.trace_add('write',lambda *args:print(rb_var.get()))
    rbf=RadioButtonFrame(firstFrame,
                        variable=rb_var,
                        optionlist=[(i,'+'+str(i)) for i in range(4)],
                        # opts=range(4),
                        indicatoron=1,
                        # horizontal=True,
                        row=3,column=0)
    b1=Button(firstFrame,
                    text='destroy me',
                    command=exit,
                    row=3,column=1)
    bf2=ButtonFrame(firstFrame,
                    optionlist=range(5,10),
                    command=print,
                    row=4,column=1)
    # label1.dnd_end=lambda x,event:print(x.text)
    # tkinter.dnd.Draggable(label1)
    textvariable=StringVar()
    options = ("choice 1", "choice 2", "choice 3", "choice 4")
    def print_choice(event):
        print(textvariable.get())
    c=Combobox(sf.content,
                textvariable=textvariable,
                command=print_choice,
                optionlist=options,
                # image='icon',
                row=0,column=1,droppable=True)
    textvariable2=StringVar()
    def print_selection(event=None):
        print(event,lb1.curselection(),type(lb1.curselection()))
        if 0 in lb1.curselection() and len(lb1.curselection())>1:
            for i in lb1.curselection():
                if i:
                    lb1.select_clear(i)
        # print(lb1.curselection(),type(lb1.curselection()))
        print(", ".join([lb1.get(i) for i in lb1.curselection()]))
        # print('selection:',lb1.get(lb1.curselection()))
        # print(f"box length: {len(lb1.get(0,'end'))}")
        for i in lb1.curselection():
            print(lb1.get(i))
    lb1=ListBox(sf.content,
                listvariable=textvariable2,
                selectmode=tkinter.MULTIPLE,
                command=print_selection,
                optionlist=options,#droppable=True,
                height=3,
                row=0,column=2)
    lb1.selection_set(0)
    CheckButton(sf.content,
                text="Boolean toggle w/default imgs ([˥˥˦˦˨])",
                anchor='c',
                variable = BooleanVar(),
                onvalue = True, offvalue = False,
                norender=True,
                # selectimage=None,
                font='default',
                row=1,column=1)
    CheckButton(sf.content,
                text="Boolean toggle w/indicatoron",
                anchor='c',
                variable = BooleanVar(),
                onvalue = True, offvalue = False,
                indicatoron=True,
                # selectimage=None,
                font='default',
                row=2,column=1)
    CheckButton(sf.content,
                text="Boolean toggle w/o default imgs ([˥˥˦˦˨])",
                anchor='c',
                variable = BooleanVar(),
                onvalue = True, offvalue = False,
                selectimage=None,
                # no_default_indicator_images=True,
                # image='icon',compound='bottom',selectimage=None,
                font='default',
                row=3,column=1)
    CheckButton(sf.content,
                text="Boolean toggle w/indicatoron\nw/o default imgs",
                anchor='c',
                variable = BooleanVar(),
                onvalue = True, offvalue = False,
                indicatoron=True,
                selectimage=None,
                # image='icon',selectimage=None,
                # no_default_indicator_images=True,
                font='default',
                row=4,column=1)
    l=Label(sf.content,text="At least this much",
            row=5,column=0, font='italic',
            borderwidth=3,relief='raised')
    log.info("l _root is {}".format(l._root()))
    log.info("Image dict: {}".format(r.theme.photo))
    # l.img=r.theme.photo['NoImage']
    # # log.info("Image: {} ({})".format(l.img.transparency, Image.maxhw(l.img)))
    # log.info("Image dir: {}".format(dir(l.img)))
    # l.img.scale(program['scale'],pixels=100,resolution=10)
    # log.info("Image: {} ({})".format(l.img.scaled, Image.maxhw(l.img,scaled=True)))
    # l['image']=l.img.scaled
    # l['compound']="bottom"
    ToolTip(l,"this image has a tooltip")
    column,row=sf.content.grid_size()
    lm_frame=Frame(sf.content,r=row,c=0,colspan=column)
    for c,cls in enumerate([Message,Label]):
    # for c,cls in enumerate([Label]):
        cname=cls.__name__
        cls(lm_frame,text="This is a {} ˥˥˦˦˨".format(cname),row=2, column=c,
                borderwidth=1,relief='raised')
        cls(lm_frame,text="This is a very long {}".format(cname),row=4, column=c,
                borderwidth=1,relief='raised',droppable=True)
        cls(lm_frame,text="This is a very very long {}".format(cname),
            row=5, column=c,
            borderwidth=1,relief='raised',droppable=True)
        cls(lm_frame,text="This is a very very very very long {}"
                    "".format(cname),
                    row=6, column=c,
                    borderwidth=1,relief='raised',droppable=True)
        lll=cls(lm_frame,text="This is a very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "very very very very "
                    "long {}".format(cname),row=7, column=c,
                    borderwidth=1,relief='raised',droppable=True)
        if cls == Label:
            lll.config(wraplength=120)
    bars={}
    for orient in ['horizontal','vertical']:
        for row in [0,2]:
            if orient=='horizontal':
                col=1
                colspan=1
                rowspan=1
                sticky='ew'
            else:
                col=row
                row=1
                colspan=1
                rowspan=1
                sticky='ns'
            bars[(orient,row+col)]=Progressbar(w.frame, orient=orient,
                                            mode='determinate',
                                            row=row, column=col,
                                            columnspan=colspan,
                                            rowspan=rowspan,
                                            sticky=sticky)
    w.bind('<ButtonRelease-1>',textchange)
    w.bind('<ButtonRelease-1>',progress,add=True)
    w.bind('<Up>',lambda event,x='^':textadd(x),add=True)
    w.bind('<Prior>',lambda event,x='^':textadd(x),add=True) #page up button
    w.bind('<Down>',lambda event,x='v':textadd(x),add=True)
    w.bind('<Next>',lambda event,x='v':textadd(x),add=True) #page down button
    w.bind('<Left>',lambda event,x='<—':textadd(x),add=True)
    w.bind('<Right>',lambda event,x='—>':textadd(x),add=True)
    log.info(dir(w))
    log.info(w.bindtags())
    log.info(w.wm_state())
    log.info(w.state())
    h=IntVar(value=1)
    j=IntVar(value=False)
    # l=list([1,2,3,4])
    k=Variable(value=l)
    # l=StringVar(value='False')
    for i in [h,j,k]:
        print(isinstance(i,tkinter.Variable),type(i),i.get(),type(i.get()))
        if isinstance(i.get(),tuple):
            print("Found a tuple!")
            for m in i.get():
                print(m)
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
    sys.exit()
