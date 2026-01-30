#!/usr/bin/env python3
# coding=UTF-8
import os
import logsetup
import glob
import platform
log = logsetup.getlog(__name__)
logsetup.setlevel('INFO')
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, letter, landscape
    from reportlab.lib.units import inch, cm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    from reportlab.rl_config import TTFSearchPath
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    log.warning("ReportLab not installed. PDF generation will not work.")

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
# log.info(f"Looking for fonts in {TTFSearchPath}")
# for f in TTFSearchPath:
#     log.info(f"in {f} found {glob.glob(f)}")
def register_fonts():
    """Registers the specified font family if available."""
    if not REPORTLAB_AVAILABLE:
        return False
    
    try:
        for filename in ['CharisSIL','Charis']:
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
            except Exception as e:
                log.warning(f"Could not register Charis fonts: {e}")
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

def create_chart(filename, items, title, num_columns=5, pagesize='A4', 
                font_name="Helvetica", padding=5, spacing=5,
                one_page=False, copyright_text=None, made_with=None,analang=None):
    """
    Generate a PDF alphabet chart.
    
    Args:
        filename (str): Output PDF filename.
        items (list): List of tuples (glyph, word, image_path).
        title (str): Chart title.
        num_columns (int): Number of columns in the grid.
        pagesize (tuple): Page size (default A4).
        font_name (str): Font family to use (Helvetica, Charis SIL, Andika).
        padding (float): Padding inside the cell (points).
        spacing (float): Spacing between elements (points).
        copyright_text (str): Text for bottom left.
        made_with (str): Text for bottom right.
    """
    if not REPORTLAB_AVAILABLE:
        log.error("Cannot generate PDF: ReportLab is not installed.")
        return

    # Try to register the requested font
    if register_fonts():
        title_font = f"{font_name}-Bold"
        text_font = f"{font_name}-Regular"
        glyph_font = f"{font_name}-Bold"
        using_helvetica=False
    else:
        using_helvetica=True
        log.error("Problem loading fonts (is Charis installed?)")
        # log.warning(f"Could not register fonts: {e}")
        log.warning("Proceeding with Helvetica")
        title_font = "Helvetica-Bold"
        text_font = "Helvetica"
        glyph_font = "Helvetica-Bold"
        # raise
    
    if pagesize.lower() in ['a4','european','default']:
        _pagesize=A4
    elif pagesize.lower() in ['letter','us']:
        _pagesize=letter
    if len(items)/num_columns < num_columns:
        _pagesize=landscape(_pagesize)
    c = canvas.Canvas(str(filename), pagesize=_pagesize)
    width, height = _pagesize
    
    # Margins
    margin_x = 0.5 * inch
    margin_y = 0.5 * inch
    
        

    # Title
    c.setFont(title_font, 24)
    c.drawCentredString(width / 2, height - margin_y - 20, title)
    
    # Footer Helper
    def draw_footer():
        footer_y = margin_y / 2
        c.setFont(text_font, 10)
        
        if copyright_text:
            c.drawString(margin_x, footer_y, f'© {copyright_text}')
        
        if analang:
            analang_width = c.stringWidth(analang, text_font, 10)
            c.drawCentredString(width / 2, footer_y, f"[{analang}]")

        if made_with:
            mw_width = c.stringWidth(made_with, text_font, 10)
            c.drawString(width - margin_x - mw_width, footer_y, made_with)

    # Grid calculations
    grid_top = height - margin_y - 60
    grid_bottom = margin_y
    grid_width = width - 2 * margin_x
    grid_height = grid_top - grid_bottom
    
    col_width = grid_width / num_columns
    
    # Font Metrics
    glyph_font_size = 36
    word_font_size = 14
    
    # Get font metrics
    try:
        f = pdfmetrics.getFont(text_font)
        ascent = f.face.ascent
        descent = f.face.descent
    except KeyError:
        # Fallback if font not found (shouldn't happen if registered, but safe)
        f = pdfmetrics.getFont("Helvetica")
        ascent = 1000
        descent = -200

    # Calculate heights in points
    glyph_ascent = (ascent / 1000.0) * glyph_font_size
    glyph_descent = (descent / 1000.0) * glyph_font_size
    glyph_height = glyph_ascent - glyph_descent # descent is negative

    word_ascent = (ascent / 1000.0) * word_font_size
    word_descent = (descent / 1000.0) * word_font_size
    word_height = word_ascent - word_descent

    # Calculate Row Height
    # We need space for: Padding + Glyph + Spacing + Image + Spacing + Word + Padding
    # Let's ensure image has at least some reasonable space, e.g., half of column width
    min_image_height = col_width * 0.6
    
    required_height = (padding * 2) + glyph_height + (spacing * 2) + min_image_height + word_height
    
    # Initial row height based on column width (aspect ratio)
    row_height = col_width * 1.5
    
    # Adjust if required height is larger
    row_height = max(row_height, required_height)
    
    # num_rows = (len(items) + num_columns - 1) // num_columns
    
    current_x = margin_x
    current_y = grid_top - row_height
    
    log.info(f"Metrics: {ascent=} {descent=} {glyph_height=} {word_height=} {row_height=}")

    for i, (glyph, word, image_path) in enumerate(items):
        # Check if we need a new page
        if current_y < grid_bottom:
            if one_page:
                return create_chart(filename, items, title, 
                            num_columns=num_columns+1,
                            pagesize=pagesize,
                            font_name=font_name,
                            padding=padding,
                            spacing=spacing,
                            one_page=True,
                            copyright_text=copyright_text,
                            made_with=made_with,
                            analang=analang)
            
            draw_footer() # Footer on current page
            c.showPage()
            current_y = grid_top - row_height
            current_x = margin_x
            # Redraw title on new page? Maybe not.
        
        # Cell Boundaries
        cell_top = current_y + row_height
        cell_bottom = current_y
        
        # Draw Cell Border (Optional, for debugging)
        # c.rect(current_x, current_y, col_width, row_height)
        
        # Calculate Y positions
        
        # Glyph: Top aligned
        # Baseline = Top - Padding - Ascent
        glyph_baseline_y = cell_top - padding - glyph_ascent
        
        # Word: Bottom aligned
        # Baseline = Bottom + Padding - Descent (since descent is negative, -descent is positive)
        word_baseline_y = cell_bottom + padding - word_descent
        
        # Image Area
        # Top = Glyph Baseline + Descent - Spacing
        image_area_top = glyph_baseline_y + glyph_descent - spacing
        # Bottom = Word Baseline + Ascent + Spacing
        image_area_bottom = word_baseline_y + word_ascent + spacing
        
        avail_img_height = image_area_top - image_area_bottom
        avail_img_width = col_width - (padding * 2)
        
        # Glyph
        c.setFont(glyph_font, glyph_font_size)
        glyph_width = c.stringWidth(glyph, glyph_font, glyph_font_size)
        c.drawString(current_x + (col_width - glyph_width) / 2, glyph_baseline_y, glyph)
        
        # Word
        c.setFont(text_font, word_font_size)
        if word:
            word_width = c.stringWidth(word, text_font, word_font_size)
            c.drawString(current_x + (col_width - word_width) / 2, word_baseline_y, word)
        
        # Image
        if image_path and os.path.exists(image_path) and avail_img_height > 0:
            try:
                img = ImageReader(image_path)
                img_width, img_height = img.getSize()
                aspect = img_height / float(img_width)
                
                # Scale to fit
                display_width = avail_img_width
                display_height = avail_img_width * aspect
                
                if display_height > avail_img_height:
                    display_height = avail_img_height
                    display_width = avail_img_height / aspect
                
                # Center image
                img_x = current_x + (col_width - display_width) / 2
                img_y = image_area_bottom + (avail_img_height - display_height) / 2
                
                c.drawImage(img, img_x, img_y, width=display_width, height=display_height, mask='auto', preserveAspectRatio=True)
            except Exception as e:
                log.error(f"Error drawing image {image_path}: {e}")
        
        # Move to next cell
        current_x += col_width
        if (i + 1) % num_columns == 0:
            current_x = margin_x
            current_y -= row_height
            
    draw_footer() # Footer on last page
    c.save()
    log.info(f"PDF saved to {filename}")
    if using_helvetica:
        return "using_helvetica"
    return num_columns