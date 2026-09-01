# coding=UTF-8
from frontend import ui
from tasks.base import Task
from backend.core.report_mixins import Multislice, MultisliceS, MultisliceT, Multicheck, Multicheckslice, ByUF, Background
from backend.reporting.generator import Report
from backend.core.lexicon import WordCollection, Parse, Tone, Segments, Syllables, Vowels, Consonants
from tasks.sound import Sound, Record
import backend.core.sorting_engine #import Sort
from backend.core.categories import Categories
from utilities.utilities import *
from utilities import file, logsetup, rx
from io_put import export
from tasks.alphabet_chart import AlphabetChart
from tasks.alphabet_comparison import AlphabetComparisonPages
from utilities.i18n import _
from random import randint
log = logsetup.getlog(__name__)

from utilities.error_handler import notify_error as ErrorNotice
from frontend.sort_buttons import SortGroupButtonFrame, SortGlyphGroupButtonFrame
from backend.core.alphabet import Alphabet
from io_put import sound
from frontend import sound_ui, transcriber

class ExportData(ui.Window):
    """docstring for ExportData."""
    taskicon = 'USBdrive'
    def tooltip(self):
        return _("This tells you how much data you could export now, and "
                    "allows you to export it.")
    tasktitle = "Export Data"
    def dobuttonkwargs(self):
        text=_("Export Data")
        tttext=_("This tells you how much data you could export now, and "
                    "allows you to export it.")
        return {'text':text,
                # 'fn':pass,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.taskchooser.theme.photo['USBdrive'],
                'sticky':'ew',
                'tttext':tttext
                }
    def on_quit(self):
        ui.Window.on_quit(self)
        self.program.taskchooser.gettask()
    def switch(self,event=None):
        if self.exportclass == export.Lexicon:
            self.exportclass=export.Examples
        else:
            self.exportclass=export.Lexicon
        self.report_data()
    def do_export(self,event=None):
        self.done_notice=ui.Label(self.frame,
                                    text=_("In Progress..."),
                                    anchor='c',padx=50,
                                    row=4,column=0,columnspan=2,sticky='we'
                                )
        for i in self.export.export():
            self.progress(i*100)
        self.progress(100)
        self.done_notice['text']=_("Done!\n(saved to {dir})").format(dir=self.export.save_dir)
    def report_data(self,check=None,event=None):
        if hasattr(self,'button') and isinstance(self.button,dict):
            for i in self.button.values():
                i.destroy()
            del self.button
        for o in ['info','button',
                    'export_button', 'switch_button',
                    'done_notice']:
            try:
                getattr(self,o).destroy()
            except Exception:
                pass
        self.update()
        self.export=self.exportclass(
                lift=self.program.db,
                analang=self.program.params.analang(),
                audiolang=self.program.params.audiolang(),
                audiodir=self.program.settings.audiodir,
                save_dir=self.program.settings.exportsdir,
                check=check,
                max_rows_total=self.max_rows_total,
                max_rows_per_file=self.max_rows_per_file,
                )
        self.info=ui.Label(self.frame,
            text=_("Checking work done..."),
            anchor='c',padx=50,
            row=0,column=0,sticky='we'
        )
        self.button_frame=ui.Frame(self.frame,
                                    row=2,column=0,
                                    )
        self.progress(0,self.frame,row=3,column=0)
        for i in self.export.report():
            self.progress(i*100)
        self.info['text']=self.export.info
        self.export_button=ui.Button(self.button_frame,
                text=_("Export"),
                anchor='c',padx=50,
                row=0,column=1,sticky='we'
        )
        if self.exportclass == export.Lexicon:
            self.switch_button=ui.Button(self.button_frame,
                    text=_("Check Examples"),
                    anchor='c',padx=50,
                    row=0,column=0,sticky='w'
            )
            if self.slices:
                allchecks=self.program.status.allcheckswCVdata()
                self.button={c:ui.Button(self.button_frame,
                                        text=_("Just {check} data").format(check=c),
                                        anchor='c',padx=50,
                                        row=allchecks.index(c)+1,
                                        column=0,sticky='w'
                                        )
                        for c in allchecks
                            }
                for c in self.button:
                    self.button[c].bind("<Button-1>",
                                        lambda event,x=c: self.report_data(x))

        else:
            self.switch_button=ui.Button(self.button_frame,
                    text=_("Check Lexicon"),
                    anchor='c',padx=50,
                    row=0,column=0,sticky='w'
            )
        self.export_button.bind("<Button-1>",self.do_export)
        self.switch_button.bind("<Button-1>",self.switch)
    def __init__(self, program):
        self.program=program
        self.exportclass=export.Lexicon
        title=(_("{azt} Data Export").format(azt=self.program.name))
        ui.Window.__init__(self,self.program.tk_root, title=title)
        self.slices=False #allow user to output data for each check
        self.max_rows_total=None
        self.max_rows_per_file=None
        self.report_data()
class Transcription(object):
    def _configure_transcription(self,event=None):
        sound_ui.ASRModelSelectionWindow(self)
    def setcontext(self):
        super().setcontext()
        self.context.menuitem(_("Transcription settings"),
                                    self._configure_transcription)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.soundsettings.load_ASR() #after file settings are loaded
class WordCollectionwRecordings(WordCollection,Record):
    def getinstructions(self):
        return _("Record a word in your language that goes with these "
                "meanings."
                "\nGive just a single word (not a phrase) wherever possible."
                # "\nClick-Speak-Release on the record button."
                )
    def set_up_transcription(self):
        self.set_transcription_fields()
        self.set_transcription_frame(row=3,column=0,colspan=2) #instructions2
    def set_transcription_fields(self,**kwargs):
        ftype=kwargs.pop('ftype',self.ftype)
        self.transcription_var=ui.StringVar()
        self.transcription_ipa_var=ui.StringVar()
        self.transcription_tone_var=ui.StringVar()
        self.transcription_var.trace_add('write', self.show_drafts)
        self.transcription_ipa_var.trace_add('write', self.store_phonetic)
        self.transcription_tone_var.trace_add('write', self.store_tone)
        if ftype not in self.entry.fields: #Need this to record to
            if ftype == 'lx':
                self.entry.lx=lift.Lexeme(self.entry)
            elif ftype == 'lc':
                self.entry.lx=lift.Citation(self.entry)
            else:
                self.entry.fields[ftype]=lift.Field(self.entry,ftype=ftype)
    def set_transcription_frame(self,**kwargs):
        ftype=kwargs.pop('ftype',self.ftype)
        try:
            self.wordframe.recordFrame.destroy()#don't leave this around!
        except Exception:
            pass
        log.info(f"setting frame with settings: {self.soundsettings}")
        self.wordframe.recordFrame=sound_ui.RecordnTranscribeButtonFrame(
                        self.wordframe,
                        self, #task
                        self.entry.fields[ftype],#node,
                        transcription_var=self.transcription_var,
                        transcription_ipa_var=self.transcription_ipa_var,
                        transcription_tone_var=self.transcription_tone_var,
                        # show_transcriptions=True, #this typically in Entry
                        # show_transcriptions_ipa=True,
                        show_tone=True,
                        shown='none',
                        sticky='ew',
                        **kwargs
                    )
        # Stage-3 display trigger: if this word already has stored ASR drafts
        # (from a bulk run or a prior session) and no live recording drove the
        # display this session, show the draft buttons — deferred so the rest of
        # the word UI (instructions2 etc.) exists first. Read-only: it builds
        # buttons and writes no forms.
        try:
            self.wordframe.recordFrame.after(1, self.maybe_show_stored_drafts)
        except Exception as e:
            log.info(f"couldn't schedule stored-draft display: {e}")
    def maybe_show_stored_drafts(self):
        """Show stored ASR drafts for an already-recorded word WITHOUT re-running
        ASR (the stage-3 decoupled display). No-op if a live recording drove the
        display this session, or there are no stored drafts. show_drafts is
        read-only here: it builds buttons and only fills an EMPTY field."""
        try:
            rf=getattr(self.wordframe,'recordFrame',None)
            if rf is None or getattr(getattr(rf,'recorder',None),
                                     'transcriptions',None):
                return
            if self._draft_transcriptions():
                self.show_drafts()
        except Exception as e:
            log.info(f"maybe_show_stored_drafts skipped: {e}")
    def _draft_transcriptions(self):
        """Transcription-lane draft candidates {repo: text} for the selector.
        Sources from the STORED ASR annotations (ADR 0002) — the stage-3
        contract, identical whether a bulk run or the live path produced them.
        Falls back to the live recorder's in-memory candidates only if nothing
        is stored yet (e.g. ASR just ran but persist hasn't landed)."""
        rf=getattr(self.wordframe,'recordFrame',None)
        node=getattr(rf,'node',None)
        tx={}
        if node is not None and node.isnode():
            audiolang=self.program.params.audiolang()
            node.getforms()
            form=node.forms.get(audiolang)
            if form is not None:
                tx=form.load_drafts()[0] or {}
        if not tx:
            tx=getattr(getattr(rf,'recorder',None),'transcriptions',None) or {}
        # Buttons show diacritic-free forms (models emit tone marks we
        # don't want at collection); the LIFT-stored drafts keep them.
        # Normalizing HERE — before dedup/consensus/cap — also means a
        # click credits every model whose raw draft collapses to the
        # chosen form (draft_entry tallies all repos behind the value).
        from utilities.encodings import strip_diacritics
        tx={r:strip_diacritics(v) for r,v in tx.items()}
        # 'top models only' (B): show only the kept repos (None == no limit)
        ss=getattr(self,'soundsettings',None) or getattr(self.program,
                                                         'soundsettings',None)
        return self._filter_top_asr(tx,ss)
    @staticmethod
    def _enabled_drafts(tx,ss):
        """The kwarg-selection level of the draft-display funnel: the user's
        enabled models AND selected sister languages (a macrolanguage counts
        for its members) govern display as well as inference. Fails open
        wherever the selection can't be read (backend.asr unimportable,
        nothing enabled): show rather than hide."""
        try:
            # already imported in any sound-capable session; the mapping and
            # language helpers are module-level so this filter works BEFORE
            # any model loads (the stored drafts display without ASR running).
            from backend import asr
        except Exception as e:
            log.info(f"draft display filter unavailable (no backend.asr): {e}")
            return tx
        kwargs=getattr(ss,'asr_kwargs',None) or {}
        repo_map=(getattr(getattr(ss,'asr',None),'repo_modelnames',None)
                    or asr.REPO_MODELNAMES)
        # return_ipa/show_tone are output-LANE flags that alias a repo in
        # the map (neurlang/katyayego) — return_ipa is even forced True with
        # no checkbox — so they must not resurrect a deselected model's
        # transcription drafts here.
        enabled={v for k,v in repo_map.items()
                 if kwargs.get(k) and k not in ('return_ipa','show_tone')}
        if enabled: #none enabled would hide everything; fail open instead
            # Stored keys carry language decorations, e.g.
            # 'facebook/mms-1b-all (swh!)': match on the repo-name prefix,
            # but never repo-vs-repo (whisper-large isn't -large-v3).
            tx={r:v for r,v in tx.items()
                if any(r == e or r.startswith(e+' ') for e in enabled)}
        allowed=set()
        for code in kwargs.get('sister_languages') or ():
            for c in [code]+asr.sister_members(code):
                allowed.update((c,asr.mms_lang(c))) #raw + alpha3
        allowed.discard(None)
        if allowed:
            import re
            def lang_ok(r):
                # '(xxx!)' marks a language-DIRECTED run ('aaa!=bbb!' a
                # requested/actual pair): hide it when no side is selected.
                # Bare keys and '(xxx?)' (detected, not directed) pass on
                # the model alone.
                m=re.search(r'\(([^)]*!)\)$',r)
                return (not m or
                        bool(set(re.findall(r'[A-Za-z]+',m.group(1)))&allowed))
            tx={r:v for r,v in tx.items() if lang_ok(r)}
        return tx
    MAX_DRAFT_BUTTONS=20 #more pushes everything else off the page
    @staticmethod
    def _cap_draft_forms(tx,ss,maxforms=None):
        """'Top models only' also promises a page that fits: never more
        than MAX_DRAFT_BUTTONS distinct forms (== buttons). Forms from
        the highest-tallied repos are kept first; ties — beyond the top
        ranks every tally is 1/0, so most forms tie — fill the remaining
        slots at random. ('All models' never comes here: the user asked
        to see everything, whatever it does to the page.)"""
        if maxforms is None:
            maxforms=WordCollectionwRecordings.MAX_DRAFT_BUTTONS
        values={v for v in tx.values() if v}
        if len(values) <= maxforms:
            return tx
        tally=getattr(ss,'asr_repos',{}) or {}
        def besttally(v):
            return max((tally.get(r,0) or 0)
                        for r,val in tx.items() if val==v)
        import random
        ranked=sorted(values,key=lambda v:(-besttally(v),random.random()))
        chosen=set(ranked[:maxforms])
        log.info(f"draft-form cap: {len(values)} unique forms -> "
                 f"{maxforms} (top models only)")
        #empty-valued repos pass through (they make no buttons anyway):
        return {r:v for r,v in tx.items() if not v or v in chosen}
    @staticmethod
    def _filter_top_asr(tx,ss):
        """The draft-display funnel: everything stored → the user's kwarg
        selection (models + sister languages: _enabled_drafts) → the 'top
        models only' boolean. The last step only ever selects WITHIN the
        kwarg selection, and never so hard that the selector collapses: a
        unanimous top-5 leaves one form (one button), which looks broken.
        Widen n by 5 per iteration until at least two distinct forms survive;
        once widening stops adding repos — or the selected draft set is
        unanimous anyway — return every selected draft rather than hide what
        ASR produced. In the other direction, 'top models only' also caps
        the distinct forms shown at MAX_DRAFT_BUTTONS (_cap_draft_forms);
        with the toggle off, everything shows, uncapped."""
        if ss is None:
            return tx
        tx=WordCollectionwRecordings._enabled_drafts(tx,ss)
        def distinct(d):
            return len({v for v in d.values() if v})
        def cap(d):
            return WordCollectionwRecordings._cap_draft_forms(d,ss)
        keep=ss.top_asr_keys()
        if keep is None:
            #toggle off (no cap), or toggle on with nothing tallied yet
            #(run everything, but still keep the page intact):
            return cap(tx) if ss.top_models_only() else tx
        if distinct(tx) < 2:
            return tx #widening can't help (and ≤1 form needs no cap)
        n=5
        while True:
            kept={r:v for r,v in tx.items() if r in keep}
            if distinct(kept) >= 2:
                return cap(kept)
            n+=5
            wider=ss.top_asr_keys(n=n,cap=max(20,n))
            if wider == keep: #tally exhausted (untallied repos never rank)
                return cap(tx)
            keep=wider
    def show_drafts(self,*args):
        # log.info(f"show_drafts got args {args}")
        instructions2=(_("click on the best option(s) above"),
                        _("correct the consonants and vowels below."))
        try:
            self.wordframe.draftFrame.destroy()
        except Exception:
            pass
        drafts=self._draft_transcriptions()
        # Dedup by VALUE, retaining value -> [repos]: many models/languages emit
        # the same string, and consensus is the signal we surface.
        byvalue={}
        for repo,text in drafts.items():
            if text:
                byvalue.setdefault(text,[]).append(repo)
        log.info(f"show_drafts: {len(drafts)} draft(s) {sorted(drafts)} "
                 f"-> {len(byvalue)} unique value(s)")
        if not byvalue:
            return #no drafts: no buttons, and no 'click above' instructions
        if len(byvalue) == 1 and not self.var.get():
            self.var.set(next(iter(byvalue)))  # auto-fill an EMPTY field; never overwrite
        # A single (unanimous) form still gets its button: it is how the user
        # sees what ASR produced — and reverts to it — when the visible form
        # differs (hand edit, earlier mistake, etc).
        c,r=self.wordframe.recordFrame.grid_size()
        self.wordframe.draftFrame=ui.Frame(self.wordframe.recordFrame,
                                            column=c,
                                            row=0
                                        )
        self.wordframe.toneFrame=ui.Label(self.wordframe.recordFrame,
                                            column=c,
                                            row=1
                                        )
        # Most-frequent (consensus) first: the value the most models produced on
        # top. Supersedes the old length-sort, since dedup removes the clutter.
        ordered=sorted(byvalue.items(),key=lambda kv: len(kv[1]),reverse=True)
        aspect=3/4 #float OK
        nrows=max(3,int((len(ordered)*aspect)**.5))
        max_len=20 #don't want words kicking buttons off the page...
        for i,(value,repos) in enumerate(ordered):
            ui.Button(self.wordframe.draftFrame,
                text=value[:max_len],
                command=lambda v=value,rs=repos:self.draft_entry(rs,v),
                column=i//nrows,
                row=i%nrows,
            )
        if hasattr(self,'instructions2'):
            self.instructions2['text']='\n'.join(instructions2)
        if self.transcription_tone_var.get():
            self.wordframe.toneFrame['text']=self.transcription_tone_var.get()
        else:
            self.wordframe.toneFrame['text']=''
    def draft_entry(self,repos,value,*args):
        # Fills the visible field (may be overwritten on confirmation later).
        # Called on a button click (a user choice), so credit EVERY repo behind
        # the chosen value — after dedup the tally must stay honest, not credit
        # just one of several models that agreed.
        if isinstance(repos,str): #tolerate a single-repo caller
            repos=[repos]
        for repo in repos:
            self.program.soundsettings.tally_asr_repo(repo)
        self.var.set(value)
        self.update_idletasks()
        self.program.settings.storesettingsfile(setting='soundsettings')
        log.info(self.program.soundsettings.asr_repo_tally())
    def store_phonetic(self,*args):
        #Need to fix this; format isn't correct
        self.entry.fieldvalue(self.ftype,
                        self.program.db.phoneticlangname(machine=True),
                        value=self.transcription_ipa_var.get().split('\n')[0]
                        )
    def store_tone(self,*args):
        self.entry.fieldvalue(self.ftype,
                        self.program.db.tonelangname(machine=True),
                        value=self.transcription_tone_var.get()
                        )
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Record.__init__(self,**kwargs)
        # WordCollection.__init__(self,**kwargs)
