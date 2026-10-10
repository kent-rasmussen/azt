#!/usr/bin/env python3
# coding=UTF-8
"""Dekereke (Rod Casali) <-> LIFT conversion, XSLT-driven, mirroring io_put/xlp.py.

Dekereke (https://casali.canil.ca/) keeps a phonology database as a flat table:
a <phon_data> root of <data_form> records whose child element names ARE the
columns. Those names are defined by the user, per database, so nothing here may
hard-code them — we read the inventory, guess what each column is for, and ask.

The mapping itself lives in dekereke_transforms/*.xsl, next to xlptransforms/.
This module is what a stylesheet cannot be: it hands the parser raw bytes (three
encodings are live in the field), mints the guids and timestamps XSLT 1.0 has no
way to make, guesses the column roles, and keeps the sidecar that lets an export
put back everything A-Z+T doesn't understand.
"""
from utilities.i18n import _
from utilities import logsetup
log=logsetup.getlog(__name__)
from utilities import file
from xml.etree import ElementTree as ET #stdlib at import time, as in xlp.py
import datetime
import pathlib
import re
from random import randint

ROOTTAG='phon_data'
RECORDTAG='data_form'
"""Elements with children are structure, not columns: Dekereke nests Praat
measurements in <qvp_acoustic_data_>, which has no LIFT home."""
SETTINGSSUFFIX='-DkUserSettings.xml'
SIDECARSUFFIX='.dekereke.xml'
"""backend/langtags.py:43 — note the Zxxx; a bare -x-audio is NOT recognized."""
AUDIOSUFFIX='-Zxxx-x-audio'
NAME=re.compile(r'^[A-Za-z_][\w.\-]*$')

class Error(Exception):
    """Base class for exceptions in this module."""
    pass
class BadParseError(Error):
    def __init__(self, filename):
        self.filename=filename
        super().__init__(_("{file} isn’t a Dekereke database file."
                            ).format(file=filename))
class LxmlMissing(Error):
    pass

def lxml():
    """The one defensive import, as io_put/xlp.py:90-95 does it — but raising,
    so a caller can tell the user why nothing happened."""
    try:
        import lxml.etree
    except ImportError:
        log.info(_("Couldn’t find/import lxml, so not converting Dekereke data."))
        raise LxmlMissing(_("Converting Dekereke files needs the ‘lxml’ module, "
                            "which isn’t installed."))
    return lxml.etree

def available():
    """Ask before offering the feature, so it is never offered and then refused."""
    try:
        lxml()
        return True
    except LxmlMissing:
        return False

def transformsdir():
    """NOT file.gettransformsdir(): that one looks under utilities/ and returns
    an error string. io_put/cawl.py resolves bundled data this way."""
    return file.pathname_from_base_dir('dekereke_transforms')

