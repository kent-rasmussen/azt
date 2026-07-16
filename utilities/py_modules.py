#!/usr/bin/env python3
# coding=UTF-8
from utilities import logsetup
log=logsetup.getlog(__name__)
logsetup.setlevel('INFO',log) #for this file
import platform
import sys
import subprocess
from utilities.utilities import stouttostr

try:
     _('x')
except NameError:
    def _(x):
        return str(x)

def pip_install(installs=[],secondtry=False):
    """With a list provided in installs, this installs only those modules.
    Otherwise, it tries to install everything needed by A−Z+T.
    Yes, this is excessive, but better than leaving users hanging if they can't
    resolve pip install issues."""
    if secondtry:
        log.info(_("Trying a second time, with ‘--force-reinstall’"))
    else:
        log.info(_("Installing python dependencies"))
    if platform.system() == 'Linux':
        log.info(_("If you have errors containing ˋportaudioˊ above, you should "
            "install pyaudio with your package manager."))
    # The following is here to see what version python will be looking for, and
    # why it didn't find what's there. It doesn't input to anything afterwards.
    log.info("FYI, looking for this platform: {}_{}".format(
                                                        platform.system(),
                                                        platform.processor()))
    installfolder='modulestoinstall/'
    installedsomething=False
    """Migrate this to `bin/pip install -r requirements.txt`"""
    if not installs:
        installs=[
            ['--upgrade', 'pip', 'setuptools', 'wheel'], #this is probably never needed
            ['urllib3'],
            ['numpy>=2.1,<2.5'], #KEEP IN STEP with requirements.txt — a bare
            # 'numpy' here installed 2.5.1 over the pin and re-broke numba
            # (2026-07-16); the backstop must never fight the requirements
            ['pyaudio'],
            ['Pillow'], #for PIL
            ['lxml'],
            ['psutil'],
            ['soundfile'],
            ['scipy'], #resampling (file_sound); also a transformers dep
            ['transformers'],
            ['huggingface_hub[hf_xet]'], #allow large file download
            ['langcodes[data]'],
            ['pyautogui'],
            ['svglib'],
            # ['mysql-connector-python', 'wave'], #needed for wave
            # 'pymysql', #or maybe this one
            ['torch==2.7.1+cpu',
             '--extra-index-url','https://download.pytorch.org/whl/cpu'],
            #pinned CPU wheel — bare 'torch' from PyPI pulls the CUDA build
            #(GBs) on Linux; keep in step with requirements.txt
            ['openai-whisper'], #for import whisper
            ['packaging'],
            ['patiencediff'],
            ['reportlab'], #for PDF
            #azt-collab collaboration (daemon runs in this env on desktop):
            ['dulwich'], #daemon git ops
            ['cryptography'], #LAN identity (peer keypair + cert)
            ['zeroconf'], #LAN discovery (mDNS)
            ['segno'], #pairing-QR rendering
            ['kivy'], #NOT imported in-process: the daemon's project picker +
            #          settings UI are Kivy SUBPROCESSES, and a standalone
            #          install has no other python to run them in
            ]
    else:
        installs=[installs] #do the whole list at once, if given a list
    log.info("Installs: {}".format(', '.join([i for j in installs for i in j])))
    for install in installs:
        thisinstalled=False
        pyargs=[sys.executable, '-m', 'pip', 'install',
        '-f', installfolder, #install the one in this folder, if there
        '--no-index' #This stops it from looking online
        ]
        npyargs=len(pyargs)
        if secondtry:
            pyargs.extend(['--force-reinstall'])
        pyargs.extend(install)
        log.info("Running `{}`".format(' '.join(pyargs)))
        try:
            o=subprocess.check_output(pyargs,shell=False,
                                        stderr=subprocess.STDOUT)
            o=stouttostr(o)
            if not o or "Successfully installed" in o:
                log.info(_("looks like it was successful; so I’m going to reboot "
                            "in a bit. Output follows:"))
                thisinstalled=installedsomething=True
        except subprocess.CalledProcessError as e:
            o=stouttostr(e.output)
            if 'Could not find a version' in o:
                pyargs.remove('--no-index')
                log.info("Running `{}`".format(' '.join(pyargs)))
                try:
                    o=subprocess.check_output(pyargs,shell=False,
                                            stderr=subprocess.STDOUT)
                    o=stouttostr(o)
                    if not o or "Successfully installed" in o:
                        log.info(_("looks like it was at last successful; so "
                                "I’m going to reboot in a bit. Output follows:"))
                        thisinstalled=installedsomething=True
                except subprocess.CalledProcessError as e:
                    o=stouttostr(e.output)
                    if "Could not find a version" in o:
                        errors=[i for i in o.splitlines() if "ERROR:" in i]
                        log.info(_("Please make sure your internet is connected, then "
                        "click {}\n{}").format(_("OK"),'\n'.join(errors)))
                        # ErrorNotice(text=t,parent=ui.Root(),wait=True)
                        log.info(_("Trying again, hopefully with internet"))
                        try:
                            o=subprocess.check_output(pyargs,shell=False,
                                                stderr=subprocess.STDOUT)
                            o=stouttostr(o)
                            if not o or "Successfully installed" in o:
                                log.info(_("looks like it was at last successful;"
                                        " so I’m going to reboot in a bit. "
                                        "Output follows:"))
                                thisinstalled=installedsomething=True
                        except Exception as e:
                            log.info(_("I’m going to give up now, sorry!\n{}"
                                "").format('\n'.join(errors)))
                            # ErrorNotice(text=t,parent=ui.Root(),wait=True)
                            log.error(_("Looks like there was an error, "
                                        "after all: {}").format(e))
        if not thisinstalled:
            log.info(_("Nothing installed. Output follows:"))
        log.info(o) #just give bytes, if encoding isn't correct
    if not installedsomething and not secondtry:
        pip_install(secondtry=True) #force reinstalls, just once

