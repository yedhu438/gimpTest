import sys, json, urllib.request
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_ps_font_name
from pathlib import Path

JOBS_DIR   = Path(r"C:\Varsany\jobs")
IMAGES_DIR = Path(r"C:\Varsany\Temp\OrderImages")
BASE_URL   = "http://www.crssoft.co.uk/CustomOrderImages/"

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
        urllib.request.urlretrieve(BASE_URL + fname, dest)
    return fname

conn = get_connection()
cur  = conn.cursor()
cur.execute("""
    SELECT o.OrderID, d.FrontImageJSON, d.FrontImage, d.FrontText, d.FrontFonts, d.FrontColours,
           d.BackImageJSON, d.BackImage, d.BackText, d.BackFonts, d.BackColours
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID = '202-8958969-0276362'
""")
r = cur.fetchone()
conn.close()

for zone_name, img_json, img_field, text, fonts, colours in [
    ("front", r[1], r[2], r[3], r[4], r[5]),
    ("back",  r[6], r[7], r[8], r[9], r[10]),
]:
    fi = get_img(img_json, img_field)
    ft = (text or "").strip()
    if not fi and not ft: continue
    job = {
        "order_id":    f"202-8958969-0276362_{zone_name}",
        "template":    "C:\\Varsany\\template\\adulttshirt.psd",
        "zones": { zone_name: {
            "customer_image": ensure_image(fi),
            "text_lines":     [l.strip() for l in ft.split("\n") if l.strip()] if ft else [],
            "font_ps_name":   get_ps_font_name(fonts),
            "colour_hex":     get_colour(colours),
        }},
        "output_path": f"C:\\Varsany\\Output\\ps_test\\202-8958969-0276362_{zone_name}.psd",
        "canvas_w_px": 3779, "canvas_h_px": 3779, "dpi": 320
    }
    (JOBS_DIR / f"202-8958969-0276362_{zone_name}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
    print(f"Queued {zone_name}: font={get_ps_font_name(fonts)} colour={get_colour(colours)}")