class WordCollectionLexeme(WordCollection,Task):
    def tooltip(self):
        return _("Don’t use this task.")
    tasktitle = "Word Collection for Lexeme Forms"
    def __init__(self, program, **kwargs): #frame, filename=None
        """This should never really be used, though I made it first, so I've
        left it"""
        self.ftype=program.params.ftype('lx') #lift.Entry.citationformnodeofentry
        super().__init__(program=program, **kwargs)
        log.info("Initializing {}".format(_(self.tasktitle)))
        #Status frame is 0,0
        self.getwords()
class WordCollectionCitation(WordCollection,Task):
    def tooltip(self):
        return _("This task helps you collect words in citation form.")
    tasktitle = "Add Words" # for Citation Forms
    def __init__(self, program, **kwargs): #frame, filename=None
        self.ftype=program.params.ftype('lc') #lift.Entry.citationformnodeofentry
        super().__init__(program=program, **kwargs)
        log.info("Initializing {}".format(_(self.tasktitle)))
        #Status frame is 0,0
        self.getwords()
class WordCollectionCitationwRecordings(WordCollectionwRecordings,Task):
    def tooltip(self):
        return _("This task helps you collect words in citation form through "
                "recordings with automatic transcription drafts.")
    tasktitle = "Add Words with Audio" # for Citation Forms
    def __init__(self, **kwargs): #frame, filename=None
        super().__init__(**kwargs)
        log.info("Initializing {}".format(_(self.tasktitle)))
        self.getwords()
class _WordCollectionSecondForm(WordCollection,Task):
    """Base for word collection tasks that require a second form field."""
    ftype_code = None  # override in subclasses
    form_label = None  # override in subclasses
    def __init__(self, program, **kwargs):
        self.ftype=program.params.ftype(self.ftype_code)
        super().__init__(program=program, **kwargs)
        if not self.program.settings.secondformfieldsOK():
            ErrorNotice(_("To collect {form} forms, you must first "
                            "define which fields should contain those forms"
                            ).format(form=self.form_label),
                            wait=True)
            self.shutdowntask()
            return
        log.info("Initializing {}".format(_(self.tasktitle)))
        self.getwords()
class WordCollectionPlural(_WordCollectionSecondForm):
    def tooltip(self):
        return _("This task helps you collect plural word forms.")
    tasktitle = "Add plural forms"
    ftype_code = 'pl'
    form_label = "Plural"
class WordCollectionImperative(_WordCollectionSecondForm):
    def tooltip(self):
        return _("This task helps you collect imperative word forms.")
    tasktitle = "Add imperative forms"
    ftype_code = 'imp'
    form_label = "Imperative"
class ParseWords(Parse,Task):
    taskicon = 'iconWord'
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "automatically and with confirmation.")
    def run_getparses(self):
        msg=_("Parsing (ask: {ask} auto: {auto})").format(
            ask=self.parser.ask, auto=self.parser.auto)
        self.ui.wait_and_drive_work(msg, self.getparses())
    def dobuttonkwargs(self):
        fn=self.run_getparses
        text=_("Parse!")
        tttext=_("{azt} tries to do as much as possible automatically, and "
                "according to the level you have set for confirmation."
                ).format(azt=self.program.name)
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    tasktitle = "Parse Words"
    def __init__(self, program, **kwargs): #frame, filename=None
        log.info("Initializing {}".format(_(self.tasktitle)))
        super().__init__(program=program, **kwargs)
        # self.checkeach=True #confirm each word
class WordCollectnParse(Parse,WordCollection,Task):
    """This task collects words, from the SIL CAWL, or one by one.
    First in citation form, then pl or imperativewith Parse"""
    taskicon = 'iconWord'
    def tooltip(self):
        return _("This task helps you collect and parse words.")
    def dobuttonkwargs(self):
        if self.program.taskchooser.cawlmissing:
            fn=self.run_addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren’t already in your database "
                    "(you are missing {count} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(count=len(self.program.taskchooser.cawlmissing))
        else:
            text=_("Add a Word")#?
            fn=self.addmorpheme#?
            tttext=_("This adds any word, but is best used after filling out a "
                    "wordlist, if the word you want to add isn’t there "
                    "already.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['Word'],
                'sticky':'ew',
                'tttext':tttext
                }
    tasktitle = "Add and Parse Words" # for Citation Forms
    def __init__(self, program, **kwargs):
        log.info("Initializing {}".format(_(self.tasktitle)))
        self.ftype=program.params.ftype('lc') #always correct?
        # self.nodetag='citation'
        super().__init__(program=program, **kwargs)
        self.program.taskchooser.withdraw()
        fn=self.getwords()#?
class WordCollectnParsewRecordings(Parse,WordCollectionwRecordings,Task):
    """This task collects words, from the SIL CAWL, or one by one.
    First in citation form, then pl or imperativewith Parse"""
    taskicon = 'iconWordRec'
    def tooltip(self):
        return _("This task helps you collect and parse words by recording "
                "them, with an automatic draft.")
    def dobuttonkwargs(self):
        if self.program.taskchooser.cawlmissing:
            fn=self.run_addCAWLentries
            text=_("Add remaining CAWL entries")
            tttext=_("This will add entries from the Comparative African "
                    "Wordlist (CAWL) which aren’t already in your database "
                    "(you are missing {} CAWL tags). If the appropriate "
                    "glosses are found in your database, CAWL tags will be "
                    "merged with those entries."
                    "\nDepending on the number of entries, this may take "
                    "awhile.").format(count=len(self.program.taskchooser.cawlmissing))
        else:
            text=_("Add a Word")#?
            fn=self.addmorpheme#?
            tttext=_("This adds any word, but is best used after filling out a "
                    "wordlist, if the word you want to add isn’t there "
                    "already.")
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['WordRec'],
                'sticky':'ew',
                'tttext':tttext
                }
    tasktitle = "Add and Parse Words with Audio" # for Citation Forms
    def __init__(self, **kwargs):
        log.info("Initializing {}".format(_(self.tasktitle)))
        super().__init__(**kwargs)
        self.program.taskchooser.withdraw()
        fn=self.getwords()
class WordsParse(Parse,WordCollection,Task):
    taskicon = 'iconWord'
    def tooltip(self):
        return _("This task helps you parse words you collected earlier.")
    tasktitle = "Parse Already Collected Words" # for Citation Forms
    def dobuttonkwargs(self):
        pass
    def __init__(self, program, **kwargs):
        log.info("Initializing {}".format(_(self.tasktitle)))
        self.ftype=program.params.ftype('lc') #always correct?
        # self.nodetag='citation'
        super().__init__(program=program, **kwargs)
        # if not self.program.settings.secondformfieldsOK():
        #     ErrorNotice(_("To parse, you must first define which fields "
        #                     "should contain secondary forms"),
        #                     wait=True)
        #     self.shutdowntask()
        #     return
        self.dodone=True #give me words with citation done
        self.checkeach=True #confirm each word (not default)
        self.dodoneonly=True #don't give me other words
        self.userresponse=Object()
        self.program.taskchooser.withdraw()
        #This should either be adapted to use parse or not by keyword, or have
        # another method for addnParse
        # if me:
        #     self.downloadallCAWLimages()
        fn=self.getwords()#?
class ParseSlice(Parse):
    """This task is likely obsolete"""
    tasktitle = "Parse One Slice"
    byslice=True #give me words in a selected slice (make this selectable?)
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "for one slice(?PS??!?) of the dictionary at a time.")
    def __init__(self, **kwargs): #frame, filename=None
        super().__init__(**kwargs)
        # parse-only task: only already-collected words (Parse.__init__ no
        # longer sets these globally; collection variants take the full list)
        self.dodone=True
        self.dodoneonly=True
