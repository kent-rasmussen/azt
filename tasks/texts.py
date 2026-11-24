# coding=UTF-8
"""Transcribe Texts: long recordings in <project>/texts (not audio/, Kent 2026-11-06), clause chunk by clause chunk.

The task's board (on the main screen) has a row per recording there: how many of its clauses the
models have transcribed, how many have their words found, how many the person has transcribed, and buttons for
the steps that work on a whole text — "Parse" (MMS, for each language in Transcription settings, over any
clause it hasn't done, then word breaks by consensus over the candidates, timed by forced alignment:
azt_asr/wordbreaks.py) and "ASR only" (every model in settings, where it hasn't run). "Process all" parses every
recording, one after another (Kent, 2026-11-07). These come first, before any clause-by-clause work
(Kent, 2026-11-06). A recording is cut at pauses and added to the project's texts file
(backend/core/texts.py) the first time anything opens it.

Clicking a text's "Transcribed by you" count opens its clause page: one clause at a time, played alone or with context, its ASR
candidates as buttons, an entry field to transcribe it, and Back/Next (each move saves).

"Sort words from these texts", under the board, puts the words of all the texts into one word lexicon
(backend/core/text_lexicon.py) and switches to it, to sort them together.
"""
import itertools
import math
import os
import queue
import tempfile
import threading
import copy

from frontend import ui
from tasks.base import Task
from tasks.sound import Sound
from tasks.bulk_asr import BulkASR
from backend.core import texts
from utilities.i18n import _, N_
from utilities import logsetup
from utilities.error_handler import notify_error as ErrorNotice
log = logsetup.getlog(__name__)

CONTEXT_SECONDS = 2.0   # heard before and after a clause by "With context"
TEXT_PLACEHOLDER = N_("(none)")  # shown (translated) for an empty title/speaker/other voices; never stored
# Candidate columns: as many as fit in CANDIDATE_CHAR_BUDGET characters of the 'read' font (a safe
# page width), each as wide as the longest candidate plus padding, aiming at no more than
# CANDIDATE_MAX_ROWS rows. They always sit in a scrolling frame (buildcandidates).
CANDIDATE_CHAR_BUDGET = 72
CANDIDATE_PAD_CHARS = 4
CANDIDATE_MAX_ROWS = 6
SPLIT_MAX = 6        # "Split into:" offers 2..SPLIT_MAX
LINE_SPLIT_MAX = 5   # each line of the whole-text page offers 2..LINE_SPLIT_MAX (Kent, 2026-11-23: 2|3|4|5)
SPLIT_MIN_MS = 500   # no piece of a split shorter than this
SPLIT_POOL = 12      # ways to split are made from this many of a clause's best breakpoints

# How a whole-text step ended, for TextRun.
DONE, CANCELLED, FAILED = 'done', 'cancelled', 'failed'
ASR, WORDS = 'asr', 'words'   # the whole-text steps


def _minutes(seconds):
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


class TextBulkASR(BulkASR):
    """Bulk ASR over clause chunks rather than lexicon recordings: each phrase's span is written as a
    16 kHz wav (the models take paths), and results go into the texts file as candidates. Clauses a model has
    already transcribed are skipped for that model. on_done(outcome, note) runs when its window closes, which
    it does by itself when the run ends well."""

    def __init__(self, program, text, audio, phrases, on_done, heading=None, mms_only=False):
        super().__init__(program)
        self.text = text
        self.audio = audio
        self.phrases = phrases
        self.on_done = on_done
        self.heading = heading
        self.mms_only = mms_only   # Parse: only the MMS adapters, as words are aligned with one
        self.outcome = self.note = None

    def _keep_keys(self):
        if not self.mms_only:
            return super()._keep_keys()
        # The MMS-1b-all adapter for each language in Transcription settings, wherever a clause lacks its
        # candidate (prior drafts skip the rest); nothing else (Kent 2026-11-07).
        asr = self.asr
        return {f"{repo} ({asr._mms_lang(lang)}!)"
                for repo in getattr(asr, 'language_adaptor_models', ()) if repo in asr.models
                for lang in asr.effective_sister_languages()}

    def _collect(self):
        # Candidates that heard other audio than the clause now uses (a careful take recorded since) go first,
        # so the models run again on what is there now (Kent, 2026-11-21: ASR only from the take).
        stale = [p for p in self.phrases if p.stale_candidates()]
        for p in stale:
            p.clear_candidates()
        if stale:
            log.info(f"{self.text.title}: dropped the candidates of {len(stale)} clauses, which have a careful "
                     f"take now")
            self.text.db.save()
        folder = os.path.join(tempfile.gettempdir(), 'azt_text_chunks')
        return list(texts.chunk_files(self.text, self.audio, self.phrases, folder).items())

    def run(self):
        self.pairs = self._collect()
        if not self.pairs:
            self.on_done(DONE, None)
            return
        if not self._prepare_asr():
            self.on_done(FAILED, _("the speech recognition models couldn’t be loaded"))
            return
        self._build_window(len(self.pairs))
        status = _("Transcribing {n} clauses…").format(n=len(self.pairs))
        self.status['text'] = f"{self.heading}\n{status}" if self.heading else status
        threading.Thread(target=self._worker, name='text-asr', daemon=True).start()
        self._poll()

    def _prior_drafts(self):
        return {path: set(phrase.candidates()) for path, phrase in self.pairs}

    def _persist(self, results):
        n = wrote = 0
        for path, phrase in self.pairs:
            tx, _ipa = results.get(path, ({}, {}))
            if not tx:
                continue
            n += 1
            key = len(tx)
            if self._persisted.get(path) == key:
                continue
            phrase.add_candidates(tx)
            phrase.set_asr_audio(phrase.audio_source())   # what they heard: its take, or the recording
            self._persisted[path] = key
            wrote += 1
        if wrote:
            self.text.db.save()
        return n

    def _finish(self, error=None, persisted=0, attempted=0, total=0):
        super()._finish(error=error, persisted=persisted, attempted=attempted, total=total)
        if error:
            self.outcome, self.note = FAILED, _("transcribing failed: {e}").format(e=error)
        elif self.cancel.is_set():
            self.outcome, self.note = CANCELLED, _("transcribing cancelled")
        else:
            self.outcome = DONE
            self.note = _("{n} of {total} clauses transcribed").format(n=persisted, total=total)
            self._close()   # nothing to read in the window: go on
            return
        self.button['text'] = _("Close")

    def _close(self):
        try:
            self.win.destroy()
        except Exception:
            pass
        self.on_done(self.outcome or CANCELLED, self.note)


