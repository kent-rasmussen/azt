# coding=UTF-8
"""A word's two play buttons, and play-all.

`▶` (WORD_TEXT) plays the word's own sound (its careful-speech take, if it
has one); `[▶]` (PHRASE_TEXT) plays it in the PHRASE it was cut from, with
at most a second of the phrase each side (CONTEXT_S).
Decisions, Kent 2026-11-05 (agenda/azt/text_word_alignment.md): a lexicon
built from text recordings has no glosses and no images, so a word is known
only by listening to it and to its phrase. The labels are symbols, not
words, so there is nothing to translate; the tooltips say what they do.
Each button appears only when there is something to play: `|>` when the
word has a playable sound file, `[|>]` when the sense has a phrase with one.
General on purpose — the same pair is for lexical sorting later, not only
for text words.

Either sound may be a SPAN of a longer recording ('story.ogg#t=12.340,
12.810', io_put/lift.py FormParent.hassoundfile → audiofileURL + audiospan);
the span rides on the player (SoundFilePlayer(span=…)), so the buttons play
just the word or just the phrase.

Backend-neutral: only `from frontend import ui`, and `after()`, which both
backends have (webview's runs the callback on a timer THREAD — see PlayAll).
"""
import os
import threading

from utilities.i18n import _
from utilities import logsetup, executables
log=logsetup.getlog(__name__)
from frontend import ui
try:
    from io_put import sound
except Exception as e:
    # optional, as everywhere: no sound stack means no play buttons, not a
    # failed import (see sort_buttons.py's same guard).
    sound=None
    log.info(f"sound stack unavailable ({e}); no play buttons")

# Play triangles, not the ASCII '|>' they were written as in the notes
# (Kent, 2026-11-06).
WORD_TEXT='▶'
PHRASE_TEXT='[▶]'
# Shown beside the row play-all is playing. A SHAPE, not a colour: the
# highlight must read without colour (the row's border also thickens). Not
# '▶', which is now the play buttons' own face.
PLAYING_MARK='♪'
# `[▶]` plays the word with at most this much of its phrase on each side
# (Kent, 2026-11-06: whole phrases ran to 15 s and more).
CONTEXT_S=1.0
# `▶` plays a word's span with this much more on each side: cut strictly
# at the word boundaries it sounds clipped (Kent, 2026-11-06).
WORD_PAD_S=0.1


def playback(program, task=None):
    """The ``(interface, settings)`` pair ``SoundFilePlayer`` takes, or
    ``(None, None)`` when this machine can't play. Never raises.

    THE ONE ACCESSOR for a page that PLAYS but never records (sort, verify):
    ``SoundSettings.ensure`` (backend/core/sound.py) makes and stores both
    halves; reading ``program.audio`` or ``.soundsettings`` raw is the bug
    this replaced three times in one evening (Kent 2026-07-29/31). Moved
    here from ``_GroupButtonFrame._playback`` (sort_buttons.py), which now
    calls this, so the sort buttons and these buttons cannot drift apart.
    Unlike a Sound task, an unusable output config degrades to no button —
    a sort or verify board must never open the mic-check window mid-sort."""
    # attribute, not a key: main.py sets program['nosound'] before App
    # absorbs it, and consumers read program.nosound.
    if sound is None or getattr(program,'nosound',False):
        return None,None
    # PERMISSIVE ON PURPOSE (Kent 2026-07-31): give up only when there is
    # genuinely nothing to play with. A play that fails at CLICK time is
    # recoverable and says so; a missing button is a dead page.
    ss=None
    try:
        from backend.core.sound import SoundSettings
        try:
            # The analang, so a FIRST ensure landing here still seeds ASR for
            # the right language (ensure applies it only when it constructs).
            analang_obj=program.languages.get_obj(task.analang)
        except Exception:
            analang_obj=None
        ss=SoundSettings.ensure(program, analang_obj=analang_obj)
    except Exception as e:
        # e.g. speakers but no mic: default_in raises although playback
        # needs no input card. Use whatever a Sound task already built.
        log.info("SoundSettings.ensure failed for %s (%s); falling back to "
                "an existing settings object.",type(task).__name__,e)
        ss=(getattr(task,'soundsettings',None)
            or getattr(program,'soundsettings',None)
            or getattr(getattr(program,'settings',None),
                       'soundsettings',None))
    if ss is None:
        return None,None
    # ONE OWNER FOR THE HANDLE (2026-09-11): confirm_audio() owns
    # program.audio; ensure already ran it, so this matters only on the
    # fallback path above.
    audio=getattr(ss,'audio',None)
    if audio is None:
        try:
            ss.confirm_audio()
            audio=ss.audio
        except Exception as e:
            log.info("no audio handle for %s (%s); no play button.",
                    type(task).__name__,e)
            return None,None
    return audio,ss


