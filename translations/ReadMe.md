# Translation ReadMe
Because of the way we are doing translations (within the constraints of
Python), there are a couple things we should all pay attention to:

- The following formats work:
    - `_("Language with code [{}]").format(xyz)`
        - format()ed string on one line
    - `_("{} doesn't look like a well formed lift file; please "`\n
      `"try again.").format(filename)`
        - format()ed strings, with format on line after reference
    - `_("Your regular expressions look OK for {0} (there are "\n
                "no segments in your {0} data that are not in a regex). "
                "Note, this doesn't \nsay anything about digraphs or "
                "complex segments which should be counted as a single "
                "segment --those may not be covered by \n"
                "your regexes.".format(lang))`
        - format()ed strings with multiple references to the same format item, given at the end
