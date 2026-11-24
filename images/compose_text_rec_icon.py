#!/usr/bin/env python3
"""Make the Transcribe Texts icon (Kent, 2026-11-20): speech IN, text OUT. (The microphone in the lower right
corner means a task that records, as 'Add Words with Audio'; this one doesn't, so it isn't there.)

    cd azt/images && ../../env/bin/python compose_text_rec_icon.py [--layout row|vertical|diagonal]

--layout row (the default; Kent: "lrt, mic > page (no ZAZA, no arrow stem), equal height mic and page"): left to
right, the microphone, an arrowhead, the page of text ('Report', its lines only), the microphone and the page the
same height. The image is the row plus a margin, so wider than tall; the icon is scaled to the height of
'ZA Report_icon.png'.
--layout vertical: on the page of text, the microphone above the ZAZA letter stack, an arrow down between them.
--layout diagonal: the same, microphone upper left, letters lower right.

Writes 'ZA Report Rec.png' and 'ZA Report Rec_icon.png', named in frontend/theme_data.py. Run again after
changing a source image or a setting. The only microphone image is small ('Microphone alone_sm.png'), so at full
size it is scaled up and a little soft; at icon size it isn't.
"""
import argparse
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE, MIC, LETTERS = 'Report.png', 'Microphone alone_sm.png', 'ZAZA clear stacks6.png'
SIZE_LIKE = 'ZA Report_icon.png'
OUT, OUT_ICON = 'ZA Report Rec.png', 'ZA Report Rec_icon.png'
INK = (26, 26, 26, 255)   # the arrow: near-black, like the letters


def _scaled(name, width):
    img = Image.open(os.path.join(HERE, name)).convert('RGBA')
    return img.resize((width, max(1, round(img.height * width / img.width))), Image.LANCZOS)


def _arrow(draw, start, end, shaft, head, tip_len):
    """A straight arrow from `start` to `end` (its tip), any direction."""
    (x0, y0), (x1, y1) = start, end
    length = math.hypot(x1 - x0, y1 - y0)
    if length == 0:
        return
    ux, uy = (x1 - x0) / length, (y1 - y0) / length   # along the arrow
    px, py = -uy, ux                                   # across it
    bx, by = x1 - ux * tip_len, y1 - uy * tip_len      # where the head starts
    if length > tip_len:
        s = shaft / 2
        draw.polygon([(x0 + px * s, y0 + py * s), (bx + px * s, by + py * s),
                      (bx - px * s, by - py * s), (x0 - px * s, y0 - py * s)], fill=INK)
    k = head / 2
    draw.polygon([(bx + px * k, by + py * k), (bx - px * k, by - py * k), (x1, y1)], fill=INK)


def _content(img):
    """`img` cropped to what is drawn in it: its opaque part, or where it has no transparency, its non-white."""
    img = img.convert('RGBA')
    alpha = img.getchannel('A')
    if alpha.getextrema()[0] < 255:
        box = alpha.point(lambda a: 255 if a > 16 else 0).getbbox()
    else:
        box = img.convert('L').point(lambda v: 255 if v < 240 else 0).getbbox()
    return img.crop(box) if box else img


def compose_row(margin=0.08, gap=0.08, head_len=0.16, head_across=0.3):
    """Microphone, arrowhead, page, left to right, the microphone and the page `1` tall; the rest are fractions
    of that height: the arrowhead's length and breadth, the gaps either side of it, the margin all round."""
    page_img = Image.open(os.path.join(HERE, PAGE)).convert('RGBA')
    background = page_img.getpixel((0, 0))
    page = _content(page_img)
    mic = _content(Image.open(os.path.join(HERE, MIC)))
    height = page.height   # the page at its own size; the microphone scaled up to it
    page_w = page.width
    mic = mic.resize((round(mic.width * height / mic.height), height), Image.LANCZOS)
    pad, between, head_w = round(height * margin), round(height * gap), round(height * head_len)
    width = pad + mic.width + between + head_w + between + page_w + pad
    canvas = Image.new('RGBA', (width, height + 2 * pad), background)
    x = pad
    canvas.alpha_composite(mic, (x, pad))
    x += mic.width + between
    cy, k = pad + height / 2, height * head_across / 2
    ImageDraw.Draw(canvas).polygon([(x, cy - k), (x, cy + k), (x + head_w, cy)], fill=INK)
    x += head_w + between
    canvas.alpha_composite(page, (x, pad))
    return canvas


