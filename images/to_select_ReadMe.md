# CAWL Selection Images

The `images/toselect/` folder contains illustration images organized by CAWL
number. These images are maintained in a separate repository so they can be
shared across projects.

## Quick setup

From the azt project directory, run:

```bash
python images/to_select_update.py
```

This will:
1. Clone `images_CAWL` as a sibling of your azt directory (e.g. if azt is at
   `~/bin/raspy/azt`, the images go to `~/bin/raspy/images_CAWL`).
2. Create a symlink at `images/toselect` pointing to that clone.

If the repository is already cloned, the same command pulls the latest changes.

## Manual setup

```bash
# From the parent of your azt directory:
cd /path/to/parent
git clone https://github.com/kent-rasmussen/images_CAWL.git

# Then create the symlink inside azt:
cd azt/images
ln -s ../../images_CAWL toselect
```

## Using in other projects

Clone `images_CAWL` alongside your project and symlink or reference it as
needed. The repository contains only image folders named by CAWL number
(e.g. `0001_body/`, `0002_skin_of_man/`).
