"""Every global name a function reads must exist in its module.

`logfinished` was called by the tone report and the status refresh, and
defined nowhere: a finished tone report died at its last line with
"name 'logfinished' is not defined" (Kent's run, 2026-10-14). Star imports
hide this from a linter, so check the IMPORTED module: `symtable` says which
names each function reads as globals (not locals, not closure variables),
and the module, after its imports ran, must hold every one, or builtins.
"""
import builtins
import importlib
import symtable

import pytest

MODULES = [
    'backend.reporting.generator',
    'backend.core.report_mixins',
    'backend.core.analysis',
    'backend.core.lexicon',
    'backend.core.categories',
    'backend.core.sorting_engine',
    'backend.core.alphabet',
    'backend.core.profiles',
    'backend.core.analysis_inputs',
    'backend.core.vcs',
    'io_put.xlp',
    'io_put.lift',
    'tasks.tasks',
    'settings',
]

# (function, name) pairs known to read an undefined global, with the reason
# each is tolerated. Keep this short; each entry is a debt (delete the dead
# code, or fix it, and drop the entry).
SCRIPT = "only in lift.py's __main__ block, where the script defines it"
ALLOWED = {
    'io_put.lift': {
        ('report', 'filenames'): SCRIPT,
        ('report', 'lifts'): SCRIPT,
        ('writetofile', 'lift'): SCRIPT,
        ('revert_stuff', 'lift'): SCRIPT,
        ('__init__', 'lift'): "class Language: no callers anywhere",
    },
    'backend.core.alphabet': {
        ('update_symbols', 'cv'): "no callers; docstring: 'rethink entirely'",
        ('update_symbols', 'items'): "no callers; docstring: 'rethink entirely'",
    },
    'tasks.tasks': {
        ('addtonefieldpron', 'check'): "no callers; marked unused",
    },
}


def _global_reads(table, out):
    if table.get_type() == 'function':
        for sym in table.get_symbols():
            if sym.is_referenced() and sym.is_global() \
                    and not sym.is_assigned():
                out.add((table.get_name(), table.get_lineno(),
                         sym.get_name()))
    for child in table.get_children():
        _global_reads(child, out)
    return out


@pytest.mark.parametrize('modname', MODULES)
def test_every_global_a_function_reads_is_defined(modname):
    try:
        mod = importlib.import_module(modname)
    except ImportError as e:
        pytest.skip(f'{modname} does not import here: {e}')
    path = mod.__file__
    with open(path, encoding='utf-8') as f:
        source = f.read()
    reads = _global_reads(symtable.symtable(source, path, 'exec'), set())
    known = set(vars(mod)) | set(dir(builtins))
    allowed = ALLOWED.get(modname, {})
    missing = sorted((line, fn, name) for fn, line, name in reads
                     if name not in known and (fn, name) not in allowed)
    assert not missing, '\n'.join(
        f'{path}:{line} {fn}() reads undefined global {name!r}'
        for line, fn, name in missing)
