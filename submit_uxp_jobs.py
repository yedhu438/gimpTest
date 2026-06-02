import sys, json, urllib.request
from datetime import date
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
from pathlib import Path

JOBS_DIR   = Path(r"C:\Varsany\jobs")
IMAGES_DIR = Path(r"C:\Varsany\Temp\OrderImages")
BASE_URL   = "http://www.crssoft.co.uk/CustomOrderImages/"
OUTPUT_ROOT = Path(r"C:\Varsany\Output")

# ── Colour extraction from SKU ─────────────────────────────────────────────────
COLOUR_MAP = {
    "Blk": "black", "Black": "black",
    "Wht": "white", "White": "white",
    "Nvy": "navy",  "Navy": "navy",
    "Pnk": "pink",  "Pink": "pink",
    "Red": "red",   "Blu": "blue",  "Blue": "blue",
    "Grn": "green", "Gry": "grey",  "Grey": "grey",
    "Pur": "purple","Brn": "brown", "Org": "orange",
    "Grph": "graphite", "Ivry": "ivory", "Ivo": "ivory",
    "Fch": "fuchsia", "Yel": "yellow", "Tl": "teal",
    "Kki": "khaki", "Cml": "camel", "Camo": "camo",
}

def get_colour_from_sku(sku):
    """Extract garment colour from SKU string."""
    sku_parts = sku.replace("-", "_").split("_")
    for part in sku_parts:
        for code, colour in COLOUR_MAP.items():
            if part == code or part.startswith(code):
                return colour
    return None

def get_output_folder(sku, zone_count):
    """
    Route to correct output subfolder:
      - multi-zone (2+)        → Automated\{colour}\ or Automated\
      - kids hoodie single     → DTF Kids Hoodie\{colour}\ or DTF Kids Hoodie\
      - everything else single → DTF Front\{colour}\ or DTF Front\
    """
    today     = date.today().strftime("%Y-%m-%d")
    colour    = get_colour_from_sku(sku)
    sku_lower = sku.lower()

    if zone_count >= 2:
        folder = "Automated"
    elif any(k in sku_lower for k in ["kidshoo", "kidshood", "gymhoodie"]):
        folder = "DTF Kids Hoodie"
    else:
        folder = "DTF Front"

    base = OUTPUT_ROOT / today / folder
    if colour:
        base = base / colour
    base.mkdir(parents=True, exist_ok=True)
    return str(base)

# ── Image helpers ──────────────────────────────────────────────────────────────
def get_img(img_json, img_field):
    if img_json:
        try:
            names = list(json.loads(img_json).values())
            if names: return names[0].strip()
        except: pass
    return (img_field or "").strip() or None

def get_colour_hex(colour_json):
    if colour_json:
        try:
            d = json.loads(colour_json)
            c = d.get("Colour1","").strip()
            if c and c.startswith("#"): return c
        except: pass
    return "#ffffff"

def ensure_image(fname):
    if not fname: return None
    dest = IMAGES_DIR / fname
    if not (dest.exists() and dest.stat().st_size > 0):
        try:
            urllib.request.urlretrieve(BASE_URL + fname, dest)
            print(f"  Downloaded: {fname}")
        except Exception as e:
            print(f"  FAILED: {fname} — {e}")
            return None
    return fname

def make_zone(img_json, img_field, text_raw, fonts_json, colours_json, preview_img=None):
    fi = get_img(img_json, img_field)
    ft = (text_raw or "").strip()
    if not fi and not ft: return None
    ps, fam, sty = get_font_info(fonts_json)
    return {
        "customer_image": ensure_image(fi),
        "preview_image":  ensure_image((preview_img or "").strip() or None),
        "text_lines":     [l.strip() for l in ft.split("\n") if l.strip()] if ft else [],
        "font_ps_name":   ps,
        "font_family":    fam,
        "font_style":     sty,
        "colour_hex":     get_colour_hex(colours_json),
    }

# ── Main ───────────────────────────────────────────────────────────────────────
JOBS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

conn = get_connection()
cur  = conn.cursor()
cur.execute("""
    SELECT TOP 10 o.OrderID, o.SKU,
        d.FrontImageJSON, d.FrontImage, d.FrontText,  d.FrontFonts,  d.FrontColours,  d.FrontPreviewImage,
        d.BackImageJSON,  d.BackImage,  d.BackText,   d.BackFonts,   d.BackColours,   d.BackPreviewImage,
        d.PocketImageJSON,d.PocketImage,d.PocketPreviewImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE (d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != '')
    AND o.DateAdd >= DATEADD(day, -30, GETDATE())
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()
conn.close()

print(f"Found {len(rows)} orders. Writing jobs...\n")

for row in rows:
    oid, sku = row[0], row[1]
    zones    = {}

    front = make_zone(row[2], row[3], row[4], row[5], row[6], row[7])
    back  = make_zone(row[8], row[9], row[10], row[11], row[12], row[13])
    pi    = get_img(row[14], row[15])
    pp    = (row[16] or "").strip() or None

    if front: zones["front"]  = front
    if back:  zones["back"]   = back
    if pi:
        zones["pocket"] = {
            "customer_image": ensure_image(pi),
            "preview_image":  ensure_image(pp),
            "text_lines": [], "font_ps_name": "Arial-BoldMT",
            "font_family": "Arial", "font_style": "Bold", "colour_hex": "#ffffff"
        }

    if not zones:
        print(f"[SKIP] {oid}"); continue

    # Route to correct output folder
    out_folder = get_output_folder(sku, len(zones))
    out_path   = f"{out_folder}\\{oid}.psd"

    job = {
        "order_id":    oid,
        "sku":         sku,
        "combined":    True,
        "template":    "C:\\Varsany\\template\\combined_template.psd",
        "zones":       zones,
        "output_path": out_path,
        "dpi":         320
    }
    (JOBS_DIR / f"{oid}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
    colour = get_colour_from_sku(sku) or "no-colour"
    folder_name = "Automated" if len(zones) >= 2 else ("DTF Kids Hoodie" if any(k in sku.lower() for k in ["kidshoo","kidshood","gymhoodie"]) else "DTF Front")
    print(f"[JOB] {oid} | {folder_name}\\{colour} | zones:{list(zones.keys())}")

print("\nAll jobs written.")
