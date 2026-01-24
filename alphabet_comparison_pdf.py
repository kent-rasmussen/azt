#!/usr/bin/env python3
# coding=UTF-8
import os
import random
import logging
import platform
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, letter, landscape
    from reportlab.lib.units import inch, cm
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    from reportlab.rl_config import TTFSearchPath
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.getLogger(__name__).warning("ReportLab not installed. PDF generation will not work.")

log = logging.getLogger(__name__)

# Re-use font registration logic from alphabet_chart_pdf.py
if platform.system() == 'Windows':
    for path in [r'C:\Windows\Fonts',
            r''.join([r'C:\Users\\',
                    str(os.getlogin()),
                    r'\AppData\Local\Microsoft\Windows\Fonts'
                    ])
            ]:
        TTFSearchPath.append(path)
for i in list(TTFSearchPath):
    TTFSearchPath.append(i+'/*')
# log.info(f"Looking for fonts in {TTFSearchPath}")
# for f in TTFSearchPath:
#     log.info(f"in {f} found {glob.glob(f)}")

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
    # This logic assumes simple pairing, but we are injecting Cover/Imprint now.
    # We should only apply comparative logic to content pages.
    # Content pages are those without a special type.
    
    # Find indices of content pages
    content_indices = [i for i, d in enumerate(data) if d.get('type') == 'content']
    
    for k in range(0, len(content_indices), 2):
        if k+1 < len(content_indices):
            idx1 = content_indices[k]
            idx2 = content_indices[k+1]
            data[idx1]['comparative'] = False
            data[idx2]['comparative'] = data[idx1] 
    return data

def draw_svg(canvas, path, x, y, width=None, height=None, center=False):
    """
    Draws an SVG file onto the canvas.
    Requires svglib.
    """
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPDF
        
        drawing = svg2rlg(path)
        if not drawing:
            return
            
        # Original size
        dw = drawing.width
        dh = drawing.height
        
        # Determine scale
        scale_x = 1.0
        scale_y = 1.0
        
        if width and height:
            scale_x = width / dw
            scale_y = height / dh
            scale = min(scale_x, scale_y) # preserve aspect ratio
        elif width:
            scale = width / dw
        elif height:
            scale = height / dh
        else:
            scale = 1.0
            
        drawing.scale(scale, scale)
        
        # Calculate final dimensions
        fw = dw * scale
        fh = dh * scale
        
        # Position
        dx = x
        dy = y
        
        if center:
            dx = x - (fw / 2)
            # dy is usually bottom, so if we want to center vertically?
            # drawing draws from bottom-left usually? 
            # reportlab graphics drawing: 0,0 is bottom left of drawing.
        
        # renderPDF.draw(drawing, canvas, x, y) draws at x,y.
        # But we scaled it. scaling happens around 0,0?
        # usually need to translate?
        # renderPDF.draw takes drawing, canvas, x, y. 
        # It translates canvas to x,y and draws.
        
        renderPDF.draw(drawing, canvas, dx, dy)
        
    except ImportError:
        logging.getLogger(__name__).warning("svglib not installed. Cannot render SVG.")
    except Exception as e:
        logging.getLogger(__name__).error(f"Error rendering SVG {path}: {e}")

def split_extra_text(title, body, image_path, font_name, font_size, width, first_page_h, other_page_h):
    """Splits body text into page-sized chunks with spacing between paragraphs."""
    from reportlab.lib.utils import simpleSplit
    
    line_height = font_size * 1.2
    spacer_height = line_height * 0.5
    
    # Process text into lines and spacers
    paragraphs = [p for p in body.split('\n') if p.strip()]
    all_items = []
    
    for i, p in enumerate(paragraphs):
        p_lines = simpleSplit(p, f"{font_name}-Regular", font_size, width)
        for line in p_lines:
            all_items.append((line, line_height))
        # Add half-line spacer between paragraphs
        if i < len(paragraphs) - 1:
            all_items.append(("", spacer_height))
    
    pages = []
    
    def chunk_items(items, max_h, page_title, is_first, img=None):
        current_h = 0
        chunk = []
        remaining = []
        for j, (text, h) in enumerate(items):
            if current_h + h > max_h:
                remaining = items[j:]
                break
            chunk.append((text, h))
            current_h += h
        
        pages.append({
            'type': 'extra_text',
            'title': page_title,
            'image': img if is_first else None,
            'items': chunk,
            'is_first': is_first
        })
        return remaining

    # Page 1
    remaining = chunk_items(all_items, first_page_h, title, True, image_path)
    
    # Subsequent pages
    while remaining:
        remaining = chunk_items(remaining, other_page_h, "", False)
        
    return pages

