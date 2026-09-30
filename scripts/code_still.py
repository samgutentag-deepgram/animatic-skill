#!/usr/bin/env python3
"""Render a code file as a still for a beat, with an optional range of lines lit up.

    python3 code_still.py smallest.py animatic/03-connect.png
    python3 code_still.py smallest.py animatic/04-listen.png --lines 17-25

Long files are cropped to a window around the lit lines, so the text stays readable.
"""
import argparse, os, pathlib, sys
from PIL import Image, ImageDraw, ImageFont

W, H, MAX_LINES = 1920, 1080, 30


def mono(size):
    for path in ['/System/Library/Fonts/Menlo.ttc', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
                 'C:/Windows/Fonts/consola.ttf']:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source', type=pathlib.Path)
    ap.add_argument('out', type=pathlib.Path)
    ap.add_argument('--lines', help='lines to light up, e.g. 12-20')
    args = ap.parse_args()
    if not args.source.is_file():
        sys.exit(f'not a file: {args.source}')
    code = args.source.read_text().expandtabs(4).splitlines() or ['']
    lit = range(0)
    if args.lines:
        a, _, b = args.lines.partition('-')
        lit = range(int(a), int(b or a) + 1)
    first = 1
    if len(code) > MAX_LINES:                   # window around the lit lines, or the top
        centre = (lit.start + lit.stop) // 2 if lit else MAX_LINES // 2
        first = max(1, min(centre - MAX_LINES // 2, len(code) - MAX_LINES + 1))
    shown = code[first - 1:first - 1 + MAX_LINES]

    size = min(34, int((H - 160) / (len(shown) * 1.4)), int((W - 260) / (max(map(len, shown)) * 0.6 or 1)))
    f, step = mono(size), int(size * 1.4)
    img = Image.new('RGB', (W, H), '#0b0d10')
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 30, W - 40, H - 30), 16, fill='#16191e', outline='#2a2f36', width=2)
    d.text((80, 50), args.source.name, font=mono(26), fill='#8a9099')
    y = 110
    for n, line in enumerate(shown, first):
        on = n in lit
        if on:
            d.rectangle((60, y - 4, W - 60, y + step - 4), fill='#2a2410')
        d.text((80, y), f'{n:>3}', font=f, fill='#5c636b')
        d.text((80 + size * 3, y), line, font=f, fill='#f1f2f4' if on or not lit else '#9aa0a6')
        y += step
    args.out.parent.mkdir(parents=True, exist_ok=True)
    img.save(args.out)
    print(f'wrote {args.out}')


if __name__ == '__main__':
    main()
