#!/usr/bin/env python3
# coding=UTF-8
from utilities import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import numpy
# import soundfile
import whisper
import torch
import datetime, copy
from data import whisper_codes_names
from data import ethnologue_macrolanguages_members
_MACRO_MEMBERS = ethnologue_macrolanguages_members.dict  # {macro: [member codes]}
WHISPER_SIZES=['tiny', 'base', 'small', 'medium', 'large-v1',
                'large-v2', 'large-v3', 'large']
# kwarg -> model repo, module-level so the draft-display filter can consult
# the user's selection before any model is loaded. NB return_ipa/show_tone
# are output-lane flags that alias a model repo, not model selections.
REPO_MODELNAMES={
                'neurlang':"neurlang/ipa-whisper-base",
                'return_ipa':"neurlang/ipa-whisper-base",
                'allosaurus':'allosaurus',
                'mms_all': "facebook/mms-1b-all",
                'mms_1107': "facebook/mms-1b-l1107",
                'mms_102': "facebook/mms-1b-fl102",
                'katyayego': "katyayego/Wav2Vec2Phoneme-CSfinetune",
                'show_tone': "katyayego/Wav2Vec2Phoneme-CSfinetune",
                'cherokee': "sil-ai/kent-cherokee",
                'zulgo': "sil-ai/kent-zulgo",
                'baffanji': "sil-ai/kent-bafanji",
                **{f'whisper-{i}':f'whisper-{i}' for i in WHISPER_SIZES},
            }
def mms_lang(code):
    """ISO 639-3 form of a raw language tag ('en' -> 'eng'); the raw code
    itself if the mapping fails."""
    if not code:
        return code
    try:
        import langcodes
        return langcodes.Language.get(code).to_alpha3() or code
    except Exception:
        return code
def sister_members(code):
    """Member languages of a macrolanguage (swa -> [swh, swc, …]); [] if the
    code is not a macrolanguage."""
    return list(_MACRO_MEMBERS.get(code, []) or [])
from transformers import pipeline
from huggingface_hub import try_to_load_from_cache, _CACHED_NO_EXIST
# from backend import langtags
device = "cuda:0" if torch.cuda.is_available() else "cpu"

