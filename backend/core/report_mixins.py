# coding=UTF-8
from utilities.utilities import *
from utilities.i18n import _
from utilities import logsetup
from backend.core.lexicon import Tone
log=logsetup.getlog(__name__)

def set_do(task,fn):
    """Adopt fn as the task's report function. These scope mixins run OUTSIDE
    Background in the MRO (their assignment lands after Background's wrap ran),
    so re-apply the background wrap here for Background variants."""
    if isinstance(task,Background):
        fn=lambda f=fn:task.background(f)
    task.do=fn
class Multislice(object):
    """This class just triggers which settings are visible to the user, and
    updates changes from child classes"""
    multislice_max=True #maybe should be an integer default value?
    def __init__(self, **kwargs):
        # ui/status/program only exist after the Task init deeper in the MRO,
        # so run the rest of the chain before touching them.
        super().__init__(**kwargs)
        self.status.redofinalbuttons() #because the fns changed
class MultisliceS(Multislice):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        set_do(self,self.basicreport)
        self.program.status.group(None)
        self.status.redofinalbuttons() #buttons capture self.do; rebuild
class MultisliceT(Multislice):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        set_do(self,self.tonegroupreportcomprehensive)
        self.status.redofinalbuttons() #buttons capture self.do; rebuild
class Multicheck(object):
    multicheckscope=True
    def __init__(self, **kwargs):
        """This should only be used for segmental checks; tone reports are
        always multiple checks"""
        super().__init__(**kwargs) #Task init first; see Multislice
        self.program.status.group(None)
        set_do(self,self.basicreport)
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
        # The concrete report classes set self.do at the END of their init
        # (after their super() call), so the chain must complete before we can
        # read — let alone wrap — it.
        super().__init__(**kwargs)
        log.info("Setting up background report, based on {name}"
                "".format(name=self.do.__name__))
        self.do=lambda fn=self.do:self.background(fn)
        self.status.redofinalbuttons() #because the fns changed
