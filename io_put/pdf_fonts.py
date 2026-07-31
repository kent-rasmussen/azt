#!/usr/bin/env python3
# coding=UTF-8
"""Shared PDF font registration for ReportLab-based PDF generation."""
import os
import platform
from utilities import logsetup
from utilities import fonts as fontlib
from utilities.i18n import _

log = logsetup.getlog(__name__)

try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    from reportlab.rl_config import TTFSearchPath
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    log.warning("ReportLab not installed. PDF generation will not work.")

if REPORTLAB_AVAILABLE:
    if platform.system() == 'Windows':
        # NO os.getlogin() here: it raises OSError under pythonw (no
        # console) — and this runs AT IMPORT, on the boot path, so it
        # killed double-click launches while cmd launches worked
        # (found 2026-07-16). Env vars are the safe identity source.
        _user_fonts = os.path.join(
            os.environ.get('LOCALAPPDATA')
            or os.path.join(os.path.expanduser('~'), 'AppData', 'Local'),
            'Microsoft', 'Windows', 'Fonts')
        for path in [os.path.join(os.environ.get('WINDIR', r'C:\Windows'),
                                  'Fonts'),
                     _user_fonts]:
            TTFSearchPath.append(path)
    # The posix font dirs were never added (only Windows had a branch), so
    # ReportLab searched its own bundled paths on Linux/mac. ADDITIVE — the
    # Windows entries above and ReportLab's own defaults are untouched;
    # this only widens the net (Kent 2026-07-31: "if currently using
    # TTFSearchPath, don't do less than that").
    for _d in fontlib.font_dirs():
        if _d not in TTFSearchPath:
            TTFSearchPath.append(_d)
    # enable font subdirectories:
    for i in list(TTFSearchPath):
        TTFSearchPath.append(i+'/*')


# What actually registered, and what didn't — read by the PDF generators
# so they can fall back and SAY they fell back, instead of silently
# producing Helvetica (Kent 2026-07-31).
_registered = {}      # key -> family name registered with ReportLab
_missing = []         # [(key, detail)]
_done = False


def registered_families():
    """{'charis': 'Charis', ...} — families usable in a PDF right now."""
    return dict(_registered)


def missing_families():
    """[(key, detail)] for families that could not be registered."""
    return list(_missing)


def _register_one(key, family):
    """Register all four faces of ONE family, all-or-nothing.

    All-or-nothing matters: the old code registered face by face and let an
    exception abort mid-family, leaving 'Charis-Regular' present and
    'Charis-Bold' absent with registerFontFamily never called — so a later
    setFont('Charis-Bold') died at DRAW time, long after the log line.
    Nothing is committed to pdfmetrics until all four faces resolve."""
    try:
        pdfmetrics.getFont('{}-Regular'.format(family))
        return True             # already registered this session
    except KeyError:
        pass
    faces = {}
    for face in fontlib.FACES:
        got = None
        for name in fontlib.face_files(key, face):
            # Bare name FIRST so ReportLab's own TTFSearchPath still does
            # the work it was doing on Windows; the absolute path from our
            # recursive finder is the fallback for what it can't reach
            # (Charis lives two levels deep on Linux, TTFSearchPath globs
            # one). Never less than before.
            for candidate in [name, fontlib.findfontfile(name)]:
                if not candidate:
                    continue
                try:
                    got = TTFont('{}-{}'.format(family, face), candidate)
                    break
                except Exception:
                    continue
            if got is not None:
                break
        if got is None:
            _missing.append((key, _("no file found for the {face} face"
                                    ).format(face=face)))
            log.warning("PDF fonts: no file for %s %s (tried %s)",
                        family, face, fontlib.face_files(key, face))
            return False
        faces[face] = got
    try:
        for face, ttf in faces.items():
            pdfmetrics.registerFont(ttf)
        registerFontFamily(family,
                           normal='{}-Regular'.format(family),
                           bold='{}-Bold'.format(family),
                           italic='{}-Italic'.format(family),
                           boldItalic='{}-BoldItalic'.format(family))
    except Exception as e:
        _missing.append((key, str(e)))
        log.warning("PDF fonts: could not register %s: %s", family, e)
        return False
    return True


def register_fonts():
    """Register the SIL families we can find. Returns True if ANY of them
    registered — Charis alone is enough (Kent 2026-07-31).

    This used to be all-or-nothing across BOTH families: the Andika calls
    sat outside the per-family try, so a machine with Charis but no Andika
    returned False and both PDF generators fell back to Helvetica while
    logging "is Charis installed?". Since neither installer ships Andika
    (RunMeAsAdmin…bat, RunMetoInstall_Linux.sh), that was the DEFAULT
    supported install."""
    global _done
    if not REPORTLAB_AVAILABLE:
        return False
    if _done:
        return bool(_registered)
    _done = True
    for key, family in (('charis', 'Charis'), ('andika', 'Andika')):
        if _register_one(key, family):
            _registered[key] = family
            log.info("PDF fonts: %s registered", family)
    if not _registered:
        log.error("PDF fonts: neither Charis nor Andika could be "
                  "registered; PDFs will use Helvetica.")
    return bool(_registered)


def pdf_font(requested):
    """(family, downgraded_from) for a PDF: the requested family if it
    registered, else Charis, else Helvetica. ``downgraded_from`` is the
    name the caller asked for when we could NOT give it, else None — the
    generators use it to tell the user rather than silently substituting.

    Charis-before-Helvetica is the point: asking for Andika on a
    Charis-only machine should give a real Unicode font, not a fallback
    that can't render the orthography."""
    if str(requested or '').strip().casefold().startswith('helvetica'):
        return 'Helvetica', None    # asked for it on purpose
    register_fonts()
    key = fontlib.key_for_family(requested) or ''
    if key in _registered:
        return _registered[key], None
    if 'charis' in _registered:
        return _registered['charis'], requested
    return 'Helvetica', requested


def warn_if_downgraded(downgraded_from, replacement):
    """Say it out loud, once per PDF, when we couldn't use the font the
    user picked. notify_user (not notify_error): the PDF still gets made,
    so this must not block the export."""
    if not downgraded_from:
        return
    from utilities.error_handler import notify_user
    if replacement == 'Helvetica':
        msg = _("This PDF uses Helvetica: neither Charis nor Andika could "
                "be found on this computer. Accented and special letters "
                "may not print correctly. Install Charis (free from "
                "software.sil.org) and make the PDF again.")
    else:
        msg = _("This PDF uses {replacement} because {wanted} could not be "
                "found on this computer.").format(replacement=replacement,
                                                  wanted=downgraded_from)
    log.warning(msg)
    try:
        notify_user(msg)
    except Exception as e:
        log.info("couldn’t show the font notice: {}".format(e))
