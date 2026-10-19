# coding=UTF-8
"""Centralized translation function.

Every module does `from utilities.i18n import _` instead of using LazyGlobal.
App.interfacelang() calls set_translator() to swap the live function.
"""
import gettext

_current = gettext.gettext  # fallback until App loads a real translation

def _(msg):
    return _current(msg)

def N_(msg):
    """MARK a string for translation without translating it yet.

    For text defined where `_()` can't run usefully — a class attribute, a
    menu list — and translated later where it is shown, with `_(value)`.
    xgettext only collects literals written inside a keyword call, so a plain
    `tasktitle = "Alphabet Report"` never reached azt.pot (2026-10-19);
    `tasktitle = N_("Alphabet Report")` does (`extract.py` passes
    `--keyword=N_`). Returns its argument unchanged."""
    return msg

def set_translator(func):
    global _current
    _current = func
