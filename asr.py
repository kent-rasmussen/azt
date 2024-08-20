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
