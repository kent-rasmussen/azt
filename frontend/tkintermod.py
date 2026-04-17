import sys
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
    exception_texts_to_raise=[
        'recursion',
        'local variable',
        'bad window path name'
    ]
    exception_types_to_raise=[
        # _tkinter.TclError,
        AttributeError,
        KeyError,
        NameError
    ]
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
            print(f"Shutting down system{msg}")
            # raise SystemExit(msg)
            sys.exit()
        except (KeyError,NameError,AttributeError) as e:
            raise e
        except Exception as err:
            if any(i in str(err) for i in self.exception_texts_to_raise):
                raise err
            elif any(isinstance(err,t) for t in self.exception_types_to_raise):
                raise err
            else:
                print(f"not raising {type(err)} Exception {err} (frontend.tkintermod)")
            # raise err
        except KeyboardInterrupt:
            pass