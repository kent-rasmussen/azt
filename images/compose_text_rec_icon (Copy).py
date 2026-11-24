#!/usr/bin/env python3
"""Make the Transcribe Texts icon (Kent, 2026-11-20): on the full page of text ('Report'), the record
microphone above the ZAZA letter stack, with an arrow from the one down to the other — speech IN, letters OUT.
(The microphone in the lower right corner means a task that records, as 'Add Words with Audio'; this one
doesn't, so it isn't there.)

    cd azt/images && ../../env/bin/python compose_text_rec_icon.py

Writes 'ZA Report Rec.png' (the page's size) and 'ZA Report Rec_icon.png' (the size of 'ZA Report_icon.png'),
named in frontend/theme_data.py. Run again after changing a source image or a setting below; the switches give
each piece's size as a fraction of the page's width. The only microphone image is small
('Microphone alone_sm.png'), so at full size it is scaled up and a little soft; at icon size it isn't.
"""
import argparse
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


def compose(mic_size, letters_size, top):
    page = Image.open(os.path.join(HERE, PAGE)).convert('RGBA')
    w, h = page.size
    mic = _scaled(MIC, round(w * mic_size))
    letters = _scaled(LETTERS, round(w * letters_size))
    cx = w // 2
    mic_at = (cx - mic.width // 2, round(h * top))
    letters_at = (cx - letters.width // 2, h - letters.height - round(h * 0.03))
    page.alpha_composite(mic, mic_at)
    # the arrow, from just under the microphone to just over the letters
    y0 = mic_at[1] + mic.height + round(h * 0.015)
    y1 = letters_at[1] + round(letters.height * 0.12)   # the stack's top edge is a little below its box
    shaft, head = max(2, round(w * 0.03)), round(w * 0.11)
    draw = ImageDraw.Draw(page)
    tip_len = round(head * 0.9)
    if y1 - y0 > tip_len:
        draw.rectangle([cx - shaft // 2, y0, cx + shaft // 2, y1 - tip_len], fill=INK)
    draw.polygon([(cx - head // 2, y1 - tip_len), (cx + head // 2, y1 - tip_len), (cx, y1)], fill=INK)
    page.alpha_composite(letters, letters_at)
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--mic', type=float, default=0.3, help="microphone width / page width (default 0.3)")
    ap.add_argument('--letters', type=float, default=0.62, help="ZAZA width / page width (default 0.62)")
    ap.add_argument('--top', type=float, default=0.03, help="microphone's top / page height (default 0.03)")
    args = ap.parse_args()
    full = compose(args.mic, args.letters, args.top)
    full.save(os.path.join(HERE, OUT))
    icon_size = Image.open(os.path.join(HERE, SIZE_LIKE)).size
    full.resize(icon_size, Image.LANCZOS).save(os.path.join(HERE, OUT_ICON))
    print(f"{OUT}: {full.width}x{full.height}; {OUT_ICON}: {icon_size[0]}x{icon_size[1]}")


if __name__ == '__main__':
    main()
