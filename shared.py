# shared.py — Common helpers for all Varsany export scripts
import json, urllib.request, os
from datetime import date
from pathlib import Path

_base       = os.environ.get("VARSANY_BASE", r"C:\Varsany")
JOBS_DIR    = Path(os.environ.get("VARSANY_JOBS",   os.path.join(_base, "jobs")))
IMAGES_DIR  = Path(os.environ.get("VARSANY_IMAGES", os.path.join(_base, "Temp", "OrderImages")))
BASE_URL    = "http://www.crssoft.co.uk/CustomOrderImages/"
OUTPUT_ROOT = Path(os.environ.get("VARSANY_OUTPUT", os.path.join(_base, "Output")))
MAX_ITEMS_PER_PSD = 6  # Max zones per PSD to stay within 30000px PSD limit

def is_manual_order(front_fonts, back_fonts, pocket_fonts=None, sleeve_fonts=None):
    combined = " ".join([(front_fonts or ""), (back_fonts or ""),
                         (pocket_fonts or ""), (sleeve_fonts or "")]).lower()
    return "emb" in combined or "rhine" in combined

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
    # Safety: if fname looks like JSON, try to extract filename from it
    if fname.strip().startswith("{"):
        try:
            names = list(json.loads(fname).values())
            if names: fname = names[0].strip()
            else: return None
        except: return None
    dest = IMAGES_DIR / fname
    if not (dest.exists() and dest.stat().st_size > 0):
        try:
            urllib.request.urlretrieve(BASE_URL + fname, dest)
            print(f"  Downloaded: {fname}")
        except Exception as e:
            print(f"  FAILED: {fname} -- {e}"); return None
    if is_print and sku:
        try:
            from bg_remover import remove_background
            cleaned = remove_background(str(dest), sku)
            if cleaned != str(dest):
                return Path(cleaned).name
        except: pass
    return fname

def make_zone(img_json, img_field, text_raw, fonts_json, colours_json,
              preview_img=None, sku=None, zone_name="front", product="adulttshirt"):
    from font_map import get_font_info
    from product_canvas import PRODUCT_CANVAS
    fi = get_img(img_json, img_field)
    ft = (text_raw or "").strip()
    if not fi and not ft: return None
    ps, fam, sty = get_font_info(fonts_json)
    canvas = PRODUCT_CANVAS.get(product, PRODUCT_CANVAS.get("adulttshirt"))
    w, h = canvas.get(zone_name, canvas.get("front", (3779, 3779)))
    return {
        "customer_image": ensure_image(fi, sku, is_print=True),
        "preview_image":  ensure_image((preview_img or "").strip() or None),
        "text_lines":     [l.strip() for l in ft.split("\n") if l.strip()] if ft else [],
        "font_ps_name":   ps, "font_family": fam, "font_style": sty,
        "colour_hex":     get_colour_hex(colours_json),
        "zone_w_px": w, "zone_h_px": h,
    }

def write_jobs(orders_dict):
    """
    orders_dict: {order_id: [rows]}
    Each order's zones are split into chunks of MAX_ITEMS_PER_PSD.
    Writes job JSONs to JOBS_DIR.
    Returns (written, skipped) counts.
    """
    from sku_parser import build_zone_label
    from product_canvas import SKU_MAP

    def detect_product(sku):
        for prefix, product in sorted(SKU_MAP, key=lambda x: -len(x[0])):
            if sku.startswith(prefix): return product
        return "adulttshirt"

    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    written = skipped = 0

    for order_id, items in orders_dict.items():
        if any(is_manual_order(r[6], r[12]) for r in items):  # row[6]=FrontFonts, row[12]=BackFonts
            print(f"[SKIP-MANUAL] {order_id} ({len(items)} items)")
            skipped += 1; continue

        first_sku = items[0][1]
        product   = detect_product(first_sku)

        # Build all zones for this order
        all_zones = {}
        total_zones = 0
        for idx, row in enumerate(items):
            sku    = row[1]
            suffix = f"_{idx}" if len(items) > 1 else ""

            # Column mapping (row[0]=OrderID, row[1]=SKU, row[2]=DateAdd):
            # row[3]=FrontImageJSON, row[4]=FrontImage, row[5]=FrontText
            # row[6]=FrontFonts, row[7]=FrontColours, row[8]=FrontPreviewImage
            # row[9]=BackImageJSON, row[10]=BackImage, row[11]=BackText
            # row[12]=BackFonts, row[13]=BackColours, row[14]=BackPreviewImage
            # row[15]=PocketImageJSON, row[16]=PocketImage, row[17]=PocketPreviewImage

            pi = get_img(row[15], row[16])
            if pi:
                zone = make_zone(row[15], row[16], None, row[6], row[7], row[17], sku, "pocket", product)
                if zone:
                    zone["label"] = build_zone_label("pocket", sku, True)
                    all_zones[f"pocket{suffix}"] = zone
                    total_zones += 1

            front = make_zone(row[3], row[4], row[5], row[6], row[7], row[8], sku, "front", product)
            if front:
                front["label"] = build_zone_label("front", sku, True)
                all_zones[f"front{suffix}"] = front
                total_zones += 1

            back = make_zone(row[9], row[10], row[11], row[12], row[13], row[14], sku, "back", product)
            if back:
                back["label"] = build_zone_label("back", sku, True)
                all_zones[f"back{suffix}"] = back
                total_zones += 1

        if not all_zones: skipped += 1; continue

        _tpl_dir = Path(os.environ.get("VARSANY_TEMPLATES", os.path.join(_base, "template")))
        tpl = str(_tpl_dir / f"{product}.psd")
        if not (_tpl_dir / f"{product}.psd").exists():
            tpl = str(_tpl_dir / "combined_template.psd")

        # Split into chunks of MAX_ITEMS_PER_PSD
        def item_idx(k):
            p = k.rsplit("_", 1)
            return int(p[1]) if len(p) == 2 and p[1].isdigit() else 0

        zone_keys = sorted(all_zones.keys(), key=item_idx)
        chunks = []; chunk = {}; last_idx = None; cnt = 0
        for k in zone_keys:
            idx = item_idx(k)
            if idx != last_idx: cnt += 1; last_idx = idx
            if cnt > MAX_ITEMS_PER_PSD:
                chunks.append(chunk); chunk = {}; cnt = 1
            chunk[k] = all_zones[k]
        if chunk: chunks.append(chunk)

        num_parts = len(chunks)
        for part_idx, chunk_zones in enumerate(chunks, 1):
            part = part_idx if num_parts > 1 else None
            out_path = get_output_path(first_sku, len(chunk_zones), order_id, len(items), part)
            job_id   = f"{order_id}_{part_idx}" if part else order_id
            job = {
                "order_id": order_id, "sku": first_sku, "combined": True,
                "template": tpl, "zones": chunk_zones,
                "output_path": out_path, "dpi": 320
            }
            (JOBS_DIR / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
            parts_str = Path(out_path).parts
            routing   = "\\".join(parts_str[-3:-1])
            part_label = f" (part {part_idx}/{num_parts})" if num_parts > 1 else ""
            print(f"[JOB] {order_id}{part_label} | {len(chunk_zones)} zones | {routing}")
            written += 1

    return written, skipped
