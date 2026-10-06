# coding=UTF-8
"""No translation may say `<unk>`.

Kent, 2026-09-22, on the tone rename page: "i don't know if <unk>* is new or
not, but it's bad". Not new: `<unk>` is what a machine translator emits for a
token outside its vocabulary, and the French and Arabic catalogues carried
sixteen of them — every tone letter in the two example melodies, the glottal
stop, the curly and modifier-letter quotes, `≠`, `←` and the `|` separators
of a menu path. Each is restored to the character the msgid has. This keeps
the next machine-translated batch from bringing them back.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CATALOGUES = sorted((ROOT / 'translations').glob('*/LC_MESSAGES/*.po'))


@pytest.mark.parametrize('po', CATALOGUES, ids=lambda p: p.parent.parent.name)
def test_catalogue_has_no_unknown_token(po):
    bad = [(n, line.strip()) for n, line in
           enumerate(po.read_text(encoding='utf-8').splitlines(), 1)
           if '<unk>' in line]
    assert not bad, "{}: {} line(s) with <unk>, e.g. {}:{}".format(
        po.parent.parent.name, len(bad), bad[0][0], bad[0][1][:80])


def test_there_are_catalogues_to_check():
    assert CATALOGUES, "no .po files found under translations/"
