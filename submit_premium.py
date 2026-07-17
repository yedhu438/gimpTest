import sys, json, urllib.request
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from font_map import get_font_info
from pathlib import Path

JOBS_DIR   = Path(r"C:\gimpTest\jobs")
IMAGES_DIR = Path(r"C:\gimpTest\Temp\OrderImages")
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
        try:
            urllib.request.urlretrieve(BASE_URL + fname, dest)
            print(f"  Downloaded: {fname}")
        except Exception as e:
            print(f"  FAILED: {fname} — {e}")
            return None
    return fname

conn = get_connection()
cur  = conn.cursor()
# Get orders with premium fonts specifically
cur.execute("""
    SELECT TOP 5 o.OrderID,
        d.FrontImageJSON, d.FrontImage, d.FrontText, d.FrontFonts, d.FrontColours,
        d.BackImageJSON,  d.BackImage,  d.BackText,  d.BackFonts,  d.BackColours
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE (d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != '')
    AND (
        d.FrontFonts LIKE '%Spidey%' OR d.FrontFonts LIKE '%Paint%' OR
        d.FrontFonts LIKE '%Block%'  OR d.FrontFonts LIKE '%Camo%'  OR
        d.FrontFonts LIKE '%Cozy%'   OR d.FrontFonts LIKE '%Mermaid%' OR
        d.FrontFonts LIKE '%Football%' OR d.FrontFonts LIKE '%Flower%' OR
        d.FrontFonts LIKE '%Reflection%' OR d.FrontFonts LIKE '%Texture%'
    )
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()
conn.close()

print(f"Found {len(rows)} orders with premium fonts.\n")
for row in rows:
    oid = row[0]
    zones = {}
    fi = get_img(row[1], row[2]); ft = (row[3] or "").strip()
    ps, fam, sty = get_font_info(row[4])
    if fi or ft:
        zones["front"] = {"customer_image": ensure_image(fi),
            "text_lines": [l.strip() for l in ft.split("\n") if l.strip()] if ft else [],
            "font_ps_name": ps, "font_family": fam, "font_style": sty, "colour_hex": get_colour(row[5])}
    bi = get_img(row[6], row[7]); bt = (row[8] or "").strip()
    ps2, fam2, sty2 = get_font_info(row[9])
    if bi or bt:
        zones["back"] = {"customer_image": ensure_image(bi),
            "text_lines": [l.strip() for l in bt.split("\n") if l.strip()] if bt else [],
            "font_ps_name": ps2, "font_family": fam2, "font_style": sty2, "colour_hex": get_colour(row[10])}
    if not zones: continue
    job = {"order_id": oid, "combined": True,
        "template": "C:\\gimpTest\\template\\combined_template.psd",
        "zones": zones, "output_path": f"C:\\gimpTest\\Output\\ps_test\\{oid}.psd", "dpi": 320}
    (JOBS_DIR / f"{oid}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
    print(f"[PREMIUM JOB] {oid} | fonts:{fam} | zones:{list(zones.keys())}")
print("Done.")