def sound_of(node):
    """``(url, span)`` for a form node with a playable sound file, else
    None. `span` is (start_s, end_s) of a longer recording, or None for the
    whole file."""
    if node is None:
        return None
    try:
        if node.hassoundfile():
            return node.audiofileURL,getattr(node,'audiospan',None)
    except Exception as e:
        log.info("couldn't check %s for a sound file (%s)",node,e)
    return None


def in_context(word, phrase, context=CONTEXT_S):
    """`phrase` ``(url, span)`` cut down to `word`'s span plus `context`
    seconds each side, never past the phrase's own ends — when both are
    spans of the same recording. Otherwise `phrase` as it is."""
    if not word or not phrase or word[1] is None or phrase[1] is None:
        return phrase
    try:
        same=os.path.abspath(str(word[0]))==os.path.abspath(str(phrase[0]))
    except Exception:
        same=False
    if not same:
        return phrase
    (ws,we),(ps,pe)=word[1],phrase[1]
    if ws is None or we is None:
        return phrase
    start=max(ps or 0.0, ws-context, 0.0)
    end=we+context if pe is None else min(pe, we+context)
    return phrase[0],(start,end)


def padded(word, phrase=None, pad=WORD_PAD_S):
    """`word` ``(url, span)`` with `pad` seconds more each side, never
    before 0 nor past `phrase`'s span when that is a span of the same
    recording. A whole file (no span) is `word` as it is."""
    if not word or word[1] is None:
        return word
    ws,we=word[1]
    if ws is None or we is None:
        return word
    ps=pe=None
    if phrase and phrase[1] is not None:
        try:
            if (os.path.abspath(str(word[0]))
                    ==os.path.abspath(str(phrase[0]))):
                ps,pe=phrase[1]
        except Exception:
            pass
    start=max(ps or 0.0, ws-pad, 0.0)
    end=we+pad if pe is None else min(pe, we+pad)
    return word[0],(start,end)


def word_node(sense, ftype='lc'):
    """The sense's form node of type `ftype` (usually 'lc'), or None."""
    try:
        return sense.ftypes[ftype]
    except (AttributeError,KeyError,TypeError):
        return None


class PlayButtons(object):
    """What play_buttons() built. `frame` is None when nothing was built;
    `play_word()` returns the duration in seconds of what it started, or
    None (nothing to play) — what play-all chains on."""
    def __init__(self):
        self.frame=None
        self.word_player=self.phrase_player=None
        self.word_button=self.phrase_button=None
    @property
    def can_play_word(self):
        return self.word_player is not None
    def play_word(self):
        if self.word_player is None:
            return None
        return self.word_player.play()
    def play_phrase(self):
        if self.phrase_player is None:
            return None
        return self.phrase_player.play()


def _button(frame, text, player, src, tip, program, column):
    url,span=src
    b=ui.Button(frame, text=text, cmd=lambda:player.play(),
                column=column, row=0, sticky='nsew')
    tiptext=tip
    if (getattr(program,'praat',None)
            and not str(url).lower().endswith('.m4a')):
        # praat can't read m4a. A span opens the WHOLE recording — Praat is
        # not asked to select it — so the times go to the log.
        tiptext+='; '+_("right click to open in praat")
        def praat(event=None):
            if span is not None:
                log.info("opening the whole of {} in praat; this sound is "
                         "{} to {} s of it".format(url,*span))
            executables.praatopen(program,url)
            # the window's own <<ContextMenu>> (ui.ContextMenu) is the same
            # right-click: 'break' keeps its menu from posting over this
            return 'break'
        try:
            b.bind('<Button-3>',praat)
        except Exception as e:
            log.info("praat right-click not bound (%s)",e)
    try:
        ui.ToolTip(b,tiptext)
    except Exception as e:
        log.info("play-button tooltip skipped (%s)",e)
    return b


