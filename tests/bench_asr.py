#!/usr/bin/env python3
# coding=UTF-8
"""ASR bulk-transcription timing harness (throwaway — not part of the app).

Purpose
-------
Stage 2 of the record -> bulk-ASR -> select redesign must transcribe on the
order of ~1700 audio files through several models. Before committing to a loop
structure we need *real numbers* for this machine and this model set:

  1. cold model-load cost (per model / total)
  2. warm per-file inference cost (per model: mean / p90)
  3. MMS per-sister-language adaptor-switch cost (the cheap-switch claim)
  4. realistic end-to-end get_transcriptions() cost per file (full model set,
     including the sister-language sweep)
  5. extrapolation to the full corpus, model-major vs file-major

These answer: how long does a full run take, where does the time go, is
model-major (load each model once, sweep all files) worth it vs the current
per-file inferall(), and does batching / MMS language-switch change the picture.

How to run
----------
This imports the *live* azt code and needs the project venv (torch/whisper/
transformers). Run with the project interpreter; cwd does not matter:

    /home/kentr/bin/AZT/azt/env/bin/python <path-to-this-file>/bench_asr.py

or:

    cd /home/kentr/bin/AZT/azt && source env/bin/activate && python /path/to/bench_asr.py

Edit the CONFIG block below to match the models you actually have cached and
the sister languages you want measured. Results are printed and also written to
bench_asr_results.json next to this script.

NOTE on downloads: the real Stage 2 task will warn before downloading an
uncached model. This harness does NOT gate downloads — it reports is_cached()
status, then loads whatever MODEL_KWARGS asks for. Set models you don't have to
False to avoid surprise downloads.
"""
import sys
import os
import time
import glob
import json
import statistics

# --- point at the live checkout so imports resolve regardless of cwd ---
AZT_ROOT = '/home/kentr/bin/AZT/azt'
if AZT_ROOT not in sys.path:
    sys.path.insert(0, AZT_ROOT)

# =========================== CONFIG (edit me) ===========================
AUDIO_DIR = '/home/kentr/Assignment/Tools/WeSay/nml-x-test/audio'
CACHE_DIR = '/media/kentr/hfcache'        # HF / whisper model cache
SISTER_LANGUAGES = ['swa', 'sna', 'lin',
		'kdc', 'asa', 'wmw', 'ziw', 
		'ngp', 'heh', 'kki', 'zga', 
		'sbp', 'vid', 'poy', 'ndj', 
		'swh', 'cwe', 'ruf', 'gog', 'ksb']
					# add more to measure switch cost,
                                          # e.g. ['swa', 'sna', 'lin', ...]
SAMPLE_FILES = 20                         # files to time on (None = all)
EXTRAPOLATE_TO = 1700                     # project to the full corpus

# Which models to load. These are ASRtoText kwargs (keys of repo_modelnames).
# Set to what you actually have cached. mms_all + neurlang are app defaults.
MODEL_KWARGS = dict(
    mms_all=True,        # facebook/mms-1b-all   (language-adaptor; cheap switch)
    neurlang=True,       # neurlang/ipa-whisper-base (IPA)
    show_tone=True,      # katyayego/...CSfinetune  (tone + IPA)
    # whisper_base=True, # whisper-base (LWC text; uncomment if wanted)
)
AUDIO_EXTS = ('.wav', '.m4a', '.mp3', '.flac', '.ogg')
# ========================================================================


def p90(xs):
    if not xs:
        return float('nan')
    s = sorted(xs)
    return s[min(len(s) - 1, int(0.9 * len(s)))]


def make_program():
    program = App({})                       # App(program_dict); {} -> no extra attrs
    langtags.Languages(program)             # sets program.languages (ASR needs it)
    return program


def list_audio():
    files = sorted(f for f in glob.glob(os.path.join(AUDIO_DIR, '*'))
                   if f.lower().endswith(AUDIO_EXTS))
    if SAMPLE_FILES:
        files = files[:SAMPLE_FILES]
    return files


