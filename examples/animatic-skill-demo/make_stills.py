import sys
from PIL import Image, ImageDraw, ImageFont
MONO = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 30)
SANS = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 28)
def window(title, text, out, size=30):
    mono = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', size)
    img = Image.new('RGB', (1920, 1080), '#0b0d10')
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((60, 40, 1860, 1040), 18, fill='#16191e', outline='#2a2f36', width=2)
    for i, c in enumerate(['#ff5f57', '#febc2e', '#28c840']):
        d.ellipse((90 + i * 34, 68, 112 + i * 34, 90), fill=c)
    d.text((210, 64), title, font=SANS, fill='#8a9099')
    y = 130
    for line in text.splitlines():
        d.text((100, y), line, font=mono, fill='#e6e8eb' if not line.startswith(('#', '  !!')) else '#e0b341')
        y += int(size * 1.45)
    img.save(out)
if __name__ == '__main__':
    title, src, out, size = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 30
    window(title, open(src).read(), out, size)
