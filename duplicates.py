#!/usr/bin/env python3
# coding=UTF-8

import psutil
import pathlib

def running_file(path):
    psutil.process_iter.cache_clear()
    l=list()
    for q in psutil.process_iter([]):
        try:
            for c in q.cmdline():
                if pathlib.Path(path).resolve() == pathlib.Path(c).resolve():
                    l.append(q.cmdline())
                # elif 'main.py' in c:
                #     l.append(q.cmdline())
        except psutil.ZombieProcess:
            continue
    if len(l)>1:
        print(f"\n{pathlib.Path(path).resolve()} is already running:\n\n",l)
        input('\nPress ENTER to exit\n')
        return True
