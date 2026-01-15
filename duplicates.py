#!/usr/bin/env python3
# coding=UTF-8

import psutil
import pathlib
import sys
# print(sys.argv)
use_list_comprehension=False
def running_file(path):
    ok_processes=1
    if '--restart' in sys.argv:
        ok_processes+=1
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
                qcmd=q.info['cmdline']
                if qcmd is None or '-X' in qcmd: #avoids need for try/except
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
            enter="Appuyer ENTER pour quitter"
        else:
            running="is already running"
            enter="Press ENTER to exit"
        print(f"\n{pathlib.Path(path).resolve()} {running}:\n\n",
                '\n'.join([str(i) for i in l]))
        input('\n' + enter + '\n')
        return True
