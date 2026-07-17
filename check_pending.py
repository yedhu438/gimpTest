import sys
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT COUNT(*) FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE d.IsDesignComplete = 0
      AND d.IsOrderProcess = 0
""")
print("Pending orders (IsDesignComplete=0):", cur.fetchone()[0])
conn.close()
