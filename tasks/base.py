# coding=UTF-8
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)
from backend.core.lexicon import Tone, Segments #for makecvtok

class TaskBase:
    """Pure logic base for tasks. No window, no UI dependency.

    Holds class-level flags, makecvtok/makeeverythingok logic, and
    program wiring. Unknown attribute access delegates to self.ui
    (the TaskWindow) via __getattr__, so backend mixins can call
    window methods transparently.
    """
    is_chooser=False
    is_report=False
    is_record_task=False
    # TWO FLAGS, TWO QUESTIONS — they are one letter apart in meaning and
    # were being used as if they were the same (Kent, 2026-09-17: "I think
    # we need to talk about these two attributes"):
    #   `uses_second_forms`  — this task READS OR WRITES the second-form
    #       field, so the setting must be defined before it works. It gates
    #       `Segments.second_forms_ready`, which Parse's word loader, its
    #       word-entry binding and its Next button each consult (three
    #       escalating asks; only Next withholds anything).
    #       It USED to gate a call in `Sort.runcheck`, deleted 2026-09-29:
    #       no task that reaches `runcheck` declares this flag, and no task
    #       that declares it reaches `runcheck`, so that gate could never
    #       fire. See the second-form flags audit, plans 3 and 4.
    #   `whole_word_checks`  — this task lets the user choose WHICH WHOLE-WORD
    #       FORM to work on, so the settings pane draws the second-form field
    #       line: the field is what makes a pl/imp choice exist at all.
    #       RENAMED FROM `show_second_fields` AND REHOMED 2026-09-29 (plan 1
    #       of the second-form flags audit). It sat on `Segments`,
    #       i.e. EVERY segmental task, so SortV, SortC, SortCV, Transcribe*,
    #       Record* and Report* all drew a line for a setting they never
    #       read. It now sits on `WordCollection` and `Syllables` only —
    #       word collection and the syllable sort, the two places where
    #       choosing the form is a rational act (Kent, 2026-09-17).
    #       Parse draws the same line through `uses_second_forms` instead,
    #       because it needs the field rather than merely offering it.
    #       It now draws the WORD-CHECK line too (`StatusFrame.wordcheckline`,
    #       plan 2, 2026-09-29): which FORM of the word — lc, lx, and pl/imp
    #       where their field is named. A word check is not a cvt check;
    #       the cvt line picks segments WITHIN the form, and this page does
    #       not draw one.
    # `<unset>` IS A LEGAL STATE, and no sort may be stopped for it: with no
    # field defined there is simply no second-form check to select (for cvt
    # 'S' the check list is `[params.ftype()]`, analysis.py:1857, and the
    # ftype defaults to 'lc'). So no sort sets `uses_second_forms`. See
    # the settings-prompts-in-one-window item for the confirmation in full.
    uses_second_forms=False
    do_not_show_slices=False
    multislice_max=False
    multicheck_scope=False
    do_not_show_cvt=False
    show_parser_ui=False
    no_leaderboard=False
    icon_leaderboard=False
    glyph_leaderboard=False
    cvt_sensitive=False
    whole_word_checks=False
    # THE VERB ON THE WORD-CHECK LINE. "Collecting citation forms" on a
    # collection page, "Sorting citation forms" on the syllable sort — the
    # value is the same word check either way, but the sentence it sits in
    # is the task's. NOT wrapped in `_()` here: a module-level call would
    # freeze the string in whatever language was live at import, the same
    # reason `tasktitle` is a bare string and translated at use.
    word_check_prefix="Working on"
    # WHICH WORD FORM THIS TASK WORKS ON, declared rather than assigned
    # (Kent, 2026-09-29). `Task.__init__` applies it, exactly as it applies
    # `cvt` one line earlier — so declaring IS setting, and a task that wants
    # something other than the citation form overrides this instead of
    # writing `self.ftype=` in its own `__init__` where nobody can see it.
    #   DEFAULTED HERE RATHER THAN DECLARED PER TASK, at Kent's call: "we
    # could set works_on_ftype in tasks.Base, and override it where
    # necessary, which fits current and expected usage." Nothing overrides it
    # today — `WordCollectionLexeme` was the only `lx` task and it is gone —
    # so every task opens on citation forms, which is also decision 4 of
    # the ftype-as-a-setting item: the word check does NOT persist across opens, and
    # Kent: "most of the time we're working in citation forms; even switching
    # back to that on returning to the task is not weird."
    #   What this REPLACED was a blind `if not hasattr(self,'ftype')` reset
    # to 'lc' that fired for every task that had not set one first, which is
    # the same effect with none of the visibility.
    works_on_ftype='lc'
    # AND DOES IT NEED ITS OWN CHOOSER FOR THAT FORM? A separate question
    # from `whole_word_checks`, and all three word-check pages answer it
    # differently (see `StatusFrame.wordcheckline`): word collection has no
    # check line, so this is its only way to pick one; the syllable sort's
    # CHECK line is the chooser as of plan 6; the record page offers a
    # button per form and needs no mode. Only the first sets this.
    offers_word_check_line=False
    show_buttoncolumnsline=False

    # NO `ftype` ATTRIBUTE, AND NO PROPERTY STANDING IN FOR ONE. The word
    # form has one owner, `program.params.ftype()`, and every reader asks it
    # directly (Kent, 2026-09-29: "drop self.ftype and read params.ftype()
    # everywhere"). It used to be a real attribute, set in six constructors
    # and re-copied in four more, with an ErrorNotice in `categories.py` for
    # when the two disagreed.
    #   A PROPERTY WAS TRIED FIRST AND REJECTED, and the reason is the one
    # that matters here: `lift.py`'s `ftype` is a DIFFERENT THING sharing the
    # name — the LIFT node's `type` string, always a parameter, where `lc`
    # and `lx` coincide with these codes and `pl`/`imp` do not exist at all.
    # A task-side `self.ftype` keeps the app's setting looking like the value
    # you hand to lift, which is exactly the resemblance that hid the
    # `sense.ftypes` gap. Kent: "How will you manage the distinction between
    # a task's attribute and the one we send to lift?" `params.ftype()` at
    # the call site reads as the app's setting; `sense.ftypes[…]` reads as
    # the node. That difference is the point, so it is spelled out.

    def __getattr__(self, name):
        """Delegate unknown attributes to self.ui (the TaskWindow).

        This lets backend mixins call window methods (withdraw, frame,
        runwindow, context, etc.) without importing frontend code.
        Only fires when normal attribute lookup fails.
        """
        # Prevent recursion: if ui isn't set yet, stop
        try:
            ui = object.__getattribute__(self, 'ui')
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}' "
                f"(ui not yet initialized)")
        if ui is None:
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}' "
                f"(ui is None)")
        # Per-instance recursion guard
        try:
            guard = object.__getattribute__(self, '_getattr_guard')
        except AttributeError:
            guard = set()
            object.__setattr__(self, '_getattr_guard', guard)
        if name in guard:
            raise AttributeError(
                f"'{type(self).__name__}' has no attribute '{name}'")
        guard.add(name)
        try:
            return getattr(ui, name)
        finally:
            guard.discard(name)

    # -- Delegation methods for super() chains --
    # These exist because __getattr__ doesn't intercept super() calls.
    # Concrete tasks override setcontext/on_quit and chain via super().

    def setcontext(self):
        """Terminator for the task-mixin setcontext chain.

        TaskDressing populates window-chrome items and then calls
        ``self.task.setcontext()``, which walks the mixin MRO. Each
        mixin's ``setcontext`` should call ``super().setcontext()``
        before adding its own items; this base method ends the chain.
        """
        pass

    # ── Being finished, as a FACT rather than an inference ────────────
    # WHY THIS EXISTS. Long builds ask "should I still be doing this?" and
    # the answer used to be inferred from the WINDOW —
    # `Senses._window_is_there()`, i.e. `winfo_exists()`. That was a reliable
    # proxy only because tkinter's `on_quit` ends in `destroy()`. The webview
    # backend HIDES windows instead (see `_close_native_window`: freeing a
    # pywebview window at the wrong moment crashes Qt, and this app reuses
    # windows anyway), so a closed task's window is alive and the proxy says
    # "carry on".
    #
    # AND THE LOOPS ARE NOT INTERRUPTED ANY MORE. `lexicon.py:2101`'s comment
    # describes the tkinter world exactly: "`waiting()` + `waitprogress`
    # drain the event loop, so the click is serviced HERE". One event loop,
    # one flow, so the window died mid-iteration and the guard caught it.
    # Under webview every page event arrives on its OWN THREAD
    # (`webview/util.py:_call`, visible in every faulthandler dump), so
    # clicking Tasks does not interrupt the affix loop — it runs beside it.
    # Two task flows, concurrently, neither aware of the other. That is what
    # Kent saw as the parser still working after an unrelated task had
    # started (2026-09-16): "the parser work shouldn't be continuing AFTER
    # another unrelated task is already started. That wait shouldn't appear
    # at all."
    #
    # SO ASK THE TASK, NOT THE WINDOW. A task that has been closed knows it;
    # nothing has to be deduced. `program.task is self` is already the
    # codebase's idiom for the same question — see `hide_chooser` — and a
    # FLAG needs no handle, which answers this item's own objection to
    # close-time cancellation ("half 1 can only cancel work whose handle the
    # window holds"): a synchronous build ten frames down can read a flag.
    #
    # See the concurrent-webview-flows item.
    _closed = False

    def still_wanted(self):
        """Should work belonging to this task keep going?

        False once this task has been closed, or once the program has moved
        on to another one. Never raises: a build asking this question is
        mid-flight, and an exception here would replace the fault it exists
        to prevent."""
        if self._closed:
            return False
        try:
            live = getattr(self.program, 'task', None)
            # `None` means the chooser cleared it (`chooser.py:163`) and no
            # task is live — which is also a reason to stop. A DIFFERENT
            # task means the user moved on.
            if live is not None and live is not self:
                return False
        except Exception:
            return True
        return True

    def _on_close(self, why=''):
        """Record that this task is finished, and drop what it is holding.

        Called from `on_quit` and from `_dismiss_unshown` — the two ways a
        task ends — so a task cannot be closed without its work being told.
        Concrete tasks override to add their own teardown and should call
        `super()._on_close(why)` first, so the flag is set even if their own
        cleanup raises.

        Idempotent: both exits can run for one task, and a second close must
        not undo the first or log twice."""
        if self._closed:
            return
        self._closed = True
        log.info("task %s closed%s — work belonging to it should stop",
                 type(self).__name__, ' ({})'.format(why) if why else '')
        # WHAT THE TASK ITSELF HOLDS. `cancel_drive_work` is the one handle
        # the window has, and tkinter's `on_quit` has always called it
        # (`ui_tkinter.py:1420`); anything else a task holds belongs in its
        # own override.
        for attr in ('cancel_drive_work',):
            fn = getattr(self, attr, None)
            if callable(fn):
                try:
                    fn()
                except Exception as e:
                    log.info("task %s: %s failed on close (%r)",
                             type(self).__name__, attr, e)

    def on_quit(self, **kwargs):
        """Delegate to the window's on_quit (ui.Window)."""
        self._on_close('on_quit')
        self.ui.waitdone()
        self.ui.on_quit(**kwargs)

    def _dismiss_unshown(self):
        """Quietly tear down this task's still-withdrawn window WITHOUT reviving
        the parent chooser or quitting to root (both of which on_quit would do).
        Used when the open-time syllable-profile offer sends the user to a
        different task: that task is already open, so this board must just go."""
        # THE OTHER WAY A TASK ENDS, so it records the same fact. Without
        # this a task dismissed by the profile offer would leave its loops
        # believing they were still wanted. See `_on_close`.
        self._on_close('dismissed unshown')
        try:
            self.ui.exitFlag.true()
            self.ui.cleanup()
            self.ui.destroy()
        except Exception as e:
            log.info(f"_dismiss_unshown: {e}")

    def makecvtok(self):
        """Should these not be done locally, in Tone and Segments?"""
        if isinstance(self,Tone):
            self.checktypename='frame'
            self.cvt='T'
        if isinstance(self,Segments):
            self.checktypename='check'
            # 'S' (SortSyllables) inherits Segments for shared helpers but is a
            # whole-word syllable-profile sort; don't reset it to 'V'.
            if self.cvt not in ['V','C','CV','σ']:
                self.cvt='V'
        self.cvt=self.program.params.cvt(self.cvt)

    def i_am_the_task(self):
        self.program.task=self
        self.program.status.task(self)

    def hide_chooser(self):
        """Withdraw the task chooser — UNLESS the user has gone back to it.

        Tasks hide the chooser behind the page they have just built. But the
        chooser's Tasks button can fire DURING that build (a slow affix load
        drains the event loop), and `gettask()` then quits this task and
        re-reveals the chooser. Withdrawing unconditionally on the way out
        hid it again, leaving the user with NO WINDOW AT ALL — Kent,
        2026-09-14, clicking Tasks during a page load.

        `gettask` clears `program.task` (chooser.py:163), so that is the
        test. Returns False when it declined, which is also the caller's
        signal to stop building a page nobody is waiting for.
        """
        if getattr(self.program,'task',None) is not self:
            log.info("not hiding the task chooser: %s is no longer the live "
                     "task, so the user has asked to be back there",
                     type(self).__name__)
            return False
        self.program.taskchooser.withdraw()
        return True

    def makeeverythingok(self):
        """The value of this method is unclear. This may be better
        done elsewhere."""
        try:
            self.makecvtok()
            # A copy of the global into the task was refreshed here. Gone
            # 2026-09-29: there is no copy, so there was nothing to refresh.
            self.program.slices.makepsok()
            self.program.slices.makeprofileok()
            self.program.status.makecheckok()
            # AND THE GROUP, LAST, because it depends on all four above.
            # This validated cvt, ps, profile and check and left the group
            # alone, so opening a task kept whatever group the previous one
            # had been on — Kent, 2026-09-30, opening Sort Vowels straight
            # from the syllable sort: "I just saw group=CVCCCV on SortV".
            # A cvprofile is not a vowel.
            #   `refreshattributechanges` got the same call on the same day,
            # but that runs on settings CHANGES; a task OPEN comes through
            # here, which is why fixing one did not fix the other.
            self.program.status.makegroupok()
        except AttributeError as e:
            log.info(_("Maybe status/slices aren’t set up yet."))

