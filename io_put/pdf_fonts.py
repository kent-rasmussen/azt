#!/usr/bin/env python3
# coding=UTF-8
"""Shared PDF font registration for ReportLab-based PDF generation."""
import os
import platform
from utilities import logsetup

log = logsetup.getlog(__name__)

try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    from reportlab.rl_config import TTFSearchPath
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    log.warning("ReportLab not installed. PDF generation will not work.")

if REPORTLAB_AVAILABLE:
    if platform.system() == 'Windows':
        for path in [r'C:\Windows\Fonts',
                    r''.join([r'C:\Users\\',
                            str(os.getlogin()),
                            r'\AppData\Local\Microsoft\Windows\Fonts'
                            ])
                    ]:
            TTFSearchPath.append(path)
    # enable font subdirectories:
    for i in list(TTFSearchPath):
        TTFSearchPath.append(i+'/*')


def register_fonts():
    """Registers Charis SIL and Andika font families if available."""
    if not REPORTLAB_AVAILABLE:
        return False
    try:
        # Check if already registered to avoid re-registering
        for filename in ['CharisSIL', 'Charis']:
            try:
                pdfmetrics.getFont('Charis-Regular')
                break
            except:
                pass
            try:
                pdfmetrics.registerFont(TTFont('Charis-Regular', f'{filename}-Regular.ttf'))
                pdfmetrics.registerFont(TTFont('Charis-Bold', f'{filename}-Bold.ttf'))
                pdfmetrics.registerFont(TTFont('Charis-Italic', f'{filename}-Italic.ttf'))
                pdfmetrics.registerFont(TTFont('Charis-BoldItalic', f'{filename}-BoldItalic.ttf'))
                registerFontFamily('Charis',
                            normal='Charis-Regular',
                            bold='Charis-Bold',
                            italic='Charis-Italic',
                            boldItalic='Charis-BoldItalic')
                break
            except Exception as e:
                log.warning(f"Could not register Charis fonts with '{filename}': {e}")

        pdfmetrics.registerFont(TTFont('Andika-Regular', 'Andika-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Andika-Bold', 'Andika-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Andika-Italic', 'Andika-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('Andika-BoldItalic', 'Andika-BoldItalic.ttf'))
        registerFontFamily('Andika',
                            normal='Andika-Regular',
                            bold='Andika-Bold',
                            italic='Andika-Italic',
                            boldItalic='Andika-BoldItalic')
        return True
    except Exception as e:
        log.warning(f"Could not register fonts: {e}")
        return False
