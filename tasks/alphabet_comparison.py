# coding=UTF-8
from backend.core.alphabet import AlphabetComparisonData
from frontend.alphabet_comparison import PageSetupUI
from utilities.i18n import _
from utilities import logsetup
log = logsetup.getlog(__name__)

class AlphabetComparisonPages(AlphabetComparisonData, PageSetupUI):
    """A report-style task whose UI IS its own setup window (PageSetupUI). Like
    AlphabetChart it deliberately does NOT inherit Task (which would build a
    redundant TaskWindow 'main page' and make it the app main window, so closing
    it quit AZT). The chooser opens this window directly; closing it (X) returns
    to the chooser like the Tasks/Reports button (gettask)."""
    my_settings = [
                    'comparison_exids',
                    # 'order',
                    # 'ncolumns', 'chart_title',
                    'pagesize'
                ]
    taskicon = 'alpha_page_icon'
    is_report = True
    def tooltip(self):
        return _("This task helps you compare alphabet letters with example words "
            "and pictures to represent each letter.")
    tasktitle = "Alphabet Comparison Pages"
    def save_settings(self):
        for k in self.my_settings:
            value = getattr(self, k)
            from frontend import ui
            if isinstance(value, ui.Variable):
                value = value.get()
                log.info(_("found '{key}' ui.Variable: {value}").format(key=k, value=value))
            else:
                log.info(_("Didn't find '{key}' ui.Variable: {value}").format(key=k, value=value))
            getattr(self.program.settings, 'alpha_' + k)(value)
        self.program.settings.storesettingsfile(setting='alphabet')
    def __init__(self, program):
        self.program=program
        # This task IS its config window. Register as the current task and point
        # .ui at self so chooser.gettask() can tear this window down via
        # program.task.ui.on_quit().
        self.program.task = self
        self.ui = self
        self.selected_cover_path = None
        self.selected_logo_path = None
        self.init_comparison_data()
        # Hide the chooser while the setup page is open; closing the page
        # returns to it (below), so it is restored then.
        self.program.taskchooser.ui.withdraw()
        PageSetupUI.__init__(self, self.program.taskchooser)
        self.mainwindow = False  # not the app main window — don't quit on close
        # Closing the page routes back to the chooser like the Tasks/Reports
        # button (gettask), which tears this window down via finish_task_ui.
        self.protocol("WM_DELETE_WINDOW", self.program.taskchooser.gettask)
