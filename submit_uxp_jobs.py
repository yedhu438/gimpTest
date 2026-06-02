import sys, json, urllib.request, os
from datetime import date
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
from sku_parser import build_zone_label
from pathlib import Path

JOBS_DIR    = Path(r"C:\Varsany\jobs")
IMAGES_DIR  = Path(r"C:\Varsany\Temp\OrderImages")
BASE_URL    = "http://www.crssoft.co.uk/CustomOrderImages/"
OUTPUT_ROOT = Path(os.environ.get("VARSANY_OUTPUT", r"C:\Varsany\Output"))

def is_manual_order(front_fonts, back_fonts, pocket_fonts=None, sleeve_fonts=None):
    """Returns True if any font field contains emb or rhine — skip these orders."""
    combined = " ".join([
        (front_fonts  or ""),
        (back_fonts   or ""),
        (pocket_fonts or ""),
        (sleeve_fonts or ""),
    ]).lower()
    return "emb" in combined or "rhine" in combined

def get_output_path(sku, zone_count, order_id):
    """Build output path: Output\YYYY-MM-DD\{category}\{colour?}\OrderID.psd"""
    today   = date.today().strftime("%Y-%m-%d")
    sku_low = sku.lower()

    # Level 2 — Category (check in order)
    if zone_count >= 2:
        category = "Automated"
    elif any(k in sku_low for k in ["kidshoo", "kidshood", "gymhoodie"]):
        category = "DTF Kids Hoodie"
    else:
        category = "DTF Front"

    # Level 3 — Colour: only black or white, everything else = no subfolder
    if "blk" in sku_low:
        colour = "black"
    elif "wht" in sku_low:
        colour = "white"
    else:
        colour = None

    folder = OUTPUT_ROOT / today / category
    if colour:
        folder = folder / colour
    folder.mkdir(parents=True, exist_ok=True)
    return str(folder / f"{order_id}.psd")

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
            print(f"  FAILED: {fname} -- {e}")
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

skipped = 0
written = 0

for row in rows:
    oid, sku = row[0], row[1]

    # ── Skip embroidery / rhinestone orders ───────────────────────────────────
    front_fonts  = row[5]
    back_fonts   = row[11]
    pocket_fonts = None   # not in query yet — add if needed
    sleeve_fonts = None   # not in query yet — add if needed
    if is_manual_order(front_fonts, back_fonts, pocket_fonts, sleeve_fonts):
        print(f"[SKIP] {oid} -- embroidery/rhinestone font, process manually")
        skipped += 1
        continue

    zones = {}
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
        print(f"[SKIP] {oid} -- no zones"); skipped += 1; continue

    # Add label to each zone
    is_multi_size = False
    for zone_name in list(zones.keys()):
        zones[zone_name]["label"] = build_zone_label(zone_name, sku, is_multi_size)

    out_path = get_output_path(sku, len(zones), oid)
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
    parts = Path(out_path).parts
    routing = "\\".join(parts[-3:-1])
    print(f"[JOB] {oid} | {routing} | zones:{list(zones.keys())}")
    written += 1

print(f"\nDone: {written} jobs written, {skipped} skipped.")
