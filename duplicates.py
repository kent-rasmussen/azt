#!/usr/bin/env python3
# coding=UTF-8

import psutil
import pathlib

def running_file(path):
    resolved=pathlib.Path(path).resolve()
    psutil.process_iter.cache_clear()

    l=list()
    for q in psutil.process_iter([]):
        try:
            qcmd=q.cmdline()
            if '-X' not in qcmd:
                continue
            for c in qcmd:
                if resolved == pathlib.Path(c).resolve():
                    l.append(qcmd)
        except psutil.ZombieProcess:
            continue
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
