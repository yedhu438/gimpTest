import sys, os, json, shutil, urllib.request
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
    "default":     {"front":(int(30*PX_PER_CM),int(30*PX_PER_CM)),"back":(int(30*PX_PER_CM),int(30*PX_PER_CM))},
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
            return d.get("Colour1") or d.get("colour1") or "#ffffff"
        if raw.startswith("#"): return raw
    except: pass
    return "#ffffff"

FONT_NAME_MAP = {
    "Helvetica":        "Helvetica",
    "Helvetica Neue":   "Helvetica",
    "Arial":            "ArialMT",
    "Arial Bold":       "Arial-BoldMT",
    "No":               "ArialMT",
    "Chewy":            "Chewy-Regular",
    "Lato":             "Lato-Regular",
    "Russo One":        "RussoOne-Regular",
    "Bebas Neue":       "BebasNeue-Regular",
    "Permanent Marker": "PermanentMarker-Regular",
    "Roboto":           "Roboto-Regular",
    "Ultra":            "Ultra-Regular",
    "Fondamento":       "Fondamento-Regular",
    "Abel":             "Abel-Regular",
    "Spidey Font":      "SpiderWeb",
    "Spider Web":       "SpiderWeb",
    "Paint Font":       "PaintSplashesRainbow",
    "Soccer Army":      "SoccerArmy",
    "Smart Kids":       "SmartKids",
    "Cozy Winter":      "CozyWinter",
    "Camoblock":        "Camoblock",
    "Bouquet Display":  "BouqetDisplay",
    "Wavemermaid":      "Wavemermaid",
}

def parse_font(raw):
    if not raw: return "ArialMT"
    try:
        raw = raw.strip()
        if raw.startswith("{"):
            d = json.loads(raw)
            font = d.get("PremiumFont") or d.get("NormalFont") or "Arial"
        else:
            font = raw
        return FONT_NAME_MAP.get(font, font)
    except: pass
    return "ArialMT"

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
        size = os.path.getsize(dest_plugin)
        if size > 10000:
            shutil.copy2(dest_plugin, cache_path)
            return fname
        else:
            os.remove(dest_plugin)
            return None
    except: return None

def write_job(oid, zone_name, zone_data, canvas):
    w, h = canvas.get(zone_name, canvas.get("front",(3780,3780)))
    job = {
        "order_id":    f"{oid}_{zone_name}",
        "template":    "adulttshirt.psd",
        "zones":       {zone_name: zone_data},
        "output_path": f"{oid}_{zone_name}.psd",
        "canvas_w_px": w, "canvas_h_px": h, "dpi": 320
    }
    Path(JOBS_DIR, f"{oid}_{zone_name}.json").write_text(json.dumps(job,indent=2),encoding="utf-8")

conn = get_connection()
cur  = conn.cursor()

# â”€â”€ BATCH 1: 10 orders with images (any font) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("=" * 60)
print("BATCH 1: 10 orders with customer images")
print("=" * 60)
cur.execute("""
    SELECT TOP 30 o.OrderID, o.SKU,
        d.FrontImageJSON, d.FrontImage, d.FrontText, d.FrontFonts, d.FrontColours,
        d.BackImageJSON,  d.BackImage,  d.BackText
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder=d.idCustomOrder
    WHERE d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage))!=''
      AND d.FrontText  IS NOT NULL AND LTRIM(RTRIM(d.FrontText)) !=''
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()

count = 0
for row in rows:
    if count >= 10: break
    oid, sku = row[0], row[1]
    canvas = CANVAS.get(detect_product(sku), CANVAS["default"])
    fi = get_img(row[2], row[3])
    ft = (row[4] or "").strip()
    ff = parse_font(row[5]) or "Arial Bold"
    fc = parse_colour(row[6])
    if not fi or not ft: continue
    fi_dest = ensure_image(fi)
    if not fi_dest: continue
    write_job(oid, "front", {"customer_image":fi_dest,"text_lines":[l.strip() for l in ft.split("\n") if l.strip()],"font_name":ff,"colour_hex":fc}, canvas)
    bi = get_img(row[7], row[8])
    bt = (row[9] or "").strip()
    if bi:
        bi_dest = ensure_image(bi)
        if bi_dest:
            write_job(oid, "back", {"customer_image":bi_dest,"text_lines":[l.strip() for l in bt.split("\n") if l.strip()],"font_name":"Arial Bold","colour_hex":"#ffffff"}, canvas)
    count += 1
    print(f"  [{count:02d}] {oid} ({sku}) font={ff}")

# â”€â”€ BATCH 2: 10 orders with PREMIUM fonts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print()
print("=" * 60)
print("BATCH 2: 10 orders with premium fonts")
print("=" * 60)
cur.execute("""
    SELECT TOP 50 o.OrderID, o.SKU,
        d.FrontImageJSON, d.FrontImage, d.FrontText, d.FrontFonts, d.FrontColours
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder=d.idCustomOrder
    WHERE d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage))!=''
      AND d.FrontText  IS NOT NULL AND LTRIM(RTRIM(d.FrontText)) !=''
      AND d.FrontFonts IS NOT NULL AND d.FrontFonts LIKE '%PremiumFont%'
    ORDER BY o.DateAdd DESC
""")
rows2 = cur.fetchall()
conn.close()

count2 = 0
for row in rows2:
    if count2 >= 10: break
    oid, sku = row[0], row[1]
    canvas = CANVAS.get(detect_product(sku), CANVAS["default"])
    fi = get_img(row[2], row[3])
    ft = (row[4] or "").strip()
    ff = parse_font(row[5])
    fc = parse_colour(row[6])
    if not fi or not ft or not ff: continue
    fi_dest = ensure_image(fi)
    if not fi_dest: continue
    write_job(oid, "front", {"customer_image":fi_dest,"text_lines":[l.strip() for l in ft.split("\n") if l.strip()],"font_name":ff,"colour_hex":fc}, canvas)
    count2 += 1
    print(f"  [{count2:02d}] {oid} ({sku}) PREMIUM font={ff}")

print(f"\nTotal jobs written: {count + count2} orders queued.")
print("UXP plugin will process them automatically.")

