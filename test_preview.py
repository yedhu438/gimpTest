"""
test_preview.py
Pick 3 orders that have FrontPreviewImage populated and run them.
Tests that preview images are correctly downloaded and placed as hidden layers.
"""
import sys, os
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')

import pyodbc
from batch_processor import run_batch

DB_SERVER = os.environ.get('DB_SERVER', '')
DB_NAME   = os.environ.get('DB_NAME', 'dbAmazonCustomOrders')
DB_UID    = os.environ.get('DB_UID', '')
DB_PWD    = os.environ.get('DB_PWD', '')

conn = pyodbc.connect(
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={DB_SERVER};DATABASE={DB_NAME};'
    f'UID={DB_UID};PWD={DB_PWD};TrustServerCertificate=yes;'
)
cur = conn.cursor()

# Pick 3 recent orders with FrontPreviewImage populated
cur.execute("""
    SELECT TOP 3
        o.OrderID,
        d.FrontPreviewImage,
        d.FrontImage,
        d.FrontText
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE ISNULL(d.FrontPreviewImage, '') <> ''
    ORDER BY NEWID()
""")
rows = cur.fetchall()
conn.close()

if not rows:
    print("No orders with FrontPreviewImage found.")
    sys.exit(0)

order_ids = []
print("=== Orders selected for preview test ===")
for r in rows:
    print(f"  OrderID      : {r[0]}")
    print(f"  FrontPreview : {r[1]}")
    print(f"  FrontImage   : {r[2] or '(none)'}")
    print(f"  FrontText    : {(r[3] or '')[:60]}")
    print()
    order_ids.append(r[0])

print("=" * 60)
print("Running export (reprocess=True to bypass IsDesignComplete)...")
print("=" * 60)

run_batch(
    order_id_filter = order_ids,
    reprocess       = True,
    upload_nas      = False,
)

print("\nDone.")