class Task(TaskBase):
    """Task with a separate TaskWindow. Creates the window on init."""
    ui_kwargs={"withdrawn"}
    def __init__(self, program, **kwargs):
        self.program = program
        if hasattr(self,'cvt'):
            self.program.params.cvt(self.cvt)
        # THE DECLARED FORM, applied the same way `cvt` is. Unconditional,
        # because `works_on_ftype` is always declared (TaskBase defaults it
        # to 'lc') — where this used to be `if not hasattr(self,'ftype')`,
        # which is now always False since `ftype` is a property.
        self.program.params.ftype(self.works_on_ftype)
        # OWNER AND MODAL-ON ARE DIFFERENT RELATIONSHIPS, and this line
        # conflated them. A task window was parented to the CHOOSER'S
        # WINDOW, which meant the chooser had to have one before any task
        # could exist — the single blocker to building the chooser's logic
        # without its UI (the modal-window-stack item).
        #
        # What the parent is actually used for splits cleanly in two:
        #   * OWNER — `theme`, `wraplength`, `renderer`, and resolving the
        #     root. All of that is on the root already, so the root is the
        #     honest owner.
        #   * MODAL-ON — closing returns you to what launched you, and
        #     `set_transient_for` tells the compositor to keep the two
        #     together. That IS the chooser, and it is declared separately
        #     (`TaskWindow` does it), when there is a window to declare it
        #     against.
        # Kent's framing, 2026-09-16: "the task is a modal on the
        # taskchooser, which is only visible/useful when the task it called
        # is gone. the runwindow is a further modal on that."
        #
        # NO BEHAVIOUR CHANGE TODAY: the chooser always has a window, so
        # this still picks it. The `else` is what lets a window-less chooser
        # exist later without this line being the thing that stops it.
        if self.program.taskchooser == self:
            parent=self.program.tk_root
        else:
            self.i_am_the_task()
            chooser_ui=getattr(self.program.taskchooser,'ui',None)
            if chooser_ui is not None and getattr(chooser_ui,'winfo_exists',
                                                  lambda: False)():
                parent=chooser_ui
            else:
                log.info("the task chooser has no window, so %s is owned by "
                         "the root; it is modal on nothing because nothing "
                         "is behind it",type(self).__name__)
                parent=self.program.tk_root
        self.analang=self.program.db.analang
        self.min_to_multicolumn=6
        self.makeeverythingok()
        from frontend.task_window import TaskWindow
        ui_kwargs={k:v for k,v in kwargs.items() if k in self.ui_kwargs}
        # TIMED 2026-09-28: this is where the task WINDOW is built, and the
        # screencast shows the page painted about 1.7s after the task is
        # asked for, then a 6.47s silence. Knowing which side of this line
        # that silence falls on decides whether to look at window building or
        # at what the subclasses do afterwards.
        import time as _time
        _t_win=_time.perf_counter()
        self.ui = TaskWindow(self, parent, **ui_kwargs)
        log.info(f"Done initializing {self.__class__.__name__} "
                 f"(base: {self.program.task_base()}) — TaskWindow built in "
                 f"{_time.perf_counter()-_t_win:.2f}s")
