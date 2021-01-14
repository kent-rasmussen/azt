# Translation ReadMe
<--Two spaces at the end of a line gives a linebreak, but three ticks (```)
gives better overall format, with shading-->
Because of the way we are doing translations (within the constraints of
Python), there are a couple things we should all pay attention to:

- The following formats work:
    - format()ed string on one line:

        ```
        _("Language with code [{}]").format(xyz)
        ```
    - format()ed strings, with format on line after reference

        ```
        _("{} doesn't look like a well formed lift file; please "
        "try again.").format(filename)`
        ```
    - format()ed strings with multiple references to the same format item, given at the end
        ```
        _("Your regular expressions look OK for {0} (there are "
        "no segments in your {0} data that are not in a regex). "
        "Note, this doesn't \nsay anything about digraphs or "
        "complex segments which should be counted as a single "
        "segment --those may not be covered by \n"
        "your regexes.".format(lang))`
        ```
- There doesn't seem to be any difference on the use of `_("").format()` syntax or `_("".format())` syntax
- There doesn't seem to be any way to bring the format items into the translation, so we're stuck hopefully understanding more or less what each `{}` means.
