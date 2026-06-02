import sys, json, urllib.request
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
from pathlib import Path

JOBS_DIR   = Path(r"C:\Varsany\jobs")
IMAGES_DIR = Path(r"C:\Varsany\Temp\OrderImages")
BASE_URL   = "http://www.crssoft.co.uk/CustomOrderImages/"

PX_PER_CM = 320 / 2.54
CANVAS = {
    "adulttshirt": {"front":(int(30*PX_PER_CM),int(30*PX_PER_CM)),"back":(int(30*PX_PER_CM),int(30*PX_PER_CM)),"pocket":(int(9*PX_PER_CM),int(9*PX_PER_CM))},
    "kidstshirt":  {"front":(int(23*PX_PER_CM),int(30*PX_PER_CM)),"back":(int(23*PX_PER_CM),int(30*PX_PER_CM))},
    "adulthoodie": {"front":(int(25*PX_PER_CM),int(25*PX_PER_CM)),"back":(int(25*PX_PER_CM),int(25*PX_PER_CM)),"pocket":(int(9*PX_PER_CM),int(9*PX_PER_CM))},
    "babyvest":    {"front":(int(15*PX_PER_CM),int(17*PX_PER_CM))},
    "default":     {"front":(int(30*PX_PER_CM),int(30*PX_PER_CM)),"back":(int(30*PX_PER_CM),int(30*PX_PER_CM))},
}
SKU_MAP = [
    ("AnyTxtAdultHood_","adulthoodie"),("AnyTxtBabyVest_","babyvest"),
    ("AnyTxt","adulttshirt"),("KidsTee_","kidstshirt"),
    ("MenHood_","adulthoodie"),("WmnTee_","adulttshirt"),
    ("MenTee_","adulttshirt"),("BabyVest","babyvest"),("COMenTee_","adulttshirt"),
]
def detect_product(sku):
    for prefix, product in sorted(SKU_MAP, key=lambda x: -len(x[0])):
        if sku.startswith(prefix): return product
    return "default"

def get_img(img_json, img_field):
    if img_json:
        try:
            names = list(json.loads(img_json).values())
            if names: return names[0].strip()
        except: pass
    return (img_field or "").strip() or None

def get_colour(colour_json):
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
        "colour_hex":     get_colour(colours_json),
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

for row in rows:
    oid, sku = row[0], row[1]
    product  = detect_product(sku)
    zones    = {}

    front = make_zone(row[2], row[3], row[4], row[5], row[6], row[7])
    back  = make_zone(row[8], row[9], row[10], row[11], row[12], row[13])
    pi    = get_img(row[14], row[15])
    pp    = (row[16] or "").strip() or None

    if front: zones["front"] = front
    if back:  zones["back"]  = back
    if pi:
        zones["pocket"] = {
            "customer_image": ensure_image(pi),
            "preview_image":  ensure_image(pp),
            "text_lines": [], "font_ps_name": "Arial-BoldMT",
            "font_family": "Arial", "font_style": "Bold", "colour_hex": "#ffffff"
        }

    if not zones:
        print(f"[SKIP] {oid}"); continue

    job = {
        "order_id":    oid,
        "combined":    True,
        "template":    "C:\\Varsany\\template\\combined_template.psd",
        "zones":       zones,
        "output_path": f"C:\\Varsany\\Output\\ps_test\\{oid}.psd",
        "dpi":         320
    }
    (JOBS_DIR / f"{oid}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
    fonts_used = list(set(d['font_family'] for d in zones.values()))
    print(f"[JOB] {oid} | zones:{list(zones.keys())} | fonts:{fonts_used}")

print("\nAll jobs written.")
