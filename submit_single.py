import sys, json, urllib.request, os
from datetime import date
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
from sku_parser import build_zone_label
from product_canvas import PRODUCT_CANVAS, SKU_MAP
from pathlib import Path

JOBS_DIR    = Path(r"C:\gimpTest\jobs")
IMAGES_DIR  = Path(r"C:\gimpTest\Temp\OrderImages")
BASE_URL    = "http://www.crssoft.co.uk/CustomOrderImages/"
OUTPUT_ROOT = Path(os.environ.get("VARSANY_OUTPUT", r"C:\gimpTest\Output"))
TODAY       = date.today().strftime("%Y-%m-%d")

ORDER_IDS = ["203-7336765-5059543"]

def detect_product(sku):
    for prefix, product in sorted(SKU_MAP, key=lambda x: -len(x[0])):
        if sku.startswith(prefix): return product
    return "adulttshirt"

def get_zone_sizes(product, zone_name):
    canvas = PRODUCT_CANVAS.get(product, PRODUCT_CANVAS.get("adulttshirt"))
    w, h = canvas.get(zone_name, canvas.get("front", (3779, 3779)))
    return w, h

def is_manual_order(front_fonts, back_fonts):
    combined = " ".join([(front_fonts or ""), (back_fonts or "")]).lower()
    return "emb" in combined or "rhine" in combined

def get_output_path(sku, zone_count, order_id):
    sku_low = sku.lower()
    if zone_count >= 2:
        category = "Automated"
    elif any(k in sku_low for k in ["kidshoo", "kidshood", "gymhoodie"]):
        category = "DTF Kids Hoodie"
    else:
        category = "DTF Front"
    if "blk" in sku_low:
        colour = "black"
    elif "wht" in sku_low:
        colour = "white"
    else:
        colour = None
    folder = OUTPUT_ROOT / TODAY / category
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
            print(f"  FAILED: {fname} -- {e}"); return None
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
        "font_ps_name":   ps, "font_family": fam, "font_style": sty,
        "colour_hex":     get_colour_hex(colours_json),
    }

JOBS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

written = 0; skipped = 0; not_found = 0

for oid in ORDER_IDS:
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT o.OrderID, o.SKU,
                d.FrontImageJSON, d.FrontImage, d.FrontText,  d.FrontFonts,  d.FrontColours,  d.FrontPreviewImage,
                d.BackImageJSON,  d.BackImage,  d.BackText,   d.BackFonts,   d.BackColours,   d.BackPreviewImage,
                d.PocketImageJSON,d.PocketImage,d.PocketPreviewImage
            FROM tblCustomOrder o
            JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
            WHERE o.OrderID = ?
        """, oid)
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] {oid}: {e}"); skipped += 1; continue

    if not row:
        print(f"[NOT FOUND] {oid}"); not_found += 1; continue

    oid, sku = row[0], row[1]
    if is_manual_order(row[5], row[11]):
        print(f"[SKIP-MANUAL] {oid}"); skipped += 1; continue

    product = detect_product(sku)
    zones = {}
    front = make_zone(row[2], row[3], row[4], row[5], row[6], row[7])
    back  = make_zone(row[8], row[9], row[10], row[11], row[12], row[13])
    pi    = get_img(row[14], row[15]); pp = (row[16] or "").strip() or None

    if front:
        w, h = get_zone_sizes(product, "front")
        front["zone_w_px"] = w; front["zone_h_px"] = h
        zones["front"] = front
    if back:
        w, h = get_zone_sizes(product, "back")
        back["zone_w_px"] = w; back["zone_h_px"] = h
        zones["back"] = back
    if pi:
        w, h = get_zone_sizes(product, "pocket")
        pocket_zone = {"customer_image": ensure_image(pi), "preview_image": ensure_image(pp),
                       "text_lines": [], "font_ps_name": "Arial-BoldMT", "font_family": "Arial",
                       "font_style": "Bold", "colour_hex": "#ffffff", "zone_w_px": w, "zone_h_px": h}
        zones["pocket"] = pocket_zone

    if not zones:
        print(f"[SKIP-EMPTY] {oid}"); skipped += 1; continue

    tpl = f"C:\\gimpTest\\template\\{product}.psd"
    if not (Path(r"C:\gimpTest\template") / f"{product}.psd").exists():
        tpl = "C:\\gimpTest\\template\\combined_template.psd"

    out_path = get_output_path(sku, len(zones), oid)
    job = {"order_id": oid, "sku": sku, "combined": True,
           "template": tpl, "zones": zones, "output_path": out_path, "dpi": 320}
    (JOBS_DIR / f"{oid}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
    print(f"[JOB] {oid} | {sku} | zones:{list(zones.keys())}")
    written += 1

print(f"\nDone: {written} jobs queued, {skipped} skipped, {not_found} not found.")