class TextFindWords:
    """"Find words" over one text: word breaks by consensus over the clauses' ASR candidates, and times by
    forced alignment with an MMS adapter (azt_asr/wordbreaks.py, via backend/core/texts.py). The work runs on a
    worker thread, on a copy of the text, with a progress window; the words go into the text and the texts file
    when it ends (on the main thread). on_done(outcome, note) runs when the window closes, which it does by
    itself when the run ends well."""

    def __init__(self, program, text, audio, on_done, heading=None, only=None):
        self.program = program
        self.text = text
        self.audio = audio
        self.on_done = on_done
        self.heading = heading
        self.only = only   # guids of the clauses to do (before sorting: Text.sync_words), or None: all
        self.outcome = self.note = None
        self.cancel = threading.Event()
        self.q = queue.Queue()  # worker -> main: ('progress', (done, total)), ('done', counts), ('error', str)

    def run(self):
        ss = getattr(self.program, 'soundsettings', None)
        tally = getattr(ss, 'asr_repos', None) or {}
        cache_dir = (getattr(ss, 'asr_kwargs', None) or {}).get('cache_dir')
        adapter = texts.align_adapter(self.text, tally)
        if not adapter:
            self.on_done(FAILED, _("no clause has candidates from an MMS model, and words are aligned with one: "
                                   "transcribe it first, with MMS chosen in Transcription settings"))
            return
        snapshot = copy.deepcopy(self.text.node)   # here, on the main thread; the worker reads only this
        # clauses with a careful take are cut from it, not the recording (Kent, 2026-11-21)
        self.takes = texts.take_audio(self.text)
        work = (snapshot, self.audio, self.text.db.project_dir, self.text.output_path('_words.TextGrid'),
                self.text.output_path('_words.tsv'), adapter, cache_dir)
        self.mms = texts.loaded_mms(self.program)
        self.snapshot = snapshot
        self.total = len(self.only) if self.only is not None else len(self.text.phrases())
        self._build_window(adapter)
        threading.Thread(target=self._worker, args=work, name='text-words', daemon=True).start()
        self._poll()

    def _build_window(self, adapter):
        self.win = ui.Window(self.program.taskchooser.ui, title=self.heading or _("Find words"), exit=False)
        f = self.win.frame
        self.status = ui.Label(f, text=_("Loading the alignment model ({adapter})…").format(adapter=adapter),
                               row=0, column=0, sticky='ew')
        self.bar = ui.Progressbar(f, row=1, column=0, sticky='ew')
        self.button = ui.Button(f, text=_("Cancel"), command=self._request_cancel, row=2, column=0)

    def _request_cancel(self):
        self.cancel.set()
        self.status['text'] = _("Cancelling — finishing the current clause…")

    def _worker(self, *work):
        try:
            counts = texts.find_words(*work, progress=lambda done, total: self.q.put(('progress', (done, total))),
                                      should_cancel=self.cancel.is_set, mms=self.mms, takes=self.takes,
                                      only=self.only)
        except Exception as e:
            log.error(f"Find words failed: {e}", exc_info=True)
            self.q.put(('error', str(e)))
            return
        self.q.put(('done', counts))

    def _progress(self, done_total):
        done, total = done_total
        self.status['text'] = _("Finding the words of clause {n} of {total}…").format(n=done, total=total)
        self.bar.current(done / max(total, 1))

    def _poll(self):
        last = None   # coalesce: one UI update per poll
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == 'progress':
                    last = payload
                elif kind == 'error':
                    self._finish(error=payload)
                    return
                elif kind == 'done':
                    self._finish(counts=payload)
                    return
        except queue.Empty:
            pass
        if last:
            self._progress(last)
        self.win.after(150, self._poll)

    def _finish(self, counts=None, error=None):
        if error:
            self.outcome, self.note = FAILED, _("couldn’t find words: {e}").format(e=error)
        else:
            self.text.take_words(self.snapshot)
            self.text.db.save()
            if counts['cancelled']:
                self.outcome = CANCELLED
                self.note = _("cancelled: {words} words found in {worded} of {total} clauses so far").format(
                    words=counts['words'], worded=counts['worded'], total=self.total)
            else:
                self.outcome = DONE
                self.note = _("{words} words found in {worded} of {total} clauses ({timed} with times)").format(
                    words=counts['words'], worded=counts['worded'], total=self.total, timed=counts['timed'])
                self._close()   # nothing to read in the window: go on
                return
        self.status['text'] = self.note
        self.bar.current(1.0)
        self.button['text'] = _("Close")
        self.button['command'] = self._close

    def _close(self):
        try:
            self.win.destroy()
        except Exception:
            pass
        self.on_done(self.outcome or CANCELLED, self.note)


class TextRun:
    """Whole-text steps (ASR, WORDS, in that order) over recordings, one after another: each recording is
    opened (cut into clauses the first time), then each step runs with its own progress window. Transcribing
    and finding words are adjacent, so Find words borrows the models ASR has loaded (texts.loaded_mms).
    A cancel stops the whole run; a step that fails skips the rest of that recording, and the run goes on to
    the next. What each step did goes on the board (TranscribeTexts.boardnote) at the end.
    only: {path: guids} to find words for only those clauses of each recording (before sorting); then:
    called at the end, unless the run was cancelled."""

    def __init__(self, task, paths, steps, only=None, then=None):
        self.task = task
        self.program = task.program
        self.todo = list(paths)
        self.n = len(self.todo)
        self.steps = [s for s in (ASR, WORDS) if s in steps]
        self.notes = []
        self.only = only
        self.then = then
        self.cancelled = False

    def start(self):
        self.task.boardnote = None
        self._next()

    def _next(self):
        self.text = self.audio = None
        if not self.todo:
            self._end()
            return
        path = self.todo.pop(0)
        self.path = path
        self.i = self.n - len(self.todo)
        name = os.path.basename(path)
        try:
            with self.task.ui.waiting(_("Opening {name}…").format(name=name)):
                self.text, self.audio = self.task.db.open_recording(path)
        except Exception as e:
            log.error(f"couldn't open {path} as a text: {e}", exc_info=True)
            self.notes.append(_("{name}: couldn’t open it: {e}").format(name=name, e=e))
            self._next()
            return
        self.left = list(self.steps)
        self._step()

    def _step(self):
        if not self.left:
            self._next()
            return
        step = self.left.pop(0)
        heading = (_("{title} (text {i} of {n})").format(title=self.text.title, i=self.i, n=self.n)
                   if self.n > 1 else self.text.title)
        if step == ASR:
            # Parse (ASR then WORDS): the MMS adapters only, where a clause lacks one; "ASR only" runs every
            # model in settings (Kent 2026-11-07). Clauses a model has done are skipped either way.
            TextBulkASR(self.program, self.text, self.audio, self.text.phrases(), self._done, heading,
                        mms_only=WORDS in self.steps).run()
        else:
            only = self.only.get(self.path) if self.only is not None else None
            TextFindWords(self.program, self.text, self.audio, self._done, heading, only=only).run()

    def _done(self, outcome, note):
        if note:
            self.notes.append(f"{self.text.title}: {note}")
        if outcome == CANCELLED:
            self.todo = []
            self.cancelled = True
            self._end()
        elif outcome == FAILED:
            self._next()
        else:
            self._step()

    def _end(self):
        self.text = self.audio = None
        self.task.boardnote = '\n'.join(self.notes) or None
        if self.then is not None and not self.cancelled:
            self.then()
            return
        self.task.refreshboard()


