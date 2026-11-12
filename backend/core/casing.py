# coding=UTF-8
"""Capital letters of an orthography's glyphs (agenda: alphabet_chart_capitals.md, DECIDED 2026-09-03).

The capital of a glyph is a property of the orthography, stored in the alphabet settings:
  - `alphabet_casing`: the project's rule, 'full' (NY), 'title' (Ny) or 'none' (the default: charts show no
    capitals, as before);
  - `glyph_capitals`: sparse per-glyph overrides, {glyph: capital}; an explicit None means "no capital".

Two uses, deliberately different (Kent 2026-11-07):
  - MATCHING a word against the alphabet (profiles, glyph regexes) accepts a glyph's title AND full capital,
    whatever the rule, unless an override names the one capital (or None) — so "This" profiles as Th+i+s
    rather than 'Invalid';
  - SHOWING a capital (the chart, later) follows the rule, with the overrides on top.
Neither is str.upper() alone being right for every orthography; the overrides are how a project says so."""

RULES = ('full', 'title', 'none')
DEFAULT_RULE = 'none'


def _title(glyph):
    return glyph[:1].upper() + glyph[1:]


def _derived(glyph, rule):
    if rule == 'full':
        return glyph.upper()
    if rule == 'title':
        return _title(glyph)
    return None


def capital(glyph, rule=DEFAULT_RULE, overrides=None):
    """The capital to SHOW for `glyph`: an override if there is one, else the rule's; None if none (also when
    the rule's capital is the glyph itself, i.e. it has no case pair)."""
    overrides = overrides or {}
    if glyph in overrides:
        return overrides[glyph] or None
    c = _derived(glyph, rule)
    return c if c and c != glyph else None


def matching_capitals(glyph, overrides=None):
    """Every capital form that should MATCH as `glyph` in a word: an override's one capital (none for an
    explicit None), else the title and full capitals that differ from the glyph."""
    overrides = overrides or {}
    if glyph in overrides:
        c = overrides[glyph]
        return {c} if c and c != glyph else set()
    return {c for c in (_title(glyph), glyph.upper()) if c and c != glyph}


def fold(glyphs, overrides=None):
    """`glyphs` without those that are only a capital of another glyph in the list (e.g. 'F' beside 'f'), in
    order: the capital matches as its glyph, so it is not a letter of its own."""
    glyphs = list(glyphs)
    capitals = set()
    for g in glyphs:
        capitals |= matching_capitals(g, overrides)
    return [g for g in glyphs if g not in capitals]
