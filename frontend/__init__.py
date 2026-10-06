# coding=UTF-8
"""Frontend package — resolves `ui` to the selected backend.

Usage by consumer modules:
    from frontend import ui

Which backend that is comes from `utilities.ui_backend.chosen()`, which is
the ONE place the question is decided — set AZT_UI_BACKEND=webview, or pass
--webview / --tkinter on the command line.

The selector deliberately lives outside this package: main.py needs the
answer before it may import `frontend` (importing anything from here runs
this file, which imports a backend), and two independent readers of the
environment disagreed as soon as one of them gained the power to refuse.
See utilities/ui_backend.py.
"""
from utilities import ui_backend as _select

backend_requested = _select.requested()
backend = _select.chosen()

if backend == 'webview':
    from frontend import ui_webview as ui
else:
    from frontend import ui_tkinter as ui