class ParseSliceWords(ParseSlice):
    """This task is likely obsolete"""
    tasktitle = "Parse One Slice, word by word"
    checkeach=True #confirm each word
    def tooltip(self):
        return _("This task will help you parse your citation forms, "
                "for one slice of the dictionary at a time.")
    def __init__(self, **kwargs): #frame, filename=None
        super().__init__(**kwargs)
class Placeholder(Task):
    """Fake check, placeholder for now."""
    taskicon = 'icon'
    def tooltip(self):
        return _("Tooltip here.")
    def dobuttonkwargs(self):
        fn=self.addCAWLentries
        text=_("Add remaining CAWL entries")
        tttext=_("This will add entries from the Comparative African "
                "Wordlist (CAWL) which aren’t already in your database "
                "(you are missing {} CAWL tags). If the appropriate "
                "glosses are found in your database, CAWL tags will be "
                "merged with those entries."
                "\nDepending on the number of entries, this may take "
                "awhile.").format(count=len(self.program.taskchooser.cawlmissing))
        return {'text':text,
                'fn':fn,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['icon'],
                'sticky':'ew',
                'tttext':tttext
                }
    tasktitle = "Placeholder Check2"
    def __init__(self, program, **kwargs): #frame, filename=None
        super().__init__(program=program, **kwargs)
        log.info("Initializing {}".format(_(self.tasktitle)))
        for r in range(5):
            ui.Label(self.frame,
                    text=_("This is a check placeholder."),
                    row=r, column=0)
