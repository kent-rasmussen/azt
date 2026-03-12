# coding=UTF-8
from tasks.base import Task
from backend.core.alphabet import AlphabetChartData
from frontend.alphabet_chart import OrderAlphabetUI
from utilities.utilities import LazyGlobal
from utilities import logsetup
log = logsetup.getlog(__name__)

def __getattr__(name):
    if name in ('_',):
        import main
        return getattr(main, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

for name in ('_',):
    if name not in globals():
        globals()[name] = LazyGlobal(name)

class AlphabetChart(Task, AlphabetChartData, OrderAlphabetUI):
    my_settings = [
                    'exids',
                    # 'order',
                    'ncolumns', 'chart_title',
                    'copyright',
                    'pagesize'
                ] + AlphabetChartData.my_settings
    def taskicon(self):
        return self.program.theme.photo['alpha_icon']
    def tooltip(self):
        return _("This task helps you organize an alphabet and select words "
            "with pictures to represent each letter.")
    def tasktitle(self):
        return _("Alphabet Chart")
    def save_settings(self):
        for k in self.my_settings:
            value = getattr(self, k)
            from frontend import ui_tkinter as ui
            if isinstance(value, ui.Variable):
                value = value.get()
                log.info(_("found '{key}' ui.Variable: {value}").format(key=k, value=value))
            else:
                log.info(_("Didn't find '{key}' ui.Variable: {value}").format(key=k, value=value))
            getattr(self.program.settings, 'alpha_' + k)(value)
        self.program.settings.storesettingsfile(setting='alphabet')
    def __init__(self, program):
        self.program=program
        Task.__init__(self, program)
        title = _("Alphabet Chart UI for Glyph Ordering and Selection")
        self.init_chart_data(program)
        # hide_vars requires ui.BooleanVar — set up here, not in backend data class
        from frontend import ui_tkinter as ui
        self.hide_vars = {g: ui.BooleanVar(value=False) for g in self.order}
        for i in self.hide_vars.values():
            i.trace_add('write', self.update_shown)
        OrderAlphabetUI.__init__(self, self.program.taskchooser)
        self.mainwindow = False  # don't exit on close
