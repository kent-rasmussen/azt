# Translation ReadMe
Because of the way we are doing translations (within the constraints of
Python), there are a couple things we should all pay attention to:

- The following formats work:
    - `_("{} doesn't look like a well formed lift file; please "
                  "try again.").format(filename)`
    - `_("Language with code [{}]").format(xyz)`
    - `_("Your regular expressions look OK for {0} (there are "
                "no segments in your {0} data that are not in a regex). "
                "Note, this doesn't \nsay anything about digraphs or "
                "complex segments which should be counted as a single "
                "segment --those may not be covered by \n"
                "your regexes.".format(lang))`
