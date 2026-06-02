import sys, json, urllib.request
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
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

def get_colour(c):
    if c:
        try:
            d = json.loads(c); v = d.get("Colour1","").strip()
            if v.startswith("#"): return v
        except: pass
    return "#ffffff"

def ensure_image(fname):
    if not fname: return None
    dest = IMAGES_DIR / fname
    if not (dest.exists() and dest.stat().st_size > 0):
        try: urllib.request.urlretrieve(BASE_URL + fname, dest); print(f"  Downloaded: {fname}")
        except Exception as e: print(f"  FAILED: {fname}"); return None
    return fname

conn = get_connection()
cur  = conn.cursor()
# Get 2 orders — one with back, one with premium font
cur.execute("""
    SELECT TOP 2 o.OrderID, o.SKU,
        d.FrontImageJSON, d.FrontImage, d.FrontText, d.FrontFonts, d.FrontColours, d.FrontPreviewImage,
        d.BackImageJSON,  d.BackImage,  d.BackText,  d.BackFonts,  d.BackColours,  d.BackPreviewImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE (d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != '')
    AND o.DateAdd >= DATEADD(day, -30, GETDATE())
    AND (d.BackImage IS NOT NULL AND LTRIM(RTRIM(d.BackImage)) != '')
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()
conn.close()

for row in rows:
    oid = row[0]
    zones = {}
    ps,fam,sty = get_font_info(row[5])
    fi = get_img(row[2],row[3]); ft = (row[4] or "").strip()
    if fi or ft:
        zones["front"] = {"customer_image":ensure_image(fi),"preview_image":ensure_image((row[7] or "").strip() or None),
            "text_lines":[l.strip() for l in ft.split("\n") if l.strip()] if ft else [],
            "font_ps_name":ps,"font_family":fam,"font_style":sty,"colour_hex":get_colour(row[6])}
    ps2,fam2,sty2 = get_font_info(row[11])
    bi = get_img(row[8],row[9]); bt = (row[10] or "").strip()
    if bi or bt:
        zones["back"] = {"customer_image":ensure_image(bi),"preview_image":ensure_image((row[13] or "").strip() or None),
            "text_lines":[l.strip() for l in bt.split("\n") if l.strip()] if bt else [],
            "font_ps_name":ps2,"font_family":fam2,"font_style":sty2,"colour_hex":get_colour(row[12])}
    if not zones: continue
    job = {"order_id":oid,"combined":True,"template":"C:\\Varsany\\template\\combined_template.psd",
           "zones":zones,"output_path":f"C:\\Varsany\\Output\\ps_test\\{oid}.psd","dpi":320}
    (JOBS_DIR/f"{oid}.json").write_text(json.dumps(job,indent=2),encoding="utf-8")
    print(f"[JOB] {oid} | zones:{list(zones.keys())} | fonts:{fam},{fam2}")
print("Done.")
