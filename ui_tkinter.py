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
    def __init__(self, parent, *args, **kwargs): #because this is used everywhere.
        """this removes gridding kwargs from the widget calls"""
        log.info("Gridded parent: {}".format(parent))
        log.info("Gridding? ({})".format(kwargs))
        grid=False
        if set(kwargs) & set(['sticky','row','column','columnspan','padx','pady']):
            grid=True
            self.sticky=kwargs.pop('sticky',"ew")
            self.row=kwargs.pop('row',kwargs.pop('r',0))
            self.column=kwargs.pop('column',kwargs.pop('col',kwargs.pop('c',0)))
            self.columnspan=kwargs.pop('columnspan',1)
            self.rowspan=kwargs.pop('rowspan',1)
            self.padx=kwargs.pop('padx',0)
            self.pady=kwargs.pop('pady',0)
            self.ipadx=kwargs.pop('ipadx',0)
            self.ipady=kwargs.pop('ipady',0)
        super(Gridded, self).__init__(parent, *args, **kwargs)
        if grid:
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
        else:
            log.info("Not Gridding! ({})".format(kwargs))
class UI(ObectwArgs):
    """docstring for Widget."""
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
class Frame(tkinter.Frame,UI):
            if hasattr(parent,attr):
                setattr(self,attr,getattr(parent,attr))
            else:
                log.info("parent doesn't have attr {}, skipping inheritance"
                        "".format(attr))
    def __init__(self, *args, **kwargs): #because this is used everywhere.
        log.info("Initializing UI object")
        if hasattr(self,'theme'):
            try:
                self['background']=self.theme.background
                self['bg']=self.theme.background
                self['foreground']=self.theme.background
                self['activebackground']=self.theme.activebackground
            except TypeError as e:
                log.info("TypeError {}".format(e))
        super(UI, self).__init__(*args, **kwargs)
class Root(tkinter.Tk,UI):
    """docstring for Root."""
    def settheme(self,theme):
        self.theme=theme
        self['background']=self.theme.background
        self['bg']=self.theme.background
    def __init__(self, *args, **kwargs):
        self.exitFlag = ExitFlag()
        super(Root, self).__init__()
        self.protocol("WM_DELETE_WINDOW", lambda s=self: Window.on_quit(s))
class Toplevel(tkinter.Toplevel,UI): #NoParent
    def __init__(self, parent, *args, **kwargs):
        log.info("Initializing Toplevel object")
        log.info("Toplevel parent: {}".format(parent))
        UI.inherit(self,parent)
        super(Toplevel, self).__init__(parent)
        self['background']=self.theme.background
        self['bg']=self.theme.background
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
        self.parent = parent
        # for attr in ['fonts','theme','debug','wraplength','photo','renderings',
        #         'program','exitFlag']:
        #     if hasattr(parent,attr):
        #         setattr(self,attr,getattr(parent,attr))
        self.inherit()
        """tkinter.Frame thingies below this"""
        tkinter.Frame.__init__(self,parent,**kwargs)
        self['background']=parent['background']
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
    def __init__(self,parent,xscroll=False):
        """Make this a Frame, with all the inheritances, I need"""
        self.parent=parent
        # inherit(self)
        Frame.__init__(self,parent)
        """Not sure if I want these... rather not hardcode."""
        # log.debug(self.parent.winfo_children())
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        """With or without the following, it still scrolls through..."""
        self.grid_propagate(0) #make it not shrink to nothing

        """We might want horizonal bars some day? (also below)"""
        if xscroll == True:
            xscrollbar = tkinter.Scrollbar(self, orient=tkinter.HORIZONTAL)
            xscrollbar.grid(row=1, column=0, sticky=tkinter.E+tkinter.W)
        yscrollbar = tkinter.Scrollbar(self)
        yscrollbar.grid(row=0, column=1, sticky=tkinter.N+tkinter.S)
        """Should decide some day which we want when..."""
        self.yscrollbarwidth=50 #make the scrollbars big!
        self.yscrollbarwidth=0 #make the scrollbars invisible (use wheel)
        self.yscrollbarwidth=15 #make the scrollbars useable, but not obnoxious
        yscrollbar.config(width=self.yscrollbarwidth)
        yscrollbar.config(background=self.theme['background'])
        yscrollbar.config(activebackground=self.theme['activebackground'])
        yscrollbar.config(troughcolor=self.theme['background'])
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
            xscrollbar.config(background=self.theme['background'])
            xscrollbar.config(activebackground=self.theme['activebackground'])
            xscrollbar.config(troughcolor=self.theme['background'])
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
    def resetframe(self):
        if self.parent.exitFlag.istrue():
            return
        if self.winfo_exists(): #If this has been destroyed, don't bother.
            if hasattr(self,'frame') and type(self.frame) is Frame:
                self.frame.destroy()
            self.frame=Frame(self.outsideframe)
            self.frame.grid(column=0,row=0,sticky='nsew')
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
        self.parent=parent
        """Things requiring tkinter.Window below here"""
        super(Window, self).__init__(parent)
        # self.config(className="azt")
        self['background']=self.theme['background']
        """Is this section necessary for centering on resize?"""
        for rc in [0,2]:
            self.grid_rowconfigure(rc, weight=3)
            self.grid_columnconfigure(rc, weight=3)
        self.outsideframe=Frame(self)
        """Give windows some margin"""
        self.outsideframe['padx']=25
        self.outsideframe['pady']=25
        self.outsideframe.grid(row=1, column=1,sticky='we')
        self.iconphoto(False, self.photo['icon']) #don't want this transparent
        self.title(title)
        self.resetframe()
        self.exitFlag=ExitFlag() #This overwrites inherited exitFlag
        if exit is True:
            e=(_("Exit")) #This should be the class, right?
            self.exitButton=tkinter.Button(self.outsideframe, width=10, text=e,
                                command=self.on_quit,
                                activebackground=self.theme['activebackground'],
                                background=self['background']
                                            )
            self.exitButton.grid(column=2,row=2)
        if backcmd is not False: #This one, too...
            b=(_("Back"))
            cmd=lambda:backcmd(parent, window, check, entry, choice)
            self.backButton=tkinter.Button(self.outsideframe, width=10, text=b,
                                command=cmd,
                                activebackground=self.theme['activebackground'],
                                background=self.theme['background']
                                            )
            self.backButton.grid(column=3,row=2)
