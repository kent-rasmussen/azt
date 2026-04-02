# coding=UTF-8
from tasks.base import Task
from backend.core.alphabet import AlphabetComparisonData
from frontend.alphabet_comparison import PageSetupUI
from utilities.i18n import _
from utilities import logsetup
log = logsetup.getlog(__name__)

class AlphabetComparisonPages(Task, AlphabetComparisonData, PageSetupUI):
    my_settings = [
                    'comparison_exids',
                    # 'order',
                    # 'ncolumns', 'chart_title',
                    'pagesize'
                ]
    taskicon = 'iconTranscribeV'
    def tooltip(self):
        return _("This task helps you compare alphabet letters with example words "
            "and pictures to represent each letter.")
    tasktitle = "Alphabet Comparison Pages"
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
        self.selected_cover_path = None
        self.selected_logo_path = None
        self.init_comparison_data()
        PageSetupUI.__init__(self, self.program.taskchooser)
        self.mainwindow = False  # don't exit on close
