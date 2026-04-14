# coding=UTF-8
"""Syllable profile analysis: builds CV profiles for every sense in the database.

Extracted from settings/__init__.py — this is computational analysis,
not settings read/write.
"""
import threading
from utilities import logsetup, rx
from utilities.utilities import setnesteddictval
from utilities.i18n import _
from backend.core.analysis import SliceDict

log = logsetup.getlog(__name__)


class ProfileAnalyzer:
    def __init__(self, program):
        self.program = program
        self.program.profiles = self
        self.setvalidcharacters()

    def setvalidcharacters(self):
        """These are sent to rxdict, but the top two are also used here"""
        self.profilesegments = ['N','G','S','D','C','V','ʔ']
        self.profilelegit = ['̃','N','G','S','D','C','Ṽ','V','ʔ','ː',"̀",'=','<','.']
        self.invalidchars = [' ','...',')','(<field type="tone"><form lang="gnd"><text>']

    # ------------------------------------------------------------------
    # Polygraph handling
    # ------------------------------------------------------------------

    def checkforpolygraphsindata(self):
        for lang in self.program.db.s:
            for sclass in [sc for sc in self.program.db.s[lang]
                                if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                if self.program.db.s[lang][sclass]:
                    return True

    def polygraphLWCdefaults(self):
        lwcdefaults = {
            'en': {
                'D': {'gh':True, 'bb':True, 'dd':True, 'gg':True, 'gu':True,
                       'mb':False, 'nd':False, 'dw':False, 'gw':False, 'zl':False},
                'C': {'ckw':False, 'thw':False, 'tch':True, 'cc':True, 'pp':True,
                       'pt':False, 'tt':True, 'ck':True, 'qu':True, 'mp':False,
                       'nt':False, 'nk':False, 'tw':False, 'kw':False, 'ch':True,
                       'ph':True, 'sh':True, 'hh':True, 'ff':True, 'sc':False,
                       'ss':True, 'th':True, 'sw':False, 'hw':True, 'ts':False,
                       'sl':False},
                'G': {'yw':False},
                'N': {'mm':True, 'ny':False, 'gn':True, 'nn':True, 'nw':False},
                'S': {'rh':True, 'wh':True, 'll':True, 'rr':True, 'lw':False,
                       'rw':False},
                'V': {'ou':True, 'ei':True, 'ai':True, 'yi':True, 'ea':True,
                       'ay':True, 'ee':True, 'ey':True, 'ie':True, 'oa':True,
                       'oo':True, 'ow':True, 'ue':True, 'oe':True, 'au':True,
                       'oi':True, 'eau':True},
            },
            'fr': {
                'D': {'gh':False, 'bb':False, 'dd':False, 'gg':False, 'gu':True,
                       'mb':False, 'nd':False, 'dw':False, 'gw':False, 'zl':False},
                'C': {'ckw':False, 'thw':False, 'tch':True, 'cc':True, 'pp':True,
                       'pt':False, 'tt':False, 'ck':False, 'qu':True, 'mp':False,
                       'nt':False, 'nk':False, 'tw':False, 'kw':False, 'ch':True,
                       'ph':True, 'sh':False, 'hh':False, 'ff':False, 'sc':False,
                       'ss':True, 'th':True, 'sw':False, 'hw':False, 'ts':False,
                       'sl':False},
                'G': {'yw':False},
                'N': {'mm':False, 'ny':False, 'gn':True, 'nn':False, 'nw':False},
                'S': {'rh':True, 'wh':True, 'll':True, 'rr':True, 'lw':False,
                       'rw':False},
                'V': {'ou':True, 'ei':True, 'ai':True, 'yi':False, 'ea':True,
                       'ay':False, 'ee':False, 'ey':False, 'ie':True, 'oa':True,
                       'oo':True, 'ow':False, 'ue':True, 'oe':True, 'au':True,
                       'oi':True, 'eau':True},
            },
        }
        analang = self.program.params.analang()
        langnames = self.program.settings.languagenames
        if analang in lwcdefaults:
            log.info(_("It looks like you're working on your LWC; using {lang} digraph defaults")
                    .format(lang=langnames[analang]))
            return lwcdefaults[analang]
        try:
            interlang = self.program.interfacelang()
            log.info(_("Using your interface language ({lang}) digraph defaults")
                    .format(lang=langnames[interlang]))
            return lwcdefaults[interlang]
        except KeyError:
            log.info(_("It looks like neither your LWC ({analang}) nor your interface language ({interlang}) "
                    "has a set of digraph defaults, so not providing any")
                    .format(analang=langnames[analang],
                            interlang=langnames[self.program.interfacelang()]))
            return {}

    def polygraphcheck(self):
        log.info(_("Checking for Digraphs and Trigraphs!"))
        firstrun = False
        if not hasattr(self, 'polygraphs'):
            firstrun = True
            self.polygraphs = {}
        for lang in self.program.db.analangs:
            if lang not in self.program.db.s:
                log.error(_("Language {lang} found without segment settings."
                            ).format(lang=lang))
                continue
            if lang not in self.polygraphs:
                self.polygraphs[lang] = self.polygraphLWCdefaults()
            for sclass in [sc for sc in self.program.db.s[lang]
                                    if ('dg' in sc or 'tg' in sc or 'qg' in sc)]:
                pclass = sclass.replace('dg','').replace('tg','').replace('qg','')
                if pclass not in self.polygraphs[lang]:
                    self.polygraphs[lang][pclass] = {}
                for pg in self.program.db.s[lang][sclass]:
                    if not firstrun and pg not in self.polygraphs[lang][pclass]:
                        log.info(_("{polygraph} ({pclass}/{sclass}) has no Di/Trigraph setting; "
                        "prompting user for info.").format(polygraph=pg,pclass=pclass,sclass=sclass))
                        if self.program.settings.askaboutpolygraphs(onboot=True):
                            log.info(_("Asked about polgraphs, but user "
                                        "exited, so exiting {name}"
                                        ).format(name=self.program.name))
                            self.program.mainwindow.on_quit()
                        return
        log.info("Di/Trigraph settings seem complete; moving on.")

    # ------------------------------------------------------------------
    # Interpretation / distinguish defaults
    # ------------------------------------------------------------------

    def checkinterpretations(self):
        """This sets sane defaults, if not there"""
        if (not hasattr(self, 'distinguish')) or (self.distinguish is None):
            self.distinguish = {}
        if (not hasattr(self, 'interpret')) or (self.interpret is None):
            self.interpret = {}
        for var in self.profilelegit + [i+'wd' for i in self.profilesegments]:
            if var in ['C','V']:
                continue
            if ((var not in self.distinguish) or
                (type(self.distinguish[var]) is not bool)):
                self.distinguish[var] = False
            """These defaults are not settable, yet:"""
            if var in ["̀",'ː']:  # typically word-forming
                self.distinguish[var] = False
            if var in ['<','=','.']:  # typically not word-forming
                self.distinguish[var] = True
        for var in ['NC','CG','CS','VV','VN']:
            if ((var not in self.interpret) or
                (type(self.interpret[var]) is not str) or
                not(1 <= len(self.interpret[var]) <= 2)):
                if 'V' in var:
                    self.interpret[var] = var
                else:
                    self.interpret[var] = 'CC'
        if self.interpret['VV'] == 'Vː' and self.distinguish['ː'] == False:
            self.interpret['VV'] = 'VV'
        log.log(2, "self.distinguish: {}".format(self.distinguish))

    # ------------------------------------------------------------------
    # Segment lists and regex setup
    # ------------------------------------------------------------------

    def slists(self):
        """Sets up the lists of segments, by types, from the lift database."""
        log.info(_("Found db.analangs: {langs}").format(langs=self.program.db.analangs))
        log.info(_("Found params analang: {lang}").format(lang=self.program.params.analang()))
        self.s = {l: {} for l in set(self.program.db.analangs +
                                [self.program.db.analang])}
        for lang in set(self.s) & set(self.program.db.s):
            for sclass in [x for x in self.program.db.s[lang]
                                        if 'dg' not in x
                                        and 'tg' not in x
                                        and 'qg' not in x]:
                try:
                    assert sclass in self.polygraphs[lang]
                    pgthere = [k for k, v in self.polygraphs[lang][sclass].items() if v]
                    log.debug(_("Polygraphs for {lang} in {sclass}: {pgs}").format(
                        lang=lang, sclass=sclass, pgs=pgthere))
                    self.s[lang][sclass] = pgthere
                except (AssertionError, AttributeError):
                    self.s[lang][sclass] = list()
                self.s[lang][sclass] += self.program.db.s[lang][sclass]
            log.info(_("Segment lists for {lang} language: {segments}").format(
                lang=lang, segments=self.s[lang]))
        for lang in set(self.s) - set(self.program.db.s):
            self.s[lang] = self.program.db.hypotheticals
            log.info(_("Segment lists for {lang} language: {segments}").format(
                lang=lang, segments=self.s[lang]))

    def setupCVrxs(self):
        self.slists()  # makes s; depends on polygraphs
        analang = self.program.db.analang
        glyphs_present = self.program.status.all_groups_verified_anywhere()
        for cvt in glyphs_present:
            if cvt == 'V':
                there = self.s[analang][cvt]
            else:
                there = [i
                        for k in ({'C'} | {ki for ki in self.distinguish
                            if not self.distinguish[ki]}) & set(self.s[analang])
                        for j in self.s[analang][k]
                        if k in self.s[analang]
                        for i in j
                    ]
            self.s[analang][cvt].extend(glyphs_present[cvt] - set(there))
        self.rxdict = rx.RegexDict(distinguish=self.distinguish,
                                interpret=self.interpret,
                                sdict=self.s[self.program.db.analang],
                                profilelegit=self.profilelegit,
                                invalidchars=self.invalidchars,
                                profilesegments=self.profilesegments)

    def addtoCVrxs(self, s):
        """Add a new grapheme while running, so we don't have to restart
        between C/V changes."""
        if not hasattr(self, 'analang'):
            self.analang = self.program.db.analang
        cvt = self.program.params.cvt()
        analang = self.program.db.analang
        if cvt in ['C', 'V'] and s not in self.s[analang][cvt]:
            self.s[analang][cvt] += [s]
            self.rxdict.makeglyphregex(cvt)

    # ------------------------------------------------------------------
    # Profile extraction
    # ------------------------------------------------------------------

    def addtoprofilesbysense(self, sense, ps, profile):
        setnesteddictval(self.profilesbysense, [sense], ps, profile, addval=True)
        try:
            self.profilesbysense[ps][profile] += [sense]
        except KeyError:
            try:
                self.profilesbysense[ps][profile] = [sense]
            except KeyError:
                self.profilesbysense[ps] = {profile: [sense]}

    def addtoformstosearch(self, sense, form, ps, oldform=None):
        setnesteddictval(self.formstosearch, [sense], ps, form, addval=True)
        if oldform:
            try:
                self.formstosearch[ps][oldform].remove(sense)
                log.info(_("Removed {form} ({val})").format(
                    form=form, val=self.formstosearch[ps][form]))
            except ValueError:
                log.error(_("Apparently {sense} isn't under {form}?").format(
                    sense=sense, form=form))
            if not self.formstosearch[ps][oldform]:
                del self.formstosearch[ps][oldform]
                log.info(_("Deleted key of empty list"))

    def getprofileofsense(self, sense, ps):
        form = sense.textvaluebyftypelang(self.profilesbysense['ftype'],
                                        self.profilesbysense['analang'])
        if not form:
            return form, None
        profile = self.rxdict.profileofform(form, ps=ps)
        self.extractsegmentsfromform(form, ps=ps)
        if not set(self.profilelegit).issuperset(profile):
            profile = 'Invalid'
        setnesteddictval(self.profilesbysense, [sense], ps, profile, addval=True)
        setnesteddictval(self.formstosearch, [sense], ps, form, addval=True)
        sense.cvprofilevalue(self.profilesbysense['ftype'], profile)
        return form, profile

    def getprofilesbyps(self, ps):
        senses = self.program.db.sensesbyps[ps]
        self.sextracted[ps] = {}
        n = self._getprofiles(senses, ps)
        log.info(_("Processed {n} forms to {ps} syllable profiles").format(n=n, ps=ps))

    def _getprofiles(self, senses, ps):
        n = 0
        todo = len(senses)
        for sense in senses:
            n += 1
            if n % 100:
                t = threading.Thread(target=self.getprofileofsense,
                                    args=(sense, ps))
                t.start()
            else:
                form, profile = self.getprofileofsense(sense, ps)
                log.debug(_("{count}: {form} > {profile}").format(
                    count=str(n)+'/'+str(todo), form=form, profile=profile))
        try:
            t.join()
        except UnboundLocalError:
            pass
        return n

    def extractsegmentsfromform(self, form, ps):
        for s in set(self.profilelegit) & set(self.rxdict.rx):
            for i in [j for j in self.rxdict.rx[s][0].findall(form) if j]:
                i = ''.join(i).lower()
                setnesteddictval(self.sextracted, 1, ps, s, i, addval=True)

    def getscounts(self):
        """This depends on self.sextracted, from run(), so should only
        run when that changes."""
        scount = {}
        for ps in self.sextracted:
            scount[ps] = {}
            for s in self.rxdict.rx:
                try:
                    scount[ps][s] = sorted(
                        [(x, self.sextracted[ps][s][x])
                         for x in self.sextracted[ps][s]],
                        key=lambda x: x[1], reverse=True)
                except KeyError:
                    pass
        self.program.slices.scount(scount)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self):
        """Build CV profiles for every sense in the database."""
        # Pick up persisted profile config from settings (loaded from file)
        s = self.program.settings
        for attr in ('distinguish', 'interpret', 'polygraphs', 'sextracted',
                     'scount', 'adhocgroups'):
            val = getattr(s, attr, None)
            if val is not None:
                setattr(self, attr, val)
        self.profileswdatabyentry = {}
        self.profilesbysense = {}
        self.profilesbysense['Invalid'] = []
        self.profilesbysense['analang'] = self.program.db.analang
        self.profilesbysense['ftype'] = self.program.params.ftype()
        self.profiledguids = []
        self.formstosearch = {}
        self.sextracted = {}
        self.program.settings.notifyuserofextrasegments()
        self.polygraphcheck()
        self.checkinterpretations()
        self.setupCVrxs()
        for ps in self.program.db.pss:
            self.getprofilesbyps(ps)
        if hasattr(self, 'adhocgroups'):
            for ps in self.adhocgroups:
                for a in self.adhocgroups[ps]:
                    log.debug("Adding {} to {} ps-profile: {}".format(
                        a, ps, self.adhocgroups[ps][a]))
                    these = [self.program.db.sensedict[i]
                            for i in self.adhocgroups[ps][a]]
                    setnesteddictval(self.profilesbysense, these, ps, a)
        else:
            self.adhocgroups = {}
        SliceDict(self.adhocgroups, self.profilesbysense, self.program)
        if self.program.slices.profile():
            self.getscounts()
        self.program.settings.storesettingsfile(setting='profiledata')
