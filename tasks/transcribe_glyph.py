# coding=UTF-8
"""Shared glyph transcription window logic.

Used by TranscribeS (as a task) and by Sort.name_new_glyphs (standalone).
Contains the makewindow UI builder and all supporting methods for
naming/renaming glyph groups.
"""
from frontend import ui
from frontend.sort_buttons import SortGlyphGroupButtonFrame
from frontend import transcriber
from utilities.utilities import nn
from utilities.i18n import _
from utilities import logsetup
log = logsetup.getlog(__name__)

# Glyph character palettes for the Transcriber widget
VOWEL_GLYPHS = [
    #tilde (decomposed):
    'ã', 'ẽ', 'ɛ̃', 'ə̃', 'ɪ̃', 'ĩ', 'õ', 'ɔ̃', 'ũ', 'ʊ̃',
    #Combining Greek Perispomeni (decomposed):
    'a͂', 'i͂', 'o͂', 'u͂',
    #single code point vowels:
    'a', 'e', 'i', 'ə', 'o', 'u',
    'ɑ', 'ɛ', 'ɨ', 'ɔ', 'ʉ', 'ɩ',
    'æ', 'ʌ', 'ɪ', 'ï', 'ö', 'ʊ',
]

CONSONANT_GLYPHS = [
    'bh','dh','gh','gb',
    'b', 'd','g','ɡ',
    'kk','kp',
    'p', 'ɓ',
    't','ɗ','ɖ','c','k','q',
    'vh','zh',
    'j', 'v','z',
    'ʒ','ð','ɣ',
    'ch','ph','sh','hh','pf','bv',
    'f','s','ʃ','θ','x','h',
    'dj','dz','dʒ',
    'chk',
    'ts','tʃ',
    'zl', 'ɮ',
    'sl', 'ɬ',
    'ʔ',
    "ꞌ",  #Latin Small Letter Saltillo
    "'",  #Tag Apostrophe
    'ʼ',  #modifier letter apostrophe
    'ẅ','y',
    'w', 'm',
    'n','ŋ','ɲ','ɱ',
    'mm','ŋŋ','ny',
    "ng'",
    'l','r',
    'rh','wh',
]


