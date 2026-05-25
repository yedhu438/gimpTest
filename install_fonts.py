"""
install_fonts.py
================
Copies all required fonts (standard + premium) from W:\\Resources\\Fonts\\
into C:\\Varsany\\Fonts\\ with the exact filenames the batch processor expects.
Also downloads Lato Bold from Google Fonts (the only file missing from W:).

Run:
    python install_fonts.py

Requirements:
  - W: drive mapped to \\\\IndiaNAS\\Vector Designs  (already done)
  - Internet connection (for Lato Bold download only)
"""

import os
import shutil
import urllib.request

SRC  = r"W:\Resources\Fonts"
DEST = r"C:\Varsany\Fonts"

os.makedirs(DEST, exist_ok=True)

# ─── FONT COPY MAP ────────────────────────────────────────────────────────────
# (source filename on W:)  →  (destination filename in C:\\Varsany\\Fonts\\)
# Destination names are chosen so they normalise (lowercase, no spaces/hyphens)
# to the exact keys used in batch_processor.py FONT_ALIASES / PREMIUM_FONT_KEYS.

COPY_MAP = {
    # Standard fonts
    "abel-v18-latin-regular (2).ttf":          "Abel-Regular.ttf",          # → abelregular
    "BebasNeue-Regular.ttf":                   "BebasNeue-Regular.ttf",      # → bebasneueregular
    "chewy-v18-latin-regular.ttf":             "Chewy-Regular.ttf",          # → chewyregular
    "Fondamento-Regular.ttf":                  "Fondamento-Regular.ttf",     # → fondamentoregular
    "lato-v24-latin-regular.ttf":              "Lato-Regular.ttf",           # → latoregular
    "permanent-marker-v16-latin-regular.ttf":  "PermanentMarker-Regular.ttf",# → permanentmarkerregular
    "Roboto-Regular.ttf":                      "Roboto-Regular.ttf",         # → robotoregular
    "RussoOne-Regular.ttf":                    "RussoOne-Regular.ttf",       # → russooneregular
    "ultra-v25-latin-regular.ttf":             "Ultra-Regular.ttf",          # → ultraregular
    # Premium texture fonts
    "Smart Kids.otf":                          "Smart Kids.otf",             # → smartkids
    "Colorful Blocks.otf":                     "Colorful Blocks.otf",        # → colorfulblocks
    "Paint Splashes Rainbow.otf":              "Paint Splashes Rainbow.otf", # → paintsplashesrainbow
    "Wavemermaid.otf":                         "Wavemermaid.otf",            # → wavemermaid
    "Refraction Ray.otf":                      "Refraction Ray.otf",         # → refractionray
    "Camoblock.otf":                           "Camoblock.otf",              # → camoblock
    "Spider Web.otf":                          "Spider Web.otf",             # → spiderweb
    "Cozy Winter.otf":                         "Cozy Winter.otf",            # → cozywinter
    "Soccer Army.otf":                         "Soccer Army.otf",            # → soccerarmy
    "Tropical Flower.otf":                     "Tropical Flower.otf",        # → tropicalflower
    "VINYLFONT.TTF":                           "VinylFont.ttf",              # → vinylfont
}

# Lato Bold is not on W: — download from Google Fonts
DOWNLOAD_MAP = {
    "Lato-Bold.ttf": "https://fonts.gstatic.com/s/lato/v24/S6u9w4BMUTPHh6UVSwiPHA.ttf",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ─── COPY FROM W: ─────────────────────────────────────────────────────────────

print("Copying fonts from W:\\Resources\\Fonts ...\n")
ok = skip = fail = 0

for src_name, dest_name in COPY_MAP.items():
    src_path  = os.path.join(SRC, src_name)
    dest_path = os.path.join(DEST, dest_name)

    if os.path.exists(dest_path):
        print(f"  EXISTS   {dest_name}")
        skip += 1
        continue

    if not os.path.exists(src_path):
        print(f"  MISSING  {src_name}  (not found on W: drive)")
        fail += 1
        continue

    shutil.copy2(src_path, dest_path)
    size = os.path.getsize(dest_path) // 1024
    print(f"  COPIED   {dest_name}  ({size} KB)")
    ok += 1

print(f"\n  Copied: {ok}   Already present: {skip}   Not found: {fail}")

# ─── DOWNLOAD LATO BOLD ───────────────────────────────────────────────────────

print("\nDownloading Lato Bold from Google Fonts ...\n")
for filename, url in DOWNLOAD_MAP.items():
    dest_path = os.path.join(DEST, filename)
    if os.path.exists(dest_path):
        print(f"  EXISTS   {filename}")
        continue
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        print(f"  DOWNLOADED  {filename}  ({len(data)//1024} KB)")
    except Exception as e:
        print(f"  FAIL  {filename}  — {e}")

# ─── VERIFY ───────────────────────────────────────────────────────────────────

print("\n─── Fonts now installed in C:\\Varsany\\Fonts\\ ─────────────────")
installed = sorted(f for f in os.listdir(DEST) if f.lower().endswith((".ttf", ".otf")))
print(f"  {len(installed)} font files total\n")

expected_dest_names = set(COPY_MAP.values()) | set(DOWNLOAD_MAP.keys())
missing = [n for n in expected_dest_names if not os.path.exists(os.path.join(DEST, n))]

if missing:
    print("  STILL MISSING:")
    for n in sorted(missing):
        print(f"    • {n}")
else:
    print("  All required fonts are installed.")
    print("\n  Ready to run:  python export_orders_with_images.py")
