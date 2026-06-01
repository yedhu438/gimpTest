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

FONT_NAME_MAP = {
    "Permanent Marker": "PermanentMarker-Regular",
    "Helvetica":        "Helvetica",
    "Helvetica Neue":   "Helvetica",
    "Arial":            "ArialMT",
    "Arial Bold":       "Arial-BoldMT",
    "No":               "ArialMT",
    "Chewy":            "Chewy-Regular",
    "Lato":             "Lato-Regular",
    "Russo One":        "RussoOne-Regular",
    "Bebas Neue":       "BebasNeue-Regular",
    "Roboto":           "Roboto-Regular",
    "Ultra":            "Ultra-Regular",
    "Fondamento":       "Fondamento-Regular",
    "Abel":             "Abel-Regular",
    "Spidey Font":      "SpiderWebRegular",
    "Spider Web":       "SpiderWebRegular",
    "Paint Font":       "PaintSplashesRainbow",
    "Soccer Army":      "SoccerArmyVer2",
    "Smart Kids":       "SmartKidsRegular",
    "Cozy Winter":      "CozyWinterRegular",
    "Camoblock":        "CamoBlockRegular",
    "Camo Font":        "CamoBlockRegular",
    "Bouquet Display":  "BouqetDisplay",
    "Bouqet Display":   "BouqetDisplay",
    "Wavemermaid":      "WavemermaidRegular",
    "Colorful Blocks":  "ColorfulBlocksRegular",
    "Refraction Ray":   "RefractionRayRegular",
}

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
        if raw.startswith("{"): return json.loads(raw).get("Colour1","#ffffff")
        if raw.startswith("#"): return raw
    except: pass
    return "#ffffff"

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
    except: return "ArialMT"

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
# Get orders with premium fonts â€” exclude Permanent Marker (already done)
cur.execute("""
    SELECT TOP 30 o.OrderID, o.SKU,
        d.FrontText, d.FrontFonts, d.FrontColours,
        d.FrontImageJSON, d.FrontImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder=d.idCustomOrder
    WHERE d.FrontFonts IS NOT NULL
      AND d.FrontFonts LIKE '%PremiumFont%'
      AND d.FrontFonts NOT LIKE '%Permanent Marker%'
      AND d.FrontFonts NOT LIKE '%"PremiumFont":"",%'
      AND d.FrontFonts NOT LIKE '%"PremiumFont":"No"%'
      AND d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != ''
      AND d.FrontText  IS NOT NULL AND LTRIM(RTRIM(d.FrontText))  != ''
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()
conn.close()

# Deduplicate by font name â€” get 10 with different premium fonts
seen_fonts = set()
seen_orders = set()
count = 0

print("Exporting 10 orders with different premium fonts...\n")

for row in rows:
    if count >= 10: break
    oid, sku = row[0], row[1]
    if oid in seen_orders: continue

    ft  = (row[2] or "").strip()
    ff  = parse_font(row[3])
    fc  = parse_colour(row[4])
    fi  = get_img(row[5], row[6])

    if not fi or not ft: continue
    if ff in ("ArialMT", "Arial-BoldMT"): continue  # skip non-premium

    fi_dest = ensure_image(fi)
    if not fi_dest: continue

    canvas = CANVAS.get(detect_product(sku), CANVAS["default"])
    w, h = canvas.get("front", (3780,3780))

    job = {
        "order_id":    f"{oid}_front",
        "template":    "adulttshirt.psd",
        "zones":       {"front": {
            "customer_image": fi_dest,
            "text_lines":     [l.strip() for l in ft.split("\n") if l.strip()],
            "font_name":      ff,
            "colour_hex":     fc
        }},
        "output_path": f"{oid}_front.psd",
        "canvas_w_px": w, "canvas_h_px": h, "dpi": 320
    }
    Path(JOBS_DIR, f"{oid}_front.json").write_text(json.dumps(job,indent=2),encoding="utf-8")
    seen_orders.add(oid)
    seen_fonts.add(ff)
    count += 1
    print(f"  [{count:02d}] {oid} ({sku})")
    print(f"        font={ff} | colour={fc} | text={ft[:40]}")

print(f"\n{count} jobs queued. UXP plugin will process automatically.")
print(f"Fonts used: {sorted(seen_fonts)}")

