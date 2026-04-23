from utilities import file, rx, logsetup
log = logsetup.getlog(__name__)
import io_put.sound as sound #assuming this is the current location of AudioInterface

class Sound(object):
    """Headless backend mixin for playing audio and managing PyAudio streams."""
    settings_attrs=['fs', 'sample_format', 'audio_card_out']

    def donewpyaudio(self):
        try:
            self.pyaudio.terminate()
        except:
            log.info("Apparently self.pyaudio doesn't exist, or isn't initialized.")

    def pyaudiocheck(self):
        try:
            self.pyaudio.pa.get_format_from_width(1) #just check if its OK
        except:
             self.pyaudio=sound.AudioInterface()

    def makesoundsettings(self):
        self.pyaudiocheck()
        if not hasattr(self.program.settings,'soundsettings'):
            log.info("Making new soundsettings object")
            self.program.settings.soundsettings=sound.SoundSettings(self.pyaudio,
                        analang_obj=self.program.languages.get_obj(self.analang)
                        )

    def loadsoundsettings(self):
        self.makesoundsettings()
        self.program.settings.loadsettingsfile(setting='soundsettings')
        self.program.soundsettings=self.program.settings.soundsettings
        if self.program.hostname == 'karlap' and (
                        'cache_dir' not in self.program.soundsettings.asr_kwargs
                        ):
            self.program.soundsettings.asr_kwargs[
                                            'cache_dir']='/media/kentr/hfcache'

    def storesoundsettings(self):
        self.program.settings.storesettingsfile(setting='soundsettings')

    def soundsettingscheck(self):
        if not hasattr(self.program.settings,'soundsettings'):
            self.loadsoundsettings()

    def missingsoundattr(self):
        ss=self.program.settings.soundsettings
        for s in self.settings_attrs:
            if hasattr(ss,s):
                if s+'s' in ss.hypothetical and (getattr(ss,s)
                                                not in ss.hypothetical[s+'s']):
                    log.info("Sound setting {setting} invalid; asking again".format(setting=s))
                    return True
                elif 'audio_card' in s and (getattr(ss,s)
                                                    not in ss.cards['dict']):
                    log.info("Sound setting {setting} invalid; asking again".format(setting=s))
                    return True
            else:
                log.info("Missing sound setting {setting}; asking again".format(setting=s))
                return True
        self.program.settings.soundsettingsok=True

    def soundcheck(self):
        self.soundsettingscheck()
        self.soundsettings=self.program.settings.soundsettings
        self.soundsettings.check()
        # Note: UI checking like mikecheck() is moved to tasks.sound
        if not self.ui.exitFlag.istrue() and self.missingsoundattr():
            return True #Signal to UI that mikecheck is needed

    def audioexists(self,relfilename):
        return file.exists(self.audioURL(relfilename))

    def audioURL(self,relfilename):
        return str(file.getdiredurl(self.program.settings.audiodir,relfilename))

    def hassoundfile(self,node,recheck=False):
        return node.hassoundfile(recheck)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Record(Sound):
    """Headless backend mixin for recording logic (file names, paths)."""
    settings_attrs=['audio_card_in']+Sound.settings_attrs

    def filenameoptions(self,node):
        ps=self.program.slices.ps()
        if ps:
            pslocopts=[ps]
        else:
            pslocopts=[]
        profile=self.program.slices.profile()
        if ps and profile:
            pslocopts.insert(0,ps+'_'+profile)
        fieldlocopts=[None]
        try:
            l=node.locationvalue()
            pslocopts.insert(0,ps+'-'+l)
            fieldlocopts.append(l)
        except AttributeError:
            pass
        if not pslocopts:
            pslocopts=[None]
        filenames=[]
        form=node.textvaluebylang(self.analang)
        if not form:
            log.error("filenameoptions: no {ana} analang in "
                "{id}!".format(ana=self.analang, id=node.sense.id))
        for pslocopt in pslocopts:
            for fieldlocopt in fieldlocopts:
                for legacy in ['_', None]:
                    for tags in [ None, 1 ]:
                        args=[node.sense.id]
                        if tags:
                            args+=[node.tag]
                            if node.tag == 'field':
                                args+=[node.ftype]
                        args+=[form]
                        for l in self.glosslangs:
                            args+=[node.glossbylang(l)]
                        optargs=args[:]
                        optargs.insert(0,pslocopt)
                        optargs.insert(3,fieldlocopt)
                        wavfilename='_'.join([x for x in optargs if x])
                        if legacy == '_':
                            wavfilename+='_'
                        wavfilename=rx.urlok(wavfilename)
                        filenames+=[wavfilename+'.wav']
        return filenames

    def makeaudiofilename(self,node):
        if self.hassoundfile(node):
            return
        filenames=self.filenameoptions(node)
        for f in filenames:
            if self.audioexists(f):
                node.textvaluebylang(lang=self.program.params.audiolang(),value=f)
                break
        f=filenames[-1]
        node.audiofilenametoput=f
        node.audiofileURL=self.audioURL(f)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
