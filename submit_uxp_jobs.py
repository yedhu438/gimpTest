import sys, json, urllib.request, os
from datetime import date
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
from sku_parser import build_zone_label
from product_canvas import PRODUCT_CANVAS, SKU_MAP
from bg_remover import remove_background
from pathlib import Path

JOBS_DIR    = Path(r"C:\Varsany\jobs")
IMAGES_DIR  = Path(r"C:\Varsany\Temp\OrderImages")
BASE_URL    = "http://www.crssoft.co.uk/CustomOrderImages/"
OUTPUT_ROOT = Path(os.environ.get("VARSANY_OUTPUT", r"C:\Varsany\Output"))

def is_manual_order(front_fonts, back_fonts, pocket_fonts=None, sleeve_fonts=None):
    combined = " ".join([(front_fonts or ""), (back_fonts or ""),
                         (pocket_fonts or ""), (sleeve_fonts or "")]).lower()
    return "emb" in combined or "rhine" in combined

def detect_product(sku):
    for prefix, product in sorted(SKU_MAP, key=lambda x: -len(x[0])):
        if sku.startswith(prefix): return product
    return "adulttshirt"

def get_zone_sizes(product, zone_name):
    canvas = PRODUCT_CANVAS.get(product, PRODUCT_CANVAS.get("adulttshirt"))
    w, h = canvas.get(zone_name, canvas.get("front", (3779, 3779)))
    return w, h

MAX_ITEMS_PER_PSD = 6  # Max items per PSD to stay within 30000px PSD limit

def get_output_path(sku, zone_count, order_id, item_count=1, part=None):
    today   = date.today().strftime("%Y-%m-%d")
    sku_low = sku.lower()
    if item_count > 1 or zone_count >= 2:
        category = "Automated"
    elif any(k in sku_low for k in ["kidshoo", "kidshood", "gymhoodie"]):
        category = "DTF Kids Hoodie"
    else:
        category = "DTF Front"
    colour = "black" if "blk" in sku_low else "white" if "wht" in sku_low else None
    folder = OUTPUT_ROOT / today / category
    if colour:
        folder = folder / colour
    folder.mkdir(parents=True, exist_ok=True)
    # Add part suffix for split orders e.g. OrderID_1.psd, OrderID_2.psd
    fname = f"{order_id}_{part}.psd" if part else f"{order_id}.psd"
    return str(folder / fname)

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

def ensure_image(fname, sku=None, is_print=False):
    if not fname: return None
    dest = IMAGES_DIR / fname
    if not (dest.exists() and dest.stat().st_size > 0):
        try:
            urllib.request.urlretrieve(BASE_URL + fname, dest)
            print(f"  Downloaded: {fname}")
        except Exception as e:
            print(f"  FAILED: {fname} -- {e}"); return None
    if is_print and sku:
        cleaned = remove_background(str(dest), sku)
        if cleaned != str(dest):
            return Path(cleaned).name
    return fname

def make_zone(img_json, img_field, text_raw, fonts_json, colours_json,
              preview_img=None, sku=None, zone_name="front", product="adulttshirt"):
    fi = get_img(img_json, img_field)
    ft = (text_raw or "").strip()
    if not fi and not ft: return None
    ps, fam, sty = get_font_info(fonts_json)
    w, h = get_zone_sizes(product, zone_name)
    return {
        "customer_image": ensure_image(fi, sku, is_print=True),
        "preview_image":  ensure_image((preview_img or "").strip() or None),
        "text_lines":     [l.strip() for l in ft.split("\n") if l.strip()] if ft else [],
        "font_ps_name":   ps, "font_family": fam, "font_style": sty,
        "colour_hex":     get_colour_hex(colours_json),
        "zone_w_px":      w, "zone_h_px": h,
    }

JOBS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

conn = get_connection()
cur  = conn.cursor()
cur.execute("""
    SELECT o.OrderID, o.SKU,
        d.FrontImageJSON, d.FrontImage, d.FrontText,  d.FrontFonts,  d.FrontColours,  d.FrontPreviewImage,
        d.BackImageJSON,  d.BackImage,  d.BackText,   d.BackFonts,   d.BackColours,   d.BackPreviewImage,
        d.PocketImageJSON,d.PocketImage,d.PocketPreviewImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE (d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != '')
    AND o.DateAdd >= DATEADD(day, -30, GETDATE())
    ORDER BY o.OrderID, o.SKU
""")
rows = cur.fetchall()
conn.close()