def play_buttons(parent, sense, program, ftype='lc', row=0, column=0,
                 task=None, pair=None, node=None, **gridkwargs):
    """Build the `|>` / `[|>]` pair for `sense` in a frame gridded at
    (row, column) of `parent`. Returns a PlayButtons, whose `frame` is None
    when there was nothing to play or no way to play it (no sound stack, no
    device) — the page then simply has no buttons there.

    `pair` is a ready ``playback()`` result, so a page building many rows
    asks for the audio handle once rather than per row. `node` overrides
    which form is "the word" (a tone page's frame example); by default it is
    `sense.ftypes[ftype]`."""
    pb=PlayButtons()
    if sound is None or sense is None:
        return pb
    # A text word said again on its own (careful speech, lift.py
    # Sense.careful) plays in place of its span of the text (Kent,
    # 2026-11-06); the span stays the word's own audio in the LIFT.
    own=sound_of(node if node is not None else word_node(sense,ftype))
    whole=sound_of(getattr(sense,'phrase',None))
    word=(node is None and sound_of(getattr(sense,'careful',None))
          or padded(own,whole))
    # the phrase only around the word's span in it (never the careful take's)
    phrase=in_context(own,whole)
    if not word and not phrase:
        return pb
    audio,ss=pair if pair is not None else playback(program,task)
    if audio is None or ss is None:
        return pb
    gridkwargs.setdefault('sticky','w')
    pb.frame=ui.Frame(parent, row=row, column=column, **gridkwargs)
    col=0
    if word:
        pb.word_player=sound.SoundFilePlayer(word[0],audio,ss,span=word[1])
        pb.word_button=_button(pb.frame, WORD_TEXT, pb.word_player, word,
                               _("Click to hear this word"), program, col)
        col+=1
    if phrase:
        pb.phrase_player=sound.SoundFilePlayer(phrase[0],audio,ss,
                                               span=phrase[1])
        pb.phrase_button=_button(pb.frame, PHRASE_TEXT, pb.phrase_player,
                                 phrase,
                                 _("Click to hear this word in its phrase "
                                   "(up to a second each side)"), program,
                                 col)
    return pb


