# coding=UTF-8
"""UI presenter for VCS (version control) operations.

Backend vcs.py delegates all UI widget creation here, so it has
zero frontend imports at either module or function level.
"""
from frontend import ui
from utilities.i18n import _


class VCSPresenter:
    """Handles all UI rendering for VCS operations."""

    def __init__(self, program):
        self.program = program

    def confirm_commit(self, diff, repotypename, on_confirm, on_deny):
        """Show commit confirmation dialog. Returns the window for wait."""
        w = ui.Window(self.program.tk_root,
                      title=_("Commit Confirm"), exit=False)
        text = (_("Do you want to commit language data via {repo} now?")
                .format(repo=repotypename) + '\n' + diff[:300])
        prompt = ui.Label(w, text=text, row=0, column=0, sticky='')
        bf = ui.Frame(w, row=1, column=0, sticky='')
        yes = ui.Button(bf, text=_("Yes"), command=on_confirm,
                        row=1, column=0, sticky='w', padx=50)
        no = ui.Button(bf, text=_("No"), command=on_deny,
                       row=1, column=1, sticky='e', padx=50)
        w.lift()
        return w, yes

    def show_wait(self, msg):
        """Show the shared wait dialog with msg (the one reused wait window).
        Returns the root; call .waitdone() on the result to dismiss it."""
        root = self.program.tk_root
        root.wait(msg)
        return root

    def show_exe_warning(self, repo):
        """Show VCS executable missing warning.

        repo: an object with repotypename, installpage, wexeurl,
              wdownloadsurl, thisos, exists() attributes.
        """
        from utilities.utilities import sysrestart, openweburl
        title = _("Warning: {type} Executable Missing!").format(
            type=repo.repotypename)
        text = _("you don't seem to have the {repo} executable installed in "
                 "your computer's PATH.").format(repo=repo.repotypename)
        if repo.repotypename == 'Mercurial':
            text += '\n' + _("(Mercurial is used by Chorus and "
                             "languagedepot.org)")
            if not repo.exists():
                return  # No repo, no exe — nothing to warn about
        w = ui.Window(getattr(self.program, 'tk_root', None) or ui.Root(), title=title)
        w.withdraw()
        if repo.repotypename == 'Git':
            text += '\n' + _("(Git is used by {name} to track changes in your "
                             "data, and to keep {name} up to date)"
                             ).format(name=self.program.name)
        clickable = _("Please see {url} for installation recommendations"
                      ).format(url=repo.installpage)
        l = ui.Label(w.frame, text=text, column=0, row=0)
        l.wrap()
        m = ui.Label(w.frame, text=clickable, column=0, row=1)
        m.wrap()
        m.bind("<Button-1>", lambda e: openweburl(repo.installpage))
        ui.ToolTip(m, _("Go to {url}").format(url=repo.installpage))
        if repo.thisos == 'Windows':
            clickable1 = _("(e.g., in Windows, install *this* file),"
                           ).format(url=repo.wexeurl)
            clickable2 = _("or see all your options at {url}."
                           ).format(url=repo.wdownloadsurl)
            n = ui.Label(w.frame, text=clickable1, column=0, row=2)
            n.bind("<Button-1>", lambda e: openweburl(repo.wexeurl))
            ui.ToolTip(n, _("download {url}").format(url=repo.wexeurl))
            o = ui.Label(w.frame, text=clickable2, column=0, row=3)
            o.bind("<Button-1>", lambda e: openweburl(repo.wdownloadsurl))
            ui.ToolTip(o, _("Go to {url}").format(url=repo.wdownloadsurl))
        text = _("After you install {repo}, you should restart."
                 ).format(repo=repo.repotypename)
        if repo.repotypename == 'Git':
            text += '\n' + _(
                "You can keep using {name} without installing {repo}, but "
                "it is not recommended, and you will continue to see "
                "this warning."
                " And sooner or later that's going to get really annoying"
            ).format(name=self.program.name, repo=repo.repotypename)
        r = ui.Label(w.frame, text=text, column=0, row=4)
        r.wrap()
        rb = ui.Button(w.frame, text=_("Restart Now"), column=1, row=4,
                       cmd=sysrestart)
        ui.ToolTip(rb, _("Install {repo} first, then do this"
                         ).format(repo=repo.repotypename))
        w.deiconify()
        w.lift()
        return w
