import db

ORDER_ID = "202-9500638-1356365"

conn = db.get_connection()
cur = conn.cursor()

cur.execute("SELECT * FROM tblCustomOrder WHERE OrderID=?", ORDER_ID)
cols = [d[0] for d in cur.description]
rows = cur.fetchall()
print("=== tblCustomOrder ===")
for row in rows:
    for c, v in zip(cols, row):
        if v not in (None, ""):
            print(f"  {c:<30} {v}")
    print()

cur.execute("""
    SELECT d.* FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID = ?
    ORDER BY d.idCustomOrderDetails
""", ORDER_ID)
cols2 = [d[0] for d in cur.description]
rows2 = cur.fetchall()
print(f"=== tblCustomOrderDetails ({len(rows2)} rows) ===")
for i, row in enumerate(rows2, 1):
    print(f"\n  -- Row {i} --")
    for c, v in zip(cols2, row):
        if v not in (None, "", 0, False, b'\x00'):
            print(f"  {c:<30} {v}")

conn.close()