def main():
    from dummy import App                       # noqa: E402
    from backend import langtags                # noqa: E402
    from backend import asr as asrmod           # noqa: E402

    results = {'machine_model_set': dict(MODEL_KWARGS),
               'sister_languages': SISTER_LANGUAGES,
               'audio_dir': AUDIO_DIR}
    files = list_audio()
    print(f"# audio files (sampled): {len(files)} of corpus, "
          f"extrapolating to {EXTRAPOLATE_TO}")
    if not files:
        print(f"!! no audio found in {AUDIO_DIR}")
        return
    results['n_sampled'] = len(files)

    program = make_program()

    # ---- 1. model load timing -----------------------------------------
    t0 = time.perf_counter()
    asr = asrmod.ASRtoText(program,
                           cache_dir=CACHE_DIR,
                           sister_languages=SISTER_LANGUAGES,
                           **MODEL_KWARGS)
    load_total = time.perf_counter() - t0
    asr.do_not_return = []                   # bare infer() reads this
    loaded = list(asr.models)
    print(f"\n[1] model load: {load_total:.1f}s for {loaded}")
    def _cached(m):
        # asr.is_cached() has a latent bug (refers to bare `cache_dir`, should
        # be self.cache_dir) — guard so the bench runs; cosmetic only.
        try:
            return bool(asr.is_cached(m))
        except Exception:        # noqa: BLE001
            return 'unknown'
    cache_status = {m: _cached(m) for m in loaded}
    print(f"    cached: {cache_status}")
    results['load_total_s'] = load_total
    results['loaded_models'] = loaded
    results['cache_status'] = cache_status

    # ---- 2. warm per-model per-file inference -------------------------
    print("\n[2] warm per-file inference (model loaded once, sweep files):")
    per_model = {}
    asr.sister_language = None
    for repo in loaded:
        asr.repo = repo
        asr.model = asr.models[repo]
        times = []
        for f in files:
            t = time.perf_counter()
            try:
                asr.infer(f)
            except Exception as e:        # noqa: BLE001 - keep timing other models
                print(f"    {repo} FAILED on {os.path.basename(f)}: {e}")
            times.append(time.perf_counter() - t)
        per_model[repo] = times
        print(f"    {repo:42s} mean {statistics.mean(times):5.2f}s  "
              f"p90 {p90(times):5.2f}s")
    results['per_model_infer_s'] = {k: {'mean': statistics.mean(v),
                                        'p90': p90(v)}
                                    for k, v in per_model.items()}

    # ---- 3. MMS per-sister-language adaptor switch --------------------
    mms = [r for r in loaded if r in asr.language_adaptor_models]
    if mms:
        print("\n[3] MMS adaptor switch cost (per sister language):")
    switch = {}
    for repo in mms:
        asr.repo = repo
        asr.model = asr.models[repo]
        switch[repo] = {}
        for lang in SISTER_LANGUAGES:
            asr.sister_language = lang
            t = time.perf_counter()
            asr.load_ctc_adaptor()
            sw = time.perf_counter() - t
            t = time.perf_counter()
            try:
                asr.infer(files[0])
            except Exception as e:        # noqa: BLE001
                print(f"    {repo}->{lang} infer FAILED: {e}")
            inf = time.perf_counter() - t
            switch[repo][lang] = {'switch_s': sw, 'infer_s': inf}
            print(f"    {repo} -> {lang}: adaptor {sw:5.2f}s + infer {inf:5.2f}s")
    asr.sister_language = None
    results['mms_switch_s'] = switch

    # ---- 4. end-to-end get_transcriptions per file --------------------
    print("\n[4] end-to-end get_transcriptions() per file (full set + sweep):")
    e2e = []
    n_candidates = []
    for f in files:
        t = time.perf_counter()
        try:
            asr.get_transcriptions(f)
            n_candidates.append(len(getattr(asr, 'transcriptions', {})) +
                                len(getattr(asr, 'transcriptions_ipa', {})))
        except Exception as e:            # noqa: BLE001
            print(f"    FAILED on {os.path.basename(f)}: {e}")
        e2e.append(time.perf_counter() - t)
    e2e_mean = statistics.mean(e2e)
    print(f"    mean {e2e_mean:.2f}s  p90 {p90(e2e):.2f}s  "
          f"candidates/file ~{statistics.mean(n_candidates):.1f}"
          if n_candidates else f"    mean {e2e_mean:.2f}s")
    results['e2e_per_file_s'] = {'mean': e2e_mean, 'p90': p90(e2e)}

    # ---- 5. extrapolation ---------------------------------------------
    per_file_infer = sum(statistics.mean(v) for v in per_model.values())
    model_major_h = (load_total + per_file_infer * EXTRAPOLATE_TO) / 3600.0
    file_major_h = ((load_total + per_file_infer) * EXTRAPOLATE_TO) / 3600.0
    e2e_h = e2e_mean * EXTRAPOLATE_TO / 3600.0
    print(f"\n[5] extrapolation to {EXTRAPOLATE_TO} files:")
    print(f"    model-major (load each model once, sweep all):  ~{model_major_h:.2f} h")
    print(f"    file-major  (current inferall per file, naive): ~{file_major_h:.2f} h"
          f"   (wastes ~{(file_major_h - model_major_h):.2f} h reloading)")
    print(f"    e2e get_transcriptions x N (sanity check):       ~{e2e_h:.2f} h")
    results['extrapolation_h'] = {'model_major': model_major_h,
                                  'file_major': file_major_h,
                                  'e2e': e2e_h,
                                  'n': EXTRAPOLATE_TO}

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'bench_asr_results.json')
    with open(out, 'w') as fh:
        json.dump(results, fh, indent=2, default=str)
    print(f"\nwrote {out}")


if __name__ == '__main__':
    main()