class ToneFrameDrafter(ui.Window):
    def addback(self,lang,event=None):
        self.forms[lang]={
                        'before':'',
                        'after':''
                        }
        self.status()
    def skiplang(self,lang,event=None):
        del self.forms[lang]
        self.status()
    def analangftypecode(self):
        return '_'.join([self.analang,self.forms['field']])
    def stripftypecode(self,x):
        return x.removesuffix('_'+self.forms['field'])
    def status(self):
        if self.exitFlag.istrue(): #this IS the window; no .ui here
            return
        try:
            self.fds.destroy()
            self.exf.destroy()
        except AttributeError:
            # log.info("First status frame, or no example yet ({}).".format(e))
            pass
        self.fds=ui.Frame(self.content,row=1,column=0)
        # The button/entry pairs editable() registers, keyed by field. Reset
        # here because the rebuild just destroyed every widget they point at;
        # any edit in flight goes with them, which is the right outcome — a
        # rebuild only happens when the page's shape changed under the edit.
        self.fields={}
        self.active=None
        if 'field' not in self.forms:
            d=self.program.params.ftype()
            log.info("Didn't find field type; setting current ({}).".format(d))
            self.forms['field']=d
        # STRAIGHT TO THE FULL PAGE (Kent 2026-08-31). This used to open a modal
        # child window demanding a name before it would show anything — so the
        # user had to name a thing before seeing what it was, and abandoning the
        # prompt quit the whole drafter. Two rules were collapsed into one: "may
        # not proceed without a name" (wrong) and "may not FINISH without a
        # name" (right). Only the second survives, and it was ALREADY enforced
        # in the right place: exemplified() refuses an empty name, and submit()
        # is reachable only from there. So the gate did not move — the up-front
        # copy of it was simply deleted. An abandoned page still stores nothing,
        # because nothing is written until submit().
        self.forms.setdefault('name','')
        # log.info("Found name")
        # log.info("Starting status with self.form: {}".format(self.forms))
        nametext=_("Frame name:")
        relief='raised' #flat, raised, sunken, groove, and ridge
        frameparams=ui.Frame(self.fds,columnspan=4,column=0,row=0,pady=50,
                            # sticky='w': this row holds two controls that swap
                            # for wider editors. Centred, every swap re-centred
                            # the whole row — the label slid sideways and the
                            # far control was pushed out of the scroll frame.
                            # Anchored left, an editor grows rightward into
                            # empty space and nothing else moves.
                            sticky='w',
                            # highlightthickness=5,
                            # highlightbackground=self.theme.activebackground
                            )
        nameframe=ui.Frame(frameparams,columnspan=2,column=0,row=0,padx=50)
        namelabel=ui.Label(nameframe,text=nametext,column=0,row=0)
        self.editable(nameframe,('name',None),
                    placeholder=_("Give a frame name!"),
                    tooltip=_("Set the frame name for status table and reports"),
                    column=1,row=0)
        fieldname=_("Field to frame:")
        ftypeframe=ui.Frame(frameparams,column=2,row=0)
        ftypelabel=ui.Label(ftypeframe,text=fieldname,column=0,row=0)
        self.editable(ftypeframe,('field',None),
                    tooltip=_("Which dictionary field this frame applies to"),
                    column=1,row=0)
        ui.ToolTip(ftypelabel)
        self.forms['field']
        #order glosslangs first, then other options:
        self.langs=[self.analangftypecode()]+self.program.settings.glosslangs+[
                                    l for l in self.program.db.glosslangs
                                    if l not in self.program.settings.glosslangs]
        for l in [self.analangftypecode()]+self.program.settings.glosslangs: #actually selected
            try:
                self.forms[l]['after']=self.forms[l].get('after','')
            except KeyError: #i.e., if no l in self.forms
                self.forms[l]={'after':''}
            self.forms[l]['before']=self.forms[l].get('before','')
        # log.info("Langs done: {}".format(langs))
        # log.info("self.langs: {}".format(self.langs))
        # log.info("Langs in process: {}".format(langsbeforeonly))
        # log.info("Langs langstodo: {}".format(langstodo))
        nothing='______'
        for n,l in enumerate(self.langs):
            langname=self.program.settings.languagenames[self.stripftypecode(l)]
            if l in self.forms:
                log.info("Working on {}".format(langname))
                if l == self.stripftypecode(l): #no change means gloss
                    tintro=_("Gloss in {lang}:").format(lang=langname)
                    if l in self.program.settings.glosslangs:
                        ltttext=_("current gloss language")
                    else:
                        ltttext=_("additional gloss language")
                        b=ui.Button(self.fds,text='X',
                                    cmd=lambda l=l:self.skiplang(l),
                                    column=0,row=n+1,sticky='e')
                        b.tt=ui.ToolTip(b, _("Skip {lang}").format(lang=langname))
                else:
                    tintro=_("{lang}:").format(lang=langname)
                    ltttext=_("analysis language")
                li=ui.Label(self.fds,text=tintro,column=1,row=n+1)
                li.tt=ui.ToolTip(li, ltttext)
                lineframe=ui.Frame(self.fds,column=2,row=n+1)
                if 'Language ' in langname:
                    tword=_("<word>")
                else:
                    tword=_("<{lang} word>").format(lang=langname)
                # editable() reads the value itself and falls back to the
                # placeholder, so the old try/except-per-slot text juggling is
                # gone; all these two lines still owe is that the key exists.
                self.forms[l].setdefault('before','')
                self.editable(lineframe,(l,'before'),placeholder=nothing,
                                tooltip=self.promptstrings(l,'before')['prompt'],
                                column=1,row=0,padx=0,ipadx=0)
                ui.Label(lineframe,text=tword,column=2,row=0,padx=0,ipadx=0)
                self.forms[l].setdefault('after','')
                self.editable(lineframe,(l,'after'),placeholder=nothing,
                                tooltip=self.promptstrings(l,'after')['prompt'],
                                column=3,row=0,padx=0,ipadx=0)
            else:
                text=_("Add {lang} gloss").format(lang=langname)
                button=ui.Button(self.fds,text=text,
                                relief=relief,
                                font='small',
                                cmd=lambda l=l: self.addback(l),
                                columnspan=2,column=0,row=n+1,padx=0,ipadx=0)
                ui.ToolTip(button,_("Add {lang} values for this frame").format(
                                    lang=langname
                                    ))
        text=_("Get Example")
        exemplify=ui.Button(self.fds,text=text,cmd=self.exemplified,
                            columnspan=2,column=0,row=n+2)
        exemplify.update_idletasks()
        self.scroll.reflow()  # grow canvas to cover the rebuilt status frame
        # `self.parent.withdraw()` used to run here, on EVERY rebuild. Dropped:
        # Tone.addframe is the only thing that builds a drafter and it already
        # withdrew the task window before constructing one, so this was a no-op
        # with a side effect — a withdraw firing on every keystroke-commit, in a
        # page whose whole problem was withdraws changing what is on screen.
    def _value(self,key):
        """Current value behind an editable key. Keys are ('name',None),
        ('field',None) and (lang,'before'|'after') — one flat vocabulary, so the
        active-field bookkeeping never has to care which kind it is holding."""
        lang,context=key
        if lang in ('name','field'):
            return self.forms.get(lang,'')
        return self.forms.get(lang,{}).get(context,'')
    def _store(self,key,value):
        lang,context=key
        if lang in ('name','field'):
            self.forms[lang]=value
        else:
            self.forms.setdefault(lang,{})[context]=value
    STRUCTURAL={('field',None)}
    """Keys whose commit changes the SHAPE of the page, not just a value.

    Only the field type qualifies: analangftypecode() is `analang_<field>`, so
    changing it re-keys every analysis-language row in self.forms and self.langs.
    Everything else is one button's text, and rebuilding for that would throw
    away the widgets the user is looking at to change a label."""
    def _drop_examples(self):
        """Examples illustrate the frame AS DEFINED, so any change to the
        definition invalidates them — examples that outlive their frame are
        worse than none (Kent 2026-08-31). status() does this as part of its
        rebuild; an in-place commit has to do it deliberately, and this is the
        one line that was ever the rebuild's real job on a text edit."""
        if hasattr(self,'exf'):
            try:
                self.exf.destroy()
            except Exception:
                pass
            del self.exf
    def _reflow(self,tobottom=False):
        """Re-measure AFTER the event loop has applied the widget swap.

        tobottom=True also scrolls the new content into view — for 'Get
        Example', whose output is built BELOW the fold, so without it the click
        produced no visible change at all and read as a dead button (Kent
        2026-09-01).

        Called inline this measured the OLD geometry: the entry gridded a
        moment earlier had not been mapped yet, so the row kept the width of
        the button it replaced and the page only straightened itself out once
        the user typed and some later event forced a relayout (Kent 2026-08-31:
        "fixed after typing, but not before. same for other row issue"). Same
        family as the three boards that built content into a ScrollingFrame and
        never reflowed — measuring before the thing is mapped.

        Scheduled with after_idle and a viewability retry, copying
        TaskDressing._reflow_board_soon — the shape this codebase already
        settled on for exactly this hazard. after_idle (not after(1)) because
        grid() queues the requested-size recompute as an IDLE task: a 1 ms
        timer can fire before that idle work has run, which is a re-measure of
        the same stale geometry the inline call saw. Do NOT reach for
        update_idletasks here — reflow() does its own platform-scoped flush,
        and a bare one write-deadlocks XWayland."""
        def go(n=10):
            try:
                if self.exitFlag.istrue() or not self.scroll.winfo_exists():
                    return
                if not self.scroll.winfo_toplevel().winfo_viewable():
                    if n>0:
                        self.after(50,lambda:go(n-1))
                    else:
                        log.info("TFDP reflow skipped: window never mapped")
                    return
                self.scroll.reflow()
                if tobottom:
                    # AFTER the reflow, which is what sets the scrollregion —
                    # scrolling to a bottom the canvas doesn't know about yet
                    # goes nowhere.
                    self.scroll.tobottom()
            except Exception as e:
                log.info("TFDP reflow failed: %s",e)
        try:
            self.after_idle(go)
        except Exception as e:
            log.info("TFDP: could not schedule reflow: %s",e)
    def _close_active(self):
        pair=self.fields.get(self.active)
        self.active=None
        if pair is None:
            return
        try:
            pair['entry'].grid_remove()
            pair['button'].grid()
        except Exception:
            pass #the widgets went away under us; a rebuild will restore them
    def edit(self,key):
        """Make one field active: swap its button for its entry, in place.

        ONE AT A TIME is enforced here rather than by convention — opening a
        field closes whatever was open, so there is no state in which two edits
        are live and no question about which one a Return belongs to."""
        if key not in self.fields:
            return
        self._close_active()
        self.active=key
        pair=self.fields[key]
        pair['button'].grid_remove()
        pair['entry'].grid()
        combo=pair.get('combo')
        if combo is not None:
            # Re-derive from the stored code, same rule as the entry fields
            # below: what the control shows must describe the definition, not
            # whatever it held when it was last closed.
            pair['var'].set(self.fieldtypename())
        field=pair.get('field')
        if field is not None:
            # Start from the STORED value each time, not from whatever the entry
            # held when it was last abandoned: the widget outlives the edit now,
            # so a var left over from an escaped edit would silently reappear as
            # if it were the saved value. The BOX is re-derived from the stored
            # form for the same reason and by the same rule as at build time —
            # the definition so far is what it must describe, never a leftover
            # from an edit the user walked away from.
            pair['var'].set(self._value(key))
            if pair.get('wordbreak') is not None:
                pair['wordbreak'].set(self._wordbreak(key))
            # Size the field to its content, as the alphabet page does
            # (`edit_title`: width = len(value)+5). A default-width Entry is far
            # wider than the button it replaces, so opening one grew the row and
            # RE-CENTRED it — the label slid left and the field-type control was
            # pushed off the side of the scroll frame (Kent 2026-08-31, with a
            # screenshot).
            #
            # The bounds differ by KIND, because the two kinds hold different
            # things. A frame name is a phrase and gets room. A before/after
            # fragment is a word or two ('a', 'un', 'the') sitting INLINE
            # between the label and the <word> marker, so every character of
            # width shoves the rest of the row rightward — at the name's floor
            # of 12 it pushed the 'after' button off the edge of the scroll
            # frame (Kent, second screenshot). Narrow is not a cosmetic
            # preference here; it is what keeps the rest of the row reachable.
            floor,ceiling=(12,40) if key[1] is None else (5,16)
            try:
                field['width']=min(max(len(self._value(key))+2,floor),ceiling)
            except Exception:
                pass #width is cosmetic; never lose the edit over it
            # Focus immediately. The alphabet page records this same gap twice
            # (edit_title, edit_copyright): without it the entry appears but
            # takes no keyboard focus, so the first keystrokes go nowhere.
            field.focus_set()
            field.icursor('end')
        # An entry is taller and wider than the button it replaced, and a
        # ScrollingFrame's canvas is not sized to its content until reflow()
        # runs — the defect that made three boards look empty (fixed 08-28).
        # Swapping widgets in a scroll frame without reflowing is the same bug.
        self._reflow()
    def commit(self,key=None,value=None):
        """Take the value — or, with no key, abandon the edit.

        Committing is the ONLY thing that writes, which is what makes Escape
        safe to offer: a field the user walks away from changes nothing."""
        # Compose BEFORE closing the edit: _compose reads the checkbox, and
        # _close_active is where the entry (and its box) goes back into hiding.
        if key is not None:
            value=self._compose(key,value)
        self._close_active()
        if key is None:
            return
        self._store(key,value)
        if key in self.STRUCTURAL:
            self.status() #re-keys the language rows; also drops the examples
            return
        pair=self.fields.get(key)
        if pair is not None:
            pair['button']['text']=self._display(key)
        self._drop_examples()
        self._reflow()
    WORDBREAK_MARK='·'
    """How a word break is SHOWN on a button (display only; never stored).

    A trailing space and no trailing space look identical, which is the whole
    complaint. U+00B7 rather than U+2423 (␣, the conventional symbol): this text
    is drawn in the analysis font, and a missing glyph would render as tofu —
    strictly worse than the invisible space it is meant to expose. U+00B7 is
    Latin-1 and present in every font this app can be asked to use."""
    def _wordbreak(self,key):
        """Does the STORED value carry a space at the word boundary? The stored
        form is the authority — the checkbox is initialised from this, not the
        other way round, so what the page shows always describes what is on
        disk (see [[cvprofile is data, not analysis]]: same rule, other data)."""
        lang,context=key
        value=self._value(key)
        if context=='before':
            return value.endswith(' ')
        if context=='after':
            return value.startswith(' ')
        return False
    def _compose(self,key,text):
        """Build the value the frame will actually use, from the text the user
        typed PLUS the word-break box.

        Kent's rule (2026-08-31), and the substance of the whole item: the form
        is separated from the neighbouring word by a space IF AND ONLY IF the
        box is checked, WHATEVER the user typed. So the box is the authority and
        the typed text cannot smuggle a boundary space past it — an invisible
        character stops being something you acquire by accident and becomes an
        explicit, single-valued decision.

        Only the boundary edge is touched: 'before' abuts the word on its RIGHT
        ('before'+'__'+'after'), 'after' on its LEFT. Whitespace at the far edge
        is left alone — it is not what the box is about, and silently trimming
        it would be an edit nobody asked for."""
        lang,context=key
        pair=self.fields.get(key) or {}
        box=pair.get('wordbreak')
        if box is None or context not in ('before','after'):
            return text
        if context=='before':
            text=text.rstrip()
            return text+' ' if box.get() else text
        text=text.lstrip()
        return ' '+text if box.get() else text
    def _pick_fieldtype(self,key,label):
        """The dropdown deals in LABELS ("Citation form"); self.forms stores
        CODES ('lc'). Map back here rather than storing the label, or the code
        that keys every analysis-language row would become display text."""
        code=next((c for c,l in self.fieldtypes() if l==label),None)
        if code is None:
            log.info("TFDP: no field type matches {!r}; ignoring".format(label))
            return
        self.commit(key,code)
    def _display(self,key,placeholder=None):
        """What the button shows. The field type is the one key whose stored
        value ('lc') is not what a user should read, so it renders through
        fieldtypename(); everything else shows its value, or the placeholder it
        was built with when there is nothing stored yet — with any word break
        marked, since an unmarked one is invisible."""
        if key in self.STRUCTURAL:
            return self.fieldtypename()
        if placeholder is None:
            placeholder=self.fields[key]['placeholder']
        value=self._value(key)
        if not value:
            return placeholder
        lang,context=key
        if context=='before' and value.endswith(' '):
            return value[:-1]+self.WORDBREAK_MARK
        if context=='after' and value.startswith(' '):
            return self.WORDBREAK_MARK+value[1:]
        return value
    def editable(self,parent,key,placeholder='',tooltip=None,**grid):
        """A button showing a value, which BECOMES an entry field in place.

        This is the alphabet page's idiom (`frontend/alphabet_chart.py`
        edit_title/_set_chart_title: a permanent pair sharing one cell, swapped
        with grid()/grid_remove()), and it replaces four modal child windows —
        the frame name, each language's before/after text, and the field-type
        chooser. Those windows were confusing on their own terms (Kent
        2026-08-31) AND were the concrete case that made both visibility guards
        guess wrong: each was a toplevel parented to a drafter that withdrew
        ITSELF to show them, so the app was left with a mapped window whose
        ancestor was hidden, and 'what is the user looking at' had no answer.
        With every edit in place, this page never withdraws or deiconifies.

        Both halves are built here and one is hidden, so editing is a swap
        rather than a rebuild.
        """
        b=ui.Button(parent,text=self._display(key,placeholder),relief='raised',
                    cmd=lambda k=key:self.edit(k),**grid)
        ui.ToolTip(b,tooltip) if tooltip else ui.ToolTip(b)
        f=ui.Frame(parent,**grid)
        pair={'button':b,'entry':f,'placeholder':placeholder,'field':None,
                'var':None}
        self.fields[key]=pair
        if key in self.STRUCTURAL:
            # A pick-one, so an entry field would be the wrong instrument. A ROW
            # OF BUTTONS was the wrong one too (Kent 2026-08-31): the options
            # are as wide as their labels, so the row ran off the side of the
            # scrolling frame — and a horizontal overflow inside a vertical
            # scroll frame is simply unreachable. A dropdown is bounded by its
            # widest label instead of by their sum.
            labels=[label for code,label in self.fieldtypes()]
            pair['var']=var=ui.StringVar(self,self.fieldtypename())
            pair['combo']=ui.Combobox(f,textvariable=var,optionlist=labels,
                        width=max([len(i) for i in labels]+[8])+2,
                        command=lambda event=None,k=key,v=var:
                                    self._pick_fieldtype(k,v.get()),
                        row=0,column=0)
        else:
            pair['var']=var=ui.StringVar(self,self._value(key))
            pair['field']=field=ui.EntryField(f,render=True,text=var,
                                            row=0,column=0,sticky='')
            # field.rendered is DELIBERATELY NOT GRIDDED. The old modal showed
            # this rendered-text preview under the entry, and inline it is what
            # made the page jump: empty, the label reserves a default height,
            # and the first keystroke makes the renderer draw and the label
            # shrink to the rendering — so the row was ~45px too tall until you
            # typed, which pushed every row below it down and left the row's own
            # label vertically off-centre (Kent 2026-09-01, screenshot pairs for
            # both the name and the analang rows). It was NOT the reflow timing,
            # which is why deferring the reflow did not touch it.
            #
            # If a preview is wanted back for a non-Latin analysis orthography,
            # it needs a home whose height does not depend on whether it has
            # rendered yet — not a cell in the row being edited.
            def take(event=None,k=key,v=var):
                self.commit(k,v.get())
                # 'break' so Tab COMPLETES the entry instead of also doing its
                # default job — moving focus, which would land it on the entry
                # we just hid, or on whatever follows in an order the page
                # never defined.
                return 'break'
            field.bind('<Return>',take)
            field.bind('<Tab>',take)
            field.bind('<Escape>',lambda event=None:self.commit())
            ui.Button(f,text=_("OK"),cmd=take,row=0,column=1)
            if key[1] in ('before','after'):
                # THE WORD-BREAK BOX. Whether this text is separated from the
                # word by a space is otherwise invisible — a leading, trailing
                # or absent space all look the same — so it gets typed by
                # accident and nobody can see it afterwards. Making it a box
                # makes it a decision: _compose() then builds the stored form
                # from the text AND the box, box winning.
                #
                # UNDER the entry and in the small font (Kent 2026-08-31, with a
                # screenshot): beside it, at the inherited reading size, it was
                # wider than the field it qualifies and pushed OK off the edge
                # of the scrolling frame. It is a footnote to the value, not a
                # peer of it, so it should read as one.
                pair['wordbreak']=box=ui.BooleanVar()
                box.set(self._wordbreak(key))
                # font='small' shrank the LABEL but not the box: CheckButton
                # draws its own from theme images (indicatoron=False), so the
                # image is what set the height. image_pixels sizes both states
                # now, so this is the actual knob.
                cb=ui.CheckButton(f,text=_("word break"),variable=box,
                                font='small',
                                image_pixels=12,image_scaleto='height',
                                row=1,column=0,columnspan=2,sticky='w')
                ui.ToolTip(cb,_("Separate this text from the word with a "
                            "space. Shown as ‘{mark}’ when set.").format(
                            mark=self.WORDBREAK_MARK))
        f.grid_remove() #hidden until edit() swaps it in
        return b
    def fieldtypename(self):
        # Fall back to the raw code rather than IndexError: the page now BUILDS
        # before anything is settled, so a stored field type that is not in this
        # ps's option list must render as something clickable, not crash the
        # page out from under the user.
        return next((i[1] for i in self.fieldtypes()
                    if i[0] == self.forms.get('field')),
                    str(self.forms.get('field','')))
    def fieldtypes(self):
        # try:
        #     log.info("{}".format(self.program.settings.pluralname))
        #     log.info("{}".format(self.program.settings.imperativename))
        #     log.info("{}".format(self.program.settings.secondformfield[self.program.settings.verbalps]))
        #     log.info("{}".format(self.program.settings.secondformfield[self.program.settings.nominalps]))
        # except Exception as e:
        #     log.error("Exception in ps-land:{}".format(e))
        opts=[
                ('lc', _("Citation form")),
                ('lx', _("Lexeme form")),
                ]
        """These should maybe be switched over to just pl and imp"""
        if self.ps == self.program.settings.nominalps:
            opts.append((self.program.settings.pluralname, _("Plural form")))
        elif self.ps == self.program.settings.verbalps:
            opts.append((self.program.settings.imperativename, _("Imperative form")))
        return [(i,j) for (i,j) in opts if i]
    # getfieldtype() lived here: a child ui.Window holding a ButtonFrame of the
    # field-type options. Replaced by editable()'s ('field',None) branch, which
    # shows the same options inline. So did setfieldtype(choice,window), whose
    # only extra job was closing that window.
    def exemplified(self,event=None):
        log.info("Giving example now")
        checktoadd=self.forms['name']
        if hasattr(self,'exf'):
            self.exf.destroy()
        self.exf=ui.Frame(self.content,row=2,column=0,sticky='w')
        # THE NAME GATE, and now the ONLY one. The up-front prompt is gone, so
        # this is what keeps a frame from being finished unnamed — and it holds,
        # because the "Use this tone frame" button that calls submit() is built
        # below, inside this method, after this return. .strip() added with the
        # gate move: a name of spaces passed `in ['',None]` and would have been
        # stored as a frame nobody could tell from another.
        if not str(checktoadd or '').strip():
            text=_('Sorry, empty name! \nPlease provide at least \na frame '
                'name, to distinguish it \nfrom other frames.')
            log.error(rx.delinebreak(text))
            l1=ui.Label(self.exf,
                        text=text,
                        font='read',
                        justify=ui.LEFT,anchor='w',
                        row=0,column=0,
                        sticky='w')
            self._reflow(tobottom=True) #or the label stays invisible
            return
        #don't give exs w/o all glosses
        """Define the new frame"""
        checkdefntoadd={'field':self.forms['field']}
        log.info("Ready to add frame with this form info: {}".format(self.forms))
        # log.info("Ready to add frame with this lookingfor info: {}".format(self.lookingfor))
        for lang in [i for i in self.forms #self.lookingfor
                            if 'before' in self.forms[i]
                            if 'after' in self.forms[i]
                ]: #just the defined languages
            before=self.forms[lang]['before']
            after=self.forms[lang]['after']
            checkdefntoadd[lang]=str(before+'__'+after)
        formdict=self.gimmesenseformdictwftypengloss(checkdefntoadd)
        #This should only pull from current ps
        # log.info('formdict result: {}'.format(formdict))
        padx=50
        pady=10
        row=0
        text=_("Examples for {name} {field} tone frame").format(name=checktoadd,
                                                        field=self.fieldtypename())
        lt=ui.Label(self.exf,
                text=text,
                font='readbig',
                justify=ui.LEFT,anchor='w',
                row=row,column=0,
                sticky='w',#columnspan=2,
                padx=padx,pady=pady)
        if not formdict:
            l1=ui.Label(self.exf,
                    text=_("None!"),
                    font='read',
                    justify=ui.LEFT,anchor='w',
                    row=row,column=0,
                    sticky='w',
                    padx=padx,pady=pady)
            self._reflow(tobottom=True) #or the label stays invisible
            return
        for lang,forms in formdict.items():
            row+=1
            text=('[{}]: {}'.format(lang,forms))#framed.forms.framed[lang]))
            l1=ui.Label(self.exf,
                    text=text,
                    font='read',
                    justify=ui.LEFT,anchor='w',
                    row=row,column=0,
                    sticky='w',
                    padx=padx,pady=pady)
            log.info('langlabel:{}'.format(text))
        """toneframes={'Nom':
                        {'name/location (e.g.,"By itself")':
                            {'analang.xyz': '__',
                            'glosslang.xyz': 'a __'},
                            'glosslang2.xyz': 'un __'},
                    }   }
        """
        row+=1
        stext=_('Use {name} tone frame').format(name=checktoadd)
        subframe=ui.Frame(self.exf,row=row,column=0,sticky='w')
        sub_btn=ui.Button(subframe,text = stext,
                          command = lambda x=checkdefntoadd,
                                            n=checktoadd: self.submit(x,n),
                          row=0,column=0,
                          )
        ui.Label(subframe, text=_("<= No changes after this! \nPlease check that "
                                "the above looks good on several examples!"),
                                justify='left', row=0, column=1, padx=15)
        # log.info('sub_btn:{}'.format(stext))
        sub_btn.update_idletasks()
        # grow the canvas to cover the example frame just built, then scroll to
        # it: the examples land below the fold, so without the scroll the click
        # looked like nothing happened.
        self._reflow(tobottom=True)
    def promptstrings(self,lang=None,context=None):
        #None of this changes in editing. Is that what we want?
        if lang:
            lname=self.program.settings.languagenames[self.stripftypecode(lang)]
            text=_("Fill in the {lang} frame forms below.\n(include a "
                "space to separate word forms)"
                ).format(lang=lname)
            if lang != self.stripftypecode(lang): #i.e., analang
                kind=_('form')
                ok=_('Use this form')
            else:
                kind=_('gloss')
                ok=_("Use this {lang} form {context} the dictionary gloss").format(lang=lname,
                                context=_(context))
                # `self.glosslangs.append(lang)` was here — a mutation hidden in
                # a string builder. It has to go now that this is called once
                # per language per rebuild to make a tooltip (it would grow
                # without bound), and nothing loses anything: the attribute is
                # written only here and read only by SortT.addtonefieldpron,
                # which is a DIFFERENT class's attribute and is marked "unused;
                # leads to broken lift fn" in its own signature line.
            if context == 'before':
                text+='\n'+_("What text goes *before* \n<==the {lang} word *{kind}* "
                        "\nin the frame?").format(lang=lname,kind=kind)
            elif context == 'after':
                text+='\n'+_("What text goes *after* \nthe {lang} word *{kind}*==> "
                        "\nin the frame?").format(lang=lname,kind=kind)
        else:
            text=_("What do you want to call this new {ps} tone frame for {lang}?"
                    ).format(ps=self.ps,
                            lang=self.program.settings.languagenames[self.analang])
            ok=_("Use this name")
        return {'lang':lang, 'prompt':text, 'ok':ok}
    # promptwindow() lived here — the modal child window behind every edit on
    # this page, and the direct cause of the 1.14.3 no-window report: it created
    # a toplevel and then WITHDREW ITS OWN PARENT (`self.withdraw()`, "Don't
    # show status when asking for a value"), leaving a mapped window whose
    # ancestor was hidden. Replaced by editable() above.
    #
    # Two of its mechanisms are deliberately NOT carried over:
    #  - the '<no content>' placeholder, swapped in and out on focus. It existed
    #    because a blank field in a bare modal looked broken; inline, the
    #    surrounding labels say what the slot is. It was also a live hazard —
    #    a placeholder that silently becomes the stored value, which is exactly
    #    what the name-gate item warned against. An empty value now stays empty.
    #  - stashing a StringVar INTO self.forms when a key was missing, so an
    #    abandoned prompt left a widget object where a string belonged. That is
    #    why status() had to test `isinstance(self.forms['name'],ui.StringVar)`
    #    to decide whether the user had really answered. Nothing writes to
    #    self.forms now except commit().
    def submit(self,checkdefntoadd,checktoadd,event=None):
        log.info("Submitting {} frame with these values: {}".format(
                                                checktoadd,checkdefntoadd
                                                ))
        # Having made and unset these, we now reset and write them to file.
        self.program.toneframes.addframe(self.ps,checktoadd,checkdefntoadd)
        self.program.status.renewchecks() #renew (not update), because of new frame
        # log.info("object: {}".format(self.program.toneframes))
        self.program.settings.storesettingsfile(setting='toneframes')
        self.program.settings.setcheck(checktoadd) #assume we will use this now
        self.task.deiconify()
        self.destroy()
    def gimmesense(self,sense=None,next=False,**kwargs):
        sensesbyps=self.program.db.sensesbyps[self.ps]
        if next and sense:
            # log.info("trying {} sense {}/{}".format(self.ps,
            #                                     sensesbyps.index(sense)+1,
            #                                     len(sensesbyps)))
            try:
                return sensesbyps[sensesbyps.index(sense)+1]
            except IndexError:
                return sensesbyps[0]
        else:
            sense=sensesbyps[randint(0, len(sensesbyps)-1)]
            # log.info("returning random {} sense {}".format(self.ps,sense.id))
            return sense
    def gimmesenseformdictwftypengloss(self,framedef,**kwargs):
        tried=0
        langs=[i for i in framedef if i not in ['name','field']]
        glosslangs=[i for i in langs if i == self.stripftypecode(i)]
        # log.info("checking for these langs: {}".format(langs))
        # log.info("checking for this frame: {}".format(framedef))
        ftype=framedef['field']
        while not tried or None in f.values():
            f={lang:None for lang in langs} #start each with a clean slate
            if tried > self.program.db.nsenses*1.5: #give up looking randomly
                sense=self.gimmesense(sense,next=True)
            else:
                sense=self.gimmesense()
            f.update(sense.formatteddictbylang(self.analang, #This is xyz_ftype
                                        glosslangs,
                                        # self.program.settings.glosslangs,
                                        frame=framedef
                                            ))
            # log.info("Analang form found: {}".format(f[self.analang]))
            tried+=1
            log.info("Values found: {}".format(f))
            if tried> self.program.db.nsenses*3.5:
                errortext=_("I’ve tried (randomly, then through each) {count} "
                "times, and not found one "
                "of your {total} senses with data in each of these languages: "
                "{langs}. \nAre you asking for gloss "
                "languages which actually have data in your database? \nOr, are "
                "you missing gloss fields (i.e., you have only ‘definition’ "
                "fields)?").format(count=tried,total=self.program.db.nsenses,langs=langs)
                log.error(errortext)
                return #errortext
        log.debug("Found entry {} with glosses {}".format(sense.id,f))
        return f
    def __init__(self,parent):
        ui.Window.__init__(self,parent)
        self.task=parent #this should always be called by a window task
        self.program=parent.program #inherit() doesn't carry program
        self.analang=parent.analang
        self.ps=self.program.slices.ps()
        self.forms={}
        # we want to start this net wide, to cover future usage
        # At some point, I may want to distinguish the analang from its gloss
        # in the same language code. They have different values in LIFT, and
        # there might be reason to distinguish them in the frame definitions.
        # But until I figure out how i want to do that, each language should
        # just appear once.
        self.glosslangs=list()
        self.padx=50
        self.pady=10
        title=_("Define a New {ps} Tone Frame for {lang}").format(ps=self.ps,
                        lang=self.program.settings.languagenames[self.analang])
        self.title(title)
        t=f"Add {self.ps} Tone Frame for {self.program.settings.languagenames[self.analang]}"#+'\n'?
        ui.Label(self.frame,text=t,font='title',row=0,column=0)
        self.scroll=ui.ScrollingFrame(self.frame,row=1,column=0)
        self.content=self.scroll.content
        # Which field is being edited, or None, and the button/entry pairs it
        # indexes. Set here as well as in status(), because status() returns
        # early when the window is already exiting.
        self.active=None
        self.fields={}
        self.status()

    def store(self):
        log.info(_("Saving toneframes dict to file"))
        self.program.settings.storesettingsfile('toneframes')