class ASRtoText(object):
    def load_whisper(self,size='base'):
        repo=f"whisper-{size}"
        model_kwargs=copy.deepcopy(self.model_kwargs)
        try:
            model_kwargs['download_root']=model_kwargs.pop('cache_dir')
        except KeyError:
            pass #don't set root if no cache
        # openai-whisper's load_model accepts only (name, device,
        # download_root, in_memory); the shared ASR kwargs carry HF-pipeline
        # extras (dtype, …) that TypeError here (2026-07-13). Whitelist.
        model_kwargs={k:v for k,v in model_kwargs.items()
                      if k in ('download_root','in_memory')}
        self.models[repo]=whisper.load_model(size,
                                        device=device,
                                        **model_kwargs
                                        )
    def load_faster_whisper(self,model_id):
        """This isn't working yet"""
        """Faster Whisper, Whisper X, Distil-Whisper, and Whisper-Medusa"""
        from transformers import AutoModelForSpeechSeq2Seq,AutoProcessor
        from faster_whisper import WhisperModel,BatchedInferencePipeline
        repo=model_id.split('/')[0]
        for compute_type in ["float32","int8"]:
                self.models[f"{repo}_{compute_type}"]=WhisperModel(
                                                     model_id,
                                                    device=device,
                                                    cpu_threads=threads, #4 is default, 0 takes environmental variable OMP_NUM_THREADS
                                                    compute_type=compute_type,
                                                )
        print(self.model.__class__.__name__)
        print(self.model.model.__class__.__name__)
    def load_neurlang(self):
        modelname='neurlang/ipa-whisper-base'
        if modelname in self.models:
            return
        pipe=pipeline("automatic-speech-recognition",
                            model=modelname,
                            chunk_length_s=30,
                            device=device,
                            model_kwargs=self.model_kwargs
                            )
        pipe.model.config.forced_decoder_ids = None
        pipe.model.config.suppress_tokens = []
        pipe.model.generation_config.forced_decoder_ids = None
        pipe.model.generation_config._from_model_config = True
        self.model=pipe.model
        self.models[modelname]=pipe
    def load_ctc_model(self,model):
        if model in self.models:
            log.info(f"Model {model} is already loaded.")
            return
        self.repo=model
        self.models[self.repo]=pipeline("automatic-speech-recognition",
                                    model=model,
                                    device=device,
                                    model_kwargs=self.model_kwargs
                                )
    def load_other_models(self):
        for model in [
            "excalibur12/wav2vec2-large-lv60_phoneme-timit_english_timit-4k_simplified",
            "Bluecast/wav2vec2-Phoneme",
            "ctaguchi/wav2vec2-large-xlsr-japlmthufielta-ipa1000-ns",
            "MultiBridge/wav2vec-LnNor-IPA-ft",
        ]:
            self.load_ctc_model(model)
    def load_katyayego(self,just_tone=False):
        model="katyayego/Wav2Vec2Phoneme-CSfinetune"
        self.load_ctc_model(model)
    def _mms_lang(self,code=None):
        """MMS adapters are keyed by ISO 639-3 (e.g. 'eng'), but sister-language
        defaults arrive as raw tags (e.g. 'en'). Map to alpha3 so the adapter
        actually loads; fall back to the raw code if the mapping fails."""
        code=self.sister_language if code is None else code
        return mms_lang(code)
    def load_ctc_adaptor(self):
        """This doesn't impact self.model"""
        if not hasattr(self,'_adapter_failures'):
            self._adapter_failures=set()
        code=self._mms_lang()
        for repo in [i for i in self.models
                        if i in self.language_adaptor_models]:
            try:
                # log.info("Currently using "
                #     f"{self.models[repo].model.target_lang} adaptor")
                self.models[repo].model.load_adapter(code,
                                                    **self.model_kwargs)
                self.models[repo].tokenizer.set_target_lang(code)
                # print(f"Loaded {repo} model {code} adaptor")
            except OSError as e:
                # Don't swallow silently: a code with no adapter (e.g. 'swa' —
                # MMS uses 'swh') otherwise "succeeds" in ~0s producing nothing.
                # Record + warn so preflight_sister_languages can report it and
                # the bulk sweep can skip it.
                self._adapter_failures.add((repo,self.sister_language))
                arrow=f" (→{code})" if code!=self.sister_language else ""
                # An unsupported language (no MMS adapter) — macro or member or
                # typo — is routine: log and move on, don't nag every run. The
                # once-per-run preflight summary is where they're all reported.
                if self._macro_covered_by_members(self.sister_language):
                    log.info(f"No '{self.sister_language}'{arrow} MMS adapter for "
                             f"{repo} (macrolanguage); its members cover it.")
                else:
                    log.info(f"No '{self.sister_language}'{arrow} MMS adapter for "
                             f"{repo}; skipping this language.")
    def load_allosaurus(self):
        from allosaurus.app import read_recognizer
        repo='allosaurus'
        self.models[repo]=read_recognizer()
    def load_postprocess_by_kwarg(self,**kwargs):
        import re
        if not kwargs:
            log.info("not reloading postprocess_by_kwarg")
            return
        log.info("Running load_postprocess_by_kwarg")
        self.postprocess_dicts = [] #A list of sequential transformations
        if kwargs.get('simplify_unusual_IPA'):
            self.postprocess_dicts.append({
                                    "ʌ":"ə",
                                    "ɻ̩":"r",
                                    "ɹ":"r",
                                    "ɚ":"er",
                                    "ʰ":"",
                                })
        if kwargs.get('simplify_stress'):
            self.postprocess_dicts.append({
                                            "ˈ":"",
                                            "ˌ":"",
                            })
        if kwargs.get('simplify_stops'):
            self.postprocess_dicts.append({
                                            "p̚":"p",
                                            # "tp̚":"p",
                                            # "k":"p",
                                            "pʰ":"p",
                                            "tʰ":"t",
                                            "kʰ":"k",
                                            "b̥":"b",
                                            "ɾ":"d",
                                            "k̟":"k",
                            })
        if kwargs.get('simplify_affricates'):
            self.postprocess_dicts.append({
                                            "k͡p":"kp",
                                            # "gk͡b":"gb",
                                            "t͡ɕ":"tsh",
                                            "t͡s":"ts",
                                            "tʃ":"tsh",
                                            "dʒ":"j"
                            })
        if kwargs.get('simplify_IPA_fricatives'):
            self.postprocess_dicts.append({
                                            "ɕ":"sh",
                                            "θ":"th",
                                            "ð":"th",
                                            "ʂ":"sh",
                                            "ʃ":"sh",
                                            "ʒ":"zh",
                                            "ʐ":"zh",
                            })
        if kwargs.get('simplify_offglides'):
            self.postprocess_dicts.append({
                                "ʲ":"",
                                "ʷ":"",
                            })
        else:
            self.postprocess_dicts.append({ #don't show tiny letters in any case
                                "ʲ":"y",
                                "ʷ":"w",
                            })
        if kwargs.get('simplify_dipthongs'):
            self.postprocess_dicts.append({
                                "uə":"u",
                                # "aʊ":"a",
                                "oʊ":"o",
                                "ow":"o",
                            })
        if kwargs.get('seven_vowels'):
            self.postprocess_dicts.append({
                                "ɪ":"i",
                                "ʌ":"e",
                                "ə":"e",
                                "ɜ":"e",
                                "e̞":"ɛ",
                                "ʊ":"u",
                                "o̞":"ɔ",
                                "ä":"a",
                                "ɑ":"a",
                                "æ":"a",
                            })
        if kwargs.get('five_vowels'):
            self.postprocess_dicts.append({
                                "ɪ":"i",
                                "ʌ":"e",
                                "ə":"e",
                                "e̞":"e",
                                "ɛ":"e",
                                "ɜ":"e",
                                "ʊ":"u",
                                "o̞":"o",
                                "ɔ":"o",
                                "ä":"a",
                                "ɑ":"a",
                                "æ":"a",
                            })
        if kwargs.get('barred_vowels'):
            self.postprocess_dicts.append({
                "ʊ":"ʉ",
                "ɪ":"ɨ",
            })
        if kwargs.get('simplify_nasals'):
            self.postprocess_dicts.append({
                                "ŋ":"n",
                                "ɴ":"n",
                            })
        if kwargs.get('simplify_length'):
            self.postprocess_dicts.append({
                                "ː": "",
                            })
        else:
            self.postprocess_dicts.append({ #don't leave ː in any case
                                "iː": "ii",
                                "uː": "uu",
                                "aː": "aa",
                                "ɑː": "ɑɑ",
                                "æː": "ææ",
                                "oː": "oo",
                                "ɔː": "ɔɔ",
                                "o̞ː": "o̞o̞",
                                "e̞ː": "e̞e̞",
                                "ʊː": "ʊʊ",
                                "əː": "əə",
                                "ʌː": "ʌʌ",
                            })
        """This regex just looks for each key; replacement is by dict value"""
        self.postprocess_regexes = [re.compile('|'.join(map(re.escape,i)))
                                        for i in self.postprocess_dicts]
        log.info(f"ASR postprocess reloaded ({kwargs})")
    def _postprocess(self):
        in_process=self.raw
        for n,r in enumerate(self.postprocess_regexes):
            in_process=r.sub(lambda match:
                        self.postprocess_dicts[n][match.group(0)], in_process)
        return in_process
    def get_tone(self):
        tonenumbers=[i for i in self.ipa if i.isdigit()]
        if not tonenumbers:
            # log.info(f"No tone numbers in '{self.ipa}' ({self.repo}); "
            #             "skipping tone.")
            return
        # print("Getting Tone")
        self.tone_melody=''.join(tonenumbers)
        print(f"{self.ipa=} {self.tone_melody=}")
        self.convert_tone_numbers()
    def postprocess(self):
        if self.repo in self.models_with_spaced_phones:
            self.ipa=''.join(self.raw.split(' '))
            if self.show_tone and self.repo in self.models_that_give_tone:
                #For now, just one. if more, prioritize
                self.get_tone() #depends on IPA
            return ''.join(self._postprocess().split(' '))
        else:
            return self._postprocess()
    def convert_tone_numbers(self):
        #These are all nonbreaking spaces!
        d=str.maketrans({'5': '˩˩ ',
                        '4': '˨˨ ',
                        '3': '˧˧ ',
                        '2': '˦˦ ',
                        '1': '˥˥ ',
                        })
        if self.tone_melody:
            self.tone_melody=f"[{self.tone_melody.translate(d).strip(' ')}]"
    def do_not_return_data(self):
        if self.show_tone and self.repo in self.models_that_give_tone:
            self.get_tone()
        if self.return_ipa and self.repo in self.models_that_give_IPA:
            log.info(f"Returning just IPA for {self.repo}")
            return self.repo,'',self.ipa if self.ipa else ''
        return '','',''
    def is_any_whisper(self):
        if hasattr(self.model,'model'):
            if 'Whisper' in self.model.model.__class__.__name__:
                return True
        elif 'Whisper' in self.model.__class__.__name__:
            return True
    def return_data(self):
        if not self.sister_language and self.lang: #returned from lang ID
            repo=f"{self.repo} ({self.lang}?)"
        elif (self.sister_language and
                self.is_any_whisper()) or 'facebook/' in self.repo:
            """I need to read this, not report it, for those cases where
            an adaptor wasn't found"""
            # log.info("Currently using "
            #         f"{self.models[self.repo].model.target_lang} adaptor")
            # log.info(f"{self.model.model.target_lang=}")
            # log.info(f"{self.lang=}")
            # log.info(f"{self.sister_language=}")
            try:
                repo=f"{self.repo} ({self.model.model.target_lang}!)"
            except AttributeError:
                if self.sister_language == self.lang or (self.sister_language
                        in whisper_codes_names.by_iso and
                        whisper_codes_names.by_iso[self.sister_language][0]):
                    repo=f"{self.repo} ({self.sister_language}!)"
                else:
                    repo=f"{self.repo} ({self.sister_language}!={self.lang}!)"
        else:
            repo=self.repo
        return repo,self.postprocess(),self.ipa if self.ipa else ''
    def inferall_lang_spec(self,input_file):
        models=[i for i in self.models if i in self.language_specifiable_models]
        log.info(f"Going to inferall on {len(models)} language-specific models")
        for self.repo in models:
            self.model=self.models[self.repo]
            yield self.infer(input_file)
    def inferall_lang_nonspec(self,input_file):
        models=[i for i in self.models
                    if i not in self.language_specifiable_models]
        log.info(f"Going to inferall on {len(models)} language "
                    "non-specific models")
        for self.repo in models:
            self.model=self.models[self.repo]
            yield self.infer(input_file)
    def inferall(self,input_file):
        log.info(f"Going to inferall on all {len(self.models)} models")
        for self.repo in self.models:
            self.model=self.models[self.repo]
            yield self.infer(input_file)
    def infer(self,input_file):
        self.raw=self.ipa=''
        if self.model.__class__.__name__ in ['Recognizer']:
            self.repo="allosaurus"
            self.raw=self.ipa=self.model.recognize(input_file)
            self.lang=None
        elif self.model.__class__.__name__ in ['Whisper']:
            kwargs={'word_timestamps':True}
            log.info(f"self.sister_language: {self.sister_language}")
            if self.sister_language in whisper_codes_names.by_iso:
                kwargs['language']=whisper_codes_names.by_iso[self.sister_language][0]
            transcription = self.model.transcribe(input_file, **kwargs)
            self.lang=transcription['language']
            """This is a list of dictionary items, with start and end keys,
            among others. This should be able to draft utterance boundaries"""
            timing=transcription['segments']
            transcription = transcription['text']
        elif self.model.__class__.__name__ in ['WhisperModel']:
            transcription=''
            kwargs={'word_timestamps':True}
            if self.sister_language:
                kwargs['language']=self.sister_language
            segments, info = self.model.transcribe(input_file, **kwargs)
            for s in segments:
                print(f"[{s.start:.2f}s -> {s.end:.2f}s] {s.text}")
                self.raw+=s.text
                for word in s.words:
                    print(f"  [{word.start:.2f}s -> {word.end:.2f}s] {word.word}")
            self.ipa=self.raw
            self.lang=info.language
        elif self.model.__class__.__name__ in [
                                        'AutomaticSpeechRecognitionPipeline'
                                            ]:
            _slang=self._mms_lang()
            if (self.sister_language and 'facebook/' in self.repo and
            self.model.model.target_lang != _slang):
                log.info(f"Model lang {self.model.model.target_lang} != "
                    f"sister lang {self.sister_language} (→{_slang}); "
                    "not inferring.")
                return self.do_not_return_data()
            self.lang=None
            # data,samplerate=soundfile.read(input_file)
            # self.raw = self.model(data, batch_size=8)['text']
            #above two or below
            self.raw = self.model(input_file, batch_size=8)['text']
            if self.repo in self.models_that_give_IPA:
                self.ipa=self.raw
        else:
            print(f"Model type {self.model.__class__.__name__} not found.")
            #This will die now.
        log.info(f"ready to return (or not) for {self.repo} {self.raw=}")
        if self.repo in self.do_not_return:
            return self.do_not_return_data()
        else:
            return self.return_data()
    def set_do_not_return(self):
        """Models whose output to suppress given the current show_tone/return_ipa
        flags. Extracted from get_transcriptions so the bulk path shares it."""
        self.do_not_return={i for i in self.models_that_give_tone
                            for k,v in self.repo_modelnames.items()
                            if not getattr(self,k)
                            and getattr(self,'show_tone')
                            and v == i and k != 'show_tone'
                        }
        self.do_not_return|={i for i in self.models_that_give_IPA
                            for k,v in self.repo_modelnames.items()
                            if not getattr(self,k)
                            and v == i
                        }
    def _sister_members(self, code):
        """Member languages of a macrolanguage (swa -> [swh, swc, …]); [] if the
        code is not a macrolanguage."""
        return sister_members(code)
    def effective_sister_languages(self):
        """Sister languages to actually transcribe: each requested code PLUS, for
        any macrolanguage (e.g. swa), ALL its member languages (swh, swc, …). MMS
        keys individual codes, so a macro alone produces nothing — its members
        provide the coverage, and if swa is asked for, both swh AND swc run."""
        out, seen = [], set()
        for code in (self.sister_languages or []):
            for c in [code] + self._sister_members(code):
                if c and c not in seen:
                    seen.add(c); out.append(c)
        return out
    def _macro_covered_by_members(self, code):
        """True if `code` is a macrolanguage whose member(s) are also being
        transcribed — so its own missing MMS adapter is harmless (don't warn)."""
        members = self._sister_members(code)
        return bool(members and set(members) & set(self.effective_sister_languages()))
    def preflight_sister_languages(self):
        """Validate the EFFECTIVE sister-language codes (macros expanded to their
        members) against available MMS adapters before a bulk run. A macrolanguage
        with no adapter is NOT reported unusable when its members cover it — its
        absence is expected (MMS keys individual codes). Returns (usable, unusable);
        requires MMS models loaded (else all pass, moot)."""
        usable,unusable=set(),set()
        for code in sorted(set(self.effective_sister_languages())):
            self.sister_language=code
            self._adapter_failures=set()
            self.load_ctc_adaptor()
            if self._adapter_failures:
                if not self._macro_covered_by_members(code):
                    unusable.add(code)
            else:
                usable.add(code)
        self.sister_language=None
        if unusable:
            log.info(f"Sister-language codes with no MMS adapter (skipped): "
                     f"{sorted(unusable)}. Usable: {sorted(usable)}.")
        return usable,unusable
    def transcribe_files_bulk(self,files,progress_cb=None,should_cancel=None,
                              checkpoint_cb=None,checkpoint_every=100,prior=None,
                              keep_keys=None,usable_langs=None,dead_after=10,
                              plan_cb=None,unit_done_cb=None):
        """Stage-2 MODEL-MAJOR, LANGUAGE-MAJOR sweep (asr_bulk_transcription_design.md).
        Each model runs across ALL files before the next; for MMS (adapter)
        models each sister language's adapter loads ONCE then sweeps every file —
        collapsing the per-file adapter thrash of the file-major live path.
        Models persist in self.models between files (loaded once).

        Returns {file: (transcriptions, ipa)} with {repo: text} dicts, for the
        caller to persist via Form.persist_drafts (both stages write identical
        annotations, so the selector can't tell which produced them).

        progress_cb(model=,lang=,file_idx=,nfiles=,unit_idx=,nunits=) fires per
        file (throttle in the caller); should_cancel() is polled to abort early.
        checkpoint_cb(snapshot) fires after each unit with a COPY of the results
        so far — the caller persists it so a crash/power-cut mid-run keeps what's
        done (resume just fills gaps; both are idempotent).
        prior={file: set of decorated repo keys already stored for that file's
        CURRENT md5}. A (file, model[/lang]) whose key is already present is
        skipped (gap-fill) — so adding a model only runs the new one, and resume
        skips finished work. Whisper's key depends on the DETECTED language and
        can't be predicted, so those are never skipped.
        dead_after: if a model/language unit's first N actual inferences ALL
        come back empty (no text, no IPA), abandon the rest of that unit and
        move on — a dead model shouldn't chunk through the whole wordlist
        producing ''. 0/None disables the bail-out.
        plan_cb(names) fires once with the final pruned unit list (which
        model/language sweeps WILL run); unit_done_cb(name) fires as each
        completes — so the caller can persist to-do/done visibly
        (audio.json asr_in_process)."""
        progress_cb=progress_cb or (lambda **k: None)
        should_cancel=should_cancel or (lambda: False)
        prior=prior or {}
        self.set_do_not_return()
        files=list(files)
        results={f:({},{}) for f in files}
        models=list(self.models)
        spec=[m for m in models if m in self.language_specifiable_models]
        nonspec=[m for m in models if m not in self.language_specifiable_models]
        langs=sorted(set(self.effective_sister_languages()))  # macros -> members
        # one "unit" == one (model) or (model,language) sweep over all files
        units=[(m,None) for m in nonspec]+[(m,l) for m in spec
                                            for l in (langs or [None])]
        processed=[0]   # files inferred across all units, for the N-file cadence
        touched=set()   # recordings we actually ran ASR on this run (the denom)
        def snapshot():
            # a COPY of results-so-far; made on THIS (worker) thread, so no race
            return {f:(dict(tx),dict(ip))
                    for f,(tx,ip) in results.items() if tx or ip}
        def expected_key(repo,lang):
            # the decorated draft key this (repo,lang) WOULD store, when it's
            # predictable — so we can gap-fill/skip. None => unpredictable
            # (whisper decorates by DETECTED language), so never skip those.
            if repo not in self.language_specifiable_models:
                return repo                       # non-language model: bare key
            if repo in self.language_adaptor_models and lang:
                return f"{repo} ({self._mms_lang(lang)}!)"   # MMS: adapter lang
            return None
        def sweep(repo,lang,unit_idx):
            self.repo=repo
            self.model=self.models[repo]
            self.sister_language=lang
            unit_key=expected_key(repo,lang)
            # 'top models only': skip a predictable unit whose key isn't in the
            # keep set. Whisper's key is unpredictable (detected lang) so it runs
            # and is filtered on output below.
            if keep_keys is not None and unit_key and unit_key not in keep_keys:
                return True
            def done_already(f):
                return bool(unit_key) and unit_key in prior.get(f,())
            if unit_key and all(done_already(f) for f in files):
                return True   # whole unit already stored — don't even load adapter
            if repo in self.language_adaptor_models and lang:
                self.load_ctc_adaptor()  # switch adapter ONCE for this language
                # No adapter for this language (unsupported macro/member/typo) —
                # skip its dead unit (logged above) rather than infer nothing over
                # every file.
                if (repo,lang) in getattr(self,'_adapter_failures',set()):
                    return True
            inferred=0        # real inferences this unit (gap-fill skips don't count)
            produced=False    # any non-empty output yet this unit?
            for i,f in enumerate(files):
                if should_cancel():
                    return False
                if done_already(f):
                    progress_cb(model=repo,lang=lang,file_idx=i,nfiles=len(files),
                                unit_idx=unit_idx,nunits=len(units))
                    continue   # gap-fill: this model already drafted this file
                try:
                    r,text,ipa=self.infer(str(f))  # pipeline wants a path str
                except Exception as e:
                    log.error(f"bulk infer failed on '{f}' with {repo}"
                                f"{'/'+lang if lang else ''}: {e}")
                    r,text,ipa=None,'',''
                touched.add(f)   # inference actually ran on this recording
                inferred+=1
                if (text and text.strip()) or (ipa and ipa.strip()):
                    produced=True
                elif dead_after and inferred>=dead_after and not produced:
                    # dead model/adapter: first N inferences all empty — don't
                    # burn CPU on the rest of the wordlist for nothing
                    log.warning(f"bulk ASR: {repo}{'/'+lang if lang else ''} "
                                f"produced no output for its first {inferred} "
                                f"recordings; skipping the rest of this model")
                    return True
                tx,ip=results[f]
                if r and (keep_keys is None or r in keep_keys):
                    if text: tx[r]=text        # output filter (also catches whisper)
                    if ipa: ip[r]=ipa
                processed[0]+=1
                # checkpoint every N files so a crash keeps recent work, not just
                # once per (whole-wordlist) unit
                if (checkpoint_cb and checkpoint_every
                        and processed[0]%checkpoint_every==0):
                    checkpoint_cb(snapshot())
                progress_cb(model=repo,lang=lang,file_idx=i,nfiles=len(files),
                            unit_idx=unit_idx,nunits=len(units))
            return True
        # Show a correct "of N": pre-drop units that WON'T run — top-filtered,
        # unsupported language (per preflight's usable set), or already fully done
        # (gap-fill) — so nunits reflects what will actually be transcribed.
        def _will_run(repo,lang):
            # Keep every model/language that STRUCTURALLY runs — the top-models
            # set and supported languages. Gap-fill (already-transcribed
            # recordings) is a per-recording skip INSIDE the sweep, so it must NOT
            # drop a whole model from the count (that made it show "1" not "16").
            key=expected_key(repo,lang)
            if keep_keys is not None and key and key not in keep_keys:
                return False
            if (repo in self.language_adaptor_models and lang
                    and usable_langs is not None and lang not in usable_langs):
                return False
            return True
        units=[u for u in units if _will_run(*u)]
        def unit_name(repo,lang):
            return f"{repo} ({lang})" if lang else repo
        if plan_cb:
            plan_cb([unit_name(*u) for u in units])
        for unit_idx,(repo,lang) in enumerate(units):
            if should_cancel():
                break
            # announce the unit so the display advances through ALL units — a unit
            # fully skipped by gap-fill wouldn't otherwise update progress and the
            # bar would look stuck
            progress_cb(model=repo,lang=lang,file_idx=0,nfiles=len(files),
                        unit_idx=unit_idx,nunits=len(units))
            done=sweep(repo,lang,unit_idx)
            if checkpoint_cb:
                checkpoint_cb(snapshot())   # flush this unit's tail (< N files)
            if not done:
                break
            if unit_done_cb:
                unit_done_cb(unit_name(repo,lang))
        stuck=[f for f in touched if not (results[f][0] or results[f][1])]
        if stuck:
            log.info("bulk ASR: %d recording(s) ran but produced NO draft "
                     "(empty/corrupt/silent audio?): %s",
                     len(stuck), [str(f) for f in stuck])
        self._bulk_touched=touched   # how many recordings this run actually processed
        return results
    def get_transcriptions(self,file):
        """If language(s) given, this currently iterates over languages (or not). Should probably rethink."""
        def add_values_no_dup(x,y,z):
            if not x and not y and not z:
                return
            if self.repo in x:
                text="OK"
            else:
                text=f"!= '{self.repo}'!"
            log.info(f"inferall iteration ({x} {text}: {z if z else y})")
            if x in self.transcriptions or x in self.transcriptions_ipa:
                tx=self.transcriptions[x] if x in self.transcriptions else None
                ix=self.transcriptions_ipa[x] if x in self.transcriptions_ipa else None
                log.error(f"repo {x} seems to have data again? "
                            f"({y},{z}, after {tx},{ix})")
                exit()
            if y:
                self.transcriptions[x]=y
            if z:
                self.transcriptions_ipa[x]=z
        self.transcriptions={}
        self.transcriptions_ipa={}
        self.set_do_not_return()
        # log.info(f"{self.repo_modelnames=}")
        # log.info(f"{self.models_that_give_IPA=}")
        # log.info(f"{self.do_not_return=}")
        # log.info(f"{self.models.keys()=}")
        self.error_text=None # reset for this file, attempt
        try:
            assert self.sister_languages,"No Sister Language(s) Specified"
            self.sister_language=None
            for x,y,z in self.inferall_lang_nonspec(file):
                add_values_no_dup(x,y,z)
            for self.sister_language in set(self.effective_sister_languages()):
                adaptors=[v.model.target_lang for k,v in self.models.items()
                                        if k in self.language_adaptor_models]
                if set(adaptors)-set(self.sister_language):
                    self.load_ctc_adaptor()
                for x,y,z in self.inferall_lang_spec(file):
                    add_values_no_dup(x,y,z)
                log.info(f"Got transcriptions for {self.sister_language}")
        except (KeyError,AssertionError) as e:
            log.info(f"Not using language specific transcription ({e})")
            self.sister_language=None
            try:
                for x,y,z in self.inferall(file):
                    add_values_no_dup(x,y,z)
            except ValueError as e:
                if 'fmpeg' in str(e):
                    self.error_text=str(e)
                    return
                else:
                    raise e
        except ValueError as e:
            if 'fmpeg' in str(e):
                self.error_text=str(e)
                return
            else:
                raise e
        # log.info(f"self.transcriptions: {self.transcriptions}")
        # log.info(f"self.transcriptions_ipa: {self.transcriptions_ipa}")
    def make_repo_dicts(self):
        self.repo_modelnames=dict(REPO_MODELNAMES) #module-level, incl. whisper
        whisper_methods={f'whisper-{i}':lambda x=i: self.load_whisper(size=x)
                                for i in self.whisper_sizes}
        ctc_methods={i:lambda x=i:self.load_ctc_model(x) for i in [
                                        "facebook/mms-1b-all",
                                        "facebook/mms-1b-l1107",
                                        "facebook/mms-1b-fl102",
                                        "katyayego/Wav2Vec2Phoneme-CSfinetune"
                                                    ]
                    }
        self.repo_methods={
            'neurlang/ipa-whisper-base': self.load_neurlang,
            'allosaurus': self.load_allosaurus
        }
        self.repo_methods.update(whisper_methods)
        self.repo_methods.update(ctc_methods)
    def unload(self,repo):
        if repo in self.models:
            del self.models[repo]
            log.info(f"ASR model {repo} unloaded.")
    def is_cached(self,model_name):
        location=try_to_load_from_cache(model_name,
                                    self.cache_dir,
                                repo_type='model' #by default
                            )
        if location is _CACHED_NO_EXIST:
            log.error(f"The model {model_name} doesn't seem to exist")
        else:
            return location
    def load_models_by_kwarg(self,**kwargs):
        if not kwargs: #we are only making changes here, maybe none
            log.info("not reloading models_by_kwarg")
            return
        log.info("Running load_models_by_kwarg")
        kwargs_that_give_tone=[k for k,v in self.repo_modelnames.items()
                                    if v in self.models_that_give_tone]
        tone_should_be=getattr(self,'show_tone') or kwargs.get('show_tone')
        kwargs_that_give_IPA=[k for k,v in self.repo_modelnames.items()
                                    if v in self.models_that_give_IPA]
        ipa_kwargs_to_remain=[i for i in kwargs_that_give_IPA
                            if kwargs.get(i,getattr(self,i))]
        ipa_keep_at_least=['neurlang']
        # log.info(f"{ipa_kwargs_to_remain=}")
        # log.info(f"{kwargs_that_give_IPA=}")
        # log.info(f"{ipa_keep_at_least=}")
        # log.info(f"{self.return_ipa=}")
        if self.return_ipa and not ipa_kwargs_to_remain:
            kwargs['return_ipa']=True
        log.info(f"{kwargs=}")
        to_do=[k for k,v in kwargs.items() if k in self.repo_modelnames and v]
        to_undo=[k for k,v in kwargs.items()
                                if k in self.repo_modelnames and not v]
        for k,v in kwargs.items():
            if k in self.repo_modelnames: #these are all we do here
                if v:
                    self.repo_methods[self.repo_modelnames[k]]()
                    log.info(f"ASR model {k} loaded.")
                elif self.return_ipa and k in kwargs_that_give_IPA:
                    log.info(f"ASR model {k} not unloaded (to preserve IPA).")
                elif tone_should_be and k in kwargs_that_give_tone:
                    log.info(f"ASR model {k} not unloaded (to preserve tone).")
                else:
                    self.unload(self.repo_modelnames[k])
            if k not in ['return_ipa']: #don't mess with this one
                setattr(self,k,v)
        log.info(f"ASR models reloaded ({kwargs})")
    def complete_kwargs_w_defaults(self,**kwargs):
        self.postprocess_kwargs=[
            'simplify_unusual_IPA',
            'simplify_stress',
            'simplify_stops',
            'simplify_affricates',
            'simplify_IPA_fricatives',
            'simplify_offglides',
            'barred_vowels',
            'simplify_dipthongs',
            'five_vowels',
            'seven_vowels',
            'simplify_nasals',
            'simplify_length',
        ]
        self.do_by_default=[
            'simplify_unusual_IPA',
            'simplify_IPA_fricatives',
            'simplify_stress',
            'simplify_stops',
            'simplify_dipthongs',
            'simplify_nasals',
        ]
        self.kwarg_defaults={i:True if i in self.do_by_default else False
                            for i in self.postprocess_kwargs}
        self.kwarg_defaults.update({i:True if i in ['mms_all',
                                                # 'allosaurus',
                                                'neurlang']
                                            else False
                                for i in self.repo_modelnames})
        self.kwarg_defaults.update(kwargs) #override defaults with given kwargs
        return self.kwarg_defaults
    def __init__(self,program,**kwargs):
        kwargs['return_ipa']=True #always, for now
        self.languages=program.languages
        self.models=dict()
        self.do_not_return=[] #models that should not return transcriptions
        log.info(f"Loading ASR with kwargs {kwargs}")
        self.whisper_sizes=WHISPER_SIZES
        self.faster_whisper_models=['turbo', 'distil-large-v3',
                        'deepdml/faster-whisper-large-v3-turbo-ct2']
        self.make_repo_dicts()
        kwargs=self.complete_kwargs_w_defaults(**kwargs)
        for k in ['sister_languages','cache_dir','show_tone']:
            setattr(self,k,kwargs.get(k,False))
        self.model_kwargs={}
        if self.cache_dir:
            self.model_kwargs["cache_dir"]=self.cache_dir
        #This needs to be the actual model name (for testing against) not kwarg.
        self.models_that_give_tone=['katyayego/Wav2Vec2Phoneme-CSfinetune']
        self.models_that_give_IPA=['katyayego/Wav2Vec2Phoneme-CSfinetune',
                                    'neurlang/ipa-whisper-base',
                                    # 'allosaurus' #sucks; don't depend on this
                                ]
        self.models_with_spaced_phones=[
                                        'allosaurus',
                                        'katyayego/Wav2Vec2Phoneme-CSfinetune',
                                        'excalibur12',
                                        'Bluecast',
                                        ]
        #These load an adaptor layer and tokenizer specific to a language:
        self.language_adaptor_models=["facebook/mms-1b-all",
                                        "facebook/mms-1b-l1107",
                                        "facebook/mms-1b-fl102"
                                        ]
        #These take a keyword or language identification (but no model change):
        self.language_kwarg_models=['whisper-'+i for i in self.whisper_sizes]
        self.language_specifiable_models=(self.language_adaptor_models+
                                            self.language_kwarg_models)
        all_kwargs=set(self.repo_modelnames)|set(self.postprocess_kwargs)|set(
                        ['sister_languages','cache_dir','show_tone',
                         'top_models_only'])
        if set(kwargs)-all_kwargs:
            log.error(f"unknown kwargs! ({set(kwargs)-all_kwargs})")
        else:
            log.info("ASR init kwargs OK")
        for k in all_kwargs:
            setattr(self,k,kwargs.get(k,False))
            # log.info(f"{k} {getattr(self,k)}")
        self.load_models_by_kwarg(**kwargs)
        self.load_postprocess_by_kwarg(**kwargs)
