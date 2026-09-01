# coding=UTF-8
"""Is there anything on screen? — the shared answer, and the global watchdog.

Two consumers, one rule. `TaskDressing.guardvisible` is the SCOPED guard: it
fires once, 15 s after `getrunwindow`, because that call is a known producer of
"both windows withdrawn". `VisibilityWatchdog` is the GLOBAL one: it polls for
the life of the app and does not care who withdrew what.

The global one exists because enumerating producers cannot finish the job.
`getrunwindow` has 16 call sites and a name, but the real class is *any*
`withdraw()` whose matching `deiconify()` is not in a `finally` — and the ones
that bite are the abandon/exception paths nobody exercises. Three found outside
`getrunwindow` on 2026-08-31 alone (`Tone.addframe`, `parse_foreground`,
`App.restart`); the next one will be written next month. A watchdog that asks
only "does the user have a window right now?" is indifferent to all of that.

WHAT IT DELIBERATELY IS NOT: a cure for a wedged UI. It runs on `after()`, so
it is dead whenever the main thread is blocked — `App.restart`'s
`while self.writing: time.sleep(1)` being the known case. It reports WITHDRAWN
windows, never WEDGED ones. That distinction is why `wayland_freeze_audit.md`
exists as a separate item, and pretending otherwise would make the log lie.

Everything here uses only `ui_interface` methods (`winfo_exists`,
`winfo_viewable`, `winfo_children`, `after`, `deiconify`, `default_root`), so it
holds for the webview backend too, and every step is wrapped: a watchdog that
can break the app is worse than no watchdog.
"""
from utilities import logsetup
log=logsetup.getlog(__name__)
from frontend import ui


MAX_WINDOW_DEPTH=8


def _collect_toplevels(parent,out,depth=0):
    """Add every toplevel under `parent`, recursing THROUGH toplevels only.

    A run window is `ui.Window(task_window)` — a child of the TASK window, so a
    grandchild of the root: one level of `root.winfo_children()` cannot see it,
    and a guard built on that would report NO WINDOW with a run window up. (The
    scoped guard escapes this only because it passes its own run window in by
    hand.)

    Descending only into toplevels keeps this cheap: a page's few thousand
    labels hang under FRAMES, which are never entered, so the walk is bounded
    by the number of windows and their direct children — not by page content.
    """
    if depth>MAX_WINDOW_DEPTH:
        return
    try:
        children=list(parent.winfo_children())
    except Exception:
        return
    for child in children:
        try:
            if child.winfo_toplevel() != child:
                continue #a frame or widget: not a window, and not a way to one
        except Exception:
            continue
        if any(child is w for w in out):
            continue #cycles and diamonds: a window reached twice is still one
        out.append(child)
        _collect_toplevels(child,out,depth+1)


def candidate_windows(*extra):
    """Every window that could be showing the user something: the app root, the
    whole tree of toplevels beneath it, plus whatever the caller knows about.
    Dead and half-built widgets are simply not evidence."""
    widgets=[w for w in extra if w is not None]
    try:
        root=ui.default_root()
    except Exception:
        root=None
    if root is not None:
        widgets.append(root)
        _collect_toplevels(root,widgets)
    return widgets


def anything_viewable(*extra):
    """True if the user can see SOME window right now.

    Skips AMBIENT windows (`guard_ambient`): viewable, but not a surface the
    user can work in. The status/message window is parented to the root and
    stays open all session by design, so counting it silently disabled the
    scoped guard from the first notify onward — which is why no NO WINDOW line
    was ever logged, through the whole 2026-08 hunt, even while the user sat
    looking at nothing (Kent 2026-08-27). Wait dialogs and real modals still
    count: those mean "something is happening, and the user is being told",
    which is exactly the evidence a visibility guard should accept.
    """
    for w in candidate_windows(*extra):
        try:
            if getattr(w,'guard_ambient',False):
                continue
            if w.winfo_exists() and w.winfo_viewable():
                return True
        except Exception:
            continue #a dead or half-built widget just isn't evidence
    return False


def has_content(w):
    """Has this window been BUILT — i.e. is there anything in it to look at?

    `w.frame`, NOT `w`: `ui.Window` puts its own Exit button in `outsideframe`,
    not in `frame` (both backends), so testing the window itself would count a
    bare run window as built — which is precisely the empty-kiosk-with-a-
    quit-button that must never be revealed (Kent 2026-08-24, on "Sort!").
    Load-bearing; don't simplify to `w`.
    """
    try:
        return bool(w is not None and w.winfo_exists()
                    and w.frame.winfo_children())
    except Exception:
        return False