# Group rows by OrderID
from collections import defaultdict
orders = defaultdict(list)
for row in rows:
    orders[row[0]].append(row)

print(f"Found {len(rows)} rows across {len(orders)} unique orders.\n")
written = skipped = 0

for order_id, items in orders.items():
    # Skip if any item has emb/rhine
    has_manual = any(is_manual_order(r[5], r[11]) for r in items)
    if has_manual:
        print(f"[SKIP-MANUAL] {order_id} ({len(items)} items)")
        skipped += 1; continue

    # Use first item's SKU for folder routing and template
    first_sku = items[0][1]
    product   = detect_product(first_sku)

    # Build zones list — all items stacked
    # Each item contributes: pocket (if any), front, back (if any)
    # Zone key = zone_name + "_" + index to keep them unique
    all_zones = {}
    total_print_zones = 0

    for idx, row in enumerate(items):
        sku = row[1]
        suffix = f"_{idx}" if len(items) > 1 else ""  # suffix for multi-item orders

        # Pocket
        pi = get_img(row[14], row[15])
        if pi:
            key = f"pocket{suffix}"
            zone = make_zone(row[14], row[15], None, row[5], row[6], row[16], sku, "pocket", product)
            if zone:
                zone["label"] = build_zone_label("pocket", sku, True)
                all_zones[key] = zone
                total_print_zones += 1

        # Front
        front = make_zone(row[2], row[3], row[4], row[5], row[6], row[7], sku, "front", product)
        if front:
            key = f"front{suffix}"
            front["label"] = build_zone_label("front", sku, True)
            all_zones[key] = front
            total_print_zones += 1

        # Back
        back = make_zone(row[8], row[9], row[10], row[11], row[12], row[13], sku, "back", product)
        if back:
            key = f"back{suffix}"
            back["label"] = build_zone_label("back", sku, True)
            all_zones[key] = back
            total_print_zones += 1

    if not all_zones:
        skipped += 1; continue

    tpl = f"C:\\Varsany\\template\\{product}.psd"
    if not (Path(r"C:\Varsany\template") / f"{product}.psd").exists():
        tpl = "C:\\Varsany\\template\\combined_template.psd"

    # Split into chunks of MAX_ITEMS_PER_PSD to stay within PSD 30000px limit
    zone_keys  = list(all_zones.keys())
    # Group zone keys by item index (zones for same item share same suffix _0, _1 etc.)
    from itertools import groupby
    def item_idx(k):
        parts = k.rsplit("_", 1)
        return int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 0
    zone_keys.sort(key=item_idx)
    # Chunk by item index
    chunks = []
    chunk  = {}
    last_idx = None
    item_count_in_chunk = 0
    for k in zone_keys:
        idx = item_idx(k)
        if idx != last_idx:
            item_count_in_chunk += 1
            last_idx = idx
        if item_count_in_chunk > MAX_ITEMS_PER_PSD:
            chunks.append(chunk)
            chunk = {}
            item_count_in_chunk = 1
        chunk[k] = all_zones[k]
    if chunk:
        chunks.append(chunk)

    num_parts = len(chunks)
    for part_idx, chunk_zones in enumerate(chunks, 1):
        part = part_idx if num_parts > 1 else None
        out_path = get_output_path(first_sku, len(chunk_zones), order_id, len(items), part)
        job_id   = f"{order_id}_{part_idx}" if part else order_id
        job = {
            "order_id":    order_id,
            "sku":         first_sku,
            "combined":    True,
            "template":    tpl,
            "zones":       chunk_zones,
            "output_path": out_path,
            "dpi":         320
        }
        (JOBS_DIR / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
        parts_str = Path(out_path).parts
        routing   = "\\".join(parts_str[-3:-1])
        part_label = f" (part {part_idx}/{num_parts})" if num_parts > 1 else ""
        print(f"[JOB] {order_id}{part_label} | {len(chunk_zones)} zones | {routing}")
        written += 1

print(f"\nDone: {written} jobs written, {skipped} skipped.")
