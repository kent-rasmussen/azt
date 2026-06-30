"""Display-server detection. Env-var only — no GUI/tkinter dependency, so both
frontend and backend can import it.

Under GNOME/Wayland the Tk app runs through XWayland, where synchronous X
round-trips (update/update_idletasks) made while a window is transitioning
(mapping a dialog/popup, deiconify, -fullscreen toggle) can deadlock with mutter
and freeze the app. The central UI.update/update_idletasks override checks
USING_WAYLAND to skip those synchronous calls there (invisible on X11/Windows,
where users run). See docs/wayland_freeze_audit.md.
"""
import os


def using_wayland():
    return (os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'
            or bool(os.environ.get('WAYLAND_DISPLAY')))


USING_WAYLAND = using_wayland()
