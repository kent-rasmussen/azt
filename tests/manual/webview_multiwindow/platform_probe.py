# coding=UTF-8
"""A-Z+T manual test: does this platform's webview support A-Z+T's windows?

ONE QUESTION PER STEP, answered in the page. Every window primitive the port
depends on is exercised in order, and the result is drawn as a PASS/FAIL table
INSIDE the probe window — so a machine that cannot hand text back (no write
access, no clipboard, no shell you want to use) still reports its result to a
photograph. That lesson came from the Keyman check, where the copy-a-report
flow assumed a machine that could paste.

    pip install pywebview          # Windows: also pulls pythonnet
    python platform_probe.py

Optional, to force an engine:
    PYWEBVIEW_GUI=gtk python platform_probe.py
    PYWEBVIEW_GUI=qt  python platform_probe.py

WHAT IT IS FOR. On Linux/GTK we know: a window created HIDDEN never appears
(show() will not map it), which is why A-Z+T cannot create its task windows
withdrawn the way the tkinter backend does. Windows uses a THIRD engine —
EdgeChromium/WebView2, neither GTK nor Qt — and if that one honours
`hidden=True`, then the platform that actually matters can create windows
hidden and the startup flash gets a proper fix there rather than a workaround.
Qt additionally segfaults when a window is destroyed, so the destroy step here
is a real question and not a formality.

Steps 1, 5 and 6 are decided by the machine; the rest need your eye, because
no webview API reports whether a window is actually mapped.

Deliberately imports nothing from azt.
"""
import json
import os
import platform
import sys
import threading
import time

PAUSE = 1.5

PAGE = """
<html><head><meta charset="utf-8"><style>
 body{font:15px/1.45 system-ui,sans-serif;margin:0;padding:18px 22px;
      background:#8cd9bf;color:#111}
 h1{font-size:19px;margin:0 0 4px} h2{font-size:15px;margin:18px 0 6px}
 #env{font:12px ui-monospace,Consolas,monospace;white-space:pre-wrap;
      background:#f7f7f9;border:1px solid #ccc;padding:8px;margin:8px 0}
 #q{background:#fff;border:2px solid #333;padding:14px;margin:12px 0;
    font-size:17px;min-height:52px}
 button{font:inherit;padding:8px 22px;margin-right:10px;cursor:pointer}
 table{border-collapse:collapse;width:100%;margin-top:8px;background:#fff}
 td,th{border:1px solid #bbb;padding:5px 8px;text-align:left;font-size:13px}
 .pass{color:#076;font-weight:700} .fail{color:#b00;font-weight:700}
 .skip{color:#777}
 #verdict{font-size:20px;font-weight:700;margin:14px 0;padding:10px;
          background:#fff;border:2px solid #333}
</style></head><body>
<h1>A-Z+T webview platform probe</h1>
<div id="env">collecting…</div>
<div id="q">starting…</div>
<div><button id="yes">Yes</button><button id="no">No</button></div>
<h2>Results</h2>
<table id="results"><tr><th>Step</th><th>Result</th><th>Note</th></tr></table>
<div id="verdict"></div>
<script>
 var current=null;
 function env(text){document.getElementById('env').textContent=text
   +"\\nuserAgent: "+navigator.userAgent;}
 function ask(key,question){
   current=key;
   document.getElementById('q').textContent=question;
   document.getElementById('yes').disabled=false;
   document.getElementById('no').disabled=false;
 }
 function noask(text){
   current=null;
   document.getElementById('q').textContent=text;
   document.getElementById('yes').disabled=true;
   document.getElementById('no').disabled=true;
 }
 function record(step,ok,note){
   var t=document.getElementById('results');
   var cls=ok==null?'skip':(ok?'pass':'fail');
   var word=ok==null?'—':(ok?'PASS':'FAIL');
   t.insertAdjacentHTML('beforeend','<tr><td>'+step+'</td><td class="'+cls
     +'">'+word+'</td><td>'+(note||'')+'</td></tr>');
 }
 function verdict(text){document.getElementById('verdict').textContent=text;}
 function send(ok){
   if(current===null) return;
   var k=current; current=null;
   document.getElementById('yes').disabled=true;
   document.getElementById('no').disabled=true;
   document.getElementById('q').textContent='…';
   window.pywebview.api.answer(k,ok);
 }
 document.getElementById('yes').onclick=function(){send(true)};
 document.getElementById('no').onclick=function(){send(false)};
</script></body></html>
"""

