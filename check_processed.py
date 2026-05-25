from db import get_connection
conn = get_connection()
cur  = conn.cursor()
cur.execute("""
    SELECT TOP 20
        o.OrderID,
        o.SKU,
        d.Processed_Orders,
        d.ProcessBy,
        d.ProcessTime
    FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE d.Processed_Orders = 'Completed'
    ORDER BY d.ProcessTime DESC
""")
rows = cur.fetchall()
if rows:
    print(f"{'OrderID':<25} {'SKU':<35} {'Status':<12} {'ProcessedBy':<20} {'Time'}")
    print("-" * 105)
    for r in rows:
        print(f"{str(r[0]):<25} {str(r[1]):<35} {str(r[2]):<12} {str(r[3]):<20} {str(r[4])}")
else:
    print("No orders marked Completed yet — waiting for next automation run.")
conn.close()
