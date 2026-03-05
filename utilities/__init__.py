import os
import sys
import __main__
try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    source_base_dir = sys._MEIPASS
    print(f"using {source_base_dir=}")
except Exception:
    print(dir(__main__),type(__main__))
    for f in ['name', 'package', 'spec', 'doc', 'builtins', 'annotations']:
        print(f, getattr(__main__, '__'+f+'__'))
    try:
        source_base_dir=os.path.dirname(__main__.__file__)
    except Exception:
        print(f"can't find __file__ in __main__, assume this is module testing.")
        source_base_dir=None