class DekerekeXML(object):
    """A Dekereke file as data: its columns in the database's own order, its
    records, and the audio folder its sibling settings file points at."""
    def __init__(self, filename):
        self.filename=pathlib.Path(filename)
        raw=self.filename.read_bytes()
        """Bytes, never str: the older releases write UTF-16LE with an
        encoding="utf-16" declaration, and a decoded string makes the parser
        refuse the declaration outright."""
        try:
            self.tree=ET.ElementTree(ET.fromstring(raw))
        except ET.ParseError as e:
            log.error(_("{file} doesn’t parse as XML ({error})").format(
                                                file=self.filename,error=e))
            raise BadParseError(self.filename)
        if self.tree.getroot().tag != ROOTTAG:
            log.error(_("{file} has root ‘{tag}’, not ‘{expected}’").format(
                                        file=self.filename,
                                        tag=self.tree.getroot().tag,
                                        expected=ROOTTAG))
            raise BadParseError(self.filename)
        self.utf16=raw[:2] in (b'\xff\xfe', b'\xfe\xff')
        self.crlf=b'\r\n' in raw[:4096]
        self.getcolumns()
        self.getaudiodir()
        log.info(_("Read {records} Dekereke records, {columns} columns, from "
                    "{file}").format(records=len(self.records()),
                                    columns=len(self.columns),
                                    file=self.filename.name))
    def records(self):
        return self.tree.getroot().findall(RECORDTAG)
    def getcolumns(self):
        """First-seen order is Dekereke's own column order, and the order an
        export has to put back."""
        self.columns=[]
        for record in self.records():
            for node in record:
                if len(node): #children mean structure, not a column
                    continue
                if node.tag not in self.columns:
                    self.columns.append(node.tag)
        return self.columns
    def badcolumnnames(self):
        """xsl:element aborts the whole export on a name XML won't take, and it
        aborts part-written, so check before starting."""
        return [c for c in self.columns if not NAME.match(c)]
    def getaudiodir(self):
        """Dekereke keeps bare .wav names in the database and the folder — plus
        the per-column recording suffixes — in a sibling settings file."""
        self.audiodir=None
        self.audiosuffixes={}
        settings=self.filename.with_name(self.filename.stem+SETTINGSSUFFIX)
        if not settings.exists():
            log.info(_("No {file}; we’ll have to ask where the sound files are."
                        ).format(file=settings.name))
            return
        try:
            root=ET.fromstring(settings.read_bytes())
        except ET.ParseError:
            log.error(_("{file} doesn’t parse; ignoring it.").format(
                                                        file=settings.name))
            return
        node=root.find('.//sound_file_path')
        if node is not None and node.text:
            self.audiodir=node.text
            log.info(_("Dekereke sound files: {dir}").format(dir=self.audiodir))
        """A database may hold several takes of one word — one per column —
        named by suffixing the record's sound file: 'Phonetic<TAB>-phon'."""
        for node in root.iter('column_to_sound_file_suffix_mapping'):
            if node.text and '\t' in node.text:
                column,suffix=node.text.split('\t',1)
                self.audiosuffixes[column.strip()]=suffix.strip()
        if self.audiosuffixes:
            log.info(_("Dekereke records a separate take for {columns}").format(
                        columns=', '.join(sorted(self.audiosuffixes))))
        return self.audiodir
    def values(self, column):
        """Every non-empty value in a column — what a guess is checked against."""
        return [n.text for r in self.records() for n in r.findall(column)
                                            if n is not None and n.text]

"""Column-name cues. The exact-match rules come from the Phonology Assistant
add-on's AutoMapper (Seth Johnston, dual-licensed for use here); the pattern
rules below are new, because A-Z+T has homes for elicitation frames and
paradigm slots that Phonology Assistant had not."""
CUES=[ #ordered: an earlier role claims a column first, and fills only once
        ('phonetic',    ['phonetic','fonetik','ipa']),
        ('reference',   ['reference','ref','no','nomor']),
        ('tone',        ['pitch','tone','nada','surface_melody']),
        ('phonemic',    ['phonemic','fonemik']),
        ('gloss',       ['gloss','arti','englishgloss']),
        ('gloss2',      ['indonesiangloss','gloss2','artiindonesia',
                                                            'nationalgloss']),
        ('pos',         ['category','pos','partofspeech','kategori',
                                                            'kelaskata']),
        ('orthographic',['orthography','tulisan','ejaan']),
        ('audio',       ['soundfile','audio','sound','rekaman']),
        ('note',        ['notes','note','catatan']),
        ('cvprofile',   ['syllableprofile','profile','cvprofile','polasuku']),
        ('skipflag',    ['kosong','empty','skip','omit']),
        ]
PARADIGMCUES=['cmpl','incmp','imp','svc','seq','pl','perf','jamak','perintah']
SPEAKERCUES=['speaker','penutur']
PITCHSUFFIX='_Pitch'
ROLES=['phonetic','reference','tone','phonemic','gloss','pos','orthographic',
        'audio','note','cvprofile','cvprofileok','skipflag','frame','pitchtwin',
        'field','ignore']

