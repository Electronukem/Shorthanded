"""
Handwriting Shortcut Analyzer
Upload a handwriting image → compare stroke complexity with vs without shortcuts for f, m, w.
Shortcuts use minimum strokes while remaining OCR-readable.
"""
import gradio as gr
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize
import os, warnings

warnings.filterwarnings("ignore")

# ── OCR setup ──────────────────────────────────────────────────────────────────
print("Loading OCR model (first run downloads ~100MB)...")
import easyocr
reader = easyocr.Reader(['en'], gpu=False, verbose=False)
print("OCR ready.")

# ── Shortcut glyphs (pre-generated minimum-stroke PNGs) ───────────────────────
SHORTCUT_PATH = "data/MyWriting/shortcuts"
SHORTCUT_LETTERS = ['f', 'm', 'w']

def load_shortcut_glyphs():
    glyphs = {}
    for ch in SHORTCUT_LETTERS:
        path = os.path.join(SHORTCUT_PATH, f"{ch}_minimum.png")
        if os.path.exists(path):
            glyphs[ch] = Image.open(path).convert("L")
    return glyphs

GLYPHS = load_shortcut_glyphs()

# ── Stroke measurement ─────────────────────────────────────────────────────────

def skeleton_pixels(pil_img):
    """Count skeleton pixels = total ink path length (proxy for writing effort)."""
    gray = np.array(pil_img.convert("L"))
    binary = gray < 128          # ink = True
    if not binary.any():
        return 0
    skel = skeletonize(binary)
    return int(skel.sum())

def skeleton_overlay(pil_img):
    """Return image with skeleton drawn in red over original."""
    gray = np.array(pil_img.convert("L"))
    binary = gray < 128
    skel = skeletonize(binary)
    out = pil_img.convert("RGB").copy()
    arr = np.array(out)
    arr[skel] = [220, 40, 40]    # red skeleton
    return Image.fromarray(arr)

# ── Shortcut version builder ───────────────────────────────────────────────────

def build_shortcut_image(ocr_results, orig_img):
    """
    Replace each f/m/w bounding-box region in orig_img with the shortcut glyph.
    Returns the modified image.
    """
    result = orig_img.convert("RGB").copy()
    replaced = {ch: 0 for ch in SHORTCUT_LETTERS}

    for (bbox, text, conf) in ocr_results:
        # bbox: [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x1, x2 = int(min(xs)), int(max(xs))
        y1, y2 = int(min(ys)), int(max(ys))
        region_w = max(x2 - x1, 1)
        region_h = max(y2 - y1, 1)

        # Estimate per-character width within this word
        n_chars = max(len(text), 1)
        char_w = region_w // n_chars

        for i, ch in enumerate(text.lower()):
            if ch not in GLYPHS:
                continue
            cx1 = x1 + i * char_w
            cx2 = cx1 + char_w
            cy1, cy2 = y1, y2
            # White out the character region
            draw = ImageDraw.Draw(result)
            draw.rectangle([cx1, cy1, cx2, cy2], fill="white")
            # Paste scaled shortcut glyph
            glyph = GLYPHS[ch].resize((cx2 - cx1, cy2 - cy1), Image.LANCZOS)
            glyph_rgb = glyph.convert("RGB")
            result.paste(glyph_rgb, (cx1, cy1))
            replaced[ch] += 1

    return result, replaced

# ── Per-letter skeleton stats from user samples ────────────────────────────────

