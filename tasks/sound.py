from backend.core.sound import SoundSettings, Record as BackendRecord
from frontend import sound_ui, ui
from utilities import logsetup
from io_put import lift

log = logsetup.getlog(__name__)


class Sound(object):
    """UI task mixin for sound-enabled tasks.

    Ensures ``program.soundsettings`` exists and runs mic-check when the
    current settings don't validate against available hardware.
    """
    is_sound_task = True

    def _configure_sound(self, event=None):
        sound_ui.SoundSettingsWindow(self)

    def setcontext(self):
        super().setcontext()
        self.context.menuitem("Sound settings", self._configure_sound)

    def soundcheck(self):
        analang_obj = self.program.languages.get_obj(self.analang)
        ss = SoundSettings.ensure(self.program, analang_obj=analang_obj)
        self.soundsettings = ss
        self.pyaudio = ss.pyaudio
        if ss.soundcheck(include_input=getattr(self, 'is_record_task', False)):
            self.mikecheck()

    def mikecheck(self):
        self.ui.withdraw()
        self.program.soundsettings.confirm_pyaudio()
        self.soundsettingswindow = sound_ui.SoundSettingsWindow(self)
        if not self.soundsettingswindow.exitFlag.istrue():
            self.soundsettingswindow.wait_window(self.soundsettingswindow)
        self.program.soundsettings.done_pyaudio()
        self.ui.deiconify()
        if (not self.ui.exitFlag.istrue()
                and self.soundsettingswindow.winfo_exists()):
            self.soundsettingswindow.destroy()

    def _configure_transcription(self, event=None):
        sound_ui.ASRModelSelectionWindow(self)

    def _toggle_top_models(self, event=None):
        ss = self.program.soundsettings
        ss.set_top_models_only(not ss.top_models_only())
        try:
            self.program.settings.storesettingsfile(setting='soundsettings')
        except Exception as e:
            log.info("couldn't persist top_models_only: {}".format(e))
        try:   # rebuild the context menu so the label flips on next open
            self.context.menu.destroy()
        except Exception:
            pass
        try:   # refresh the current word's draft buttons under the new filter
            if hasattr(self, 'show_drafts'):
                self.show_drafts()
        except Exception as e:
            log.info("couldn't refresh drafts after toggle: {}".format(e))

    def storesoundsettings(self):
        self.program.soundsettings.store_to_file()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.soundcheck()


