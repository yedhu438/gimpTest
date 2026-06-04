import sys, json, urllib.request, os
from datetime import date
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
from sku_parser import build_zone_label
from product_canvas import PRODUCT_CANVAS, SKU_MAP
from pathlib import Path

JOBS_DIR    = Path(r"C:\Varsany\jobs")
IMAGES_DIR  = Path(r"C:\Varsany\Temp\OrderImages")
BASE_URL    = "http://www.crssoft.co.uk/CustomOrderImages/"
OUTPUT_ROOT = Path(os.environ.get("VARSANY_OUTPUT", r"C:\Varsany\Output"))
TODAY       = date.today().strftime("%Y-%m-%d")

# All order IDs from the screenshot
ORDER_IDS = [
    "203-6236215-1733152","202-0127184-1532306","203-9762478-2556307","205-0106736-6116364","202-5968997-3242714",
    "204-5101368-2957930","203-4636703-7813114","206-6330390-5244319","204-7585867-5547551","203-8312778-8581945",
    "204-9156864-7840361","202-8084255-4177965","202-8460172-5696313","204-7488562-9160355","205-0729183-3644320",
    "204-3311570-2943569","026-0651492-2737914","205-0610156-7343549","026-5970900-0897141","204-2102833-3401136",
    "203-3695437-9146729","206-0855838-8905149","026-1819948-5001117","205-7886006-6362709","026-8565155-7233915",
    "026-5111856-3584359","206-2471230-7325965","202-6098429-7126702","203-6284181-8462730","026-0036932-3013121",
    "204-2817757-1236368","206-3572786-4348366","026-8212489-4010769","026-6585824-8495541","206-2800733-4277161",
    "205-2840758-1365969","205-1368303-9226706","206-8988405-2473112","203-0255002-1675568","205-8554460-9325119",
    "204-8299831-7509106","205-0497198-1143526","203-7756570-0101939","026-5816024-5757103",
    "026-3252663-6912318","026-7691468-7527569","206-4960052-2919568","202-8795577-8833949","202-1617454-4809126",
    "205-7891635-5353145","204-2697521-4663558","203-7680791-0183565","203-9338559-0341913",
    "204-8531503-2072301","206-2471230-7325965","206-3231041-6315566","206-8052483-8641169",
    "202-5641924-2892332","203-4145188-8946735","202-9154282-4422700","203-5136728-4488364",
    "203-5867058-0668351","203-1410550-6440318","026-4624805-9882711","026-6251648-6821148",
    "202-7564392-8545969","202-7509517-1992320","204-1698233-8078721","202-9347318-1459502",
    "205-4404307-6590733","205-5775939-9621168","206-3965895-5371539","204-3343154-8614700",
    "204-6991043-2411562","203-9170006-6233952","203-7376146-5235536","204-1301720-6616348",
    "026-4517621-5165150","204-4003244-6997939","026-4387938-4078740","202-7211270-7494730",
    "206-5219568-7025159","203-1112524-1905148","205-3169051-6267566","026-9289117-5538700",
    "206-7825850-3386740","202-2705985-0385135","203-8497074-0724337","205-9138097-0664328",
]

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

# Deduplicate
order_ids = list(dict.fromkeys(ORDER_IDS))
print(f"Total unique orders: {len(order_ids)}\n")

written = 0
skipped = 0
not_found = 0

for oid in order_ids:
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
        print(f"[DB ERROR] {oid}: {e}")
        skipped += 1; continue

    if not row:
        print(f"[NOT FOUND] {oid}")
        not_found += 1; continue

    oid, sku = row[0], row[1]

    if is_manual_order(row[5], row[11]):
        print(f"[SKIP-MANUAL] {oid} -- emb/rhine")
        skipped += 1; continue

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
        zones["pocket"] = {
            "customer_image": ensure_image(pi), "preview_image": ensure_image(pp),
            "text_lines": [], "font_ps_name": "Arial-BoldMT",
            "font_family": "Arial", "font_style": "Bold", "colour_hex": "#ffffff",
            "zone_w_px": w, "zone_h_px": h
        }
    if not zones: skipped += 1; continue

    for zone_name in list(zones.keys()):
        zones[zone_name]["label"] = build_zone_label(zone_name, sku, True)

    tpl = f"C:\\Varsany\\template\\{product}.psd"
    if not (Path(r"C:\Varsany\template") / f"{product}.psd").exists():
        tpl = "C:\\Varsany\\template\\combined_template.psd"

    out_path = get_output_path(sku, len(zones), oid)
    job = {
        "order_id": oid, "sku": sku, "combined": True,
        "template": tpl, "zones": zones,
        "output_path": out_path, "dpi": 320
    }
    (JOBS_DIR / f"{oid}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
    parts = Path(out_path).parts
    routing = "\\".join(parts[-3:-1])
    print(f"[JOB] {oid} | {sku} | {routing} | zones:{list(zones.keys())}")
    written += 1

print(f"\nDone: {written} jobs queued, {skipped} skipped, {not_found} not found.")
