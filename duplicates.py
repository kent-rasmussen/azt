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
        print(f"\n{pathlib.Path(path).resolve()} is already running:\n\n",
                '\n'.join([str(i) for i in l]))
        input('\nPress ENTER to exit\n')
        return True