class BackToMainLexicon:
    """NOT A TASK: a task-list button that closes the texts' word lexicon and opens the project's again
    (App.use_lexicon(None)). It sits where Transcribe Texts does, under Analysis, which is offered only on the
    main lexicon, so the two take turns there (Kent, 2026-11-20: "that's where most people would look for it").
    The same action stays in the task list's menus (ui_shell)."""
    tasktitle = N_("Back to the main lexicon")
    taskicon = 'iconWord'
    lexicons = ('texts',)
    mark_texts = False   # its title is about leaving the texts; no " — text words" on it

    def tooltip(self):   # called unbound, as tooltip(None), like the tasks'
        return _("Close the word lexicon of the texts, and open the project's own lexicon again.")

    def __init__(self, program, **kwargs):
        program.use_lexicon(None)


class VirtualRows:
    """Lines of a long scrolling page (one frame each, in `scroll.content`'s column 0), DRAWN ONLY NEAR THE
    VIEW: Tk renders every mapped widget, and on this display that is ~57 ms a widget, so a 57-clause text's
    860 took 49.5 s (Kent, 2026-11-24). Lines away from the view are made but not gridded; each row keeps a
    pinned height, so the scrollbar still measures the whole page. The same idea as the verify page's
    (SortPresenter._virtualize_verify), on lines that are whole frames, which keeps it simple: a line is
    gridded at its CURRENT place whenever it comes into view, so lines moved by a split or join need nothing
    else. Without a canvas to read (another backend) every line is drawn."""
    BUFFER = 2          # lines drawn beyond each edge of the view
    POLL_MS = 150       # how often the view is checked (scrolling has no one event on every backend)

    def __init__(self, scroll, lines, row_height=48):
        self.scroll, self.lines, self.rowH = scroll, list(lines), row_height
        self.content = scroll.content
        self.canvas = getattr(scroll, 'canvas', None)
        self.placed = {}     # id(line) -> the row it is gridded at
        self.win = None
        self.pinned = 0
        self.measured = False
        self._pin()
        self.window()
        if self.canvas is not None:
            self.canvas.after(self.POLL_MS, self._poll)

    def _pin(self):
        n = len(self.lines)
        for r in range(n):
            self.content.rowconfigure(r, minsize=self.rowH)
        for r in range(n, self.pinned):
            self.content.rowconfigure(r, minsize=0)   # rows a join emptied
        self.pinned = n

    def _range(self):
        n = len(self.lines)
        if self.canvas is None:
            return 0, n
        try:
            height = self.canvas.winfo_height()
            if height <= 1:
                height = self.canvas.winfo_screenheight()   # not mapped yet: as much as could show
            top = self.canvas.yview()[0]
        except Exception:
            height, top = self.canvas.winfo_screenheight(), 0.0
        if not 0.0 <= top <= 1.0:
            top = 0.0
        first, visible = int(top * n), int(height / self.rowH) + 1
        lo, hi = max(0, first - self.BUFFER), min(n, first + visible + self.BUFFER)
        if lo >= hi:   # never draw nothing
            lo, hi = 0, min(n, visible + self.BUFFER)
        return lo, hi

    def window(self, force=False):
        try:
            if not self.content.winfo_exists():
                return
        except Exception:
            return
        lo, hi = self._range()
        if not force and self.win == (lo, hi):
            return
        self.win = (lo, hi)
        for i, line in enumerate(self.lines):
            key = id(line)
            if lo <= i < hi:
                if self.placed.get(key) != i:
                    line.grid(row=i, column=0, sticky='w', pady=2)
                    self.placed[key] = i
            elif key in self.placed:
                line.grid_remove()
                del self.placed[key]

    def _poll(self):
        try:
            if not self.canvas.winfo_exists():
                return
        except Exception:
            return
        if not self.measured:   # the real line height, once a line has one: rows pinned to fit it
            heights = [line.winfo_height() for line in self.lines if id(line) in self.placed]
            tallest = max(heights, default=1)
            if tallest > 1:
                self.measured = True
                if abs(tallest + 4 - self.rowH) > 4:
                    self.rowH = tallest + 4
                    self._pin()
                    self.win = None
        self.window()
        self.canvas.after(self.POLL_MS, self._poll)

    def replace(self, i, count, new):
        """Lines i…i+count-1 become `new` (a split: one becomes several; a join: two become one)."""
        for line in self.lines[i:i + count]:
            self.placed.pop(id(line), None)
            line.destroy()
        self.lines[i:i + count] = new
        self._pin()
        self.window(force=True)


class CarefulTake:
    """A clause said again carefully, in the record / play / delete pattern of the word record buttons
    (sound_ui.RecordButtonFrame; Kent, 2026-11-23: a record button beside ▶ didn't say it meant "delete and
    record again"): with no take, a press-and-hold record button (composites.hold); after a good take, ‣ to
    hear it and × to drop it, which brings the record button back. `name` is the take's file relative to the
    texts folder ('audio/…'); `taken` says the clause has it now. on_saved(name) links a new take (a clause's
    careful-audio item, or a split piece's, once the split is made); on_removed() unlinks it (the file stays,
    and the next take records over it). The recording itself is never touched (Kent, 2026-11-20)."""

    def __init__(self, parent, task, name, on_saved, row, column, taken=False, on_removed=None):
        from frontend.play_buttons import playback
        self.task, self.name, self.on_saved, self.on_removed = task, name, on_saved, on_removed
        self.url = os.path.join(task.db.project_dir, texts.TEXTS_FOLDER, *name.split('/'))
        self.frame = ui.Frame(parent, row=row, column=column, sticky='w', padx=(10, 0))
        self.b = self.p = self.r = None
        self.audio, self.ss = playback(task.program, task)
        if self.audio is None:
            return   # no sound on this machine: no button (playback says why in the log)
        try:
            from io_put import sound
        except Exception as e:
            log.info(f"no careful-speech button ({e})")
            return
        self.sound = sound
        if taken and os.path.exists(self.url):
            self._playanddelete()
        else:
            self._recordbutton()

    def _recordbutton(self):
        from frontend import composites
        self.b = ui.Button(self.frame, image='record', command=lambda: None, row=0, column=0)
        composites.hold(self.b, self._start, self._stop)
        ui.ToolTip(self.b, _("Say this clause again, carefully: press, speak, release"))

    def _playanddelete(self):
        player = self.sound.SoundFilePlayer(self.url, self.audio, self.ss)
        self.p = ui.Button(self.frame, text='‣', font='readbig', command=lambda: player.play(),
                           row=0, column=1, sticky='nsw')
        ui.ToolTip(self.p, _("Hear the careful take"))
        self.r = ui.Button(self.frame, text='×', font='read', command=self._remove, row=0, column=2,
                           sticky='nsw')
        ui.ToolTip(self.r, _("Try again"))

    def _remove(self):
        for w in (self.p, self.r):
            if w is not None:
                w.destroy()
        self.p = self.r = None
        if self.on_removed is not None:
            self.on_removed()
        self._recordbutton()

    def _start(self, event=None):
        os.makedirs(os.path.dirname(self.url), exist_ok=True)
        self.recorder = self.sound.SoundFileRecorder(self.url, self.audio, self.ss)
        self.recorder.start()

    def _stop(self, event=None):
        try:
            self.recorder.stop()
        except Exception as e:
            log.info(f"couldn't stop the careful-speech recorder ({e})")
            return
        if getattr(self.recorder, 'file_write_OK', False):
            log.info(f"careful-speech take: {self.url}")
            self.b.destroy()   # as the word buttons: the record button gives way to ‣ and ×
            self.b = None
            self._playanddelete()
            self.on_saved(self.name)
            session = getattr(self.task.program, 'collab', None)
            if session is not None:   # the take is a file outside the texts file: commit it now
                session.commit_artifacts()


