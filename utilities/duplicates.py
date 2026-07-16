#!/usr/bin/env python3
# coding=UTF-8

import os
import psutil
import pathlib
import sys
# print(sys.argv)
use_list_comprehension=False
def running_file(path):
    ok_processes=1
    if '--restart' in sys.argv:
        ok_processes+=1
    # venv bootstrap (py_modules.ensure_venv): the parent that relaunched
    # us may not have finished exiting yet — exclude exactly that pid,
    # once (pop: don't inherit into restarts).
    skip_pids={os.environ.pop('AZT_BOOTSTRAP_PARENT_PID','')}
    # Generic rule: our DIRECT spawner is never an independent copy — it's
    # the venv-bootstrap parent, or the old instance waiting out a Windows
    # sysrestart (subprocess.run blocks). A user-launched duplicate is
    # never our parent, so this can't weaken the real gate.
    skip_pids.add(str(os.getppid()))
    skip_pids.discard('')
    resolved=pathlib.Path(path).resolve()
    # psutil.process_iter.cache_clear() #doesn't seem to help
    try:
        if use_list_comprehension:
            l=[q.info['cmdline'] for q in psutil.process_iter(['cmdline'])
                if q.info['cmdline'] and '-X' not in q.info['cmdline']
                        and not [c for c in q.info['cmdline'] if 'py.exe' in c]
                and resolved in [pathlib.Path(c).resolve() for c in q.info['cmdline']]
                ]
        else:
            l=list() #may be less efficient
            for q in psutil.process_iter(['cmdline']):
                if str(q.pid) in skip_pids:
                    continue #our spawner (bootstrap parent / restart waiter)
                qcmd=q.info['cmdline']
                if qcmd is None or '-X' in qcmd or [i for i in qcmd
                                                if 'py.exe' in i]: #avoids need for try/except
                    continue
                for c in qcmd:
                    if resolved == pathlib.Path(c).resolve():
                        l.append(qcmd)
    except OSError as e:
        print(f"OS Error checking for running file: {e}")
        return
    if len(l)>ok_processes:
        import locale
        loc,enc=locale.getlocale()
        code=loc.split('_')[0]
        code='fr'
        if code in ['fr','FR','Fr','Français','French']:
            running="est déjà en cours"
            enter="Appuyer ENTER, ou fermer ce fenetre, pour quitter"
        else:
            running="is already running"
            enter="Press ENTER, or close this window, to exit"
        print(f"\n{pathlib.Path(path).resolve()} {running}:\n\n",
                '\n'.join([str(i) for i in l]))
        input('\n' + enter + '\n')
        return True
