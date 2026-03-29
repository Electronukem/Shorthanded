"""
Generate minimum-stroke versions of f, m, w that OCR can still recognize.
Saves PNGs to data/MyWriting/shortcuts/
"""
from PIL import Image, ImageDraw
import os

os.makedirs("data/MyWriting/shortcuts", exist_ok=True)

W, H = 400, 400
STROKE = 6

def new_img():
    img = Image.new("RGB", (W, H), "white")
    return img, ImageDraw.Draw(img)

# ── f ──────────────────────────────────────────────────────────────────────────
# Minimum: vertical stem + crossbar. The curved top is NOT needed for OCR to
# distinguish f (the crossbar alone does it vs i, l, t etc.)
# Even simpler: a + shape where the vertical extends below the crossbar.
img, dr = new_img()
# vertical stem
dr.line([(200, 80), (200, 320)], fill="black", width=STROKE)
# crossbar (above midpoint, like a real f)
dr.line([(150, 175), (260, 175)], fill="black", width=STROKE)
img.save("data/MyWriting/shortcuts/f_minimum.png")

# ── m ──────────────────────────────────────────────────────────────────────────
# Minimum: two humps. One hump = n, two humps = m.
# Simplest form: /\/\ drawn as straight lines (no curves needed).
# Start stroke, two peaks, end stroke.
img, dr = new_img()
points = [
    (80, 300),   # start bottom-left
    (80, 180),   # up left side
    (160, 120),  # first peak
    (200, 200),  # valley
    (240, 120),  # second peak (slightly lower is fine)
    (280, 300),  # down right side
]
dr.line(points, fill="black", width=STROKE)
img.save("data/MyWriting/shortcuts/m_minimum.png")

# ── w ──────────────────────────────────────────────────────────────────────────
# Minimum: 3 direction changes (down-up-down-up).
# Can be written as a wide V with a center notch — straight lines only.
# This is already close to your sample but straighter lines suffice.
img, dr = new_img()
points = [
    (80, 160),   # top-left
    (140, 300),  # first valley
    (200, 200),  # center rise (the key distinguisher from u/v)
    (260, 300),  # second valley
    (320, 160),  # top-right
]
dr.line(points, fill="black", width=STROKE)
img.save("data/MyWriting/shortcuts/w_minimum.png")

print("Saved to data/MyWriting/shortcuts/")
print("  f_minimum.png — vertical stem + crossbar (no curved top)")
print("  m_minimum.png — two straight-line humps (/\\/\\)")
print("  w_minimum.png — wide V with center notch (4 straight lines)")
