#!/usr/bin/env python3
"""Compare clause detectors on text recordings that are already split (Kent, 2026-11-19).

azt cuts a recording into clauses once, when it is first opened, and writes the comparison then. For one
opened before that, run this: for each recording, a Praat TextGrid with a tier per detector that can run
(backend/core/texts.py DETECTORS: energy, silero, ...), numbered and unpadded so the gaps are the pauses each
found, a 'breakpoints' tier (every place the recording could be split, over its quiet stretch, with its score,
length and depth over 0.2 s), and a 'clauses' tier of the text's current clauses when --texts is given.

    cd azt && ../env/bin/python tests/manual/compare_segments.py --texts PROJECT/LIFT.texts.flextext \\
        PROJECT/texts/story.ogg [...]

Writes <stem>_segments.TextGrid beside each recording (or in --out). Open it in Praat with the recording.
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

AZT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, AZT)

from backend.core import texts   # noqa: E402


def current_clauses(flextext, audio_path):
    """[(begin_ms, end_ms)] of the text in `flextext` whose recording has `audio_path`'s file name, or None."""
    want = os.path.basename(audio_path)
    for it in ET.parse(flextext).getroot().iter('interlinear-text'):
        media = it.find('media-files/media')
        if media is not None and os.path.basename(media.get('location', '')) == want:
            return [(int(p.get('begin-time-offset')), int(p.get('end-time-offset'))) for p in it.iter('phrase')]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('recordings', nargs='+', help='text recordings')
    ap.add_argument('--texts', help="the project's texts file (<lift>.texts.flextext), for a 'clauses' tier")
    ap.add_argument('--out', help='folder for the TextGrids (default: beside each recording)')
    args = ap.parse_args()
    for path in args.recordings:
        clauses = current_clauses(args.texts, path) if args.texts else None
        if args.texts and clauses is None:
            print(f"{path}: not in {args.texts}; no 'clauses' tier")
        stem = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(args.out or os.path.dirname(os.path.abspath(path)), stem + '_segments.TextGrid')
        audio = texts.load_audio(path)
        places = None
        try:   # every place the recording could be split, clause boundaries included
            places = texts.breakpoints_for(audio)
        except ImportError as e:
            print(f"{path}: no breakpoints tier ({e})")
        found = texts.compare_segments(audio, out, clauses, name=os.path.basename(path), breakpoints=places)
        counts = ', '.join(f"{d} {len(c)}" for d, c in found.items())
        print(f"{path}: {len(clauses) if clauses else '-'} clauses now; {counts} -> {out}")


if __name__ == '__main__':
    main()