def compose(mic_size, letters_size, top, layout='vertical'):
    """layout 'vertical': microphone over the letters, arrow straight down; 'diagonal': microphone upper left,
    letters lower right, arrow between (Kent, 2026-11-20: try both)."""
    page = Image.open(os.path.join(HERE, PAGE)).convert('RGBA')
    w, h = page.size
    mic = _scaled(MIC, round(w * mic_size))
    letters = _scaled(LETTERS, round(w * letters_size))
    if layout == 'diagonal':
        mic_at = (round(w * 0.04), round(h * top))
        letters_at = (w - letters.width - round(w * 0.03), h - letters.height - round(h * 0.03))
        # from off the microphone's lower right to the stack's upper left (its top edge is a little inside its box)
        start = (mic_at[0] + mic.width + round(w * 0.01), mic_at[1] + mic.height + round(h * 0.01))
        end = (letters_at[0] + round(letters.width * 0.22), letters_at[1] + round(letters.height * 0.22))
    else:
        cx = w // 2
        mic_at = (cx - mic.width // 2, round(h * top))
        letters_at = (cx - letters.width // 2, h - letters.height - round(h * 0.03))
        # from just under the microphone to just over the letters
        start = (cx, mic_at[1] + mic.height + round(h * 0.015))
        end = (cx, letters_at[1] + round(letters.height * 0.12))   # the stack's top edge is a little below its box
    page.alpha_composite(mic, mic_at)
    # widths halved, length kept (Kent, 2026-11-20: "cut the arrow width in half")
    shaft, head = max(1, round(w * 0.015)), round(w * 0.075)
    tip_len = round(w * 0.05)
    _arrow(ImageDraw.Draw(page), start, end, shaft, head, tip_len)
    page.alpha_composite(letters, letters_at)
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--mic', type=float, default=0.3, help="microphone width / page width (default 0.3)")
    ap.add_argument('--letters', type=float, default=0.62, help="ZAZA width / page width (default 0.62)")
    ap.add_argument('--top', type=float, default=0.03, help="microphone's top / page height (default 0.03)")
    ap.add_argument('--layout', choices=('row', 'vertical', 'diagonal'), default='row',
                    help="row: microphone > page, left to right; vertical: microphone over the letters; diagonal: "
                         "microphone upper left, letters lower right (default row)")
    ap.add_argument('--gap', type=float, default=0.08,
                    help="row: the space either side of the arrowhead / the row's height (default 0.08)")
    ap.add_argument('--head', type=float, default=0.16,
                    help="row: the arrowhead's length / the row's height (default 0.16; its breadth is 0.3)")
    args = ap.parse_args()
    if args.layout == 'row':
        full = compose_row(gap=args.gap, head_len=args.head)
    else:
        full = compose(args.mic, args.letters, args.top, args.layout)
    full.save(os.path.join(HERE, OUT))
    like = Image.open(os.path.join(HERE, SIZE_LIKE)).size
    if args.layout == 'row':   # its own shape, at the other icons' height
        icon_size = (round(full.width * like[1] / full.height), like[1])
    else:
        icon_size = like
    full.resize(icon_size, Image.LANCZOS).save(os.path.join(HERE, OUT_ICON))
    print(f"{OUT}: {full.width}x{full.height}; {OUT_ICON}: {icon_size[0]}x{icon_size[1]}")


if __name__ == '__main__':
    main()
