"""Clone/update the lift_templates repository and point lift_templates/SILCAWL at it.

Thin wrapper over utilities/sister_repos.py — the one principled mechanism
for all sister repos (azt-collab, images_CAWL, lift_templates). Kept for
standalone use and for callers that import ensure_available() (io_put/cawl.py).

Usage:
    python lift_templates/SILCAWL_update.py    # from the azt directory
    python -m lift_templates.SILCAWL_update    # as a module
"""
import os
import sys

# standalone execution: make the azt root importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utilities import sister_repos

REPO_NAME = "lift_templates"


def ensure_available():
    """Clone/link if needed; True when lift_templates/SILCAWL is usable.
    Never raises; call freely from application code."""
    return sister_repos.ensure(REPO_NAME)


def clone_or_update():
    """git pull an existing clone (or clone afresh), then ensure the link."""
    return sister_repos.update(REPO_NAME)


if __name__ == "__main__":
    clone_or_update()
