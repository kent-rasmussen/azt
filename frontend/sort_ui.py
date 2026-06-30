# coding=UTF-8
"""UI presenter for Sort workflow operations.

Backend sorting_engine.py delegates all UI widget creation here, so it
has zero frontend imports.
"""
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

    def set_sense_illustration(self, sense):
        _t0=time.perf_counter() # DIAG (1.3.13): see build_verify_layout log
        try:
            if not sense.image or not sense.image.base_img:
                # don't reload images unnecessarily;
                # base_img is None if image failed to load
                iuri=sense.illustrationURI()
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

    def offer_profile_setup(self, parent, note):
        """No syllable-profile data yet for this ps: offer to affirm the machine
        analysis as profiles, or go sort syllable profiles first. Returns
        'affirm' / 'sort' / 'cancel'."""
        result={'choice':'cancel'}
        # Build withdrawn, then deiconify — so it appears composed and placed,
        # rather than mapping empty and reflowing (the "took a bit / wrong spot").
        w=ui.Window(parent, title=_("Set up syllable profiles?"), exit=False,
                    withdrawn=True)
        n=ui.Label(w.frame, text=note, font='instructions',
                  row=0, column=0, columnspan=3, sticky='ew', padx=10, pady=6)
        n.wrap()
        def choose(c):
            result['choice']=c
            w.destroy()
        ui.Button(w.frame, text=_("Trust machine analysis; \nmaybe correct later"),
                 cmd=lambda:choose('affirm'), font='instructions',
                 row=1, column=0, sticky='ew', padx=4)
        ui.Button(w.frame, text=_("Sort syllable profiles manually; \ncome back here later"),
                 cmd=lambda:choose('sort'), font='instructions',
                 row=1, column=1, sticky='ew', padx=4)
        ui.Button(w.frame, text=_("Cancel"), cmd=lambda:choose('cancel'),
                 font='small', row=1, column=2, sticky='ew', padx=4)
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
        if sense.image:
            sense.image.scale(l.theme.scale, pixels=65, scaleto='height')
            l['image'] = sense.image.scaled
            l['compound'] = 'left'
        l.wrap()
        buttonframe.sortitem = sortitem
        return sortitem

    def build_present_group(self, runwindow_frame, buttonframe, sort_obj,
                           item, kwargs):
        """Build the sort item display for a group. Returns frame or None."""
        sortitem = ui.Frame(runwindow_frame, border=True,
                           column=1, row=1, sticky='nw')
        ui.Label(sortitem, text='', width=5, sticky='')
        tosort_frame = SortGroupButtonFrame(sortitem, sort_obj,
                                           show_check=True, label=True,
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
                                     row=1, sticky='nsew', columnspan=2)
        return groupsFrame, buttonframe

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
        ui.Label(titles, text=' '.join(title), font='title',
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
            buttonframe = SortButtonFrame(f, sort_obj,
                                         list(items), macrosort=True,
                                         show_check=True,
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
                ui.Button(navframe, text=oktext, font='instructions',
                         cmd=verifycanary.destroy,
                         column=0, row=0, sticky='ew', padx=4)
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
                _grid_ok() # OK button + single resume_configure reflow + timing log
                # VIRTUALIZE (1.3.32): unmap rows outside the viewport so waitdone's
                # render paints only the ~visible dozen, not all N. EXPERIMENTAL —
                # comment out this block (or revert the version) to disable.
                try:
                    self._virtualize_verify(buttonframe, nav_row+1, bc)
                except Exception as e:
                    log.info("verify virtualize skipped: %s", e)
                if runwindow.iswaiting():
                    _wd=time.perf_counter() # DIAG (1.3.30): waitdone()'s full update()
                    runwindow.waitdone()    # renders the build backlog while the window
                    log.info("verify reveal (waitdone) %.1fs", # is hidden — the real gap
                             time.perf_counter()-_wd)
                # ONE commit so the complete window paints (no per-item flush did it).
                # update() DRAINS the event queue while flushing, which avoids the
                # XWayland write-deadlock a bare update_idletasks hits on a large
                # backlog — the single remaining synchronous round-trip of the build.
                _c=time.perf_counter() # DIAG (1.3.29): measure the PAINT — the gap
                try:                    # between "verify build" and the window appearing
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
        for ws in (rowmap.get(0),rowmap.get(1)):
            for w in (ws or []):
                try: rowH=max(rowH,w.winfo_reqheight())
                except Exception: pass
        if rowH<10: rowH=80
        for r in range(nrows):
            content.rowconfigure(r, minsize=rowH)
        state={'win':None}
        def window():
            if not canvas.winfo_exists(): return
            ch=canvas.winfo_height()
            if ch<=1: ch=canvas.winfo_screenheight() # not mapped yet → estimate
            try: top=canvas.yview()[0]
            except Exception: top=0.0
            first=int(top*nrows); visible=int(ch/rowH)+1; buf=6
            lo,hi=max(0,first-buf),min(nrows,first+visible+buf)
            if state['win']==(lo,hi): return
            state['win']=(lo,hi)
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

    def build_verify_button(self, parent, text, sense, is_label,
                           notok_fn, row, column, ipady, **kwargs):
        """Build a single verify button or label. Returns (widget, frame_or_None)."""
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
        b['image'] = self.set_sense_illustration(sense)
        b['compound'] = 'left'
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
                buttons[group] = buttonclass(pair_frame, sort_obj,
                                            group=group, showtonegroup=True,
                                            label=True, row=r, sticky='w')
            r = 1
        canary = ui.Label(pair_frame, text='', col=1)
        return canary
