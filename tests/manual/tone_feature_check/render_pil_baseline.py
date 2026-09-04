# coding=UTF-8
"""A-Z+T manual test: the BASELINE half of the tone feature check.

index.html shows what a browser can do. This shows what the app does *today* -
by using the same mechanism `frontend.ui_tkinter.Renderer.render` uses:
`utilities.fonts.face_files()` in priority order (the `-tstv` hidden-staves
builds FIRST), opened by PATH with `PIL.ImageFont.truetype`. Opening by path is
the whole point of the Renderer: Tk asks for fonts by FAMILY NAME and can never
select a particular file, so a tuned/staveless build is unreachable from Tk
without it.

    cd /path/to/azt && source env/bin/activate
    python tests/manual/tone_feature_check/render_pil_baseline.py

Writes one PNG per family into a temp directory (printed at the end) - never
into the repo, so it is safe on a read-only or unwritable checkout. Put those
beside a screenshot of the same rows in index.html; that side-by-side IS Step 2
of `agenda/webview_when_to_finish.md`.

The console output matters as much as the images: it names the font file that
actually won for each family, which is the open question in
`agenda/tstv_font_availability.md` - whether any machine besides the dev box
carries a `-tstv` build at all.

Unlike index.html this one DOES import azt, so it is dev-box only. That is
deliberate: it must use the real table, not a copy of it.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))

# Same strings as index.html's matrix. Keep the two in step.
ROWS = [
    ('chao',     'Chao tone letters U+02E5-02E9', '˥ ˦ ˧ ˨ ˩'),
    ('chaorev',  'Right-stem U+A712-A716',        '꜒ ꜓ ꜔ ꜕ ꜖'),
    ('contour2', '2-letter contours (MUST JOIN)',
     '˥˩ ˩˥ ˧˥ ˥˧ ˨˦'),
    ('contour3', '3-letter contours (MUST JOIN)',
     '˥˧˩ ˩˧˥ ˧˨˧'),
    ('chin',     'Chinantec marks',               'ˋ ˈ ˉ ˊ'),
    ('word',     'Tone-marked words',
     'ka˥˩ ta˩˥ na˧'),
    ('ortho',    'Modifier letters',              'ajᵃpijeʲj'),
]

SIZE = 46


def main():
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    try:
        from utilities import fonts as fontlib
    except ImportError as e:
        sys.stderr.write("Could not import utilities.fonts ({}).\n"
                         "Run this from the azt checkout, in its venv.\n"
                         "".format(e))
        return 2
    try:
        import PIL.Image
        import PIL.ImageDraw
        import PIL.ImageFont
    except ImportError:
        sys.stderr.write("Pillow is not installed in this interpreter.\n")
        return 2

    outdir = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(
        prefix='azt_tone_baseline_')
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    keys = ['charis', 'andika', 'gentium', 'gentiumbook', 'dejavu']
    print("Font files, in the Renderer's own priority order")
    print("(-tstv FIRST; the first one found is the one the app draws with):")
    print("")
    for key in keys:
        candidates = fontlib.face_files(key, 'Regular')
        winner, winner_path = None, None
        for name in candidates:
            path = fontlib.findfontfile(name)
            if path:
                winner, winner_path = name, path
                break
        print("  {:12s} tries {}".format(key, ' -> '.join(candidates)))
        if winner:
            tstv = '-tstv' in winner
            print("  {:12s} USES  {}   {}".format(
                '', winner_path, '<- TSTV (staveless) build' if tstv
                else '(no tstv build on this machine)'))
        else:
            print("  {:12s} USES  nothing - no file found".format(''))
        print("")

        if not winner_path:
            continue
        try:
            font = PIL.ImageFont.truetype(font=winner_path, size=SIZE)
        except OSError as e:
            print("  could not open {}: {}".format(winner_path, e))
            continue

        pad, lineh = 14, int(SIZE * 1.9)
        img = PIL.Image.new('RGB', (1000, pad * 2 + lineh * len(ROWS)), 'white')
        draw = PIL.ImageDraw.Draw(img)
        small = PIL.ImageFont.load_default()
        for i, (rid, lab, text) in enumerate(ROWS):
            y = pad + i * lineh
            draw.text((pad, y), lab, font=small, fill='#777')
            draw.text((pad, y + 14), text, font=font, fill='black')
        dest = os.path.join(outdir, 'baseline_{}.png'.format(key))
        img.save(dest)
        print("  wrote {}".format(dest))
        print("")

    print("")
    print("Baseline images are in: {}".format(outdir))
    print("Compare them against the same rows in index.html.")
    print("If the app's output already has no staves, that is the -tstv FILE")
    print("doing it, not a feature - which is exactly the mechanism a webview")
    print("would replace with font-feature-settings: \"cv92\" 1.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