class Sort(backend.core.sorting_engine.Sort):
    is_sort_task=True
    cvt_sensitive=True
    def dobuttonkwargs(self):
        return {'text':_("Sort!"),
                'fn':self.runcheck,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                # 'image':self.program.theme.photo[self.cvt], #self.cvt
                'image':self.cvt, #self.cvt
                'sticky':'ew'
                }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
class SortSyllables(backend.core.sorting_engine.SyllablePrep,
                    Sort,Syllables,Segments,Task):
    # SyllablePrep FIRST so its runcheck routes Task 1 (the three primitive
    # checks, each sliced ≤MAX_SLICE) through maybeverifysyllables, NOT maybesort;
    # once prep is complete it hands off to Task 2 (profile-class profile sort) via
    # the inherited Sort.runcheck/maybesort. Syllables before Segments so its
    # group/form overrides win (relabel profile groups, never rewrite the surface
    # form); Segments still supplies shared helpers. presortgroups + the
    # sort/verify/join cycle come from Syllables (lexicon.py). See
    # docs/syllable_sort_redesign.md and docs/sort_syllables_design.md.
    taskicon = 'iconWord'
    tasktitle = "Sort Word Syllables" #Citation Form Sorting in Tone Frames
    cvt='S'
    def tooltip(self):
        return _("This task helps you sort words in citation form by whole "
                "word syllable profiles.")
    # dobuttonkwargs inherited from Sort: image=self.cvt ('S' → the syllable
    # photo, renamed from 'CV').
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Opened mid-session (e.g. 'Not {profile}' → 'sort syllables') we inherit
        # the previous task's in-memory picture, and the single profile/status
        # rebuild the defer path skipped (no per-click load_ps_profiles) never ran.
        # Do it now so the board lands on the correct STAGE (prep vs profile) and
        # Task-2 verification reflects reality — instead of only self-correcting
        # after a redundant 'Sort!'. maybeboard keys the board on
        # syllable_prep_complete, which reads the 'S' prep status node that
        # syllable_slices resyncs.
        try:
            # Enforce the cvprofile↔annotation invariant HERE (scrub otherwise only
            # runs at boot) so a mid-session divergence is cleared → that word drops
            # out → it becomes affirmable → the trigger can fix it, instead of a
            # stuck 'unverified but no trigger' group.
            self.program.profiles.scrub_sorts_to_primitives()
            self.program.db.load_ps_profiles()    # refresh profile slices
            self.syllable_slices(rebuild=True)     # resync the 'S' prep status node
            self.rebuild_syllable_profile_done()   # profile 'done' from …-x-cvprofile
            self.status.maybeboard()               # redraw with the true stage
        except Exception as e:
            log.info("SortSyllables open refresh failed: %s", e)
