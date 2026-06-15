import sys, os
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')
from db import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT TOP 3
        o.OrderID, o.SKU, CONVERT(varchar, o.DateAdd, 120) as DateAdd,
        d.PrintLocation, d.FrontText, d.FrontFonts, d.FrontColours,
        d.FrontImage, d.FrontPreviewImage, d.BackText, d.BackImage,
        d.IsDesignComplete, d.IsOrderProcess
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE o.DateAdd >= DATEADD(day, -7, GETDATE())
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()
cols = [c[0] for c in cur.description]

print(f"Retrieved {len(rows)} orders (last 7 days)\n")
for row in rows:
    print("=" * 60)
    for col, val in zip(cols, row):
        if val not in (None, '', 0, False):
            print(f"  {col}: {str(val)[:100]}")
conn.close()
print("\nDone.")
