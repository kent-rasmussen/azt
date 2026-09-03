# coding=UTF-8
"""Is there anything on screen? — the shared answers, and the global guards.

THREE GUARDS, ONE RULE SET. They must play nicely together (Kent 2026-09-01),
because the two symptoms are opposite ends of one dependency and a remedy for
either can produce the other — which is not hypothetical: the 2026-07-29 fix for
"no window at all" (`_get_safe_window` deiconifying a fresh run window) was
caught by the nothing-but-Quit guard on its first live run as a producer of
nothing-but-Quit.

  | guard | asks | acts? |
  |---|---|---|
  | `TaskDressing.guardvisible` (scoped, in ui_shell) | is anything viewable 15 s after THIS `getrunwindow`? | yes — it knows which run window belongs to the call in flight, so it can reveal the right one |
  | `VisibilityWatchdog` (global, below) | is anything viewable at all, ever? | NO, reports only — its signal cannot separate "the user has nothing" from "I failed to find what they are looking at" |
  | `QuitOnlyGuard` (global, below) | is a VIEWABLE window empty? | yes — that signal's innocent readings are excluded by `iswaiting()` and by strikes, and its action cannot cause the other symptom |

THE RULES THAT KEEP THEM FROM FIGHTING:
 1. **Nothing a guard adds is content.** `has_content()` ignores QuitOnlyGuard's
    placeholder, so a filled-in empty page never reads to the other two as a
    legitimate page to reveal.
 2. **A wait dialog suppresses everything.** It is the sanctioned way to have an
    empty or hidden window, and it is what a producer should use instead of
    being caught by a guard.
 3. **Never reveal an empty window; never withdraw the last one.** The first
    would produce nothing-but-Quit, the second no-window-at-all. Between them
    those two prohibitions are the whole contract.

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
from utilities.i18n import _
from utilities.error_handler import notify_user as NotifyUser
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


def first_viewable(*extra):
    """The first window the user can actually see, or None.

    Returns the WIDGET, not a bool, because two different questions are asked of
    this one walk and they need different answers: "is anything on screen?" (the
    watchdog's alarm — a splash counts, the user can see something happening)
    and "is the app usable?" (clearing the restart marker — a splash must NOT
    count, since the whole of boot happens after it). Only the caller knows
    which it is asking, so hand back the window and let it decide.

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
                return w
        except Exception:
            continue #a dead or half-built widget just isn't evidence
    return None


def anything_viewable(*extra):
    """True if the user can see SOME window right now. See first_viewable for
    which windows count and why."""
    return first_viewable(*extra) is not None


_reported_empty=set()


def report_empty_page(where,window=None,outcome=''):
    """An empty page was detected. Log it, and TELL THE USER WE NOTICED.

    Kent's framing (2026-09-03), which is the reason this exists rather than
    just more log lines: neither NBQ ("nothing but Quit") nor NWAA ("no window
    at all") is finished until they stop appearing, and the two are the same
    finding — an empty page — differing only in what the guard did about it. So
    the useful distinction is not which symptom appeared, but WHETHER WE SAW IT:

      * noticed  → "go to the log and report the line showing the problem"
      * unnoticed → "find the stack trace and start figuring it out from cold"

    A notice turns every remaining instance into the first kind. That is worth
    more than any particular remedy, because the remedy is caller-specific:
    whether an empty page should be rebuilt, skipped, or merely revealed later
    depends on what the caller was trying to do, and a guard cannot know that.
    Detection and notification are the guard's whole job.

    THE STATUS WINDOW, NOT THE FRAME. notify_user appends to the one session
    status window — a separate Toplevel that surfaces itself above a fullscreen
    kiosk page. Gridding a notice into the page's `frame` would make
    has_content() read the page as BUILT and hand the other two guards a
    legitimate-looking reveal target; see the capitalised warning in
    has_content. This is the same reason QuitOnlyGuard raises a wait rather than
    gridding a message.

    Once per `where` per session: these fire from polled guards and per-reveal
    hooks, and a notice that repeats teaches the user to ignore it.

    Never raises: a diagnostic that dies on the interesting case is worse than
    none (the isrunwindow lesson)."""
    try:
        if where in _reported_empty:
            return
        _reported_empty.add(where)
        try:
            title=window.title() if window is not None else '?'
        except Exception:
            title='?'
        log.warning("EMPTY PAGE (%s): %r had nothing in its frame%s. This line "
                "is the report — grep EMPTY PAGE.",
                where,title,(' — '+outcome) if outcome else '')
        NotifyUser(text=_("A page had nothing on it, so {name} did not show "
                    "it. Your work and your data are fine.\n\nIf you were "
                    "expecting something here, please send your log (Help "
                    "▸ Email my log to support) — what happened is recorded "
                    "in it.").format(name=_("A-Z+T")),
                    title=_("An empty page was skipped"))
    except Exception as e:
        try:
            log.info("report_empty_page failed: %s",e)
        except Exception:
            pass


def has_content(w):
    """Has this window been BUILT — i.e. is there anything in it to look at?

    `w.frame`, NOT `w`: `ui.Window` puts its own Exit button in `outsideframe`,
    not in `frame` (both backends), so testing the window itself would count a
    bare run window as built — which is precisely the empty-kiosk-with-a-
    quit-button that must never be revealed (Kent 2026-08-24, on "Sort!").
    Load-bearing; don't simplify to `w`.

    NOTHING A GUARD ADDS IS CONTENT — the rule that keeps the three from
    feeding each other false evidence (Kent 2026-09-01: they "need to play
    nicely together"). It costs nothing to state now that QuitOnlyGuard raises
    a WAIT rather than gridding a notice into the frame, but it was a live
    hazard while it did, and it is the reason that action was changed: anything
    a guard puts in `frame` reads here as "this page has content" and makes an
    empty page a legitimate reveal target for the other two.
    """
    try:
        if w is None or not w.winfo_exists():
            return False
        return bool(w.frame.winfo_children())
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


class QuitOnlyGuard:
    """Global guard against the NOTHING-BUT-QUIT page.

    Kent, 2026-09-01: *"set up a global guard like the invisible watchdog, since
    that page is bad no matter who did (or ever would) produce it."* Which is the
    right frame: a fullscreen block of theme colour whose only control is Exit
    solicits the most destructive action available, at the moment the user is
    most confused, and it is the only thing they can do. He watched a user on a
    Zoom call come close to pressing it for exactly that reason. Hunting
    producers one at a time cannot finish — the audit of `resetframe` callers
    found and fixed one, and the shape can be reached by any page that reveals
    before it builds — so this asks the question about the SCREEN instead.

    WHY THIS ONE MAY ACT, WHERE THE WATCHDOG MAY NOT. The watchdog's signal is
    ambiguous in a way that matters: "I found no viewable window" conflates "the
    user has nothing" with "I failed to find what they are looking at", and
    acting on the second wrecked a live page (1.14.3). This signal has two
    innocent readings — a page still BUILDING, and a page just TORN DOWN (Kent's
    correction; that is the `resetframe` gap) — and CRUCIALLY WE DO NOT NEED TO
    TELL THEM APART, because the remedy is the same either way and neither
    survives the filters:
      - `iswaiting()`: a wait dialog covering the window is the sanctioned way
        to have an empty frame, and both innocent cases are supposed to use one.
      - STRIKES: a teardown on its way to a withdraw, or a rebuild that lands
        promptly, is over in milliseconds. Three seconds of an empty page is not
        a gap; it is the ~10s page Kent measured.
    So what is left is a page that is wrong, whichever direction it was heading.

    WHAT IT DOES, per Kent's ordering (2026-09-01): *"a full screen of nothing
    but theme color — nothing would be better than that, and a wait window would
    be better than nothing, if it is over ~3s."* So, worst to best:

        blank themed page  <  no window at all  <  a wait window

    It therefore raises a WAIT on the offending window. That is the app's own
    sanctioned cover for a page that is not ready: it withdraws the window (so
    the blank page and its lone Exit stop being on screen — the "nothing"
    Kent prefers) and puts a dialog there saying something is happening (the
    "better than nothing"). Both guards accept a wait as evidence, so this does
    not fight them.

    THE WAIT IS CLOSED WHEN CONTENT ARRIVES, and that half is not optional: a
    wait nobody closes is the `tryNAgain` hole — the user parked on a dialog
    forever, with the watchdog suppressed because a wait window is viewable.
    So the guard keeps watching what it covered and calls waitdone() the moment
    the frame has real children, which also reveals the page.

    ITS ONE STRUCTURAL BLIND SPOT, and it is not fixable here: this runs on
    `after()`, and `after()` callbacks do not fire until `mainloop()` is
    entered. Everything in `App._run_setup` — including `TaskChooser`'s own
    construction — happens BEFORE that. So a page that sits blank during boot
    is invisible to this guard AND to the watchdog AND to `guardvisible`, no
    matter when they are started, because no timer runs at all yet. Kent hit
    exactly this (2026-09-02: NBQ seen, nothing in the log, the tail showing the
    chooser being built). The remedy for boot-time blankness is therefore a WAIT
    OPENED BY THE BUILDER, not a guard — the same conclusion `App.restart`'s
    `time.sleep` loop forced, and for the same reason.
    """
    POLL_MS=1000
    STRIKES=3
    ATTR='_nbq_covered'

    def __init__(self,program):
        self.program=program
        self.running=False
        self.strikes={} #id(window) -> consecutive observations

    def start(self):
        if self.running:
            return
        self.running=True
        log.info("quit-only guard: polling every %sms, acting after %s strikes",
                self.POLL_MS,self.STRIKES)
        self._schedule()

    def stop(self):
        self.running=False

    def _schedule(self):
        try:
            root=ui.default_root()
            if root is None:
                self.running=False
                return
            root.after(self.POLL_MS,self._tick)
        except Exception:
            log.exception("quit-only guard: could not schedule")
            self.running=False

    def _real_children(self,w):
        """What the page has actually built. The guard adds nothing to the
        frame any more — it raises a wait instead — so every child here is the
        page's own."""
        try:
            return list(w.frame.winfo_children())
        except Exception:
            return []

    def _is_quit_only(self,w):
        try:
            if getattr(w,'exitButton',None) is None:
                return False #no Exit button: not this symptom (e.g. exit=False)
            if not (w.winfo_exists() and w.winfo_viewable()):
                return False
            if w.iswaiting():
                return False #covered by a wait: an empty frame is expected
            if not w.frame.winfo_exists():
                return False
            return not self._real_children(w)
        except Exception:
            return False #a half-built widget is not evidence

    def _tick(self):
        try:
            if not self.running:
                return
            seen=set()
            for w in candidate_windows():
                key=id(w)
                seen.add(key)
                if getattr(w,self.ATTR,False):
                    # Ours, and covered. Uncover ONLY on real content — not on
                    # "no longer looks quit-only", which is true the instant we
                    # cover it (a wait is up, the window is withdrawn) and would
                    # undo the cover on the very next poll.
                    if self._real_children(w):
                        self._uncover(w)
                    continue
                if self._is_quit_only(w):
                    self.strikes[key]=self.strikes.get(key,0)+1
                    if self.strikes[key]==self.STRIKES:
                        self._cover(w)
                else:
                    self.strikes.pop(key,None)
            for gone in [k for k in self.strikes if k not in seen]:
                self.strikes.pop(gone,None)
        except Exception:
            log.exception("quit-only guard failed") #never break the app
        finally:
            if self.running:
                self._schedule()

    def _cover(self,w):
        """Replace the blank page with a wait dialog."""
        try:
            log.warning("NOTHING BUT QUIT: %r has been visible for %ss with an "
                    "empty frame and no wait covering it. Raising a wait over "
                    "it. Find the producer: this page revealed itself before "
                    "it had content.",
                    w.title(),self.POLL_MS*self.STRIKES/1000)
        except Exception:
            pass
        try:
            # thenshow=True so waitdone() below REVEALS the page rather than
            # leaving it withdrawn — otherwise curing the blank page would
            # produce the other symptom, no window at all.
            w.wait(msg=_("Please wait…"),thenshow=True)
            setattr(w,self.ATTR,True)
        except Exception:
            log.exception("quit-only guard: could not cover the empty page")

    def _uncover(self,w):
        """Content arrived: close our wait, which also reveals the page."""
        try:
            setattr(w,self.ATTR,False)
        except Exception:
            pass
        try:
            log.info("quit-only guard: %r has content now; revealing it",
                    w.title())
            w.waitdone()
        except Exception:
            log.exception("quit-only guard: could not uncover the page")


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

    def __init__(self,program,on_first_window=None):
        self.program=program
        self.misses=0
        self.armed=False    # see choice 3
        self.reported=False # see choice 4
        self.running=False
        # Called ONCE, the first time a window is actually viewable. This class
        # already has to compute that to arm itself, and it is the only place in
        # the app that computes it FROM THE EVENT LOOP — setup code can only
        # report that it finished constructing, which is not the same claim.
        # Used to clear the restart marker: "the restart worked" means a window
        # reached the screen, not that _run_setup returned.
        self.on_first_window=on_first_window

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
            seen=first_viewable(*self._reveal_candidates())
            if seen is not None:
                # The hook wants the first WORK SURFACE, so it stays pending
                # while only a boot_only window (the splash) is up — and keeps
                # being retried on later ticks, rather than being spent on the
                # splash and lost. Kent asked exactly this: "should it clear as
                # soon as we see the 'loading' splash screen?" No — the whole of
                # boot happens after the splash, so that is the failure window
                # the marker exists to describe.
                if (self.on_first_window is not None
                        and not getattr(seen,'boot_only',False)):
                    try:
                        self.on_first_window()
                    except Exception:
                        log.exception("visibility watchdog: on_first_window failed")
                    finally:
                        self.on_first_window=None #once, not every tick
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
