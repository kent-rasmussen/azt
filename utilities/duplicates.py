#!/usr/bin/env python3
# coding=UTF-8

import os
import psutil
import pathlib
import sys
import time
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
    # Restart predecessors, handed over explicitly by utilities.sysrestart
    # (2026-07-30). NOT popped: the list must survive into the next restart so a
    # chain skips every predecessor, not just the immediate one. It exists because
    # the ancestor walk below is unreliable exactly when it matters — a Tk app with
    # worker threads does not exit promptly, and one dead intermediate truncates
    # ppid walking, so a lingering grandparent counted as a duplicate ("too many
    # processes" on restart after update, Windows, field 2026-07-30).
    skip_pids |= {p for p in
                    os.environ.get('AZT_PREDECESSOR_PIDS','').split(',') if p}
    # Generic rule: our ANCESTORS are never independent copies — they're
    # the venv-bootstrap parent, or old instances waiting out Windows
    # sysrestarts (subprocess.run blocks, so restart CHAINS accumulate one
    # waiter per restart — three found after two restarts, 2026-07-16). A
    # user-launched duplicate is never our ancestor, so this can't weaken
    # the real gate.
    try:
        for anc in psutil.Process().parents():
            skip_pids.add(str(anc.pid))
    except Exception:
        skip_pids.add(str(os.getppid()))
    skip_pids.discard('')
    resolved=pathlib.Path(path).resolve()
    # psutil.process_iter.cache_clear() #doesn't seem to help
    try:
        if use_list_comprehension:
            # Dead branch (the flag is False): kept for reference, but note it
            # honours neither skip_pids nor the (pid, age, cmdline) shape the
            # reporting below needs — the tuple keeps it at least printable.
            l=[(q.pid,-1,q.info['cmdline'])
                for q in psutil.process_iter(['cmdline'])
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
                        # Keep the pid and age: when this gate fires wrongly the
                        # printed list is the only evidence, and "which pid, how
                        # old" is what distinguishes a lingering predecessor from a
                        # genuine second copy the user launched.
                        try:
                            age=int(time.time()-q.create_time())
                        except Exception:
                            age=-1
                        l.append((q.pid,age,qcmd))
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
                '\n'.join(f"pid {pid} ({age}s old): {cmd}"
                            for pid,age,cmd in l))
        print(f"(this process: pid {os.getpid()}; "
                f"allowed {ok_processes}; skipped pids: "
                f"{sorted(skip_pids) or 'none'})")
        input('\n' + enter + '\n')
        return True
