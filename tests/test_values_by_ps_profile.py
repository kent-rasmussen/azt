"""annotation_values_by_ps_profile / tone_values_by_ps_profile: one pass per
slice now (2026-11-12); they were quadratic in the slice, ~19s of the status
refresh after a profile rename. These compare against the old comprehensions,
copied verbatim below, on fake senses built to hit each edge: a check named
with no values, a value under a check no sense names, empty values, an empty
profile key, and (tone) the `frames` filter."""
import random

import pytest

lift = pytest.importorskip('io_put.lift')
LiftXML = lift.LiftXML


class FakeSense:
    def __init__(self, ann, keys=None, tone=None):
        self.ann = ann
        self.keys = list(ann) if keys is None else keys
        self.tone = tone or {}

    def annotationvaluedictbyftypelang(self, ftype, lang):
        return self.ann

    def annotationkeysbyftypelang(self, ftype, lang):
        return self.keys

    def tonevaluedict(self):
        return self.tone


def old_annotations(self, ftype='lc'):
    return {ps:{profile:{check:{v
                        for sense in self.sensesbyps_profile[ps][profile]
                        for c,v in sense.annotationvaluedictbyftypelang(
                                        ftype,self.analang).items()
                        if v
                        if c==check
                                }
                        for sense in self.sensesbyps_profile[ps][profile]
                        for check in sense.annotationkeysbyftypelang(
                                                ftype,self.analang)
                        }
                for profile in self.ps_profiles[ps]
                if profile
                }
            for ps in self.ps_profiles
            }


def old_tones(self, frames=None):
    def wanted(ps,check):
        return frames is None or check in frames.get(ps,())
    return {ps:{profile:{check:{v
                        for sense in self.sensesbyps_profile[ps][profile]
                        for c,v in sense.tonevaluedict().items()
                        if v
                        if c==check
                                }
                        for sense in self.sensesbyps_profile[ps][profile]
                        for check in sense.tonevaluedict().keys()
                        if wanted(ps,check)
                        }
                for profile in self.ps_profiles[ps]
                if profile
                }
            for ps in self.ps_profiles
            }


def fake_db(seed):
    rnd = random.Random(seed)
    checks = ['V1', 'C1', 'V1=V2', 'C2', 'σ']
    frames = ['Isolation', 'Possessive', 'Plural']
    db = LiftXML.__new__(LiftXML)
    db.analang = 'xx'
    db.ps_profiles = {'Noun': ['CVC', 'CVCV', ''], 'Verb': ['CVC']}
    db.sensesbyps_profile = {}
    for ps, profiles in db.ps_profiles.items():
        db.sensesbyps_profile[ps] = {}
        for profile in profiles:
            senses = []
            for _ in range(rnd.randint(0, 12)):
                ann = {c: rnd.choice(['', 'a', 'e', 'i', 'NA'])
                       for c in rnd.sample(checks, rnd.randint(0, 4))}
                keys = list(ann)
                if rnd.random() < .2:   # names a check it has no value for
                    keys.append('C9')
                if rnd.random() < .2 and keys:  # a value under an unnamed check
                    keys.pop(0)
                tone = {f: rnd.choice(['', '1', '2', '3'])
                        for f in rnd.sample(frames, rnd.randint(0, 3))}
                senses.append(FakeSense(ann, keys, tone))
            db.sensesbyps_profile[ps][profile] = senses
    return db


@pytest.mark.parametrize('seed', range(25))
def test_annotations_match_the_old_form(seed):
    db = fake_db(seed)
    assert db.annotation_values_by_ps_profile('lc') == old_annotations(db)


@pytest.mark.parametrize('seed', range(25))
@pytest.mark.parametrize('frames', [None, {'Noun': ['Isolation']},
                                    {'Verb': ['Plural', 'Possessive']}, {}])
def test_tones_match_the_old_form(seed, frames):
    db = fake_db(seed)
    assert db.tone_values_by_ps_profile(frames=frames) == \
        old_tones(db, frames=frames)


def test_one_pass_is_linear():
    """Each sense is asked for its values once per slice, not once per
    (sense, check) pair."""
    calls = []

    class Counting(FakeSense):
        def annotationvaluedictbyftypelang(self, ftype, lang):
            calls.append(1)
            return self.ann

    db = LiftXML.__new__(LiftXML)
    db.analang = 'xx'
    db.ps_profiles = {'Noun': ['CVC']}
    db.sensesbyps_profile = {'Noun': {'CVC': [
        Counting({'V1': 'a', 'C1': 'b', 'C2': 'd'}) for _ in range(50)]}}
    db.annotation_values_by_ps_profile('lc')
    assert len(calls) == 50
