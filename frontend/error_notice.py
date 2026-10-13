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
            # A COMMAND, NOT A '<ButtonRelease>' BINDING. The bare event name
            # never fired under webview, so the notice's action button was
            # drawn and did nothing ("Use this folder for collaboration",
            # Kent 2026-10-13: "there, but nonfunctional"); OK beside it, a
            # command, worked. Close first, then act — the action may open
            # its own notice or restart the app.
            action=button[1]
            # Some handlers here were written for the event argument
            # (`lambda event, x=…`), others take none: ask the signature
            # rather than retrying on TypeError, which would run a handler
            # twice if it raised one itself.
            import inspect
            try:
                inspect.signature(action).bind()
                wants_event=False
            except TypeError:
                wants_event=True
            except ValueError: #no signature (builtins): assume none
                wants_event=False
            def _act(*args):
                try:
                    self.withdraw()
                except Exception:
                    pass
                try:
                    if wants_event:
                        action(args[0] if args else None)
                    else:
                        action()
                finally:
                    try:
                        self.destroy()
                    except Exception:
                        pass
            b=ui.Button(self.frame, text=button[0],
                    cmd=_act,
                    row=1, column=1, sticky='e')
        b=ui.Button(self.frame, text=_("OK"),
                cmd=self.on_quit,
                row=1, column=2, sticky='nse')
        self.attributes("-topmost", True)
        self.deiconify()
        # Keyboard escape hatch (Return/Escape) — handy if a dialog ever fails to
        # paint its OK button.
        self.bind('<Return>', lambda e: self.on_quit())
        self.bind('<Escape>', lambda e: self.on_quit())
        self.update_idletasks() # paint before wait_window
        if wait:
            self.wait_window(self)
        if self.exitFlag.istrue():
            return
        if not isinstance(self.parent,ui.Root):
            self.parent.deiconify()
        # self.pull() # in case there's a source available
