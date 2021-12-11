#!/usr/bin/env python3
# coding=UTF-8
import sys
import platform
import logging
log = logging.getLogger(__name__) #bc not imported as a module...
import unicodedata
import tkinter #as gui
import tkinter.font
import tkinter.scrolledtext
import file #for image pathnames
from random import randint #for theme selection
# import tkintermod
# tkinter.CallWrapper = tkintermod.TkErrorCatcher
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
class Gridded(ObectwArgs):
    def dogrid(self):
        if self._grid:
            log.info("Gridding at r{},c{},rsp{},csp{},st{},padx{},pady{},"
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
        return kwargs
    def __init__(self, *args, **kwargs): #because this is used everywhere.
        """this removes gridding kwargs from the widget calls"""
        self.gridkwargs=['sticky','row','column','columnspan','padx','pady']
        # log.info("Gridded parent: {}".format(parent))
        # log.info("Gridding? ({})".format(kwargs))
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
            log.info("Not Gridding! ({})".format(kwargs))
class Childof(object):
    def inherit(self,parent=None,attr=None):
        """This function brings these attributes from the parent, to inherit
        from the root window, through all windows, frames, and scrolling frames, etc
        """
        if not parent and hasattr(self,'parent') and self.parent:
            parent=self.parent
        elif parent:
            self.parent=parent
        if attr is None:
            attrs=['theme',
                    # 'fonts', #in theme
                    # 'debug',
                    'wraplength',
                    # 'photo', #in theme
                    'renderings',
                    'program','exitFlag']
        else:
            attrs=[attr]
        for attr in attrs:
            if hasattr(parent,attr):
                setattr(self,attr,getattr(parent,attr))
            else:
                log.info("parent doesn't have attr {}, skipping inheritance"
                        "".format(attr))
    def __init__(self, parent): #because this is used everywhere.
        log.info("Initializing Childof object")
        self.parent=parent
        self.inherit()
class UI(ObectwArgs):
    """docstring for UI, after tkinter widgets are initted."""
    def wait(self,msg=None):
        if hasattr(self,'ww') and self.ww.winfo_exists() == True:
            log.debug("There is already a wait window: {}".format(self.ww))
            return
        self.ww=Wait(self,msg)
    def waitdone(self):
        try:
            self.ww.close()
        except tkinter.TclError:
            pass
    def __init__(self): #because this is used everywhere.
        log.info("Initializing UI object")
        if hasattr(self,'theme'):
            try:
                self['background']=self.theme.background
                self['bg']=self.theme.background
                self['foreground']=self.theme.background
                self['activebackground']=self.theme.activebackground
                self['troughcolor']=self.theme.background
            except TypeError as e:
                log.info("TypeError {}".format(e))
            except tkinter.TclError as e:
                log.info("TclError {}".format(e))
        # super(UI, self).__init__(*args, **kwargs)
class Root(tkinter.Tk,UI):
    """docstring for Root."""
    def settheme(self,theme):
        self.theme=theme
        self['background']=self.theme.background
        self['bg']=self.theme.background
    def __init__(self, *args, **kwargs):
        self.exitFlag = ExitFlag()
        super(Root, self).__init__()
        UI.__init__(self)
        self.protocol("WM_DELETE_WINDOW", lambda s=self: Window.on_quit(s))
class Toplevel(tkinter.Toplevel,UI): #NoParent
    def __init__(self, parent, *args, **kwargs):
        log.info("Initializing Toplevel object")
        log.info("Toplevel parent: {}".format(parent))
        Childof.__init__(self,parent)
        tkinter.Toplevel.__init__(self)
        UI.__init__(self)
class Frame(Gridded,Childof,tkinter.Frame):
    def windowsize(self):
        if not hasattr(self,'configured'):
            self.configured=0
        if self.configured>10:
            return
        availablexy(self)
        """The above script calculates how much screen is left to fill, these
        next two lines give a max widget size to stay in the window."""
        # height=self.parent.winfo_screenheight()-self.otherrowheight
        # width=self.parent.winfo_screenwidth()-self.othercolwidth
        # print('height=',self.parent.winfo_screenheight(),-self.otherrowheight)
        # print('width=',self.parent.winfo_screenwidth(),-self.othercolwidth)
        # print(height,width)
        """This is how much space the contents of the scrolling canvas is asking
        for. We don't need the scrolling frame to be any bigger than this."""
        """These lines are different than for the scrolling frame"""
        contentrw=self.winfo_reqwidth()
        contentrh=self.winfo_reqheight()
        """If the current scrolling frame dimensions are smaller than the
        scrolling content, or else pushing the window off the screen, then make
        the scrolling window the smaller of
            -the scrolling content or
            -the max dimensions, from above."""
        # if self.winfo_width() < contentrw:
        #      self.config(width=contentrw)
        # if self.winfo_width() > self.maxwidth:
        #     self.config(width=self.maxwidth)
        if ((self.winfo_width() < contentrw)
                or (self.winfo_width() > self.maxwidth)):
                self.config(width=min(self.maxwidth,contentrw))
        # if self.winfo_height() < contentrh:
        #     self.config(height=contentrh)
        # if self.winfo_height() > self.maxheight:
        #     self.config(height=self.maxheight)
        if ((self.winfo_height() < contentrh)
                or (self.winfo_height() > self.maxheight)):
            self.config(height=min(self.maxheight,contentrh))
        self.configured+=1
    def __init__(self, parent, **kwargs):
        log.info("Initializing Frame object")
        Gridded.__init__(self,**kwargs)
        kwargs=self.lessgridkwargs(**kwargs)
        Childof.__init__(self,parent)
        # for attr in ['fonts','theme','debug','wraplength','photo','renderings',
        #         'program','exitFlag']:
        #     if hasattr(parent,attr):
        #         setattr(self,attr,getattr(parent,attr))
        self['bg']=self.theme.background
        UI.__init__(self)
        self.dogrid()
class Scrollbar(Gridded,tkinter.Scrollbar,UI):
    """docstring for Scrollbar."""

    def __init__(self, parent, *args, **kwargs):
        UI.inherit(self,parent)
        Childof.__init__(self,parent)
        if 'orient' in kwargs and kwargs['orient']==tkinter.HORIZONTAL:
            kwargs['sticky']=kwargs.get('sticky',tkinter.E+tkinter.W)
        else:
            kwargs['sticky']=kwargs.get('sticky',tkinter.N+tkinter.S)
        # yscrollbar.config(background=self.theme.background)
        # yscrollbar.config(activebackground=self.theme.activebackground)
        # yscrollbar.config(troughcolor=self.theme.background)
        super(Scrollbar, self).__init__(
        parent=parent,
        **kwargs
        )
        """after theme is inherited:"""
        self['background']=self.theme.background
        self['activebackground']=self.theme.activebackground
        self['troughcolor']=self.theme.background
        UI.__init__(self)
        self.dogrid()
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
            log.info("self.content reqwidth differs from canvas; fixing.")
            # update the inner frame's width to fill the canvas
            # self.content_id.config(width=self.content.winfo_reqwidth())
            self.canvas.itemconfigure(self.content_id,
                                        width=self.content.winfo_reqwidth())
        if self.content.winfo_reqheight() != self.canvas.winfo_height():
            log.info("self.content reqheight differs from canvas; fixing.")
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
    def __init__(self,parent,xscroll=False,**kwargs):
        UI.inherit(self,parent)
        Gridded.__init__(self,**kwargs)
        """Make this a Frame, with all the inheritances, I need"""
        # inherit(self)
        super(ScrollingFrame,self).__init__(parent, **kwargs)
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
        for attr in ['fonts','theme','debug','wraplength','photo','renderings',
                'program','exitFlag']:
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
class Window(Toplevel):
        UI.__init__(self)
        self.dogrid()
    def resetframe(self):
        if self.parent.exitFlag.istrue():
            return
        if self.winfo_exists(): #If this has been destroyed, don't bother.
            if hasattr(self,'frame') and type(self.frame) is Frame:
                self.frame.destroy()
            self.frame=Frame(self.outsideframe,
                            column=0,row=0,sticky='nsew'
                            )
    def removeverifymenu(self,event=None):
        #This removes menu from the verify window
        if hasattr(self,'menubar'):
            self.menubar.destroy()
            self.parent.verifymenu=False
            self.setcontext(context='verifyT')
            return True #i.e., removed, to maybe replace later
    def on_quit(self):
        # Do this when a window closes, so any window functions can know
        # to just stop, rather than trying and throwing an error. This doesn't
        # do anything but set the flag value on exit, the logic to stop needs
        # to be elsewhere, e.g., if `self.exitFlag.istrue(): return`
        def killall():
            self.destroy()
            sys.exit()
        if hasattr(self,'exitFlag'): #only do this if there is an exitflag set
            print("Setting window exit flag True!")
            self.exitFlag.true()
        if type(self) is tkinter.Tk: #exit afterwards if main window
            killall()
        else:
            self.destroy() #do this for everything
    def __init__(self, parent, backcmd=False, exit=True, title="No Title Yet!",
                choice=None, *args, **kwargs):
        UI.inherit(self,parent)
        self.parent=parent
        self.theme=parent.theme
        """Things requiring tkinter.Window below here"""
        super(Window, self).__init__(parent) #no title attr for Toplevel
        # self.config(className="azt")
        self['background']=self.theme.background
        # self['background']=self.theme.background
        """Is this section necessary for centering on resize?"""
        for rc in [0,2]:
            self.grid_rowconfigure(rc, weight=3)
            self.grid_columnconfigure(rc, weight=3)
        self.outsideframe=Frame(self)
        """Give windows some margin"""
        self.outsideframe['padx']=25
        self.outsideframe['pady']=25
        self.outsideframe.grid(row=1, column=1,sticky='we')
        self.iconphoto(False, self.theme.photo['icon']) #don't want this transparent
        self.title(title)
        self.resetframe()
        self.exitFlag=ExitFlag() #This overwrites inherited exitFlag
        if exit:
            e=(_("Exit")) #This should be the class, right?
            self.exitButton=Button(self.outsideframe, width=10, text=e,
                                command=self.on_quit,
                                font='small'
                                            )
            self.exitButton.grid(column=2,row=2)
        if backcmd is not False: #This one, too...
            b=(_("Back"))
            cmd=lambda:backcmd(parent, window, check, entry, choice)
            self.backButton=Button(self.outsideframe, width=10, text=b,
                                command=cmd,
                                            )
            self.backButton.grid(column=3,row=2)
        UI.__init__(self)
        self.dogrid()
class Renderer(ObectwArgs):
    def __init__(self,test=False,**kwargs):
        try:
            import PIL.ImageFont
            import PIL.ImageTk
            import PIL.ImageDraw
            import PIL.Image
        except:
            log.info("Seems like PIL is not installed; skipping Renderer init.")
            self.img=None
            return
        font=kwargs['font'].actual() #should always be there
        xpad=ypad=fspacing=font['size']
        fname=font['family']
        fsize=int(font['size']*1.33)
        fspacing=10
        fonttype=''
        if font['weight'] == 'bold':
            fonttype+='B'
        if font['slant'] == 'italic':
            fonttype+='I'
        if fonttype == '':
            fonttype='R'
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
        if fname in ["Andika","Andika SIL"]:
            file='Andika-{}.ttf'.format('R') #There's only this one
            filenostaves='Andika-tstv-{}.ttf'.format(fonttype)
        elif fname in ["Charis","Charis SIL"]:
            file='CharisSIL-{}.ttf'.format(fonttype)
            filenostaves='CharisSIL-tstv-{}.ttf'.format(fonttype)
        elif fname in ["Gentium","Gentium SIL"]:
            if fonttype == 'B':
                fonttype='R'
            if fonttype == 'BI':
                fonttype='I'
            file='Gentium-{}.ttf'.format(fonttype)
            filenostaves='Gentium-tstv-{}.ttf'.format(fonttype)
        elif fname in ["Gentium Basic","Gentium Basic SIL"]:
            file='GenBas{}.ttf'.format(fonttype)
            filenostaves='GenBas-tstv-{}.ttf'.format(fonttype)
        elif fname in ["Gentium Book Basic","Gentium Book Basic SIL"]:
            file='GenBkBas{}.ttf'.format(fonttype)
            filenostaves='GenBkBas-tstv-{}.ttf'.format(fonttype)
        elif fname in ["DejaVu Sans"]:
            fonttype=fonttype.replace('B','Bold').replace('I','Oblique').replace('R','')
            if len(fonttype)>0:
                fonttype='-'+fonttype
            file='DejaVuSans{}.ttf'.format(fonttype)
            filenostaves='DejaVuSans-tstv-{}.ttf'.format(fonttype)
        else:
            log.error("Sorry, I have no info on font {}".format(fname))
            return
        try:
            font = PIL.ImageFont.truetype(font=filenostaves, size=fsize)
            log.log(2,"Using No Staves font")
        except:
            log.debug("Couldn't find No Staves font, going without")
            font = PIL.ImageFont.truetype(font=file, size=fsize)
        img = PIL.Image.new("1", (10,10), 255)
        draw = PIL.ImageDraw.Draw(img)
        w, h = draw.multiline_textsize(text, font=font, spacing=fspacing)
        textori=text
        lines=textori.split('\n') #get everything between manual linebreaks
        for line in lines:
            li=lines.index(line)
            words=line.split(' ') #split by words/spaces
            nl=x=y=0
            while y < len(words):
                y+=1
                l=' '.join(words[x+nl:y+nl])
                w, h = draw.multiline_textsize(l, font=font, spacing=fspacing)
                log.log(2,"Round {} Words {}-{}:{}, width: {}/{}".format(y,x+nl,
                                                y+nl,l,w,wraplength))
                if wraplength and w>wraplength:
                    words.insert(y+nl-1,'\n')
                    x=y-1
                    nl+=1
            line=' '.join(words) #Join back words
            lines[li]=line
        text='\n'.join(lines) #join back sections between manual linebreaks
        w, h = draw.multiline_textsize(text, font=font, spacing=fspacing)
        log.log(2,"Final size w: {}, h: {}".format(w,h))
        black = 'rgb(0, 0, 0)'
        white = 'rgb(255, 255, 255)'
        img = PIL.Image.new("RGBA", (w+xpad, h+ypad), (255, 255, 255,0 )) #alpha
        draw = PIL.ImageDraw.Draw(img)
        draw.multiline_text((0+xpad//2, 0+ypad//4), text,font=font,fill=black,
                                                                align=align)
        self.img = PIL.ImageTk.PhotoImage(img)
class Text(ObectwArgs):
    def wrap(self):
        availablexy(self)
        wraplength=min(self['wraplength'],self.maxwidth)
        self.config(wraplength=wraplength)
        log.log(3,'self.maxwidth (Label class): {}'.format(self.maxwidth))
    def render(self, **kwargs):
        style=(kwargs['font']['family'], # from kwargs['font'].actual()
                kwargs['font']['size'],kwargs['font']['weight'],
                kwargs['font']['slant'],kwargs['font']['underline'],
                kwargs['font']['overstrike'])
        if style not in self.renderings:
            self.renderings[style]={}
        if kwargs['wraplength'] not in self.renderings[style]:
            self.renderings[style][kwargs['wraplength']]={}
        thisrenderings=self.renderings[style][kwargs['wraplength']]
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
            i=Renderer(
                        text=self.text,
                        # wraplength=kwargs['wraplength'],
                        **kwargs)
            self.tkimg=i.img
            if self.tkimg is not None:
                thisrenderings[self.text]=self.image=self.tkimg
                self.text=''
    def __init__(self,parent,**kwargs):
        self.text=kwargs.pop('text','')
        self.renderings=parent.renderings
        self.anchor=kwargs.pop('anchor',"w")
        if 'font' in kwargs:
            if isinstance(kwargs['font'],tkinter.font.Font):
                log.info("Found font {}; using as is".format(kwargs['font']))
            elif kwargs['font'] in self.theme.fonts: #if font key (e.g., 'small')
                kwargs['font']=self.theme.fonts[kwargs['font']] #change key to font
        else:
            kwargs['font']=self.theme.fonts['default']
        kwargs['wraplength']=kwargs.get('wraplength',
                                        getattr(self,'wraplength',0))
        log.info("Button wraplength: {}".format(kwargs['wraplength']))
        # self.wraplength=kwargs.get('wraplength',defaultwr) #also for ButtonLabel
        self.norender=kwargs.pop('norender',False)
        self.image=kwargs.pop('image',None)
        d=set(["̀","́","̂","̌","̄","̃", "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉"])
        sticks=set(['˥','˦','˧','˨','˩',' '])
        if set(self.text) & (sticks|d) and not self.norender:
            self.render(**kwargs)
            log.info("text and image: {} - {}".format(self.text,self.image))
        else:
            self.text=nfc(self.text)
        log.info(parent)
        super(Text,self).__init__(parent,
                                    text=self.text,
                                    image=self.image,
                                    **kwargs)
class Menu(tkinter.Menu,UI): #not Text
    def pad(self,label):
        w=5 #Make menus at least w characters wide
        if len(label) <w:
            spaces=" "*(w-len(label))
            label=spaces+label+spaces
        return label
    def add_command(self,label,command):
        label=self.pad(label)
        tkinter.Menu.add_command(self,label=label,command=command)
    def add_cascade(self,label,menu):
        label=self.pad(label)
        tkinter.Menu.add_cascade(self,label=label,menu=menu)
    def __init__(self,parent,**kwargs):
        UI.inherit(self,parent)
        self.theme=parent.theme
        super(Menu,self).__init__(parent,**kwargs)
        self['font']=self.theme.fonts['default']
        self['activebackground']=self.theme.background
        self['background']=self.theme.menubackground
        UI.__init__(self)
class ContextMenu(Text,UI):
    def updatebindings(self):
        def bindthisncheck(w):
            log.log(2,"{};{}".format(w,w.winfo_children()))
            if type(w) is not tkinter.Canvas: #ScrollingFrame:
                w.bind('<Enter>', self._bind_to_makemenus)
            for child in w.winfo_children():
                bindthisncheck(child)
        self.parent.bind('<Leave>', self._unbind_to_makemenus) #parent only
        bindthisncheck(self.parent)
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
            log.info("menuinit done: {}".format(self.menu.__dict__))
        except:
            log.error("Problem initializing context menu")
    def menuitem(self,msg,cmd):
        self.menu.add_command(label=msg,command=cmd)
    def dosetcontext(self):
        try:
            log.log(3,"setcontext: {}".format(self.parent.setcontext))
            self.parent.setcontext(context=self.context)
        except:
            log.error("You need to have a setcontext() method for the "
                        "parent of this context menu ({}), to set menu "
                        "items under appropriate conditions ({}): {}.".format(
                            self.parent,self.context,self.parent.setcontext))
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
        self.root=tkinter.Tk()
        self.root.withdraw()
        self.root.parent=self.parent
        UI.inherit(self.root,self.parent)
    def __init__(self,parent,context=None):
        self.parent=parent
        self.getroot()
        UI.inherit(self,parent)
        super(ContextMenu,self).__init__(parent)
        self.parent.context=self
        self.context=context #where the menu is showing (e.g., verifyT)
        # self.inherit()
        self.updatebindings()
class Label(Gridded,Text,tkinter.Label,UI): #,tkinter.Label
        UI.__init__(self)
    def __init__(self, parent, **kwargs):
        UI.inherit(self,parent)
        log.info("label parent: {}".format(parent))
        """These shouldn't need to be here..."""
        self.theme=parent.theme
        self.parent=parent
        super(Label,self).__init__(
            **kwargs)
        i=self.grid_info()
        log.info("Label final grid_info: {}".format(i))
        if i and self.text:
            self.wrap()
        self['background']=kwargs.get('background',self.theme.background)
        UI.__init__(self)
        self.dogrid()
class EntryField(Gridded,tkinter.Entry,UI):
    def renderlabel(self,grid=False,event=None):
        v=self.get()
        if hasattr(self,'rendered'): #Get grid info before destroying old one
            mygrid=self.rendered.grid_info()
            grid=True
            self.rendered.destroy()
        self.rendered=Label(self.parent,text=v)
        d=["̀","́","̂","̌","̄","̃", "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉"]
        if set(d) & set(v):
            if grid:
                self.rendered.grid(**mygrid)
            elif hasattr(self,'rendergrid'):
                self.rendered.grid(**self.rendergrid)
            else:
                log.error("Help! I have no idea what happened!")
            delattr(self,'rendergrid')
        elif grid:
                self.rendergrid=mygrid
    def __init__(self, parent, render=False, **kwargs):
        UI.inherit(self,parent)
        self.parent=parent
        super(EntryField,self).__init__(parent,**kwargs)
        if render is True:
            self.bind('<KeyRelease>', self.renderlabel)
            self.renderlabel()
        UI.__init__(self)
        self['background']=self.theme.offwhite #because this is for entry...
        self.dogrid()
class RadioButton(tkinter.Radiobutton,UI):
    def __init__(self, parent, column=0, row=0, sticky='w', **kwargs):
        UI.inherit(self,parent)
        self.parent=parent
        if 'font' not in kwargs:
            kwargs['font']=self.theme.fonts['default']
        kwargs['activebackground']=self.theme.activebackground
        kwargs['selectcolor']=self.theme.activebackground
        super(RadioButton,self).__init__(parent,**kwargs)
        self.grid(column=column, row=row, sticky=sticky)
        UI.__init__(self)
        self.dogrid()
class RadioButtonFrame(Frame):
    def __init__(self, parent, horizontal=False,**kwargs):
        UI.inherit(self,parent)
        for vars in ['var','opts']:
            if (vars not in kwargs):
                print('You need to set {} for radio button frame!').format(vars)
            else:
                setattr(self,vars,kwargs[vars])
                del kwargs[vars] #we don't want this going to the button.
        column=0
        sticky='w'
        self.parent=parent
        super(RadioButtonFrame,self).__init__(parent,**kwargs)
        kwargs['background']=self.theme.background
        kwargs['activebackground']=self.theme.activebackground
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
class Button(Gridded,Text,tkinter.Button,UI):
    def nofn(self):
        pass
    def __init__(self, parent, choice=None, window=None, command=None, **kwargs):
        """Usta include column=0, row=1, norender=False,"""
        UI.inherit(self,parent)
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
        super(Button,self).__init__(
            parent,
            command=cmd,
            **kwargs)
        self['activebackground']=self.theme.activebackground
        self['background']=self.theme.background
        self['bg']=self.theme.background
        UI.__init__(self)
        self.dogrid()
class CheckButton(tkinter.Checkbutton,UI):
    def __init__(self, parent, **kwargs):
        self.inherit()
        super(CheckButton,self).__init__(parent,
                                bg=self.theme.background,
                                activebackground=self.theme.activebackground,
                                # bg=self.theme.background,
                                image=self.theme.photo['uncheckedbox'],
                                selectimage=self.theme.photo['checkedbox'],
                                indicatoron=False,
                                compound='left',
                                font=self.fonts['read'],
                                anchor='w',
                                **kwargs
                                )
        UI.__init__(self)
        self.dogrid()
class ButtonFrame(Frame):
    def __init__(self,parent,
                    **kwargs
                    ):
        # Gridded.__init__(self,**kwargs)
        # Childof.__init__(self,parent)
        super(ButtonFrame,self).__init__(parent,**kwargs)
        for kwarg in ['row', 'column']: #done with these
            if kwarg in kwargs:
                del kwargs[kwarg]
        gimmenull=False # When do I want a null option added to my lists? ever?
        self['background']=self.theme.background
        optionlist=kwargs['optionlist']
        command=kwargs['command']
        log.info("Buttonframe option list: {} ({})".format(optionlist,command))
        window=kwargs['window']=kwargs.get('window',None)
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
        elif optionlist[0] is dict:
            print("looks like options are already in dictionary format.")
        elif (type(optionlist[0]) is str) or (type(optionlist[0]) is int):
            """when optionlist is a list of strings/codes/integers"""
            print("looks like options are just a list of codes; making dict.")
            optionlist = [({'code':optionlist[i], 'name':optionlist[i]}
                            ) for i in range(0, len(optionlist))]
        elif type(optionlist[0]) is tuple:
            if type(optionlist[0][1]) is str:
                """when optionlist is a list of binary tuples (codes,names)"""
                print("looks like options are just a list of (codes,names) "
                        "tuples; making dict.")
                optionlist = [({'code':optionlist[i][0],
                                'name':optionlist[i][1]}
                                ) for i in range(0, len(optionlist))]
            elif type(optionlist[0][1]) is int:
                """when optionlist is a list of binary tuples (codes,counts)"""
                print("looks like options are just a list of (codes,counts) "
                        "tuples; making dict.")
                optionlist = [({'code':optionlist[i][0],
                                'description':optionlist[i][1]}
                                ) for i in range(0, len(optionlist))]
        if not 'name' in optionlist[0].keys(): #duplicate name from code.
            for i in range(0, len(optionlist)):
                optionlist[i]['name']=optionlist[i]['code']
        if gimmenull == True:
            optionlist.append(({code:"Null",name:"None of These"}))
        for choice in optionlist:
            if choice['name'] == ["Null"]:
                command=newvowel #come up with something better here..…
            if 'description' in choice:
                print(choice['name'],str(choice['description']))
                text=choice['name']+' ('+str(choice['description'])+')'
            else:
                text=choice['name']
            """commands are methods, so this normally includes self (don't
            specify it here). x= as a lambda argument allows us to assign the
            variable value now (in the loop across choices). Otherwise, it will
            maintain a link to the variable itself, and give the last value it
            had to all the buttons... --not what we want!
            """
            cmd=lambda x=choice['code'], w=window:command(x,window=w)
            b=Button(self,text=text,choice=choice['code'],
                    window=window,cmd=cmd,#width=self.width,
                    row=i,
                    **kwargs
                    )
            i=i+1
        UI.__init__(self)
class ScrollingButtonFrame(ScrollingFrame,ButtonFrame):
    """This needs to go inside another frame, for accurrate grid placement"""
    def __init__(self,parent,**kwargs):
        Gridded.__init__(self,**kwargs)
        Childof.__init__(self,parent)
        optionlist=kwargs['optionlist']
        command=kwargs['command']
        window=kwargs['window']=kwargs.get('window',None)
        ScrollingFrame.__init__(self,parent,**kwargs)
        for kwarg in ['row', 'column']: #done with these
            if kwarg in kwargs:
                del kwargs[kwarg]
        self.bf=ButtonFrame(parent=self.content,
                            optionlist=optionlist,
                            command=command,
                            window=window,
                            row=0,
                            column=0,
                            **kwargs)
        UI.__init__(self)
        self.dogrid()
class ToolTip(object):
    """
    create a tooltip for a given widget
    modified from https://stackoverflow.com/, originally from
    www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
    Modified to include a delay time by Victor Zaccardo, 25mar16
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.dispx = 25
        self.dispy = 20
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
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
        label.pack(ipadx=1)
        self.widget.bind("<Leave>", self.leave)
    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
class Wait(Window): #tkinter.Toplevel?
    def close(self):
        self.update_idletasks()
        self.parent.deiconify()
        self.destroy()
    def __init__(self, parent=None,msg=None):
        global program
        super(Wait, self).__init__(parent,exit=False)
        self.parent.withdraw()
        self.withdraw() #don't show until we're done making it
        self.attributes("-topmost", True)
        self['background']=parent['background']
        title=(_("Please Wait! {name} Dictionary and Orthography Checker "
                        "in Process").format(name=self.program['name']))
        self.title(title)
        text=_("Please Wait...")
        self.l=Label(self.outsideframe, text=text,
                font='title',anchor='c')
        self.l.grid(row=0,column=0,sticky='we')
        if msg is not None:
            self.l1=Label(self.outsideframe, text=msg,
                font='default',anchor='c')
            self.l1.grid(row=1,column=0,sticky='we')
        self.l2=Label(self.outsideframe,
                        image=self.theme.photo['small'],
                        text='',
                        )
        self.l2.grid(row=2,column=0,sticky='we',padx=50,pady=50)
        self.deiconify() #show after the window is built
        #for some reason this has to follow the above, or you get a blank window
        self.update_idletasks() #updates just geometry
class Theme(object):
    """docstring for Theme."""
    def setimages(self):
        # Program icon(s) (First should be transparent!)
        log.info("Scaling images; please wait...") #threading?
        try:
            if program: #'scale' in
                scale=program['scale']
        except NameError:
            scale=1
        # threading.Thread(target=thread_function, args=(arg1,),kwargs={'arg2': arg2})
        # if process:
        #     from multiprocessing import Process
        #     log.info("Running as multi-process")
        #     p = Process(target=block)
        # elif thread:
        #     from threading import Thread
        #     log.info("Running as threaded")
        #     p = Thread(target=block)
        # else:
        #     log.info("Running in line")
        #     block()
        # if process or thread:
        #     p.exception = None
        #     try:
        #         p.start()
        #     except BaseException as e:
        #         log.error("Exception!", traceback.format_exc())
        #         p.exception = e
        #     p.join(timeout) #finish this after timeout, in any case
        #     if p.exception:
        #         log.error("Exception2!", traceback.format_exc())
        #         raise p.exception
        #     if process:
        #         p.terminate() #for processes, not threads
        # x and y here express a float as two integers, so 0.7 = 7/10, because
        # the zoom and subsample fns only work on integers
        y=25 #10 #Higher number is better resolution (x*y/y), more time to process
        y=int(y) # These all must be integers
        x=int(scale*y)
        self.photo={}
        def mkimg(name,relurl):
            imgurl=file.fullpathname(relurl)
            if x != y: # should scale if off by >2% either way
                self.photo[name] = tkinter.PhotoImage(
                                        file = imgurl).zoom(x,x).subsample(y,y)
            else: #if close enough...
                self.photo[name] = tkinter.PhotoImage(file = imgurl)
            log.info(type(self.photo[name]))
        for name,relurl in [ ('transparent','images/AZT stacks6.png'),
                            ('small','images/AZT stacks6_sm.png'),
                            ('icon','images/AZT stacks6_icon.png'),
                            ('T','images/T alone clear6.png'),
                            ('C','images/Z alone clear6.png'),
                            ('V','images/A alone clear6.png'),
                            ('CV','images/ZA alone clear6.png'),
                            ('backgrounded','images/AZT stacks6.png'),
                            #Set images for tasks
                            ('verifyT','images/Verify List.png'),
                            ('sortT','images/Sort List.png'),
                            ('joinT','images/Join List.png'),
                            ('record','images/Microphone alone_sm.png'),
                            ('change','images/Change Circle_sm.png'),
                            ('checkedbox','images/checked.png'),
                            ('uncheckedbox','images/unchecked.png')
                        ]:
            mkimg(name,relurl)
        log.info("Done scaling images")
    def settheme(self):
        defaulttheme='greygreen'
        multiplier=99 #The default theme will be this more frequent than others.
        pot=list(self.themes.keys())+([defaulttheme]*
                                        (multiplier*len(self.themes)-1))
        self.name='Kent' #for the colorblind (to punish others...)
        self.name='highcontrast' #for low light environments
        self.name=pot[randint(0, len(pot))-1] #mostly defaulttheme
        try:
            if (platform.uname().node == 'karlap' and
                    self.program and
                    not self.program['production']):
                self.name='Kim' #for my development
        except Exception as e:
            log.info("Assuming I'm not working from main ({}).".format(e))
        """These versions might be necessary later, but with another module"""
        if self.name not in self.themes:
            print("Sorry, that theme doesn't seem to be set up. Pick from "
            "these options:",self.themes.keys())
            exit()
        for k in self.themes[self.name]:
            setattr(self,k,self.themes[self.name][k])
            log.info("Theme {}: {}".format(k,getattr(self,k)))
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
        log.info("Setting fonts with {} theme".format(fonttheme))
        try:
            if program: #'scale' in
                scale=program['scale']
        except NameError:
            scale=1
        if fonttheme == 'smaller':
            default=12*scale
        else:
            default=18*scale
        normal=int(default*4/3)
        big=int(default*5/3)
        title=bigger=int(default*2)
        small=int(default*2/3)
        default=int(default)
        log.info("Default font size: {}".format(default))
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
                'default':tkinter.font.Font(family=charis, size=default)
                    }
        """additional keyword options (ignored if font is specified):
        family - font family i.e. Courier, Times
        size - font size (in points, |-x| in pixels)
        weight - font emphasis (NORMAL, BOLD)
        slant - ROMAN, ITALIC
        underline - font underlining (0 - none, 1 - underline)
        overstrike - font strikeout (0 - none, 1 - strikeout)
        """
    def __init__(self,program=None):
        self.program=program
        self.setthemes()
        self.setfonts()
        self.setimages()
        self.settheme()
        log.info("Using {} theme ({})".format(self.name,self.program))
        super(Theme, self).__init__()
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
def availablexy(self,w=None):
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
                # These are actual the row/col after the max in span,
                # but this is what we want for range()
                sib.rowmax=sib.row+sib.grid_info()['rowspan']
                sib.colmax=sib.col+sib.grid_info()['columnspan']
                sib.rows=set(range(sib.row,sib.rowmax))
                sib.cols=set(range(sib.col,sib.colmax))
                if wrows & sib.rows == set(): #the empty set
                    sib.reqheight=sib.winfo_reqheight()
                    log.log(3,"sib {} reqheight: {}".format(sib,sib.reqheight))
                    """Give me the tallest cell in this row"""
                    if ((sib.row not in rowheight) or (sib.reqheight >
                                                            rowheight[sib.row])):
                        rowheight[sib.row]=sib.reqheight
                if wcols & sib.cols == set(): #the empty set
                    sib.reqwidth=sib.winfo_reqwidth()
                    log.log(3,"sib {} width: {}".format(sib,sib.reqwidth))
                    """Give me the widest cell in this column"""
                    if ((sib.col not in colwidth) or (sib.reqwidth >
                                                            colwidth[sib.col])):
                        colwidth[sib.col]=sib.reqwidth
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
        borderSize= 0 #not working: self.winfo_rootx() - self.winfo_x()
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
if __name__ == '__main__':
    """To Test:"""
    # loglevel='Debug'
    loglevel='INFO'
    from logsetup import *
    log=logsetup(loglevel)
