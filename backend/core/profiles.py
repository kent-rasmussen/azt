# coding=UTF-8
"""Syllable profile analysis: builds CV profiles for every sense in the database.

Extracted from settings/__init__.py — this is computational analysis,
not settings read/write.
"""
from utilities import logsetup, rx
from utilities.utilities import setnesteddictval
from utilities.i18n import _
from backend.core.analysis import SliceDict, SyllableSliceDict

log = logsetup.getlog(__name__)

# Truthy sentinel "part of speech" for senses that have none. The CV profile is a
# ps-INDEPENDENT form fact, so ps-less words still get one — `profileofform`
# ignores ps for the value and only refuses to run when ps is falsy. They're
# computed but NOT added to the per-ps aggregation (sextracted/profilesbysense),
# since they belong to no ps and must not leak a phantom ps into segmental/reports.
PSLESS = '(no ps)'


class ProfileAnalyzer:
    def __init__(self, program):
        self.program = program
        self.program.profiles = self
        self._profile_conversions_logged = set() # input profiles already logged once
        self._invalid_logged = set()              # input profiles whose result was bad
        self._syls_none_logged = set()            # sense ids flagged for syls=None
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

    def _confirmed_primitives(self, sense, ftype):
        """(beg, end, syls) from this sense's VERIFIED syllable primitives (the
        'lc primitive verification' codes). Each stays None until that primitive
        is verified, so the profile constraint only acts on confirmed dimensions."""
        beg = end = syls = None
        for code in sense.primitiveverification(ftype):
            k, _sep, v = str(code).partition('=')
            if k == '#C':
                beg = v
            elif k == 'C#':
                end = v
            elif k == 'syls':
                syls = v
        return beg, end, syls

    def constrain_presort_profile(self, sense, profile, ftype):
        """Constrain a machine profile to the word's CONFIRMED primitives before it
        becomes a presort group (e.g. 'CVCV' → 'CVC' for a confirmed C_1_C word).
        No-op until primitives are verified. Logging: conversions and invalid
        results once per INPUT profile; syls=None once per sense id."""
        beg, end, syls = self._confirmed_primitives(sense, ftype)
        if beg is None and end is None and syls is None:
            return profile  # nothing confirmed → leave the machine analysis alone
        sid = getattr(sense, 'id', '?')
        if syls is None:  # confirmed #C/C# but no verified count — a data anomaly
            if sid not in self._syls_none_logged:
                self._syls_none_logged.add(sid)
                log.warning("Syllable presort: syls=None (no verified count) for "
                        "sense %s — confirmed #C=%s C#=%s.", sid, beg, end)
        r = self.program.params.constrain_profile(profile, beg, end, syls)
        new = r['profile']
        if not r['valid'] and profile not in self._invalid_logged:
            self._invalid_logged.add(profile)
            log.error("Syllable presort: result %s does NOT meet the constraints "
                    "(#C=%s C#=%s syls=%s) — e.g. sense %s. Please report.",
                    new, beg, end, syls, sid)
        if r['changed'] and profile not in self._profile_conversions_logged:
            self._profile_conversions_logged.add(profile)
            note = ' [fallback: CV-per-syllable]' if r['fallback'] else ''
            log.info("Syllable presort: %s → %s%s to fit confirmed primitives "
                    "(#C=%s C#=%s syls=%s) — logged once per input profile.",
                    profile, new, note, beg, end, syls)
        return new

    def getprofileofsense(self, sense, ps):
        form = sense.textvaluebyftypelang(self.profilesbysense['ftype'],
                                        self.profilesbysense['analang'])
        if not form:
            return form, None
        profile = self.rxdict.profileofform(form, ps=ps)
        if ps != PSLESS: # ps-less: compute the profile VALUE only, no per-ps aggregation
            self.extractsegmentsfromform(form, ps=ps)
        ftype=self.profilesbysense['ftype']
        if not set(self.profilelegit).issuperset(profile):
            profile = 'Invalid'
        # …-x-cvprofile_MT keeps the STRAIGHT machine analysis (or 'Invalid'),
        # irrespective of any constraint — it's the raw reference and the source
        # the 'affirm' shortcut copies into the data form.
        machine = profile
        sense.cvprofilemachinevalue(ftype, machine)  # raw machine analysis (always)
        # SLICE BY THE CONFIRMED PROFILE — the plain …-x-cvprofile DATA form
        # (cvprofilevalue, machine=False) — NOT the machine analysis nor a
        # constrained derivation of it. This makes _profilesbysense agree with the
        # status slice (sensesbyps_profile reads the same field), so a word is
        # segmentally sorted ONLY under its trusted profile, and the old two-index
        # divergence (sorted in CVC by constrained-machine, invisible to status by
        # data form) is gone. A word with no confirmed form is left OUT of segmental
        # slicing — it still gets syllable-prep'd to acquire one (senses() cvt='S'
        # uses the whole wordlist, not _profilesbysense). Keeping the current sort
        # (lc annotation) legal per primitives and clearing a mismatched cvprofile
        # verification are handled on load by scrub_sorts_to_primitives, not here.
        confirmed = sense.cvprofilevalue(ftype)
        if ps != PSLESS:
            setnesteddictval(self.formstosearch, [sense], ps, form, addval=True)
            if confirmed and confirmed != 'Invalid':
                setnesteddictval(self.profilesbysense, [sense], ps, confirmed,
                                 addval=True)
        return form, confirmed

    def _set_trusted_profile(self, sense, ftype, profile):
        """Write a trusted profile CONSISTENTLY: the plain …-x-cvprofile DATA and
        the profile-sort annotation (name=ftype, e.g. 'lc') that records which
        profile the word is sorted into. Keeping them aligned means the annotation
        never claims a different 'last sorted' group than the trusted profile,
        and the normal group/done check won't see a mismatch and unverify it."""
        sense.cvprofilevalue(ftype, profile)
        sense.annotationvaluebyftypelang(ftype, self.program.db.analang,
                                         ftype, profile)

    def affirm_machine_profiles(self, ftype=None, rebuild=True):
        """Accept the straight machine CV analysis as the (confirmed) profile DATA:
        copy each sense's …-x-cvprofile_MT into the plain …-x-cvprofile form, which
        the segmental/tone sorts read. For languages where syllable-profile sorting
        isn't worth it — they then proceed on the machine analysis as if confirmed,
        skipping SortSyllables. Rebuilds the ps-profile slices so the sorts pick the
        profiles up. Returns the number of senses affirmed."""
        ftype = ftype or self.program.params.ftype()
        n = 0
        for s in self.program.db.senses:
            # Fill HOLES only — never rewrite an existing profile (it may be
            # hand-verified good data; affirm must not clobber it). To repair
            # already-written bad profiles, use reconcile_profiles_to_primitives.
            if s.cvprofilevalue(ftype):
                continue
            m = s.cvprofilemachinevalue(ftype)
            if not m or m == 'Invalid':
                continue
            # Respect any verified syllable sorting: affirm the machine profile
            # CONSTRAINED to the word's confirmed primitives (#C/C#/syls), not the
            # raw _MT (e.g. machine 'CCVCV', 2 syls/V-final, on a word verified
            # C#=C, syls=1 → 'CCVC'). No verified primitives → no-op → raw machine.
            affirmed = self.constrain_presort_profile(s, m, ftype)
            if affirmed and affirmed != 'Invalid':
                self._set_trusted_profile(s, ftype, affirmed)
                n += 1
        log.info("Affirmed the machine CV analysis as profile data for %d "
                "sense(s).", n)
        if n:
            # Persist the plain forms to LIFT — otherwise a restart re-reads the
            # file without them and the "set up profiles?" trigger fires again.
            self.program.maybewrite(definitely=True)
        if rebuild and n:
            self.program.db.load_ps_profiles()  # "build slicedict after"
        return n

    def reconcile_profiles_to_primitives(self, ftype=None, rebuild=True):
        """Repair path (NOT normal flow): constrain each EXISTING plain profile to
        the word's confirmed #C/C#/syls. Unlike affirm (which only fills holes),
        this DOES touch existing profiles — but only to FIX ones that violate the
        verified primitives (e.g. a raw-machine 'CCVCV' affirmed onto a C#=C/syls=1
        word → 'CCVC'). A profile already consistent with its primitives is
        unchanged (constrain is a no-op), so good/verified data is never rewritten.
        Use this once to clean up profiles written by the old raw-copy affirm.
        Returns the count changed."""
        ftype = ftype or self.program.params.ftype()
        n = 0
        for s in self.program.db.senses:
            cur = s.cvprofilevalue(ftype)
            if not cur or cur == 'Invalid':
                continue
            fixed = self.constrain_presort_profile(s, cur, ftype)
            if not fixed or fixed == 'Invalid':
                continue
            anno = s.annotationvaluebyftypelang(ftype, self.program.db.analang,
                                                ftype)
            # Repair if the plain profile violated its primitives (fixed != cur)
            # OR the sort-group annotation drifted from the trusted profile (the
            # stale 'lc' the old raw affirm left, e.g. CCVCV while plain is CCVC).
            if fixed != cur or anno != fixed:
                self._set_trusted_profile(s, ftype, fixed)
                n += 1
        log.info("Reconciled %d profile(s) to their confirmed primitives.", n)
        if n:
            self.program.maybewrite(definitely=True)
        if rebuild and n:
            self.program.db.load_ps_profiles()
        return n

    def scrub_sorts_to_primitives(self, ftype=None):
        """Run on EVERY load. Keep the distinction between a word's CURRENT SORT
        POSITION (the `lc` annotation), which must always be legal per the word's
        confirmed primitives, and the user's TRUST decision (the confirmed
        `cvprofile` …-x-cvprofile form), which is what actually includes the word in
        segmental sorting (read by _profilesbysense / sensesbyps_profile). Per sense,
        in order:
          (1) MISSING profile sort (no `lc` annotation) → leave it; only a manual
              sort or the trust trigger adds one.
          (2) ILLEGAL profile sort (`lc` annotation violates confirmed primitives,
              e.g. 'CVCV' with #C=C/C#=C/syls=1) → constrain and rewrite the
              ANNOTATION (the sort), nothing else.
          (3) the (now-legal) `lc` annotation no longer matches the confirmed
              `cvprofile` form → CLEAR that cvprofile verification (do NOT migrate
              it). The word loses its trusted profile → drops out of segmental
              slicing → the profile-setup trigger fires so the user re-sets it
              manually or by trust.
        The `'<profile> lc verification'` SEGMENTAL fields are context-tagged by the
        profile they were confirmed under and are NOT touched. Self-healing: once the
        data is consistent, constrain is a no-op and nothing is written. Profile
        constraint requires confirmed primitives, so it no-ops on un-prepped words."""
        ftype = ftype or self.program.params.ftype()
        analang = self.program.db.analang
        fixed_sort = cleared_verif = 0
        for s in self.program.db.senses:
            anno = s.annotationvaluebyftypelang(ftype, analang, ftype)
            if not anno or anno == 'Invalid':
                continue  # (1) missing sort — never auto-add
            legal = self.constrain_presort_profile(s, anno, ftype)  # (2)
            if legal and legal != 'Invalid' and legal != anno:
                s.annotationvaluebyftypelang(ftype, analang, ftype, legal)
                anno = legal
                fixed_sort += 1
            confirmed = s.cvprofilevalue(ftype)  # (3) profile VERIFICATION
            if confirmed and confirmed != anno:
                s.cvprofilevalue(ftype, False)  # clear; word drops out → trigger
                cleared_verif += 1
        if fixed_sort or cleared_verif:
            log.info("Profile scrub: corrected %d illegal sort annotation(s); "
                     "cleared %d cvprofile verification(s) that no longer matched "
                     "the (legal) sort.", fixed_sort, cleared_verif)
            self.program.maybewrite(definitely=True)
        return fixed_sort, cleared_verif

    def migrate_cvprofiles_to_machine_form(self):
        """One-time migration. Old code wrote the machine analysis into the
        plain …-x-cvprofile form; now that form holds the user-confirmed sorting
        result (the data) and the analysis lives in the …-x-cvprofile_MT form.
        If NO _MT form exists anywhere for this ftype, the existing plain values
        are old analysis (regenerated every open), not user data — preserve each
        in its _MT form and clear the plain form so it isn't mistaken for a
        confirmed value. Idempotent: if any _MT form already exists, assume the
        migration was done. Runs before analysis reseeds the plain form."""
        ftype = self.profilesbysense['ftype']
        senses = self.program.db.senses
        if any(s.cvprofilemachinevalue(ftype) for s in senses):
            return  # analysis (_MT) form already present → already migrated
        moved = 0
        for s in senses:
            v = s.cvprofilevalue(ftype)
            if v:
                s.cvprofilemachinevalue(ftype, v)  # preserve old analysis in _MT
                s.cvprofilevalue(ftype, False)      # clear the data form
                moved += 1
        if moved:
            log.info("Migrated {n} '{ftype}' cvprofile value(s) from the data "
                    "form to the analysis (_MT) form".format(n=moved, ftype=ftype))

    def getprofilesbyps(self, ps):
        senses = self.program.db.sensesbyps[ps]
        self.sextracted[ps] = {}
        n = self._getprofiles(senses, ps)
        log.info(_("Processed {n} forms to {ps} syllable profiles").format(n=n, ps=ps))

    def _getprofiles(self, senses, ps):
        # SYNCHRONOUS (1.3.22): the old code spawned a fire-and-forget thread per
        # sense and joined only the LAST one, so nearly all profile computations
        # raced — concurrently mutating the shared XML tree and the aggregation
        # dicts (sextracted/profilesbysense/formstosearch), which could land wrong
        # or incomplete and even differ run-to-run. Profile computation is cheap
        # regex work (and under the GIL the threads bought no real CPU win), so run
        # it in order: deterministic and race-free.
        todo = len(senses)
        for n, sense in enumerate(senses, 1):
            form, profile = self.getprofileofsense(sense, ps)
            if n % 100 == 0:
                log.debug(_("{count}: {form} > {profile}").format(
                    count=str(n)+'/'+str(todo), form=form, profile=profile))
        return len(senses)

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
        self._profile_conversions_logged = set() # per run: one line per input profile
        self._invalid_logged = set()
        self._syls_none_logged = set()
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
        self.migrate_cvprofiles_to_machine_form()
        # Keep each word's profile SORT (lc annotation) legal per its confirmed
        # primitives, and clear any cvprofile verification that no longer matches —
        # BEFORE the slices below are built (they read the confirmed cvprofile form).
        self.scrub_sorts_to_primitives()
        if self.program.params.PROFILE_CONSTRAINT.get('force_resort'):
            log.warning("PROFILE_CONSTRAINT['force_resort'] is ON (TESTING): "
                    "re-deriving EVERY word's syllable profile from the "
                    "constrained machine analysis, OVERWRITING confirmed sort "
                    "data. Turn it off and don't save over good data.")
        for ps in self.program.db.pss:
            self.getprofilesbyps(ps)
        # ps-INDEPENDENT coverage: a sense with no part of speech still has a form,
        # hence a CV profile, hence syllable-prep primitives. The loop above skips
        # it (db.pss drops falsy ps values), so compute its profile here too —
        # value only, under the PSLESS sentinel, with no per-ps aggregation.
        psless=[s for s in self.program.db.senses if not s.psvalue()]
        if psless:
            n=self._getprofiles(psless, PSLESS)
            log.info("Computed CV profiles for {n} part-of-speech-less word(s) "
                    "(prep is wordlist-wide; they have no ps for per-ps sorts)"
                    .format(n=n))
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
        # If syllable prep has been STARTED (any word carries a #C primitive),
        # re-seed the primitives from the now-current profiles and rebuild the prep
        # slice node AT LOAD — so syllable_prep_complete is honest without waiting
        # for a 'Sort!' press (a word that only just became analyzable, e.g.
        # 'always', gets its syls now, not on the next prep run). Pristine DBs are
        # left untouched. Same idempotent rule (params.seed_sense_primitives) as
        # the prep-task presort, so the two can't drift.
        ftype = self.program.params.ftype()
        analang = self.program.db.analang
        if any(s.annotationvaluebyftypelang(ftype, analang, '#C')
                for s in self.program.db.senses):
            tally = {'seeded': 0, 'defaulted': 0, 'syls': 0}
            for s in self.program.db.senses:
                tag = self.program.params.seed_sense_primitives(s, ftype, analang)
                if tag in tally:
                    tally[tag] += 1
            if any(tally.values()):
                log.info("Load: seeded syllable primitives (seeded=%d defaulted=%d "
                        "syls-backfilled=%d).", tally['seeded'], tally['defaulted'],
                        tally['syls'])
            try:
                SyllableSliceDict(self.program,
                                self.program.slices.ps(), ftype).build()
            except Exception as e:
                log.info("Load: couldn't rebuild syllable prep slices: %s", e)
        if self.program.slices.profile():
            self.getscounts()
        self.program.settings.storesettingsfile(setting='profiledata')