class GlyphTranscribeHelper:
    """Handles glyph naming/renaming window.

    Instantiate with a 'task' (the Sort/Segments task that has backend
    methods like rename_macrogroup, add_int_group, maybewrite, etc.)
    and call makewindow(glyph) for each glyph to name.

    Attributes set after makewindow returns:
        ok_done: True if user clicked OK
        window_failed: True if no examples found for glyph
    """

    def __init__(self, task, glyphspossible=None,
                 switch_text=None, switch_tt=None,
                 on_done=None, on_go_back=None):
        """
        task: Sort/Segments task instance (provides program, ui, frame,
              rename_macrogroup, add_int_group, maybewrite, getglyph, etc.)
        glyphspossible: list of characters for the transcriber palette
        on_done: callback after successful submit (default: save alphabet settings)
        on_go_back: callback for "go back" button (default: just close window)
        """
        self.task = task
        self.program = task.program
        self.glyphspossible = glyphspossible
        self.switch_text = switch_text or _("Switch letters with this group")
        self.switch_tt = switch_tt or _(
            "This switches letters for the two groups, and updates each of them")
        self.on_done = on_done
        self.on_go_back = on_go_back
        self.ok_done = False
        self.window_failed = False
        self.analang = self.program.db.analang
        self.cvt = self.program.params.cvt()

    # -- Window management --

    @property
    def frame(self):
        return self.task.ui.frame

    def waitdone(self):
        """No-op for API compatibility with old Task-based approach."""
        pass

    def destroy(self):
        """Clean up any remaining runwindow."""
        if hasattr(self, 'runwindow') and self.runwindow:
            self.runwindow.destroy()

    # -- Form validation --

    def updateerror(self):
        newvalue = self.transcriber.formfield.get()
        if newvalue == '':
            noname = _("Give a name for this group!")
            log.debug(noname)
            self.errorlabel['text'] = noname
            return 1
        elif newvalue != self.group and newvalue in self.groups:
            deja = [_("Sorry, there is already a group with that label"),
                    _("see comparison below.")]
            log.debug('; '.join(deja))
            self.errorlabel['text'] = ';\n '.join(deja)
            self.setgroup_comparison(newvalue)
            return 1
        self.errorlabel['text'] = ''

    def updateform(self, *args):
        self.set_ok_w_form(self.updateerror())

    def set_ok_w_form(self, error=False):
        form = self.transcriber.formfield.get()
        self.oktext.set(_("OK: Add the letter \u2018{form}\u2019 {newline}to my alphabet "
                          "{newline}for this sound").format(form=form, newline="\n"))
        if form and not error:
            self.ok_button['state'] = 'normal'
        else:
            self.ok_button['state'] = 'disabled'

    # -- Comparison buttons --

    def comparisonbuttons(self):
        try:  # successive runs
            self.compframe.compframeb.destroy()
            log.info("Comparison frameb destroyed!")
        except Exception:  # first run
            log.info("Problem destroying comparison frame, making...")
        self.compframe.compframeb = ui.Frame(self.compframe)
        self.compframe.compframeb.grid(row=1, column=0)
        t = _('Compare with another group')
        if (hasattr(self, 'group_comparison')
                and self.group_comparison in self.groups
                and self.group_comparison != self.group):
            log.info("Making comparison buttons for group {group} now".format(
                group=self.group_comparison))
            t = _('Compare with another group ({group})').format(
                group=self.group_comparison)
            self.compframe.bf2 = SortGlyphGroupButtonFrame(
                self.compframe.compframeb,
                self.task,
                group=self.group_comparison,
                showtonegroup=True,
                playable=True,
                unsortable=False,
                alwaysrefreshable=True,
                font='default',
                wraplength=self.buttonframew
            )
            self.compframe.bf2.grid(row=0, column=0, sticky='w')
            self.compframe.b2 = ui.Button(self.compframe.compframeb,
                                          text=self.switch_text,
                                          cmd=self.switchgroups,
                                          row=0, column=1, sticky='w')
            self.compframe.b2tt = ui.ToolTip(self.compframe.b2, self.switch_tt)
        elif not hasattr(self, 'group_comparison'):
            log.info("No comparison found !")
        elif self.group_comparison not in self.groups:
            log.info("Comparison ({comp}) not in group list ({groups})"
                     "".format(comp=self.group_comparison, groups=self.groups))
        elif self.group_comparison == self.group:
            log.info("Comparison ({comp}) same as subgroup ({group}); not showing."
                     "".format(comp=self.group_comparison, group=self.group))
        else:
            log.info(_("This should never happen (renamegroup/"
                       "comparisonbuttons)"))
        self.sub_c['text'] = t

    def setgroup_comparison(self, group=None, **kwargs):
        if group:
            self.program.settings.set('group_comparison', group)
        else:
            w = self.task.getglyph(comparison=True, **kwargs)
            if w and w.winfo_exists():
                log.info("Waiting for {w}".format(w=w))
                w.wait_window(w)
        log.info(_("Groups: {group} (of {groups}); "
                   "{comp}?").format(group=self.group, groups=self.groups,
                                    comp=self.program.settings.group_comparison))
        if hasattr(self.program.settings, 'group_comparison'):
            self.group_comparison = self.program.settings.group_comparison
        if self.errorlabel['text'] == _("Sorry, pick a comparison first!"):
            self.updateerror()
        self.comparisonbuttons()

    # -- Submit / switch --

    def polygraphwarn(self, newvalue):
        # Self-contained (uses this helper's own group/program/analang/cvt):
        # don't delegate to self.task, which only has polygraphwarn for the
        # Transcribe task — the helper is also driven by Sort.name_new_glyphs,
        # whose task (SortV/SortC) has no such method.
        if len(newvalue) != 1 or len(self.group) != 1:
            warning = [_("This name change ('{group}' > '{new}') impacts your "
                        "digraph and trigraph settings."
                        ).format(group=self.group, new=newvalue)]
            if len(newvalue) > 1:
                warning.append(_("{azt} will add '{new}' to those settings."
                            ).format(azt=self.program.name, new=newvalue))
                if newvalue not in self.program.profiles.polygraphs[self.analang][self.cvt]:
                    self.program.profiles.polygraphs[self.analang][self.cvt][newvalue] = True
                    self.program.settings.storesettingsfile('profiledata')
            if len(self.group) > 1:
                warning.append(_("{azt} will *not* remove '{group}' from "
                            "those settings, because you may still be "
                            "using it elsewhere."
                            ).format(azt=self.program.name, group=self.group))
            warning.extend(['', _("**If this isn't what you wanted, "
                        "fix and confirm your digraph and "
                        "trigraph settings in the menu "
                        "\n(this will make {azt} restart and redo "
                        "the syllable profile analysis)."
                        ).format(azt=self.program.name)])
            log.info('\n'.join(warning))

    def submitform(self):
        newvalue = self.transcriber.formfield.get()
        self.polygraphwarn(newvalue)
        self.task.rename_macrogroup(self.group, newvalue)
        self.program.alphabet.glyph(newvalue)
        self.refresh_status_buttons(self.group, newvalue)
        self.task.maybewrite()
        self.ok_done = True
        if hasattr(self, 'group_comparison'):
            delattr(self, 'group_comparison')
        self.runwindow.on_quit()

    def refresh_status_buttons(self, *args):
        """This is just for the Transcribe task, to update the glyph list"""
        if hasattr(self.task, 'status') and hasattr(self.task.status,'glyphbuttons'):
            for i in args:
                if (i in self.task.status.glyphbuttons
                        and self.task.status.glyphbuttons[i].winfo_exists()):
                    self.task.status.glyphbuttons[i].destroy()

    def switchgroups(self, comparison=None):
        if (not hasattr(self, 'group') or not hasattr(self, 'group_comparison')
                and not comparison):
            log.error(_("Missing either group or comparison, without value "
                        "specified; can't switch them."))
            return
        log.info(_("Switching groups; using \u2018{comp}\u2019 for "
                   "\u2018{group}\u2019").format(comp=self.group_comparison, group=self.group))
        g = self.task.add_int_group(self.task)
        self.task.rename_macrogroup(self.group, g, updatestatus=False)
        self.task.rename_macrogroup(self.group_comparison, self.group, updatestatus=False)
        self.task.rename_macrogroup(g, self.group_comparison)
        self.refresh_status_buttons(g, self.group_comparison)
        self.runwindow.on_quit()
        self.makewindow()  # The other group needs a name, too!

    # -- Done / Go back --

    def done(self):
        """Submit form and finish. Override or pass on_done for custom behavior."""
        log.info("GlyphTranscribe done")
        self.submitform()
        self.program.alphabet.save_settings()
        if self.on_done:
            self.on_done()

    def go_back(self):
        """Go back without submitting. Override or pass on_go_back for custom."""
        log.info("GlyphTranscribe go_back")
        self.runwindow.on_quit()
        if self.on_go_back:
            self.on_go_back()

    # -- Main window builder --

    def makewindow(self, glyph=None, event=None):
        """Build the transcribe/rename glyph window.

        Blocks (via wait_window) until the user submits or closes.
        Sets self.ok_done and self.window_failed accordingly.
        """
        # Sound settings (optional)
        soundsettings = getattr(self.program.settings, 'soundsettings', None)
        if soundsettings is not None:
            soundsettings.confirm_pyaudio()
            soundsettings = getattr(self.task, 'soundsettings', soundsettings)

        self.ok_done = False
        if glyph:
            self.group = self.program.alphabet.glyph(glyph)
        else:
            self.group = self.program.alphabet.glyph()
        if not isinstance(self.group, str):
            log.info("Group not a string! ({group}, {type})".format(
                group=self.group, type=type(self.group)))
        cvt = self.program.params.cvt()
        self.groups = self.program.alphabet.glyphs()
        self.otherglyphs = set(self.groups) - {self.group}
        padx = 50
        if self.program.settings.lowverticalspace:
            log.info("Using low vertical space setting")
            pady = 0
        else:
            pady = 10
        self.buttonframew = int(self.program.screenw / 3.5)
        title = [self.program.params.cvtdict()[cvt]['sg'], _("letter")]
        getformtext = [_("What letter(s) will you use for this {sg} "
                         "group?").format(sg=self.program.params.cvtdict()[cvt]['sg'])]
        if self.group.isdigit():
            title.insert(0, _("Name New"))
            initval = ''
        else:
            title.insert(0, _("Rename"))
            title.append(f"\u2018{self.group}\u2019")
            initval = self.group
        self.task.ui.getrunwindow(title=title)
        self.runwindow = self.task.ui.runwindow
        titlel = ui.Label(self.runwindow.frame, text=' '.join(title),
                          font='title',
                          row=0, column=0, sticky='ew', padx=padx, pady=pady)
        getform = ui.Label(self.runwindow.frame,
                           text='\n'.join(getformtext),
                           font='read',
                           norender=True,
                           row=1, column=0, sticky='ew', padx=padx, pady=pady)
        getform.wrap()
        inputfeedbackframe = ui.Frame(self.runwindow.frame,
                                      row=2, column=0, sticky='')
        self.transcriber = transcriber.Transcriber(inputfeedbackframe,
                                                  initval=initval,
                                                  soundsettings=soundsettings,
                                                  chars=self.glyphspossible,
                                                  row=0, column=0, sticky='')
        self.transcriber.newname.trace_add('write', self.updateform)
        infoframe = ui.Frame(inputfeedbackframe,
                             row=0, column=1, sticky='')
        g = nn(self.otherglyphs, perline=len(self.otherglyphs) // 3)
        glyphslabel = ui.Label(infoframe,
                               text='\n'.join([_("Don't use Other Groups:"), g]),
                               column=1,
                               sticky='new',
                               padx=padx,
                               rowspan=2)
        self.errorlabel = ui.Label(infoframe, text='',
                                   fg='red',
                                   wraplength=int(
                                       self.frame.winfo_screenwidth() / 3),
                                   row=2, column=1, sticky='nsew')
        ui.Button(infoframe,
                  text=_("Go back and join \nwith one of\n← these groups"),
                  command=self.go_back,
                  column=2,
                  rowspan=2,
                  sticky='nsew')
        examplesframe = ui.Frame(self.runwindow.frame,
                                 row=4, column=0, sticky='')
        self.oktext = ui.StringVar()
        self.ok_button = ui.Button(examplesframe,
                                   textvariable=self.oktext,
                                   font='title',
                                   row=0,
                                   column=1,
                                   sticky='ns',
                                   padx=padx,
                                   ipadx=30,
                                   ipady=20,
                                   pady=20,
                                   command=self.done)
        self.updateform()  # updates button state
        cmd = lambda x=self.group: self.transcriber.set_value(x)
        b = SortGlyphGroupButtonFrame(examplesframe, self.task,
                                      group=self.group,
                                      showtonegroup=True,
                                      on_select=cmd,
                                      playable=True,
                                      alwaysrefreshable=True,
                                      row=0, column=0, sticky='w',
                                      wraplength=self.buttonframew)
        self.window_failed = False
        if not b.hasexample:
            self.task.ui.clear_runwindow()
            self.window_failed = True
            return
        self.compframe = ui.Frame(examplesframe,
                                  highlightthickness=10,
                                  highlightbackground=self.frame.theme.white,
                                  pady=20, row=1, column=0, sticky='',
                                  columnspan=2)
        t = _('Compare with another group')
        fn = self.setgroup_comparison
        self.sub_c = ui.Button(self.compframe,
                               text=t,
                               command=lambda: fn(),
                               row=0, column=0)
        self.comparisonbuttons()
        # The run window was created withdrawn (getrunwindow with no msg, so no
        # thenshow wait) and nothing opened a wait while building here, so this
        # waitdone() has no active wait to reveal through — it's a no-op. Deiconify
        # explicitly, as the sort path does (sorting_engine.presenttosort); without
        # it the rename / name-new-glyph page stays hidden and wait_window() below
        # blocks on an invisible window.
        self.runwindow.waitdone()
        if not self.runwindow.exitFlag.istrue():
            self.runwindow.deiconify()
            self.runwindow.update_idletasks()
        self.sub_c.wait_window(self.runwindow)  # blocks until window closes
