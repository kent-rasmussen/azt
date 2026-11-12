"""A template's entries are new to the project made from it (io_put/cawl.py): Kent 2026-11-11, a freshly
made LIFT had dateCreated="2008-08-09T05:17:11Z" dateModified="2011-02-02T02:24:50Z", from SILCAWL."""
import pytest

try:
    from io_put import lift
except ImportError as e:  # optional dep missing in this env
    pytest.skip(f"optional dependency not installed: {e.name}", allow_module_level=True)

TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<lift version="0.13">
  <entry id="x_1" dateCreated="2008-08-09T05:17:11Z" dateModified="2011-02-02T02:24:50Z" guid="1">
    <sense id="s1" dateCreated="2008-08-09T05:17:11Z"><gloss lang="en"><text>water</text></gloss></sense>
  </entry>
</lift>
"""


def test_template_dates_become_now(tmp_path):
    path = tmp_path / 'template.lift'
    path.write_text(TEMPLATE, encoding='utf-8')
    db = lift.LiftXML(str(path), tostrip=True)
    before = lift.getnow()
    assert db.stamp_dates_now() == 2
    entry = next(n for n in db.nodes.iter() if n.tag == 'entry')
    sense = next(n for n in db.nodes.iter() if n.tag == 'sense')
    assert entry.get('dateCreated') >= before and entry.get('dateModified') >= before
    assert sense.get('dateCreated') >= before
    assert 'dateModified' not in sense.attrib      # only dates that were there


GUIDED = """<?xml version="1.0" encoding="utf-8"?>
<lift version="0.13">
  <entry id="???_784e1105-404b-4ca3-93b5-d1ae75764fcf" guid="784e1105-404b-4ca3-93b5-d1ae75764fcf">
    <sense id="skin (of man)_d56b5a5d-7cbf-49b9-a2dd-24eebb0ae462"><gloss lang="en"><text>skin</text></gloss></sense>
    <sense id="plain"><gloss lang="en"><text>hide</text></gloss></sense>
  </entry>
</lift>
"""


def test_template_guids_are_new_each_load(tmp_path):
    """Every project made from CAWL shared the template's guids (Kent 2026-11-11)."""
    path = tmp_path / 'template.lift'
    path.write_text(GUIDED, encoding='utf-8')
    ids = []
    for _load in range(2):
        db = lift.LiftXML(str(path), tostrip=True)
        assert db.regenerate_ids() == 3
        entry = next(n for n in db.nodes.iter() if n.tag == 'entry')
        senses = [n for n in db.nodes.iter() if n.tag == 'sense']
        assert entry.get('guid') != '784e1105-404b-4ca3-93b5-d1ae75764fcf'
        assert entry.get('id') == '???_' + entry.get('guid')
        assert senses[0].get('id').startswith('skin (of man)_')
        assert 'd56b5a5d' not in senses[0].get('id')
        assert senses[1].get('id') != 'plain'
        ids.append(entry.get('guid'))
    assert ids[0] != ids[1]
