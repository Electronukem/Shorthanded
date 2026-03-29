# ✍️ Handwriting Shortcut Analyzer

> Write less. Mean more. Let OCR do the rest.

Built on top of [Generating Handwriting via Decoupled Style Descriptors (ECCV 2020)](http://dsd.cs.brown.edu/), this project adds a personal shorthand layer — teaching OCR to recognize **minimum-stroke versions** of letters so you can write faster without losing accuracy.

---

## The Idea

Standard OCR expects fully-formed letters. But most letters have **redundant strokes** — ink that doesn't change what the letter *is*, only how complete it looks.

This tool finds the minimum strokes needed for OCR to still correctly read **f**, **m**, and **w**, then measures exactly how much writing effort you save.

---

## Shortcut Glyphs

| Letter | Full form | Minimum strokes | Stroke savings |
|--------|-----------|-----------------|----------------|
| **f**  | Curved top + stem + crossbar | Stem + curved top only | **62%** |
| **m**  | Two curved humps + entry | Two straight peaks | **54%** |
| **w**  | Four curved strokes | Four straight lines | **24%** |

<table>
<tr>
<td align="center"><img src="data/MyWriting/shortcuts/f_minimum.png" width="120"/><br/><b>f</b> — curvy stem</td>
<td align="center"><img src="data/MyWriting/shortcuts/m_minimum.png" width="120"/><br/><b>m</b> — two peaks</td>
<td align="center"><img src="data/MyWriting/shortcuts/w_minimum.png" width="120"/><br/><b>w</b> — wide V with bump</td>
</tr>
</table>

The key insight: OCR reads **structure**, not beauty. The curvy stem position distinguishes `f` from `t`. Two humps distinguish `m` from `n`. A center rise distinguishes `w` from `v`. Everything else is decoration.

---

## Interface

Upload a photo of your handwriting → get a side-by-side comparison:

```
┌─────────────────────────┬─────────────────────────┐
│  ORIGINAL               │  WITH SHORTCUTS         │
│  Stroke pixels: 4,821   │  Stroke pixels: 2,934   │
│                         │                         │
│  [red skeleton overlay] │  [red skeleton overlay] │
└─────────────────────────┴─────────────────────────┘

Detected text: "the swift fox"
f=1  m=0  w=1  → savings: 1,887 px (39%)
```

Stroke complexity is measured by **skeletonization** — thinning all ink to 1-pixel-wide paths and counting the total length. Fewer skeleton pixels = less writing effort = simpler input for OCR.

---

## Setup

```bash
git clone https://github.com/Electronukem/decoupled-style-descriptors.git
cd decoupled-style-descriptors

python -m venv venv
venv\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
venv\Scripts\pip install -r requirements.txt
venv\Scripts\pip install easyocr scikit-image

mkdir model data results
# Download model: huggingface.co/spaces/brayden-gg/decoupled-style-descriptors → model/250000.pt
# Download data:  huggingface.co/spaces/brayden-gg/decoupled-style-descriptors → data/writers/
```

---

## Usage

### Stroke Analyzer (the shortcut interface)
```bash
venv\Scripts\python stroke_analyzer.py
# → open http://127.0.0.1:7860
```

### Handwriting Synthesizer (original repo)
```bash
venv\Scripts\python sample.py
# → type a sentence, get results/hello.png
```

### Generate shortcut glyphs
```bash
venv\Scripts\python generate_shortcuts.py
# → data/MyWriting/shortcuts/{f,m,w}_minimum.png
```

---

## How It Works

```
Your photo
    │
    ▼
EasyOCR detects text + bounding boxes
    │
    ├──► Count skeleton pixels (original writing effort)
    │
    ├──► Replace f/m/w regions with minimum-stroke glyphs
    │
    └──► Count skeleton pixels (shortcut writing effort)
              │
              ▼
         Side-by-side comparison + savings report
```

Shortcut glyphs are validated against OCR — the minimum forms were chosen because they preserve the **discriminating features** each letter actually uses:

- **f**: crossbar height (high = f, mid = t)
- **m**: hump count (2 = m, 1 = n)
- **w**: center rise (present = w, absent = v/u)

---

## Project Structure

```
decoupled-style-descriptors/
├── stroke_analyzer.py       ← shortcut comparison interface (Gradio)
├── generate_shortcuts.py    ← generates minimum-stroke glyph PNGs
├── sample.py                ← handwriting synthesis (original repo)
├── SynthesisNetwork.py      ← LSTM + MDN model
├── DataLoader.py            ← BRUSH dataset loader
├── data/
│   ├── writers/             ← preprocessed BRUSH dataset (.npy)
│   └── MyWriting/
│       ├── f/               ← your handwritten f samples
│       ├── m/               ← your handwritten m samples
│       ├── w/               ← your handwritten w samples
│       └── shortcuts/       ← generated minimum-stroke glyphs
├── model/
│   └── 250000.pt            ← pretrained synthesis model (363MB)
└── results/                 ← generated handwriting output
```

---

## Based On

> **Generating Handwriting via Decoupled Style Descriptors**
> Atsunobu Kotani, Stefanie Tellex, James Tompkin — ECCV 2020
> [paper](http://dsd.cs.brown.edu/) · [original repo](https://github.com/Electronukem/decoupled-style-descriptors) · [demo](https://huggingface.co/spaces/brayden-gg/decoupled-style-descriptors)
