"""Transcribe Tone's one "Next" button (Kent, 2026-10-19): it replaced "Use
this name and go to: main screen / next group / next tone frame / next
syllable profile / comparison group". Next goes to the next group in this
frame, then the next frame, then the next syllable profile, skipping only
what was named since the task opened — not what was named in an earlier
session."""
import pytest

tasks = pytest.importorskip('tasks.tasks')
Transcribe = tasks.Transcribe

# ps Noun; profile -> frame -> groups
DATA = {'CVCV': {'Exists': ['1', 'High'], 'Isolation': ['2']},
        'CVC': {'Exists': ['3']}}


class Fake:
    _slice_key = Transcribe._slice_key
    _pick_unnamed_group = Transcribe._pick_unnamed_group
    nextunvisited = Transcribe.nextunvisited

    def __init__(self):
        st = {'profile': 'CVCV', 'check': 'Exists', 'group': '1'}
        self.st = st
        self.named_here = set()

        class Slices:
            ps = staticmethod(lambda: 'Noun')
            profile = staticmethod(lambda: st['profile'])

        class Params:
            check = staticmethod(lambda: st['check'])

        def cycle(key, options):
            i = options.index(st[key]) if st[key] in options else -1
            st[key] = options[(i + 1) % len(options)]

        class Status:
            groups_visible = staticmethod(
                lambda **k: DATA[st['profile']].get(st['check'], []))
            checks = staticmethod(lambda **k: sorted(DATA[st['profile']]))
            profiles = staticmethod(lambda **k: sorted(DATA))
            nextcheck = staticmethod(
                lambda **k: cycle('check', sorted(DATA[st['profile']])))
            nextprofile = staticmethod(
                lambda **k: cycle('profile', sorted(DATA)))

            @staticmethod
            def makecheckok():
                if st['check'] not in DATA[st['profile']]:
                    st['check'] = sorted(DATA[st['profile']])[0]

            @staticmethod
            def group(g=None):
                if g is not None:
                    st['group'] = g
                return st['group']

        class Program:
            slices = Slices
            params = Params
            status = Status
        self.program = Program

    def name_current(self):
        self.named_here.add(self._slice_key() + (self.st['group'],))

    def where(self):
        return (self.st['profile'], self.st['check'], self.st['group'])


def test_next_walks_groups_then_frames_then_profiles_then_stops():
    f = Fake()
    seen = [f.where()]
    while True:
        f.name_current()
        if not f.nextunvisited():
            break
        seen.append(f.where())
    assert seen == [('CVCV', 'Exists', '1'), ('CVCV', 'Exists', 'High'),
                    ('CVCV', 'Isolation', '2'), ('CVC', 'Exists', '3')]


def test_numbered_groups_come_first():
    f = Fake()
    f.st['group'] = 'High'
    f.name_current()
    assert f.nextunvisited() and f.where() == ('CVCV', 'Exists', '1')


def test_a_new_visit_starts_fresh():
    """Nothing named in an earlier session is skipped."""
    f = Fake()
    assert f.nextunvisited() and f.where()[:2] == ('CVCV', 'Exists')
