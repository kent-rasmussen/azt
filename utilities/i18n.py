# coding=UTF-8
"""Centralized translation function.

Every module does `from utilities.i18n import _` instead of using LazyGlobal.
App.interfacelang() calls set_translator() to swap the live function.
"""
import gettext

_current = gettext.gettext  # fallback until App loads a real translation

def _(msg):
    return _current(msg)

def set_translator(func):
    global _current
    _current = func
