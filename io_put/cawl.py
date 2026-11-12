# coding=UTF-8
"""CAWL (Comparative African Wordlist) loading utility, moved from main.py."""
from utilities import file, logsetup
from utilities.i18n import _
from io_put import lift

log = logsetup.getlog(__name__)
logsetup.setlevel('INFO', log)

def loadCAWL():
    stockCAWL=file.pathname_from_base_dir('lift_templates/SILCAWL/SILCAWL.lift')
    if not file.exists(stockCAWL):
        from lift_templates.SILCAWL_update import ensure_available
        ensure_available()
    if file.exists(stockCAWL):
        log.info(_("Found stock LIFT file: {file}").format(file=stockCAWL))
    try:
        cawldb=lift.LiftXML(str(stockCAWL),tostrip=True) # Don't load everything
    except lift.BadParseError as e:
        text=_("{file} doesn’t look like a well formed lift file; please "
                "try again. ({error})").format(file=stockCAWL,error=e)
        return text
    except Exception as e:
        log.info(_("Error: {error}").format(error=e))
    # Both uses (a new project, and filling out an established one) take these
    # entries in as new: not with the template's 2008/2011 dates, nor its guids.
    log.info("CAWL: %d nodes' dates set to now",cawldb.stamp_dates_now())
    log.info("CAWL: %d entries/senses given new guids",cawldb.regenerate_ids())
    log.info(_("Done loading stock LIFT file, parsed to tree/nodes."))
    return cawldb