# NOTHING HERE IS IDENTIFIED BY COLOUR. Kent is colourblind, so a question
# like "is the yellow window on screen?" is unanswerable — and it was, in the
# first version. Windows are named by their TITLE BAR text and by the heading
# printed inside them, both of which read the same in greyscale.
EXTRA = ("<html><body style='font:22px system-ui;padding:40px'>"
         "<h2 id='h'>{}</h2>"
         "<p>If you can read this, this window is on screen.</p>"
         "</body></html>")
HIDDEN_TITLE = 'EXTRA 1 (created hidden)'
VISIBLE_TITLE = 'EXTRA 2 (created visible)'


class Api:
    def __init__(self):
        self.events = {}
        self.answers = {}

    def waiter(self, key):
        ev = threading.Event()
        self.events[key] = ev
        return ev

    def answer(self, key, ok):
        self.answers[key] = bool(ok)
        ev = self.events.get(key)
        if ev:
            ev.set()
        return 'ok'


def main():
    try:
        import webview
    except ImportError:
        sys.stderr.write("pywebview is not installed in this interpreter.\n"
                         "  pip install pywebview\n")
        return 2

    api = Api()
    main_window = webview.create_window('A-Z+T webview platform probe',
                                        html=PAGE, js_api=api,
                                        width=900, height=760)

    def js(code):
        try:
            return main_window.evaluate_js(code)
        except Exception as e:
            print("evaluate_js failed: {}".format(e))
            return None

    def record(step, ok, note=''):
        print("  {:<44} {}".format(
            step, 'PASS' if ok else ('FAIL' if ok is False else '-')))
        js('record({},{},{})'.format(json.dumps(step),
                                     'null' if ok is None else
                                     ('true' if ok else 'false'),
                                     json.dumps(note)))

    def ask(key, step, question):
        ev = api.waiter(key)
        js('ask({},{})'.format(json.dumps(key), json.dumps(question)))
        ev.wait()
        ok = api.answers.get(key, False)
        record(step, ok)
        return ok

    def asked_engine():
        """The engine to request: --engine=NAME, else PYWEBVIEW_GUI, else the
        platform default.

        --engine= is accepted because the APP accepts it, and a probe whose
        switches differ from the app's is a probe that tests the wrong thing:
        the first version read only PYWEBVIEW_GUI, so `--engine=qt` was
        silently ignored and a table labelled Qt was actually GTK."""
        for arg in sys.argv:
            if arg.startswith('--engine='):
                return arg.split('=', 1)[1].strip().lower() or None
        name = (os.environ.get('AZT_WEBVIEW_ENGINE')
                or os.environ.get('PYWEBVIEW_GUI') or '').strip().lower()
        return name or None

    def pywebview_version():
        try:
            import webview as wv
            v = getattr(wv, '__version__', None)
            if v:
                return v
        except Exception:
            pass
        try:
            from importlib.metadata import version
            return version('pywebview')
        except Exception:
            return 'unknown'

    def loaded_engine():
        """WHICH ENGINE ACTUALLY LOADED — not which one was asked for.

        The two can differ, and on Windows the difference is the whole point:
        if the WebView2 runtime is missing, pywebview can fall back to
        **mshtml** (legacy Trident/IE), which has no CSS Grid, so A-Z+T's
        pages would render as garbage rather than not rendering. A result
        table that does not name the engine cannot be read.

        Asked three ways, because pywebview's internals move between
        versions and the userAgent is the one answer that cannot lie: it is
        the engine's own self-report."""
        asked = asked_engine() or '(not specified — platform default)'
        module = 'unknown'
        try:
            import webview.guilib as guilib
            gui = getattr(guilib, 'guilib', None)
            module = getattr(gui, '__name__', None) or str(gui)
        except Exception as e:
            module = 'could not read webview.guilib ({})'.format(e)
        ua = js('navigator.userAgent') or ''
        fingerprint = 'unrecognised'
        low = ua.lower()
        if 'edg/' in low or 'edge' in low:
            fingerprint = 'EdgeChromium / WebView2'
        elif 'chrome' in low and 'safari' in low and 'version/' not in low:
            fingerprint = 'Chromium (Qt WebEngine or CEF)'
        elif 'version/' in low and 'safari' in low:
            fingerprint = 'WebKit (WebKitGTK)'
        elif 'trident' in low or 'msie' in low:
            fingerprint = 'MSHTML / Trident — LEGACY IE, no CSS Grid'
        return asked, module, fingerprint, ua

    def work(_win):
        version = pywebview_version()
        asked, module, fingerprint, ua = loaded_engine()
        js('env({})'.format(json.dumps(
            "platform:  {} {}\npython:    {}\npywebview: {}\n"
            "engine asked for: {}\nengine module:    {}\n"
            "ENGINE IN USE:    {}".format(
                platform.system(), platform.release(),
                platform.python_version(), version,
                asked, module, fingerprint))))
        print("")
        print("engine asked for: {}".format(asked))
        print("engine module:    {}".format(module))
        print("ENGINE IN USE:    {}".format(fingerprint))
        print("userAgent:        {}".format(ua))
        # In the results table too, so a photograph of it is self-contained.
        record('0. engine in use: {}'.format(fingerprint),
               None if 'unrecognised' in fingerprint
               else ('LEGACY' not in fingerprint),
               'asked for {}'.format(asked))
        print("")
        print("A-Z+T webview platform probe — answer in the window")
        print("")

        results = {}

        # 1 — machine-decided: can Python script the page at all?
        got = js('1+1')
        results['bridge'] = (got == 2)
        record('1. evaluate_js works (machine)', got == 2,
               'returned {!r}'.format(got))

        # 2 — THE OPEN QUESTION. GTK fails this; Windows/EdgeChromium unknown.
        js('noask("Creating a window with hidden=True, then calling show() '
           'after 1.5s…")')
        hidden_win = webview.create_window(HIDDEN_TITLE,
                                           html=EXTRA.format(HIDDEN_TITLE),
                                           width=520, height=260,
                                           hidden=True)
        time.sleep(PAUSE)
        # POLARITY: ask the question whose YES is the PASS. The first version
        # asked "is it on screen?" and recorded the answer directly, so
        # correct behaviour (not on screen) was written down as FAIL and the
        # note had to explain that the failure was fine. A result table that
        # needs a footnote to be read the right way up is a broken table.
        before = ask('hidden_before', '2a. created hidden STAYS hidden',
                     'A window was just created with hidden=True, titled '
                     '"{}". Is it correctly NOT on screen? '
                     '(Yes = it is hidden, as asked.)'.format(HIDDEN_TITLE))
        try:
            hidden_win.show()
        except Exception as e:
            record('2b. show() on a created-hidden window', False, str(e))
        else:
            time.sleep(PAUSE)
            results['created_hidden'] = ask(
                'hidden_after', '2b. created hidden then show() APPEARS',
                'show() has now been called on "{}". Did it APPEAR? '
                '(On Linux/GTK it never does — that is the thing being '
                'tested.)'.format(HIDDEN_TITLE))
        if not before:
            record('2a note', None,
                   'it was VISIBLE despite hidden=True — unexpected')

        # 3 — hide/show round trip on a window created VISIBLE.
        js('noask("Creating a second window, visible this time…")')
        vis = webview.create_window(VISIBLE_TITLE,
                                    html=EXTRA.format(VISIBLE_TITLE),
                                    width=520, height=260)
        time.sleep(PAUSE)
        ask('vis_shown', '3a. created visible IS visible',
            'Is a window titled "{}" on screen now?'.format(VISIBLE_TITLE))
        rounds = []
        for n in (1, 2, 3):
            vis.hide()
            time.sleep(PAUSE)
            gone = ask('hide{}'.format(n),
                       '3b.{} hide() hides it'.format(n),
                       'Round {}: hide() called on "{}". Has it '
                       'DISAPPEARED?'.format(n, VISIBLE_TITLE))
            vis.show()
            time.sleep(PAUSE)
            back = ask('show{}'.format(n),
                       '3c.{} show() brings it back'.format(n),
                       'Round {}: show() called on "{}". Has it COME '
                       'BACK?'.format(n, VISIBLE_TITLE))
            rounds.append(gone and back)
        results['hide_show'] = all(rounds)
        record('3. hide/show round trip, 3 rounds', all(rounds),
               '{} of 3 clean'.format(sum(1 for r in rounds if r)))

        # 4 — resize: machine-decided, the page can measure itself.
        js('noask("Resizing the extra window…")')
        try:
            w0 = vis.evaluate_js('window.innerWidth')
            vis.resize(760, 420)
            time.sleep(PAUSE)
            w1 = vis.evaluate_js('window.innerWidth')
            ok = bool(w0 and w1 and int(w1) > int(w0))
            results['resize'] = ok
            record('4. resize() takes effect (machine)', ok,
                   '{} -> {}'.format(w0, w1))
        except Exception as e:
            record('4. resize() takes effect (machine)', False, str(e))

        # 5 — destroy. Qt SEGFAULTS here; if the process dies, the absence of
        #     further rows in the table is itself the answer.
        js('noask("Destroying the extra window — if this process dies here, '
           'that IS the result: no further rows will appear.")')
        time.sleep(PAUSE)
        try:
            vis.destroy()
            time.sleep(PAUSE)
        except Exception as e:
            record('5a. destroy() does not raise', False, str(e))
        else:
            record('5a. destroy() does not raise', True)
        alive = js('1+1') == 2
        results['destroy'] = alive
        record('5b. process survives destroy() (machine)', alive)
        ask('destroy_gone', '5c. destroyed window is gone',
            'Has "{}" gone from the screen?'.format(VISIBLE_TITLE))

        # 6 — is the FIRST window still usable afterwards? (Qt's crash took
        #     the whole process; a milder bug might only break the survivor.)
        record('6. this window still scriptable (machine)',
               js('1+1') == 2)

        # CLEAN UP THE WINDOW STEP 2 LEFT BEHIND. If created-hidden worked,
        # "EXTRA 1" is on screen and the probe was walking away from it
        # (reported 2026-09-08 on Qt, which passes that step). A test that
        # litters is a test people stop running.
        try:
            if hidden_win is not None:
                hidden_win.destroy()
        except Exception as e:
            print("could not close {}: {}".format(HIDDEN_TITLE, e))

        good = [k for k, v in results.items() if v]
        bad = [k for k, v in results.items() if not v]
        summary = ("VERDICT — works: {} | fails: {}".format(
            ', '.join(good) or 'nothing', ', '.join(bad) or 'nothing'))
        print("")
        print(summary)
        print("Photograph the window if this machine cannot paste text.")
        js('verdict({})'.format(json.dumps(summary)))
        js('noask("Done. Close this window to finish.")')

    start_kwargs = {}
    engine = asked_engine()
    if engine:
        start_kwargs['gui'] = engine
        print("requesting engine: {}".format(engine))
    webview.start(work, main_window, **start_kwargs)
    return 0


if __name__ == '__main__':
    sys.exit(main())
