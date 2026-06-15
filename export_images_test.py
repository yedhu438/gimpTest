"""
export_images_test.py
Export 5 random orders that have customer images, from a given date.
"""
import sys, random
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')

import pyodbc, os
from batch_processor import run_batch

# ── Config ────────────────────────────────────────────────────────────────────
DATE   = '2026-06-10'
PICK   = 5
# ─────────────────────────────────────────────────────────────────────────────

def get_image_order_ids(date):
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.environ["DB_SERVER"]};'
        f'DATABASE={os.environ["DB_NAME"]};'
        f'UID={os.environ["DB_UID"]};'
        f'PWD={os.environ["DB_PWD"]};'
        'TrustServerCertificate=yes;'
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT o.OrderID
        FROM tblCustomOrder o
        JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
        WHERE CAST(o.DateAdd AS DATE) = ?
          AND (ISNULL(d.FrontImage,'')  <> ''
            OR ISNULL(d.BackImage,'')   <> ''
            OR ISNULL(d.PocketImage,'') <> ''
            OR ISNULL(d.SleeveImage,'') <> '')
        ORDER BY NEWID()
    """, date)
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids

print(f"Fetching image orders for {DATE}...")
all_ids = get_image_order_ids(DATE)
print(f"Found {len(all_ids)} image orders on {DATE}")

if not all_ids:
    print("No image orders found for this date.")
    sys.exit(0)

# ORDER BY NEWID() already randomises; take first PICK
picked = all_ids[:PICK]
print(f"Randomly selected {len(picked)} orders:")
for i, oid in enumerate(picked, 1):
    print(f"  {i}. {oid}")

print()
print("=" * 60)
print(f"Running export...")
print("=" * 60)

run_batch(
    order_id_filter = picked,
    upload_nas      = False,
    reprocess       = True,
)

print("Done.")
