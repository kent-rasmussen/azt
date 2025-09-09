#!/usr/bin/env python3
# coding=UTF-8
import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import numpy

import whisper
class ASRtoText(object):
    def transcribe(self, audio, **kwargs):
        from pydub import AudioSegment
        # audio = AudioSegment(audio,
        #         frame_rate=16000,
        #         sample_width=2, #pyaudio.paInt16,
        #         channels=1
        #     )
        audio.set_frame_rate(16000)
        audio = audio.set_sample_width(2)
        audio = audio.set_channels(1)
        arr = numpy.array(audio.get_array_of_samples())
        arr = arr.astype(numpy.float32)/32768.0
        # numpydata = numpy.frombuffer(self.fulldata, dtype=numpy.int16)
        # fp16=False on CPU, for now
        self.result = self.model.transcribe(arr,fp16=False, **kwargs)
        print(self.result["text"])
        return self.result["text"]
    def __init__(self,modelname='tiny'):
        # model = whisper.load_model("base")
        # model = whisper.load_model("base")
        self.model = whisper.load_model(modelname)
        # model = whisper.load_model("small")
        #model = whisper.load_model("medium")
        #model = whisper.load_model("large")
if __name__ == '__main__':
    print(datetime.datetime.now())
    asr=ASRtoText(
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
    test={1:'/home/kentr/bin/raspy/azt/John_01_zmb_NP.wav',
        2:'/home/kentr/bin/raspy/azt/John_01_zmb_word.wav'}
    for i in test.values():
        log.info(f"{asr.return_ipa=}")
        asr.get_transcriptions(i)
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
