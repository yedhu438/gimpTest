import sys
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection

ORDER_ID = "204-0742290-3536308"

conn = get_connection()
cur = conn.cursor()

# tblCustomOrder
cur.execute("""
    SELECT * FROM tblCustomOrder WHERE OrderID = ?
""", ORDER_ID)
cols_o = [d[0] for d in cur.description]
rows_o = cur.fetchall()

print(f"{'='*72}")
print(f"tblCustomOrder — {ORDER_ID}")
print(f"{'='*72}")
for row in rows_o:
    for col, val in zip(cols_o, row):
        print(f"  {col:<30} : {val}")
    print()

# tblCustomOrderDetails
cur.execute("""
    SELECT d.* FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID = ?
    ORDER BY d.DateAdd
""", ORDER_ID)
cols_d = [d[0] for d in cur.description]
rows_d = cur.fetchall()

print(f"{'='*72}")
print(f"tblCustomOrderDetails — {len(rows_d)} row(s)")
print(f"{'='*72}")
for i, row in enumerate(rows_d, 1):
    print(f"\n--- Row {i} ---")
    for col, val in zip(cols_d, row):
        if val is not None and str(val).strip():
            print(f"  {col:<35} : {val}")

conn.close()
