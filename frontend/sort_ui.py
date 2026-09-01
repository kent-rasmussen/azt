# coding=UTF-8
"""UI presenter for Sort workflow operations.

Backend sorting_engine.py delegates all UI widget creation here, so it
has zero frontend imports.
"""
import re
import time
import threading
import queue
from frontend import ui
from frontend.presenter_base import PresenterBase
from frontend.sort_buttons import (SortButtonFrame, SortGroupButtonFrame,
                                   SortGlyphGroupButtonFrame)
from utilities.i18n import _
from utilities import logsetup

log = logsetup.getlog(__name__)


def choose_shown_checks(checks_per_frame):
    """Pick the default member (check position) each glyph frame should show
    when a Review-Letter-Groups page is presented.

    Privilege FIRST the number of frames that can show the same position, THEN
    (on ties) the position nearest the front of the word — lowest first digit,
    so C1 beats C2, and a compound like C1=C2 counts as position 1; digitless
    checks (T, lc…) rank last. Frames that can't show the winning position get
    the same rule applied again among themselves, so each ends up on its best
    remaining shared position, or its own frontmost when nothing is shared.

    Takes one list of check codes per frame; returns the chosen check per
    frame (None for a frame with no checks). Pure — no widget access — so the
    caller maps checks back to member indexes."""
    def frontness(check):
        m=re.search(r'\d+',check or '')
        return int(m.group()) if m else float('inf')
    chosen=[None]*len(checks_per_frame)
    unassigned=[i for i,checks in enumerate(checks_per_frame) if checks]
    while unassigned:
        counts={}
        for i in unassigned:
            for c in set(checks_per_frame[i]):
                counts[c]=counts.get(c,0)+1
        best=min(counts,key=lambda c:(-counts[c],frontness(c),str(c)))
        covered=[i for i in unassigned if best in checks_per_frame[i]]
        for i in covered:
            chosen[i]=best
        unassigned=[i for i in unassigned if i not in covered]
    return chosen


def _rss_mb():
    """Resident memory of this process, in MB (-1 if psutil unavailable)."""
    try:
        import psutil, os
        return psutil.Process(os.getpid()).memory_info().rss/1e6
    except Exception:
        return -1.0


