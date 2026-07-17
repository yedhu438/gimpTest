import sys, json, urllib.request, os
from datetime import date
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
from sku_parser import build_zone_label
from pathlib import Path

JOBS_DIR    = Path(r"C:\gimpTest\jobs")
IMAGES_DIR  = Path(r"C:\gimpTest\Temp\OrderImages")
BASE_URL    = "http://www.crssoft.co.uk/CustomOrderImages/"
OUTPUT_ROOT = Path(os.environ.get("VARSANY_OUTPUT", r"C:\gimpTest\Output"))

# Product categories and their SKU prefix keywords
# IMPORTANT: More specific prefixes must come BEFORE catch-alls like "AnyTxt"
CATEGORIES = {
    "adulthoodie":  ["AnyTxtAdultHood_","MenHood_","HandStand","SplitGirl","FballN","NewFball"],
    "kidshoodie":   ["AnyTxtKidsHood_","KidsHood_"],
    "babyvest":     ["AnyTxtBabyVest_","BabyVest"],
    "totebag":      ["AnyTxtTote_"],
    "backpack":     ["AnyTxtBckpck_","BckPack","Name01"],
    "buckethat":    ["AnyTextHat_"],
    "beanie":       ["AnytxtBeanie_"],
    "socks":        ["AnyTxtSocksAnkl_","AnyTxtSocks"],
    "makeupbag":    ["AnyTxtMakUp_"],
    "slipper":      ["AnyTxtSlip"],
    "cushion":      ["PCushion"],
    "adulttshirt":  ["MenTee_","WmnTee_","COMenTee_","PoloTee_","AdultPoloTee_","LegendSince","AnyTxtOverSizeTee_","AnyTxt"],
    "kidstshirt":   ["KidsTee_","SLan01KidsTee_","FootballKids","67BdayT02Kid","CustomKidsTee_"],
}

def is_manual_order(front_fonts, back_fonts):
    combined = " ".join([(front_fonts or ""), (back_fonts or "")]).lower()
    return "emb" in combined or "rhine" in combined

def get_output_path(sku, zone_count, order_id, category):
    today   = date.today().strftime("%Y-%m-%d")
    sku_low = sku.lower()
    if zone_count >= 2:
        cat_folder = "Automated"
    elif any(k in sku_low for k in ["kidshoo", "kidshood", "gymhoodie"]):
        cat_folder = "DTF Kids Hoodie"
    else:
        cat_folder = "DTF Front"
    if "blk" in sku_low:
        colour = "black"
    elif "wht" in sku_low:
        colour = "white"
    else:
        colour = None
    folder = OUTPUT_ROOT / today / cat_folder
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

cat_counts = {k: 0 for k in CATEGORIES}
seen_ids   = set()
written    = 0
skipped    = 0

# Query per category with LIKE filters — avoids fetching entire table
for cat, prefixes in CATEGORIES.items():
    if cat_counts[cat] >= 5:
        continue
    try:
        conn = get_connection()
        cur  = conn.cursor()
        # Build WHERE clause for this category's prefixes
        like_clauses = " OR ".join([f"o.SKU LIKE '{p}%'" for p in prefixes])
        cur.execute(f"""
            SELECT TOP 50 o.OrderID, o.SKU,
                d.FrontImageJSON, d.FrontImage, d.FrontText,  d.FrontFonts,  d.FrontColours,  d.FrontPreviewImage,
                d.BackImageJSON,  d.BackImage,  d.BackText,   d.BackFonts,   d.BackColours,   d.BackPreviewImage,
                d.PocketImageJSON,d.PocketImage,d.PocketPreviewImage
            FROM tblCustomOrder o
            JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
            WHERE (d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != '')
            AND ({like_clauses})
            ORDER BY o.DateAdd DESC
        """)
        rows = cur.fetchall()
        conn.close()
        print(f"\n[{cat}] Found {len(rows)} orders...")
    except Exception as e:
        print(f"\n[{cat}] DB error: {e}")
        continue

    for row in rows:
        if cat_counts[cat] >= 5:
            break
        oid, sku = row[0], row[1]
        if oid in seen_ids: continue
        seen_ids.add(oid)

        if is_manual_order(row[5], row[11]):
            print(f"  [SKIP-MANUAL] {oid}")
            skipped += 1; continue

        zones = {}
        front = make_zone(row[2], row[3], row[4], row[5], row[6], row[7])
        back  = make_zone(row[8], row[9], row[10], row[11], row[12], row[13])
        pi    = get_img(row[14], row[15]); pp = (row[16] or "").strip() or None

        if front: zones["front"] = front
        if back:  zones["back"]  = back
        if pi:
            zones["pocket"] = {
                "customer_image": ensure_image(pi), "preview_image": ensure_image(pp),
                "text_lines": [], "font_ps_name": "Arial-BoldMT",
                "font_family": "Arial", "font_style": "Bold", "colour_hex": "#ffffff"
            }
        if not zones: skipped += 1; continue

        for zone_name in list(zones.keys()):
            zones[zone_name]["label"] = build_zone_label(zone_name, sku, True)

        tpl_path = f"C:\\gimpTest\\template\\{cat}.psd"
        if not (Path(r"C:\gimpTest\template") / f"{cat}.psd").exists():
            tpl_path = "C:\\gimpTest\\template\\combined_template.psd"

        out_path = get_output_path(sku, len(zones), oid, cat)
        job = {
            "order_id": oid, "sku": sku, "combined": True,
            "template": tpl_path, "zones": zones,
            "output_path": out_path, "dpi": 320
        }
        (JOBS_DIR / f"{oid}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
        parts = Path(out_path).parts
        routing = "\\".join(parts[-3:-1])
        print(f"  [JOB] {oid} | {sku} | {routing} | zones:{list(zones.keys())}")
        cat_counts[cat] += 1
        written += 1

print(f"\nResult: {written} jobs written, {skipped} skipped.")
print("\nPer category:")
for cat, count in cat_counts.items():
    print(f"  {cat:<15} {count}/5 {'OK' if count>=5 else 'NOT ENOUGH ORDERS'}")