class TranscribeTexts(Sound, Task):
    tasktitle = N_("Transcribe Texts")
    taskicon = 'iconTextRec'   # was Transcribe Tone's icon (Kent, 2026-11-20)
    lexicons = ('main',)       # it MAKES the text lexicon; not offered while sorting one
    do_not_show_slices = True
    do_not_show_cvt = True
    no_leaderboard = False
    icon_leaderboard = False
    glyph_leaderboard = False

    def tooltip(self):
        return _("This task helps you transcribe longer recordings (texts) clause by clause, starting "
                 "from what the speech recognition models give.")

    def dobuttonkwargs(self):
        return None   # no big button: the board's rows open the texts

    def setcontext(self):
        super().setcontext()
        from frontend import sound_ui
        self.context.menuitem(_("Transcription settings"),
                              lambda event=None: sound_ui.ASRModelSelectionWindow(self))

    # ---- the texts file ---------------------------------------------------------------------------------

    @property
    def db(self):
        if getattr(self, '_db', None) is None:
            s = self.program.settings
            path = os.path.join(str(s.directory), f"{s.liftnamebase}.texts.flextext")
            self._db = texts.TextsDB(path, s.directory, self.program.params.analang())
        return self._db

    def lexicon_path(self):
        from backend.core import text_lexicon
        return text_lexicon.lexicon_path(self.db, self.program.settings.liftnamebase)

    # ---- the board --------------------------------------------------------------------------------------

    def buildboard(self, parent):
        """The texts board, in the status frame's board (StatusFrame.maybeboard): a row per recording in
        <project>/texts (any length: everything there is a text), with its counts and whole-text steps;
        "Process all" above, "Sort words from these texts" below. Returns the table's ScrollingFrame, for the
        status frame to reflow once the window is mapped (it scrolls only then), or None."""
        folder = texts.texts_dir(self.program.settings.directory)
        recordings = texts.recordings(folder, min_seconds=0)
        ui.Label(parent, text=_("Texts"), font='title', row=0, column=0, sticky='w', padx=10)
        if not recordings:
            ui.Label(parent, text=_("No recordings in {folder}: put the texts’ recordings there.").format(
                         folder=folder), row=1, column=0, sticky='w', padx=10)
            return
        b = ui.Button(parent, text=_("Process all"), row=1, column=0, sticky='w', padx=10, pady=5,
                      command=lambda: self.run_steps([p for p, _s in recordings], (ASR, WORDS)))
        ui.ToolTip(b, _("Parse each text, one after another: transcribe with MMS any clause it hasn’t done, "
                        "then find the words"))
        scroll = ui.ScrollingFrame(parent, row=2, column=0, sticky='w')
        table = scroll.content
        # Clause counts, the total given once (Kent, 2026-11-06)
        headers = (_("Text"), _("Length"), _("Clauses"), _("ASR"),
                   _("Parsed (words)"), _("Transcribed by you"))
        tips = {3: _("Automatically transcribed by AI models")}
        for column, header in enumerate(headers):
            label = ui.Label(table, text=header, font='small', row=0, column=column, padx=5, sticky='s')
            if column in tips:
                ui.ToolTip(label, tips[column])
        any_words = False
        for row, (path, seconds) in enumerate(recordings, 1):
            text = self.db.at(path)
            name = text.title if text is not None and text.title else os.path.basename(path)
            # the title opens the whole-text page: every clause, to listen, record, split and join (Kent,
            # 2026-11-23); the clause-by-clause page stays on "Transcribed by you"
            label = ui.Button(table, text=name, row=row, column=0, sticky='e', padx=5,
                              command=lambda p=path: self.makewholewindow(p))
            tip = _("Listen to {name} clause by clause, record it said again carefully, and split or join its "
                    "clauses").format(name=name)
            if name != os.path.basename(path):
                tip += '\n' + os.path.basename(path)
            ui.ToolTip(label, tip)
            ui.Label(table, text=_minutes(seconds), row=row, column=1, padx=5)
            if text is None:
                cells = ('—',) * 4
            else:
                c = text.counts()
                any_words = any_words or bool(c['words'])
                # each column leads with a number of clauses
                cells = (str(c['clauses']), str(c['asr']), f"{c['worded']} ({c['words']})", str(c['final']))
            for column, cell in enumerate(cells, 2):
                if column == 5:   # transcribed by you: opens the clause page (Kent, 2026-11-06)
                    label = ui.Button(table, text=cell, row=row, column=column, padx=5,
                                      command=lambda p=path: self.makewindow(p))
                    tip = _("Transcribe {name} clause by clause").format(name=name)
                    if text is None:
                        tip += '\n' + _("Not opened yet: it is cut into clauses the first time")
                    ui.ToolTip(label, tip)
                    continue
                label = ui.Label(table, text=cell, row=row, column=column, padx=5)
                if text is None:
                    ui.ToolTip(label, _("Not opened yet: it is cut into clauses the first time"))
            steps = ui.Frame(table, row=row, column=6, sticky='w', padx=5)
            # named as the columns they fill (Kent 2026-11-07)
            for column, (label, which, tip) in enumerate((
                    (_("Parse"), (ASR, WORDS),
                     _("Find the words of {name}, first transcribing with MMS (for the languages in "
                       "Transcription settings) any clause it hasn’t done")),
                    (_("ASR only"), (ASR,),
                     _("Transcribe {name} with every model in Transcription settings, where it hasn’t been; "
                       "no words found")))):
                b = ui.Button(steps, text=label, font='small', row=0, column=column, padx=2,
                              command=lambda p=path, w=which: self.run_steps([p], w))
                ui.ToolTip(b, tip.format(name=name))
        row = 3
        note = getattr(self, 'boardnote', None)
        if note:
            ui.Label(parent, text=note, font='small', row=row, column=0, sticky='w', padx=10, pady=5)
            row += 1
        if any_words:
            b = ui.Button(parent, text=_("Sort words from these texts"), command=self.sort_texts,
                          row=row, column=0, sticky='w', padx=10, pady=5)
            ui.ToolTip(b, _("Put the words found in all these texts into one word lexicon, and switch to it "
                            "to sort them"))
        return scroll

    def refreshboard(self):
        try:
            self.program.mainwindow.status.maybeboard()
        except Exception as e:
            log.info(f"couldn't redraw the texts board: {e}")

    def run_steps(self, paths, steps):
        TextRun(self, paths, steps).start()

    def sort_texts(self):
        """All the texts' words into the one word lexicon (new ones added, changed ones updated, gone ones
        removed: text_lexicon.make_lexicon), then switch to it (the
        project, its settings and audio stay; see App.use_lexicon) and go to the task list to sort them."""
        from backend.core import text_lexicon
        path = self.lexicon_path()
        lexicon = getattr(self.program, 'lexicon_filename', None)
        if lexicon and os.path.abspath(str(lexicon)) == os.path.abspath(path):
            # it is open for sorting, and would be written over from memory
            ErrorNotice(_("The texts’ word lexicon is open for sorting; go back to the main lexicon "
                          "(on the task list) before adding to it."))
            return
        # What sorting respelled goes into the texts first (as on "Back to the main lexicon"), or this rebuild
        # would spell it back: azt doesn't reopen the word lexicon after a restart, so that may not have run.
        self.program.texts_from_lexicon(path)
        self._db = None   # that wrote the texts file: read it again
        # Then each transcribed clause's words say what its transcription now does (Kent, 2026-11-23): respelled
        # in place, or, where its breaks changed, found and timed again (only those clauses), before building.
        again = {}
        for text in self.db.texts():
            _n, guids = text.sync_words()
            if guids and os.path.exists(text.path()):
                again[text.path()] = guids
        self.db.save()
        if again:
            TextRun(self, list(again), (WORDS,), only=again, then=lambda: self.build_word_lexicon(path)).start()
            return
        self.build_word_lexicon(path)

    def build_word_lexicon(self, path):
        """The word lexicon from the texts' words as they are now (sort_texts has brought them up to date),
        then switch to it."""
        from backend.core import text_lexicon
        text_list = [t for t in self.db.texts() if os.path.exists(t.path())]
        try:
            # spans are named from the lexicon's own folder, its audio folder when open (file_parser);
            # all_texts, so a text whose recording is missing keeps its words' entries
            result = text_lexicon.make_texts_lexicon(path, text_list, os.path.dirname(path),
                                                     self.program.params.analang(),
                                                     self.program.params.audiolang(),
                                                     all_texts=self.db.texts())
        except Exception as e:
            log.error(f"couldn't make the texts' word lexicon: {e}", exc_info=True)
            ErrorNotice(_("Couldn’t make the word lexicon: {e}").format(e=e))
            return
        if result is None:
            ErrorNotice(_("No text has words yet: click “Parse” first."))
            return
        self.program.use_lexicon(path)

    # ---- the clause page --------------------------------------------------------------------------------

    def opentext(self, path):
        """Open the text of this recording (cut into clauses the first time) as self.text, self.audio,
        self.phrases. False (and said) if it can't be."""
        path = path or getattr(self.program.settings, 'textrecording', None)
        if not path or not os.path.exists(path):
            ErrorNotice(_("Pick a text on the board first."))
            return False
        self.program.settings.textrecording = path
        with self.ui.waiting(_("Opening {name}…").format(name=os.path.basename(path))):
            try:
                self.text, self.audio = self.db.open_recording(path)
            except Exception as e:
                log.error(f"couldn't open {path} as a text: {e}")
                ErrorNotice(_("Couldn’t open {name}: {e}").format(name=os.path.basename(path), e=e))
                return False
            self.phrases = self.text.phrases()
            if not self.phrases:
                ErrorNotice(_("No speech found in {name}.").format(name=os.path.basename(path)))
                return False
        return True

    def makewindow(self, path=None):
        if not self.opentext(path):
            return
        # Resume at the first clause with no transcription.
        self.index = next((i for i, p in enumerate(self.phrases) if not p.final()), 0)
        self.ui.getrunwindow(title=_("Transcribe {title}").format(title=self.text.title))
        self.buildclause()
        self.ui.runwindow.waitdone()
        self.ui.runwindow.deiconify()

    # ---- the whole text (Kent, 2026-11-23): every clause a line, to listen to and record the text clause by
    # clause, splitting and joining clauses as you go; no transcriptions here. From the text's title on the board.

    def makewholewindow(self, path):
        if not self.opentext(path):
            return
        self.ui.getrunwindow(title=_("Clauses of {title}").format(title=self.text.title))
        self.buildwhole()
        self.renumberlines()
        self.ui.runwindow.waitdone()
        self.ui.runwindow.deiconify()

    def buildwhole(self):
        """A line per clause: its number, ▶ (the clause) and [▶] (with context), its times, its careful take
        (record, or ‣ and ×), and 2…LINE_SPLIT_MAX to split it into that many at its best breakpoints there
        and then, and "Join with next". The whole page scrolls. A split is made at once (no other ways offered,
        no cancel: Kent, 2026-11-23); a wrong one is fixed by joining pieces, and splitting again.
        FAST ON PURPOSE (Kent, 2026-11-24: "lots of very long pauses"): drawing every line of a 57-clause text
        took 49.5 s here (~860 widgets at ~57 ms each, log 2026-11-24 09:38), and rebuilding them all after each
        join 32 s. So only the lines near the view are drawn (VirtualRows), and a split or join replaces just
        its own lines."""
        self.page = 'whole'
        top = self.ui.runwindow.frame
        ui.Label(top, text=self.text.title or os.path.basename(self.text.location), font='title',
                 row=0, column=0, sticky='w')
        ui.Label(top, text=_("Listen to each clause, record it said again carefully, and split or join clauses "
                             "where they are wrong."), font='small', row=1, column=0, sticky='w', pady=(0, 10))
        self.wholescroll = ui.ScrollingFrame(top, row=2, column=0, sticky='nsew')
        self.wholeplayer = self.player()
        self.wholerows = VirtualRows(self.wholescroll, [self.buildline(p) for p in self.phrases])

    def buildline(self, phrase):
        """One clause's line on the whole-text page, not yet gridded (VirtualRows places it). Its buttons find
        the clause by its node when pressed, so lines can move as clauses are split and joined."""
        player, node = self.wholeplayer, phrase.node
        line = ui.Frame(self.wholescroll.content)
        line.number = ui.Label(line, text='', font='read', row=0, column=0, sticky='e', padx=(0, 10))
        b, e = phrase.begin_ms / 1000, phrase.end_ms / 1000
        ui.Button(line, text='▶', command=lambda: player.play(start=b, end=e), row=0, column=1)
        c = ui.Button(line, text='[▶]', row=0, column=2, padx=(5, 0),
                      command=lambda: player.play(start=max(0, b - CONTEXT_SECONDS), end=e + CONTEXT_SECONDS))
        ui.ToolTip(c, _("Play with context"))
        ui.Label(line, text=f"{b:.3f}–{e:.3f} s ({e - b:.1f} s)", font='small', row=0, column=3, padx=10)
        CarefulTake(line, self, phrase.careful() or self.take_name(phrase.guid[:8]),
                    on_saved=lambda name, p=phrase: self.link_take(p, name), row=0, column=4,
                    taken=phrase.careful_path() is not None, on_removed=lambda p=phrase: self.unlink_take(p))
        for k, n in enumerate(range(2, LINE_SPLIT_MAX + 1)):
            s = ui.Button(line, text=str(n), font='small', row=0, column=5 + k, padx=(20 if k == 0 else 2, 2),
                          command=lambda n=n: self.splitline(node, n))
            ui.ToolTip(s, _("Split this clause into {n} clauses").format(n=n))
        if phrase.node is not self.phrases[-1].node:
            ui.Button(line, text=_("Join with next"), font='small', command=lambda: self.joinline(node),
                      row=0, column=5 + LINE_SPLIT_MAX, padx=(10, 2))
        return line

    def renumberlines(self):
        for k, line in enumerate(self.wholerows.lines, 1):
            try:
                line.number['text'] = f"{k}."
            except Exception as e:
                log.info(f"whole-text page: line {k} not renumbered ({e})")

    def _index_of(self, node):
        return next((i for i, p in enumerate(self.phrases) if p.node is node), None)

    def splitline(self, node, n):
        i = self._index_of(node)
        if i is None:
            return
        phrase = self.phrases[i]
        with self.ui.runwindow.waiting(self.splitting_msg(i, n)):
            options = self.split_options(phrase, n)
            if not options:
                ErrorNotice(_("Couldn’t find {n} clauses in this one: try fewer.").format(n=n))
                return
            pieces = self.text.split_phrase(phrase, options[0])
            self.db.save()
            self.phrases = self.text.phrases()
            self.wholerows.replace(i, 1, [self.buildline(p) for p in self.phrases[i:i + len(pieces)]])
            self.renumberlines()

    def joinline(self, node):
        i = self._index_of(node)
        if i is None or i + 1 >= len(self.phrases):
            return
        with self.ui.runwindow.waiting(self.joining_msg(i)):
            if self.text.join_phrases(self.phrases[i], self.phrases[i + 1]) is None:
                ErrorNotice(_("Couldn’t join these clauses."))
                return
            self.db.save()
            self.phrases = self.text.phrases()
            self.wholerows.replace(i, 2, [self.buildline(self.phrases[i])])
            self.renumberlines()

    @staticmethod
    def splitting_msg(i, n):
        return _("Splitting clause {k} into {n}: finding the pauses in it most likely to be clause breaks, "
                 "then sharing out its words, and saving…").format(k=i + 1, n=n)

    @staticmethod
    def joining_msg(i):
        return _("Joining clauses {k} and {k2}: putting their words and transcriptions together, "
                 "and saving…").format(k=i + 1, k2=i + 2)

    def showclause(self, index, msg=None, work=None):
        """Show clause `index`. `work` (a split or join) runs first, under the same wait window, which says what
        is happening (`msg`); if it returns False the page is left as it was."""
        with self.ui.runwindow.waiting(msg, thenshow=True):
            if work is not None and work() is False:
                return
            self.index = index
            self.ui.runwindow.resetframe()
            if index >= len(self.phrases):
                self.buildend()
            else:
                self.buildclause()

    def player(self):
        from io_put import sound
        ss = getattr(self.program, 'soundsettings', None)
        return sound.SoundFilePlayer(self.text.path(), getattr(ss, 'audio', None), ss)

    def buildtextframe(self, parent):
        """Title, speaker and other voices as click-to-edit 'name: value' lines (each saved when
        committed), beside the progress count. Whole-text steps are on the board."""
        from frontend import composites
        frame = ui.Frame(parent, row=0, column=0, sticky='w', pady=10)
        placeholder = _(TEXT_PLACEHOLDER)
        for row, (key, label) in enumerate((('title', _("Title:")), ('speaker', _("Speaker:")),
                                            ('voices', _("Other voices:")))):
            var = ui.StringVar(value=getattr(self.text, key) or placeholder)
            composites.entry_field(frame, var, label=label, placeholder=placeholder,
                                   on_commit=lambda value, k=key: self.settextfield(k, value),
                                   row=row, column=0)
        done, total = self.text.progress()
        ui.Label(frame, text=_("{done} of {total} clauses transcribed").format(done=done, total=total),
                 font='small', row=0, column=3, sticky='w', padx=20)

    def settextfield(self, key, value):
        setattr(self.text, key, '' if value == _(TEXT_PLACEHOLDER) else value)
        self.db.save()

    def buildcandidates(self, parent, by_value, row, column=0):
        """Candidate buttons, most-agreed-on first, in as many columns as fit (column-major, so the
        ranking reads down each column), ALWAYS in a scrolling frame, which is only as tall as its buttons
        until the page runs out, then scrolls. Deciding to scroll by ROW COUNT (past MAX_ROWS) missed long
        clauses: a few candidates of 3–4 wrapped lines each ran off the bottom of the page with no scrollbar
        (Kent, 2026-11-20). Candidates too long for one line use the default font, not the large 'read'."""
        items = sorted(by_value.items(), key=lambda kv: -len(kv[1]))
        n = len(items)
        widest = max(len(value) for value, _models in items) + CANDIDATE_PAD_CHARS
        fit = max(1, CANDIDATE_CHAR_BUDGET // widest)
        ncols = max(1, min(fit, math.ceil(n / CANDIDATE_MAX_ROWS)))
        nrows = math.ceil(n / ncols)
        font = 'read' if widest <= CANDIDATE_CHAR_BUDGET else 'default'
        frame = ui.ScrollingFrame(parent, row=row, column=column, sticky='w', pady=10).content
        for i, (value, models) in enumerate(items):
            b = ui.Button(frame, text=value, font=font,
                          command=lambda v=value, m=models: self.pick(v, m),
                          row=i % nrows, column=i // nrows, sticky='w', padx=(0, 10))
            ui.ToolTip(b, text='\n'.join(models))

    def buildclause(self):
        self.page = 'clause'
        top = self.ui.runwindow.frame
        phrase = self.phrases[self.index]
        self.buildtextframe(top)
        ui.Label(top, text=_("Clause {n} of {total}").format(n=self.index + 1, total=len(self.phrases)),
                 font='title', row=1, column=0, sticky='w')
        clause = ui.Frame(top, row=2, column=0, sticky='ew', pady=10)
        begin, end = phrase.begin_ms / 1000, phrase.end_ms / 1000
        player = self.player()
        play = ui.Frame(clause, row=0, column=0, sticky='w')
        ui.Button(play, text=_("Play clause"), command=lambda: player.play(start=begin, end=end),
                  row=0, column=0, sticky='w')
        ui.Button(play, text=_("Play with context"),
                  command=lambda: player.play(start=max(0, begin - CONTEXT_SECONDS), end=end + CONTEXT_SECONDS),
                  row=0, column=1, sticky='w', padx=10)
        ui.Label(play, text=f"{begin:.3f}–{end:.3f} s", font='small', row=0, column=2, padx=10)
        # the clause said again carefully (Kent, 2026-11-20: "we're going to want to do the careful speech")
        CarefulTake(play, self, phrase.careful() or self.take_name(phrase.guid[:8]),
                    on_saved=lambda name, p=phrase: self.link_take(p, name), row=0, column=3,
                    taken=phrase.careful_path() is not None, on_removed=lambda p=phrase: self.unlink_take(p))
        # SPLIT THIS CLAUSE: how many clauses it really is; the split screen finds that many (showsplit)
        split = ui.Frame(play, row=0, column=4, sticky='w', padx=(30, 0))
        ui.Label(split, text=_("Split into:"), font='small', row=0, column=0)
        for k, n in enumerate(range(2, SPLIT_MAX + 1), 1):
            ui.Button(split, text=str(n), font='small', command=lambda n=n: self.showsplit(n),
                      row=0, column=k, padx=2)
        # ...and its reverse, at the end of the split buttons (Kent, 2026-11-23: badly split clauses)
        if self.index + 1 < len(self.phrases):
            b = ui.Button(split, text=_("Join with next"), font='small', command=self.joinnext,
                          row=0, column=SPLIT_MAX, padx=(10, 2))
            ui.ToolTip(b, _("Make this clause and the next one clause"))

        self.var = ui.StringVar(value=phrase.final())
        self.picked = None    # model keys of a clicked candidate; None: no click on this visit
        # Back | entry | Next on one row; the candidates go under the entry, in its column.
        entryrow = ui.Frame(clause, row=1, column=0, sticky='w', pady=(10, 0))
        if self.index > 0:
            ui.Button(entryrow, text=_("Back"), command=lambda: self.move(-1),
                      row=0, column=0, sticky='e', padx=(0, 10))
        ui.EntryField(entryrow, textvariable=self.var, font='readbig', row=0, column=1, sticky='ew')
        ui.Button(entryrow, text=_("Next"), command=lambda: self.move(1),
                  row=0, column=2, sticky='w', padx=(10, 0))
        self.candidatebox = ui.Frame(entryrow, row=1, column=1, sticky='w')
        self.buildcandidatearea(phrase)

    def buildcandidatearea(self, phrase):
        """The candidates under the entry, or "Transcribe this clause" when there are none that still apply:
        candidates that heard other audio than the clause's ASR now uses (a careful take recorded since) aren't
        shown (Kent, 2026-11-23: remove them as soon as they no longer work). Rebuilt in place when a take is
        recorded (link_take)."""
        box = self.candidatebox
        for child in list(box.winfo_children()):
            child.destroy()
        by_value = {}
        if not phrase.stale_candidates():
            for model, value in phrase.candidates().items():
                by_value.setdefault(value, []).append(model)
        if by_value:
            # Each distinct text once, labelled by every model that gave it.
            self.buildcandidates(box, by_value, row=0, column=0)
        else:
            ui.Button(box, text=_("Transcribe this clause"), command=self.transcribe_clause,
                      row=0, column=0, sticky='w', pady=10)

    # ---- the split screen (Kent, 2026-11-20): how many clauses this is; we find that many, "another way" to
    # retry; each piece with ▶ and a careful-speech take; "OK" makes them clauses ----------------------

    def take_name(self, key):
        """A careful-speech take's file, relative to the texts folder: audio/<recording stem>_<key>_careful.wav."""
        return f"audio/{self.text.stem}_{key}_careful.wav"

    def link_take(self, phrase, name):
        phrase.take_recorded(name)   # links it, and drops the candidates, which heard other audio
        self.db.save()
        try:   # their buttons go now, not on the next visit (Kent, 2026-11-23); the clause page only
            if getattr(self, 'page', None) == 'clause' and self.phrases[self.index] is phrase:
                self.buildcandidatearea(phrase)
        except Exception as e:
            log.info(f"candidates not redrawn after the take ({e})")

    def unlink_take(self, phrase):
        """× on a clause's careful take: the clause goes back to its span of the recording for ASR and words
        (the take's candidates no longer apply, so they go from the page too)."""
        phrase.set_careful('')
        self.db.save()
        try:
            if getattr(self, 'page', None) == 'clause' and self.phrases[self.index] is phrase:
                self.buildcandidatearea(phrase)
        except Exception as e:
            log.info(f"candidates not redrawn after the take was dropped ({e})")

    def clause_breakpoints(self, phrase):
        """The phrase's stored breakpoints, else found now (texts cut before 2026-11-20 have none)."""
        places = phrase.breakpoints()
        if places:
            return places
        cache = self.__dict__.setdefault('_breakpoints', {})
        key = (phrase.begin_ms, phrase.end_ms)
        if key not in cache:
            try:
                cache[key] = texts.breakpoints_for(self.audio, [key])[0]
            except Exception as e:
                log.error(f"couldn't find breakpoints for {key}: {e}")
                cache[key] = []
        return cache[key]

    def split_options(self, phrase, n):
        """Ways to cut `phrase` into `n` pieces, best first: sets of n-1 cuts from its best SPLIT_POOL
        breakpoints, every piece at least SPLIT_MIN_MS long, ranked by their scores' sum."""
        begin, end = phrase.begin_ms, phrase.end_ms
        pool = sorted([(score, ms) for ms, score, *_rest in self.clause_breakpoints(phrase)
                       if begin + SPLIT_MIN_MS <= ms <= end - SPLIT_MIN_MS], reverse=True)[:SPLIT_POOL]
        options = []
        for combo in itertools.combinations(pool, n - 1):
            cuts = sorted(ms for _s, ms in combo)
            edges = [begin] + cuts + [end]
            if all(b - a >= SPLIT_MIN_MS for a, b in zip(edges, edges[1:])):
                options.append((sum(s for s, _ms in combo), cuts))
        return [cuts for _total, cuts in sorted(options, reverse=True)]

    def showsplit(self, n, attempt=0):
        phrase = self.phrases[self.index]
        with self.ui.runwindow.waiting(_("Finding the best places to split clause {k} into {n}: the pauses in "
                                         "it most likely to be clause breaks…").format(k=self.index + 1, n=n),
                                       thenshow=True):
            options = self.split_options(phrase, n)
            if not options:
                ErrorNotice(_("Couldn’t find {n} clauses in this one: try fewer.").format(n=n))
                return
            self.__dict__.setdefault('_takes', {})
            if attempt == 0:
                self._joined_away = set()   # a new split screen: nothing joined away yet
            self.ui.runwindow.resetframe()
            self.buildsplit(phrase, n, options, attempt % len(options))

    def buildsplit(self, phrase, n, options, attempt):
        self.page = 'split'
        top = self.ui.runwindow.frame
        cuts = options[attempt]
        ui.Label(top, text=_("Clause {k} as {n} clauses").format(k=self.index + 1, n=n),
                 font='title', row=0, column=0, sticky='w')
        ui.Label(top, text=_("Way {i} of {m}: listen to each; record it said again carefully if you like.").format(
                     i=attempt + 1, m=len(options)), font='small', row=1, column=0, sticky='w')
        player = self.player()
        rows = ui.Frame(top, row=2, column=0, sticky='w', pady=10)
        edges = [phrase.begin_ms] + cuts + [phrase.end_ms]
        for i, (b, e) in enumerate(zip(edges, edges[1:])):
            ui.Label(rows, text=f"{i + 1}.", font='read', row=i, column=0, sticky='e', padx=(0, 10))
            ui.Button(rows, text='▶', command=lambda b=b, e=e: player.play(start=b / 1000, end=e / 1000),
                      row=i, column=1, sticky='w')
            ui.Label(rows, text=f"{b / 1000:.3f}–{e / 1000:.3f} s ({(e - b) / 1000:.1f} s)", font='small',
                     row=i, column=2, sticky='w', padx=10)
            name = self._takes.get((b, e)) or self.take_name(f"{b}-{e}")
            CarefulTake(rows, self, name, on_saved=lambda nm, key=(b, e): self._takes.__setitem__(key, nm),
                        row=i, column=3, taken=(b, e) in self._takes,
                        on_removed=lambda key=(b, e): self._takes.pop(key, None))
            s = ui.Button(rows, text=_("Split in two"), font='small',
                          command=lambda i=i: self.splitpiece(phrase, cuts, i), row=i, column=4, padx=(20, 0))
            ui.ToolTip(s, _("Cut this piece at its best place not tried yet"))
            if i < len(cuts):   # every piece but the last: join it with the next
                j = ui.Button(rows, text=_("Join with next"), font='small',
                              command=lambda i=i: self.joinpieces(phrase, cuts, i), row=i, column=5, padx=(5, 0))
                ui.ToolTip(j, _("Make this piece and the next one piece"))
        buttons = ui.Frame(top, row=3, column=0, sticky='w', pady=10)
        ui.Button(buttons, text=_("OK"), command=lambda: self.acceptsplit(phrase, cuts),
                  row=0, column=0, padx=(0, 10))
        if len(options) > 1:
            ui.Button(buttons, text=_("Another way"),
                      command=lambda: self.showsplit(n, attempt + 1), row=0, column=1, padx=(0, 10))
        ui.Button(buttons, text=_("Cancel"), command=lambda: self.showclause(self.index), row=0, column=2)

    def joinnext(self):
        """This clause and the next made one (Text.join_phrases); what is typed in the entry is saved first."""
        self.save()
        phrase, following = self.phrases[self.index], self.phrases[self.index + 1]

        def work():
            if self.text.join_phrases(phrase, following) is None:
                ErrorNotice(_("Couldn’t join these clauses."))
                return False
            self.db.save()
            self.phrases = self.text.phrases()
        self.showclause(self.index, msg=self.joining_msg(self.index), work=work)

    def joinpieces(self, phrase, cuts, i):
        """On the split screen: pieces i and i+1 made one (the cut between them taken out), to see the others
        as they were and accept them, or split the joined one differently after (Kent, 2026-11-23)."""
        self.__dict__.setdefault('_joined_away', set()).add(cuts[i])   # not offered again by splitpiece
        cuts = cuts[:i] + cuts[i + 1:]
        if not cuts:
            self.showclause(self.index)   # nothing left to split
            return
        self.redrawsplit(phrase, cuts)

    def splitpiece(self, phrase, cuts, i):
        """On the split screen: piece i cut in two at its best breakpoint that isn't a cut already nor one
        joined away on this screen — so join two pieces, then split the joined one, and it is cut somewhere
        else; join and split again for the next place (Kent, 2026-11-23)."""
        edges = [phrase.begin_ms] + cuts + [phrase.end_ms]
        b, e = edges[i], edges[i + 1]
        tried = self.__dict__.setdefault('_joined_away', set())
        places = sorted([(score, ms) for ms, score, *_rest in self.clause_breakpoints(phrase)
                         if b + SPLIT_MIN_MS <= ms <= e - SPLIT_MIN_MS and ms not in tried and ms not in cuts],
                        reverse=True)
        if not places:
            ErrorNotice(_("No other place to split this piece."))
            return
        self.redrawsplit(phrase, sorted(cuts + [places[0][1]]))

    def redrawsplit(self, phrase, cuts):
        """The split screen for these cuts, as the person has made them (no other ways offered)."""
        with self.ui.runwindow.waiting(_("Showing the pieces again…"), thenshow=True):
            self.ui.runwindow.resetframe()
            self.buildsplit(phrase, len(cuts) + 1, [cuts], 0)

    def acceptsplit(self, phrase, cuts):
        def work():
            pieces = self.text.split_phrase(phrase, cuts)
            for piece in pieces:
                name = self._takes.get((piece.begin_ms, piece.end_ms))
                if name:
                    piece.set_careful(name)
            self._takes = {}
            self.db.save()
            self.phrases = self.text.phrases()
        self.showclause(self.index, work=work,
                        msg=_("Making clause {k} into {n} clauses: sharing out its words and transcription, "
                              "and saving…").format(k=self.index + 1, n=len(cuts) + 1))

    def buildend(self):
        top = self.ui.runwindow.frame
        done, total = self.text.progress()
        ui.Label(top, text=_("That’s the end of {title} ({done} of {total} clauses transcribed).\n"
                             "Pick another text on the main screen to keep going.").format(
                     title=self.text.title, done=done, total=total),
                 font='read', row=0, column=0, sticky='w')
        ui.Button(top, text=_("Back"), command=lambda: self.showclause(len(self.phrases) - 1),
                  row=1, column=0, sticky='w', pady=10)

    # ---- actions ----------------------------------------------------------------------------------------

    def pick(self, value, models):
        self.var.set(value)
        self.picked = models

    def save(self):
        """Store the clause's transcription (the text's details save as each is committed)."""
        phrase = self.phrases[self.index]
        value = self.var.get().strip()
        if value != phrase.final() or self.picked is not None:
            # A click records which candidate(s) the final value started from, replacing any earlier
            # record; with no click this visit the record stays as it was (none: typed from scratch).
            phrase.set_final(value, chosen=self.picked)
            if self.picked:
                ss = getattr(self.program, 'soundsettings', None)
                if ss is not None:
                    for model in self.picked:
                        ss.tally_asr_repo(model)
                    self.program.settings.storesettingsfile(setting='soundsettings')
        self.db.save()
        self.refreshboard()   # under the clause page: its counts

    def move(self, step):
        if getattr(self, 'index', None) is not None and self.index < len(self.phrases):
            self.save()
        self.showclause(max(0, self.index + step))

    def transcribe_clause(self):
        self.save()
        text = self.text
        TextBulkASR(self.program, text, self.audio, [self.phrases[self.index]],
                    lambda _outcome, _note: self.text is text and self.showclause(self.index)).run()

    def __init__(self, program, **kwargs):
        super().__init__(program=program, **kwargs)
