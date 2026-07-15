# coding=UTF-8
"""Stage-2 bulk ASR (asr_bulk_transcription_design.md).

Sweeps every recorded audio form in the lexicon through the configured models
on a worker thread (model-major, language-major — see
`ASRtoText.transcribe_files_bulk`), then persists the draft candidates onto each
`<analang>-x-audio` form as annotations (ADR 0002), so the stage-3 selector
rebuilds them with no live ASR. Launched from the Advanced menu; Cancel (mid-run)
or Done (after) returns to the task chooser.

Threading contract: the worker does only ASR inference (torch, CPU — no Tk).
Progress messages flow worker -> main via a Queue; the main thread coalesces
them to one UI update per poll (throttled, per the XWayland flush concern) and
does all LIFT mutation + writing itself, after the worker finishes.
"""
import hashlib
import queue
import threading

from frontend import ui
from utilities.i18n import _
from utilities import logsetup
log = logsetup.getlog(__name__)
from utilities.error_handler import notify_error as ErrorNotice


class BulkASR:
    def __init__(self, program):
        self.program = program
        self.cancel = threading.Event()
        self.q = queue.Queue()      # worker -> main progress/status messages
        self.results = None
        self.pairs = []             # [(audiofileURL, form-container node), ...]
        self._md5cache = {}         # audio path -> md5 (compute once, reuse)
        self._persisted = {}        # url -> (n_tx, n_ipa) last written, skip unchanged

    # -- enumeration ---------------------------------------------------------
    def _collect(self):
        """Every recorded audio location: word-form fields and examples across
        all senses. Each entry is (audio file URL, the node carrying the
        <analang>-x-audio form) so we can transcribe the file and persist onto
        its form."""
        pairs = []
        seen = set()  # entry-level fields (lx/lc/pl/imp) appear in EVERY
        # sense's ftypes — without dedup a two-sense entry's citation
        # recording is enumerated (and transcribed) once per sense.
        for sense in self.program.db.senses:
            nodes = list((getattr(sense, 'ftypes', {}) or {}).values())
            nodes += list((getattr(sense, 'examples', {}) or {}).values())
            for node in nodes:
                try:
                    if node.hassoundfile() and node.audiofileURL not in seen:
                        seen.add(node.audiofileURL)
                        pairs.append((node.audiofileURL, node))
                except Exception as e:
                    log.info(f"skipping a node while collecting audio: {e}")
        return pairs

    # -- launch --------------------------------------------------------------
    def run(self):
        try:
            self.program.task.withdraw()   # hide the launching task window
        except (AttributeError, Exception):
            pass
        self.pairs = self._collect()
        if not self.pairs:
            ErrorNotice(_("No recorded audio found to transcribe."), wait=True)
            self.program.taskchooser.gettask()
            return
        if not self._prepare_asr():
            self.program.taskchooser.gettask()
            return
        self._build_window(len(self.pairs))
        threading.Thread(target=self._worker, name='bulk-asr',
                         daemon=True).start()
        self._poll()

    def _prepare_asr(self):
        # Launched from the Advanced menu, possibly before any sound task set up
        # program.soundsettings — SoundSettings.ensure() creates/loads it
        # idempotently (canonical home is program.settings.soundsettings).
        from backend.core.sound import SoundSettings
        ss = SoundSettings.ensure(self.program)
        if not getattr(ss, 'asrOK', True):
            ErrorNotice(_("ASR is not available or not enabled."), wait=True)
            return False
        try:
            ss.load_ASR()
        except Exception as e:
            log.info(f"load_ASR: {e}")
        self.asr = getattr(ss, 'asr', None)
        if self.asr is None:
            ErrorNotice(_("Could not load the ASR model(s)."), wait=True)
            return False
        self.asr.sister_languages = ss.asr_kwargs.get('sister_languages')
        self.asr.show_tone = ss.asr_kwargs.get('show_tone')
        # Sister-language preflight: keep the USABLE set (langs with an MMS
        # adapter) to filter units so the progress denominator is correct.
        # Unsupported codes are logged and skipped quietly — no modal nag.
        self._usable_sisters = None
        try:
            usable, _unusable = self.asr.preflight_sister_languages()
            self._usable_sisters = usable
        except Exception as e:
            log.info(f"sister-language preflight skipped: {e}")
        return True

    # -- progress window -----------------------------------------------------
    def _build_window(self, nfiles):
        self.win = ui.Window(self.program.taskchooser.ui,
                             title=_("Bulk transcription"), exit=False)
        f = self.win.frame
        self.status = ui.Label(f, text=_("Transcribing {n} recordings…").format(
                                   n=nfiles), row=0, column=0, sticky='ew')
        # Level 1 (which model / overall) then Level 2 (files in this model)
        self.unit_label = ui.Label(f, text=_("Preparing…"), row=1, column=0,
                                   sticky='w')
        self.unit_bar = ui.Progressbar(f, row=2, column=0, sticky='ew')
        self.file_label = ui.Label(f, text='', row=3, column=0, sticky='w')
        self.file_bar = ui.Progressbar(f, row=4, column=0, sticky='ew')
        self.button = ui.Button(f, text=_("Cancel"),
                                command=self._request_cancel, row=5, column=0)

    def _request_cancel(self):
        self.cancel.set()
        self.status['text'] = _("Cancelling — finishing the current file…")

    def _update_progress(self, kw):
        unit_idx = kw.get('unit_idx', 0); nunits = kw.get('nunits', 1)
        file_idx = kw.get('file_idx', 0); nfiles = kw.get('nfiles', 1)
        model = kw.get('model', ''); lang = kw.get('lang')
        modeldesc = model + (" — " + lang if lang else '')
        # Level 1 — WHICH model/language, and how many models done. The bar
        # advances within a model too (so it doesn't look frozen during a long
        # single-model sweep), not just when a whole model finishes.
        self.unit_label['text'] = _("Model {i} of {n}:  {model}").format(
            i=unit_idx + 1, n=nunits, model=modeldesc)
        overall = (unit_idx + (file_idx + 1) / max(nfiles, 1)) / max(nunits, 1)
        self.unit_bar.current(overall)
        # Level 2 — files within THIS model
        self.file_label['text'] = _("    recording {i} of {n} (this model)").format(
            i=file_idx + 1, n=nfiles)
        self.file_bar.current((file_idx + 1) / max(nfiles, 1))

    # -- worker + poll -------------------------------------------------------
    def _prior_drafts(self):
        """{url: set of repo keys already drafted for the file's CURRENT md5} —
        lets the sweep skip work already done: adding a model runs only the new
        one, and resume skips finished files. An md5 mismatch (re-recorded) is
        treated as nothing stored — it'll be redone and the stale drafts wiped on
        persist. Read once at worker start, before any persist runs."""
        prior = {}
        audiolang = self.program.params.audiolang()
        for url, node in self.pairs:
            try:
                node.getforms()
                form = node.forms.get(audiolang)
                if form is None:
                    continue
                tx, ipa, _tone, md5 = form.load_drafts()
                if md5 and md5 == self._md5(url):
                    prior[url] = set(tx) | set(ipa)
            except Exception as e:
                log.info(f"prior-drafts read failed for '{url}': {e}")
        return prior

    def _worker(self):
        files = [url for url, _node in self.pairs]
        prior = self._prior_drafts()   # skip (file, model) pairs already done
        keep = None                    # 'top models only' keep-set (None == all)
        ss = getattr(self.program, 'soundsettings', None)
        if ss is not None and hasattr(ss, 'top_asr_keys'):
            keep = ss.top_asr_keys()
        try:
            self.results = self.asr.transcribe_files_bulk(
                files,
                progress_cb=lambda **kw: self.q.put(('progress', kw)),
                should_cancel=self.cancel.is_set,
                checkpoint_cb=lambda snap: self.q.put(('checkpoint', snap)),
                prior=prior, keep_keys=keep,
                usable_langs=getattr(self, '_usable_sisters', None),
                plan_cb=lambda names: self.q.put(('plan', names)),
                unit_done_cb=lambda name: self.q.put(('unit_done', name)))
        except Exception as e:
            log.error(f"bulk ASR worker failed: {e}")
            self.q.put(('error', str(e)))
            return
        self.q.put(('done', None))

    def _track_units(self, todo=None, done=None):
        """Maintain audio.json's top-level asr_in_process {'todo': [...],
        'done': [...]} so the user can see which model/language sweeps this
        bulk run will do and has done. Called on the main thread only."""
        ss = getattr(self.program, 'soundsettings', None)
        if ss is None:
            return
        state = getattr(ss, 'asr_in_process', None)
        if not isinstance(state, dict):
            state = {}
        if todo is not None:            # plan: fresh run replaces old state
            state = {'todo': list(todo), 'done': []}
        if done is not None:            # one unit finished: move it over
            state.setdefault('todo', [])
            state.setdefault('done', [])
            if done in state['todo']:
                state['todo'].remove(done)
            if done not in state['done']:
                state['done'].append(done)
        ss.asr_in_process = state
        try:
            self.program.settings.storesettingsfile(setting='soundsettings')
        except Exception as e:
            log.info(f"couldn't persist asr_in_process: {e}")

    def _poll(self):
        last = None            # coalesce: one UI update per poll (throttle)
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == 'progress':
                    last = payload
                elif kind == 'plan':
                    # audio.json asr_in_process: the pruned unit list this run
                    # WILL do (Kent 2026-07-14: "which models it will do, or
                    # has done"). Main thread — safe to write settings here.
                    self._track_units(todo=payload)
                elif kind == 'unit_done':
                    self._track_units(done=payload)
                elif kind == 'checkpoint':
                    if last:
                        self._update_progress(last); last = None
                    # background-write the work so far, so a power-cut/crash keeps
                    # it; skip if a write is still in flight (next checkpoint or
                    # the final persist catches up) to avoid mutating mid-write.
                    if not getattr(self.program, 'writing', False):
                        n = self._persist(payload)
                        self.status['text'] = _(
                            "Saved drafts for {n} recording(s) so far…").format(n=n)
                elif kind == 'error':
                    if last:
                        self._update_progress(last)
                    self._finish(error=payload)
                    return
                elif kind == 'done':
                    if last:
                        self._update_progress(last)
                    self._persist_and_finish()
                    return
        except queue.Empty:
            pass
        if last:
            self._update_progress(last)
        self.win.after(150, self._poll)

    # -- persistence + finish ------------------------------------------------
    def _persist(self, results):
        """Persist accumulated drafts onto their audio forms and trigger a
        BACKGROUND LIFT write (the in-place maybewrite writer). Idempotent —
        safe to call repeatedly for checkpoints; a resume just fills gaps.
        Returns the count of recordings with drafts written."""
        audiolang = self.program.params.audiolang()
        n = 0        # recordings that have drafts
        wrote = 0    # recordings actually (re)written this call
        for url, node in self.pairs:
            tx, ipa = results.get(url, ({}, {}))
            if not (tx or ipa):
                continue
            n += 1
            key = (len(tx), len(ipa))   # drafts only grow, so a count change == new data
            if self._persisted.get(url) == key:
                continue                # unchanged since last checkpoint — skip
            try:
                node.getforms()   # wrap the audio form so it carries persist_drafts
                form = node.forms.get(audiolang)
                if form is None:
                    continue
                form.persist_drafts(transcriptions=tx, ipa=ipa, tone={},
                                    md5=self._md5(url))
                self._persisted[url] = key
                wrote += 1
            except Exception as e:
                log.error(f"bulk ASR persist failed for '{url}': {e}")
        if wrote:
            self.program.taskchooser.maybewrite(definitely=True)   # background write
        return n

    def _persist_and_finish(self):
        n = self._persist(self.results or {})
        # denominator = recordings actually worked on this run (gap-fill and the
        # top-models filter intentionally skip the rest), not the lexicon total
        attempted = len(getattr(self.asr, '_bulk_touched', set())) or n
        total = len(self.pairs)
        log.info(f"bulk ASR: transcribed {n}/{attempted} this run "
                 f"({total} recordings total)")
        self._finish(persisted=n, attempted=attempted, total=total)

    def _finish(self, error=None, persisted=0, attempted=0, total=0):
        a = attempted or persisted
        if error:
            self.status['text'] = _("Error: {e}").format(e=error)
        elif self.cancel.is_set():
            self.status['text'] = _(
                "Cancelled after {n} of {a} this run ({t} total).").format(
                    n=persisted, a=a, t=total)
        else:
            self.status['text'] = _(
                "Done. Transcribed {n} of {a} this run ({t} recordings total).").format(
                    n=persisted, a=a, t=total)
        self.unit_bar.current(1.0)
        self.file_bar.current(1.0)
        self.button['text'] = _("Return to menu")
        self.button['command'] = self._close

    def _close(self):
        try:
            self.win.destroy()
        except Exception:
            pass
        self.program.taskchooser.gettask()

    def _md5(self, path):
        if path in self._md5cache:            # compute once; reused each checkpoint
            return self._md5cache[path]
        try:
            with open(path, 'rb') as fh:
                m = hashlib.md5(fh.read()).hexdigest()
        except OSError as e:
            log.error(f"Can't md5 audio '{path}': {e}")
            m = None
        self._md5cache[path] = m
        return m
