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
# page width), each as wide as the longest candidate plus padding; past CANDIDATE_MAX_ROWS rows even
# then, the buttons scroll.
CANDIDATE_CHAR_BUDGET = 72
CANDIDATE_PAD_CHARS = 4
CANDIDATE_MAX_ROWS = 6

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

    def __init__(self, program, text, audio, on_done, heading=None):
        self.program = program
        self.text = text
        self.audio = audio
        self.on_done = on_done
        self.heading = heading
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
        work = (snapshot, self.audio, self.text.db.project_dir, self.text.output_path('_words.TextGrid'),
                self.text.output_path('_words.tsv'), adapter, cache_dir)
        self.mms = texts.loaded_mms(self.program)
        self.snapshot = snapshot
        self.total = len(self.text.phrases())
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
                                      should_cancel=self.cancel.is_set, mms=self.mms)
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
    the next. What each step did goes on the board (TranscribeTexts.boardnote) at the end."""

    def __init__(self, task, paths, steps):
        self.task = task
        self.program = task.program
        self.todo = list(paths)
        self.n = len(self.todo)
        self.steps = [s for s in (ASR, WORDS) if s in steps]
        self.notes = []

    def start(self):
        self.task.boardnote = None
        self._next()

    def _next(self):
        self.text = self.audio = None
        if not self.todo:
            self._end()
            return
        path = self.todo.pop(0)
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
            TextFindWords(self.program, self.text, self.audio, self._done, heading).run()

    def _done(self, outcome, note):
        if note:
            self.notes.append(f"{self.text.title}: {note}")
        if outcome == CANCELLED:
            self.todo = []
            self._end()
        elif outcome == FAILED:
            self._next()
        else:
            self._step()

    def _end(self):
        self.text = self.audio = None
        self.task.boardnote = '\n'.join(self.notes) or None
        self.task.refreshboard()


class TranscribeTexts(Sound, Task):
    tasktitle = N_("Transcribe Texts")
    taskicon = 'iconTranscribe'
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
            label = ui.Label(table, text=name, row=row, column=0, sticky='e', padx=5)
            if name != os.path.basename(path):
                ui.ToolTip(label, os.path.basename(path))
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

    def makewindow(self, path=None):
        path = path or getattr(self.program.settings, 'textrecording', None)
        if not path or not os.path.exists(path):
            ErrorNotice(_("Pick a text on the board first."))
            return
        self.program.settings.textrecording = path
        with self.ui.waiting(_("Opening {name}…").format(name=os.path.basename(path))):
            try:
                self.text, self.audio = self.db.open_recording(path)
            except Exception as e:
                log.error(f"couldn't open {path} as a text: {e}")
                ErrorNotice(_("Couldn’t open {name}: {e}").format(name=os.path.basename(path), e=e))
                return
            self.phrases = self.text.phrases()
            if not self.phrases:
                ErrorNotice(_("No speech found in {name}.").format(name=os.path.basename(path)))
                return
            # Resume at the first clause with no transcription.
            self.index = next((i for i, p in enumerate(self.phrases) if not p.final()), 0)
        self.ui.getrunwindow(title=_("Transcribe {title}").format(title=self.text.title))
        self.buildclause()
        self.ui.runwindow.waitdone()
        self.ui.runwindow.deiconify()

    def showclause(self, index):
        self.index = index
        with self.ui.runwindow.waiting(thenshow=True):
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
        ranking reads down each column); a scrolling frame only when even that runs past MAX_ROWS."""
        items = sorted(by_value.items(), key=lambda kv: -len(kv[1]))
        n = len(items)
        widest = max(len(value) for value, _models in items) + CANDIDATE_PAD_CHARS
        fit = max(1, CANDIDATE_CHAR_BUDGET // widest)
        ncols = max(1, min(fit, math.ceil(n / CANDIDATE_MAX_ROWS)))
        nrows = math.ceil(n / ncols)
        if nrows > CANDIDATE_MAX_ROWS:
            frame = ui.ScrollingFrame(parent, row=row, column=column, sticky='w', pady=10).content
        else:
            frame = ui.Frame(parent, row=row, column=column, sticky='w', pady=10)
        for i, (value, models) in enumerate(items):
            b = ui.Button(frame, text=value, font='read',
                          command=lambda v=value, m=models: self.pick(v, m),
                          row=i % nrows, column=i // nrows, sticky='w', padx=(0, 10))
            ui.ToolTip(b, text='\n'.join(models))

    def buildclause(self):
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
        by_value = {}
        for model, value in phrase.candidates().items():
            by_value.setdefault(value, []).append(model)
        if by_value:
            # Each distinct text once, labelled by every model that gave it.
            self.buildcandidates(entryrow, by_value, row=1, column=1)
        else:
            ui.Button(entryrow, text=_("Transcribe this clause"), command=self.transcribe_clause,
                      row=1, column=1, sticky='w', pady=10)

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
