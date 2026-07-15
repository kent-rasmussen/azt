"""Clone/update the images_CAWL repository and point images/toselect at it.

Thin wrapper over utilities/sister_repos.py — the one principled mechanism
for all sister repos (azt-collab, images_CAWL, lift_templates). Kept for
standalone use and for callers that import ensure_available().

Usage:
    python images/to_select_update.py          # from the azt directory
    python -m images.to_select_update          # as a module
"""
import os
import sys

# standalone execution: make the azt root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utilities import sister_repos

REPO_NAME = "images_CAWL"


def ensure_available():
    """Clone/link if needed; True when images/toselect is usable.
    Never raises; call freely from application code."""
    return sister_repos.ensure(REPO_NAME)


def clone_or_update():
    """git pull an existing clone (or clone afresh), then ensure the link."""
    return sister_repos.update(REPO_NAME)


if __name__ == "__main__":
    clone_or_update()
