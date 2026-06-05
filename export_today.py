import sys
from datetime import date
from collections import defaultdict
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection
from shared import write_jobs

TODAY = date.today().strftime("%Y-%m-%d")

conn = get_connection()
cur  = conn.cursor()
cur.execute(f"""
    SELECT o.OrderID, o.SKU, o.DateAdd,
        d.FrontImageJSON, d.FrontImage, d.FrontText,  d.FrontFonts,  d.FrontColours,  d.FrontPreviewImage,
        d.BackImageJSON,  d.BackImage,  d.BackText,   d.BackFonts,   d.BackColours,   d.BackPreviewImage,
        d.PocketImageJSON,d.PocketImage,d.PocketPreviewImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE (d.FrontImage IS NOT NULL AND LTRIM(RTRIM(d.FrontImage)) != '')
    AND CAST(o.DateAdd AS DATE) = '{TODAY}'
    ORDER BY o.OrderID, o.SKU
""")
rows = cur.fetchall()
conn.close()

orders = defaultdict(list)
for row in rows:
    orders[row[0]].append(row)

print(f"Today: {TODAY} | {len(rows)} rows | {len(orders)} unique orders\n")
written, skipped = write_jobs(orders)
print(f"\nDone: {written} jobs queued, {skipped} skipped.")