class Record(BackendRecord, Sound):
    """UI task mixin for recording widgets and session windows."""
    is_record_task = True
    icon_leaderboard = True

    def setcontext(self):
        log.info("Setting Record menu context")
        super().setcontext()
        self.context.menuitem("Transcription settings",
                              self._configure_transcription)
        ss = getattr(self.program, 'soundsettings', None)
        if ss is not None:
            # label names the OTHER state (the convention), detected from current
            label = ("Transcribe with all ASR models" if ss.top_models_only()
                     else "Transcribe with top ASR models only")
            self.context.menuitem(label, self._toggle_top_models)

    def makelabelsnrecordingbuttons(self, parent, node, r, c):
        t = node.formatted(self.analang, self.glosslangs)
        lxl = ui.Label(parent, text=t, row=r, column=c + 1, sticky='w')
        lcb = sound_ui.RecordButtonFrame(parent, self, node,
                                         row=r, column=c, sticky='w')

    def cleanup_pa(self, parentframe):
        import gc
        for w in parentframe.content.winfo_children():
            if type(w) is sound_ui.RecordButtonFrame:
                w.recorder.streamclose()
                w.player.streamclose()
        parentframe.destroy()
        gc.collect()

    def showentryformstorecordpage(self):
        if self.ui.runwindow.exitFlag.istrue():
            return
        if not self.ui.runwindow.frame.winfo_exists():
            return
        # Open the wait BEFORE resetframe(): on the 2nd and later groups this
        # window is already mapped, so blanking it here — with Exit living in
        # outsideframe — leaves an empty fullscreen kiosk page until the first
        # page finishes building. wait() withdraws and covers the screen; the
        # per-page `with waiting()` below finds the wait already active, so it
        # just reuses it and its exit does the single reveal. No extra
        # withdraw/deiconify cycle, no flash of a one-label page.
        self.ui.runwindow.wait(msg="Getting words to record…", thenshow=True)
        try:
            self.ui.runwindow.resetframe()
            ps = self.program.slices.ps()
            profile = self.program.slices.profile()
            count = self.program.slices.count()
            text = "Record {profile} {ps} Words: click 'Record', talk, and release ({count} words)".format(profile=profile, ps=ps, count=count)
            log.info(text)
            instr = ui.Label(self.ui.runwindow.frame, anchor='w', text=text)
            instr.grid(row=0, column=0, sticky='w')
            senses = self.program.slices.senses(ps=ps, profile=profile)
            if not senses:
                senses = self.program.db.senses
            nperpage = 5
            pages = [senses[i:i + nperpage] for i in range(0, len(senses), nperpage)]
            # A5 in-place reload: resume at the page the user was on. The old task
            # stashes its position as _record_anchor (below); reload_database hands
            # it over as program._reload_anchor; consume it here (once) by seeking
            # to the page holding the anchored sense in the anchored slice.
            start = 0
            anchor = getattr(self.program, '_reload_anchor', None)
            if (anchor and anchor.get('ps') == ps
                    and anchor.get('profile') == profile):
                ids = [s.id for s in senses]
                if anchor.get('senseid') in ids:
                    start = ids.index(anchor['senseid']) // nperpage
                    log.info("record page: resuming at page %d (reload anchor)",
                             start)
                self.program._reload_anchor = None
            for pageno, page in enumerate(pages):
                if pageno < start:
                    continue
                self._record_anchor = {'ps': ps, 'profile': profile,
                                       'senseid': page[0].id}
                if self.ui.runwindow.exitFlag.istrue():
                    return
                with self.ui.runwindow.waiting(thenshow=True):
                    buttonframes = ui.ScrollingFrame(self.ui.runwindow.frame,
                                                     row=1, column=0, sticky='w')
                    row = 0
                    done = list()
                    for row, entry in enumerate([i.entry for i in page]):
                        self.ui.runwindow.column = 0
                        if entry.guid in done:
                            continue
                        else:
                            done.append(entry.guid)
                        ftypes = ['lc', 'pl', 'imp']
                        for node in [entry.sense.nodebyftype(f) for f in ftypes
                                     if entry.sense.nodebyftype(f)]:
                            self.ui.runwindow.column += 2
                            self.makelabelsnrecordingbuttons(buttonframes.content, node,
                                                            row, self.ui.runwindow.column)
                    ui.Button(buttonframes.content, column=1, row=row,
                              text="Next {count} words".format(count=nperpage),
                              cmd=lambda x=buttonframes: self.cleanup_pa(x))
                    # INSIDE the wait block, not after it: leaving the block calls
                    # waitdone(), and waitdone() IS the reveal (deiconify+update).
                    # A ScrollingFrame's children are invisible until reflow sizes
                    # the canvas, so reflowing after the reveal maps a fullscreen
                    # kiosk window whose only visible widget is the Exit button in
                    # outsideframe — the "blank page with just Quit" report. Sibling
                    # showsenseswithexamplestorecord already has the right order
                    # (reflow, then waitdone).
                    buttonframes.reflow()  # grow canvas to cover this page's record buttons
                # Page built and revealed; the outer wait opened above is closed
                # by this first inner block's exit. Everything from here is the
                # user working the page, uncovered by design.
                buttonframes.wait_window(buttonframes)
        finally:
            # Covers the paths where NO page build ran — no senses, or every page
            # skipped by the reload anchor — so the dialog can't be left up over
            # the wait_window() below. No-op once a page build has closed it.
            # Guarded: this runs on every exit path, including ones where the run
            # window is already gone (quit mid-build), and an exception raised in
            # a finally would replace whatever actually happened.
            try:
                self.ui.runwindow.waitdone()
            except Exception as e:
                log.info("could not close the record-page wait: {}".format(e))
        if not self.ui.runwindow.exitFlag.istrue():
            self.ui.runwindow.wait_window(self.ui.runwindow.frame)

    def showentryformstorecord(self, justone=False):
        self.ui.getrunwindow()
        if justone or not self.program.slices.valid():
            self.showentryformstorecordpage()
        else:
            ps = self.program.slices.ps()
            profile = self.program.slices.profile()
            for psprofile in self.program.slices.valid():
                if self.ui.runwindow.exitFlag.istrue():
                    return 1
                self.program.slices.ps(psprofile[1])
                self.program.slices.profile(psprofile[0])
                def _nextgroup(event=None):
                    # OPEN THE WAIT BEFORE BLANKING THE PAGE. This button used
                    # to be wired straight to resetframe, which is precisely
                    # what resetframe's own docstring forbids: it empties
                    # `frame` on a VIEWABLE window, and the Exit button lives in
                    # `outsideframe`, so the user was left looking at a
                    # fullscreen block of theme colour containing nothing but
                    # Quit for as long as the next group's page took to build.
                    # That is the nothing-but-Quit page, on the recording flow,
                    # produced by a deliberate click — and Kent watched a user
                    # on a Zoom call come close to pressing that Quit, because
                    # it was the only thing on screen (2026-09-01).
                    #
                    # The wait withdraws the window and covers the screen. The
                    # next page's own wait (showentryformstorecordpage, which
                    # opens one and calls resetframe itself) finds this one
                    # already active and reuses it, so its exit does the single
                    # reveal — no extra withdraw/deiconify cycle. Exactly the
                    # handover documented at showentryformstorecordpage's head.
                    try:
                        self.ui.runwindow.wait(msg=_("Getting the next group…"),
                                            thenshow=True)
                    except Exception as e:
                        log.info("could not cover the next-group gap: {}".format(e))
                    self.ui.runwindow.resetframe()
                nextb = ui.Button(self.ui.runwindow, text="Next Group",
                                  cmd=_nextgroup)
                nextb.grid(row=0, column=1, sticky='ne')
                self.showentryformstorecordpage()
            self.program.slices.ps(ps)
            self.program.slices.profile(profile)
        self.program.soundsettings.done_pyaudio()

    def showsenseswithexamplestorecord(self, senses=None, progress=None, skip=False):
        def setskip(event):
            self.ui.runwindow.frame.skip = True
            entryframe.destroy()
        self.ui.getrunwindow()
        if self.ui.exitFlag.istrue() or self.ui.runwindow.exitFlag.istrue():
            return
        if skip == 'skip':
            self.ui.runwindow.frame.skip = True
        else:
            self.ui.runwindow.frame.skip = skip
        text = "Words and phrases to record: click 'Record', talk, and release"
        instr = ui.Label(self.ui.runwindow.frame, anchor='w', text=text)
        instr.grid(row=0, column=0, sticky='w', columnspan=2)
        if senses is None:
            senses = self.program.settings.entriestoshow
        for sense in senses:
            examples = list(sense.examples.values())
            if examples == []:
                continue
            if ((self.ui.runwindow.frame.skip == True) and
                (lift.atleastoneexamplehaslangformmissing(examples,
                                     self.program.settings.audiolang) == False)):
                continue
            row = 0
            if self.ui.runwindow.exitFlag.istrue():
                return 1
            entryframe = ui.Frame(self.ui.runwindow.frame)
            entryframe.grid(row=1, column=0)
            if progress is not None:
                progressl = ui.Label(self.ui.runwindow.frame, anchor='e',
                                     font='small',
                                     text='({} {}/{})'.format(*progress))
                progressl.grid(row=0, column=2, sticky='ne')
            text = sense.formatted(self.analang, self.glosslangs)
            if not text:
                entryframe.destroy()
                continue
            ui.Label(entryframe, anchor='w', font='read',
                     text=text).grid(row=row,
                                     column=0, sticky='w')
            self.ui.runwindow.frame.scroll = ui.ScrollingFrame(entryframe)
            self.ui.runwindow.frame.scroll.grid(row=1, column=0, sticky='w')
            examplesframe = ui.Frame(self.ui.runwindow.frame.scroll.content)
            examplesframe.grid(row=0, column=0, sticky='w')
            for example in examples:
                if (skip == True and
                    lift.examplehaslangform(example, self.program.settings.audiolang) == True):
                    continue
                text = example.formatted(self.analang, self.glosslangs)
                if not text:
                    continue
                row += 1
                rb = sound_ui.RecordButtonFrame(examplesframe, self, example)
                rb.grid(row=row, column=0, sticky='w')
                ui.Label(examplesframe, anchor='w', text=text
                         ).grid(row=row, column=1, sticky='w')
            row += 1
            d = ui.Button(examplesframe, text="Done/Next", command=entryframe.destroy)
            d.grid(row=row, column=0)
            self.ui.runwindow.frame.scroll.reflow()  # grow canvas to cover examples
            self.ui.runwindow.waitdone()
            if self.ui.runwindow.exitFlag.istrue():
                return 1
            if self.ui.runwindow.frame.skip == True:
                return 'skip'

    def showtonegroupexs(self):
        def next_p():
            self.program.status.nextprofile()
            self.ui.runwindow.on_quit()
            self.showtonegroupexs()
        self.makeanalysis()
        self.analysis.donoUFanalysis()
        torecord = self.analysis.sensesbygroup
        if not torecord:
            self.analysis.do()
            self.showtonegroupexs()
            return
        skip = False
        for i in range(self.examplespergrouptorecord):
            for ufgroup in torecord:
                if len(torecord[ufgroup]) > i:
                    sense = torecord[ufgroup][i]
                    exited = self.showsenseswithexamplestorecord([sense],
                                                                 (ufgroup, i + 1, self.examplespergrouptorecord),
                                                                 skip=skip)
                    if exited == 'skip':
                        skip = True
                    if exited == True:
                        return
        if not (self.ui.runwindow.exitFlag.istrue() or self.ui.exitFlag.istrue()):
            # waitdone() is the REVEAL, so it has to come last. It used to run
            # first, which mapped the window and only then blanked it with
            # resetframe() — an empty kiosk page showing nothing but Exit until
            # these two widgets were gridded.
            with self.ui.runwindow.waiting(thenshow=True):
                self.ui.runwindow.resetframe()
                ui.Label(self.ui.runwindow.frame, anchor='w', font='read',
                         text="All done! Sort some more words, and come back."
                         ).grid(row=0, column=0, sticky='w')
                ui.Button(self.ui.runwindow.frame,
                          text="Continue to next syllable profile",
                          command=next_p).grid(row=1, column=0)
        self.program.soundsettings.done_pyaudio()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
