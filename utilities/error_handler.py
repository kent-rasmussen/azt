# coding=UTF-8
"""Backend-safe error notification.

Backend modules call `notify_error(text, **kwargs)` instead of importing
ErrorNotice from the frontend. At startup, `set_error_handler()` is called
to wire this to the real UI ErrorNotice dialog.

Before the UI is initialized, errors are logged to stderr.
"""
import logging
log = logging.getLogger(__name__)

def _default_handler(text, **kwargs):
    """Fallback before UI is initialized."""
    log.error(f"ErrorNotice (no UI): {text}")

_handler = _default_handler

def notify_error(text, **kwargs):
    """Show an error to the user. Backend-safe — no tkinter dependency.
    Returns whatever the handler returns (the notice window instance for
    the ErrorNotice handler), so callers that need to track a single
    open dialog can — see App.collab_offer_reload (F6)."""
    return _handler(text, **kwargs)

def set_error_handler(handler):
    """Set the error display function. Called once at startup with ErrorNotice."""
    global _handler
    _handler = handler
