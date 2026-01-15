#!/usr/bin/env python3
# coding=UTF-8

import psutil
import pathlib

def running_file(path):
    resolved=pathlib.Path(path).resolve()
    # psutil.process_iter.cache_clear() #doesn't seem to help

    l=[q.info['cmdline'] for q in psutil.process_iter(['cmdline'])
            if q.info['cmdline'] and '-X' not in q.info['cmdline']
                    and not [c for c in q.info['cmdline'] if 'py.exe' in c]
            and resolved in [pathlib.Path(c).resolve() for c in q.info['cmdline']]
            ]
    # l=list() #may be less efficient
    # for q in psutil.process_iter(['cmdline']):
    #     qcmd=q.info['cmdline']
    #     if qcmd is None or '-X' in qcmd: #avoids need for try/except
    #         continue
    #     for c in qcmd:
    #         if resolved == pathlib.Path(c).resolve():
    #             l.append(qcmd)
    if len(l)>1:
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