def window_state(w):
    """One-line state of a window, for the log. Never raises: every probe below
    throws TclError on a destroyed widget, and a diagnostic that dies on the
    interesting case is worse than none (the isrunwindow lesson, 2026-08-27)."""
    try:
        if w is None:
            return "None"
        if not w.winfo_exists():
            return f"{w!r} destroyed"
        bits=[repr(w)]
        for probe in ('winfo_ismapped','winfo_viewable','state','iswaiting'):
            try:
                bits.append(f"{probe[6:] if probe.startswith('winfo_') else probe}"
                            f"={getattr(w,probe)()}")
            except Exception:
                pass
        bits.append(f"content={has_content(w)}")
        return " ".join(bits)
    except Exception as e:
        return f"probe failed: {e}"


class VisibilityWatchdog:
    """Poll for "the app is alive and the user has no window", forever.

    Five deliberate choices, each one paid for by a previous attempt:

    1. POLL, don't one-shot. The scoped guard fires 15 s after a specific call
       and is then gone; a second occurrence later in the session goes
       unreported. This keeps checking for the whole session.
    2. STRIKES, not a single miss. Pages legitimately withdraw one window
       before revealing the next, so a single unlucky sample is not evidence.
       Five consecutive misses at 5 s ≈ 25 s — deliberately LATER than the
       scoped guard's 15 s, so the better-informed reveal (it knows which run
       window belongs to the call in flight) always gets first refusal.
    3. ARM ON FIRST SIGHTING. Startup has no window on purpose — the root is
       withdrawn (`main.py`) and the splash comes later — so firing during boot
       on a slow machine would be a false alarm every single time. Nothing is
       reported until something has been seen viewable at least once.
    4. ONE REPORT PER EPISODE. A genuinely stuck app would otherwise write a
       line every 5 s and bury the first, most useful one. After firing, the
       watchdog goes quiet until it sees a window again.
    5. FALL BACK TO THE CHOOSER. Never reveal an empty window — but unlike the
       scoped guard, this one does not get to decline. It has already waited
       25 s, so "no build is in flight" is settled, and the user is owed a
       target. The task chooser is the app's home screen and always has
       content, so it is the last resort before giving up.
    """
    POLL_MS=5000
    STRIKES=5   # POLL_MS * STRIKES must stay > TaskDressing.RUNWINDOW_GUARD_MS
    REVEAL=False
    """DO NOT flip this to True without reading the whole story.

    1.14.3 shipped this watchdog revealing. It immediately interrupted Kent
    mid-page: the tone frame drafter was on screen, the watchdog decided nothing
    was viewable, and deiconified the TASK WINDOW — the drafter's own parent —
    on top of the page he was working in. Its log dump named exactly two
    candidates, both task windows, and never mentioned the drafter, so the
    window the user was actually in was not even a thing this class could see.

    That is the FOURTH time a timer in this item has been wrong about when to
    reveal (2 s revealed empty pages mid-build; 15 s traded that for long blank
    waits; reveal-on-content counted children that were present but unlaid-out;
    now this). The pattern is not a tuning problem. A global watchdog knows one
    thing — "I could not find a viewable window" — and CANNOT distinguish "the
    user has nothing" from "I failed to find what the user is looking at". The
    first calls for a reveal; the second is an interruption, and getting it
    wrong is worse than the bug, because a page that steals focus mid-task
    destroys work while a missing window merely stalls it.

    So: the LOG half was always the safe half, and it is the half that carries
    the value here — the 2026-07-29 field incident was unsolvable precisely
    because it produced no line. The scoped `guardvisible` keeps revealing,
    because it knows WHICH run window belongs to the call in flight; this one
    reports and shuts up. Turn it back on only with evidence that the walk below
    sees every window a user can be in.
    """

    def __init__(self,program):
        self.program=program
        self.misses=0
        self.armed=False    # see choice 3
        self.reported=False # see choice 4
        self.running=False

    def start(self):
        """Begin polling. Idempotent — a second call is a no-op, so wiring it
        from more than one place cannot double the poll rate."""
        if self.running:
            return
        self.running=True
        log.info("visibility watchdog: polling every %sms, reporting after %s "
                "consecutive misses",self.POLL_MS,self.STRIKES)
        self._schedule()

    def stop(self):
        self.running=False

    def _host(self):
        """Schedule on the ROOT. tkinter's after() wrapper deletes its own
        command AFTER running the callback, which on a widget destroyed
        meanwhile is an AttributeError it does not catch — surfacing as a crash
        inside tkinter (Kent 2026-08-25). The root outlives every page."""
        try:
            return ui.default_root()
        except Exception:
            return None

    def _schedule(self):
        try:
            host=self._host()
            if host is None:
                self.running=False
                return
            host.after(self.POLL_MS,self._tick)
        except Exception:
            log.exception("visibility watchdog: could not schedule")
            self.running=False

    def _shutting_down(self):
        """Don't report on the way out: every window going away is correct
        then, and a NO WINDOW line during shutdown is noise that would teach
        the reader to ignore the ones that matter."""
        for holder in (self._host(),getattr(self.program,'task',None)):
            try:
                if holder is not None and holder.exitFlag.istrue():
                    return True
            except Exception:
                continue
        return bool(getattr(self.program,'exiting',False))

    def _tick(self):
        try:
            if not self.running:
                return
            if self._shutting_down():
                self.stop()
                return
            # Ask about the SAME windows it would reveal, on top of the tree
            # walk: the list it can offer the user and the list it counts as
            # evidence must be the same list, or it can report NO WINDOW about
            # a window it is holding a reference to.
            if anything_viewable(*self._reveal_candidates()):
                self.armed=True     # something has been seen: arm (choice 3)
                self.misses=0
                self.reported=False # a new episode may now be reported
            elif self.armed:
                self.misses+=1
                if self.misses>=self.STRIKES and not self.reported:
                    self.reported=True
                    self._report_and_reveal()
        except Exception:
            log.exception("visibility watchdog failed") #never break the app
        finally:
            if self.running:
                self._schedule()

    def _reveal_candidates(self):
        """In preference order: the run window of the task in flight, that
        task's own window, then the chooser. Resolved through `.ui` where
        present — a Task is a logic object that DELEGATES to its window, and the
        window is what we can ask about frames and deiconify."""
        out=[]
        for owner in (getattr(self.program,'task',None),
                        getattr(self.program,'taskchooser',None)):
            if owner is None:
                continue
            w=getattr(owner,'ui',owner)
            for cand in (getattr(w,'runwindow',None),w):
                if cand is not None and cand not in out:
                    out.append(cand)
        return out

    def _report_and_reveal(self):
        secs=self.POLL_MS*self.misses/1000
        cands=self._reveal_candidates()
        # The evidence FIRST, and unconditionally: a user with no window cannot
        # file a useful report, so the log has to. This is the line the whole
        # 2026-07-29 field incident lacked. Worded as what is actually known —
        # "found no viewable window", not "there is no window": the 1.14.3
        # occurrence said the latter while Kent was looking at a page, and the
        # overclaim is what justified the interruption.
        log.warning("NO WINDOW (global): found no viewable window in %s polls "
                "(%ss). NB this means NOT FOUND, which is not the same as not "
                "there.",self.misses,secs)
        # EVERY window the walk reached, not just the reveal candidates. The
        # 1.14.3 dump listed two task windows and nothing else, so it could not
        # say whether the page the user was in was missed by the walk or found
        # and judged unviewable — which are different bugs with different fixes.
        # Kent's reading (2026-08-31) is that the name/gloss prompt window in
        # ToneFrameDrafter never appears here at all; this settles it.
        try:
            for w in candidate_windows(*cands):
                log.warning("NO WINDOW (global): saw %s",window_state(w))
        except Exception:
            log.exception("NO WINDOW (global): could not enumerate windows")
        if not self.REVEAL:
            return #log-only; see REVEAL's docstring for why
        target=next((c for c in cands if has_content(c)),None)
        if target is None:
            log.warning("NO WINDOW (global): nothing built to reveal — every "
                    "candidate is empty or gone. The user has no target and "
                    "the app cannot give them one; this needs the log above.")
            return
        try:
            target.deiconify()
            log.warning("NO WINDOW (global): revealed %s",target)
        except Exception:
            log.exception("NO WINDOW (global): reveal of %s failed",target)
