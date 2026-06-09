# coding=UTF-8
from frontend import ui
from utilities.i18n import _
from utilities import logsetup
log = logsetup.getlog(__name__)

class ErrorNotice(ui.Window):
    """this is for things that I want the user to know, without having
    to find it in the logs."""
    """kwarg button is a tuple: (text,command)"""
    def destroy(self, event=None):
        ui.Window.destroy(self)
    def withdraw(self, event=None):
        ui.Window.withdraw(self)
    def __init__(self, text, **kwargs):
        if not text:
            log.error(_("ErrorNotice got no text?"))
            return
        #use parent window if given, else parent.self.program.tk_root, else ui.Root()
        if not (parent:=kwargs.get('parent')):
            if kwargs.get('program') and kwargs['program'].tk_root:
                parent=kwargs['program'].tk_root
            else:
                # Reuse the existing app root if there is one. Creating a
                # *second* Tk() here (the old behaviour) spawns a separate
                # interpreter whose theme images/fonts don't belong to the
                # running app — an ErrorNotice with image='USBdrive' then raised
                # `image "pyimageNNN" doesn't exist`, and the two roots fought
                # over font scaling (error page rendered hugely oversized).
                # Only make a fresh Root when none exists (very early startup).
                parent = ui.default_root() or ui.Root()
        if parent.exitFlag.istrue():
            log.error(_("Parent window is exiting; error message follows"))
            log.error(text)
            return
        title=kwargs.get('title',_("Error!"))
        wait=kwargs.get('wait')
        button=kwargs.get('button')
        image=kwargs.get('image')
        super(ErrorNotice, self).__init__(parent,title=title,exit=False,withdrawn=True)
        if hasattr(self,'theme'):
            self['background']=self.theme.background
        else:
            log.error(f"ErrorNotice has no theme! parent={type(parent).__name__}")
        self.parent.withdraw()
        # self.title = title
        self.text = text
        l=ui.Label(self.frame, text=text,
                    image=image,
                    compound='left',
                    row=0, column=1,
                    columnspan=2,
                    ipadx=25)
        l.wrap()
        if button and type(button) is tuple:
            b=ui.Button(self.frame, text=button[0],
                    cmd=None,
                    row=1, column=1, sticky='e')
            b.bind('<ButtonRelease>',self.withdraw)
            b.bind('<ButtonRelease>',button[1],add='+')
            b.bind('<ButtonRelease>',self.destroy,add='+')
        b=ui.Button(self.frame, text=_("OK"),
                cmd=self.on_quit,
                row=1, column=2, sticky='nse')
        self.attributes("-topmost", True)
        self.deiconify()
        self.update_idletasks()  # force geometry/paint before wait_window
        if wait:
            self.wait_window(self)
        if self.exitFlag.istrue():
            return
        if not isinstance(self.parent,ui.Root):
            self.parent.deiconify()
        # self.pull() # in case there's a source available
