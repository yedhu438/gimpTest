import db, sys
sys.path.insert(0, r'C:\gimpTest')
from batch_processor import parse_is_premium_font, _is_svg_only_font, parse_font

conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT TOP 50 o.OrderID, o.SKU, d.FrontFonts, d.BackFonts, d.PocketFonts,
           d.FrontImage, d.BackImage, d.PocketImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON d.idCustomOrder = o.idCustomOrder
    WHERE (ISNULL(d.FrontImage,'') != '' OR ISNULL(d.BackImage,'') != '' OR ISNULL(d.PocketImage,'') != '')
      AND (ISNULL(d.FrontFonts,'') != '' OR ISNULL(d.BackFonts,'') != '' OR ISNULL(d.PocketFonts,'') != '')
    ORDER BY o.DateAdd DESC
""")
rows = cursor.fetchall()
conn.close()

for r in rows:
    order_id, sku, ff, bf, pf, fi, bi, pi = r
    for fonts_raw, img in [(ff, fi), (bf, bi), (pf, pi)]:
        if not img:
            continue
        font = parse_font(fonts_raw or "")
        if _is_svg_only_font(font) or parse_is_premium_font(fonts_raw or ""):
            print(f"{order_id}  SKU={sku}  font={font}  img={str(img)[:60]}")
            break

