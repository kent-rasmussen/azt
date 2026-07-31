# coding=UTF-8
"""One place that knows what the SIL fonts are CALLED and where they live.

Four subsystems need this and used to disagree: Tk (`frontend/ui_tkinter`),
the webview backend, PIL rendering (`Renderer`), and ReportLab
(`io_put/pdf_fonts`). Charis v6 ships the family "Charis SIL" with files
`CharisSIL-*.ttf`; v7 renames BOTH to "Charis"/`Charis-*.ttf`. A machine can
carry either, and Kent has both around — so every lookup must try the whole
alias list rather than one hard-coded string.

Backend-safe: os/glob/platform only, no Tk, no ReportLab, no frontend.
"""
import os
import glob as _glob
import platform

from utilities import logsetup

log = logsetup.getlog(__name__)

# Family names as the FONT SYSTEM reports them (Tk `.actual('family')`,
# fontconfig, Windows). Priority order: newest naming first.
CHARIS_FAMILIES = ['Charis SIL', 'Charis']
ANDIKA_FAMILIES = ['Andika', 'Andika SIL', 'Andika New Basic']
GENTIUM_FAMILIES = ['Gentium Plus', 'Gentium', 'Gentium SIL']
GENTIUM_BOOK_FAMILIES = ['Gentium Book Plus', 'Gentium Book Basic',
                         'Gentium Book Basic SIL']

# File-name stems, priority order: the tstv (hidden-staves) builds first,
# then v6 naming, then v7 naming.
_STEMS = {
    'charis': ['CharisSIL-tstv', 'CharisSIL', 'Charis'],
    'andika': ['Andika-tstv', 'Andika', 'AndikaNewBasic'],
    'gentium': ['GentiumPlus-tstv', 'GentiumPlus', 'Gentium'],
    'gentiumbook': ['GentiumBookPlus-tstv', 'GentiumBookPlus', 'GenBkBas'],
    'dejavu': ['DejaVuSans'],
}

_ALIASES = {
    'charis': CHARIS_FAMILIES,
    'andika': ANDIKA_FAMILIES,
    'gentium': GENTIUM_FAMILIES,
    'gentiumbook': GENTIUM_BOOK_FAMILIES,
    'dejavu': ['DejaVu Sans'],
}

FACES = ['Regular', 'Bold', 'Italic', 'BoldItalic']
_SHORT = {'Regular': 'R', 'Bold': 'B', 'Italic': 'I', 'BoldItalic': 'BI'}

# The one name every subsystem should ASK for when it needs a default.
# Resolution to what's actually installed happens through the alias list.
DEFAULT_KEY = 'charis'


def key_for_family(name):
    """Which font key is this family name (however it's spelled)? None if
    we have no file knowledge for it."""
    if not name:
        return None
    want = str(name).strip().casefold()
    for key, names in _ALIASES.items():
        if want in [n.casefold() for n in names]:
            return key
    return None


# Families whose FILE suffixes don't follow the SIL convention. DejaVu
# has no '-Regular' (it's bare) and says 'Oblique' where SIL says
# 'Italic'; keeping its old spelling here is what stops this refactor
# from breaking a font that currently works.
_SUFFIXES = {
    'dejavu': {'Regular': [''], 'Bold': ['-Bold'], 'Italic': ['-Oblique'],
               'BoldItalic': ['-BoldOblique']},
}


def face_files(key, face):
    """Candidate .ttf file names for one face, priority order. Both the
    spelled-out face ('Bold') and the short one ('B') — SIL ships both
    conventions across versions."""
    stems = _STEMS.get(key, [])
    special = _SUFFIXES.get(key)
    if special is not None:
        return ['{}{}.ttf'.format(stem, suffix)
                for stem in stems for suffix in special.get(face, [''])]
    short = _SHORT.get(face, face)
    out = []
    for stem in stems:
        out.append('{}-{}.ttf'.format(stem, face))
        if short != face:
            out.append('{}-{}.ttf'.format(stem, short))
    return out


_fontfilecache = {}


def findfontfile(filename):
    """Locate an installed font file by name, searching where fonts
    actually land — including the per-user Windows fonts directory
    (%LOCALAPPDATA%/Microsoft/Windows/Fonts), which a font-dialog
    'Install' uses and which PIL's own search never checks. Returns an
    absolute path or None; results (including misses) are cached per
    filename, so a font installed mid-session needs a restart.

    Moved here from frontend/ui_tkinter (which still imports the name, so
    its callers are unchanged) because ReportLab needs the same search:
    its TTFSearchPath globs only one directory deep, and Charis installs
    two levels down on Linux (/usr/share/fonts/truetype/charis/)."""
    if filename in _fontfilecache:
        return _fontfilecache[filename]
    if platform.system() == 'Windows':
        dirs = [os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts'),
                os.path.join(os.environ.get('LOCALAPPDATA')
                             or os.path.join(os.path.expanduser('~'),
                                             'AppData', 'Local'),
                             'Microsoft', 'Windows', 'Fonts')]
    else:  # Linux and mac directories; absent ones are just skipped
        dirs = ['/usr/share/fonts', '/usr/local/share/fonts',
                os.path.expanduser('~/.fonts'),
                os.path.expanduser('~/.local/share/fonts'),
                '/System/Library/Fonts', '/Library/Fonts',
                os.path.expanduser('~/Library/Fonts')]
    found = None
    for d in dirs:
        if not os.path.isdir(d):
            continue
        hits = _glob.glob(os.path.join(_glob.escape(d), '**', filename),
                          recursive=True)
        if hits:
            found = hits[0]
            break
    _fontfilecache[filename] = found
    return found


def font_dirs():
    """The directories findfontfile searches, for handing to search paths
    that want directories rather than a finder (ReportLab's
    TTFSearchPath). Only ones that exist."""
    if platform.system() == 'Windows':
        dirs = [os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts'),
                os.path.join(os.environ.get('LOCALAPPDATA')
                             or os.path.join(os.path.expanduser('~'),
                                             'AppData', 'Local'),
                             'Microsoft', 'Windows', 'Fonts')]
    else:
        dirs = ['/usr/share/fonts', '/usr/local/share/fonts',
                os.path.expanduser('~/.fonts'),
                os.path.expanduser('~/.local/share/fonts'),
                '/System/Library/Fonts', '/Library/Fonts',
                os.path.expanduser('~/Library/Fonts')]
    return [d for d in dirs if os.path.isdir(d)]


def find_faces(key):
    """{face: absolute path} for every face of *key* we can find on disk.
    Missing faces are simply absent from the dict — callers decide whether
    a partial family is usable."""
    out = {}
    for face in FACES:
        for name in face_files(key, face):
            path = findfontfile(name)
            if path:
                out[face] = path
                break
    return out


def resolve_family(key, probe):
    """The family name to ASK a font system for, given a *probe* that
    answers "does this system have this family?" (True/False). Returns the
    first alias the system claims, else None — the caller then knows the
    family is genuinely absent rather than merely spelled differently.
    This is the v6/v7 fix: 'Charis SIL' and 'Charis' are the same font."""
    for name in _ALIASES.get(key, []):
        try:
            if probe(name):
                return name
        except Exception as e:
            log.info("font probe failed for {!r}: {}".format(name, e))
    return None
