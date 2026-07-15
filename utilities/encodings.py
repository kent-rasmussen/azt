#!/usr/bin/env python3
# coding=UTF-8
import sys
from utilities.i18n import _
def stouttostr(x):
    # This fn is necessary (and problematic) because not all computers seem to
    # reply to subprocess.check_output with the same kind of data. I have even
    # seen a computer say it was using unicode, but not return unicode
    # data (I think because it was replacing translated text, but didn't
    # replace the same encoding). Another dumb thing that I need to account for.
    if type(x) is str:
        return x.strip()
    if not sys.stdout.encoding:
        return 'ENCODING_ERROR: '+_("I can’t tell the terminal’s encoding, sorry!")
    else:
        try:
            return x.decode(sys.stdout.encoding,
                            errors='backslashreplace').strip()
        except Exception as e:
            #if the computer doesn't know what encoding it is actually using,
            # this should give us some info to debug.
            return 'ENCODING_ERROR: '+_("Can’t decode {this} (in {encoding}; {error}):"
                        ).format(this=x,
                                encoding=sys.stdout.encoding, 
                                error=e)
    return x #not sure if this is a good idea, but this should probably raise...