def measure_user_samples():
    """Measure average skeleton pixels per letter from user's own samples."""
    stats = {}
    for ch in SHORTCUT_LETTERS:
        folder = f"data/MyWriting/{ch}"
        if not os.path.exists(folder):
            continue
        totals = []
        for fname in sorted(os.listdir(folder))[:8]:
            fpath = os.path.join(folder, fname)
            try:
                img = Image.open(fpath).convert("L")
                # Crop UI chrome (top status bar ~120px, sides)
                w, h = img.size
                crop = img.crop((w//6, int(h*0.15), int(w*0.85), int(h*0.85)))
                totals.append(skeleton_pixels(crop))
            except Exception:
                continue
        if totals:
            stats[ch] = int(np.mean(totals))
    return stats

def measure_shortcut_samples():
    """Measure skeleton pixels of each shortcut glyph (normalized to ~300px height)."""
    stats = {}
    TARGET_H = 300
    for ch in SHORTCUT_LETTERS:
        if ch not in GLYPHS:
            continue
        g = GLYPHS[ch]
        aspect = g.width / g.height
        scaled = g.resize((int(TARGET_H * aspect), TARGET_H), Image.LANCZOS)
        stats[ch] = skeleton_pixels(scaled)
    return stats

USER_STATS     = measure_user_samples()
SHORTCUT_STATS = measure_shortcut_samples()

# ── Main analysis ──────────────────────────────────────────────────────────────

def analyze(image):
    if image is None:
        return None, None, "Please upload a handwriting image."

    orig = Image.fromarray(image)

    # OCR
    results = reader.readtext(image)
    detected_text = " ".join(r[1] for r in results)
    detected_lower = detected_text.lower()

    # Count shortcut-eligible letters
    letter_counts = {ch: detected_lower.count(ch) for ch in SHORTCUT_LETTERS}
    total_shortcuts = sum(letter_counts.values())

    # ── Skeleton analysis ──
    orig_skel_px = skeleton_pixels(orig)
    orig_overlay = skeleton_overlay(orig)

    # Build shortcut version
    shortcut_img, replaced = build_shortcut_image(results, orig)
    short_skel_px = skeleton_pixels(shortcut_img)
    short_overlay = skeleton_overlay(shortcut_img)

    savings_px  = orig_skel_px - short_skel_px
    savings_pct = round(100 * savings_px / orig_skel_px) if orig_skel_px > 0 else 0

    # ── Per-letter breakdown ──
    letter_rows = ""
    for ch in SHORTCUT_LETTERS:
        if letter_counts[ch] == 0:
            continue
        full_px  = USER_STATS.get(ch, "n/a")
        short_px = SHORTCUT_STATS.get(ch, "n/a")
        if isinstance(full_px, int) and isinstance(short_px, int):
            diff = full_px - short_px
            pct  = round(100 * diff / full_px) if full_px > 0 else 0
            letter_rows += (
                f"\n| **{ch}** | {letter_counts[ch]}× | "
                f"{full_px} px | {short_px} px | −{diff} px ({pct}%) |"
            )

    table = ""
    if letter_rows:
        table = (
            "\n\n### Per-letter breakdown (avg from your samples)\n"
            "| Letter | Count | Full strokes | Shortcut strokes | Savings |\n"
            "|--------|-------|-------------|------------------|---------|\n"
            + letter_rows
        )

    # ── Annotate images ──
    def annotate(img, label, px):
        out = img.copy()
        d = ImageDraw.Draw(out)
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
        except Exception:
            font = ImageFont.load_default()
        d.rectangle([0, 0, out.width, 50], fill=(30, 30, 30))
        d.text((10, 10), f"{label}  |  Stroke pixels: {px:,}", fill="white", font=font)
        return out

    orig_out  = annotate(orig_overlay,  "ORIGINAL",      orig_skel_px)
    short_out = annotate(short_overlay, "WITH SHORTCUTS", short_skel_px)

    summary = f"""## Results

**Detected text:** `{detected_text}`

**Shortcut letters in text:** f={letter_counts['f']}  m={letter_counts['m']}  w={letter_counts['w']}  (total: {total_shortcuts})

---

### Stroke complexity (skeleton pixels = total ink path length)

| | Stroke pixels |
|---|---|
| **Original** | {orig_skel_px:,} px |
| **With shortcuts** | {short_skel_px:,} px |
| **Savings** | {savings_px:,} px ({savings_pct}%) |

> *Skeleton pixels measure the total length of all pen strokes after thinning to 1-pixel-wide paths.
> Fewer pixels = less writing effort and simpler visual input for OCR.*
{table}
"""
    return orig_out, short_out, summary


# ── Gradio UI ──────────────────────────────────────────────────────────────────

with gr.Blocks(title="Handwriting Shortcut Analyzer", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
# Handwriting Shortcut Analyzer
Upload a photo of your handwriting. The analyzer counts stroke complexity (skeleton pixels)
and shows how much simpler your writing becomes when **f**, **m**, and **w** use minimum strokes.
    """)

    with gr.Row():
        inp = gr.Image(label="Upload handwriting image", type="numpy")

    btn = gr.Button("Analyze Strokes", variant="primary", size="lg")

    with gr.Row():
        out_orig  = gr.Image(label="Original  (red = detected strokes)")
        out_short = gr.Image(label="With Shortcuts  (red = detected strokes)")

    summary_md = gr.Markdown()

    btn.click(fn=analyze, inputs=inp, outputs=[out_orig, out_short, summary_md])

if __name__ == "__main__":
    app.launch()
