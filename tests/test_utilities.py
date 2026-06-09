"""Unit tests for pure helpers in utilities/utilities.py.

Small, dependency-free functions that are easy to pin and are used widely
(config parsing, group flags, single-item unwrapping).
"""
from utilities.utilities import grouptype, ifone, ofromstr


def test_ofromstr_parses_list():
    assert ofromstr("[1, 2, 3]") == [1, 2, 3]


def test_ofromstr_parses_dict():
    assert ofromstr("{'a': 1}") == {"a": 1}


def test_ofromstr_parses_int():
    assert ofromstr("5") == 5


def test_ofromstr_passes_plain_string_through():
    assert ofromstr("hello") == "hello"


def test_ofromstr_passes_malformed_through_unchanged():
    # not valid Python literal -> returned as-is, not raised
    assert ofromstr("[1, 2") == "[1, 2"


def test_grouptype_defaults_all_known_flags_false():
    g = grouptype()
    for flag in ["wsorted", "tosort", "toverify", "tojoin",
                 "torecord", "comparison", "todo"]:
        assert g[flag] is False


def test_grouptype_preserves_passed_value():
    assert grouptype(tosort=True)["tosort"] is True


def test_grouptype_keeps_extra_kwargs():
    assert grouptype(custom="x")["custom"] == "x"


def test_ifone_returns_sole_element():
    assert ifone([42]) == 42


def test_ifone_returns_none_for_multiple():
    assert ifone([1, 2]) is None


def test_ifone_returns_none_for_empty():
    assert ifone([]) is None


def test_writefilename_available_without_soundfile():
    """Regression: writefilename was moved into the soundfile-gated file_sound
    module, so `file.writefilename` vanished when `soundfile` wasn't installed —
    hanging project-open. It must exist on utilities.file unconditionally.
    (Asserts existence only; calling it touches real app settings.)"""
    from utilities import file
    assert callable(getattr(file, "writefilename", None)), (
        "utilities.file.writefilename must exist even when the optional "
        "'soundfile' package is absent")
