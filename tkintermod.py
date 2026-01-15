class TkErrorCatcher:

    '''
    Original code from https://stackoverflow.com/questions/35388271/how-to-handl
    e-errors-in-tkinter-mainloop
    In some cases tkinter will only print the traceback.
    Enables the program to catch tkinter errors normally

    To use
    import tkinter
    tkinter.CallWrapper = TkErrorCatcher

    CAUTION: this hides Tk errors from the user, so use it in production, 
    not development.
    '''

    def __init__(self, func, subst, widget):
        self.func = func
        self.subst = subst
        self.widget = widget

    def __call__(self, *args):
        # print(f"{self.func=} {self.subst=} {self.widget=}")
        try:
            if self.subst:
                args = self.subst(*args)
            return self.func(*args)
        except SystemExit as msg:
            print(f"not raising {msg}")
            # raise SystemExit(msg)
        except Exception as err:
            raise err
