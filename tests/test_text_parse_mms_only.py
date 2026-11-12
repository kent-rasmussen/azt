"""Parse on the texts board runs only the MMS adapters, one per language in
Transcription settings, where a clause lacks one (Kent, 2026-11-07); "ASR
only" keeps bulk ASR's usual keep-set."""
import pytest


class _ASR:
    language_adaptor_models = ('facebook/mms-1b-all',)
    models = {'facebook/mms-1b-all': object(), 'openai/whisper-small': object()}

    def _mms_lang(self, lang):
        return lang

    def effective_sister_languages(self):
        return ['bss', 'mcp']


def _bulk(mms_only):
    tt = pytest.importorskip('tasks.texts')
    b = tt.TextBulkASR.__new__(tt.TextBulkASR)
    b.mms_only = mms_only
    b.asr = _ASR()
    b.program = type('P', (), {'soundsettings': None})()
    return b


def test_parse_keeps_only_the_mms_adapters_in_settings():
    assert _bulk(True)._keep_keys() == {'facebook/mms-1b-all (bss!)',
                                        'facebook/mms-1b-all (mcp!)'}


def test_asr_only_keeps_every_model():
    assert _bulk(False)._keep_keys() is None   # no top-models limit set


def test_parse_keys_are_what_find_words_recognizes():
    tt = pytest.importorskip('tasks.texts')
    for key in _bulk(True)._keep_keys():
        assert tt.texts.MMS_CANDIDATE.match(key)
