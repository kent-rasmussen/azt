"""Reports by UF (tone) group — report audit, 2026-10-14.

* `Report.__init__` set `self.byUFgroup=False`, shadowing ByUF's class
  attribute, so every "by Tone group" report came out as the plain one.
* The group list read the CURRENT slice's analysis, without asking whether
  it was current.
* `StatusDict.isanalysisOK` read the current tier's checks for the current
  ps, not the tone frames of the slice asked about.
"""
from types import SimpleNamespace

import pytest

generator = pytest.importorskip('backend.reporting.generator')
report_mixins = pytest.importorskip('backend.core.report_mixins')
analysis = pytest.importorskip('backend.core.analysis')


# ── the flag ───────────────────────────────────────────────────────────────

class UF:
    byUFgroup = True        # what ByUF declares


class ByUFReport(UF, generator.Report):
    pass


def _program():
    return SimpleNamespace(
        settings=SimpleNamespace(reportbasefilename='x',
                                 reporttoaudiorelURL='',
                                 minimumwordstoreportUFgroup=3),
        profiles=SimpleNamespace(distinguish=None, profilesbysense=None),
        params=SimpleNamespace(check=lambda: 'V1'))


def test_byuf_declares_the_flag():
    assert report_mixins.ByUF.byUFgroup is True


def test_report_init_leaves_a_by_uf_report_by_uf():
    r = ByUFReport.__new__(ByUFReport)
    r.program = _program()
    generator.Report.__init__(r)
    assert r.byUFgroup is True


def test_a_plain_report_is_not_by_uf():
    r = generator.Report.__new__(generator.Report)
    r.program = _program()
    generator.Report.__init__(r)
    assert r.byUFgroup is False


def test_report_mixin_flags_use_names_taskbase_declares():
    """Multicheck said `multicheckscope`; TaskBase and the page read
    `multicheck_scope`, so the flag never took effect and every multi-check
    report died on 'no attribute cvtstodo' (Kent's run, 2026-10-14)."""
    base = pytest.importorskip('tasks.base')
    declared = {k for k, v in vars(base.TaskBase).items()
                if isinstance(v, bool)}
    for mixin in (report_mixins.Multicheck, report_mixins.Multislice):
        flags = {k for k, v in vars(mixin).items() if isinstance(v, bool)}
        assert flags <= declared, (mixin.__name__, flags - declared)
    assert report_mixins.Multicheck.multicheck_scope is True


# ── ufgroups_to_report ─────────────────────────────────────────────────────

class FakeAnalysis:
    def __init__(self, groups):
        self.groups = groups
        self.sensesbygroup = {}
        self.read = self.done = 0

    def donoUFanalysis(self):
        self.read += 1
        self.sensesbygroup = dict(self.groups)

    def do(self):
        self.done += 1
        self.sensesbygroup = dict(self.groups)


class FakeXLPR:
    cleaned = 0

    def cleanup(self):
        self.cleaned += 1


def fake_report(ok, groups):
    asked = []
    r = SimpleNamespace(minwords=3, asked=asked)
    r.analysis = FakeAnalysis(groups)
    r.makeanalysis = lambda **kw: asked.append(('makeanalysis', kw))

    def isanalysisOK(**kw):
        asked.append(('isanalysisOK', kw))
        return ok, False, ''
    r.program = SimpleNamespace(status=SimpleNamespace(
                                    isanalysisOK=isanalysisOK))
    return r


GROUPS = {'High': ['a', 'b', 'c'], 'Low': ['d', 'e', 'f', 'g'],
          'Noun_CVC_3': ['h']}


def test_groups_come_from_the_slice_asked_for(monkeypatch):
    r = fake_report(True, GROUPS)
    generator.Report.ufgroups_to_report(r, 'Verb', 'CVCV')
    assert ('makeanalysis', {'ps': 'Verb', 'profile': 'CVCV'}) in r.asked
    assert ('isanalysisOK', {'ps': 'Verb', 'profile': 'CVCV'}) in r.asked


def test_a_current_analysis_is_read_and_small_groups_left_out():
    r = fake_report(True, GROUPS)
    got = dict(generator.Report.ufgroups_to_report(r, 'Noun', 'CVC'))
    assert set(got) == {'High', 'Low'}
    assert r.analysis.read == 1 and r.analysis.done == 0


def test_a_stale_analysis_is_redone_in_the_foreground(monkeypatch):
    monkeypatch.setattr(generator.multiprocessing, 'parent_process',
                        lambda: None)
    r = fake_report(False, GROUPS)
    generator.Report.ufgroups_to_report(r, 'Noun', 'CVC')
    assert r.analysis.done == 1


def test_a_stale_analysis_in_the_background_exits_to_retry(monkeypatch):
    monkeypatch.setattr(generator.multiprocessing, 'parent_process',
                        lambda: object())
    r = fake_report(False, GROUPS)
    xlpr = FakeXLPR()
    with pytest.raises(SystemExit) as e:
        generator.Report.ufgroups_to_report(r, 'Noun', 'CVC', xlpr=xlpr)
    assert e.value.code not in (0, None), "background() retries on error"
    assert xlpr.cleaned == 1, "the lock must not block the retry"
    assert r.analysis.done == 0, "no LIFT write from the child"


# ── isanalysisOK: the slice asked about, tone frames ──────────────────────

def test_isanalysisok_reads_the_tone_frames_of_the_slice_asked(monkeypatch):
    prog = SimpleNamespace(
        params=SimpleNamespace(cvt=lambda *a: 'V', check=lambda *a: 'V1',
                               ftype=lambda *a: 'lc'),
        slices=SimpleNamespace(ps=lambda: 'Noun', profile=lambda: 'CVC',
                               pss=lambda: ['Noun', 'Verb']))
    st = analysis.StatusDict('status.json', {}, prog)
    asked, stamped = [], []
    monkeypatch.setattr(st, 'renewchecks', lambda *a, **k: None)
    monkeypatch.setattr(st, 'checks',
                        lambda **kw: asked.append(kw) or ['Isolation-Verb'])
    monkeypatch.setattr(st, 'last',
                        lambda task, **kw: stamped.append((task, kw)))
    st.isanalysisOK(ps='Verb', profile='CVCV')
    assert asked == [{'cvt': 'T', 'ps': 'Verb', 'profile': 'CVCV'}]
    assert stamped and all(kw['cvt'] == 'T' and kw['ps'] == 'Verb'
                           and kw['check'] == 'Isolation-Verb'
                           for _, kw in stamped)
