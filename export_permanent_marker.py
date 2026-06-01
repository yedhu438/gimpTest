import sys, os, json, shutil, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from pathlib import Path

BASE_URL    = "http://www.crssoft.co.uk/CustomOrderImages/"
CACHE_DIR   = r"C:\Varsany\Temp\OrderImages"
PLUGIN_DATA = r"C:\Users\yedhu\AppData\Roaming\Adobe\UXP\PluginsStorage\PHSP\27\Developer\com.varsany.automation.worker\PluginData"
IMG_DIR     = PLUGIN_DATA + r"\images"
JOBS_DIR    = PLUGIN_DATA + r"\jobs"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(IMG_DIR,   exist_ok=True)
os.makedirs(JOBS_DIR,  exist_ok=True)

PX_PER_CM = 320 / 2.54
CANVAS = {
    "adulttshirt": {"front":(int(30*PX_PER_CM),int(30*PX_PER_CM)),"back":(int(30*PX_PER_CM),int(30*PX_PER_CM))},
    "kidstshirt":  {"front":(int(23*PX_PER_CM),int(30*PX_PER_CM)),"back":(int(23*PX_PER_CM),int(30*PX_PER_CM))},
    "adulthoodie": {"front":(int(25*PX_PER_CM),int(25*PX_PER_CM)),"back":(int(25*PX_PER_CM),int(25*PX_PER_CM))},
    "babyvest":    {"front":(int(15*PX_PER_CM),int(17*PX_PER_CM))},
    "default":     {"front":(int(30*PX_PER_CM),int(30*PX_PER_CM))},
}
SKU_MAP = [
    ("MenTee_","adulttshirt"),("WmnTee_","adulttshirt"),("AnyTxt","adulttshirt"),
    ("KidsTee_","kidstshirt"),("AnyTxtAdultHood_","adulthoodie"),("MenHood_","adulthoodie"),
    ("AnyTxtBabyVest_","babyvest"),("BabyVest","babyvest"),
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

def parse_colour(raw):
    if not raw: return "#ffffff"
    try:
        raw = raw.strip()
        if raw.startswith("{"):
            d = json.loads(raw)
            return d.get("Colour1") or "#ffffff"
        if raw.startswith("#"): return raw
    except: pass
    return "#ffffff"

def ensure_image(fname):
    if not fname: return None
    dest_plugin = os.path.join(IMG_DIR, fname)
    if os.path.exists(dest_plugin) and os.path.getsize(dest_plugin) > 10000:
        return fname
    cache_path = os.path.join(CACHE_DIR, fname)
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 10000:
        shutil.copy2(cache_path, dest_plugin)
        return fname
    try:
        urllib.request.urlretrieve(BASE_URL + fname, dest_plugin)
        if os.path.getsize(dest_plugin) > 10000:
            shutil.copy2(dest_plugin, cache_path)
            return fname
        os.remove(dest_plugin)
        return None
    except: return None

conn = get_connection()
cur  = conn.cursor()
cur.execute("""
    SELECT TOP 10 o.OrderID, o.SKU,
        d.FrontText, d.FrontFonts, d.FrontColours,
        d.FrontImageJSON, d.FrontImage,
        d.BackImageJSON, d.BackImage, d.BackText
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder=d.idCustomOrder
    WHERE d.FrontFonts LIKE '%Permanent Marker%'
      AND d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != ''
      AND d.FrontText  IS NOT NULL AND LTRIM(RTRIM(d.FrontText))  != ''
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()
conn.close()

print(f"Found {len(rows)} orders with Permanent Marker font\n")

count = 0
for row in rows:
    oid, sku = row[0], row[1]
    canvas = CANVAS.get(detect_product(sku), CANVAS["default"])
    ft = (row[2] or "").strip()
    fc = parse_colour(row[4])
    fi = get_img(row[5], row[6])
    bi = get_img(row[7], row[8])
    bt = (row[9] or "").strip()

    if not fi: continue
    fi_dest = ensure_image(fi)
    if not fi_dest: continue

    # Front zone
    w, h = canvas.get("front", (3780,3780))
    job = {
        "order_id":    f"{oid}_front",
        "template":    "adulttshirt.psd",
        "zones":       {"front": {
            "customer_image": fi_dest,
            "text_lines":     [l.strip() for l in ft.split("\n") if l.strip()],
            "font_name":      "PermanentMarker-Regular",
            "colour_hex":     fc
        }},
        "output_path": f"{oid}_front.psd",
        "canvas_w_px": w, "canvas_h_px": h, "dpi": 320
    }
    Path(JOBS_DIR, f"{oid}_front.json").write_text(json.dumps(job,indent=2),encoding="utf-8")
    count += 1
    print(f"  [{count:02d}] {oid} ({sku}) text={ft[:40]} colour={fc}")

    # Back zone if exists
    if bi:
        bi_dest = ensure_image(bi)
        if bi_dest:
            w2, h2 = canvas.get("back", canvas.get("front",(3780,3780)))
            job2 = {
                "order_id":    f"{oid}_back",
                "template":    "adulttshirt.psd",
                "zones":       {"back": {
                    "customer_image": bi_dest,
                    "text_lines":     [l.strip() for l in bt.split("\n") if l.strip()] if bt else [],
                    "font_name":      "PermanentMarker-Regular",
                    "colour_hex":     fc
                }},
                "output_path": f"{oid}_back.psd",
                "canvas_w_px": w2, "canvas_h_px": h2, "dpi": 320
            }
            Path(JOBS_DIR, f"{oid}_back.json").write_text(json.dumps(job2,indent=2),encoding="utf-8")

print(f"\n{count} orders queued. UXP plugin will process them automatically.")