if __name__ == '__main__':
    print(datetime.datetime.now())
    from dummy import App
    program=App()
    from backend import langtags
    langtags.Languages(program)
    asr=ASRtoText(program,
            simplify_length=True,
            simplify_nasals=True,
            simplify_vowels=True,
            simplify_dipthongs=True,
            simplify_offglides=True,
            mms=True,
            neurlang=True,
            # allosaurus=True,
            whisper_base=True, #This should only be for LWC transcription
            show_tone=True,
            # other_models=True,
            cache_dir='/media/kentr/hfcache',
            sister_languages=['swa'],
            sister_language=None
        )
    print(datetime.datetime.now())
    test={1:'Noun_witch_(female)_d5a6855f-b8d1-4617-aeac-eeea8dded121_citation_mwanamke__mchawi_sorciere.wav',
        # 2:'John_01_zmb_word.wav'
        }
    import os
    test={k:os.path.join('/home/kentr/bin/raspy/azt/test_data/',v) 
            for k,v in test.items()}
    for i in test.values():
        log.info(f"{asr.return_ipa=}")
        asr.get_transcriptions(i)
        if asr.error_text:
            from utilities.error_handler import notify_error as ErrorNotice
            ErrorNotice(asr.error_text)
        log.info(f"{asr.return_ipa=}")
        # for m in asr.inferall(i):
        #     print(m)
        # print("Show tone:",asr.show_tone)
    quit()
    asr.sister_languages=['sna']
    for asr.repo in asr.models:
        if 'facebook' in asr.repo:
            asr.load_ctc_adaptor()
            asr.model=asr.models[asr.repo]
            for i in test.values():
                print(asr.infer(i))
    print(datetime.datetime.now())
    # for i in test.values():
    #     for m in asr.inferall(i):
    #         print(m)
    #     print("Tone:",asr.tone)
    # print(datetime.datetime.now())
