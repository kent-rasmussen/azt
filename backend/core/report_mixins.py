# coding=UTF-8
from utilities.utilities import *
from utilities import logsetup
from backend.core.lexicon import Tone
log=logsetup.getlog(__name__)

def __getattr__(name):
    # Lazy load globals from main
    if name in ('_',):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('_',):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

class Multislice(object):
    """This class just triggers which settings are visible to the user, and
    updates changes from child classes"""
    multislice_max=True #maybe should be an integer default value?
    def __init__(self, **kwargs):
        # log.info("Setting up Multislice report, with {dir}".format(dir=dir()))
        """I think these two should go:"""
        self.status.redofinalbuttons() #because the fns changed
class MultisliceS(Multislice):
    def __init__(self, **kwargs):
        self.do=self.basicreport
        self.program.status.group(None)
        super().__init__(**kwargs)
class MultisliceT(Multislice):
    def __init__(self, **kwargs):
        self.do=self.tonegroupreportcomprehensive
        super().__init__(**kwargs)
class Multicheck(object):
    multicheckscope=True
    def __init__(self, **kwargs):
        """This should only be used for segmental checks; tone reports are
        always multiple checks"""
        self.program.status.group(None)
        log.info("Setting up Multicheck report, based on {dir}".format(dir=dir()))
        self.do=self.basicreport
        self.status.redofinalbuttons() #because the fns changed
class Multicheckslice(Multicheck,MultisliceS):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
class ByUF(Tone):
    byUFgroup=True
    def __init__(self, **kwargs):
        super().__init__(**kwargs) #Nothing here; just make methods available
        log.info("doing report by UF groups")
class Background(object):
    """This class runs a report function in the background, where possible"""
    def __init__(self, **kwargs):
        log.info("Setting up background report, based on {name}"
                "".format(name=self.do.__name__))
        self.do=lambda fn=self.do:self.background(fn)
        self.status.redofinalbuttons() #because the fns changed
        super().__init__(**kwargs)
