# coding=UTF-8
"""A-Z+T manual test: does a SECOND pywebview window survive?

RESULT 2026-09-05, in two parts.

FIRST PASS (windows made with html=, no js_api): survived three rounds on
BOTH engines, including the Qt build the app crashed on. That looked like a
clean acquittal of multi-window. IT WAS NOT — the probe was not building the
same kind of window as the app, so it tested the wrong thing. Recorded
because a probe that differs from the real path in an unexamined way is how
a bug gets "ruled out" while still being the bug.

WHAT THE APP'S OWN CRASH SHOWED (PYTHONFAULTHANDLER=1, --engine=qt), and it
is the whole reason the probe was rebuilt:

    qtpy/_utils.py:53 possibly_static_exec
    webview/platforms/qt.py:966 create_window
    webview/__init__.py:303 start
    ui_webview.py:2181 mainloop

The fault is INSIDE pywebview's Qt create_window, on the main thread. No
A-Z+T frame is involved beyond sitting in start(). So the variable worth
changing is what the window is made of — hence url= + js_api here, matching
ui_webview.Toplevel. Pass --html for the old shape.

CONFIRMED NOISE either way: "Release of profile requested but WebEnginePage
still not deleted" fired THREE times in a run that did not crash. It appears
twice just before the app's segfault and looks exactly like a cause.

GTK does not crash at all, on any shape tried so far.

Why this exists (2026-09-04): the first `main.py --webview` run reached the
chooser, created a second window, flushed its queued JS, and then died:

    Toplevel 2 JS ready - flushing 46 queued calls
    Release of profile requested but WebEnginePage still not deleted. Expect troubles !
    Release of profile requested but WebEnginePage still not deleted. Expect troubles !
    Segmentation fault (core dumped)

That warning is QtWebEngine's: a QWebEngineProfile was released while a page
using it was still alive. It appears immediately before the crash and names a
window-lifetime problem — but whether the fault is pywebview's Qt backend or
A-Z+T's own window handling cannot be told from that log, because azt was
doing a hundred other things at the time.

THIS SCRIPT REMOVES AZT FROM THE PICTURE. It creates a second window and
destroys it, with no azt code involved at all.

    Segfaults here      -> pywebview/QtWebEngine. A-Z+T's Toplevel model is
                           not at fault, and the answer is the GTK backend,
                           a different window strategy, or one window with
                           in-page "windows".
    Survives here       -> the fault is in how ui_webview creates or destroys
                           Toplevels, and this script is the baseline to
                           bisect against.

    ~/bin/AZT/env/bin/python two_windows.py            # default backend
    PYWEBVIEW_GUI=qt  ~/bin/AZT/env/bin/python two_windows.py
    PYWEBVIEW_GUI=gtk python two_windows.py            # needs a venv that sees gi

Deliberately imports nothing from azt.
"""
import os
import sys
import time

PAGE = ('<html><body style="font:16px system-ui;padding:20px">'
        '<h2>{}</h2><p id="p">waiting...</p></body></html>')

# How many extra windows to open and close. The app opens one Toplevel at
# startup; more than one is worth trying because a crash on the SECOND
# teardown is a different bug from a crash on the first.
ROUNDS = 3


def main():
    try:
        import webview
    except ImportError:
        sys.stderr.write("pywebview is not installed in this interpreter.\n")
        return 2

    # MATCH THE APP'S WINDOW SHAPE, because the first version of this probe
    # did not and wrongly cleared Qt. ui_webview.Toplevel creates its windows
    # with url= (a file served by pywebview's bundled HTTP server) and
    # js_api=, where this used html= and no api. The Qt crash stack lands in
    # webview/platforms/qt.py create_window, so what the window is made OF is
    # exactly the variable worth changing.
    #   --html   old behaviour, for comparison
    shape_html = '--html' in sys.argv
    here = os.path.dirname(os.path.abspath(__file__))
    page_file = os.path.join(here, '_probe.html')
    if not shape_html:
        with open(page_file, 'w') as fh:
            fh.write(PAGE.format('served page'))

    class Api:
        def on_event(self, wid, event_name, event_data):
            return 'ok'

    api = Api()

    def make(title):
        if shape_html:
            return webview.create_window(title, html=PAGE.format(title),
                                         width=500, height=300)
        return webview.create_window(title, url=page_file, js_api=api,
                                     width=500, height=300)

    print("window shape: {}".format('html= (no js_api)' if shape_html
                                    else 'url= + js_api  (as the app does)'))
    main_window = make('main window')

    # WHICH THREAD creates the window is the other difference from the app.
    # A-Z+T builds its Toplevels inside _run_setup, which ui_webview runs on
    # a DAEMON THREAD it spawned itself (mainloop's _safe_setup); this script
    # builds them in webview.start()'s own callback. pywebview marshals
    # create_window onto the GUI thread either way, but "either way" is an
    # assumption worth testing rather than trusting — the Qt crash stack ends
    # in qtpy's possibly_static_exec, which is that marshalling.
    #   --thread  create from a separate daemon thread, as the app does
    from_thread = '--thread' in sys.argv

    # TWO MORE WAYS THIS DIFFERED FROM THE APP, found after shape and thread
    # both came back clean:
    #   --keep  don't destroy each extra window. This probe peaked at TWO
    #           live windows; A-Z+T accumulates - root, chooser, task window,
    #           run window - and the Qt crash happened while creating one
    #           MORE on top of two that were already up.
    #   --fast  don't wait for a window to finish loading before creating the
    #           next. The app creates its windows back to back from setup
    #           code that never pauses; this script slept 1.5s between every
    #           step, which is ample time for a page to settle.
    keep = '--keep' in sys.argv
    fast = '--fast' in sys.argv
    pause = 0 if fast else 1.5
    kept = []

    def work(window):
        print("creating windows from: {}".format(
            'a separate daemon thread (as the app does)' if from_thread
            else "webview.start()'s own callback"))
        print("windows are {}; pause between steps: {}s".format(
            'KEPT (accumulating, as the app does)' if keep
            else 'destroyed each round', pause))
        print("main window is up")
        window.evaluate_js('document.getElementById("p").textContent'
                           ' = "main window alive"')
        for n in range(1, ROUNDS + 1):
            print("--- round {}: creating extra window".format(n))
            extra = make('extra {}'.format(n))
            time.sleep(pause)
            try:
                extra.evaluate_js('document.getElementById("p").textContent'
                                  ' = "extra window alive"')
                print("    evaluate_js in the extra window: OK")
            except Exception as e:
                print("    evaluate_js in the extra window FAILED: {}".format(e))
            time.sleep(pause / 3)
            if keep:
                kept.append(extra)
                print("    keeping it — {} extra window(s) now live"
                      "".format(len(kept)))
            else:
                print("    destroying it")
                extra.destroy()
            time.sleep(pause)
            print("    survived round {}".format(n))
            try:
                window.evaluate_js(
                    'document.getElementById("p").textContent'
                    ' = "survived round {}"'.format(n))
            except Exception as e:
                print("    main window unusable after teardown: {}".format(e))
                break
        print("ALL ROUNDS SURVIVED - multi-window is not the crash")
        print("Close the main window to finish.")

    def launch(window):
        if not from_thread:
            return work(window)
        import threading
        t = threading.Thread(target=work, args=(window,), daemon=True)
        t.start()

    webview.start(launch, main_window, http_server=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