class PlayAll(object):
    """Play each registered row's word in turn: highlight the row, scroll it
    into view, play, then `after(duration + GAP_MS)` the next.

    CHAINED ON THE DURATION, because sounddevice.play() returns at once:
    SoundFilePlayer.play() returns how long what it started lasts, and that
    is the only clock there is.

    STOPS — and says so by its button reading "Play all" again — on Stop,
    at the end of the list, when the page goes (its `alive` test fails, e.g.
    the verify canary destroyed by OK), when the presenter builds another
    page (it calls stop()), and when the row list changes (a row removed by
    the user or another added), since "the next row" no longer means what
    it meant when play began.

    THREADS: under webview `after()` runs on a timer thread, so a step and a
    Stop click can interleave. A generation counter retires every pending
    step on stop(), and one lock keeps a step from re-highlighting a row a
    concurrent stop() just cleared."""
    GAP_MS=400

    def __init__(self, header, scroller=None, alive=None, row=0, column=0,
                 **gridkwargs):
        self.header=header          # where the button goes, made on first add
        # has .see(widget) — or a no-argument function returning it, for a
        # page that makes its scroller after its header; None → no scrolling
        self.scroller=scroller
        self.alive=alive            # () -> bool: is the page still up?
        self._grid=dict(row=row,column=column,**gridkwargs)
        self.rows=[]                # {'key','frame','marker','play'}
        self.button=None
        self._gen=0
        self._playing=False
        self._timer=None
        self._current=None
        self._queue=[]
        self._nrows=0
        self._lock=threading.RLock()

    def add(self, key, frame, play, marker=None):
        """Register a row. `key` orders play (the verify page passes
        (row, column), i.e. reading order); `frame` is the row's widget —
        its existence is how a removed row is noticed, and it is what gets
        scrolled to and outlined; `play` returns a duration or None;
        `marker` is a Label whose text shows PLAYING_MARK while playing.
        `key` may be a function, read at start, for rows that move (the sort
        page's group buttons re-grid). A frame added again replaces its old
        row (a group button rebuilds its insides when its example changes),
        and rows whose frames are gone are dropped here."""
        if play is None:
            return
        with self._lock:
            self.rows=[r for r in self.rows
                       if r['frame'] is not frame and self._exists(r['frame'])]
            self.rows.append({'key':key,'frame':frame,'marker':marker,
                              'play':play})
        if self.button is None:
            self._make_button()

    def _make_button(self):
        try:
            self.button=ui.Button(self.header, text=_("Play all"),
                                  cmd=self.toggle, **self._grid)
            ui.ToolTip(self.button,_("Play each word in turn, from the "
                                     "top; click again to stop"))
        except Exception as e:
            log.info("no play-all button (%s)",e)
            self.button=None

    @staticmethod
    def _exists(w):
        try:
            return bool(w.winfo_exists())
        except Exception:
            return False

    def _live(self):
        return [r for r in self.rows if self._exists(r['frame'])]

    def _page_alive(self):
        if self.alive is None:
            return True
        try:
            return bool(self.alive())
        except Exception:
            return False

    def toggle(self, event=None):
        if self._playing:
            self.stop()
        else:
            self.start()

    def start(self):
        with self._lock:
            rows=sorted(self._live(),key=lambda r:(r['key']()
                                    if callable(r['key']) else r['key']))
            if not rows:
                log.info("play-all: no playable rows")
                return
            self._gen+=1
            gen=self._gen
            self._playing=True
            self._queue=rows
            self._nrows=len(self.rows)
            self._set_label(_("Stop"))
        log.info("play-all: %d rows",len(rows))
        self._step(gen,0)

    def _changed(self):
        """Has a row been added or removed since play began?"""
        return (len(self.rows)!=self._nrows
                or any(not self._exists(r['frame']) for r in self._queue))

    def _step(self, gen, i):
        with self._lock:
            if gen!=self._gen:
                return                      # retired by stop()/restart
            if not self._page_alive():
                log.info("play-all: page gone; stopping")
                self.stop()
                return
            if self._changed():
                log.info("play-all: the row list changed; stopping")
                self.stop()
                return
            if i>=len(self._queue):
                self.stop()
                return
            row=self._queue[i]
            self._unhighlight()
            self._highlight(row)
            try:
                sc=self.scroller
                if sc is not None and not hasattr(sc,'see') and callable(sc):
                    sc=sc()     # given lazily: the page made it after this
                if sc is not None:
                    # Scroll FIRST: on a virtualized page the row may be
                    # unmapped, and the virtualizer maps whatever is in view.
                    sc.see(row['frame'])
            except Exception as e:
                log.info("play-all: couldn't scroll to row (%s)",e)
            try:
                duration=row['play']()
            except Exception as e:
                log.info("play-all: row %s didn't play (%s)",row['key'],e)
                duration=None
            ms=int((duration or 0)*1000)+self.GAP_MS
            try:
                self._timer=(self.button or self.header).after(
                                    ms,lambda:self._step(gen,i+1))
            except Exception as e:
                log.info("play-all: couldn't schedule the next row (%s)",e)
                self.stop()

    def stop(self, event=None):
        """Stop playing (if it is), clear the highlight, restore the label.
        Safe to call any time, from any thread, any number of times."""
        with self._lock:
            was=self._playing
            self._gen+=1
            self._playing=False
            t,self._timer=self._timer,None
            if t is not None:
                try:
                    (self.button or self.header).after_cancel(t)
                except Exception:
                    pass
            self._unhighlight()
            if was:
                if sound is not None:
                    sound.stop_playback()
                self._set_label(_("Play all"))

    def _set_label(self, text):
        if self.button is not None and self._exists(self.button):
            try:
                self.button['text']=text
            except Exception as e:
                log.info("play-all label not set (%s)",e)

    def _highlight(self, row):
        """Mark the row by SHAPE as well as anything else: the marker
        character, and a thicker outline on the row's frame."""
        self._current=row
        m=row.get('marker')
        if m is not None and self._exists(m):
            try:
                m['text']=PLAYING_MARK
            except Exception:
                pass
        f=row['frame']
        row['_ht']=None
        if self._exists(f):
            try:
                ht=f['highlightthickness']
                f.configure(highlightthickness=3)
                # only once it is known how to put it back
                row['_ht']=ht if ht not in (None,'') else 0
            except Exception:
                pass

    def _unhighlight(self):
        row,self._current=self._current,None
        if row is None:
            return
        m=row.get('marker')
        if m is not None and self._exists(m):
            try:
                m['text']=' '
            except Exception:
                pass
        f=row['frame']
        if self._exists(f) and row.get('_ht') is not None:
            try:
                f.configure(highlightthickness=row['_ht'])
            except Exception:
                pass
