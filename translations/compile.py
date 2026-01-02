#!/usr/bin/env python3
"""This module compiles .po files to .mo files using msgfmt; 
run after updating .po files from crowdin."""
import os
import subprocess
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Scanning for .po translation files in: {base_dir}")
def mod_time(file):
    return os.stat(file).st_mtime
def newer(po,mo):
    return mod_time(po) > mod_time(mo)
def compile_translations():
    count = 0
    errors = 0

    for root, dirs, files in os.walk(base_dir):
        if 'azt.po' in files:
            po=os.path.join(root, 'azt.po')
            mo=os.path.join(root, 'azt.mo')
            if 'azt.mo' not in files or newer(po,mo):
                print(f"Compiling {po} -> {mo}...")
                try:
                    subprocess.run(['msgfmt', '-o', mo, po], check=True)
                    count += 1
                except subprocess.CalledProcessError as e:
                    print(f"Error compiling {po}: {e}")
                    errors += 1
                except FileNotFoundError:
                    print("Error: msgfmt not found. Please install gettext.")
                    return
    print(f"\nDone. Compiled {count} files with {errors} errors.")

if __name__ == "__main__":
    compile_translations()
