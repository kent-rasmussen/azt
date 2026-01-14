#!/usr/bin/env python3
# coding=UTF-8
import os
import random
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.rl_config import TTFSearchPath
from reportlab.lib import colors

log = logging.getLogger(__name__)

# Re-use font registration logic from alphabet_chart_pdf.py
try:
    for i in list(TTFSearchPath):
        TTFSearchPath.append(i+'/*')
except:
    pass

def register_fonts():
    """Registers the specified font family if available."""
    try:
        # Check if already registered to avoid errors or re-registering
        try:
            pdfmetrics.getFont('Charis-Regular')
            return True
        except:
            pass

        pdfmetrics.registerFont(TTFont('Charis-Regular', 'CharisSIL-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Charis-Bold', 'CharisSIL-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Charis-Italic', 'CharisSIL-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('Charis-BoldItalic', 'CharisSIL-BoldItalic.ttf'))
        registerFontFamily('Charis',
                            normal='Charis-Regular',
                            bold='Charis-Bold',
                            italic='Charis-Italic',
                            boldItalic='Charis-BoldItalic')
        
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

def draw_triangular_examples(c, x, y, width, height, items, font_name, font_size):
    """
    Draws 3 items in a triangular layout:
      [Img1]   [Img2]
          [Img3]
    """
    if len(items) != 3:
        log.warning(f"Expected 3 items for triangular layout, got {len(items)}")
        # Handle other counts gracefully if needed, but for now specific to requirements
    
    # Grid calculation
    # Row 1: 2 items
    # Row 2: 1 item (centered)
    
    # Divide height roughly equally between the two rows
    row_height = height / 2.0
    
    # We want 2 cols in top row.
    col_width = width / 2.0
    
    # Margins/Padding
    padding = 5
    
    # Helper to draw one item (Image + Word)
    def draw_item(ix, iy, w, h, item):
        glyph, word, image_path = item
        
        # Calculate text height
        c.setFont(f"{font_name}-Regular", font_size)
        text_w = c.stringWidth(word, f"{font_name}-Regular", font_size)
        text_h = font_size * 1.2 # Approx line height
        
        # Image area
        img_avail_h = h - text_h - padding
        img_avail_w = w - (padding * 2)
        
        # Draw Image
        if image_path and os.path.exists(image_path) and img_avail_h > 0:
            try:
                img = ImageReader(image_path)
                iw, ih = img.getSize()
                aspect = ih / float(iw)
                
                disp_w = img_avail_w
                disp_h = disp_w * aspect
                
                if disp_h > img_avail_h:
                    disp_h = img_avail_h
                    disp_w = disp_h / aspect
                
                # Center image in available space
                img_x = ix + (w - disp_w) / 2
                # Align to bottom of image area
                img_y = iy + text_h + padding + (img_avail_h - disp_h) / 2
                
                c.drawImage(img, img_x, img_y, width=disp_w, height=disp_h, mask='auto', preserveAspectRatio=True)
            except Exception as e:
                log.error(f"Error drawing image {image_path}: {e}")
        
        # Draw Word (Centered at bottom)
        c.drawString(ix + (w - text_w) / 2, iy + (padding/2), word)

    # Item 1 (Top-Left)
    if len(items) > 0:
        draw_item(x, y + row_height, col_width, row_height, items[0])
        
    # Item 2 (Top-Right)
    if len(items) > 1:
        draw_item(x + col_width, y + row_height, col_width, row_height, items[1])
        
    # Item 3 (Bottom-Center)
    if len(items) > 2:
        # Center horizontally: x + width/4
        # Width same as others? Or slightly larger? Let's keep it consistent.
        # But we want it visually centered.
        # It's in the second row (bottom half of available area)
        center_x = x + (width - col_width) / 2
        draw_item(center_x, y, col_width, row_height, items[2])

def generate_prose_text(words, count):
    """Generates a randomized prose string from the words."""
    if not words:
        return ""
    
    # Create list of words repeated count times
    all_words = []
    for w in words:
        all_words.extend([w] * count)
    
    random.shuffle(all_words)
    return " ".join(all_words)

def add_comparative_data(data):
    for i in range(0, len(data), 2):
        data[i]['comparative'] = False
        data[i+1]['comparative'] = data[i]
    return data
def create_comparison_chart(filename, *data, 
                          pagesize='letter', font_name="Charis", 
                          prose_count=20, title="Comparison"):
    """
    Args:
        filename: Output path
        left_data: dict with 'symbol', 'items' [(glyph, word, img)...]
        right_data: dict with 'symbol', 'items' [(glyph, word, img)...]
        pagesize: 'A4' or 'letter'
        font_name: Font family
        prose_count: Number of times each word appears in prose
    """
    log.info(f"Creating comparison chart called with {data=} {filename=}")
    font_size = 12
    register_fonts()
    
    if pagesize.lower() == 'a4':
        _pagesize = landscape(A4)
    else:
        _pagesize = landscape(letter) # default
        
    # Create Canvas
    c = canvas.Canvas(str(filename), pagesize=_pagesize)
    width, height = _pagesize
    c.setAuthor(f"A−Z+T via {__file__}")
    c.setTitle(' '.join(str(filename.stem).split('_')))

    # Global Margins
    margin = 0.5 * inch
    
    # Split width
    half_width = width / 2.0
    
    # Draw central dividing line (optional, maybe just space?)
    # Users usually fold these, so a light line helps.
    c.setStrokeColor(colors.lightgrey)
    c.line(half_width, 0, half_width, height)
    c.setStrokeColor(colors.black)
    
    # Helper to draw one side
    def draw_side(base_x, data, prev_data=None):
        if not data:
            return # Blank page
            
        symbol = data.get('symbol', '?')
        items = data.get('items', [])
        
        # Safe extraction of words for prose (from tuple)
        words = [item[1] for item in items if len(item) > 1]
        
        # --- Layout Areas ---
        # Top-Half: Images
        # Bottom-Half: Prose
        # Header: Symbol
        
        content_width = half_width - (margin * 2)
        content_left = base_x + margin
        
        # 1. Symbol Header
        header_y = height - margin - 40
        c.setFont(f"{font_name}-Bold", 72)
        c.drawCentredString(base_x + half_width/2, header_y, symbol)
        
        # 2. Top Half (Examples)
        # Allocate space from below header to middle of page
        mid_page_y = height / 2.0
        examples_top = header_y - 20 # Spacing
        examples_height = examples_top - mid_page_y
        
        draw_triangular_examples(c, content_left, mid_page_y, content_width, examples_height, 
                               items, font_name, font_size)
        
        # 3. Bottom Half (Prose)
        # Allocate space from mid page to bottom margin
        prose_top = mid_page_y - 30 # Spacing
        prose_bottom = margin
        prose_width = content_width
        
        prose_text = generate_prose_text(words, prose_count)
        
        text_obj = c.beginText(content_left, prose_top)
        text_obj.setFont(f"{font_name}-Regular", font_size)
        text_obj.setTextOrigin(content_left, prose_top)
        
        # Simple word wrap
        from reportlab.lib.utils import simpleSplit
        lines = simpleSplit(prose_text, f"{font_name}-Regular", font_size, prose_width)
        
        for line in lines:
            if text_obj.getY() < prose_bottom:
                break # Stop if overflowing
            text_obj.textLine(line)
            
        c.drawText(text_obj)
        if prev_data: #put both on second page
            both_words = [item[1] for item 
                        in prev_data.get('items', [])+data.get('items', []) 
                        if len(item) > 1]
            prose_text = generate_prose_text(both_words, prose_count)
            prose_top = text_obj.getY() - font_size*3/2
            text_obj = c.beginText(content_left, prose_top)
            text_obj.setFont(f"{font_name}-Regular", font_size)
            text_obj.setTextOrigin(content_left, prose_top)
        
            # Simple word wrap
            lines = simpleSplit(prose_text, f"{font_name}-Regular", 12, prose_width)
            
            for line in lines:
                if text_obj.getY() < prose_bottom:
                    break # Stop if overflowing
                text_obj.textLine(line)
                
            c.drawText(text_obj)
    data = add_comparative_data(data)
    # Re-order for booklet signature
    data = make_signatures(data)
    # Draw Left Side
    for n,page_data in enumerate(data):
        if not n%2:
            start_at=prev_data=0
        else:
            start_at=half_width
            prev_data=data[n-1]
        draw_side(start_at, page_data, prev_data)
        if n%2:
            c.showPage()
    c.save()
    log.info(f"Comparison chart saved to {filename}")

def make_signatures(pages):
    """
    Reorders a list of pages for a single saddle-stitch booklet.
    Input: [1, 2, 3, 4, 5, 6, 7, 8] (8 pages, 2 sheets)
    
    Sheet 1 Front: [8, 1]
    Sheet 1 Back:  [2, 7]
    Sheet 2 Front: [6, 3]
    Sheet 2 Back:  [4, 5]
    
    Output: [8, 1, 2, 7, 6, 3, 4, 5]
    """
    pages = list(pages)
    
    # 1. Pad to multiple of 4
    n = len(pages)
    rem = n % 4
    if rem > 0:
        pages.extend([None] * (4 - rem))
    
    n = len(pages)
    reordered = []
    
    # Use 0-based indexing pointers
    p_start = 0
    p_end = n - 1
    
    while p_start < p_end:
        # Sheet Side A (Front): First and Last remaining
        # Left side of page is Last (p_end), Right side is First (p_start)
        reordered.append(pages[p_end])
        reordered.append(pages[p_start])
        
        p_start += 1
        p_end -= 1
        
        # Sheet Side B (Back): Next First and Next Last
        # Left side of page is Next First (p_start), Right side is Next Last (p_end)
        if p_start >= p_end:
            break
            
        reordered.append(pages[p_start])
        reordered.append(pages[p_end])
        
        p_start += 1
        p_end -= 1
        
    return reordered

if __name__ == "__main__":
    # Basic test
    logging.basicConfig(level=logging.INFO)
    l_data = {
        'symbol': 'b',
        'items': [
            ('b', 'ball', 'images/ball.png'), # Dummy paths
            ('b', 'bat', 'images/bat.png'),
            ('b', 'boy', 'images/boy.png'),
        ]
    }
    r_data = {
        'symbol': 'd',
        'items': [
            ('d', 'dog', 'images/dog.png'),
            ('d', 'doll', 'images/doll.png'),
            ('d', 'door', 'images/door.png'),
        ]
    }
    create_comparison_chart("test_comp.pdf", l_data, r_data)
