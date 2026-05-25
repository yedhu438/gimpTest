"""
Quick CMYK pipeline test — verifies ICC profile loads and colour conversion works.
Run: python test_cmyk.py
Outputs: test_cmyk_output.psd  (open in Photoshop to check colours)
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image
import struct, io

# ── 1. Check ICC profile is found ────────────────────────────────────────────
from batch_processor import _ICC_PATH, _find_swop_profile, _rgb_to_cmyk, write_psd

print("=== ICC Profile ===")
if _ICC_PATH:
    size = os.path.getsize(_ICC_PATH)
    print(f"  FOUND: {_ICC_PATH}  ({size:,} bytes)")
else:
    print("  NOT FOUND — colour conversion will use naive fallback")
    sys.exit(1)

# ── 2. Test colour conversions ────────────────────────────────────────────────
print("\n=== Colour Conversion (RGB → CMYK) ===")
test_colours = {
    "Pure black   #000000": (0,   0,   0),
    "Dark grey    #1e1e1e": (30,  30,  30),
    "Dark navy    #1a1a3a": (26,  26,  58),
    "Red          #ff0000": (255, 0,   0),
    "White        #ffffff": (255, 255, 255),
    "Bright green #00ff00": (0,   255, 0),
    "Orange       #ffa500": (255, 165, 0),
}

for label, rgb in test_colours.items():
    img  = Image.new("RGB", (1, 1), rgb)
    cmyk = _rgb_to_cmyk(img)
    c, m, y, k = cmyk.getpixel((0, 0))
    snap = " ← snapped to pure K" if (c == 0 and m == 0 and y == 0 and k == 255) else ""
    print(f"  {label}  →  C:{c:3d} M:{m:3d} Y:{y:3d} K:{k:3d}{snap}")

# ── 3. Write a test PSD with colour swatches ──────────────────────────────────
print("\n=== Writing test PSD ===")
sw = 200   # swatch width/height
colours = [
    ((0,   0,   0),   "Black"),
    ((255, 0,   0),   "Red"),
    ((0,   0,   255), "Blue"),
    ((0,   255, 0),   "Green"),
    ((255, 165, 0),   "Orange"),
    ((255, 255, 255), "White"),
]

layers = []
for i, (rgb, name) in enumerate(colours):
    img = Image.new("RGBA", (sw, sw), rgb + (255,))
    layers.append({"image": img, "top": 0, "left": i * sw, "name": name, "visible": True})

out = os.path.join(os.path.dirname(__file__), "test_cmyk_output.psd")
write_psd(out, sw * len(colours), sw, layers)
print(f"  Saved: {out}")
print("\nOpen test_cmyk_output.psd in Photoshop and check:")
print("  - Black swatch should be pure K (0,0,0,100) — not rich black")
print("  - Colours should match expected hues")
print("  - Info panel should show SWOP v2 profile in Document Properties")