class ColumnMap(object):
    """Which column plays which role. Guessed, then confirmed by the user:
    column names are per-database, so guessing is the best we can do, and
    confirming is why we must not do it silently."""
    def __init__(self, columns=None, analang=None, glosslangs=None):
        self.columns=list(columns or [])
        self.analang=analang
        self.glosslangs=list(glosslangs or [])
        self.roles={}
        self.langs={}
        self.twins={} #frame column -> the _Pitch column holding its tone
        self.suffixes={} #column -> its own recording's filename suffix
        self.audiodir=None
        self.utf16=False
    def automap(self):
        lowered={}
        for column in reversed(self.columns): #so the first of a pair wins
            lowered[column.lower()]=column
        for role,cues in CUES:
            for cue in cues:
                column=lowered.get(cue)
                if column and column not in self.roles:
                    self.setrole(column,role)
                    break
        self.mappitchtwins()
        self.mapbypattern()
        for column in self.columns: #nothing is dropped without being seen
            self.roles.setdefault(column,'field')
        log.info(_("Guessed roles for {n} of {total} Dekereke columns").format(
                    n=len([c for c in self.roles if self.roles[c]!='field']),
                    total=len(self.columns)))
        return self.roles
    def setrole(self, column, role, lang=None):
        if role=='gloss2':
            role,lang='gloss',lang or self.glosslang(1)
        elif role=='gloss':
            lang=lang or self.glosslang(0)
        self.roles[column]=role
        if lang:
            self.langs[column]=lang
    def glosslang(self, n):
        if len(self.glosslangs) > n:
            return self.glosslangs[n]
        return self.glosslangs[0] if self.glosslangs else 'en'
    def mappitchtwins(self):
        """‘goodX_Pitch’ holds the tone of ‘goodX’ — but only if ‘goodX’ is a
        column too, and plenty of frames have no twin."""
        for column in self.columns:
            if not column.endswith(PITCHSUFFIX):
                continue
            stem=column[:-len(PITCHSUFFIX)]
            if stem in self.columns:
                self.twins[stem]=column
                self.roles[column]='pitchtwin'
            else:
                self.roles.setdefault(column,'tone')
    def mapbypattern(self):
        """An elicitation frame is written with a capital X where the word goes
        (goodX, Xbad, Xwater); a paradigm slot is named for the slot."""
        for column in self.columns:
            if column in self.roles:
                continue
            lower=column.lower()
            if 'X' in column:
                self.roles[column]='frame'
            elif any(lower.startswith(c) for c in PARADIGMCUES):
                self.roles[column]='frame'
            elif any(lower.startswith(c) for c in SPEAKERCUES):
                self.roles[column]='field'
    def role(self, column):
        return self.roles.get(column,'field')
    def columnsforrole(self, role):
        return [c for c in self.columns if self.role(c)==role]
    def phonetic(self):
        """The one column A-Z+T will analyze. A-Z+T holds a single citation
        form per entry, so a database with several speakers' columns forces a
        choice — which is the most important thing the user confirms."""
        columns=self.columnsforrole('phonetic')
        return columns[0] if columns else None
    def fieldname(self, column):
        return 'Dk_'+re.sub(r'\W','_',column)
    def check(self):
        """User-facing text if this map can't be used, else None."""
        if not self.analang:
            return _("No language code is set for the forms.")
        if not self.phonetic():
            return _("No column is set as the form to analyze. A-Z+T needs one "
                    "— usually the phonetic transcription.")
    def bookkeepinglang(self):
        """A-Z+T tags its own bookkeeping with the first gloss language it
        finds IN THE FILE, so use a language this database actually glosses in
        — a database with only Indonesian glosses must not be labelled 'en'."""
        for column in self.columnsforrole('gloss'):
            if self.langs.get(column):
                return self.langs[column]
        return self.glosslang(0)
    def node(self):
        """The map as the document the stylesheets read (lxml refuses a
        node-set parameter, so this travels as a file)."""
        root=ET.Element('dekerekeMap',attrib={'analang':self.analang or '',
                                    'g1':self.bookkeepinglang(),
                                    'audio':self.analang+AUDIOSUFFIX
                                                if self.analang else ''})
        for n,lang in enumerate(self.glosslangs):
            ET.SubElement(root,'glosslang',attrib={'lang':lang,'n':str(n)})
        for column in self.columns:
            attrib={'name':column,'role':self.role(column)}
            if column in self.langs:
                attrib['lang']=self.langs[column]
            if column in self.twins:
                attrib['pitch']=self.twins[column]
            if column in self.suffixes:
                attrib['suffix']=self.suffixes[column]
            if self.role(column)=='field':
                attrib['field']=self.fieldname(column)
            ET.SubElement(root,'column',attrib=attrib)
        return root
    def write(self, filename):
        """The sidecar, beside the .lift: written and read only by A-Z+T. It
        remembers the column inventory, order and audio folder that LIFT has no
        way to carry, which is what makes an export able to put back the
        columns A-Z+T never understood."""
        root=self.node()
        root.tag='dekerekeSource'
        if self.audiodir:
            root.set('audiodir',self.audiodir)
        root.set('encoding','utf-16' if self.utf16 else 'utf-8')
        tree=ET.ElementTree(root)
        ET.indent(tree)
        tree.write(str(filename),encoding='UTF-8',xml_declaration=True)
        log.info(_("Wrote Dekereke sidecar {file}").format(
                                        file=pathlib.Path(filename).name))
    @classmethod
    def read(cls, filename):
        root=ET.fromstring(pathlib.Path(filename).read_bytes())
        map=cls(analang=root.get('analang'),
                glosslangs=[n.get('lang') for n in root.findall('glosslang')])
        map.audiodir=root.get('audiodir')
        map.utf16=root.get('encoding')=='utf-16'
        for node in root.findall('column'):
            column=node.get('name')
            map.columns.append(column)
            map.roles[column]=node.get('role')
            if node.get('lang'):
                map.langs[column]=node.get('lang')
            if node.get('pitch'):
                map.twins[column]=node.get('pitch')
            if node.get('suffix'):
                map.suffixes[column]=node.get('suffix')
        return map