class Menu(tkinter.Menu,UI):
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
        super().__init__(parent,**kwargs)
        self.parent=parent
        self.inherit()
        self['font']=self.fonts['default']
        #Blend with other widgets:
        # self['activebackground']=self.theme['activebackground']
        # self['background']=self.theme['background']
        # stand out from other widgets:
        self['activebackground']=self.theme['background']
        self['background']='white'
class ContextMenu(UI):
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
        UI.inherit(self.root)
    def __init__(self,parent,context=None):
        self.parent=parent
        self.parent.context=self
        self.context=context #where the menu is showing (e.g., verifyT)
        self.inherit()
        self.getroot()
        self.updatebindings()
class Renderer(object):
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
                if w>wraplength:
                    words.insert(y+nl-1,'\n')
                    x=y-1
                    nl+=1
            line=' '.join(words) #Join back words
            lines[li]=line
        text='\n'.join(lines) #join back sections between manual linebreaks
        log.debug(text)
        w, h = draw.multiline_textsize(text, font=font, spacing=fspacing)
        log.log(2,"Final size w: {}, h: {}".format(w,h))
        black = 'rgb(0, 0, 0)'
        white = 'rgb(255, 255, 255)'
        img = PIL.Image.new("RGBA", (w+xpad, h+ypad), (255, 255, 255,0 )) #alpha
        draw = PIL.ImageDraw.Draw(img)
        draw.multiline_text((0+xpad//2, 0+ypad//4), text,font=font,fill=black,
                                                                align=align)
        self.img = PIL.ImageTk.PhotoImage(img)
class Label(tkinter.Label,UI):
    def wrap(self):
        availablexy(self)
        self.config(wraplength=self.maxwidth)
        log.log(3,'self.maxwidth (Label class): {}'.format(self.maxwidth))
    def __init__(self, parent, column=0, row=1, norender=False,**kwargs):
        """These have non-None defaults"""
        self.parent=parent
        if 'text' not in kwargs or kwargs['text'] is None:
            kwargs['text']=''
        if 'font' in kwargs:
            if isinstance(kwargs['font'],tkinter.font.Font):
                pass #use as is
            elif kwargs['font'] in parent.fonts: #if font key (e.g., 'small')
                kwargs['font']=parent.fonts[kwargs['font']] #change key to font
            else:
                kwargs['font']=parent.fonts['default']
        else:
            kwargs['font']=parent.fonts['default']
        self.inherit()
        if hasattr(self,'wraplength'):
            defaultwr=self.wraplength
        else:
            defaultwr=0
        kwargs['wraplength']=kwargs.get('wraplength',defaultwr)
        d=set(["̀","́","̂","̌","̄","̃", "᷉","̋","̄","̏","̌","̂","᷄","᷅","̌","᷆","᷇","᷉"])
        sticks=set(['˥','˦','˧','˨','˩',' '])
        if set(kwargs['text']) & (sticks|d) and not norender:
            # log.info(kwargs['font']['size'])
            style=(kwargs['font']['family'], # from kwargs['font'].actual()
                    kwargs['font']['size'],kwargs['font']['weight'],
                    kwargs['font']['slant'],kwargs['font']['underline'],
                    kwargs['font']['overstrike'])
            # log.info("style: {}".format(style))
            renderings=self.parent.renderings
            # log.info("renderings: {}".format(renderings))
            if style not in renderings:
                renderings[style]={}
            if kwargs['wraplength'] not in renderings[style]:
                renderings[style][kwargs['wraplength']]={}
            thisrenderings=renderings[style][kwargs['wraplength']]
            if (kwargs['text'] in thisrenderings and
                    thisrenderings[kwargs['text']] is not None):
                log.log(5,"text {} already rendered with {} wraplength, using."
                        "".format(kwargs['text'],kwargs['wraplength']))
                kwargs['image']=thisrenderings[kwargs['text']]
                kwargs['text']=''
            elif 'image' in kwargs and kwargs['image'] is not None:
                log.error("You gave an image and tone characters in the same "
                "label? ({},{})".format(image,kwargs['text']))
                return
            else:
                log.log(5,"Sticks found! (Generating image for label)")
                i=Renderer(**kwargs)
                self.tkimg=i.img
                if self.tkimg is not None:
                    thisrenderings[kwargs['text']]=kwargs['image']=self.tkimg
                    kwargs['text']=''
        else:
            kwargs['text']=nfc(kwargs['text'])
        tkinter.Label.__init__(self, parent, **kwargs)
        self['background']=kwargs.get('background',self.theme['background'])
class EntryField(tkinter.Entry,UI):
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
        self.parent=parent
        self.inherit()
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['default']
        super().__init__(parent,**kwargs)
        if render is True:
            self.bind('<KeyRelease>', self.renderlabel)
            self.renderlabel()
        self['background']=self.theme['offwhite'] #because this is for entry...
class RadioButton(tkinter.Radiobutton,UI):
    def __init__(self, parent, column=0, row=0, sticky='w', **kwargs):
        self.parent=parent
        self.inherit()
        if 'font' not in kwargs:
            kwargs['font']=self.fonts['default']
        kwargs['activebackground']=self.theme['activebackground']
        kwargs['selectcolor']=self.theme['activebackground']
        super().__init__(parent,**kwargs)
        self.grid(column=column, row=row, sticky=sticky)
class RadioButtonFrame(Frame):
    def __init__(self, parent, horizontal=False,**kwargs):
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
        kwargs['background']=self.theme['background']
        kwargs['activebackground']=self.theme['activebackground']
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
class Button(tkinter.Button,UI):
    def nofn(self):
        pass
    def __init__(self, parent, choice=None, window=None,
                command=None, column=0, row=1, norender=False,**kwargs):
        self.parent=parent
        self.inherit()
        """For button"""
        if 'anchor' not in kwargs:
            kwargs['anchor']="w"
        if 'text' not in kwargs:
            kwargs['text']=''
        if 'wraplength' not in kwargs:
            kwargs['wraplength']=parent.wraplength
        if 'font' in kwargs:
            if isinstance(kwargs['font'],tkinter.font.Font):
                pass #use as is
            elif kwargs['font'] in parent.fonts: #if font key (e.g., 'small')
                kwargs['font']=parent.fonts[kwargs['font']] #change key to font
            else:
                kwargs['font']=parent.fonts['default']
        else:
            kwargs['font']=parent.fonts['default']
        """For image rendering of button text"""
        sticks=set(['˥','˦','˧','˨','˩',' '])
        if set(kwargs['text']) & sticks and not norender:
            style=(kwargs['font']['family'], # from kwargs['font'].actual()
                    kwargs['font']['size'],kwargs['font']['weight'],
                    kwargs['font']['slant'],kwargs['font']['underline'],
                    kwargs['font']['overstrike'])
            # log.info("style: {}".format(style))
            renderings=self.parent.renderings
            # log.info("renderings: {}".format(renderings))
            if style not in renderings:
                renderings[style]={}
            if kwargs['wraplength'] not in renderings[style]:
                renderings[style][kwargs['wraplength']]={}
            thisrenderings=renderings[style][kwargs['wraplength']]
            if (kwargs['text'] in thisrenderings and
                    thisrenderings[kwargs['text']] is not None):
                log.log(5,"text {} already rendered with {} wraplength, using."
                        "".format(kwargs['text'],kwargs['wraplength']))
                kwargs['image']=thisrenderings[kwargs['text']]
                kwargs['text']=''
            elif 'image' in kwargs and kwargs['image'] is not None:
                log.error("You gave an image and tone characters in the same "
                "button text? ({},{})".format(image,kwargs['text']))
                return
            else:
                log.log(5,"sticks found! (Generating image for button)")
                i=Renderer(**kwargs)
                self.tkimg=i.img
                if self.tkimg is not None:
                    thisrenderings[kwargs['text']]=kwargs['image']=self.tkimg
                    kwargs['text']=''
        kwargs['text']=nfc(kwargs['text'])
        """For Grid"""
        if 'sticky' in kwargs:
            sticky=kwargs['sticky']
            del kwargs['sticky'] #we don't want this going to the button.
        else:
            sticky="W"+"E"
        kwargs['activebackground']=self.theme['activebackground']
        kwargs['background']=self.theme['background']
        if self.debug == True:
            for arg in kwargs:
                print("Button "+arg+": "+kwargs[arg])
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
        tkinter.Button.__init__(self, parent, command=cmd, **kwargs)
        self.grid(column=column, row=row, sticky=sticky)
class CheckButton(tkinter.Checkbutton,UI):
    def __init__(self, parent, **kwargs):
        self.parent=parent
        self.inherit()
        super(CheckButton,self).__init__(parent,
                                bg=self.theme['background'],
                                activebackground=self.theme['activebackground'],
                                image=self.photo['uncheckedbox'],
                                selectimage=self.photo['checkedbox'],
                                indicatoron=False,
                                compound='left',
                                font=self.fonts['read'],
                                anchor='w',
                                **kwargs
                                )
class ButtonFrame(Frame):
    def __init__(self,parent,
                    optionlist,command,
                    window=None,
                    **kwargs
                    ):
        self.parent=parent
        Frame.__init__(self,parent)
        gimmenull=False # When do I want a null option added to my lists? ever?
        self['background']=self.theme['background']
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
            if 'description' in choice.keys():
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
class ScrollingButtonFrame(ScrollingFrame,ButtonFrame):
    """This needs to go inside another frame, for accurrate grid placement"""
    def __init__(self,parent,optionlist,command,window=None,**kwargs):
        ScrollingFrame.__init__(self,parent)
        self.bf=ButtonFrame(parent=self.content,
                            optionlist=optionlist,
                            command=command,
                            window=window,
                            **kwargs)
        self.bf.grid(row=0, column=0)
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
        self.parent=parent
        self.parent.withdraw()
        global program
        super(Wait, self).__init__(parent,exit=False)
        self.withdraw() #don't show until we're done making it
        self.attributes("-topmost", True)
        self['background']=parent['background']
        self.photo = parent.photo #need this before making the frame
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
        self.l2=Label(self.outsideframe, image=self.photo['small'],text='',
                        bg=self['background']
                        )
        self.l2.grid(row=2,column=0,sticky='we',padx=50,pady=50)
        self.deiconify() #show after the window is built
        #for some reason this has to follow the above, or you get a blank window
        self.update_idletasks() #updates just geometry
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
    try: #Any kind of error making a widget often shows up here
        wrow=w.grid_info()['row']
    except:
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
        if sib.winfo_class() not in ['Menu','Wait','Window']:
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
    if w.parent.winfo_class() not in ['Toplevel','Tk','Wait']:
        if hasattr(w.parent,'grid_info'): #one of these should be sufficient
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
        self.maxheight=self.parent.winfo_screenheight()-self.otherrowheight
        self.maxwidth=self.parent.winfo_screenwidth()-self.othercolwidth #+600
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
    a=tkinter.Widget()
    """To Test:"""
    # loglevel='Debug'
    loglevel='INFO'
    from logsetup import *
    log=logsetup(loglevel)
