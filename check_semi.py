import sys; sys.path.insert(0, r'C:\gimpTest')
from db import get_connection
conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT o.OrderID, o.SKU, d.FrontText, d.FrontTextJSON
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE d.CustomizationCategory = 'Semicustomized'
    AND CAST(o.DateAdd AS DATE) = CAST(GETDATE() AS DATE)
    ORDER BY o.DateAdd
""")
rows = cur.fetchall()
print(f'Total semicustomized orders today: {len(rows)}')
for r in rows:
    print(f'  {r[0]}  SKU={r[1]}  Text={r[2]}  JSON={r[3]}')
conn.close()
