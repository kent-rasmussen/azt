import os
import sys
import __main__
try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    source_base_dir = sys._MEIPASS
    print(f"using {source_base_dir=}")
except Exception:
    try:
        # Calculate root relative to this file: azt/utilities/__init__.py -> azt/
        source_base_dir = os.path.dirname(
                            os.path.dirname(
                                os.path.abspath(__file__)
                            )
                        )
    except Exception:
        print(f"can't find __file__ in __main__, assume this is module testing.")
        source_base_dir=None
