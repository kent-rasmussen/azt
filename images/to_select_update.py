"""Clone or update the images_CAWL repository and ensure it is symlinked.

This script places images_CAWL as a sibling of the azt project directory,
wherever azt happens to be installed. It can be run standalone or called
from within the program when images/toselect is missing.

Usage:
    python images/to_select_update.py          # from the azt directory
    python -m images.to_select_update          # as a module
"""
import os
import subprocess
import sys

REPO_URL = "https://github.com/kent-rasmussen/images_CAWL.git"
REPO_NAME = "images_CAWL"
SYMLINK_NAME = "toselect"

def get_paths():
    """Return (azt_dir, images_cawl_dir, symlink_path)."""
    # The azt project root is the parent of the images/ directory
    azt_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_dir = os.path.dirname(azt_dir)
    images_cawl_dir = os.path.join(parent_dir, REPO_NAME)
    symlink_path = os.path.join(azt_dir, "images", SYMLINK_NAME)
    return azt_dir, images_cawl_dir, symlink_path

def clone_or_update():
    """Clone images_CAWL if absent, or pull if present. Then ensure symlink."""
    azt_dir, images_cawl_dir, symlink_path = get_paths()

    if os.path.isdir(os.path.join(images_cawl_dir, ".git")):
        print(f"Updating {images_cawl_dir} ...")
        subprocess.check_call(["git", "-C", images_cawl_dir, "pull"])
    else:
        print(f"Cloning {REPO_URL} into {images_cawl_dir} ...")
        subprocess.check_call(["git", "clone", REPO_URL, images_cawl_dir])

    ensure_symlink(images_cawl_dir, symlink_path)
    print("Done.")

def ensure_symlink(images_cawl_dir, symlink_path):
    """Create or fix the images/toselect symlink."""
    # Compute the relative path from images/ to images_CAWL
    link_parent = os.path.dirname(symlink_path)
    rel_target = os.path.relpath(images_cawl_dir, link_parent)

    if os.path.islink(symlink_path):
        current = os.readlink(symlink_path)
        if current == rel_target:
            return
        print(f"Fixing symlink (was {current}, now {rel_target})")
        os.remove(symlink_path)
    elif os.path.isdir(symlink_path):
        print(f"Warning: {symlink_path} is a real directory, not a symlink.")
        print("Move or remove it manually, then re-run this script.")
        sys.exit(1)
    elif os.path.exists(symlink_path):
        os.remove(symlink_path)

    os.symlink(rel_target, symlink_path)
    print(f"Symlinked {symlink_path} -> {rel_target}")

def ensure_available():
    """Check that images/toselect exists; clone the repo if it doesn't.

    Call this before accessing images/toselect from application code.
    Returns True if images are available, False if clone failed.
    """
    _azt_dir, images_cawl_dir, symlink_path = get_paths()
    # If the symlink (or directory) exists and has content, nothing to do
    if os.path.isdir(symlink_path):
        return True
    # Try to clone/link
    try:
        clone_or_update()
        return True
    except Exception as e:
        print(f"Warning: could not set up CAWL images: {e}")
        return False

if __name__ == "__main__":
    clone_or_update()
