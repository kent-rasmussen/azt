"""Shared kit for the tone underlying-form (UF) tests.

Not a test module (no `test_` prefix). Builds REAL `io_put.lift` nodes —
`Field`, `Form`, `Example` — under a minimal sense, so the tone fields are
read and written by the app's own code (human form vs `…_MT` machine form,
the `tonelangname` form-lang), while nothing touches a file, a display or
the network.

Why not `lift.Sense` itself: `Sense.__init__` runs `getglosses`, which looks
for `images/toselect/` relative to the CWD and calls `ensure_available()`
(a download) when it is missing. `MiniSense` borrows exactly the `Sense`
methods the UF analysis reads — `uftonevalue`, `tonevaluebyframe`,
`tonevaluedict`, `getexamples` — as unbound functions, so what is tested is
the real code, not a copy.

The fake program carries only what `backend.core.analysis.Analysis` reads:
`db.analang`, `db.write()`, `slices.ps()/profile()/pss()/senses(ps,profile)`,
`status.checks(ps,profile)`, `status.last(...)`, `status.store()`,
`params.cvt()`.
"""
from types import MethodType, SimpleNamespace
from xml.etree import ElementTree as ET

from io_put import lift

ANALANG = 'xyz'


class FakeDB:
    """The LiftXML surface the tone nodes reach through `node.db`."""

    def __init__(self, analang=ANALANG):
        self.analang = analang
        self.writes = 0
        self.senses = []
        # the app's own form-lang rule, not a copy of it
        self.tonelangname = MethodType(lift.LiftXML.tonelangname, self)

    def write(self):
        self.writes += 1


class Root(ET.Element):
    """Stand-in for the <lift> root: an Element that carries `.db`."""


class MiniSense(lift.Node, lift.FieldParent):
    uftonevalue = lift.Sense.uftonevalue
    ufgroup = lift.Sense.ufgroup
    tonevaluebyframe = lift.Sense.tonevaluebyframe
    tonevaluedict = lift.Sense.tonevaluedict
    getexamples = lift.Sense.getexamples

    def __init__(self, parent, node):
        lift.Node.__init__(self, parent, node)
        self.id = self.get('id')
        self.entry = SimpleNamespace(guid='entry-' + self.id)
        self.annotationlang = 'en'
        lift.FieldParent.__init__(self)
        self.getexamples()

    def __repr__(self):
        return f'<MiniSense {self.id}>'


def _esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def sense_xml(db, sid, ps, tones, uf=None, uf_mt=None):
    """tones: {frame: surface group}; a value of '' writes the example with
    an EMPTY tone text (sorted-then-cleared); a frame absent from the dict
    has no example at all. uf / uf_mt pre-seed the sense-level tone field's
    human / machine form."""
    tl = db.tonelangname(db.analang)
    tl_mt = db.tonelangname(db.analang, machine=True)
    out = [f'<sense id="{_esc(sid)}">',
           f'<grammatical-info value="{_esc(ps)}"/>']
    if uf is not None or uf_mt is not None:
        out.append('<field type="tone">')
        if uf is not None:
            out.append(f'<form lang="{tl}"><text>{_esc(uf)}</text></form>')
        if uf_mt is not None:
            out.append(f'<form lang="{tl_mt}"><text>{_esc(uf_mt)}</text></form>')
        out.append('</field>')
    for frame, value in tones.items():
        out.append('<example>'
                   f'<form lang="{db.analang}"><text>w-{_esc(sid)}</text></form>'
                   '<field type="location"><form lang="en">'
                   f'<text>{_esc(frame)}</text></form></field>'
                   f'<field type="tone"><form lang="{tl}">'
                   f'<text>{_esc(value)}</text></form></field>'
                   '</example>')
    out.append('</sense>')
    return ''.join(out)


def build_senses(specs, db=None):
    """specs: iterable of dicts with keys id, ps, tones, and optional uf,
    uf_mt. Returns (db, [MiniSense, …]) in spec order."""
    db = db or FakeDB()
    root = Root('lift')
    root.db = db
    senses = []
    for spec in specs:
        el = ET.fromstring(sense_xml(db, spec['id'], spec.get('ps', 'Noun'),
                                     spec.get('tones', {}),
                                     uf=spec.get('uf'),
                                     uf_mt=spec.get('uf_mt')))
        root.append(el)
        senses.append(MiniSense(root, el))
    db.senses.extend(senses)
    return db, senses


def tone_forms(sense):
    """{form-lang: text} of the SENSE-level tone field (the UF field)."""
    f = sense.fields.get('tone')
    if f is None:
        return {}
    return {lang: f.forms[lang].textvalue() for lang in f.forms}


class FakeSlices:
    def __init__(self, by_slice, current=('Noun', 'CVC')):
        self.by_slice = by_slice            # {(ps, profile): [senses]}
        self.current = current

    def ps(self):
        return self.current[0]

    def profile(self):
        return self.current[1]

    def pss(self):
        return list(dict.fromkeys(ps for ps, _ in self.by_slice))

    def senses(self, ps=None, profile=None, **kwargs):
        return list(self.by_slice.get((ps, profile), []))


class FakeStatus:
    """Models StatusDict.checks' dispatch on the tier: tone frames for
    cvt 'T' (by ps), segmental checks otherwise. Records every call."""

    def __init__(self, program, frames_by_ps):
        self.program = program
        self.frames_by_ps = frames_by_ps
        self.check_calls = []
        self.last_calls = []
        self.stores = 0

    def checks(self, **kwargs):
        self.check_calls.append(dict(kwargs))
        cvt = kwargs.get('cvt', self.program.params.cvt())
        if cvt != 'T':
            return ['V1', 'C1']
        ps = kwargs.get('ps', self.program.slices.ps())
        return list(self.frames_by_ps.get(ps, []))

    def last(self, task, update=False, **kwargs):
        self.last_calls.append((task, update, dict(kwargs)))

    def store(self):
        self.stores += 1

    def isanalysisOK(self, **kwargs):
        return True, False, 'analysis OK (fake)'


def make_program(senses_by_slice, frames_by_ps, db, current=('Noun', 'CVC'),
                 cvt='T'):
    prog = SimpleNamespace(name='A-Z+T', db=db)
    prog.params = SimpleNamespace(cvt=lambda *a: cvt)
    prog.slices = FakeSlices(senses_by_slice, current)
    prog.status = FakeStatus(prog, frames_by_ps)
    return prog