def rolelabels():
    """What to call each role in front of a user. A linguist should not have to
    know the word ‘role’, only what A-Z+T will do with the column."""
    return [
        ('phonetic',    _("the form to sort and analyze")),
        ('orthographic',_("how it is written")),
        ('phonemic',    _("phonemic form")),
        ('gloss',       _("meaning")),
        ('pos',         _("part of speech")),
        ('audio',       _("sound file")),
        ('reference',   _("record number")),
        ('note',        _("note")),
        ('tone',        _("tone")),
        ('cvprofileok', _("syllable profile (already checked)")),
        ('cvprofile',   _("syllable profile (a guess to check)")),
        ('frame',       _("a frame A-Z+T can sort")),
        ('pitchtwin',   _("the tone of a frame")),
        ('skipflag',    _("skip records marked here")),
        ('field',       _("keep it, but don’t analyze it")),
        ('ignore',      _("leave it out")),
        ]

def sidecarname(liftfilename):
    return pathlib.Path(liftfilename).with_suffix(SIDECARSUFFIX)

def getnow():
    """io_put/lift.py:4917 — matched exactly, so A-Z+T can't tell an imported
    entry from one of its own."""
    return datetime.datetime.now(datetime.UTC).isoformat()[:-7]+'Z'

def makeguid():
    """io_put/lift.py:328-331: lowercase hex, 8-4-4-4-12."""
    def hex(n):
        return ''.join(f'{randint(0, 15):x}' for i in range(n))
    return '-'.join([hex(8),hex(4),hex(4),hex(4),hex(12)])

def identify(dekereke, map):
    """Stamp each record with the guid, sense id and timestamp XSLT 1.0 cannot
    make, and mark the records that can't become entries. Returns the number
    that can."""
    stamp=getnow()
    phonetic=map.phonetic()
    skipflags=map.columnsforrole('skipflag')
    audiocols=map.columnsforrole('audio')
    guids=set()
    n=0
    for record in dekereke.records():
        node=record.find(phonetic)
        if node is None or not (node.text or '').strip():
            """A LIFT entry with no form to analyze would be invisible in every
            sort; A-Z+T would show an empty button."""
            record.set('skip','empty-phonetic')
            continue
        if any((f:=record.find(c)) is not None and (f.text or '').strip()
                                                        for c in skipflags):
            record.set('skip','flagged')
            continue
        if audiocols:
            sound=record.find(audiocols[0])
            name=(sound.text or '').strip() if sound is not None else ''
            if name:
                stem,dot,ext=name.rpartition('.')
                record.set('soundstem',stem or name)
                record.set('soundext',dot+ext if stem else '')
        for attrib in ('guid','senseid'):
            guid=makeguid()
            while guid in guids:
                guid=makeguid()
            guids.add(guid)
            record.set(attrib,guid)
        record.set('date',stamp)
        n+=1
    skipped=len(dekereke.records())-n
    if skipped:
        log.info(_("Skipping {n} Dekereke records with no form to analyze"
                    ).format(n=skipped))
    return n

