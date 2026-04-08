# coding=UTF-8
"""CAWL (Comparative African Wordlist) loading utility, moved from main.py."""
import logging
from utilities import file
from utilities.i18n import _
from io_put import lift
# from utilities.error_handler import notify_error as ErrorNotice

log = logging.getLogger(__name__)

def loadCAWL():
    stockCAWL=file.pathname_from_base_dir('lift_templates/SILCAWL/SILCAWL.lift')
    if not file.exists(stockCAWL):
        from lift_templates.SILCAWL_update import ensure_available
        ensure_available()
    if file.exists(stockCAWL):
        log.info(_("Found stock LIFT file: {file}").format(file=stockCAWL))
    try:
        cawldb=lift.LiftXML(str(stockCAWL),tostrip=True) # Don't load everything
        log.info(_("Parsed ET."))
        log.info(_("Got ET Root."))
    except lift.BadParseError as e:
        text=_("{file} doesn't look like a well formed lift file; please "
                "try again. ({error})").format(file=stockCAWL,error=e)
        return text
    except Exception as e:
        log.info(_("Error: {error}").format(error=e))
    log.info(_("Parsed stock LIFT file to tree/nodes."))
    return cawldb
