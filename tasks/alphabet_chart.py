# coding=UTF-8
from backend.core.alphabet import AlphabetChartData
from frontend.alphabet_chart import OrderAlphabetUI
from utilities.i18n import _
from utilities import logsetup
log = logsetup.getlog(__name__)

class AlphabetChart(AlphabetChartData, OrderAlphabetUI):
    """A report-style task whose UI IS its own configuration window
    (OrderAlphabetUI). It deliberately does NOT inherit Task: a Task builds a
    generic TaskWindow 'main page' and makes it the app main window, so a second,
    pointless page appeared for this report and closing it quit AZT. Here the
    chooser opens this window directly; closing it (X) returns to the chooser
    exactly like the Tasks/Reports button (gettask), instead of quitting."""
    my_settings = [
                    'exids',
                    # 'order',
                    'ncolumns', 'chart_title',
                    'copyright',
                    'pagesize'
                ] + AlphabetChartData.my_settings
    taskicon = 'alpha_chart_icon'
    is_report = True
    def tooltip(self):
        return _("This task helps you organize an alphabet and select words "
            "with pictures to represent each letter.")
    tasktitle = "Alphabet Chart"
    def save_settings(self):
        for k in self.my_settings:
            value = getattr(self, k)
            from frontend import ui
            if isinstance(value, ui.Variable):
                value = value.get()
                log.info(_("found ‘{key}’ ui.Variable: {value}").format(key=k, value=value))
            else:
                log.info(_("Didn’t find ‘{key}’ ui.Variable: {value}").format(key=k, value=value))
            getattr(self.program.settings, 'alpha_' + k)(value)
        self.program.settings.storesettingsfile(setting='alphabet')
    def __init__(self, program):
        self.program=program
        # This task IS its config window. Register as the current task and point
        # .ui at self so chooser.gettask() can tear this window down via
        # program.task.ui.on_quit().
        self.program.task = self
        self.ui = self
        # SAY SO AND GO BACK, rather than opening a chart of nothing. A
        # language with no glyphs recorded raised `KeyError: 'nm1'` from deep
        # inside the data build (Kim, Windows, 2026-09-24), which is a
        # traceback where the honest answer is one sentence. An EMPTY chart
        # would be worse than the notice: it looks broken, and the user
        # cannot tell "nothing here yet" from "this feature is failing".
        from backend.core.alphabet import NoAlphabetData
        try:
            self.init_chart_data()
        except NoAlphabetData as e:
            # RETURN, DO NOT RAISE. `chooser.maketask` calls this constructor
            # with no handler, so an exception here reaches the Tk error
            # catcher and the user gets an error SCREEN — which is the
            # traceback again in a nicer frame. Returning leaves the chooser
            # up, which is where they already were.
            from utilities.error_handler import notify_user
            names = getattr(self.program.settings, 'languagenames', {}) or {}
            log.info("Alphabet Chart not opened: %s", e)
            notify_user(_("There is no alphabet to chart for {lang} yet.\n\n"
                          "The chart is built from the letters found in your "
                          "words, so it appears once some words have been "
                          "entered and sorted. Nothing is wrong with this "
                          "database.").format(
                              lang=names.get(e.analang, e.analang)),
                        title=_("Nothing to chart yet"))
            self.program.task = None
            return
        # A read-only webview PREVIEW of this page ran here briefly
        # (2026-09-14, --serve=alphabet_chart) and proved the point it was
        # built for: the same chart, real data, ~0s against this page's 37-42s
        # under Tk (agenda/wayland_freeze_audit.md). Removed with the rest of
        # the mixed-mode code — ADR 0004 amendment — because the decision is
        # now two complete backends, so this page gets ported in-process
        # rather than served.
        # hide_vars requires ui.BooleanVar — set up here, not in backend data class
        from frontend import ui
        self.hide_vars = {g: ui.BooleanVar(value=False) for g in self.order}
        for i in self.hide_vars.values():
            i.trace_add('write', self.update_shown)
        # Hide the chooser while the config page is open; closing the page
        # returns to it (below), so it is restored then.
        self.program.taskchooser.ui.withdraw()
        OrderAlphabetUI.__init__(self, self.program.taskchooser)
        self.mainwindow = False  # not the app main window — don't quit on close
        # Closing the page routes back to the chooser like the Tasks/Reports
        # button (gettask), which tears this window down via finish_task_ui.
        self.protocol("WM_DELETE_WINDOW", self.program.taskchooser.gettask)