def transform(etree, name):
    """Parse one stylesheet and drain its error log, as xlp.py does — but stop
    on a broken stylesheet instead of carrying on with a stale one."""
    filename=transformsdir().joinpath(name)
    if not file.exists(filename):
        raise Error(_("Can’t find the transform {file}.").format(file=filename))
    try:
        parsed=etree.parse(str(filename))
    except etree.XMLSyntaxError as e:
        for entry in e.error_log:
            log.error("{}: {} ({})".format(entry.domain_name,entry.type_name,
                                                            entry.filename))
        raise Error(_("The transform {file} is broken.").format(file=filename))
    transform=etree.XSLT(parsed)
    for error in transform.error_log:
        log.error("XSLT Error {}: {} ({})".format(error.message,error.line,
                                                            error.filename))
    return transform

def uri(path):
    """document() needs a real URI; document('') silently means the stylesheet
    itself, so an empty string yields an empty node-set and no error."""
    return pathlib.Path(path).resolve().as_uri()

def tolift(dekereke, map, liftfilename):
    """Dekereke -> LIFT. Writes the .lift file and its sidecar; returns how many
    entries were written."""
    etree=lxml()
    if error:=map.check():
        raise Error(error)
    entries=identify(dekereke,map)
    if not entries:
        raise Error(_("No Dekereke record has anything in the column you chose "
                    "to analyze, so there is nothing to import."))
    liftfilename=pathlib.Path(liftfilename)
    """What the source file told us has to reach the stylesheet, so set it
    before the map document is written, not after the transform has run."""
    map.utf16=dekereke.utf16
    map.audiodir=dekereke.audiodir
    map.suffixes=dict(dekereke.audiosuffixes)
    mapfile=liftfilename.with_suffix('.dekerekemap.tmp')
    ET.ElementTree(map.node()).write(str(mapfile),encoding='UTF-8')
    try:
        source=etree.fromstring(ET.tostring(dekereke.tree.getroot(),
                                                        encoding='UTF-8'))
        result=transform(etree,'dekereke2lift.xsl')(source,
                                    map=etree.XSLT.strparam(uri(mapfile)))
        result.write_output(str(liftfilename))
    finally:
        file.remove(mapfile)
    map.write(sidecarname(liftfilename))
    log.info(_("Wrote {entries} entries to {file}").format(entries=entries,
                                                file=liftfilename.name))
    return entries

def todekereke(liftfilename, outfilename, dekerekefilename=None, map=None):
    """LIFT -> Dekereke, by MERGING back into the original Dekereke file, so
    every column A-Z+T doesn't understand — other speakers, acoustic data,
    notes — is copied through untouched. Regenerating a Dekereke file from the
    LIFT alone would quietly discard all of it, so that is not what this does."""
    etree=lxml()
    map=map or ColumnMap.read(sidecarname(liftfilename))
    if error:=map.check():
        raise Error(error)
    if bad:=[c for c in map.columns if not NAME.match(c)]:
        """xsl:element aborts mid-write on a name XML won't take."""
        raise Error(_("These Dekereke column names can’t be written to XML: "
                    "{columns}").format(columns=', '.join(bad)))
    if not dekerekefilename:
        raise Error(_("Exporting to Dekereke needs the original Dekereke file "
                    "to merge into."))
    result=transform(etree,'lift2dekereke.xsl')(
                    etree.parse(str(dekerekefilename)),
                    lift=etree.XSLT.strparam(uri(liftfilename)),
                    map=etree.XSLT.strparam(uri(sidecarname(liftfilename))))
    outfilename=pathlib.Path(outfilename)
    text=etree.tostring(result,encoding='utf-16' if map.utf16 else 'UTF-8',
                        xml_declaration=True)
    outfilename.write_bytes(crlf(text,map.utf16))
    log.info(_("Wrote Dekereke file {file}").format(file=outfilename.name))
    return outfilename

def crlf(text, utf16=False):
    """Dekereke's own files use CRLF. Every XML parser normalizes line ends
    away and xsl:output has no lever to put them back, so we do it in bytes."""
    if utf16:
        return text.replace('\r\n'.encode('utf-16-le'),
                            '\n'.encode('utf-16-le')).replace(
                            '\n'.encode('utf-16-le'),
                            '\r\n'.encode('utf-16-le'))
    return text.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
