import sys, os
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')
import pyodbc

ORDER_ID = sys.argv[1] if len(sys.argv) > 1 else '206-7243076-3097949'

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=' + os.environ['DB_SERVER'] + ';'
    'DATABASE=' + os.environ['DB_NAME'] + ';'
    'UID=' + os.environ['DB_UID'] + ';'
    'PWD=' + os.environ['DB_PWD'] + ';'
    'TrustServerCertificate=yes;'
)
cur = conn.cursor()

# Reset Topaz_Processed so the daemon picks it up again
cur.execute("""
    UPDATE tblCustomOrderDetails
    SET Topaz_Processed = 0
    FROM tblCustomOrderDetails d
    JOIN tblCustomOrder o ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID = ?
""", ORDER_ID)
conn.commit()
print(f"Requeued: {ORDER_ID}  (rows updated: {cur.rowcount})")
conn.close()
