# Translation ReadMe
<!-- Two spaces at the end of a line gives a linebreak, but three ticks (```) -->
<!-- gives better overall format, with shading -->
Because of the way we are doing translations (within the constraints of
Python), there are a couple things we should all pay attention to:


- The *best practice* is to put a semantically helpful keyword for each variable, like this:  

      ```
      _("{name} Dictionary and Orthography Checker").format(name=self.program['name'])
      ```
  - One Reason this is best practice is that f-strings are not supported in the current version of xgettext. So while the following would be otherwise preferred:
      ```
      _(f"{n} senses found") <= xgettext should extract this, but not translate it
      _(f"Running {program['name']}") <==xgettext will neither extract nor translate strings with subexpressions>
      ```
      this would not be translated.  So even in these simple cases, the extra redundancy allows for both meaningful strings and translation:
      ```
      _("{n} senses found").format(n=n)
      _("Running {azt}").format(azt=program['name'])
      ```
- Otherwise, there doesn't seem to be any way to bring the format items into the translation, so we'd be stuck hopefully understanding more or less what each `{}` means.

- There doesn't seem to be any difference on the use of `_("").format()` syntax or `_("".format())` syntax

- The following formats work (i.e., we have some liberty, but let's keep things clear for the translators with meaningful keywords, as above):
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

## Under the Hood Process

*After marking new strings for translation, or whenever untranslated strings are noticed in the UI (or after any extensive coding)*:
- run _extract.py_ to pull strings from the code for translation. This will update the _azt.pot_ file. If there are no updates, you can stop here.
    - check and resolve errors, re-run as necessary.
- commit and push to github, which will trigger _upload-strings.yml_, pushing the new _azt.pot_ (and locally corrected translations?) to Crowdin.
- in Crowdin, run pre-translation with machine translation, just to have something.

*After new translations are approved in Crowdin*:
- trigger _download-translations.yml_ manually (from github.com), which will pull the new .po files from Crowdin, and create a pull request.
- evaluate and approve the pull request 
- pull the updated repo to local machine.
- run _compile.py_ to compile the .po files into .mo files.
    - check and resolve errors, re-run as necessary.
- commit and push the updated .mo files to github.

update-translations.yml is no longer used, though may be useful for future automation on GitHub.