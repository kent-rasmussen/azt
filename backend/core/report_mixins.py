# coding=UTF-8
from utilities.utilities import *
from utilities import logsetup
from backend.core.lexicon import Tone
log=logsetup.getlog(__name__)

def __getattr__(name):
    # Lazy load globals from main
    if name in ('counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Mirror main globals lazily to allow bare-name access
for name in ('counts', 'me', '_', 'ErrorNotice', 'askerror', 'sysrestart', 'pythonmodules', 'findexecutable', 'main', 'testversion', 'reverttomain', 'buttonwraplength', 'regexdict', 'interfacelang', 'nowruntime', 'callerfn', 'logfinished', 'nn', 'unlist', 'xlp', 'rx', 'exampletype', 'dictofchilddicts', 'dictscompare', 'flatten', 'grouptype', 't', 'openweburl', 'isinterneturl', 'scaleimageifthere', 'loadCAWL', 'saveimagefile', 'ImageFrame', 'TranscribeC', 'TranscribeV', 'TranscribeS', 'ResultWindow', 'Multislice', 'Multicheck', 'Segments', 'ToneFrames', 'CheckParameters', 'Glosslangs', 'Senses', 'WordCollection', 'Parse', 'Sort', 'HasMenus', 'Menus', 'StatusFrame', 'TaskDressing', 'TaskChooser', 'Repository', 'Mercurial', 'Git', 'GitReadOnly', 'Analysis', 'SliceDict', 'StatusDict', 'ExampleDict', 'DictbyLang', 'Settings', 'Entry', 'updateazt', 'LiftChooser', 'SortGroupButtonFrame'):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

class Multislice(object):
    """This class just triggers which settings are visible to the user, and
    updates changes from child classes"""
    def __init__(self):
        # log.info("Setting up Multislice report, with {dir}".format(dir=dir()))
        """I think these two should go:"""
        self.status.redofinalbuttons() #because the fns changed
class MultisliceS(Multislice):
    def __init__(self):
        self.do=self.basicreport
        self.program.status.group(None)
        Multislice.__init__(self)
class MultisliceT(Multislice):
    def __init__(self):
        self.do=self.tonegroupreportcomprehensive
        Multislice.__init__(self)
class Multicheck(object):
    def __init__(self):
        """This should only be used for segmental checks; tone reports are
        always multiple checks"""
        self.program.status.group(None)
        log.info("Setting up Multicheck report, based on {dir}".format(dir=dir()))
        self.do=self.basicreport
        self.status.redofinalbuttons() #because the fns changed
class Multicheckslice(Multicheck,MultisliceS):
    def __init__(self):
        Multicheck.__init__(self)
        MultisliceS.__init__(self)
class ByUF(Tone):
    def __init__(self):
        Tone.__init__(self) #Nothing here; just make methods available
        self.byUFgroup=True
        log.info("doing report by UF groups")
class Background(object):
    """This class runs a report function in the background, where possible"""
    def __init__(self):
        log.info("Setting up background report, based on {name}"
                "".format(name=self.do.__name__))
        self.do=lambda fn=self.do:self.background(fn)
        self.status.redofinalbuttons() #because the fns changed
