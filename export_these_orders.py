import sys, os
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')

from collections import defaultdict
from db import get_connection
from shared import write_jobs

ORDER_IDS = [
    '202-0171858-2639527',
    '205-2485658-0653912',
    '203-7566644-8139520',
]

placeholders = ','.join(f"'{o}'" for o in ORDER_IDS)

conn = get_connection()
cur  = conn.cursor()
cur.execute(f"""
    SELECT o.OrderID, o.SKU, o.DateAdd,
           d.FrontImageJSON, d.FrontImage, d.FrontText,
           d.FrontFonts, d.FrontColours, d.FrontPreviewImage,
           d.BackImageJSON, d.BackImage, d.BackText,
           d.BackFonts, d.BackColours, d.BackPreviewImage,
           d.PocketImageJSON, d.PocketImage, d.PocketPreviewImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID IN ({placeholders})
    ORDER BY o.OrderID, o.SKU
""")
rows = cur.fetchall()
conn.close()

orders = defaultdict(list)
for row in rows:
    orders[row[0]].append(row)

print(f"Found {len(rows)} rows across {len(orders)} orders\n")
written, skipped = write_jobs(orders)
print(f"\nDone: {written} jobs written, {skipped} skipped.")
