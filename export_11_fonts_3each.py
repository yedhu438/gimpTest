import sys, os, json, shutil, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from pathlib import Path

BASE_URL    = "http://www.crssoft.co.uk/CustomOrderImages/"
CACHE_DIR   = r"C:\gimpTest\Temp\OrderImages"
PLUGIN_DATA = r"C:\Users\yedhu\AppData\Roaming\Adobe\UXP\PluginsStorage\PHSP\27\Developer\com.varsany.automation.worker\PluginData"
IMG_DIR     = PLUGIN_DATA + r"\images"
JOBS_DIR    = PLUGIN_DATA + r"\jobs"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(IMG_DIR,   exist_ok=True)
os.makedirs(JOBS_DIR,  exist_ok=True)

PX_PER_CM = 320 / 2.54
CANVAS = {
    "adulttshirt": {"front":(int(30*PX_PER_CM),int(30*PX_PER_CM))},
    "kidstshirt":  {"front":(int(23*PX_PER_CM),int(30*PX_PER_CM))},
    "adulthoodie": {"front":(int(25*PX_PER_CM),int(25*PX_PER_CM))},
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
    "Permanent Marker":  "PermanentMarker-Regular",
    "Helvetica":         "Helvetica-Bold",
    "Arial":             "ArialMT",
    "No":                "ArialMT",
    "Chewy":             "Chewy-Regular",
    "Lato":              "Lato-Regular",
    "Russo One":         "RussoOne-Regular",
    "Bebas Neue":        "BebasNeue-Regular",
    "Roboto":            "Roboto-Regular",
    "Ultra":             "Ultra-Regular",
    "Fondamento":        "Fondamento-Regular",
    "Abel":              "Abel-Regular",
    "Spidey Font":       "SpiderWebRegular",
    "Spider Web":        "SpiderWebRegular",
    "Paint Font":        "PaintSplashesRainbow",
    "Soccer Army":       "SoccerArmyVer2",
    "Smart Kids":        "SmartKidsRegular",
    "Texture Font":      "SmartKidsRegular",
    "Cozy Winter":       "CozyWinterRegular",
    "Cozy Font":         "CozyWinterRegular",
    "Camoblock":         "CamoBlockRegular",
    "Camo Font":         "CamoBlockRegular",
    "Bouquet Display":   "BouqetDisplay",
    "Bouqet Display":    "BouqetDisplay",
    "Mermaid Font":      "WavemermaidRegular",
    "Wavemermaid":       "WavemermaidRegular",
    "Colorful Blocks":   "ColorfulBlocksRegular",
    "Block Font":        "ColorfulBlocksRegular",
    "Refraction Ray":    "RefractionRayRegular",
    "Reflection Font":   "RefractionRayRegular",
    "Flower Font":       "BouqetDisplay",
    "Football Font":     "SoccerArmyVer2",
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
        if raw.strip().startswith("{"): return json.loads(raw).get("Colour1","#ffffff")
        if raw.strip().startswith("#"): return raw.strip()
    except: pass
    return "#ffffff"

def parse_font(raw):
    if not raw: return None
    try:
        if raw.strip().startswith("{"):
            d = json.loads(raw)
            font = d.get("PremiumFont","").strip()
            if font and font.lower() not in ("no",""):
                return FONT_NAME_MAP.get(font, font), font
        return None, None
    except: return None, None

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
    SELECT TOP 500 o.OrderID, o.SKU,
        d.FrontText, d.FrontFonts, d.FrontColours,
        d.FrontImageJSON, d.FrontImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder=d.idCustomOrder
    WHERE d.FrontFonts IS NOT NULL
      AND d.FrontFonts LIKE '%PremiumFont%'
      AND d.FrontFonts NOT LIKE '%"PremiumFont":""%'
      AND d.FrontFonts NOT LIKE '%"PremiumFont":"No"%'
      AND d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != ''
      AND d.FrontText  IS NOT NULL AND LTRIM(RTRIM(d.FrontText))  != ''
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()
conn.close()

# Group by font â€” 3 orders per font, max 11 fonts
font_groups = {}
for row in rows:
    ps_name, db_name = parse_font(row[3])
    if not ps_name or not db_name: continue
    if db_name not in font_groups:
        font_groups[db_name] = []
    if len(font_groups[db_name]) < 3:
        font_groups[db_name].append((row, ps_name))

# Take up to 11 fonts
selected_fonts = list(font_groups.keys())[:11]
print(f"Found {len(selected_fonts)} premium fonts with 3+ orders each\n")

total = 0
for db_name in selected_fonts:
    orders = font_groups[db_name]
    print(f"  â”€â”€ {db_name} ({FONT_NAME_MAP.get(db_name, db_name)}) â”€â”€")
    count = 0
    for row, ps_name in orders:
        oid, sku = row[0], row[1]
        ft  = (row[2] or "").strip()
        fc  = parse_colour(row[4])
        fi  = get_img(row[5], row[6])
        if not fi or not ft: continue
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
                "font_name":      ps_name,
                "colour_hex":     fc
            }},
            "output_path": f"{oid}_front.psd",
            "canvas_w_px": w, "canvas_h_px": h, "dpi": 320
        }
        Path(JOBS_DIR, f"{oid}_front.json").write_text(json.dumps(job,indent=2),encoding="utf-8")
        count += 1
        total += 1
        print(f"    [{count}] {oid} | text={ft[:35]} | colour={fc}")
    print()

print(f"Total: {total} jobs queued across {len(selected_fonts)} fonts.")
print("UXP plugin will process automatically.")


