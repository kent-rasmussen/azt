#!/usr/bin/env python3
# coding=UTF-8
from utilities import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
from utilities.i18n import _
from frontend import ui
from utilities.error_handler import notify_error as ErrorNotice
from utilities.error_handler import notify_user
from io_put import sound
from utilities import file, executables, utilities as utils
class RecordButtonFrame(ui.Frame):
    """This is not implemented yet!!"""
    def _start(self, event=None):
        log.log(3,"Asking PA to record now")
        self.recorder.start()
    def _stop(self, event=None):
        try:
            self.recorder.stop()
            # log.info(f"self.recorder: {hasattr(self,'recorder')}")
        except Exception as e:
            log.info("Couldn't stop recorder; was it on? ({})".format(e))
        """This is done in advance of recording now:"""
        if self.recorder.file_write_OK:
            self.b.destroy()
            self.makeplaybutton()
            self.makedeletebutton()
            self.addlink()
        # THE TAKE CAN CHANGE THE SETTINGS, so re-read them onto the labels.
        # `_report_take` proves a rate upsampled and `note_fake_rate` re-picks
        # immediately — correct, and invisible: the window still said 192khz
        # after switching to 96000, so the only evidence was the log (Kent
        # 2026-09-10, "unclear that setting changed, since there was no UI
        # change"). Nothing polls: `soundcheckrefresh` runs once from
        # __init__ and on clicks, and its `refreshdelay`/`dictnow` are dead.
        # `self.task` is whoever built this frame — the SoundSettingsWindow on
        # the mic-check screen, a real Task everywhere else. Only the former
        # has labels to re-read, so this is a no-op during real recording.
        refresh = getattr(getattr(self, 'task', None), 'relabel_settings',
                          None)
        if callable(refresh):
            try:
                refresh()
            except Exception as e:
                log.info("couldn't refresh the settings labels ({})".format(e))
    def _redo(self, event=None):
        log.log(3,"I'm deleting the recording now")
        self.p.destroy()
        self.makerecordbutton()
        self.r.destroy()
    def makebuttons(self):
        if self.soundsettings.file_ok(self._filenameURL):
            self.makeplaybutton()
            self.makedeletebutton()
            self.addlink()
        else:
            self.makerecordbutton()
    def makerecordbutton(self):
        # if not hasattr(self,'recorder'):
        #     log.debug(f"PA recorder init ({vars(self)})")
        #     self.recorder=sound.SoundFileRecorder(self._filenameURL,self.pa,
        #                                     self.soundsettings)
        #     log.debug(f"PA recorder ({type(self.recorder)}) init ({vars(self)})")
        # log.debug("PA recorder made OK")
        self.b=ui.Button(self, command=self.function,
                        image='record',
                        ipadx=20, ipady=15
                        )
        self.b.grid(row=0, column=0,sticky='w')
        self.b.bind('<ButtonPress-1>', self._start)
        self.b.bind('<ButtonRelease-1>', self._stop)
        self.bt=ui.ToolTip(self.b,_("press-speak-release"))
    def _play(self,event=None):
        log.debug("Asking PA to play now")
        utils.tryrun(self.player.play)
    def makeplaybutton(self):
        self.p=ui.Button(self, text='‣', command=self._play,
                        font='readbig',
                        ipadx=20, ipady=0
                        )
        #Not using these for now
        # self.p.bind('<ButtonPress>', self._play)
        # self.p.bind('<ButtonRelease>', self.function)
        self.p.grid(row=0, column=1,sticky='nsw')
        pttext=_("Click to hear")
        if (hasattr(self.program, 'praat')
                and not str(self._filenameURL).lower().endswith('.m4a')):
            # praat can't read m4a: no bind, and no tooltip advertising it
            pttext+='; '+_("right click to open in praat")
            self.p.bind('<Button-3>',
                        lambda x: executables.praatopen(
                                                    self.program,
                                                    self._filenameURL))
        self.pt=ui.ToolTip(self.p,pttext)
    def makedeletebutton(self):
        self.r=ui.Button(self,text='×',font='read',command=self.function,
                        row=0, column=2, sticky='nsw')
        self.r.bind('<ButtonRelease-1>', self._redo)
        self.rt=ui.ToolTip(self.r,_("Try again"))
        self.r.update_idletasks()
    def function(self):
        pass
    def addlink(self):
        if self.test:
            return
        self.program.db.addmediafields(self.node,self.filename,
                                self.program.params.audiolang(),
                                # ftype=ftype,
                                write=False)
        self.task.maybewrite()
        # Client contract § 8b obl. 4: the .wav itself is a non-LIFT
        # artifact, so it only enters git on some LATER commit's
        # whole-tree staging — a session that ends here, or crashes,
        # would leave the recording on disk but out of history entirely.
        # Kent 2026-07-27: commit after every recording (cheap — the
        # daemon debounces commit_project at 500 ms, and small commits
        # are the wanted granularity).
        session=getattr(self.program,'collab',None)
        if session is not None:
            session.commit_artifacts()
        self.program.status.last('recording',update=True)
    def __init__(self,parent,task,node=None,**kwargs): #filenames
        """Uses node to make framed data, just for soundfile name"""
        """Without node, this just populates a sound file, with URL as
        provided. The LIFT link to that sound file should already be there."""
        # This class needs to be cleanup after closing, with check.done_audio()
        """Originally from https://realpython.com/playing-and-recording-
        sound-python/"""
        self.id=id
        self.task=task
        # ASK THE HONEST QUESTION. This used to call
        # `task.audio.get_format_from_width(1)` inside a try purely for the
        # side effect of finding out whether the handle still worked — a trick
        # that existed because PyAudio offered no way to ask. It survived the
        # port, and after it `AudioInterface` has no such method, so the call
        # raised AttributeError EVERY time and the except branch replaced
        # `task.audio` with a brand-new interface on every record button. That
        # is the "new AudioInterface conflicts with a Sound task that already
        # opened a stream" hazard in AUDIT_FINDINGS (L77-87), fired on every
        # build rather than occasionally. `usable()` was written for this
        # (backend/core/sound.py:436) and says so in its docstring.
        audio=getattr(task,'audio',None)
        if audio is None or not audio.usable():
            # Through the owner where there is one: confirm_audio() stores the
            # handle on `program` so every surface shares it, which a bare
            # AudioInterface() here would not (see sort_buttons._playback).
            ss=getattr(task,'soundsettings',None)
            if ss is not None and hasattr(ss,'confirm_audio'):
                ss.confirm_audio()
                task.audio=ss.audio
            else:
                task.audio=sound.AudioInterface()
        self.pa=task.audio
        if not hasattr(task,'soundsettings') or not hasattr(task,'program'):
            log.error("task missing a settings attr? "
                        f"(soundsettings:{hasattr(task,'soundsettings')}; "
                        f"program:{hasattr(task,'program')})")
            raise AttributeError("task is missing a 'soundsettings' or 'program' attribute")
        self.soundsettings=task.soundsettings
        self.program=task.program
        # log.info("RecordButtonFrame found program settings "
        #         f"{self.program}")
        # log.info("RecordButtonFrame started with soundsettings "
        #         f"{vars(self.soundsettings)}")
        self.callbackrecording=True
        self.chunk = 1024  # Record in chunks of 1024 samples (for block only)
        self.channels = 1 #Always record in mono
        self.test=kwargs.pop('test',None)
        # log.info(f"Working with node: {node} "
        #         f"({node.tag if node is not None else ''})"
        #         f": {vars(node) if node is not None else ''}")
        if node is not None and node.isnode():
            task.makeaudiofilename(node) #should fill out the following
            self.filename=node.textvaluebylang(
                                            self.program.params.audiolang())
            if not self.filename: #should have above or below
                self.filename=node.audiofilenametoput
            self._filenameURL=node.audiofileURL
            self.node=node
        elif self.test:
            # Kept in step with settings changes by _refresh_test_filename(),
            # which soundcheckrefresh() calls — see the note there.
            self.filename=self._filenameURL='test_{}_{}_{}.wav'.format(
                                self.soundsettings.fs,
                                self.soundsettings.sample_format,
                                self.soundsettings.audio_card_in)
        else:
            t=_("No framed value, nor testing; can’t continue...")
            log.error(t)
        # Just do these each once, since their dependencies don't change
        self.recorder=sound.SoundFileRecorder(self._filenameURL,self.pa,
                                        self.soundsettings)
        self.player=sound.SoundFilePlayer(self._filenameURL,self.pa,
                                            self.soundsettings)
        ui.Frame.__init__(self,parent, **kwargs)
        """These need to happen after the frame is created, as they
        might cause the init to stop."""
        #self.program.settings.mgr.get('audiolang')
        if not self.test and not self.program.db.audiolang:
            tlang=_("Set audio language to get record buttons!")
            log.error(tlang)
            ui.Label(self,text=tlang,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        if None in [self.soundsettings.fs,
                    self.soundsettings.sample_format,
                    self.soundsettings.audio_card_in,
                    self.soundsettings.audio_card_out]:
            text=_("Set all sound card settings"
                    "\n(Do|Recording|Sound Card Settings)"
                    "\nand a record button will be here.")
            log.debug(text)
            ui.Label(self,text=text,borderwidth=1,
                relief='raised' #flat, raised, sunken, groove, and ridge
                ).grid(row=0,column=0)
            return
        self.makebuttons()
class RecordnTranscribeButtonFrame(RecordButtonFrame):
    def _stop(self, event):
        RecordButtonFrame._stop(self)  # records + addlink() writes the audio form
        if self.soundsettings.asrOK and self.recorder.file_write_OK:
            with self.task.waiting("Getting transcriptions..."):
                self.recorder.get_transcriptions()
                if self.recorder.error_text:
                    ui.error(self.recorder.error_text)
                else:
                    self.persist_drafts()  # ADR 0002: durable drafts for stage 3
        else:
            log.info("Not transcribing because asr is not OK!")
        if hasattr(self.recorder,'transcriptions'):
            self.maketranscriptionlabel()
    def persist_drafts(self):
        """Live-path write-through (ADR 0002): store this recording's ASR draft
        candidates as annotations on the <analang>-x-audio form, so the selector
        (stage 3) can rebuild them later with no live ASR. The bulk batch (stage
        2) calls Form.persist_drafts directly with the same contract, so stage 3
        can't tell which produced the drafts.

        The audio form was just written by addlink()/addmediafields as a raw
        node; getforms() re-wraps it as a lift.Form carrying persist_drafts."""
        log.info("persist_drafts: called")
        if getattr(self,'node',None) is None or not self.node.isnode():
            log.info("persist_drafts: skipped — no LIFT node to attach drafts to")
            return
        rec=self.recorder
        if not hasattr(rec,'transcriptions'):
            log.info("persist_drafts: skipped — recorder has no transcriptions")
            return
        audiolang=self.program.params.audiolang()
        self.node.getforms()  # pick up the audio form addlink() just wrote
        form=self.node.forms.get(audiolang)
        if form is None:
            log.error(f"No '{audiolang}' audio form to persist ASR drafts onto.")
            return
        # tone_melody is scalar today (single tone source); the ADR tone-{repo}
        # lane needs a per-repo dict, so only persist tone when it IS a dict —
        # otherwise skip (the live tone var still shows it this session).
        tone=rec.tone_melody if isinstance(getattr(rec,'tone_melody',None),dict) else {}
        tx=getattr(rec,'transcriptions',None) or {}
        ipa=getattr(rec,'transcriptions_ipa',None) or {}
        md5=self._audio_md5()
        form.persist_drafts(transcriptions=tx,ipa=ipa,tone=tone,md5=md5)
        log.info(f"persist_drafts: {len(tx)} transcription + {len(ipa)} IPA + "
                 f"{len(tone)} tone draft(s) -> '{audiolang}' audio form "
                 f"(md5={'set' if md5 else 'none'})")
        self.task.maybewrite()
    def _audio_md5(self):
        """md5 of the current audio file (ADR 0002 staleness key); None if it
        can't be read, in which case persist_drafts skips the wipe/redraft gate."""
        import hashlib
        try:
            with open(self._filenameURL,'rb') as fh:
                return hashlib.md5(fh.read()).hexdigest()
        except OSError as e:
            log.error(f"Can't md5 audio '{self._filenameURL}': {e}")
            return None
    def _redo(self, event):
        self.remove_transcriptions()
        RecordButtonFrame._redo(self)
    def makebuttons(self):
        RecordButtonFrame.makebuttons(self)
        if (file.exists(self._filenameURL) and
                hasattr(self.recorder, 'transcriptions') and
                not self.shown == 'none'):
            self.maketranscriptionlabel()
    def maketranscriptionlabel(self):
        try:
            self.transcription_var.set(self.recorder.transcriptions)
            self.transcription_ipa_var.set(self.recorder.transcriptions_ipa)
            self.transcription_tone_var.set(self.recorder.tone_melody)
        except Exception as e:
            pass
            # log.info(f"No transcription variables set ({e})")
        self.transcriptionframe=ui.ScrollingFrame(self,row=0,col=3)
        scrolling_content=self.transcriptionframe.content
        c=0
        repos=sorted(set(self.recorder.transcriptions)|set(
                        self.recorder.transcriptions_ipa)) #all keys, keep order
        for trans in ['transcriptions','transcriptions_ipa']:
            # log.info(f"maybe showing {trans}")
            if (hasattr(self,f'show_{trans}') and
                getattr(self,f'show_{trans}') and
                hasattr(self.recorder,trans) and
                getattr(self.recorder,trans)):
                # log.info(f"showing {trans}")
                # log.info(f"showing {trans} now ({toshow[:20]})")
                setattr(self,trans,{})
                r=0
                for i in repos:
                    text=getattr(self.recorder,trans).get(i,'')
                    if text and len(repos) > self.show_repo_name_if_more_than:
                        text=i+': '+text
                    try:
                        assert text
                        getattr(self,trans)[i]=ui.Label(scrolling_content,
                                                    text=text,
                                                    ipadx=20,
                                                    row=r,
                                                    column=c
                                                    )
                    except Exception as e:
                        log.info(f"Probably nothing: {e}")
                    if self.shown == 'first':
                        continue
                    r+=1
                c+=1
        if (hasattr(self,'show_tone') and self.show_tone
                and hasattr(self.recorder,'tone_melody')
            and self.recorder.tone_melody):
            self.tone_melody=ui.Label(scrolling_content,
                                    text=self.recorder.tone_melody,
                                    ipadx=20, #ipady=15,
                                    row=self.grid_size()[1],
                                    column=0, colspan=2
                                    )
        # log.info(f"scrolling_content size: {scrolling_content.grid_size()}")
        if not sum(scrolling_content.grid_size()):
            self.transcriptionframe.destroy()
        else:
            self.transcriptionframe.reflow()  # grow canvas to cover the labels
    def remove_transcriptions(self):
        try:
            self.transcriptionframe.content.destroy()
            self.transcriptionframe.destroy()
            del self.recorder.transcriptions
            del self.recorder.transcriptions_ipa
            self.tone_melody.destroy()
            del self.recorder.tone_melody
        except Exception as e:
            log.info(f"transcription destruction failed ({e})")
            pass
    def configure_this(self):
        ASRModelSelectionWindow(self.program)
    def __init__(self,parent,task,node=None,**kwargs):
        must_haves=['transcription_var','show_transcriptions',
            'transcription_ipa_var','show_transcriptions_ipa',
            'transcription_tone_var','show_tone','shown']
        for f in must_haves:
            setattr(self,f,kwargs.pop(f,False))
        for f in [i for i in must_haves if '_var' in i]:
            if not getattr(self,f):
                setattr(self,f,ui.StringVar())
                log.info(f"Set untracked StringVar for {f}; it won't be "
                    f"available outside this {self.__class__.__name__}")
        self.show_repo_name_if_more_than=1
        super(RecordnTranscribeButtonFrame,self).__init__(parent,task,node,**kwargs)
class SoundSettingsWindow(ui.Window):
    def setsoundformat(self,choice,window):
        self.soundsettings.sample_format=choice
        self.updatesoundformat()
        self._refresh_test_filename()   # see setsoundhz
        window.destroy()
    def updatesoundformat(self):
        self.labeltext['sample_format'].set(self.soundformatlabel())
    def _describe(self, mapping, key, what):
        """The friendly name for `key`, or the raw value if there isn't one.

        NEVER RAISES, and that is the whole point. Three of the four label
        builders indexed their lookup tables directly, so ONE setting the
        table did not recognise raised inside `soundcheckrefresh` — between
        "Done setting up labels" and the labels being filled — and the Sound
        Settings window was built, left withdrawn, and never shown. Kent,
        2026-09-11: "sound settings window didn't show."

        **This is the worst possible place for that failure.** Sound Settings
        is the screen a user opens IN ORDER TO fix a bad sound setting, so a
        bad setting must not be what stops it opening. An unrecognised value
        shows as itself — which also tells the user (and the log) exactly
        which value is the odd one, instead of hiding it behind a dead menu.
        """
        try:
            if key in mapping:
                return mapping[key]
        except TypeError:      # mapping isn't a mapping
            pass
        log.warning("sound settings: %s %r is not in the list of known "
                    "values; showing it as-is", what, key)
        return key

    def soundformatlabel(self):
        self.soundsettings.check()
        cur=self._describe(self.soundsettings.hypothetical['sample_formats'],
                           getattr(self.soundsettings,'sample_format',None),
                           'format')
        return _(f"{cur}")
    def setsoundcard_byname(self,name):
        if name in self.soundsettings.cards['dict'].values():
            # choose_card, not a direct assignment: it also records WHICH
            # device the index means, without which resolve_cards() follows
            # the previously stored name and undoes this (see choose_card).
            self.soundsettings.choose_card('in',[n for n,v
                                    in self.soundsettings.cards['dict'].items()
                                    if v == name][0])
        else:
            log.error(f"card {name} not available "
                        f" ({self.soundsettings.cards['dict'].keys()})")
        self._new_input_card()
    def setsoundcardindex(self,choice,window):
        # log.info("setsoundcardindex: {}".format(choice))
        self.soundsettings.choose_card('in',choice)
        self._new_input_card()
        window.destroy()
    def _new_input_card(self):
        """A different microphone: re-derive the other settings and MEASURE it.

        Kent, 2026-09-11: "any card switch legitimately implies other settings
        change; let's offer the best the newly selected card has" — and, on the
        question of a button: "I think running that on switching input cards
        would be preferable to another button users have to hit."

        Both are improvements on what was here. `choose_card` already calls
        `forget_rate_checks()`, correctly, because a measurement of the old
        path says nothing about the new one — but nothing then re-measured, so
        switching cards could only ever LOSE information: the rate list went
        back to unannotated and stayed that way until the user happened to make
        a test recording. And the rate/format were left as the previous card's,
        re-derived only if the new card could not do them at all
        (`makedefaultifnot`), so a card offering 48000 kept a 192000 that
        merely happened to be in its list.

        Measuring HERE and not inside `choose_card`: that is a low-level setter
        documented as the only safe way to set a card, and a second of audio
        recording does not belong in one — a future caller on a startup path
        would silently acquire a recording. Output cards do not come here at
        all; nothing about the speakers affects what gets recorded.
        """
        ss=self.soundsettings
        # The new card's best, before measuring: this is also the answer if the
        # room turns out to be too quiet to judge.
        try:
            ss.default_fs()
            ss.default_sf()
        except Exception as e:
            log.info("couldn't re-derive settings for the new card ({})"
                    .format(e))
        rate=message=None
        try:
            # The wait dialog because this RECORDS, on this thread, inside the
            # click handler — without it the settings window freezes for the
            # capture with no explanation. (Kent was unconvinced it was needed;
            # doing it his stated way — "do it, and we'll see".)
            #   `self.waiting`, NOT `self.task.waiting`. `wait()` withdraws
            # the window it is called on and `waitdone()` reveals THAT window
            # again, so waiting on the TASK dropped the user back at the task
            # page with Sound Settings buried behind it — Kent, 2026-09-11:
            # "'checking what the microphone can do...' returns me to the
            # task. I can navigate back to the sound settings, but that's
            # counter intuitive." The window the user is working in is the one
            # to come back to, and this IS a window, so it can say so. (I
            # copied `self.task.waiting` from `RecordButtonFrame`, where it is
            # correct: a Frame has no wait of its own.)
            # WAIT DIALOG OFF, at Kent's request 2026-09-11 ("comment out
            # that wait now; I want to see it without") — he was unconvinced
            # it was needed and wants the bare behaviour to look at. Note the
            # measurement got SLOWER since he first said so: the settle pause
            # and the confirm-on-repeat added for the probe's verdicts take it
            # from about 1s to about 2s, and it runs on this thread, so the
            # settings window will sit unresponsive for that long with no
            # explanation. That is the thing to judge.
            # with self.waiting(_("Checking what this microphone can do..."),
            #                   thenshow=True):
            rate,message=ss.verify_fs()
        except Exception as e:
            log.info("couldn't check the new microphone's rates ({})".format(e))
        if rate:
            # The verified rate may not offer the format the old one did.
            try:
                ss.default_sf()
            except Exception as e:
                log.info("couldn't re-derive the format for {} Hz ({})"
                        .format(rate,e))
        self.relabel_settings()         # fs and format moved, not just the card
        self._refresh_test_filename()   # the name carries all three
        # QUIETER THAN A BUTTON WOULD BE. `verify_fs` returns (None, reason)
        # when the room was too quiet to judge; on a button that is a fair
        # answer to a question the user asked, but fired on every card switch
        # it is a nag for something they did not ask about and cannot act on.
        # So speak only when there is news; the rate list carries the rest.
        if rate and message:
            notify_user(message)
        elif message:
            log.info("rate check on the new microphone: %s", message)
    def updatesoundcard(self):
        self.labeltext['audio_card_in'].set(self.soundcardlabel())
    def soundcardlabel(self):
        self.soundsettings.check()
        # Was the only guarded one of the four, which is why it is not the
        # one that broke. It showed `None` for an unknown card, though —
        # less useful than the index itself, which is what _describe gives.
        cur=self._describe(self.soundsettings.cards['dict'],
                           getattr(self.soundsettings,'audio_card_in',None),
                           'input card')
        return _(f"Microphone: '{cur}'")
    def setsoundcardoutindex(self,choice,window):
        # log.info("setsoundcardoutindex: {}".format(choice))
        self.soundsettings.choose_card('out',choice)
        self.updatesoundcardoutindex()
        window.destroy()
    def updatesoundcardoutindex(self):
        self.labeltext['audio_card_out'].set(self.soundcardoutindexlabel())
    def soundcardoutindexlabel(self):
        self.soundsettings.check()
        cur=self._describe(self.soundsettings.cards['dict'],
                           getattr(self.soundsettings,'audio_card_out',None),
                           'output card')
        return _(f"Speakers: '{cur}'")
    def setsoundhz(self,choice,window):
        self.soundsettings.fs=choice
        self.updatesoundhz()
        # THE TEST FILENAME ENCODES fs, sample_format AND the input card, so
        # every setter has to re-derive it. `_refresh_test_filename` existed
        # and was called only from the full `soundcheckrefresh()`, which the
        # per-setting choosers do not run — so a take made after changing the
        # rate here went into the name built for the PREVIOUS rate:
        # "Initializing Recording to test_44100_int32_6.wav" for a 192000 Hz
        # take (Kent 2026-09-10, the second sighting of this). The name lies
        # about the file, and every combination overwrites the last.
        self._refresh_test_filename()
        window.destroy()
    def updatesoundhz(self):
        self.labeltext['fs'].set(self.soundhzlabel())
    def soundhzlabel(self):
        self.soundsettings.check()
        cur=self._describe(self.soundsettings.hypothetical['fss'],
                           getattr(self.soundsettings,'fs',None), 'rate')
        return _(str(cur))
    def getsoundcardindex(self,event=None):
        log.info("Asking for input sound card...")
        window=ui.Window(self,
                    title=_('Select Input Sound Card'))
        ui.Label(window.frame, text=_('What sound card do you '
                                    'want to record sound with with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['in']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.setsoundcardindex,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundcardoutindex(self,event=None):
        log.info("Asking for output sound card...")
        window=ui.Window(self,
                title=_('Select Output Sound Card'))
        ui.Label(window.frame, text=_('What sound card do you '
                                    'want to play sound with?')
                ).grid(column=0, row=0)
        l=list()
        for card in self.soundsettings.cards['out']:
            name=self.soundsettings.cards['dict'][card]
            l+=[(card, name)]
        buttonFrame1=ui.ScrollingButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.setsoundcardoutindex,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundformat(self,event=None):
        log.info("Asking for audio format...")
        window=ui.Window(self,
                        title=_('Select Audio Format'))
        ui.Label(window.frame, text=_('What audio format do you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        l=list()
        ss=self.soundsettings
        # WIDEST FIRST, for the same reason the rates run highest first: it is
        # what the audio layer already prefers. `default_sf`/`max_sf` both
        # take `widest()`, and ranking there goes through `sound.format_bits`
        # precisely so that "widest" is a statement about width rather than an
        # accident of how the values happen to sort — which is what it was
        # under PyAudio, whose constants ran INVERSE to width (paFloat32=1 …
        # paUInt8=32), so `max()` selected the NARROWEST format.
        #   Sorting by the same function keeps the menu and the default
        # agreeing. Sorting by the dtype NAME would not: 'float32' < 'int16'
        # < 'int32' alphabetically, which is neither width order nor stable
        # against adding a format.
        try:
            formats=sorted(ss.cards['in'][ss.audio_card_in][ss.fs],
                           key=sound.format_bits, reverse=True)
        except Exception as e:
            log.info("couldn't rank the sample formats by width ({})".format(e))
            formats=list(ss.cards['in'][ss.audio_card_in][ss.fs])
        for sf in formats:
            # _describe, not a bare index: this is the same unguarded lookup
            # that kept the settings window from opening at all (see
            # _describe), in the widget that lists the values rather than the
            # one that shows the current one.
            l+=[(sf, self._describe(ss.hypothetical['sample_formats'], sf,
                                    'format'))]
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.setsoundformat,
                                    window=window,
                                    column=0, row=1
                                    )
    def getsoundhz(self,event=None):
        log.info("Asking for sampling frequency...")
        window=ui.Window(self,
                        title=_('Select Sampling Frequency'))
        ui.Label(window.frame, text=_('What sampling frequency you '
                                    'want to work with?')
                ).grid(column=0, row=0)
        l=list()
        ss=self.soundsettings
        # HIGHEST FIRST. Kent, 2026-09-11: "rates are unintuitively ordered
        # lowest first?" — and lowest-first was my doing (it was dict order
        # before). Descending is what the rest of the audio layer already
        # believes: `default_fs` picks the highest offered, `widest()` picks
        # the widest format, and `measured_fs` walks the rates high to low.
        # Leading with 8 kHz puts the least useful option where the eye lands
        # first and buries the one the app would have chosen.
        #   Still a STABLE order, which was the reason for sorting at all: an
        # entry must not move between visits as evidence arrives (see
        # _rate_option_label).
        for fs in sorted(ss.cards['in'][ss.audio_card_in], reverse=True):
            l+=[(fs, self._rate_option_label(fs))]
        buttonFrame1=ui.ButtonFrame(window.frame,
                                    optionlist=l,
                                    command=self.setsoundhz,
                                    window=window,
                                    column=0, row=1
                                    )
    def _rate_option_label(self, fs):
        """The rate, plus what has been MEASURED about it. ANNOTATE, DON'T
        WITHHOLD (Kent, 2026-09-11: "Can we show users what we believe is true
        without actually limiting options?").

        Every rate the card will open stays selectable — the same principle as
        DETECT AND TELL, NEVER SWITCH, which this screen had not inherited: it
        listed what the device ACCEPTS and said nothing about what recording at
        that rate actually produced, so a rate disproved by the user's own last
        take was offered again, unmarked, beside one that recorded cleanly.

        Three states, and the third is the common one — so no note at all is
        the default, and an unannotated entry means "not checked" without
        needing a legend to say so (Kent: "leave this off"). Notes state the
        EVIDENCE, never a verdict: this detector has been wrong about enough
        rates in one day that "upsampled, as measured" is honest and "bad" is
        not. No colour carries any of it.

        WORDING, settled with Kent 2026-09-11:

        * **"upsampled", not "stretched"** — "technical, but precise", and
          "stretched isn't normally used". It is the word the logs and this
          item have used throughout; the user-facing text was the odd one out.
        * **no "checked:" prefix.** All three notes carried it, so it
          distinguished none of them from each other — the presence of ANY
          note already says the rate was checked.
        * **no "from a lower rate" tail** where the rate is unknown. It adds
          nothing the word does not carry, and dropping it leaves the two
          forms differing only where there is content.
        * **the original rate in the SAME UNITS** as the name beside it:
          "192khz — upsampled from 44.1khz", not "from 44100 Hz".

        ANNOTATED FROM THE PROBE TOO, since 2026-09-11. It was withheld
        because `measured_fs` swept rates back to back with no settle pause —
        the condition that produced a false accusation in the manual prober
        (agenda/honest_sound_settings.md, finding 2b). But withholding it was
        incoherent: `verify_fs`'s notice already asserted the same result in
        prose. Kent: "we're checking on load; why not share that with the
        user?" So the sweep got the settle pause and the confirm-on-repeat the
        prober has, and its verdicts now count on the same footing.
        """
        ss=self.soundsettings
        name=ss.hypothetical['fss'][fs]
        try:
            disproved=ss.fake_rates_here()
            confirmed=ss.real_rates_here()
        except Exception as e:
            log.info("couldn't read the rate checks ({})".format(e))
            return name
        if fs in disproved:
            lower=[r for r in confirmed if r < fs]
            if lower:
                # THE ORIGINAL RATE IN THE SAME UNITS as the name beside it.
                # This said "stretched from 44100 Hz" next to "192khz" — two
                # units in one line, because `{real}` was the raw integer the
                # measurement works in. The label the user already reads for
                # that rate is the one to reuse.
                return _("{name} — upsampled from {real}").format(
                            name=name,
                            real=self._describe(ss.hypothetical['fss'],
                                                max(lower), 'rate'))
            # No "from a lower rate" tail: it says nothing the word does not
            # already carry, and the two forms then differ only by the part
            # that has content (Kent, 2026-09-11).
            return _("{name} — upsampled").format(name=name)
        if fs in confirmed:
            # "NOT STRETCHED", never "real". `rate_is_fake` cannot certify a
            # rate (it never returns False), so the strongest honest claim is
            # that nothing in the take disproved this one. An earlier draft
            # said "records cleanly", which a user would read as a guarantee
            # the measurement cannot give.
            return _("{name} — not upsampled").format(name=name)
        return name
    def _refresh_test_filename(self):
        """Re-derive the mic-check filename from the CURRENT settings.

        The name is built from fs and sample_format (:145), and the recorder
        and player were handed it once, under the comment "Just do these each
        once, since their dependencies don't change". On this screen those
        dependencies are the very things the user changes, so the comment was
        false: a take at 44100/int16 was still being written to — and played
        from — `test_192000_int32.wav` (Kent 2026-09-10: "Is there a reason
        the filename doesn't respect settings?"). Two costs, and the second is
        the worse: the name lied, AND every combination overwrote the last, so
        the takes could not be compared — which is the whole purpose of this
        screen.
          The card index is in the name too, so switching microphones gives a
        separate file rather than clobbering the previous one.
        """
        if not getattr(self,'test',False):
            return
        ss=self.soundsettings
        name='test_{}_{}_{}.wav'.format(ss.fs,ss.sample_format,
                                        ss.audio_card_in)
        if name==getattr(self,'_filenameURL',None):
            return
        log.info("mic check: settings changed, recording to %s now",name)
        self.filename=self._filenameURL=name
        # The recorder derives file_tmp from this, so assigning is enough.
        for obj in (getattr(self,'recorder',None),getattr(self,'player',None)):
            if obj is not None:
                obj.filenameURL=name

    def soundcheckrefresh(self,dict=None):
        self.soundsettings.makedefaultifnot()
        self._refresh_test_filename()
        dictnow={
                'audio_card_in':self.soundsettings.audio_card_in,
                'fs':self.soundsettings.fs,
                'sample_format': self.soundsettings.sample_format,
                'audio_card_out': self.soundsettings.audio_card_out
                }
        """Call this just once. If nothing changed, wait; if changes, run,
        then run again."""
        if self.exitFlag.istrue() or self.exitFlag.istrue():
            self.on_quit()
            self.on_quit()
            return
        log.info("sound settings dict: {}".format(dict))
        self.resetframe()
        self.scroll=ui.ScrollingFrame(self.frame, row=0, column=0)
        self.content=self.scroll.content
        ui.Label(self.content, font='title',
                text=_(self.tasktitle),
                row=self.content.nrows())
        ui.Label(self.content, #font='title',
                text=_("(click any to change)"),
                row=self.content.nrows())
        self.labeltext={}
        for varname, cmd in [
            ('audio_card_in', self.getsoundcardindex),
            ('fs', self.getsoundhz),
            ('sample_format', self.getsoundformat),
            ('audio_card_out', self.getsoundcardoutindex),
                                                    ]:
            text=_("Change")
            self.labeltext[varname]=ui.StringVar()
            l=ui.Label(self.content,text=self.labeltext[varname],
                        row=self.content.nrows())
            l.bind('<ButtonRelease-1>',cmd) #getattr(self,str(cmd)))
        log.info("Done setting up labels")
        self.updatesoundcard()
        self.updatesoundhz()
        self.updatesoundformat()
        self.updatesoundcardoutindex()
        for k in self.labeltext:
            log.info(f"{k}: {self.labeltext[k].get()}")
        br=RecordButtonFrame(self.content,self,test=True,
                            row=self.content.nrows(),
                            sticky='')
        play=_("Play")
        l=_("Plug in your microphone, and make sure ‘record’ and ‘{play}’ work "
            "well here, before recording real data!").format(play=play)
        caveat=ui.Label(self.content,
                text=l,font='read',
                row=self.content.nrows(),
                sticky='')
        caveat.wrap()
        l=_("If Praat is installed in your OS path, right click on ‘{}’ above "
            "to open in Praat.").format(play)
        caveat3=ui.Label(self.content,
                text=l,font='default',
                row=self.content.nrows())
        caveat3.wrap()
        bd=ui.Button(self.content,
                    text=_("Done"),
                    cmd=self.soundcheckrefreshdone,
                    row=self.content.nrows(),
                    sticky='')
        self.scroll.reflow()  # grow canvas to cover the sound-settings rows
    def relabel_settings(self):
        """Re-read the settings onto the labels, without rebuilding the frame.

        Needed because a TAKE can change the settings: `_report_take` proves a
        rate upsampled, `note_fake_rate` drops it and re-picks, and the window
        went on displaying the old rate — so the switch was real, correct, and
        invisible (Kent 2026-09-10). `soundcheckrefresh` would show it too but
        it tears down and rebuilds the whole frame, which would destroy the
        record/play buttons the user is mid-way through using; these four
        updates just re-read the variables the labels are bound to.
        """
        # LABELS ONLY — deliberately NOT the test filename. Re-deriving it
        # here renamed the target AFTER the take, so a file recorded at
        # 192000 was then referred to as `test_44100_int32_6.wav` and played
        # back under that name (2026-09-10). The filename must be re-derived
        # BEFORE recording, which the click handlers already do; doing it
        # afterwards mislabels the take that just happened.
        for update in (self.updatesoundcard, self.updatesoundhz,
                       self.updatesoundformat, self.updatesoundcardoutindex):
            try:
                update()
            except Exception as e:
                log.info("couldn't update a sound setting label ({})"
                         .format(e))

    def soundcheckrefreshdone(self):
        self.task.storesoundsettings()
        self.on_quit()

    def on_quit(self, **kwargs):
        """GIVE THE TASK WINDOW BACK on the way out.

        `__init__` withdraws it (`:829`) so this window is not competing with
        the page behind it — and nothing ever undid that, so closing Sound
        Settings left the user with NO visible window at all (Kent,
        2026-09-11: "closing settings left no window?"; the log ends with two
        windows hidden and none shown).

        Here rather than in `soundcheckrefreshdone` so BOTH exits are covered
        — the Done button and the window's own close box, which is wired
        straight to this method (`:831`).

        Same shape as the wait-dialog fault fixed an hour earlier, and worth
        stating as a rule for this backend, where every window is a separate
        OS window rather than a Toplevel the WM keeps together: **whoever
        withdraws a window owns revealing it.**
        """
        try:
            self.task.deiconify()
        except Exception as e:
            log.info("couldn't bring the task window back ({})".format(e))
        return super().on_quit(**kwargs)
    tasktitle = "Sound Card Settings"
    def __init__(self,task,**kwargs):
        self.refreshdelay=1000 # wait 1s for a refresh check, always mainwindow
        self.program=task.program #needed to find praat
        log.info(f"Theme: {self.program.theme}")
        ui.Window.__init__(self,
                            task.ui, #this show be called from a task now
                            exit=False,
                            title=_(self.tasktitle),
                            withdrawn=True
                        )
        self.task=task
        self.soundsettings=self.program.soundsettings
        self.soundcheckrefresh()
        if not kwargs.get("withdrawn"):
            self.task.withdraw()
            self.deiconify()
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
class ASRModelSelectionWindow(ui.Window):
    def language_entry(self):
        self.language_frame=ui.Frame(self.languages_frame,
                                    row=0,column=0,
                                    sticky='new')
        self.sister_frame=ui.Frame(self.languages_frame,
                                    row=0,column=1,
                                    sticky='ew')
        ui.Label(self.language_frame,text=_("Language:"),ipadx=10,row=0,column=0)
        self.lang=ui.StringVar()
        ef=ui.EntryField(self.language_frame,textvariable=self.lang,
                        row=1, sticky='ew')
        self.langs_possible_var=ui.StringVar()
        ui.Label(self.language_frame,textvariable=self.langs_possible_var,
                font='small', ipadx=10, row=3)
        self.bind('<Return>', self.language_selection)
        self.bind('<Tab>', self.language_selection)
        self.bind('<Button-1>', self.language_selection)
        self.lang.trace_add('write', self.language_selection)
    def language_selection(self,*args):
        if hasattr(self,'lang_cur') and self.lang_cur == self.lang.get():
            return
        try:
            self.language_info.destroy()
        except Exception:
            pass
        try:
            self.lang_cur=self.lang.get()
            log.info(f"Getting language info for input {self.lang_cur}")
            display=self.languages.get_obj(self.lang_cur).full_display()
            possibles=self.languages.get_codes(self.lang_cur)
            displays=[self.languages.get_obj(j).full_display()
                                                    for j in possibles]
            log.info(f"Looking for languages related to {display}")
        except Exception as e:
            log.error(f"Language display error: {e}")
            self.lang_display_var.set(f"Error: '{self.lang_cur}' not found")
            self.sister_options=[_("Nothing")]
            self.update_n_sisters()
            self.sisters_listbox.delete(0, "end")
            return
        self.lang_display_var.set(display)
        self.langs_possible_var.set('\n'.join(displays))
        self.get_sister_options()
    def get_sister_options(self,*args):
        self.language=self.languages.get_obj(self.lang_cur)
        self.sister_options=[self.alllangs]
        self.sister_options.extend(
                self.language.supported_ancestor_objs_prioritized(
                    getattr(self,'sister_broaden',0))
                                )
        self.update_n_sisters()
        self.sisters_listbox.delete(0, "end")
        for i in self.sister_options:
            self.sisters_listbox.insert("end", i if isinstance(i,str)
                                                else i.full_display())
        max_value_len=max([len(self.sisters_listbox.get(i)) for i in range(len(self.sisters_listbox.get(0,'end')))])
        self.sisters_listbox.configure(width=min(max_value_len,60))
        self.restore_sister_selection()
        self.save_sister() #since it is showing, anyway.
    def restore_sister_selection(self):
        """Reflect the SAVED sister_languages subselection in the freshly
        populated listbox. Without this, the boot-time save_sister() below
        finds nothing selected, and its nothing-means-all branch silently
        clobbers the user's saved subselection with the full list
        (2026-07-07). Saved == full set (or nothing saved) selects the
        explicit 'all' option instead."""
        saved=set(self.soundsettings.asr_kwargs.get('sister_languages') or ())
        codes_by_index={i:opt.iso() for i,opt in enumerate(self.sister_options)
                        if opt != self.alllangs}
        wanted=[i for i,c in codes_by_index.items() if c in saved]
        self.sisters_listbox.select_clear(0,'end')
        if wanted and len(wanted) < len(codes_by_index):
            for i in wanted:
                self.sisters_listbox.select_set(i)
        else:
            self.sisters_listbox.select_set(0)
        self.last_selection_indexes=self.sisters_listbox.curselection()
    def save_sister(self,event=None):
        log.info("Saving sister language now")
        if (0 in self.sisters_listbox.curselection() and
                len(self.sisters_listbox.curselection())>1):
            #Force user to pick all(0) or some, not both
            if 0 in self.last_selection_indexes:
                self.sisters_listbox.select_clear(0)
            else:
                self.sisters_listbox.select_clear(1,'end')
        displays=[self.sisters_listbox.get(i) for i #indexed displays
                     in self.sisters_listbox.curselection()]
        lobjs=[self.sister_options[i] for i #indexed objs
                     in self.sisters_listbox.curselection() if i != 0]
        codes=[i.iso() for i in lobjs]
        displays_from_codes=[i.full_display() for i in lobjs]
        print(displays,[i.full_display() for i in self.sister_options
                                            if i != self.alllangs])
        if codes:
            log.info(f"Selected {codes}, {displays}")
        else:
            codes=[i.iso() for i in self.sister_options if i != self.alllangs]
            log.info(f"No language selected; using all: {codes}")
        self.kwarg_vars['sister_languages'].set(codes)
        self.save_kwarg_to_soundsettings('sister_languages',codes)
        self.last_selection_indexes=self.sisters_listbox.curselection()
        self._persist_soundsettings()   # a sister-language choice sticks to disk
    def update_n_sisters(self):
        n=len(self.sister_options)-1
        if n:
            self.n_sisters['text']=f"Related Languages with ASR support ({n}):"
            self.sister_frame.grid()
        else:
            self.sister_frame.grid_remove()
    def change_sister_scope(self,step):
        """'Include more/fewer languages' (Kent 2026-07-13): walk the
        language tree UP (broader family = more sister candidates) or back
        DOWN toward the first-found default (broaden=0, the old behavior).
        If a step up changes nothing (already at the top of the tree), the
        counter reverts so 'fewer' stays predictable."""
        old=getattr(self,'sister_broaden',0)
        new=max(old+step,0)
        if new==old:
            return
        before=[str(i) for i in self.sister_options]
        self.sister_broaden=new
        self.get_sister_options()
        if step>0 and [str(i) for i in self.sister_options]==before:
            self.sister_broaden=old #top of the tree; nothing broader
            return
        # A scope change means the user wants the NEW set, not their old
        # subselection (which restore_sister_selection just reinstated over
        # the rebuilt list): auto-select 'All of the below' and persist.
        self.sisters_listbox.select_clear(0,'end')
        self.sisters_listbox.select_set(0)
        self.last_selection_indexes=self.sisters_listbox.curselection()
        self.save_sister()
    def sister_selection(self):
        self.n_sisters=ui.Label(self.sister_frame,text='',
                                    ipadx=10,row=0,column=0)
        self.sisters_listbox=ui.ListBox(self.sister_frame,
                command=self.save_sister,
                # raw_command: this listbox is filled by manual .insert (not
                # optionlist), so the default _on_select choice-mapping throws on
                # an empty self.choices and save_sister never fires. save_sister
                # reads curselection() directly, so bind it raw to <<ListboxSelect>>.
                raw_command=True,
                font='default',
                selectmode='multiple',
                optionlist=[], #If analang later, populate then
                row=1,column=0,
                sticky='ew'
                )
        scope=ui.Frame(self.sister_frame,row=2,column=0,sticky='ew')
        ui.Button(scope,text=_("Include more languages"),
                cmd=lambda:self.change_sister_scope(1),row=0,column=0)
        ui.Button(scope,text=_("Include fewer languages"),
                cmd=lambda:self.change_sister_scope(-1),row=0,column=1)
    def make_kwargVars(self):
        log.info(f"making kwargVars for {self.soundsettings.asr_kwargs}")
        for k in self.soundsettings.asr_kwargs:
            # log.info(f"Looking at {k}")
            if k not in self.kwarg_vars: #if it is there, leave it alone!
                if isinstance(self.soundsettings.asr_kwargs[k],bool):
                    self.kwarg_vars[k]=ui.BooleanVar()
                elif isinstance(self.soundsettings.asr_kwargs[k],str):
                    self.kwarg_vars[k]=ui.StringVar()
                else:
                    self.kwarg_vars[k]=ui.Variable()
                self.kwarg_vars[k].set(self.soundsettings.asr_kwargs[k])
    def get_vars(self):
        self.kwarg_vars={}
        self.make_kwargVars()
        self.lang_display_var=ui.StringVar()
        self.asr_settings_w={}
    def save_kwargs_to_soundsettings(self):
        for k,v in self.kwarg_vars.items():
            self.save_kwarg_to_soundsettings(k,v)
        self._persist_soundsettings()
    def _persist_soundsettings(self):
        """Write soundsettings (incl. asr_kwargs / sister_languages) to disk so
        the choice persists across restarts. No-op until the window finishes
        init, so setup-time saves don't write partial kwargs."""
        if not getattr(self,'_ready',False):
            return
        try:
            self.program.settings.storesettingsfile(setting='soundsettings')
            log.info("Saved sound settings (asr_kwargs) to file.")
        except Exception as e:
            log.error(f"couldn't persist sound settings: {e}")
    def save_kwarg_to_soundsettings(self,k,v):
        if isinstance(v,ui.Variable):
            value=v.get()
        else:
            value=v
        # log.info(f"Starting Value: {value} ({type(value)})")
        try:
            assert self.soundsettings.asr_kwargs[k] == value
        except (AssertionError,KeyError):
            log.info(f"Changing {k} from "
                    f"{self.soundsettings.asr_kwargs.get(k,None)} "
                    f"to {value}")
            self.soundsettings.asr_kwargs[k]=value
        # This runs once before the ASR boots, when the above will suffice.
        if k in ['sister_languages'] and hasattr(self.soundsettings,'asr'):
            setattr(self.soundsettings.asr,k,value)
    def report_settings_strings(self):
        for k,v in self.kwarg_vars.items():
            if k in ['sister_languages']:
                row=self.strings_frame.grid_size()[1],
                ui.Label(self.strings_frame, text=f"{k}:", row=row, column=0)
                self.asr_settings_w[k]=ui.Label(self.strings_frame,
                                                textvariable=v,
                                                wraplength='50%',
                                                anchor='w',
                                                ipadx=10,
                                                row=row,
                                                borderwidth=1,
                                                column=1
                                                )
    def report_settings_bool(self,columns):
        self.boolean_frame_process=ui.Frame(self.boolean_frame,sticky='ew',
                                                                pady=10,r=0,c=0)
        self.boolean_frame_models=ui.Frame(self.boolean_frame,sticky='ew',
                                                                pady=10,r=1,c=0)
        self.boolean_frame_repos=ui.Frame(self.boolean_frame,sticky='ew',
                                                                rowspan=2,
                                                                pady=20,
                                                                padx=20,
                                                                r=0,c=1)
        m_buttons=p_buttons=-1
        for k,v in [(k,v) for k,v in self.kwarg_vars.items()
                        if isinstance(v,ui.BooleanVar)]:
            text=k
            if k in self.soundsettings.asr.repo_modelnames:
                if k in ["return_ipa"]:
                    continue
                parent=self.boolean_frame_models
                m_buttons+=1
                buttons=m_buttons
                if (self.soundsettings.asr.repo_modelnames[k]
                                    in self.soundsettings.asr_repos):
                    count=self.soundsettings.asr_repos[
                                    self.soundsettings.asr.repo_modelnames[k]]
                    text=f"k ({count})"
            else:
                parent=self.boolean_frame_process
                p_buttons+=1
                buttons=p_buttons
            self.asr_settings_w[k]=ui.CheckButton(parent,
                                        text = k,
                                        # no_default_indicator_images=True,
                                        variable = self.kwarg_vars[k],
                                        onvalue = True, offvalue = False,
                                        ipadx=10,
                                        sticky='ew',
                                        font='default',
                                        row=buttons//columns,
                                        column=buttons%columns
                                        )
        for frame in self.boolean_frame.winfo_children():
            for c in range(columns):
                frame.grid_columnconfigure(c, weight=1, uniform="uniwide")
        repos=sorted(self.soundsettings.asr_repos.items(),key=lambda x:-x[1])
        kwargs={'font':'small','sticky':'ew'}
        for n,(k,v) in enumerate(repos):
            ui.Label(self.boolean_frame_repos,text=k,r=n,**kwargs)
            ui.Label(self.boolean_frame_repos,text=v,r=n,c=1,**kwargs)
    def report_settings(self):
        self.settings_title=ui.Label(self.reload_frame,
                                    textvariable=self.lang_display_var,
                                    row=0,
                                    column=0,
                                    ipadx=10,
                                    anchor='w',
                                    sticky='we'
                                )
        self.report_settings_strings()
        self.report_settings_bool(columns=3)
        self.reload=ui.Button(self.reload_frame, text=_("Reload Model"),
                            command=self.reload_model,
                            row=0,column=1,
                            anchor='e',sticky='ew')
        # Next to Reload Model (Kent 2026-07-13: the page bottom is
        # inaccessible until its layout is fixed, so the button lives here).
        ui.Button(self.reload_frame, text=_("Run Bulk ASR"),
                            command=self._run_bulk_asr,
                            row=0,column=2,
                            anchor='e',sticky='ew')
    def settings_grid(self):
        self.title=ui.Label(self,text=self.page_title,font='title',
                                                    row=0,column=1)
        self.option_frame=ui.Frame(self,row=1,column=1)
        self.reload_frame=ui.Frame(self.option_frame,row=0,column=0,sticky='ew')
        self.languages_frame=ui.Frame(self.option_frame,
                                    row=1,column=0,
                                    sticky='ew')
        self.strings_frame=ui.Frame(self.option_frame,
                                    row=2,column=0,
                                    colspan=2,
                                    ipady=20,
                                    sticky='ew')
        self.boolean_frame=ui.Frame(self.option_frame,
                                    row=3,column=0,
                                    columnspan=2,
                                    ipady=10,
                                    sticky='ew')
        self.language_entry()
        self.sister_selection()
        self.report_settings()
    def changed_kwargs(self):
        return self.soundsettings.changed_kwargs()
    def reload_model(self):
        self.save_kwargs_to_soundsettings()
        #Decide if we reload entirely, or just change adaptors
        r=self.soundsettings.get_changed_kwargs()
        if not r:
            changed_kwargs=self.soundsettings.changed_kwargs
            if not changed_kwargs['all']: #.asr exists; no changes since loaded
                log.info(f"Didn't find any changed kwargs ({changed_kwargs})")
                log.info(f"kwargs is ({self.soundsettings.asr_kwargs})")
                return
        # changed_kwargs doesn't exist if r...
        # Only count models that will be loaded (not offloaded):
        if r or [i for i in changed_kwargs['repos'].values() if i]:
            self.wait(_("Reloading ASR model(s)")+'\n'+_(
                        "(This may require a large download)"),
                        thenshow=True)
        elif changed_kwargs: #any other values
            log.info("Changing settings (or dropping ASR models; not loading)")
            log.info(f"changed_kwargs: {changed_kwargs['all']} "
                        f"({bool(changed_kwargs['all'])})")
        log.info(f"asr_kwargs: {self.soundsettings.asr_kwargs}")
        # try/finally (not waiting()) because the dialog opens conditionally
        # above but waitdone() must run unconditionally; load_ASR() may raise
        # mid-download and must not leave the dialog stuck open.
        try:
            self.soundsettings.load_ASR()
        finally:
            self.waitdone()
    def modify(self):
        self.soundsettings.asr_kwargs['sister_languages']=['zmg']
        self.soundsettings.asr_kwargs['simplify_length']=False
    def __init__(self,task,**kwargs):
        window_title=_('Select ASR Settings')
        self.page_title=_('Settings for Transcription Model')
        log.info(f"Theme: {task.program.theme}")
        ui.Window.__init__(self,
                            task.ui,
                            exit=False,
                            title=window_title,
                            withdrawn=True
                            )
        self.program=task.program #needed to find praat
        self._ready=False   # persistence off until init completes (below)
        self.soundsettings=self.program.soundsettings
        if 'cache_dir' in self.soundsettings.asr_kwargs and not file.exists(self.soundsettings.asr_kwargs['cache_dir']):
            log.error(f"Cache dir {self.soundsettings.asr_kwargs['cache_dir']} "
                    "not found.")
            raise FileNotFoundError(self.soundsettings.asr_kwargs['cache_dir'])
        self.languages=self.program.languages
        try:
            self.analang=self.program.params.analang()
        except AttributeError:
            self.analang=self.program.analang #for testing
        self.alllangs=_("All of the below")
        self.get_vars()
        self.reload_model()
        self.make_kwargVars() #after ASR loaded, with full defaults
        self.settings_grid()
        if self.analang:
            self.lang.set(self.analang)
            self.get_sister_options() #Not on every change, but on boot
        self.save_kwargs_to_soundsettings()
        self._ready=True   # from here, changes persist to disk
        if not kwargs.get("withdrawn"):
            self.program.task.withdraw()
            self.deiconify()
    def _run_bulk_asr(self):
        try:
            self.withdraw()
            self.program.taskchooser.bulk_transcribe()
        except Exception as e:
            log.error(f"Bulk ASR launch failed: {e}")
class Task(ui.Window):
    def wait(self,x):
        print(x)
    def waitdone(self):
        pass
    def quittask(self):
        print("Not actually quitting task")
    def storesoundsettings(self):
        print("Not actually storing settings")
    def __init__(self,program):
        self.program=program
        self.theme=program.theme
        window_title=_('Test Task (Does nothing)')
        ui.Window.__init__(self,
                            program.tk_root,
                            # program.root,
                            exit=False,
                            title=window_title,
                            withdrawn=True
                            # state='withdrawn'
                            )
        #any sound task should find settings at self.soundsettings:
        self.soundsettings=program.soundsettings #Each task with sound should have this
        self.audio=program.soundsettings.audio
        self.audiolang=True
if __name__ == "__main__":
    try:
        _
    except:
        def _(x):
            return x
    from dummy import App
    program=App()
    program.praat='/home/kentr/bin/praat'
    program.hostname='karlap'
    program.name='A−Z+T'
    program.analang='tbt-CD'
    from backend import langtags
    program.languages=langtags.Languages(program)
    #This will normally pass self.audio from task to SoundSettings, to keep
    # one pyaudio instance, but if not, settings will create one.
    language=program.languages.get_obj(program.analang)
    program.soundsettings=sound.SoundSettings(program)
    program.soundsettings.initial_ASR_kwargs(language)
    log.info(f"asr_kwargs: {program.soundsettings.asr_kwargs}")
    r=ui.Root(program=program)
    r.title('Test Sound UI')
    program.task=Task(program=r.program)
    if r.program.hostname == 'karlap':
        r.program.soundsettings.asr_kwargs['cache_dir']='/media/kentr/hfcache'
    ssw=SoundSettingsWindow(program,withdrawn=True)
    ssw.setsoundcard_byname('default')
    ssw.destroy() #since not waiting
    log.info(f"asr_kwargs: {r.program.soundsettings.asr_kwargs}")
    # ssw.wait_window(ssw) #only if need to change stuff
    ssw=ASRModelSelectionWindow(program)
    log.info(f"asr_kwargs: {r.program.soundsettings.asr_kwargs}")
    ui.Label(r,text="Record sound to test Automatic Speech Recognition engines",row=0,column=0)
    RecordnTranscribeButtonFrame(r,program.task,test=True,
        show_transcriptions=True, #this typically in Entry
        show_tone=True,
        shown='all',
        row=2,column=0)
    r.deiconify()
    r.mainloop()
