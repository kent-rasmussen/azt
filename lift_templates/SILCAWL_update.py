"""Clone or update the lift_templates repository and ensure SILCAWL is symlinked.

This script places lift_templates as a sibling of the azt project directory,
wherever azt happens to be installed, and symlinks lift_templates/SILCAWL to it.

Usage:
    python lift_templates/SILCAWL_update.py          # from the azt directory
"""
import os
import subprocess
import sys

REPO_URL = "https://github.com/kent-rasmussen/lift_templates.git"
REPO_NAME = "lift_templates"
SYMLINK_NAME = "SILCAWL"

def get_paths():
    """Return (azt_dir, lift_templates_dir, symlink_path)."""
    # The azt project root is the parent of the lift_templates/ directory
    azt_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_dir = os.path.dirname(azt_dir)
    lift_templates_dir = os.path.join(parent_dir, REPO_NAME)
    symlink_path = os.path.join(azt_dir, "lift_templates", SYMLINK_NAME)
    return azt_dir, lift_templates_dir, symlink_path

def clone_or_update():
    """Clone lift_templates if absent, or pull if present. Then ensure symlink."""
    azt_dir, lift_templates_dir, symlink_path = get_paths()

    if os.path.isdir(os.path.join(lift_templates_dir, ".git")):
        print(f"Updating {lift_templates_dir} ...")
        subprocess.check_call(["git", "-C", lift_templates_dir, "pull"])
    else:
        print(f"Cloning {REPO_URL} into {lift_templates_dir} ...")
        subprocess.check_call(["git", "clone", REPO_URL, lift_templates_dir])

    ensure_symlink(lift_templates_dir, symlink_path)
    print("Done.")

def ensure_symlink(lift_templates_dir, symlink_path):
    """Create or fix the SILCAWL symlink."""
    link_parent = os.path.dirname(symlink_path)
    rel_target = os.path.relpath(lift_templates_dir, link_parent)

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
    """Check that SILCAWL exists; clone the repo if it doesn't.

    Call this before accessing lift_templates/SILCAWL/ from application code.
    Returns True if files are available, False if clone failed.
    """
    _azt_dir, lift_templates_dir, symlink_path = get_paths()
    if os.path.isdir(symlink_path):
        return True
    try:
        clone_or_update()
        return True
    except Exception as e:
        print(f"Warning: could not set up lift_templates: {e}")
        return False

if __name__ == "__main__":
    clone_or_update()