class SortCV(Sort,Segments,Task):
    """docstring for SortCV."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
class SortS(Sort,Segments,Task):
    def __init__(self, **kwargs):
        """TranscribeS sends us here with redo_glyph, to resume sorting that was interrupted
        by the need to transcribe a segment. This should probably be handled differently."""
        """Sort.update_to_cvt sends us here with sort_immediately if it is asked to sort
        an item with a wrong cvt"""
        """Should consider how this impacts tone logic"""
        # Resume re-entries (redo_glyph / sort_immediately) show immediately; a
        # normal open stays withdrawn until the syllable-profile offer is
        # answered, because one answer ('sort') sends the user to a different
        # task and this board should never paint behind it.
        if not (kwargs.get("redo_glyph") or kwargs.get("sort_immediately")):
            kwargs["withdrawn"]=True
        super().__init__(**kwargs)
        if g:=kwargs.get("redo_glyph"):
            self.redo_joinglyphs(g)
        elif g:=kwargs.get("sort_immediately"):
            self.runcheck()
        elif self.offer_profile_setup(at_open=True)=='sort':
            # User chose to go sort syllable profiles first: tear down this still-
            # hidden board, THEN open the syllable task (teardown before launch so
            # the two boards never coexist).
            self._dismiss_unshown()
            self.program.taskchooser.maketask('SortSyllables')
        else:
            # Profiles fine / affirmed / acknowledged: reveal the board now.
            self.deiconify()
class SortV(Vowels,SortS):
    taskicon = 'iconV'
    tasktitle = "Sort Vowels" #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by vowels.")
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # if g:=kwargs.get("redo_glyph"):
        #     self.redo_joinglyphs(g)
        # elif g:=kwargs.get("sort_immediately"):
        #     self.runcheck()
class SortC(Consonants,SortS):
    taskicon = 'iconC'
    tasktitle = "Sort Consonants" #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form by consonants.")
    # def dobuttonkwargs(self):
    #     return {'text':_("Sort!"),
    #             'fn':self.runcheck,
    #             # column=0,
    #             'font':'title',
    #             'compound':'bottom', #image bottom, left, right, or top of text
    #             'image':self.program.theme.photo['C'], #self.cvt
    #             'sticky':'ew'
    #             }
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
class SortT(Sort,Tone,Task):
    is_sort_tone_task=True
    taskicon = 'iconT'
    tasktitle = "Sort Tone" #Citation Form Sorting in Tone Frames
    def tooltip(self):
        return _("This task helps you sort words in citation form tone frames.")
    # def dobuttonkwargs(self):
    #     return {'text':_("Sort!"),
    #             'fn':self.runcheck,
    #             # column=0,
    #             'font':'title',
    #             'compound':'bottom', #image bottom, left, right, or top of text
    #             'image':self.program.theme.photo['T'], #self.cvt
    #             'sticky':'ew'
    #             }
    def addtonefieldpron(self,guid,framed): #unused; leads to broken lift fn
        sense=None
        self.program.db.addpronunciationfields(
                                    guid,sense.id,self.analang,self.glosslangs,
                                    lang='en',
                                    forms=framed,
                                    fieldtype='tone',location=check,
                                    fieldvalue=self.groupselected,
                                    ps=None
                                    )
    def marksortedguid(self,guid):
        """I think these are only valuable during a check, so we don't have to
        constantly refresh sortingstatus() from the lift file."""
        """These four functions should be generalizable"""
        self.guidssorted.append(guid)
        self.guidstosort.remove(guid)
    def marktosortguid(self,guid):
        self.guidstosort.append(guid)
        self.guidssorted.remove(guid)
    def __init__(self, **kwargs): #frame, filename=None
        # Stay withdrawn until the syllable-profile offer is answered (see SortS):
        # one answer ('sort') sends the user elsewhere, so this board must not
        # paint first.
        kwargs["withdrawn"]=True
        super().__init__(**kwargs)
        if self.offer_profile_setup(at_open=True)=='sort':
            self._dismiss_unshown()
            self.program.taskchooser.maketask('SortSyllables')
        else:
            self.deiconify()
    """Doing stuff"""
class Transcribe(Sound,Categories,Task):
    cvt_sensitive=True
    def updateerror(self):
        newvalue=self.transcriber.formfield.get()
        if newvalue == '':
            noname=_("Give a name for this group!")
            log.debug(noname)
            self.errorlabel['text'] = noname
            return 1
        elif newvalue != self.group and newvalue in self.groups:
            deja=[_("Sorry, there is already a group with that label"),
                _("see comparison below.")]
            log.debug('; '.join(deja))
            self.errorlabel['text'] = ';\n '.join(deja)
            self.setgroup_comparison(newvalue)
            return 1
        self.errorlabel['text'] = ''
    def updateform(self,*args):
        self.set_ok_w_form(self.updateerror())
    def refresh_status_buttons(self,*args):
        if hasattr(self, 'status') and hasattr(self.status, 'glyphbuttons'):
            for i in args:
                if (i in self.status.glyphbuttons
                        and self.status.glyphbuttons[i].winfo_exists()):
                    self.status.glyphbuttons[i].destroy()
    def switchgroups(self,comparison=None):
        #this doesn't save!
        if (not hasattr(self,'group') or not hasattr(self,'group_comparison')
            and not comparison):
            log.error(_("Missing either group or comparison, without value "
                        "specified; can’t switch them."))
            return
        log.info(_("Swtiching groups; using ‘{comp}’ for "
                "‘{group}’").format(comp=self.group_comparison, group=self.group))
        #actually change the data, not the group settings:
        #This method should go somewhere more reasonable:
        g=self.add_int_group(self) #Don't merge groups!
        if self.cvt == 'T':
            fn=self.rename_group
        else:
            fn=self.rename_macrogroup
        fn(self.group,g,updatestatus=False)
        fn(self.group_comparison,self.group,updatestatus=False)
        fn(g,self.group_comparison)
        self.refresh_status_buttons(g,self.group_comparison)
        # self.program.settings.setgroup(gc)
        self.ui.runwindow.on_quit()
        self.makewindow() #The other group needs a name, too!
    def submitandswitch(self):
        if hasattr(self,'group_comparison'):
            comparison=self.group_comparison
        else:
            self.errorlabel['text'] = _("Sorry, pick a comparison first!")
            return 1
        error=self.submitform()
        if not error:
            self.switchgroups(comparison)
    def updategroups(self):
        # Update locals group, groups, and othergroups from objects
        # VISIBLE, not membership: self.groups feeds self.othergroups (below) =
        # the glyph page's comparison targets, so NA must not be among them (NA
        # audit, rule C). Nothing writes self.groups back — submitform stores by
        # NAME via renamegroup — so the read-modify-write hazard doesn't apply.
        self.groups=self.program.status.groups_visible(wsorted=True)
        # log.info("self.groups: {}".format(self.groups))
        self.groupsdone=self.program.status.verified()
        self.group=self.program.status.group()
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        if not self.groups:
            ErrorNotice(_("No groups in that slice; try another!"))
            return
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        if self.group is None or self.group not in self.groups:
            w=self.getgroup(wsorted=True, guess=True, intfirst=True)
            if w.winfo_exists():
                w.wait_window(w)
            self.group=self.program.status.group()
            if not self.group:
                log.info("I asked for a framed tone group, but didn't get one.")
                return
        # log.info("group: {}, groups: {}".format(self.group,self.groups))
        self.othergroups=self.groups[:]
        try:
            self.othergroups.remove(self.group)
        except ValueError:
            log.error(_("current group ({group}) doesn’t seem to be in list of "
                "groups: ({groups})\n\tThis may be because we’re looking for data "
                "that isn’t there, or maybe a setting is off.").format(
                                                    group=self.group, groups=self.groups))
            return
        return 1
    def unsubmit(self,event=None):
        log.info("Undoing...")
        self.mistake=True
    def submitform(self):
        # Only tone reaches submitform now: segmental glyph naming goes through
        # GlyphTranscribeHelper (TranscribeS.makewindow delegates to it), which
        # has its own submitform + polygraphwarn. The former 'if cvt != "T"'
        # segmental branch here, and Transcribe.polygraphwarn, were dead — their
        # only entry was TranscribeS.done, which nothing wired — so both are
        # gone. (polygraphwarn now lives solely on the helper.)
        newvalue=self.transcriber.formfield.get()
        """updateforms=True doesn't seem to be working for segments"""
        self.updatebygroupsense(self.group,newvalue,updateforms=True)
        #NO: this should update formstosearch and profile data.
        # log.info("Doing renamegroup: {}>{}".format(self.group,newvalue))
        self.program.status.renamegroup(self.group,newvalue) #status file only
        # log.info("Doing updategroups")
        self.updategroups() #updates self.groups self.group self.othergroups self.groupsdone
        self.program.settings.storesettingsfile(setting='status')
        """Update regular expressions here!!"""
        self.maybewrite()
        self.ok_done=True
        # update forms, even if group doesn't change:
        if hasattr(self,'group_comparison'):
            delattr(self,'group_comparison') # in either case
        self.ui.runwindow.on_quit()
    def next(self):
        log.debug("running next group")
        error=self.submitform()
        if not error:
            # log.debug("group: {}".format(group))
            ints=[i for i in self.program.status.groups(wsorted=True)
                    if i.isdigit()]
            if ints:
                log.info("Found integer groups: {ints}".format(ints=ints))
                self.program.status.group(str(min(ints)))#Look for integers first
            else:
                log.info("Didn't Find integer groups: {groups}".format(
                    groups=self.program.status.groups(wsorted=True)))
                #_visible: this advances to the next group to NAME, and NA is not a
                #name-able group on any check (NA audit, rule C).
                self.program.status.nextgroup_visible(wsorted=True)
            # log.debug("group: {}".format(group))
            self.makewindow()
    def nextcheck(self):
        log.debug("running next check")
        error=self.submitform()
        if not error:
            # log.debug("check: {}".format(check))
            self.program.status.nextcheck(wsorted=True)
            # log.debug("check: {}".format(check))
            self.makewindow()
    def nextprofile(self):
        log.debug("running next profile")
        error=self.submitform()
        if not error:
            # log.debug("profile: {}".format(profile))
            self.program.status.nextprofile(wsorted=True)
            # log.debug("profile: {}".format(profile))
            self.makewindow()
    def setgroup_comparison(self,group=None,**kwargs):
        if group:
            self.program.settings.set('group_comparison',group)
        else:
            #this returns its window:
            w=self.getglyph(comparison=True,**kwargs)
            if w and w.winfo_exists(): #This window may be already gone
                log.info("Waiting for {w}".format(w=w))
                w.wait_window(w)
        #getattr: the next line guards the same attribute, since settings only has
        #it once a comparison is picked. See transcribe_glyph.setgroup_comparison.
        log.info(_("Groups: {group} (of {groups}); "
                "{comp}?").format(group=self.group, groups=self.groups,
                                comp=getattr(self.program.settings,
                                            'group_comparison', None)))
        if hasattr(self.program.settings,'group_comparison'):
            self.group_comparison=self.program.settings.group_comparison
        if self.errorlabel['text'] == _("Sorry, pick a comparison first!"):
            self.updateerror()
        self.comparisonbuttons()
    def comparisonbuttons(self):
        try: #successive runs
            self.compframe.compframeb.destroy()
            log.info("Comparison frameb destroyed!")
        except Exception: #first run
            log.info("Problem destroying comparison frame, making...")
        self.compframe.compframeb=ui.Frame(self.compframe)
        self.compframe.compframeb.grid(row=1,column=0)
        t=_('Compare with another group')
        if (hasattr(self, 'group_comparison')
                and self.group_comparison in self.groups and
                self.group_comparison != self.group):
            log.info("Making comparison buttons for group {group} now".format(
                                                group=self.group_comparison))
            t=_('Compare with another group ({group})').format(
                                                group=self.group_comparison)
            self.compframe.bf2=SortGlyphGroupButtonFrame(
                                    self.compframe.compframeb,
                                    self,
                                    group=self.group_comparison,
                                    showtonegroup=True,
                                    playable=True,
                                    unsortable=False, #no space, bad idea
                                    alwaysrefreshable=True,
                                    font='default',
                                    wraplength=self.buttonframew
                                    )
            self.compframe.bf2.grid(row=0, column=0, sticky='w')
            self.compframe.b2=ui.Button(self.compframe.compframeb,
                                        text=self.switch_text,
                                        cmd=self.switchgroups,
                                        row=0, column=1, sticky='w')
            self.compframe.b2tt=ui.ToolTip(self.compframe.b2, self.switch_tt)
            # self.maybeswitchmenu=ui.ContextMenu(self.compframe)
            # self.maybeswitchmenu.menuitem(_("Switch to this group"),
            #                                 self.switchgroups)
        elif not hasattr(self, 'group_comparison'):
            log.info("No comparison found !")
        elif self.group_comparison not in self.groups:
            log.info("Comparison ({comp}) not in group list ({groups})"
                        "".format(comp=self.group_comparison,groups=self.groups))
        elif self.group_comparison == self.group:
            log.info("Comparison ({comp}) same as subgroup ({group}); not showing."
                        "".format(comp=self.group_comparison,group=self.group))
        else:
            log.info(_("This should never happen (renamegroup/"
                        "comparisonbuttons)"))
        self.sub_c['text']=t
    def __init__(self, program, **kwargs): #frame, filename=None
        super().__init__(program=program, **kwargs)
        self.makeeverythingok() #why?
        self.ftype=self.program.params.ftype()
        self.mistake=False #track when a user has made a mistake
        self.analang=self.program.params.analang()
        self.program.status.makecheckok()
