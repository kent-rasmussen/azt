"""UI variables are built with value= by keyword, never a positional master.

tkinter's StringVar/IntVar/BooleanVar are (master, value); the webview
backend's (frontend/ui_variables.py) are (value, name). So
`ui.StringVar(self, x)` works under tkinter and, under webview, makes the
WIDGET the value. In the tone frame drafter that value then failed to
serialize ("Object of type ToneFrameDrafter is not JSON serializable") and
the page stopped after its first row (Kent, 2026-10-12: "TFDP is just
showing name, nothing beyond that one field").
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
POSITIONAL_MASTER = re.compile(r'\b(?:StringVar|IntVar|BooleanVar)\(\s*self\s*[,)]')


def test_no_variable_is_given_a_positional_master():
    found = []
    for path in ROOT.rglob('*.py'):
        if 'tests' in path.parts or 'env' in path.parts:
            continue
        for n, line in enumerate(path.read_text(encoding='utf-8',
                                                errors='replace').splitlines(), 1):
            code = line.split('#', 1)[0]
            if POSITIONAL_MASTER.search(code):
                found.append(f'{path.relative_to(ROOT)}:{n}: {line.strip()}')
    assert not found, 'pass value= by keyword:\n' + '\n'.join(found)