MIN_PYTHON=(3,10) #raise deliberately when azt needs newer; ensure_venv
#                  rolls it out: an outdated CHILD env is rebuilt from a
#                  new-enough base python; an outdated base/sister just warns.

def _venv_python(envdir):
    """The interpreter inside envdir, or None. Keeps the launcher's
    flavor on Windows: a double-click shortcut usually runs pythonw.exe
    (no console); relaunching that into python.exe would flash a console
    window up."""
    import os
    if platform.system() == 'Windows':
        exe=('pythonw.exe' if sys.executable.lower().endswith('pythonw.exe')
             else 'python.exe')
        py=os.path.join(envdir,'Scripts',exe)
    else:
        py=os.path.join(envdir,'bin','python')
    return py if os.path.isfile(py) else None

def _rmtree_force(path):
    """shutil.rmtree that also handles Windows read-only files/dirs (a
    half-created venv can be left read-only, and plain rmtree then fails
    on every boot — seen 2026-07-16). Returns True when the dir is gone."""
    import os, shutil, stat
    def _onerr(fn,p,exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            fn(p)
        except Exception:
            pass
    try:
        shutil.rmtree(path, onerror=_onerr)
    except Exception as e:
        log.error("Couldn’t remove {} ({})".format(path,e))
    return not os.path.isdir(path)

def _python_probe(py):
    """((major,minor), is_venv) of an interpreter, or (None, None) when it
    can't even run (zombie venv). is_venv matters: a half-created Windows
    venv can hold a python.exe that runs as a PLAIN python (no working
    pyvenv.cfg) — sync_requirements then silently refuses to manage it
    (2026-07-16)."""
    try:
        out=subprocess.check_output(
            [py,'-c','import sys;print(sys.version_info[0],'
                     'sys.version_info[1],'
                     'int(sys.prefix!=sys.base_prefix))'],timeout=30)
        maj,minor,isvenv=out.split()
        return (int(maj),int(minor)),bool(int(isvenv))
    except Exception:
        return None,None

def ensure_venv():
    """azt should run inside a venv named 'env', so its heavy dependency
    set lands there and not in the system python. Lookup order: SISTER
    (<azt>/../env — the suite convention, shared with the collab daemon)
    then CHILD (<azt>/env); if neither exists, CREATE the child. On a
    machine with only a plain python install (the normal fresh Windows
    case: run the python.org installer, clone azt, run azt), the first
    start creates env/ and relaunches inside it; sync_requirements below
    then fills it. Runs under a BARE python (stdlib only — this executes
    before any pip dependency can be assumed).

    Opt out with AZT_NO_VENV=1 (e.g. conda users). Never blocks startup:
    any failure logs and continues in the current interpreter."""
    import os
    if sys.prefix != sys.base_prefix:
        #already in a venv (ours or the user's own)
        if sys.version_info[:2] < MIN_PYTHON:
            log.error(_("This python ({have}) is older than A-Z+T needs "
                "({need}). Install a newer python (the python.org "
                "installer), delete this env folder, and restart."
                "").format(have='.'.join(map(str,sys.version_info[:2])),
                           need='.'.join(map(str,MIN_PYTHON))))
        return
    if os.environ.get('AZT_NO_VENV'):
        return
    if os.environ.get('AZT_VENV_RELAUNCHED'):
        log.error("Relaunched into the venv but still outside one; "
                    "continuing without it (check the env folder).")
        return
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    suite=os.path.dirname(root)
    child=os.path.join(root,'env')
    py=None
    for envdir in (os.path.join(suite,'env'),child): #sister first
        py=_venv_python(envdir)
        if py:
            break
    if py:
        v,isvenv=_python_probe(py)
        rebuild=None
        if v is None:
            # The env's python couldn't even report a version — the classic
            # Windows zombie venv: its base python was moved/uninstalled, so
            # env\Scripts\python.exe just prints "No Python at '...'" and
            # dies. Relaunching into it kills the app on every start
            # (2026-07-16, Windows) — rebuild ours, route around the user's.
            rebuild=_("its python doesn’t run — was the python it was "
                      "made from uninstalled or moved?")
        elif not isvenv:
            # runs, but as a PLAIN python: half-created venv (Windows,
            # 2026-07-16) — requirements management silently disowns it.
            rebuild=_("its python isn’t actually a virtual environment "
                      "(creation half-failed?)")
        elif v < MIN_PYTHON:
            rebuild=_("python {old} < {need}").format(
                        old='.'.join(map(str,v)),
                        need='.'.join(map(str,MIN_PYTHON)))
        if rebuild:
            if (envdir == child and sys.version_info[:2] >= MIN_PYTHON):
                #ours, broken/outdated, and we have a good base: rebuild it
                log.info(_("Rebuilding {dir} ({why})...").format(
                                                dir=envdir,why=rebuild))
                if not _rmtree_force(envdir):
                    log.error("Couldn’t remove the broken env; "
                                "continuing outside it.")
                    return
                py=None #fall through to fresh creation below
            elif v is None or not isvenv: #the user's sister env, unusable:
                log.warning(_("The env at {dir} is broken ({why}); leaving "
                    "it alone and using {child} instead. Delete or fix "
                    "{dir} to use it again.").format(dir=envdir,why=rebuild,
                                                     child=child))
                py=None #creation below makes the child
            else: #the user's sister env, old but functional: warn only
                log.warning(_("The env at {dir} runs python {old}; A-Z+T "
                    "wants {need}+. It may still work, but plan to "
                    "recreate it from a newer python.").format(dir=envdir,
                        old='.'.join(map(str,v)),
                        need='.'.join(map(str,MIN_PYTHON))))
    if py is None:
        if sys.version_info[:2] < MIN_PYTHON:
            log.error(_("This python ({have}) is older than A-Z+T needs "
                "({need}); install a newer one (the python.org installer) "
                "and restart. Trying to continue anyway..."
                "").format(have='.'.join(map(str,sys.version_info[:2])),
                           need='.'.join(map(str,MIN_PYTHON))))
            return
        if os.path.isdir(child):
            # exists but unusable (no python.exe: creation died partway,
            # possibly left read-only — Windows 2026-07-16): clear it fully
            # rather than trusting venv to repair a corpse.
            log.info(_("Clearing the broken env at {dir} before "
                        "recreating...").format(dir=child))
            if not _rmtree_force(child):
                log.error("Couldn’t clear it; continuing without a venv.")
                return
        log.info(_("First run: creating a python virtual environment at "
                    "{dir} (dependencies will install there)...").format(
                                                                dir=child))
        try:
            subprocess.check_call([sys.executable,'-m','venv',child])
        except Exception as e:
            log.error("Couldn’t create a venv ({}); continuing with {}"
                        "".format(e,sys.executable))
            return
        py=_venv_python(child)
        if py is None:
            log.error("venv created but its python is missing; "
                        "continuing with {}".format(sys.executable))
            return
        v,isvenv=_python_probe(py) #validate BEFORE relaunching into it:
        if not isvenv: #runs as plain python = half-made (Windows 2026-07-16)
            log.error("The created venv doesn’t function as one; clearing "
                        "it and continuing with {} (will retry next start)"
                        "".format(sys.executable))
            _rmtree_force(child)
            return
    log.info(_("Relaunching inside the virtual environment: {py}").format(
                                                                    py=py))
    env=dict(os.environ,
             AZT_VENV_RELAUNCHED='1', #no relaunch loops on a broken venv
             AZT_BOOTSTRAP_PARENT_PID=str(os.getpid())) #we're still alive
             #  when the child's duplicate-process check runs; it excludes
             #  this pid once (utilities/duplicates.py), then forgets it.
    try:
        subprocess.Popen([py]+sys.argv,env=env)
    except Exception as e:
        log.error("Couldn’t relaunch in the venv ({}); continuing with {}"
                    "".format(e,sys.executable))
        return
    sys.exit(0) #the venv process takes over from here
ensure_venv()

def sync_requirements():
    """Keep the venv in step with requirements.txt: any edit there (new
    dependency, version pin or bump) rolls out to EVERY install on its
    next start — the import-check below only catches packages that are
    missing outright, never wrong versions. Offline-first
    (modulestoinstall/), online fallback; stamped by content hash inside
    the venv, so unchanged requirements cost one file read per boot."""
    import os, hashlib
    if sys.prefix == sys.base_prefix:
        log.info("Not in a venv; not syncing requirements.txt here "
                    "(the per-package fallback below still runs). "
                    "AZT_NO_VENV set, or did the venv bootstrap fail?")
        return #only manage a venv, never a system python
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    req=os.path.join(root,'requirements.txt')
    if not os.path.isfile(req):
        log.error("requirements.txt not found at {} — this azt copy is "
                    "incomplete; only the per-package fallback list will "
                    "install.".format(req))
        return
    with open(req,'rb') as f:
        cur=hashlib.sha256(f.read()).hexdigest()
    stampfile=os.path.join(sys.prefix,'azt_requirements.stamp')
    try:
        with open(stampfile) as f:
            if f.read().strip() == cur:
                return
    except OSError:
        pass
    log.info(_("Requirements changed (or first run in this env); "
                "synchronizing python packages — this can take a while..."))
    base=[sys.executable,'-m','pip','install',
          '-f',os.path.join(root,'modulestoinstall'),
          '-r',req]
    for args in (base+['--no-index'],base): #offline-first, then online
        passname='offline' if '--no-index' in args else 'online'
        try:
            o=subprocess.check_output(args,stderr=subprocess.STDOUT)
            o=stouttostr(o)
            installed=[l for l in o.splitlines()
                       if l.startswith('Successfully installed')]
            log.info(_("Python packages synchronized ({mode}): {what}"
                        "").format(mode=passname,
                                   what=installed[-1] if installed
                                        else 'nothing to change'))
            with open(stampfile,'w') as f:
                f.write(cur)
            return
        except subprocess.CalledProcessError as e:
            o=stouttostr(e.output)
            tail='\n'.join(o.splitlines()[-12:])
            if passname == 'offline':
                log.info("offline package sync incomplete; trying online. "
                            "pip said:\n{}".format(tail))
            else:
                log.error("package sync FAILED — the requirements did NOT "
                            "install; the per-package backstop below will "
                            "try individually. pip said:\n{}".format(tail))
        except Exception as e:
            log.error("package sync failed ({}); continuing with "
                        "what’s installed".format(e))
sync_requirements()

def ensure_sister_repos():
    """azt expects some repos cloned beside its own clone: the collab
    daemon+client, the CAWL illustration set, and the stock wordlist
    templates. utilities/sister_repos.py owns the table and mechanics
    (clone if absent, symlink/junction the in-repo access points); each
    is optional, so this must never block startup."""
    try:
        from utilities import sister_repos
        for name,ok in sister_repos.ensure_all().items():
            if not ok:
                log.info(_("Sister repo {name} unavailable (see above); "
                            "continuing without it.").format(name=name))
    except Exception as e:
        log.error("Sister-repo setup failed ({}); continuing.".format(e))
ensure_sister_repos()

try:
    o=[]
    import urllib3, numpy, pyaudio, PIL, lxml, psutil, soundfile, scipy
    o.append("urllib3, numpy, pyaudio, PIL, lxml, psutil, soundfile, scipy imported fine")
    import transformers, huggingface_hub, langcodes #, pyautogui
    o.append("transformers, huggingface_hub, langcodes imported fine")
    import whisper, patiencediff, reportlab, language_data
    o.append("whisper, patiencediff, reportlab, language_data imported fine")
    # kivy: presence check ONLY — never import it in this (tkinter) process;
    # its import-time argv parser can eat azt's own flags (see collab.py).
    # It's needed as a SUBPROCESS runtime for the collab picker/settings UI.
    from importlib.util import find_spec as _find_spec
    if _find_spec('kivy') is None:
        raise ImportError('kivy not installed (needed for the collab '
                          'project picker / settings UI subprocesses)')
    o.append("kivy present (not imported)")
    import os, svglib
    o.append("os, svglib imported fine")
    # import platform
    if platform.system() == "Windows":
        import ctypes
        from importlib.util import find_spec
        try:
            if (spec := find_spec("torch")) and spec.origin and os.path.exists(
                dll_path := os.path.join(os.path.dirname(spec.origin), "lib", "c10.dll")
            ):
                ctypes.CDLL(os.path.normpath(dll_path))
        except Exception as e:
            log.info(f"Exception loading torch dll: {e}")

    # Testing
    # from PyQt6.QtWidgets import QApplication
    import torch
except Exception as e:
    log.info('\n'.join(o))
    log.error(f"Exception: {e}")
    if '--help' in sys.argv or '-h' in sys.argv:
        log.error("Not all modules installed, but not installing them because you asked for help.")
        sys.exit(0)
    pip_install()