class TranscribeS(Transcribe,Segments):
    macrosort=True
    do_not_show_slices=True
    glyph_leaderboard=True
    # done() removed: segmental glyph naming runs through GlyphTranscribeHelper
    # (its OK button calls helper.done, with the pyaudio teardown supplied via
    # the on_done hook in makewindow). The old done() was unwired and called the
    # now tone-only Transcribe.submitform.
    def go_back(self):
        log.info("Transcribe done for now (going back)")
        self.ui.runwindow.on_quit()
        self.program.soundsettings.done_pyaudio()
        self.program.taskchooser.maketask(f"Sort{self.program.params.cvt()}",
                                        redo_glyph=self.group)
    def set_ok_w_form(self,error=False):
        form=self.transcriber.formfield.get()
        self.oktext.set(_("OK: Add the letter ‘{form}’ {newline}to my alphabet "
                        "{newline}for this sound").format(form=form,newline="\n"))
        if form and not error:
            self.ok_button['state'] = 'normal'
        else:
            self.ok_button['state'] = 'disabled'
    def makewindow(self, glyph=None, event=None):
        from tasks.transcribe_glyph import GlyphTranscribeHelper
        if not hasattr(self, '_glyph_helper'):
            self._glyph_helper = GlyphTranscribeHelper(
                self, glyphspossible=self.glyphspossible,
                switch_text=self.switch_text, switch_tt=self.switch_tt,
                on_done=lambda: self.program.soundsettings.done_pyaudio(),
                on_go_back=self._go_back_from_helper)
        self._glyph_helper.makewindow(glyph, event)
        # Sync state back for methods that reference self.xxx
        self.ok_done = self._glyph_helper.ok_done
        self.window_failed = self._glyph_helper.window_failed
        self.group = self._glyph_helper.group
        self.groups = self._glyph_helper.groups
        self.transcriber = getattr(self._glyph_helper, 'transcriber', None)
        self.errorlabel = getattr(self._glyph_helper, 'errorlabel', None)
        if hasattr(self, 'status'):
            self.status.updateglyphbuttons()

    def _go_back_from_helper(self):
        self.program.soundsettings.done_pyaudio()
        self.program.taskchooser.maketask(f"Sort{self.program.params.cvt()}",
                                        redo_glyph=self._glyph_helper.group)
    def __init__(self, program, **kwargs):
        self.switch_text=_("Switch letters with this group")
        self.switch_tt=_("This switches letters for the two groups, and "
                            "updates each of them")
        super().__init__(program=program, **kwargs)
class TranscribeV(TranscribeS):
    tasktitle = "Vowel Letters"
    def tooltip(self):
        return _("This task helps you decide on your vowel letters.")
    taskicon = 'iconTranscribeV'
    def __init__(self, program, **kwargs): #frame, filename=None
        from tasks.transcribe_glyph import VOWEL_GLYPHS
        self.glyphspossible=VOWEL_GLYPHS
        self.cvt=program.params.cvt('V')
        super().__init__(program=program, **kwargs)
class TranscribeC(TranscribeS):
    tasktitle = "Consonant Letters"
    def tooltip(self):
        return _("This task helps you decide on your consonant letters.")
    taskicon = 'iconTranscribeC'
    def __init__(self, program, **kwargs): #frame, filename=None
        from tasks.transcribe_glyph import CONSONANT_GLYPHS
        self.glyphspossible=CONSONANT_GLYPHS
        self.cvt=program.params.cvt('C')
        super().__init__(program=program, **kwargs)
