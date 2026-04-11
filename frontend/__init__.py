# coding=UTF-8
"""Frontend package — selects ui backend based on settings or environment.

Usage by consumer modules:
    from frontend import ui

This gives either ui_tkinter or ui_webview depending on configuration.
To force a backend, set the environment variable AZT_UI_BACKEND to
'tkinter' or 'webview' before importing.
"""
import os

def _get_backend():
    """Determine which UI backend to use."""
    # Environment variable takes priority
    env = os.environ.get('AZT_UI_BACKEND', '').lower()
    if env == 'webview':
        return 'webview'
    if env == 'tkinter':
        return 'tkinter'
    # Default to tkinter (stable)
    return 'tkinter'

_backend = _get_backend()

if _backend == 'webview':
    from frontend import ui_webview as ui
else:
    from frontend import ui_tkinter as ui