def create_comparison_chart(filename, *data, 
                          pagesize='letter', font_name="Charis", 
                          prose_count=20, title="Comparison",
                          cover_image=None, logo_image=None, contributors=None, 
                          description=None, copyright_text=None, made_with=None,
                          extra_pages=None):
    """
    Args:
        filename: Output path
        data: list of dicts with 'symbol', 'items' [(glyph, word, img)...]
        pagesize: 'A4' or 'letter'
        font_name: Font family
        prose_count: Number of times each word appears in prose
        cover_image: Path to cover image
        logo_image: Path to logo image
        contributors: List of contributor names
        description: Description text for imprint page
        copyright_text: Copyright string
        made_with: Attribution string
        extra_pages: list of {'title', 'text', 'image'}
        pagesize: 'A4' or 'letter'
        font_name: Font family
        prose_count: Number of times each word appears in prose
        cover_image: Path to cover image
        logo_image: Path to logo image
        contributors: List of contributor names
        description: Description text for imprint page
        copyright_text: Copyright string
        made_with: Attribution string
    """
    log.info(f"Creating comparison chart called with {filename=}")
    font_size = 12
    if not register_fonts():
        log.error("Problem loading fonts (is Charis installed?)")
        raise
    
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
            
        page_type = data.get('type', 'content')

        if page_type == 'cover':
            # --- Cover Page ---
            # Title
            # Layout:
            # We want Logo above Title.
            # Current title_y starts at height - margin - 200.
            # We preserve this to leave room at top.
            
            title_top_y = height - margin - 200
            
            # --- Draw Logo (Above Title) ---
            logo_path = data.get('logo')
            if logo_path and os.path.exists(logo_path):
                # Available space for logo: from title_top_y up to top margin
                # top margin Y = height - margin
                # Leave a little padding (10) above title
                logo_space_bottom = title_top_y + 20
                logo_space_top = height - margin - 10
                logo_space_h = logo_space_top - logo_space_bottom
                
                if logo_space_h > 20: # If we have decent space
                    l_avail_w = half_width - (margin * 2)
                    
                    if logo_path.lower().endswith('.svg'):
                        # Center in the available vertical space
                        draw_svg(c, logo_path, base_x + half_width/2, logo_space_bottom + (logo_space_h/2), 
                                 width=l_avail_w, height=logo_space_h, center=True)
                    else:
                        try:
                            l_img = ImageReader(logo_path)
                            lw, lh = l_img.getSize()
                            l_aspect = lh / float(lw)
                            
                            l_disp_w = l_avail_w
                            l_disp_h = l_disp_w * l_aspect
                            if l_disp_h > logo_space_h:
                                l_disp_h = logo_space_h
                                l_disp_w = l_disp_h / l_aspect
                            
                            # Center horizontally
                            lx = base_x + (half_width - l_disp_w) / 2
                            # Center vertically in the space
                            ly = logo_space_bottom + (logo_space_h - l_disp_h)/2
                            
                            c.drawImage(l_img, lx, ly, width=l_disp_w, height=l_disp_h, mask='auto')
                        except Exception as e:
                            log.error(f"Error drawing logo: {e}")

            # --- Draw Title ---
            # Title starts at title_top_y and goes DOWN
            c.setFont(f"{font_name}-Bold", 36)
            title_text = data.get('title', '')
            
            from reportlab.lib.utils import simpleSplit
            available_width = half_width - (2 * margin)
            lines = simpleSplit(title_text, f"{font_name}-Bold", 36, available_width)
            
            current_y = title_top_y
            line_height = 40
            
            for line in lines:
                c.drawCentredString(base_x + half_width/2, current_y, line)
                current_y -= line_height

            # Cover Image (Below Title)
            img_path = data.get('image')
            if img_path and os.path.exists(img_path):
                img = ImageReader(img_path) if not img_path.lower().endswith('.svg') else None
                
                # Area below title
                # current_y is where the last line was drawn minus line_height.
                # So the bottom of the text is roughly current_y + line_height (since it decreased).
                # Actually, in the loop: draw at current_y, then decrement.
                # So current_y is now one line_height BELOW the last line baseline.
                # We can essentially use current_y as the start for the next section.
                start_y = current_y - 20
                avail_h = start_y - margin
                avail_w = half_width - (margin * 2)

                if avail_h > 0:
                     if img_path.lower().endswith('.svg'):
                          # Center vertically/horizontally in available space
                          # For vertical centering, we'd need to know the height.
                          # draw_svg renders at y (bottom).
                          # If we simply pass available box, it scales to fit.
                          # But if it scales to width, height might be small.
                          # Unlike drawImage, we don't easily know resulting height beforehand without parsing.
                          # However, draw_svg *does* calculate scale. 
                          # Ideally we'd center vertically too.
                          # For now, let's just center horizontally and place at margin (bottom of area).
                          # Or we could improve draw_svg to return size or handle vertical center?
                          # Let's start with horizontal centering.
                          draw_svg(c, img_path, base_x + half_width/2, margin, width=avail_w, height=avail_h, center=True)
                     else:
                        img = ImageReader(img_path)
                        iw, ih = img.getSize()
                        aspect = ih / float(iw)
                        
                        disp_w = avail_w
                        disp_h = disp_w * aspect
                        
                        # If image is too tall, scale down
                        if disp_h > avail_h:
                            disp_h = avail_h
                            disp_w = disp_h / aspect
                        
                        # Centered in the specific available area:
                        area_center_y = margin + (avail_h / 2)
                        
                        c.drawImage(img, base_x + (half_width - disp_w)/2, area_center_y - (disp_h/2), width=disp_w, height=disp_h, mask='auto', preserveAspectRatio=True)

        elif page_type == 'imprint':
            # --- Imprint Page (Inside Front) ---
            # Contributors (Top)
            c.setFont(f"{font_name}-Bold", 14)
            current_y = height - margin - 40
            c.drawCentredString(base_x + half_width/2, current_y, _("People Involved"))
            current_y -= 25
            
            c.setFont(f"{font_name}-Regular", 12)
            contribs = data.get('contributors', [])
            if contribs:
                for name in contribs:
                    c.drawCentredString(base_x + half_width/2, current_y, name)
                    current_y -= 15
            
            current_y -= 20 # Gap
            
            # Description Text (Between Contributors and Copyright)
            desc = data.get('description', '')
            if desc:
                c.setFont(f"{font_name}-Regular", 11)
                # Word wrap description
                from reportlab.lib.utils import simpleSplit
                desc_width = half_width - (margin * 2)
                lines = simpleSplit(desc, f"{font_name}-Regular", 11, desc_width)
                for line in lines:
                    c.drawCentredString(base_x + half_width/2, current_y, line)
                    current_y -= 13
            
            # Copyright (Bottom)
            copy = data.get('copyright', '')
            if copy:
                c.setFont(f"{font_name}-Regular", 10)
                c.drawCentredString(base_x + half_width/2, margin + 20, f'© {copy}')

        elif page_type == 'extra_text':
            # --- Extra Text Page ---
            title = data.get('title', '')
            lines = data.get('lines', [])
            img_path = data.get('image')
            is_first = data.get('is_first', False)
            
            current_y = height - margin
            
            # 1. Title
            if title:
                c.setFont(f"{font_name}-Bold", 18)
                c.drawCentredString(base_x + half_width/2, current_y - 20, title)
                current_y -= 50
            
            # 2. Image (First page only, if exists)
            if is_first and img_path and os.path.exists(img_path):
                # Max image height 1/3 of page?
                max_img_h = height / 3.0
                avail_w = half_width - (margin * 2)
                
                if img_path.lower().endswith('.svg'):
                    draw_svg(c, img_path, base_x + half_width/2, current_y - max_img_h, width=avail_w, height=max_img_h, center=True)
                    current_y -= (max_img_h + 20)
                else:
                    try:
                        img = ImageReader(img_path)
                        iw, ih = img.getSize()
                        aspect = ih / float(iw)
                        
                        disp_w = avail_w
                        disp_h = disp_w * aspect
                        if disp_h > max_img_h:
                            disp_h = max_img_h
                            disp_w = disp_h / aspect
                        
                        lx = base_x + (half_width - disp_w) / 2
                        ly = current_y - disp_h
                        c.drawImage(img, lx, ly, width=disp_w, height=disp_h, mask='auto', preserveAspectRatio=True)
                        current_y -= (disp_h + 20)
                    except Exception as e:
                        log.error(f"Error drawing extra image: {e}")

            # 2.5 Page Numbering
            page_num = data.get('_page_num')
            if page_num:
                 c.setFont(f"{font_name}-Regular", 10)
                 c.drawCentredString(base_x + half_width/2, margin - 10, str(page_num))

            # 3. Text
            c.setFont(f"{font_name}-Regular", 12)
            for text, h in data.get('items', []):
                if text:
                    # Left-align with margin.
                    c.drawString(base_x + margin, current_y, text)
                current_y -= h

        elif page_type == 'back':
            # --- Back Cover ---
            # Made With (Bottom)
            mw = data.get('made_with', '')
            if mw:
                c.setFont(f"{font_name}-Regular", 10)
                c.drawCentredString(base_x + half_width/2, margin + 20, mw)
        
        else:
            # --- Content Page ---
            symbol = data.get('symbol', '')
            items = data.get('items', [])
            
            # Page Numbering
            # Only for content pages.
            # data['_page_num'] should be set during preparation or we calculate here.
            # Easier to pass it in via data dict.
            page_num = data.get('_page_num')
            if page_num:
                 c.setFont(f"{font_name}-Regular", 10)
                 c.drawCentredString(base_x + half_width/2, margin - 10, str(page_num))

            # Safe extraction of words for prose (from tuple)
            words = [item[1] for item in items if len(item) > 1]
            
            content_width = half_width - (margin * 2)
            content_left = base_x + margin
            
            # 1. Symbol Header
            header_y = height - margin - 40
            c.setFont(f"{font_name}-Bold", 72)
            c.drawCentredString(base_x + half_width/2, header_y, symbol)
            
            # 2. Top Half (Examples)
            mid_page_y = height / 2.0
            examples_top = header_y - 20 # Spacing
            examples_height = examples_top - mid_page_y
            
            draw_triangular_examples(c, content_left, mid_page_y, content_width, examples_height, 
                                items, font_name, font_size)
            
            # 3. Bottom Half (Prose)
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
            if prev_data and prev_data.get('type', 'content') == 'content': #put both on second page
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

    # --- Prepare Data List ---
    # Convert tuple to list
    data_list = list(data)
    
    # Process Extra Text Pages
    processed_extra = []
    if extra_pages:
        # Dimensions for splitting
        content_w = half_width - (margin * 2)
        o_h = height - (2 * margin) - 50 # Height with title area
        
        try:
            for ep in extra_pages:
                # First page height depends on image
                image_h = (height / 3.0) if (ep.get('image') and os.path.exists(ep['image'])) else 0
                # title takes 50, image margin 20
                f_h = height - (2 * margin) - 50 - image_h - (20 if image_h > 0 else 0)
                
                chunks = split_extra_text(ep.get('title',''), ep.get('text',''), ep.get('image'), font_name, 12, content_w, f_h, o_h)
                log.info(f"Split extra page '{ep.get('title')}' into {len(chunks)} chunks")
                processed_extra.extend(chunks)
        except Exception as e:
            log.error(f"Critical error splitting extra pages: {e}")
            import traceback
            log.error(traceback.format_exc())
    
    log.info(f"Total processed extra pages: {len(processed_extra)}")

    # Label existing pages as content
    for d in data_list:
        if 'type' not in d:
            d['type'] = 'content'

    # Append extra text pages AFTER content
    data_list.extend(processed_extra)
    
    # Assign page numbers to content AND extra_text
    # User said "Only give page numbers where there is content, starting after the imprint page."
    content_page_counter = 1
    for d in data_list:
        if d.get('type') in ['content', 'extra_text']:
            d['_page_num'] = content_page_counter
            content_page_counter += 1

    # Insert Cover & Imprint at start (these shouldn't have numbers per user rule, 
    # and they aren't in the loop above which only checks 'content'/'extra_text')
    cover_page = {'type': 'cover', 'title': title, 'image': cover_image, 'logo': logo_image}
    imprint_page = {'type': 'imprint', 'contributors': contributors, 'copyright': copyright_text, 'description': description}
    
    data_list.insert(0, imprint_page)
    data_list.insert(0, cover_page)
    
    # Apply comparison data logic to Content pages only
    add_comparative_data(data_list) # Updated helper
    
    # Handle Back Cover
    # Pad to multiple of 4
    rem = len(data_list) % 4
    if rem > 0:
        for i in range(4 - rem):
            data_list.append({'type': 'empty'}) # Filler
    
    # Now valid multiple of 4.
    # The last page is index -1. This is the physical Back Cover.
    # Set its type/content to back
    data_list[-1]['type'] = 'back'
    data_list[-1]['made_with'] = made_with

    # Re-order for booklet signature
    # Note: make_signatures expects a list and returns reordered list
    # It might add padding if needed, but we already padded.
    # We need to ensure make_signatures handles our dicts.
    final_data = make_signatures(data_list)
    
    # Draw Pages
    for n,page_data in enumerate(final_data):
        if not n%2:
            start_at=prev_data=0
        else:
            start_at=half_width
            prev_data=final_data[n-1]
        
        # Check if page_data is valid dict or None (make_signatures pad)
        if page_data:
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
    
    # 1. Pad to multiple of 4 (Safety check, though we did it)
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
            ('b', 'ball', 'images/ball.png'), 
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
    # Test with mockup of new features
    create_comparison_chart("test_comp.pdf", l_data, r_data, 
                            title="My Test Booklet",
                            contributors=["Kent Rasmussen", "Jane Doe"],
                            copyright_text="(c) 2023",
                            made_with="Made with AZT")
