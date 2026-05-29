#!/usr/bin/env python3
"""
Centralized template-metadata generator for the Varsany UXP print pipeline.

Phase 1 of the UXP Refactor Plan: extract ALL layout intelligence out of the
legacy Python rendering code (../../v4/batch_processor.py) into data, so that
PSD templates + this metadata become the single source of truth — NOT Python.

Run:  python build_metadata.py
Emits (into this folder):
  - catalog.json                 single source of truth (global cfg, sku map, sizes...)
  - <product>_<zone>.json        one file per print template (worker can require() it)

Nothing here renders anything. It only describes templates.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# AUTHORITATIVE PRINT RESOLUTION
#
# AUTHORITATIVE: the Photoshop "New Document" presets (owner screenshot).
#   Resolution: 320 Pixels/Inch | Units: Centimeters | px = round(cm / 2.54 * 320)
#   -> 30 cm @ 320 ppi = 3780 px.
#
# This RESOLVES the earlier conflict:
#   * v4/batch_processor.py:81  PX_PER_CM = 320/2.54 (~126 px/cm) is CORRECT
#     (320 ppi specified in cm). 30 cm -> 3780 px.
#   * CLAUDE.md "320 px/cm = 9600 px / 9600x9600" claim is WRONG.
# ─────────────────────────────────────────────────────────────────────────────
RESOLUTION_PPI = 320              # Pixels/Inch (matches PS New Document dialog)

def cm_to_px(cm):
    return int(round(cm / 2.54 * RESOLUTION_PPI))

# Photoshop document defaults — make every template match the owner's presets.
PHOTOSHOP_DOC = {
    "resolution": RESOLUTION_PPI,
    "resolution_unit": "Pixels/Inch",
    "units": "Centimeters",
    "color_mode": "CMYK Color",
    "bit_depth": 8,
    "background": "Transparent",
    "color_profile": "U.S. Web Coated (SWOP) v2",
    "pixel_aspect_ratio": "Square Pixels",
}

# Product keys whose FRONT canvas size is confirmed by a visible PS preset.
# (Presets show one canvas; back/pocket/sleeve sizes remain v4-derived.)
PS_CONFIRMED_FRONT = {
    "adulttshirt", "kidstshirt", "adulthoodie", "babyvest", "memorialplaque",
    "golftowel", "jutebag", "kidshoodie", "totebag", "kiddo", "buckethat",
    "socks", "stringbag", "backpack", "book",
}

# ─────────────────────────────────────────────────────────────────────────────
# PER-PRODUCT PRINT-ZONE SIZES (cm)
# Source: v4/batch_processor.py PRODUCT_CANVAS  (owner Canvases.xlsx).
# NOTE: code uses pocket 9x9 for tees/hoodies; the CLAUDE.md table shows 9x7 for
#       some rows. We keep the CODE values (PRODUCT_CANVAS) as authoritative.
# ─────────────────────────────────────────────────────────────────────────────
PRODUCT_CANVAS_CM = {
    # PS-preset confirmed (front size from owner's New Document dialog)
    "adulttshirt":    {"front": (30, 30),   "back": (30, 30),   "pocket": (9, 9)},   # Adult DTF
    "kidstshirt":     {"front": (22, 30),   "back": (22, 30),   "pocket": (9, 9)},   # Kids DTF (was 23x30)
    "adulthoodie":    {"front": (25, 25),   "back": (25, 25),   "pocket": (9, 9), "sleeve": (9, 7)},  # Adult Hoodie
    "kidshoodie":     {"front": (23, 20),   "back": (23, 20),   "pocket": (9, 9)},   # Kids Hoodie
    "totebag":        {"front": (28, 28),   "back": (28, 28)},                       # Tote Bag
    "backpack":       {"front": (18, 12)},                                           # Backpack
    "stringbag":      {"front": (22, 24)},                                           # String Bag
    "jutebag":        {"front": (25, 21)},                                           # Jute Bag (was knittingbag)
    "buckethat":      {"front": (11, 5)},                                            # Bucket Hat (was 18x5)
    "socks":          {"front": (6, 12)},                                            # Socks DTF
    "babyvest":       {"front": (15, 17)},                                           # Baby Vest
    "memorialplaque": {"front": (14, 9)},                                            # Memorial Plaque (was 13x8)
    "golftowel":      {"front": (17, 17)},                                           # Towel
    "kiddo":          {"front": (16, 16)},                                           # kiddo (new)
    "book":           {"front": (15, 15)},                                           # BOOK (new)
    # v4-legacy sizes (not in visible presets — confirm against hidden PS presets)
    "makeupbag":      {"front": (23, 14)},
    "shoebag":        {"front": (23, 14)},
    "shoebag2":       {"front": (14, 14)},
    "beanie":         {"front": (9.5, 4.5)},
    "seatbelt":       {"front": (18, 4)},
    "sleepsuit":      {"front": (13, 18)},
    "hodieblanket":   {"front": (17, 5)},
    "cushion":        {"front": (30, 30)},
    "golfcase":       {"front": (15, 6)},
    "slipper":        {"front": (6, 6)},
    "default":        {"front": (30, 30),   "back": (30, 30),   "pocket": (9, 9)},
}

# ─────────────────────────────────────────────────────────────────────────────
# SKU PREFIX -> PRODUCT KEY
# Source: v4/batch_processor.py SKU_MAP (owner Canvases.xlsx). Order matters:
# specific prefixes must precede their catch-alls (e.g. AnyTxt* before AnyTxt).
# ─────────────────────────────────────────────────────────────────────────────
SKU_MAP = [
    ("MenTee_", "adulttshirt"), ("AnyTxtOverSizeTee_", "adulttshirt"),
    ("WmnTee_", "adulttshirt"), ("PoloTee_", "adulttshirt"),
    ("AdultPoloTee_", "adulttshirt"), ("SignLan01_Tee_", "adulttshirt"),
    ("Custom04_Tee_", "adulttshirt"), ("LegendSince", "adulttshirt"),
    ("KidsTee_", "kidstshirt"), ("SLan01KidsTee_", "kidstshirt"),
    ("PerSingleLetter01KidsTee_", "kidstshirt"), ("FootballKids", "kidstshirt"),
    ("67BdayT02Kid", "kidstshirt"),
    ("AnyTxtAdultHood_", "adulthoodie"), ("MenHood_", "adulthoodie"),
    ("HandStand", "adulthoodie"), ("SplitGirl", "adulthoodie"),
    ("FballN", "adulthoodie"), ("NewFball", "adulthoodie"),
    ("AnyTxtKidsHood_", "kidshoodie"), ("KidsHood_", "kidshoodie"),
    ("AnyTxtTote_", "totebag"), ("Tote", "totebag"),
    ("AnyTxtBckpck_", "backpack"), ("BckPack", "backpack"), ("Name01", "backpack"),
    ("AnyTxtBabyVest_", "babyvest"), ("BabyVest", "babyvest"),
    ("AnyTextHat_", "buckethat"),
    ("AnytxtBeanie_", "beanie"),
    ("AnyTxtMakUp_", "makeupbag"),
    ("AnyTxtBlanketHood_", "hodieblanket"),
    ("AnyTxtShoeB_", "shoebag"),
    ("AnyTxtSlip", "slipper"),
    ("AnyTxtSocks", "socks"),
    ("AnyTxt", "adulttshirt"),
    ("PCushion", "cushion"),
    ("CustomKidsTee_", "kidstshirt"), ("Custom_Tee_", "adulttshirt"),
    ("GymLeo", "default"), ("SwimSuit", "default"),
]

# ─────────────────────────────────────────────────────────────────────────────
# SKU COLOUR CODE -> RGB (for background-removal "bg matches garment" rule).
# Source: CLAUDE.md section 13.
# ─────────────────────────────────────────────────────────────────────────────
COLOUR_MAP = {
    "blk": [20, 20, 20],
    "wht": [255, 255, 255],
    "nvy": [31, 40, 80],
    "red": [200, 30, 30],
    "ylw": [255, 220, 0],
    "pnk": [255, 150, 180],
    "gry": [150, 150, 150],
}

# Source: CLAUDE.md section 11.
COMPLEXITY_FLAGS = {
    "screenshot_border":   "Black letterbox borders detected",
    "low_resolution":      "Image < 500px even after upscaling",
    "bg_removal_uncertain":"Confidence < 80%",
    "too_many_photos":     "More than 6 photos in collage",
    "text_overflow":       "Text too long for canvas",
    "unknown_product":     "Product not in product catalog",
    "processing_error":    "Any script error",
    "premium_font":        "Font .ttf file not installed",
}

# Standardized layer-name contract every PSD template MUST follow (Plan Issue 5).
# `legacy_text` is what the CURRENT worker (index.html) looks for today.
LAYER_CONTRACT = {
    "artwork": {"front": "ARTWORK_FRONT", "back": "ARTWORK_BACK",
                "sleeve": "ARTWORK_SLEEVE", "pocket": "ARTWORK_POCKET"},
    "text":    {"front": "TEXT_FRONT", "back": "TEXT_BACK",
                "sleeve": "TEXT_SLEEVE", "pocket": "TEXT_POCKET"},
    "safe_area": "SAFE_AREA",
    "bleed":     "BLEED",
}

TEXT_MAX_WIDTH_PERCENT = 0.80     # text fills ~80% of its zone width


def zone_block(cm):
    w_cm, h_cm = cm
    return {
        "width_cm": w_cm, "height_cm": h_cm,
        "width_px": cm_to_px(w_cm), "height_px": cm_to_px(h_cm),
    }


def build_catalog():
    products = {}
    for product, zones in PRODUCT_CANVAS_CM.items():
        products[product] = {z: zone_block(cm) for z, cm in zones.items()}

    return {
        "_meta": {
            "description": "Single source of truth for Varsany DTF print templates. "
                           "PSD templates + this metadata drive placement; Python no longer renders.",
            "generated_by": "build_metadata.py",
            "source": "v4/batch_processor.py (PRODUCT_CANVAS, SKU_MAP) + CLAUDE.md",
            "resolution_note": f"Authoritative resolution = {RESOLUTION_PPI} Pixels/Inch, units cm "
                               f"(owner's PS New Document dialog). Formula: px = round(cm / 2.54 * 320) "
                               f"(30 cm = 3780 px). v4 cm_to_px (320/2.54) is CORRECT; the CLAUDE.md "
                               f"'320 px/cm / 9600x9600' claim is wrong.",
            "conflicts": [
                "RESOLUTION: resolved via PS dialog -> 320 ppi in cm (30cm=3780px). v4 cm_to_px is right; CLAUDE.md 9600px is wrong.",
                "Size fixes from PS presets: kidstshirt 23x30 -> 22x30; buckethat 18x5 -> 11x5; memorialplaque 13x8 -> 14x9.",
                "knittingbag renamed -> jutebag (25x21) per owner.",
                "Pocket size: PRODUCT_CANVAS code = 9x9 cm; CLAUDE.md table = 9x7 cm. Using code (9x9), not in PS presets.",
                "Product keys differ: PRODUCT_CANVAS uses adulthoodie/adulttshirt; CLAUDE.md TEMPLATE_MAP uses hoodie/tshirt. v4 has NO template map (renders from scratch).",
            ],
            "unknowns_require_confirmation": [
                "5 of 20 PS presets were below the fold — sizes for makeupbag/shoebag/shoebag2/beanie/seatbelt/"
                "sleepsuit/hodieblanket/cushion/golfcase/slipper are v4-legacy (size_source='v4_legacy').",
                "New presets 'kiddo' (16x16) and 'book' (15x15) have no SKU prefix in sku_map yet.",
                "back/pocket/sleeve sizes are v4-derived (presets only confirm the front canvas).",
                "Exact PSD template filenames (psd_file fields are UNCONFIRMED).",
                "Real layer names inside each template (target contract assumed: ARTWORK_*/TEXT_*).",
                "Smart-object placeholder names and the safe-area inset within each canvas "
                "(safe_area/text zone default to full canvas until PSDs are inspected).",
            ],
        },
        "photoshop_document": PHOTOSHOP_DOC,
        "global": {
            "psb_threshold_bytes": 2 * 1024 * 1024 * 1024,
            "text_max_width_percent": TEXT_MAX_WIDTH_PERCENT,
        },
        "layer_contract": LAYER_CONTRACT,
        "sku_map": [list(p) for p in SKU_MAP],
        "colour_map": COLOUR_MAP,
        "complexity_flags": COMPLEXITY_FLAGS,
        "products": products,
    }


def build_template(product, zone, cm):
    w_cm, h_cm = cm
    w_px, h_px = cm_to_px(w_cm), cm_to_px(h_cm)
    full = {"x": 0, "y": 0, "width": w_px, "height": h_px}
    return {
        "template": f"{product}_{zone}",
        "product": product,
        "zone": zone,
        "psd_file": f"{product}_{zone}.psd",
        "psd_file_confirmed": False,
        "canvas": {
            "width_cm": w_cm, "height_cm": h_cm,
            "width_px": w_px, "height_px": h_px,
            "size_source": "ps_preset" if (product in PS_CONFIRMED_FRONT and zone == "front") else "v4_legacy",
        },
        "photoshop_document": PHOTOSHOP_DOC,
        "artwork": {
            "smart_object_layer": LAYER_CONTRACT["artwork"].get(zone, f"ARTWORK_{zone.upper()}"),
            "fit": "contain",
            "safe_area": full,
            "safe_area_confirmed": False,
        },
        "text": {
            "layer": LAYER_CONTRACT["text"].get(zone, f"TEXT_{zone.upper()}"),
            "legacy_layer": f"CustomerText_{zone}",
            "alignment": "center",
            "align_within": "zone",
            "max_width_percent": TEXT_MAX_WIDTH_PERCENT,
            "zone": full,
            "zone_confirmed": False,
        },
    }


def main():
    catalog = build_catalog()
    with open(os.path.join(HERE, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    count = 0
    for product, zones in PRODUCT_CANVAS_CM.items():
        for zone, cm in zones.items():
            tpl = build_template(product, zone, cm)
            fname = f"{product}_{zone}.json"
            with open(os.path.join(HERE, fname), "w", encoding="utf-8") as f:
                json.dump(tpl, f, indent=2)
            count += 1

    print(f"Wrote catalog.json + {count} per-template files into {HERE}")


if __name__ == "__main__":
    main()