class TranscribeT(Transcribe,Tone):
    tasktitle = "Transcribe Tone"
    def tooltip(self):
        return _("This task helps you transcribe your surface groups, giving "
                "them meaniningful names (e.g., [˥˥ ˨˨]) instead of numbers.")
    def dobuttonkwargs(self):
        return {'text':_("Transcribe Surface Tone Groups"),
                'fn':self.makewindow,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['Transcribe'], #self.cvt
                'sticky':'ew'
                }
    taskicon = 'iconTranscribe'
    def done(self):
        log.info("Transcribe done")
        self.submitform()
        self.program.soundsettings.done_pyaudio()
    def set_ok_w_form(self):
        pass #maybe use some day?
    def makewindow(self, group=None, event=None):
        if group:
            self.group=self.program.status.group(group)
        """Go through this and tease apart what is needed for tone complexity,
        and move that to tone.
        Note to user: you can't pick these group names (switch later, not here)
        Make another function to switch letters between groups."""
        # log.info("Making transcribe window")
        def changegroupnow(event=None):
            w=self.program.taskchooser.getgroup(wsorted=True)
            self.ui.runwindow.wait_window(w)
            if not w.exitFlag.istrue():
                self.ui.runwindow.on_quit()
                self.makewindow()
        cvt=self.program.params.cvt()
        ps=self.program.slices.ps()
        profile=self.program.slices.profile()
        check=self.program.params.check()
        self.buttonframew=int(self.program.screenw/3.5)
        if not check:
            self.getcheck(guess=True)
            if check is None:
                # log.info("I asked for a check name, but didn't get one.")
                return
        if not self.program.status.groups(wsorted=True):
            log.error(_("I don’t have any sorted data for check: {check}, "
                        "ps-profile: {ps}-{profile},").format(check=check,ps=ps,profile=profile))
            return
        groupsok=self.updategroups()
        if not groupsok:
            log.error("Problem with log; check earlier message.")
            return
        padx=50
        if self.program.settings.lowverticalspace:
            log.info("Using low vertical space setting")
            pady=0
        else:
            pady=10
        title=_("Rename {ps} {profile} {noun_sg} group ‘{group}’ in ‘{check}’ frame"
                        ).format(ps=ps,profile=profile,
                        noun_sg=self.program.params.cvtdict()[cvt]['sg'],
                        group=self.group,check=check)
        self.ui.getrunwindow(title=title)
        titlel=ui.Label(self.ui.runwindow.frame,text=title,font='title',
                        row=0,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getformtext=[_("What new name do you want to call this {sg} "
                        "group?").format(sg=self.program.params.cvtdict()[cvt]['sg'])]
        if cvt == 'T':
            getformtext.append(_("A label that describes the surface tone form "
                        "in this context would be best, like ‘[˥˥˥ ˨˨˨]’"))
        getform=ui.Label(self.ui.runwindow.frame,
                        text='\n'.join(getformtext),
                        font='read',
                        norender=True,
                        row=1,column=0,sticky='ew',padx=padx,pady=pady
                        )
        getform.wrap()
        inputfeedbackframe=ui.Frame(self.ui.runwindow.frame,
                            row=2,column=0,sticky=''
                            )
        self.transcriber=transcriber.Transcriber(inputfeedbackframe,
                                initval=self.group,
                                soundsettings=self.soundsettings,
                                chars=self.glyphspossible,
                                row=0,column=0,sticky=''
                                )
        self.transcriber.formfield.bind('<KeyRelease>', self.updateerror)
        infoframe=ui.Frame(inputfeedbackframe,
                            row=0,column=1,sticky=''
                            )
        """Make this a pad of buttons, rather than a label, so users can
        go directly where they want to be"""
        g=nn(self.othergroups,perline=len(self.othergroups)//5)
        # log.info("There: {}, NTG: {}; g:{}".format(self.groups,
        #                                             self.othergroups,g))
        groupslabel=ui.Label(infoframe,
                            text='\n'.join([_('Other Groups:'),g]),
                            row=0,column=1,
                            sticky='new',
                            padx=padx,
                            rowspan=2
                            )
        groupslabel.bind('<ButtonRelease-1>',changegroupnow)
        self.errorlabel=ui.Label(infoframe,text='',
                            fg='red',
                            wraplength=int(self.frame.winfo_screenwidth()/3),
                            row=2,column=1,sticky='nsew'
                            )
        responseframe=ui.Frame(self.ui.runwindow.frame,
                                row=3,
                                column=0,
                                sticky='',
                                padx=padx,
                                pady=pady,
                                )
        self.oktext=_('Use this name and go to:')
        column=0
        sub_lbl=ui.Label(responseframe,text = self.oktext, font='read',
                        row=0,column=column,sticky='ns'
                        )
        buttons=[
                (_('main screen'), self.done),
                (_('next group'), self.next)]
        if cvt == 'T':
            buttons+=[(_('next tone frame'), self.nextcheck)]
        else:
            buttons+=[(_('next check'), self.nextcheck)]
        buttons+=[(_('next syllable profile'), self.nextprofile),
                (_('comparison group'), self.submitandswitch)
                ]
        for button in buttons:
            column+=1
            ui.Button(responseframe,text = button[0], command = button[1],
                                anchor ='c',
                                row=0,column=column,sticky='ns'
                                )
        examplesframe=ui.Frame(self.ui.runwindow.frame,
                                row=4,column=0,sticky=''
                                )
        b=SortGroupButtonFrame(examplesframe, self,
                                group=self.group,
                                showtonegroup=True,
                                # canary=entryview,
                                playable=True,
                                unsortable=True,
                                alwaysrefreshable=True,
                                row=0, column=0, sticky='w',
                                wraplength=self.buttonframew
                                )
        self.compframe=ui.Frame(examplesframe,
                    highlightthickness=10,
                    highlightbackground=self.frame.theme.white,
                    row=0,column=1,sticky='e'
                    ) #no hlfg here
        t=_('Compare with another group')
        self.sub_c=ui.Button(self.compframe,
                        text = t,
                        command = self.setgroup_comparison,
                        row=0,column=0
                        )
        self.comparisonbuttons()
        self.ui.runwindow.waitdone()
        self.ui.runwindow.deiconify() #created withdrawn; see tonegroupsjoinrename
        self.sub_c.wait_window(self.ui.runwindow) #then move to next step
        """Store these variables above, finish with (destroying window with
        local variables):"""
    def __init__(self, program, **kwargs): #frame, filename=None
        self.switch_text=_("Switch transcriptions with this group")
        self.switch_tt=_("This doesn’t save the curent group")
        self.glyphspossible=None
        program.params.cvt('T')
        super().__init__(program=program, **kwargs)
class JoinUFgroups(Tone,Task):
    """docstring for JoinUFgroups."""
    tasktitle = "Join Underlying Form Groups"
    taskicon = 'iconJoinUF'
    do_not_show_cvt=True
    icon_leaderboard=True
    def tooltip(self):
        return _("This task helps you join hypersplit UF groups, as well as "
                "giving them meaniningful names (e.g., High or Low).")
    def dobuttonkwargs(self):
        return {'text':_("Join draft UF Groups"),
                'fn':self.tonegroupsjoinrename,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['JoinUF'], #self.cvt
                'sticky':'ew'
                }
    def tonegroupsjoinrename(self,**kwargs):
        def clearerror(event=None):
            errorlabel['text'] = ''
        def submitform():
            clearerror()
            uf=named.get()
            if uf == '':
                noname=_("Give a name for this UF tone group!")
                log.debug(noname)
                errorlabel['text'] = noname
                return
            groupsselected=[]
            for group in groupvars: #all group variables
                groupsselected+=[group.get()] #value, name if selected, 0 if not
            groupsselected=[x for x in groupsselected if x != '']
            log.info(f"groupsselected:{groupsselected}")
            if uf in self.analysis.orderedUFs and uf not in groupsselected:
                deja=_("That name is already there! (did you forget to include "
                        "the ‘{uf}’ group?)").format(uf=uf)
                log.debug(deja)
                errorlabel['text'] = deja
                return
            for group in groupsselected:
                if group in self.analysis.sensesbygroup: #selected ones only
                    log.debug(_("Changing values from {group} to {uf} for the "
                            "following sense.ids: {ids}").format(group=group,uf=uf,
                            ids=[i.id for i in self.analysis.sensesbygroup[group]]))
                    for sense in self.analysis.sensesbygroup[group]:
                        sense.uftonevalue(uf)
            self.maybewrite()
            self.ui.runwindow.on_quit()
            self.program.status.last('joinUF',update=True)
            self.tonegroupsjoinrename() #call again, in case needed
        self.makeanalysis()
        def redo(timestamps=_("By manual request")):
            with self.waiting(_("Redoing Tone Analysis")+'\n'+timestamps):
                self.analysis.do()
            # self.ui.runwindow.on_quit()
            self.tonegroupsjoinrename(redo=True) #call again, in case needed
        def done():
            self.ui.runwindow.on_quit()
        ps=kwargs.get('ps',self.program.slices.ps())
        profile=kwargs.get('profile',self.program.slices.profile())
        analysisOK,joinedsince,timestamps=self.program.status.isanalysisOK(**kwargs) #Should specify which lasts...
        if not analysisOK:
            if not kwargs.get('redo'):
                #otherwise, the user will almost certainly be upset to have to do it later
                redo(timestamps)
            else:
                txt=_("The analysis still isn’t OK after retrying; "
                        "Check your settings and try again (e.g., "
                        "{ps} {profile} checks: {checks})").format(ps=ps, profile=profile, checks=self.program.status.checks())
                ErrorNotice(txt,wait=True,parent=self)
            return
        self.ui.getrunwindow(msg=_("Preparing to join draft underlying form groups"
                                "")+'\n'+timestamps)
        self.update()
        title=_("Join/Rename Draft Underlying {ps}-{profile} tone groups").format(
                                                        ps=ps,profile=profile)
        self.ui.runwindow.title(title)
        padx=50
        pady=10
        rwrow=gprow=qrow=0
        t=ui.Label(self.ui.runwindow.frame,text=title,font='title')
        t.grid(row=rwrow,column=0,sticky='ew')
        redotext=_("Redo the analysis;\nstart these groups over")
        text=_("This page allows you to join the {ps}-{profile} draft underlying tone "
                "groups created for you by {program}, \nwhich are almost certainly "
                "too small for you. \nLooking at a draft report, and making "
                "your own judgement about which groups belong together, select "
                "all the groups that belong together in one group, and "
                "give that new group "
                "a name. You can then repeat this for other groups "
                "that should be joined. \nIf for any reason you want to undo "
                "the groups you create here, you can start over with an new "
                "analysis by pressing the ‘{redo}’ button. \nOtherwise, these "
                "joined groups will be reflected in reports until you sort "
                "more data.").format(ps=ps,profile=profile,program=self.program.name,
                                                redo=redotext.replace('\n',' '))
        rwrow+=1
        i=ui.Label(self.ui.runwindow.frame,text=text,
                    row=rwrow,column=0,sticky='ew')
        i.wrap()
        ui.Button(self.ui.runwindow.frame,text=redotext, cmd=redo,
                    row=rwrow,column=1,sticky='ew')
        rwrow+=1
        qframe=ui.Frame(self.ui.runwindow.frame)
        qframe.grid(row=rwrow,column=0,sticky='ew')
        text=_("What do you want to call this UF tone group for {ps}-{profile} words?"
                "").format(ps=ps,profile=profile)
        qrow+=1
        q=ui.Label(qframe,text=text,
                    row=qrow,column=0,sticky='ew',pady=20
                    )
        q.wrap()
        named=ui.StringVar() #store the new name here
        namefield = ui.EntryField(qframe,text=named)
        namefield.grid(row=qrow,column=1)
        namefield.bind('<Key>', clearerror)
        errorlabel=ui.Label(qframe,text='',fg='red')
        errorlabel.grid(row=qrow,column=2,sticky='ew',pady=20)
        text=_("Select the groups below that you want in this {ps} group, then "
                "click ==>").format(ps=ps)
        qrow+=1
        d=ui.Label(qframe,text=text)
        d.grid(row=qrow,column=0,sticky='ew',pady=20)
        sub_btn=ui.Button(qframe,text = _("OK"), command = submitform, anchor ='c')
        sub_btn.grid(row=qrow,column=1,sticky='w')
        done_btn=ui.Button(qframe,text = _("Done —no change"), command = done,
                                                                    anchor ='c')
        done_btn.grid(row=qrow,column=2,sticky='w')
        groupvars=list()
        rwrow+=1
        scroll=ui.ScrollingFrame(self.ui.runwindow.frame)
        scroll.grid(row=rwrow,column=0,sticky='ew')
        self.analysis.donoUFanalysis()
        nheaders=0
        if not self.analysis.orderedUFs:
            self.ui.runwindow.waitdone()
            self.ui.runwindow.on_quit()
            ErrorNotice(title=_("No draft UF groups found for {ps} words!"
                                "").format(ps=ps),
                        text=_("You don’t seem to have any analyzed {ps} groups "
                        "to join/rename. Have you done a tone analyis for {ps} "
                        "words?").format(ps=ps)
                        )
            return
        # ufgroups= # order by structured groups? Store this somewhere?
        for group in self.analysis.orderedUFs: #make a variable and button to select
            idn=self.analysis.orderedUFs.index(group)
            if idn % 5 == 0: #every five rows
                col=1
                for check in self.analysis.orderedchecks:
                    col+=1
                    cbh=ui.Label(scroll.content, text=check, font='small')
                    cbh.grid(row=idn+nheaders,
                            column=col,sticky='ew')
                nheaders+=1
            groupvars.append(ui.StringVar())
            n=len(self.analysis.sensesbygroup[group])
            buttontext=f'{group} ({n})'
            cb=ui.CheckButton(scroll.content, text = buttontext,
                                variable = groupvars[idn],
                                onvalue = group, offvalue = 0,
                                )
            cb.grid(row=idn+nheaders,column=0,sticky='ew')
            # analysis.valuesbygroupcheck[group]:
            col=1
            for check in self.analysis.orderedchecks:
                col+=1
                if check in self.analysis.valuesbygroupcheck[group]:
                    cbl=ui.Label(scroll.content,
                        text=unlist(
                                self.analysis.valuesbygroupcheck[group][check]
                                    )
                            )
                    cbl.grid(row=idn+nheaders,column=col,sticky='ew')
        scroll.reflow()  # grow canvas to cover all the group rows just built
        self.ui.runwindow.waitdone()
        # runwindow is created withdrawn; waitdone only reveals it when a
        # thenshow wait dialog ran (mature-repo path). Reveal explicitly, or
        # this waits forever on an invisible window.
        self.ui.runwindow.deiconify()
        self.ui.runwindow.wait_window(scroll)
    def __init__(self, program, **kwargs):
        super().__init__(program=program, **kwargs)
class RecordCitation(Record,Segments,Task):
    def tooltip(self):
        return _("This task helps you record words in isolation forms.")
    def dobuttonkwargs(self):
        return {'text':_("Record Dictionary Words"),
                'fn':self.showentryformstorecord,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['WordRec'],
                'sticky':'ew'
                }
    tasktitle = "Record Words" #Citation Forms
    taskicon = 'iconWordRec'
    is_record_task=True
    def __init__(self, program, **kwargs): #frame, filename=None
        super().__init__(program=program, **kwargs)
class RecordCitationT(Record,Tone,Task):
    def tooltip(self):
        return _("This task helps you record words in tone frames, in citation form.")
    def dobuttonkwargs(self):
        return {'text':_("Record Words in Tone Frames"),
                'fn':self.showtonegroupexs,
                'font':'title',
                'compound':'top', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['TRec'],
                'sticky':'ew'
                }
    taskicon = 'iconTRec'
    tasktitle = "Record Tone" #Citation Form Sorting in Tone Frames
    def __init__(self, program, **kwargs): #frame, filename=None
        super().__init__(program=program, **kwargs)
class ReportCitation(Report,Segments,Task):
    """docstring for ReportCitation."""
    tasktitle = "Alphabet Report (Not background)" # on One Data Slice
    taskicon = 'iconReport'
    report_image = 'Report'
    def tooltip(self):
        return _("This report gives you reports for one lexical "
                "category, in one syllable profile. \nIt does "
                "one of three sets of reports: \n- Vowel, \n- Consonant, or "
                "\n- Consonant-Vowel Correspondence")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom',
                'image':self.program.theme.photo[self.report_image],
                'sticky':'ew'
                }
    def runcheck(self):
        """This needs to get stripped down and updated for just this check"""
        self.program.settings.storesettingsfile()
        t=(_('Run Check'))
        log.info("Running report...")
        log.info("Using these regexs: {rx}".format(rx=self.rxdict))
        # exit() #for testing
        i=0
        cvt=self.program.params.cvt()
        if cvt == 'T':
            w=self.program.taskchooser.getcvt()
            w.wait_window(w)
            cvt=self.program.params.cvt()
            if cvt == 'T':
                ErrorNotice(_("Pick Consonants, Vowels, or CV for this report."))
                return
        ps=self.program.slices.ps()
        if not ps:
            self.getps()
        check=self.program.params.check()
        profile=self.program.slices.profile()
        if not profile:
            self.program.ui_settings.getprofile() #the chooser dialog
            profile=self.program.slices.profile()
        if not profile or not ps:
            window=ui.Window(self)
            text=_('Error: please set Ps-Profile first! ({ps}/{check}/{profile})').format(
                                                     ps=ps,check=check,profile=profile)
            ui.Label(window,text=text).grid(column=0, row=i)
            i+=1
            return
        log.info(_('Ps-Profile-Check OK; doing getresults! ({ps}/{check}/{profile})').format(
                                                 ps=ps,check=check,profile=profile))
        self.getresults()
    def __init__(self, program, **kwargs): #frame, filename=None
        super().__init__(program=program, **kwargs)
        self.program.params.ftype('lc')
        self.do=self.getresults
        self.program.status.group(None) #default to reports with all groups
class ReportCitationBackground(Background,ReportCitation):
    tasktitle = "Alphabet Report" # on One Data Slice
class ReportCitationMulticheckBackground(Multicheck,Background,ReportCitation):
    tasktitle = "Alphabet Report (checks)" # on One Data Slice
class ReportCitationMultichecksliceBackground(Multicheckslice,Background,ReportCitation):
    tasktitle = "Alphabet Report (slices/checks)" # on One Data Slice
class ReportCitationByUF(ByUF,ReportCitation):
    tasktitle = "Alphabet Report by Tone group (not background)" # on One Data Slice
class ReportCitationByUFMulticheckBackground(Multicheck,Background,ReportCitationByUF):
    tasktitle = "Alphabet Report by Tone group (checks)" # on One Data Slice
class ReportCitationByUFMultichecksliceBackground(Multicheckslice,Background,ReportCitationByUF):
    tasktitle = "Alphabet Report by Tone Group (slices/checks)" # on One Data Slice
class ReportCitationByUFBackground(ByUF,ReportCitationBackground):
    tasktitle = "Alphabet Report by Tone group" # on One Data Slice
class ReportCitationMultislice(MultisliceS,ReportCitation):
    """docstring for ReportCitation."""
    tasktitle = "Multislice Alphabet Report" # on Citation Forms
    report_image = 'VCCVRepcomp'
    def __init__(self, program, **kwargs): #frame, filename=None
        super().__init__(program=program, **kwargs)
        self.cvtstodo=['V','C','CV']

class ReportConsultantCheck(Report,Tone,Task):
    """docstring for ReportCitationT."""
    tasktitle = "Consultant Check"
    taskicon = 'icontall'
    def tooltip(self):
        return _("This task automates work normally done before a consultant "
                "check: \n- reloads status data, and \n- runs comprehensive tone "
                "reports, \n  - by location and \n  - by lexeme sense.")
    def dobuttonkwargs(self):
        return {'text':'\n'.join([_("Start!"),_("Profiles first!")]),
                'fn':self.consultantcheck,
                # column=0,
                'font':'title',
                'compound':'bottom', #image bottom, left, right, or top of text
                'image':self.program.theme.photo['icontall'],
                'sticky':'ew'
                }

class ReportCitationT(Report,Tone,Task):
    """docstring for ReportCitationT."""
    tasktitle = "Tone Report (not backgrounded)"
    taskicon = 'iconTRep'
    do_not_show_cvt=True
    report_image = 'TRep'
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
    def dobuttonkwargs(self):
        return {'text':_("Report!"),
                'fn':self.do,
                'font':'title',
                'compound':'bottom',
                'image':self.program.theme.photo[self.report_image],
                'sticky':'ew'
                }
    def __init__(self, program, **kwargs):
        super().__init__(program=program, **kwargs)
        self.do=self.tonegroupreport
        self.bylocation=False
class ReportCitationTBackground(Background,ReportCitationT):
    tasktitle = "Tone Report"
    taskicon = 'iconTRep'
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames.")
class ReportCitationTL(ReportCitationT):
    """docstring for ReportCitationT."""
    tasktitle = "Tone Report (by frames, not backgrounded)"
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by frame.")
    def __init__(self, program, **kwargs):
        super().__init__(program=program, **kwargs)
        self.bylocation=True
class ReportCitationTLBackground(Background,ReportCitationTL):
    tasktitle = "Tone Report (by frames)"
    taskicon = 'iconTRep'
    def tooltip(self):
        return _("This report gives you report for one lexical "
                "category, in one syllable profile. \nIt does "
                "this for all data sorted in tone frames, organized by frame.")
class ReportCitationMultisliceT(MultisliceT,ReportCitationT):
    tasktitle = "Multislice Tone Report (not background)"
    taskicon = 'iconTRepcomp'
    report_image = 'TRepcomp'
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
class ReportCitationMultisliceTL(MultisliceT,ReportCitationTL):
    tasktitle = "Multislice Tone Report (not background)"
    taskicon = 'iconTRepcomp'
    report_image = 'TRepcomp'
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
class ReportCitationMultisliceTBackground(Background,ReportCitationMultisliceT):
    tasktitle = "Multislice Tone Report"
    taskicon = 'iconTRepcomp'
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
class ReportCitationMultisliceTLBackground(Background,ReportCitationMultisliceTL):
    tasktitle = "Multislice Tone Report (by location)"
    taskicon = 'iconTRepcomp'
    def tooltip(self):
        return _("This report gives you reports across multiple lexical "
                "categories, and across multiple syllable profiles. \nIt does "
                "this for all data sorted in tone frames, organized by word.")
