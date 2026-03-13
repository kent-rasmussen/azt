# SILCAWL LIFT Template

The `lift_templates/SILCAWL/` folder contains the SIL Comparative African Word
List (SILCAWL) as a LIFT file. It is maintained in a separate repository so it
can be shared across projects.

## Quick setup

From the azt project directory, run:

```bash
python lift_templates/SILCAWL_update.py
```

This will:
1. Clone `lift_templates` as a sibling of your azt directory (e.g. if azt is at
   `~/bin/raspy/azt`, the templates go to `~/bin/raspy/lift_templates`).
2. Create a symlink at `lift_templates/SILCAWL` pointing to that clone.

If the repository is already cloned, the same command pulls the latest changes.

## Manual setup

```bash
# From the parent of your azt directory:
cd /path/to/parent
git clone https://github.com/kent-rasmussen/lift_templates.git

# Then create the symlink inside azt:
cd azt/lift_templates
ln -s ../../lift_templates SILCAWL
```

## Using in other projects

Clone `lift_templates` alongside your project and symlink or reference it as
needed. The repository contains `SILCAWL.lift` and its accompanying `README.md`.