class SortPresenter(PresenterBase):
    """Handles all UI rendering for Sort, Verify, and Join workflows."""
    def __init__(self, theme):
        self.theme=theme
        # Background image preloader (syllable prep): one daemon worker decodes
        # and resizes upcoming slices' images off the Tk thread while the user
        # reads the current slice aloud. See preload_images().
        self._preload_q=None
        self._preload_lock=threading.Lock()
        self._preload_seen=set() # (iuri,key) already queued; never re-queue
        self._diag_reset() # per-build timers (see build_verify_layout)

    def _diag_reset(self):
        """Zero the per-verify-build diagnostic timers/counters (1.3.13)."""
        self._img_t=0.0      # total seconds in set_sense_illustration
        self._compile_t=0.0  # subset: img.compile() on preloader-fed images
        self._vb_t=0.0       # total per-item verifybutton_fn (backend + widget)
        self._wid_t=0.0      # Frame+Button creation in build_verify_button
        self._reflow_t=0.0   # ScrollingFrame.resume_configure() layout passes
        self._n_built=0      # image already compiled+cached (reused, ~free)
        self._n_compiled=0   # preloader prepared it → only pixmap upload here
        self._n_scaled=0     # full main-thread decode+resize+compile (not fed)

    # -- Background image preloader (off-thread PIL decode/resize) --

    def _ensure_preload_worker(self):
        if self._preload_q is not None:
            return
        self._preload_q=queue.Queue()
        threading.Thread(target=self._preload_worker,
                        name='img-preload', daemon=True).start()

    def _preload_worker(self):
        while True:
            iuri,key=self._preload_q.get()
            try:
                self._preload_one(iuri,key)
            except Exception as e: # a bad image must never kill the worker
                log.info("preload %s failed: %s", iuri, e)
            finally:
                self._preload_q.task_done()

    def _preload_one(self, iuri, key):
        with self._preload_lock:
            img=self.theme.image_cache.get(iuri)
            if img is not None and getattr(img,'base_img',None) \
                    and getattr(img,'_scaled_key',None)==key:
                return # already decoded+resized at this size
        # Decode + resize with NO Tk call (compile_now=False, then prepare()).
        img=ui.Image(iuri, compile_now=False)
        if not getattr(img,'base_img',None):
            return # failed to open; main thread will log if it retries
        scale,pixels,scaleto=key
        img.prepare(scale, pixels=pixels, scaleto=scaleto)
        img._scaled_key=key
        with self._preload_lock:
            existing=self.theme.image_cache.get(iuri)
            # Don't clobber an image the main thread already fully built.
            if existing is None or getattr(existing,'scaled',None) is None:
                self.theme.image_cache[iuri]=img

    def preload_images(self, iuris):
        """Queue background decode+resize of these illustration URIs at the verify
        display size (65px height), so when their slice is built on the main
        thread set_sense_illustration() only has to compile() — the cheap Tk half.
        This is the fix for the I/O-bound per-slice build: decode the NEXT slices'
        images while the user reads the current slice aloud. No-op if iuris empty.
        """
        if not iuris:
            return
        self._ensure_preload_worker()
        key=(self.theme.scale,65,'height')
        for iuri in iuris:
            if not iuri:
                continue
            with self._preload_lock:
                if (iuri,key) in self._preload_seen:
                    continue
                img=self.theme.image_cache.get(iuri)
                if img is not None and getattr(img,'_scaled_key',None)==key:
                    continue # already prepared/built at this size
                self._preload_seen.add((iuri,key))
            self._preload_q.put((iuri,key))

    def check_button(self, parent, **kwargs):
        return ui.CheckButton(parent, **kwargs)

    def progressbar(self, parent, **kwargs):
        return ui.Progressbar(parent, **kwargs)

    def attach_context_menu(self, widget, items):
        """Right-click menu on ONE widget (a word on the verify page, a group on
        the distinguish/macrosort pages). ``items`` is [(label, cmd), …]; falsy
        entries are skipped so callers can assemble the list conditionally, and
        an empty list attaches nothing at all.

        The menu is built on FIRST popup, not here: these pages carry hundreds
        of widgets, and a Tk menu per word up front costs real widget memory for
        an affordance most words never use. Deliberately NOT ui.ContextMenu —
        that one binds the whole window through parent.setcontext(), while these
        menus are per-item and each needs its own sense/group."""
        items=[i for i in items if i]
        if not items:
            return
        held={}   # {'menu': the lazily-built ui.Menu}
        def popup(event=None):
            try:
                self.dismiss_context_menu() # never two posted at once
                m=held.get('menu')
                if m is None or not m.winfo_exists():
                    m=held['menu']=ui.Menu(widget._root(), tearoff=0)
                    for label, cmd in items:
                        m.add_command(label=label,
                                      command=self._context_invoke(cmd))
                self._open_context_menu=m
                self._context_post_serial=getattr(event,'serial',None)
                m.tk_popup(event.x_root, event.y_root)
                # NO grab_release() here. The grab tk_popup takes IS what makes a
                # click anywhere — on the menu or off it — put the menu away;
                # releasing it immediately (as ui.ContextMenu does, "don't do Tk
                # redundant grab") leaves the menu posted until an item is picked
                # (Kent 2026-07-28: "these can't just stick around"). tk_popup
                # saves and restores any grab it displaces, so this doesn't
                # fight the app's modal waits.
            except Exception as e:
                # A context menu is a convenience: never take the page down
                # with it (a destroyed widget mid-list is the likely cause).
                log.info("context menu failed: %s", e)
        def gone(event=None):
            """The word (or group) this menu belongs to was destroyed — the page
            advanced, or the action the menu itself offered removed the row — so
            the menu goes with it. A menu whose subject is gone would act on a
            dead sense, and it isn't parented to the widget (it hangs off the
            root, which is what lets it post over the page), so nothing else
            reaps it. Mostly redundant with the click dismissal above, per Kent
            2026-07-28 — but not when the row is destroyed by code."""
            m=held.pop('menu', None)
            if m is None:
                return
            if m is getattr(self, '_open_context_menu', None):
                self._open_context_menu=None
                self._context_post_serial=None
            try:
                if m.winfo_exists():
                    m.unpost()
                    m.grab_release()
                    m.destroy()
            except Exception as e:
                log.info("context menu teardown failed: %s", e)
        # add='+' so this never displaces a binding the widget already has
        # (the play button's praat open, the glyph frame's prev_item).
        widget.bind('<Button-3>', popup, add='+')
        widget.bind('<Destroy>', gone, add='+')
        try:
            if widget._root().tk.call('tk','windowingsystem')=='aqua':
                widget.bind('<Control-Button-1>', popup, add='+') # no Button-3
        except Exception as e:
            log.info("context menu aqua bind skipped: %s", e)
        # Fallback dismissal: if the grab above isn't honoured (this box's
        # XWayland does displace grabs), a click that reaches the WINDOW still
        # clears the menu. Bound once per toplevel — one binding per word would
        # be hundreds — and it dismisses whichever menu is open, not this one.
        try:
            top=widget.winfo_toplevel()
            if not getattr(top,'_azt_ctx_dismiss_bound',False):
                top.bind('<Button>', self.dismiss_context_menu, add='+')
                top._azt_ctx_dismiss_bound=True
        except Exception as e:
            log.info("context menu dismiss bind skipped: %s", e)

    def _context_invoke(self, cmd):
        """Wrap a menu command so choosing it also forgets the menu (Tk unposts
        it for us, but the handle must not outlive the click — the command may
        tear the whole page down)."""
        def run():
            self.dismiss_context_menu()
            cmd()
        return run

    def dismiss_context_menu(self, event=None):
        """Put away any posted per-item context menu. Safe to call when none is
        open (the toplevel <Button> fallback calls it on EVERY click)."""
        m=getattr(self, '_open_context_menu', None)
        if m is None:
            return
        # Widget bindings fire before the toplevel's, so the very right-click
        # that posted the menu would otherwise arrive here and unpost it again
        # immediately. Same event serial = same click; leave it alone.
        if (event is not None and getattr(event, 'serial', None) is not None
                and getattr(event, 'serial', None)
                    == getattr(self, '_context_post_serial', None)):
            return
        self._open_context_menu=None
        self._context_post_serial=None
        try:
            if m.winfo_exists():
                m.unpost()
                m.grab_release() # hand input back to the page
        except Exception as e:
            log.info("context menu dismiss failed: %s", e)

    def set_sense_illustration(self, sense):
        _t0=time.perf_counter() # DIAG (1.3.13): see build_verify_layout log
        try:
            if not sense.image or not sense.image.base_img:
                # don't reload images unnecessarily;
                # base_img is None if image failed to load.
                # local_only: sorting never fetches images (no GitHub
                # resolver) — show what's on disk, or move on.
                iuri=sense.illustrationURI(local_only=True)
                if iuri in self.theme.image_cache:
                    sense.image=self.theme.image_cache[iuri]
                elif iuri:
                    sense.image=ui.Image(iuri)
                    # Cache the loaded image by URI so senses that share an
                    # illustration share one base bitmap (and one scaled pixmap).
                    self.theme.image_cache[iuri]=sense.image
            img=sense.image
            if img and img.base_img:
                # CACHE the scaled PhotoImage: scale() re-runs PIL.resize() AND
                # allocates a NEW Tk PhotoImage (an X pixmap) every call. The same
                # word's 65px image is shown across all three prep checks, every
                # re-verify, the profile sort, and transcription — so build it ONCE
                # per (image, zoom) and hand the same object to every button. Keyed
                # by theme scale + this fixed 65px/height target; rebuilt only if
                # the zoom changes. (Tk shares one pixmap across many widgets.)
                key=(self.theme.scale,65,'height')
                prepared=getattr(img,'_scaled_key',None)==key
                if prepared and getattr(img,'scaled',None) is not None:
                    self._n_built+=1
                    return img.scaled # fully built already (compiled PhotoImage)
                if prepared and getattr(img,'scaled_img',None) is not None:
                    # The slow PIL open/decode/resize was done off-thread by the
                    # preloader (prepare()); only the cheap Tk PhotoImage compile is
                    # left, and it must run here on the main thread.
                    _c=time.perf_counter()
                    img.compile()
                    self._compile_t+=time.perf_counter()-_c
                    self._n_compiled+=1
                    return img.scaled
                img.scale(self.theme.scale, pixels=65, scaleto='height')
                img._scaled_key=key
                self._n_scaled+=1
                return img.scaled
        finally:
            self._img_t+=time.perf_counter()-_t0
    # -- Sort button frame factories --

    def sort_button_frame(self, parent, sort_obj, groups, **kwargs):
        return SortButtonFrame(parent, sort_obj, groups, **kwargs)

    def sort_group_button_frame(self, parent, sort_obj, **kwargs):
        return SortGroupButtonFrame(parent, sort_obj, **kwargs)

    def sort_glyph_group_button_frame(self, parent, sort_obj, **kwargs):
        return SortGlyphGroupButtonFrame(parent, sort_obj, **kwargs)

    def group_button_class(self, macrosort):
        """Return the appropriate button frame class for sort/macrosort."""
        if macrosort:
            return SortGlyphGroupButtonFrame
        return SortGroupButtonFrame

    # -- Composite UI builders --

    def offer_profile_setup(self, parent, note, scope=None):
        """No syllable-profile data yet for this ps: offer to affirm the machine
        analysis as profiles, or go sort syllable profiles first. `scope` (optional)
        spells out which words Trust would affect. Returns 'affirm'/'sort'/'cancel'."""
        result={'choice':'cancel'}
        # Build withdrawn, then deiconify — so it appears composed and placed,
        # rather than mapping empty and reflowing (the "took a bit / wrong spot").
        w=ui.Window(parent, title=_("Set up syllable profiles?"), exit=False,
                    withdrawn=True)
        n=ui.Label(w.frame, text=note, font='instructions',
                  row=0, column=0, columnspan=3, sticky='ew', padx=10, pady=6)
        n.wrap()
        brow=1
        if scope:
            # Show the SCOPE of the trust decision (which words, their primitives,
            # and the machine profile they'd get) so it isn't made blind.
            ui.Label(w.frame, text=scope, font='small', anchor='w', justify='left',
                    row=1, column=0, columnspan=3, sticky='w', padx=10, pady=4)
            brow=2
        def choose(c):
            result['choice']=c
            w.destroy()
        ui.Button(w.frame, text=_("Trust machine analysis; \nmaybe correct later"),
                 cmd=lambda:choose('affirm'), font='instructions',
                 row=brow, column=0, sticky='ew', padx=4)
        ui.Button(w.frame, text=_("Sort syllable profiles manually; \ncome back here later"),
                 cmd=lambda:choose('sort'), font='instructions',
                 row=brow, column=1, sticky='ew', padx=4)
        ui.Button(w.frame, text=_("Cancel"), cmd=lambda:choose('cancel'),
                 font='small', row=brow, column=2, sticky='ew', padx=4)
        w.update_idletasks() #lay out widgets before showing
        w.deiconify()
        w.lift()
        parent.wait_window(w)
        return result['choice']
    def build_present_sense(self, runwindow_frame, buttonframe, text, sense):
        """Build the sort item display for a single sense. Returns the frame."""
        sortitem = ui.Frame(runwindow_frame, column=1, row=1,
                           sticky='nw', border=True)
        l = ui.Label(sortitem, text=text, font='readbig', sticky='w')
        img = getattr(sense, 'image', None)
        if img:
            try:
                img.scale(l.theme.scale, pixels=65, scaleto='height')
                scaled = getattr(img, 'scaled', None)
            except Exception as e:
                log.info(f"Couldn't scale image for {sense.id}: {e}")
                scaled = None
            # A missing/corrupt file can load without raising but yield no
            # scaled bitmap: sorting just shows NO image (word collection
            # shows its 'no image' placeholder via ImageFrame instead).
            if scaled is not None:
                l['image'] = scaled
                l['compound'] = 'left'
        l.wrap()
        buttonframe.sortitem = sortitem
        # The class escape was a button at the BOTTOM of the page until Kent
        # 2026-08-21 — now it is a right-click on the word, matching the verify
        # page. Same gate the button had (SortButtonFrame: 'S' sort, non-primitive
        # check); advancing still means what it meant there.
        try:
            params = buttonframe.program.params
            if (getattr(buttonframe, 'cvt', None) == 'S'
                    and not params.is_syllable_primitive_check(
                        getattr(buttonframe, 'check', None))):
                def advance():
                    # The word is already out of the live to-sort list, so tell
                    # sortselected to ADVANCE rather than read the now-empty
                    # selection as Exit (which fired the spurious 'not done'
                    # warning). Mirrors 'Not {profile}'.
                    buttonframe.task._notprofile_advance = True
                    if getattr(buttonframe, 'sortitem', None):
                        buttonframe.sortitem.destroy()
                self.attach_context_menu(l, self.class_escape_items(
                            buttonframe.task, sense, on_applied=advance))
            elif (getattr(buttonframe, 'cvt', None) != 'S'
                    and not getattr(buttonframe, 'macrosort', False)
                    and buttonframe.program.slices.profile()):
                # SEGMENTAL/TONE: 'Not {profile}' on the word (Kent 2026-08-31).
                # Same gesture the verify page already offers
                # (sorting_engine's `elif profile:` menu item) and the same
                # action as the sort page's own button, which STAYS below for
                # now — two affordances, one wording, deliberately identical.
                # macrosort is excluded because the thing presented there is a
                # GROUP, not a word, so "not this profile" has no referent.
                profile = buttonframe.program.slices.profile()
                def notprofile():
                    # Mirrors sort_buttons.getanotherskip's notprofile() — keep
                    # the two in step, and if that button is ever removed this
                    # becomes the only copy.
                    todo = buttonframe.task.itemstosort()
                    if todo:
                        buttonframe.task.unverify_profile(todo[0])
                    # Advance with NO group chosen → maybesort restarts without it.
                    if getattr(buttonframe, 'sortitem', None):
                        buttonframe.sortitem.destroy()
                self.attach_context_menu(l, [
                    (_("Not {profile}").format(profile=profile), notprofile)])
        except Exception as e:
            log.info("sort-page class-escape menu skipped: %s", e)
        return sortitem

    def build_present_group(self, runwindow_frame, buttonframe, sort_obj,
                           item, kwargs):
        """Build the sort item display for a group. Returns frame or None."""
        sortitem = ui.Frame(runwindow_frame, border=True,
                           column=1, row=1, sticky='nw')
        ui.Label(sortitem, text='', width=5, sticky='')
        # reverifiable: the group presented for macrosorting may be the wrong
        # group to be giving a letter to at all — right-click reverifies it
        # first (Kent 2026-07-28), instead of hunting the Advanced menu.
        tosort_frame = SortGroupButtonFrame(sortitem, sort_obj,
                                           show_check=True, label=True,
                                           reverifiable=True,
                                           sticky='', **kwargs)
        if tosort_frame.hasexample:
            buttonframe.sortitem = sortitem
            return sortitem
        else:
            tosort_frame.destroy()
            return None

    def build_sort_layout(self, runwindow, img_mod, page_icon,
                         instructions, sort_obj, groups, macrosort):
        """Build the main sort window layout. Returns (groupsFrame, buttonframe)."""
        f = runwindow.frame
        ui.Label(f, image=f'sort{img_mod}',
                row=0, column=0, rowspan=3, sticky='new', anchor='center')
        ui.Label(f, image=page_icon, image_pixels=270,
                row=3, column=0, #rowspan=3, 
                sticky='nw')
        groupsFrame = ui.Frame(f, column=1, row=2,
                              rowspan=2, pady=0, sticky='nsew')
        f.rowconfigure(1, weight=0)
        f.rowconfigure(2, weight=1)
        f.columnconfigure(0, weight=0)
        f.columnconfigure(1, weight=1)
        ui.Label(groupsFrame, text=instructions, font='instructions',
                anchor='c', sticky='sew')
        buttonframe = SortButtonFrame(groupsFrame, sort_obj, groups,
                                     macrosort=macrosort,
                                     joinable=True,
                                     row=1, sticky='nsew', columnspan=2)
        return groupsFrame, buttonframe

    def attach_group_rename(self, widgets, parent, task, group,
                           on_renamed=None):
        """Right-click → "this group is misnamed" on every surface that shows the
        profile NAME: the verify page's title, instructions and last button
        (Kent 2026-08-24 — the same trio `syllable_group_name`'s docstring
        names). Deliberately NOT the group button beside "Reverify this group":
        reverify appears alone.

        No-op outside the syllable PROFILE check — the primitives' groups
        ('C'/'V', syllable counts) are not names anyone renames."""
        try:
            params=task.program.params
            if getattr(task,'cvt',None)!='S':
                return
            if params.is_syllable_primitive_check(params.check()):
                return
            items=[(_("These words aren’t {group}…").format(group=group),
                    lambda: self.ask_group_rename(parent, task, group,
                                                on_renamed=on_renamed))]
            for w in widgets:
                if w is not None:
                    self.attach_context_menu(w, items)
        except Exception as e:
            log.info("group-rename menu skipped: %s", e)

    def ask_group_rename(self, parent, task, group, on_renamed=None):
        """'These words aren't {group}…' — page 1. The same chooser
        `pick_syllable_profile` uses for ONE word, with the verb changed: it
        renames the GROUP. Legal profiles for this class that aren't already in
        play, plus 'Other…' → by-hand entry."""
        params=task.program.params
        beg,syls,end=params.parse_profile_class(task.program.slices.profile())
        if beg is None:
            log.info("ask_group_rename: no profile class set; ignoring.")
            return
        options=[p for p in params.unused_profiles_for_class(beg,syls,end,
                                                    limit=12) if p!=group]
        w=ui.Window(parent, title=_("What is this group really?"), exit=False)
        ui.Label(w.frame, text=_("These words are all marked {group}. "
                    "What should they be?").format(group=group),
                    font='instructions', row=0, column=0, sticky='ew')
        def apply(new):
            w.destroy()
            task.rename_profile_group(group,new)
            if on_renamed:
                on_renamed()
        # THE OPTIONS SCROLL; THE ESCAPES DO NOT (Kent 2026-08-31, Windows:
        # "bottom options run off the page"). Everything used to be gridded
        # straight into w.frame — up to twelve profile buttons plus the two
        # escapes, fifteen rows at font 'normal' — so on a short or scaled
        # screen the page simply ran past the bottom edge. The rows that fell
        # off were the LAST two, i.e. 'Other…' and 'Cancel', and this window is
        # built exit=False, so a user who cannot reach Cancel has no button at
        # all. Put the variable-length list in a scroll frame and keep the
        # fixed escapes outside it, always on screen — the same shape Kent
        # asked for on the sibling entry page ("the OK|these groups line should
        # be just under the field").
        w.frame.grid_rowconfigure(1, weight=1)
        w.frame.grid_columnconfigure(0, weight=1)
        scroll=ui.ScrollingFrame(w.frame, row=1, column=0, sticky='nsew')
        r=0
        for prof in options:
            ui.Button(scroll.content, text=prof, cmd=lambda p=prof:apply(p),
                        anchor='w', font='normal', row=r, column=0,
                        sticky='ew'); r+=1
        if not options:
            ui.Label(scroll.content,
                        text=_("(every simple profile here is already used)"),
                        font='instructions', row=r, column=0, sticky='ew')
        ui.Button(w.frame, text=_("Other… (set a profile by hand)"),
                    cmd=lambda:self._group_rename_freeentry(w, parent, task,
                                                group, beg, syls, end, apply),
                    anchor='w', relief='flat', font='normal',
                    row=2, column=0, sticky='ew')
        ui.Button(w.frame, text=_("Cancel — go back"), cmd=w.destroy,
                    anchor='w', relief='flat', font='normal',
                    row=3, column=0, sticky='ew')
        # Reflow or the list is invisible (grid_propagate(0)) — but SCHEDULED
        # and only once the window is really mapped: reflow drains
        # synchronously, and XWayland deadlocks draining into an unmapped
        # window (ui_tkinter.py:1411-1415). Same rule as the boards.
        def _settle(n=10):
            try:
                if not scroll.winfo_exists():
                    return
                if not w.winfo_viewable():
                    if n>0:
                        w.after(50,lambda:_settle(n-1))
                    return
                scroll.reflow()
            except Exception as e:
                log.info("group-rename list reflow failed: %s", e)
        try:
            w.after_idle(_settle)
        except Exception as e:
            log.info("could not schedule group-rename reflow: %s", e)
        return w

    def _group_rename_freeentry(self, page1, parent, task, group,
                               beg, syls, end, apply):
        """Page 2: type the profile by hand, validated against the class
        primitives exactly as `_syllable_profile_freeentry` does for one word."""
        page1.destroy()
        params=task.program.params
        w=ui.Window(parent, title=_("Set a profile by hand"), exit=False)
        warn=ui.Label(w.frame, text='\n'.join([
            _("⚠ Setting a profile by hand is a linguist’s "
            "call — work with your language team."),
            _("This renames EVERY word marked {group}.").format(group=group),
            _("It must be {beg}-initial, {end}-final, and "
            "{n} syllable(s)").format(beg=beg,end=end,n=syls)]),
            font='instructions', row=0, column=0, columnspan=2, sticky='ew')
        warn.wrap()
        var=self.string_var(value='')
        self.entry_field(w.frame, text=var).grid(row=1, column=0, sticky='ew')
        msg=ui.Label(w.frame, text='', font='instructions', row=2, column=0,
                    columnspan=2, sticky='ew')
        def submit():
            prof=(var.get() or '').strip().upper()
            if not params.profile_fits_class(prof,beg,syls,end):
                msg['text']=_("‘{p}’ doesn’t fit this class.").format(p=prof)
                return
            w.destroy()
            apply(prof)
        ui.Button(w.frame, text=_("Use this profile"), cmd=submit,
                    anchor='c', font='instructions', row=3, column=0,
                    sticky='ew')
        ui.Button(w.frame, text=_("← Back"),
                    cmd=lambda:(w.destroy(),
                                self.ask_group_rename(parent,task,group)),
                    anchor='c', font='instructions', row=3, column=1,
                    sticky='ew')
        return w

    def build_verify_layout(self, runwindow, title, page_icon, instructions,
                           prog_text, img_mod, group,
                           items, sort_obj, macrosort, oktext,
                           min_to_multicolumn, buttoncolumns,
                           verifybutton_fn, join_fn, prep=None):
        """Build the verify window layout.
        Returns (buttonframe, verifycanary)."""
        f = runwindow.frame
        # Let the content area expand to fill the kiosk screen
        # Override the centering spacers (rows 0,2 weight=3 from Window.post_tk_init)
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(1, weight=1)
        titles = ui.Frame(f, column=1, row=0, columnspan=1, sticky='w')
        titlelabel = ui.Label(titles, text=' '.join(title), font='title',
                column=0, row=0, sticky='w')
        # Optional progress indicator beside the title (e.g. "(N remaining)" /
        # "(last group)"); supplied by the caller as prog_text, blank if None.
        ui.Label(titles, text=(prog_text or ''), anchor='w', padx=10,
                column=1, row=0, sticky='ew')
        ui.Label(f, image=page_icon, text='', row=0, column=0, sticky='nw')
        i = ui.Label(titles, text=instructions,
                    row=1, column=0, columnspan=2, sticky='wns')
        i.wrap()
        if group != 'NA':
            ui.Label(f, image=f'verify{img_mod}', text='',
                    row=1, column=0, sticky='nws')
        #If we ever generalize this, we need to add macrosort below.
        if not macrosort and False: #off for now
            def _join_now(x):
                join_fn(sortgroup=x)
                verifycanary.destroy()
            ui.Button(f, text=_("This is a duplicate group"),
                 cmd=lambda x=group:_join_now(x), anchor='w',
                 font='instructions', row=2, sticky='ew')
        # Canary holds the OK button; the user clicks it when the list is all
        # confirmed. Created now (so verify can wait on it) but gridded AFTER the
        # items (so it sits right below them and doesn't inflate the scrollregion
        # — gridding it at a huge sentinel row blew the scroll region up ~5x).
        if macrosort:
            # reverifiable: each row here is a VERIFIED sort group being checked
            # against a letter. Left click removes it from the letter; right click
            # sends it back to verify, for when the group itself is the problem
            # (Kent 2026-07-28).
            buttonframe = SortButtonFrame(f, sort_obj,
                                         list(items), macrosort=True,
                                         show_check=True, reverifiable=True,
                                         remove_on_click=True, column=1,
                                         row=1, sticky='nsew', columnspan=2)
            verifycanary = ui.Frame(buttonframe.content, sticky='ew')
            verifycanary.grid(row=buttonframe.content.nrows(),column=0,sticky='ew')
            ui.Button(verifycanary, text=oktext, cmd=verifycanary.destroy,
                     anchor='w', font='instructions',
                     column=0, row=0, sticky='ew')
            # Reveal the kiosk run window. SortButtonFrame built itself behind its
            # own `with task.waiting()` wait, but that wait is opened on the
            # (withdrawn) TaskWindow, so its showafterwait is False and waitdone
            # reveals nothing — and by here that wait is already inactive, so this
            # waitdone() is a no-op. The run window was created withdrawn
            # (getrunwindow, no msg) and nothing else reveals it, so deiconify it
            # explicitly, exactly as the sort path does in presenttosort(). Without
            # this the macrosort verify window never appears.
            runwindow.waitdone() #built synchronously
            if not runwindow.exitFlag.istrue():
                runwindow.deiconify()
                runwindow.update_idletasks()
                # REFLOW WITH THE CANARY IN IT. Nothing did, and that is the
                # whole bug (field, OBT's Windows machine, 2026-09-01): the OK
                # button is gridded into the scroll content just above, but the
                # only reflow armed for this page was scheduled at the END of
                # SortButtonFrame.__init__ — BEFORE the canary existed — so the
                # FIFO idle queue could run _do_configure_interior on a stale
                # reqheight and set the scrollregion to end at the last group
                # button. The button was built and alive the whole time, simply
                # outside the scrollable area, with the scrollbar already at its
                # end: nothing to scroll to. Confirmed by test — removing one
                # group row mutated the content, re-fired <Configure>, and the
                # button appeared.
                #
                # WORSE THAN COSMETIC, which is why this is a small fix to a
                # serious bug: the page blocks on wait_window(verifycanary), so
                # with OK unreachable the page can only be QUIT, never finished.
                #
                # Placed HERE rather than beside the grid() call: reflow() reads
                # content.winfo_reqheight(), and grid() only queues that
                # recompute as an idle task — the update_idletasks() above is
                # what makes the measurement true. Exactly the trap
                # ScrollingFrame.reflow's own docstring documents, and the
                # non-macrosort branch's resume_configure() at the end of its
                # word list is the same move.
                buttonframe.reflow()
        else:
            buttonframe = ui.ScrollingFrame(f, row=1, column=1, rowspan=2,
                                            sticky='wsn')
            real_items=[it for it in items if it is not None]
            # Columns are the user's setting (like every other sort window).
            bc = max(buttoncolumns, 1)
            ntotal=len(real_items)
            # SINGLE PAGE, built behind a background-load WAIT (restored per Kent
            # 2026-06-17). The list is slice-bounded (one CV-profile in one ps for
            # segmental, ≤MAX_SLICE for syllable prep). Build the first screenful
            # behind a "loading" wait, reveal, then stream the rest in behind it —
            # the proven segmental path. (The real freeze is page SIZE / the next
            # window transition, handled by small slices + a reused window.)
            # Completion sentinel: off-screen (child of f, NOT the scroll content)
            # so wait_window(verifycanary) returns only on the final OK. The
            # visible OK button lives at the END of the word list.
            verifycanary=ui.Frame(f)
            reveal=min(24, ntotal) # first screenful shown before the rest streams
            nav_row=(ntotal+bc-1)//bc # row just past the last item
            # Instrumentation (to answer "what's limited at N items"): time the
            # build and log RSS before/after. Read these in the log as
            # "verify build: N items in Ts, RSS A→B MB".
            _t0=time.perf_counter(); _rss0=_rss_mb()
            self._diag_reset() # DIAG: partition this build's seconds
            # Breadcrumb BEFORE the build: a wedged build used to log
            # nothing at all — not even its size (2026-07-24, the
            # crippled V1=V2 NA page).
            log.info("verify build starting: %d items, %d cols", ntotal, bc)
            # DIAG (1.3.14): reset the run window's per-tick drive_work counters.
            runwindow._dw_work_t=runwindow._dw_prog_t=runwindow._dw_gap_t=0.0
            runwindow._dw_ticks=0; runwindow._dw_last_end=None
            def _place(slot):
                _v=time.perf_counter()
                verifybutton_fn(buttonframe.content, real_items[slot],
                               row=slot // bc, column=slot % bc, label=False)
                self._vb_t+=time.perf_counter()-_v
            def _grid_ok():
                # OK at the END of the word list (where OK belongs, as in every
                # other sort); clicking it ends the verify (destroys the canary).
                navframe=ui.Frame(buttonframe.content, sticky='ew')
                navframe.grid(row=nav_row, column=0, columnspan=bc, sticky='ew')
                okbutton=ui.Button(navframe, text=oktext, font='instructions',
                         cmd=verifycanary.destroy,
                         column=0, row=0, sticky='ew', padx=4)
                # The profile name is shown in all three of these, so "this
                # group is misnamed" is available wherever the name is (Kent
                # 2026-08-24). Renaming ends the page: the group the user was
                # verifying no longer exists under that name.
                self.attach_group_rename([titlelabel, i, okbutton], runwindow,
                            sort_obj, group,
                            on_renamed=verifycanary.destroy)
                _r=time.perf_counter()
                buttonframe.resume_configure() # one reflow now the list is whole
                self._reflow_t+=time.perf_counter()-_r
                # cached images ≈ live scaled pixmaps we're holding (a
                # client-side proxy for X pixmap pressure; cf. xrestop "Pixmaps").
                try:
                    ncached=len(self.theme.image_cache)
                except Exception:
                    ncached=-1
                _total=time.perf_counter()-_t0
                log.info("verify build: %d items in %.1fs, RSS %.0f→%.0f MB "
                         "(%d cols, %d cached imgs)", ntotal,
                         _total, _rss0, _rss_mb(), bc, ncached)
                # DIAG (1.3.14): full decomposition. per-item work = verifybutton_fn
                # (backend status/annotation lookups + widget build); drive = the
                # streaming pump — gap is after()+event-loop paint, the suspected
                # XWayland per-item cost. residual is whatever none of these caught.
                _dw_work=getattr(runwindow,'_dw_work_t',0.0)
                _dw_prog=getattr(runwindow,'_dw_prog_t',0.0)
                _dw_gap=getattr(runwindow,'_dw_gap_t',0.0)
                _dw_ticks=getattr(runwindow,'_dw_ticks',0)
                _backend=self._vb_t-self._wid_t-self._img_t
                _resid=(_total-self._vb_t-self._reflow_t-_dw_prog-_dw_gap)
                log.info("  per-item work %.1fs [verifybutton; image %.1fs "
                         "(built=%d compiled=%d[%.1fs pixmap] scaled=%d), widgets "
                         "%.1fs, backend %.1fs] | drive: genwork %.1fs, progressbar "
                         "%.1fs, eventloop/paint %.1fs over %d ticks | reflow %.1fs "
                         "| residual %.1fs", self._vb_t, self._img_t, self._n_built,
                         self._n_compiled, self._compile_t, self._n_scaled,
                         self._wid_t, _backend, _dw_work, _dw_prog, _dw_gap,
                         _dw_ticks, self._reflow_t, _resid)
            def _build_all():
                # BATCH build (1.3.28): place ALL items with NO per-tick flush. The
                # per-item synchronous progressbar flush was the ~0.6s/item cost AND
                # the large-slice deadlock (a flush per item); the actual widget work
                # is sub-second even at big slices. So build the whole list under one
                # suspend_configure, then ONE reflow + ONE drained commit.
                if runwindow.exitFlag.istrue():
                    return
                for slot in range(ntotal):
                    if runwindow.exitFlag.istrue():
                        return
                    _place(slot)
                    if slot % 50 == 49: # progress: how far, and is it images?
                        log.info("verify build progress: %d/%d (img %.1fs "
                                 "of %.1fs)", slot+1, ntotal, self._img_t,
                                 time.perf_counter()-_t0)
                _grid_ok() # OK button + single resume_configure reflow + timing log
                # VIRTUALIZE (1.3.32): unmap rows outside the viewport so waitdone's
                # render paints only the ~visible dozen, not all N. EXPERIMENTAL —
                # comment out this block (or revert the version) to disable.
                # Skipped when the whole list fits the first screenful: nothing to
                # unmap, and its winfo/grid round-trips are pure risk (2026-07-10
                # wedge was somewhere between _grid_ok and the reveal).
                # DIAG-reveal breadcrumbs (grep to remove): one line BEFORE each
                # synchronous-Tk step after the build, so a wedge names its call
                # even without a faulthandler stack.
                if ntotal>reveal:
                    log.info("DIAG-reveal virtualize starting (%d items)", ntotal)
                    try:
                        self._virtualize_verify(buttonframe, nav_row+1, bc)
                    except Exception as e:
                        log.info("verify virtualize skipped: %s", e)
                if runwindow.iswaiting():
                    _wd=time.perf_counter() # DIAG (1.3.30): waitdone()'s full update()
                    log.info("DIAG-reveal waitdone starting") # renders the build backlog
                    runwindow.waitdone()    # while the window is hidden — the real gap
                    log.info("verify reveal (waitdone) %.1fs",
                             time.perf_counter()-_wd)
                else:
                    # ONE commit so the complete window paints (no per-item flush did
                    # it). ONLY when no wait covered the build: waitdone above already
                    # did parent.update()+deiconify, so repeating update() here was a
                    # redundant second synchronous drain right after deiconify — the
                    # known XWayland wedge shape (cf. Wait.activate's scoped guard).
                    # update() DRAINS the event queue while flushing, which avoids the
                    # XWayland write-deadlock a bare update_idletasks hits on a large
                    # backlog.
                    _c=time.perf_counter() # DIAG (1.3.29): measure the PAINT — the gap
                    log.info("DIAG-reveal commit update() starting") # between "verify
                    try:                    # build" and the window appearing
                        runwindow.update()
                    except Exception as e:
                        log.info("verify commit update() failed: %s", e)
                    log.info("verify commit (paint) %.1fs", time.perf_counter()-_c)
            # Suspend the per-item scrollregion reflow (each grid otherwise schedules
            # an O(n) winfo_reqheight reflow — a synchronous X round-trip — so a naive
            # build is O(n²) round-trips). One reflow at the end, in _grid_ok.
            buttonframe.suspend_configure()
            runwindow.wait(prep, thenshow=True) # "Loading…" while we batch-build
            runwindow.after(1, _build_all) # let the dialog paint, then build it all
        return buttonframe, verifycanary

    def _virtualize_verify(self, buttonframe, nrows, bc):
        """EXPERIMENTAL (1.3.32): render only the rows near the viewport; map the
        rest on scroll. Tk renders every *mapped* gridded child, so unmapping the
        off-screen rows cuts the waitdone() render from ~0.5s×N to ~0.5s×(visible).
        Each row's height is pinned (minsize) so the scrollbar still reflects the
        whole list while most rows are unmapped. Contained here — revert this
        version (or just the call site) to disable."""
        canvas=buttonframe.canvas; content=buttonframe.content
        # Capture row -> widgets while everything is still gridded (grid_remove
        # hides widgets from grid_slaves, so we couldn't rediscover them later).
        rowmap={}
        for w in content.winfo_children():
            try: r=int(w.grid_info().get('row',-1))
            except Exception: r=-1
            if r>=0: rowmap.setdefault(r,[]).append(w)
        if not rowmap: return
        # Row height: a real reqheight if Tk has computed it, else a safe estimate.
        # (Do NOT update_idletasks here — that would render all N before we unmap.)
        rowH=0
        _reqh={} # DIAG-virt: what rows 0/1 actually measured
        for _r in (0,1):
            for w in (rowmap.get(_r) or []):
                try:
                    _h=w.winfo_reqheight()
                    _reqh.setdefault(_r,[]).append(_h)
                    rowH=max(rowH,_h)
                except Exception: pass
        _measured=rowH
        if rowH<10: rowH=80
        for r in range(nrows):
            content.rowconfigure(r, minsize=rowH)
        # DIAG-virt (2026-07-27, grep to remove): the numbers that discriminate
        # the "big verify page shows only its title" failure. Two candidates,
        # both in this function: (a) rowH inflated by a tall UNSCALED image in
        # row 0/1 — every row then inherits it as minsize, and rows*rowH can
        # pass the X11 32767px scroll-region cap; (b) the mapped window is
        # computed from a STALE yview, since the run window is REUSED and the
        # user reaches the previous page's OK button by scrolling to its bottom.
        _pinned=nrows*rowH
        log.info("DIAG-virt setup: rows=%d rowH=%d (measured=%d%s; reqheights "
                 "%s) pinned=%dpx%s", nrows, rowH, _measured,
                 '' if _measured>=10 else ' → fallback 80', _reqh, _pinned,
                 ' OVER the 32767px X11 scroll cap!' if _pinned>32767 else '')
        # A NEW page starts at the top, and must NOT inherit the previous page's
        # scroll offset: the run window is REUSED, and the user reaches the last
        # page's OK button by scrolling to its bottom. yview is a fraction of the
        # CURRENT scrollregion, so a leftover offset against this page's
        # (shorter) region reads far past the end — field log 2026-07-27:
        # yview=(2.0,2.0) → first=98 of 49 rows → the mapped range came out
        # INVERTED, [92,49), so EVERY row was unmapped and the page showed only
        # its title.
        try: canvas.yview_moveto(0)
        except Exception: pass
        state={'win':None}
        def window():
            if not canvas.winfo_exists(): return
            ch_raw=canvas.winfo_height()
            ch=ch_raw
            if ch<=1: ch=canvas.winfo_screenheight() # not mapped yet → estimate
            try: yv=canvas.yview()
            except Exception: yv=None
            top=yv[0] if yv else 0.0
            if not 0.0<=top<=1.0: top=0.0 # stale/unmapped canvas: distrust it
            first=int(top*nrows); visible=int(ch/rowH)+1; buf=6
            lo,hi=max(0,first-buf),min(nrows,first+visible+buf)
            if lo>=hi: # INVARIANT: never unmap every row (that blanks the page)
                lo,hi=0,min(nrows,visible+buf)
            if state['win']==(lo,hi): return
            state['win']=(lo,hi)
            # BEFORE the grid calls (DIAG-reveal discipline: a wedge must name
            # its step). Counts come from rowmap, so this needs no Tk call.
            log.info("DIAG-virt window: canvas h=%d%s yview=%s top=%.4f "
                     "first=%d visible=%d → mapping rows [%d,%d) of %d "
                     "(mapped=%d unmapped=%d)", ch_raw,
                     (' → screen estimate %d' % ch) if ch_raw<=1 else '',
                     yv, top, first, visible, lo, hi, nrows,
                     sum(1 for r in rowmap if lo<=r<hi),
                     sum(1 for r in rowmap if not lo<=r<hi))
            for r,ws in rowmap.items():
                vis=lo<=r<hi
                for w in ws:
                    try: (w.grid() if vis else w.grid_remove())
                    except Exception: pass
        def poll():
            if not canvas.winfo_exists(): return
            window(); canvas.after(150, poll)
        window()              # initial unmap, BEFORE waitdone renders the slice
        canvas.after(150, poll)

    def ask_syllable_count(self, parent, n):
        """Modal ±1 chooser for a miscounted word during Task-1 count verify
        (the count check has no sort page, so a flag-out is fixed via
        Shorter/Longer). Returns the new count (int), or None if cancelled."""
        result={'value':None}
        # Use ui.Window (like every other dialog): it accepts `title`, themes,
        # builds the .frame to grid into, and surfaces over the kiosk-fullscreen
        # run window. (ui.Toplevel passes kwargs straight to tkinter, so a
        # `title=` kwarg becomes the invalid option `-title` and raises.)
        w=ui.Window(parent, title=_("How many syllables?"),exit=False,
                    withdrawn=True) # stay hidden until positioned (see below)
        # ui.Label(w.frame, text='\n'.join([
        #         # _("This word has a different number of syllables."),
        #         _("Is it shorter or longer than the rest of these words?")]), font='instructions',
        #         row=0, column=0, columnspan=3, sticky='ew')
        def choose(v):
            result['value']=v
            w.destroy()
        col=0
        shorter=None
        if n>1:
            shorter=ui.Button(w.frame, text=_("Shorter ({n})").format(n=n-1),
                     cmd=lambda:choose(n-1), font='instructions',
                     row=1, column=col, sticky='ew'); col+=1
        longer=ui.Button(w.frame, text=_("Longer ({n})").format(n=n+1),
                 cmd=lambda:choose(n+1), font='instructions',
                 row=1, column=col, sticky='ew'); col+=1
        ui.Button(w.frame, text=_("Cancel"), cmd=w.destroy, font='small',
                 row=1, column=col, sticky='sew')
        # Put the pointer BETWEEN Shorter and Longer (on their row), not at the
        # window's top-left — otherwise reaching 'Longer' is a longer travel than
        # 'Shorter', biasing the choice. Estimate the offset from the buttons'
        # REQUESTED sizes while still withdrawn (winfo_reqwidth is valid before
        # mapping, so we never draw it off-position first). Buttons are packed
        # left in adjacent columns, so Shorter spans [0,sw], Longer [sw,sw+lw];
        # their centre-midpoint is (3*sw+lw)/4. With only 'Longer' (n==1) it's
        # column 0, so aim at lw/2. (Ignores the few-px frame border — an
        # estimate, as discussed.) Best-effort: WM may ignore client positioning.
        px,py=parent.winfo_pointerxy()
        gx,gy=px,py # fallback: pointer at top-left, if measuring fails
        try:
            w.update_idletasks() # compute requested sizes (valid while withdrawn)
            lw=longer.winfo_reqwidth()
            tx=(3*shorter.winfo_reqwidth()+lw)//4 if shorter is not None else lw//2
            ty=w.winfo_reqheight()//2 # one button row → centre vertically on it
            gx,gy=max(px-tx,0),max(py-ty,0)
        except Exception as e:
            log.info("couldn't position syllable chooser: %s", e)
        w.geometry('+{}+{}'.format(gx,gy))
        w.deiconify() # first time it's shown, it's already in place
        w.lift()
        parent.wait_window(w)
        return result['value']

    def class_escape_items(self, task, sense, on_applied=None):
        """[(label, cmd), …] for attach_context_menu: the one-axis moves out of a
        syllable profile class — flip word-initial, flip word-final, Shorter,
        Longer. Three of them at one syllable, since nothing is shorter.

        Was a WINDOW (ask_class_escape) until Kent 2026-08-21 asked for the moves
        to be offered directly on the word, on both the sort page and the profile
        verify page — the verify page already had a context-menu entry whose only
        job was to open that window, and the sort page had a button at the bottom
        of the page.

        Lives here, not on the sort button frame, because BOTH pages offer it
        (Kent 2026-07-29 — the verify page is where a misfiled word actually gets
        noticed, and it had no escape). The data write is the task's
        (`escape_profile_class`); `on_applied` is how each page says what "the word
        is gone from here" means — the sort page destroys its sort item to advance,
        the verify page drops the row."""
        params=task.program.params
        ftype=task.ftype
        analang=task.program.db.analang
        av=sense.annotationvaluebyftypelang
        beg=av(ftype,analang,'#C')
        end=av(ftype,analang,'C#')
        syls=av(ftype,analang,'syls')
        try:
            n=int(syls)
        except (TypeError,ValueError):
            n=1
            syls=str(n) # unset syls: don't put '' into the destination prose
        flip=lambda v:'V' if v=='C' else 'C'
        # (button label, primitive check, value). Each label names ONLY the axis
        # it moves. Labelling every button with the whole destination class made
        # all four restate all three dimensions, so the one thing that differed
        # sat mid-string; the class is stated ONCE below instead (Kent 2026-08-21).
        # The per-axis renderers already existed next to begend_name.
        moves=[(params.profile_class_initial_name(flip(beg)),'#C',flip(beg)),
                (params.profile_class_final_name(flip(end)),'C#',flip(end))]
        if n>1:
            moves.append((_("Shorter"),'syls',str(n-1)))
        moves.append((_("Longer"),'syls',str(n+1)))
        def apply(check,value):
            task.escape_profile_class(sense,check,value)
            if on_applied:
                on_applied()
        # No "this word is currently marked …" header any more: the menu is posted
        # on the word itself, so the context is the gesture. attach_context_menu
        # takes (label, cmd) pairs and has no disabled-header entry.
        return [(label,lambda c=check,v=value:apply(c,v))
                    for label,check,value in moves]

    def build_verify_button(self, parent, text, sense, is_label,
                           notok_fn, row, column, ipady, menu_items=None,
                           **kwargs):
        """Build a single verify button or label. Returns (widget, frame_or_None).
        menu_items (see attach_context_menu) hangs a right-click menu on the
        word — the verify page's escape hatches, which the left click can't
        carry (it already means "this one is different")."""
        # A non-breaking space (\xa0) in the text — e.g. an untranslated "?\xa0?"
        # gloss — can blank the WHOLE label on this Tk/font, leaving the row
        # showing only its illustration. Normalise it to a plain space for
        # display (data is untouched). Other non-ASCII in the row — the em-dash
        # separator and quote() curly quotes — render fine in every other row.
        text=(text or '').replace('\xa0',' ')
        _w=time.perf_counter() # DIAG (1.3.13): widget-creation time, vs image time
        if is_label:
            b = ui.Label(parent, text=text, column=column, row=row,
                        sticky='ew', ipady=ipady, **kwargs)
            bf = None
        else:
            bf = ui.Frame(parent, pady=1, padx=1, column=column, row=row,
                         sticky='w', border=True)
            b = ui.Button(bf, text=text, pady='0', cmd=notok_fn,
                         column=0, row=0, sticky='ew',
                         ipady=ipady, **kwargs)
        self._wid_t+=time.perf_counter()-_w
        # ZERO THE WIDGET'S OWN VERTICAL CHROME (Kent 2026-08-31: verify rows far
        # taller than their one line of text). The `pady='0'` above does NOT do
        # this: ui.Button routes a constructor pady to the GRID, so the widget's
        # own pady is still Tk's default — the same trap recorded at
        # sort_buttons.check_segments_row ("ui.Label routes constructor padx to
        # the GRID, so the Label's own 1px-a-side default is only reachable after
        # construction"), which is why that method sets l['padx'] AFTER building.
        # Tk's per-widget defaults are small individually but they stack with the
        # frame's border on every row of a whole slice. highlightthickness is the
        # focus ring, invisible here and pure height. borderwidth is deliberately
        # NOT touched: it draws the visible box these pages are designed around.
        for _k,_v in (('pady',0),('ipady',0),('highlightthickness',0)):
            try:
                b[_k]=_v
            except Exception:
                pass # not every widget/backend carries every option
        b['image'] = self.set_sense_illustration(sense)
        b['compound'] = 'left'
        # ONE-SHOT height breakdown (Kent 2026-08-31: verify rows far taller than
        # their one line of text, on Windows). Three candidates — font, image, or
        # padding — and inspection has not settled it: rows WITHOUT an
        # illustration are as tall as rows with one, which rules the image out,
        # and lowverticalspace=true already gives ipady=0/pady=1, which rules out
        # the padding I was asked to reduce. So measure instead of infer. Once per
        # page build, on the first row, and every field wrapped: a diagnostic must
        # never be what breaks the page.
        if not getattr(self,'_logged_row_height',False):
            self._logged_row_height=True
            try:
                import tkinter.font as _tkfont
                b.update_idletasks()
                f=_tkfont.Font(font=b['font'])
                img=b['image']
                log.info("DIAG-rowheight: button req=%s actual=%s | frame req=%s "
                         "| font %r linespace=%s | image h=%s | widget pady=%r "
                         "ipady(grid)=%r | scale=%s",
                         b.winfo_reqheight(), b.winfo_height(),
                         bf.winfo_reqheight() if bf is not None else 'n/a',
                         b['font'], f.metrics('linespace'),
                         (b.tk.call('image','height',img) if img else 0),
                         b['pady'], ipady, self.theme.scale)
            except Exception as e:
                log.info("DIAG-rowheight failed: %s", e)
        if menu_items:
            self.attach_context_menu(b, menu_items)
        return b, bf

    def build_join_layout(self, runwindow, title, page_icon, img_mod):
        """Build the join window layout.
        Returns (titles_frame, progress, response_button_frame, pair_frame)."""
        f = runwindow.frame
        f.titles = ui.Frame(f, column=1, row=0, columnspan=1, sticky='ew')
        ui.Label(f.titles, text=title, font='title', anchor='w',
                column=0, row=0, sticky='ew')
        progress = ui.Progressbar(f.titles, row=1, sticky='ew')
        ui.Label(f, image=page_icon, text='', row=0, column=0, sticky='nw')
        ui.Label(f, image=f'join{img_mod}', image_pixels=300,
                image_scaleto='width', text='',
                row=1, column=0, rowspan=2, sticky='nw')
        response_button_frame = ui.Frame(f, column=1, row=2,
                                        pady=10, sticky='news')
        pair_frame = ui.Frame(f, column=1, row=1)
        return progress, response_button_frame, pair_frame

    def build_join_buttons(self, response_frame, img_mod,
                          join_fn, distinguish_fn):
        """Add Same/Different buttons to the join response frame."""
        ui.Button(response_frame, text=_("Same"), font='read',
                 image=f'join{img_mod}_same', compound="bottom",
                 image_pixels=200, image_scaleto='width',
                 cmd=join_fn, column=0, padx=10, ipadx=10, sticky='nsw')
        ui.Button(response_frame, text=_("Different"), font='read',
                 image=f'join{img_mod}_different', compound="bottom",
                 image_pixels=200, image_scaleto='width',
                 cmd=distinguish_fn, column=1, padx=10, ipadx=10, sticky='nes')

    def build_join_pair(self, pair_frame, buttonclass, sort_obj,
                       current_pair, buttons):
        """Build or show button frames for a pair of groups.
        Returns canary label."""
        r = 0
        for group in current_pair:
            if group in buttons:
                buttons[group].grid(row=r)
            else:
                # reverifiable: 'Same or different?' is unanswerable when one of
                # the two groups is itself wrong — right-click reverifies THAT
                # group (Kent 2026-07-28). Cached frames (the `if` above) keep
                # the menu they were built with.
                buttons[group] = buttonclass(pair_frame, sort_obj,
                                            group=group, showtonegroup=True,
                                            label=True, reverifiable=True,
                                            row=r, sticky='w')
            r = 1
        self.show_default_members([buttons[g] for g in current_pair])
        canary = ui.Label(pair_frame, text='', col=1)
        return canary

    def show_default_members(self, frames):
        """Coordinate which member each glyph frame shows when the page is
        presented (choose_shown_checks: same position across the pair when
        possible, else frontmost). Default only — the user can still cycle
        members and examples afterwards. No-op for sort-group frames (no
        member .items) and for cached frames already on the chosen check."""
        frames=[f for f in frames if getattr(f,'items',None)]
        if not frames:
            return
        member_checks=[[m.check for m in f.items] for f in frames]
        for f,checks,check in zip(frames,member_checks,
                                  choose_shown_checks(member_checks)):
            if check is not None and checks[f.shown_index]!=check:
                f.show_one(checks.index(check))

    def choose_join_direction(self, runwindow, buttonclass, sort_obj, pair,
                              counts, on_choose, on_back=None):
        """Chooser for the syllable-profile join DIRECTION: 'We are joining these
        profiles; which is correct?'. Each option is the group's SORT BUTTON (with
        its one example) + member count; clicking it picks that profile as the one
        KEPT — the other re-annotates to it. Back cancels (no join). There's no
        lexicographic/isdigit default here (both sides are real CV profiles), so
        this is the only way the direction is chosen. See ADR 0003 /
        cv_group_creation_merging."""
        w = ui.Window(runwindow, title=_("Which profile is correct?"), exit=False)
        f = w.frame
        ui.Label(f, text=_("We are joining these profiles; which is correct?"),
                font='instructions', row=0, column=0, columnspan=2, sticky='ew')
        def pick(g):
            w.destroy()
            on_choose(g)
        for c, group in enumerate(pair):
            cell = ui.Frame(f, row=1, column=c, padx=12, sticky='n')
            # NAME THE PROFILE (Kent 2026-07-28). The question is which of two
            # profiles is correct, and the cells carried only an example word and
            # a count — so the user was asked to choose between two unlabelled
            # buttons. The group IS the profile here (both sides are real CV
            # profiles on this page), so show it as the heading of its option.
            ui.Label(cell, text=group, font='readbig',
                    row=0, column=0, sticky='n')
            # NO label=True: it makes SortGroupButtonFrame build a Label, and
            # on_select is wired only by selectbutton — so both options rendered
            # as click-dead labels that still looked like buttons.
            buttonclass(cell, sort_obj, group=group, showtonegroup=True,
                        on_select=lambda g=group: pick(g),
                        row=1, sticky='n')
            ui.Label(cell, text=_("{n} words").format(n=counts.get(group, 0)),
                    font='normal', row=2, column=0, sticky='n')
        ui.Button(f, text=_("← Back (don’t join these)"),
                cmd=lambda: (w.destroy(), on_back() if on_back else None),
                font='instructions', row=2, column=0, columnspan=2, sticky='ew')
        return w
