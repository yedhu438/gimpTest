import sys
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection

conn = get_connection()
cur = conn.cursor()

# Count across entire DB
cur.execute("""
    SELECT
        SUM(CASE WHEN PocketTopazImage IS NOT NULL AND LEN(LTRIM(RTRIM(PocketTopazImage))) > 0 THEN 1 ELSE 0 END) AS pocket_count,
        SUM(CASE WHEN SleeveTopazImage IS NOT NULL AND LEN(LTRIM(RTRIM(SleeveTopazImage))) > 0 THEN 1 ELSE 0 END) AS sleeve_count,
        COUNT(*) AS total_rows
    FROM tblCustomOrderDetails
""")
r = cur.fetchone()
print(f"Total rows in tblCustomOrderDetails : {r[2]}")
print(f"PocketTopazImage populated           : {r[0]}")
print(f"SleeveTopazImage populated           : {r[1]}")

# Show samples
for col, label in [("PocketTopazImage", "Pocket"), ("SleeveTopazImage", "Sleeve")]:
    cur.execute(f"""
        SELECT TOP 10 o.OrderID, o.SKU, d.{col}
        FROM tblCustomOrderDetails d
        JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
        WHERE d.{col} IS NOT NULL AND LEN(LTRIM(RTRIM(d.{col}))) > 0
        ORDER BY d.DateAdd DESC
    """)
    rows = cur.fetchall()
    if rows:
        print(f"\nSample {label}TopazImage entries (top 10):")
        for row in rows:
            print(f"  {row[0]}  ({row[1]})  {row[2]}")
    else:
        print(f"\n{label}TopazImage : NO entries found in entire database")

conn.close()
