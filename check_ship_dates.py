import sys
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection

conn = get_connection()
cur = conn.cursor()

cur.execute("""
    SELECT
        CAST(o.DateAdd AS DATE)             AS order_date,
        CAST(o.ConvertedShipByDate AS DATE) AS ship_date,
        COUNT(*)                            AS order_count
    FROM tblCustomOrder o
    WHERE CAST(o.DateAdd AS DATE) = '2026-06-24'
    GROUP BY CAST(o.DateAdd AS DATE), CAST(o.ConvertedShipByDate AS DATE)
    ORDER BY ship_date
""")
rows = cur.fetchall()
print(f"{'Order Date':<14} {'Ship By Date':<14} {'Count':>6}")
print("-" * 36)
for order_date, ship_date, count in rows:
    print(f"{str(order_date):<14} {str(ship_date):<14} {count:>6}")

conn.close()
