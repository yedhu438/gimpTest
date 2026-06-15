import pyodbc, os, sys
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=' + os.environ['DB_SERVER'] + ';'
    'DATABASE=' + os.environ['DB_NAME'] + ';'
    'UID=' + os.environ['DB_UID'] + ';'
    'PWD=' + os.environ['DB_PWD'] + ';'
    'TrustServerCertificate=yes;'
)
cur = conn.cursor()

# How many orders have Topaz columns populated?
cur.execute("""
    SELECT
        COUNT(*) AS total_orders,
        SUM(CASE WHEN IsTopazImageProcess = 1 THEN 1 ELSE 0 END) AS topaz_enabled,
        SUM(CASE WHEN ISNULL(FrontTopazImage,'') <> '' THEN 1 ELSE 0 END) AS has_front_topaz,
        SUM(CASE WHEN ISNULL(BackTopazImage,'')  <> '' THEN 1 ELSE 0 END) AS has_back_topaz
    FROM tblCustomOrderDetails
""")
row = cur.fetchone()
print("=== Topaz Column Population ===")
print(f"  Total order details   : {row[0]}")
print(f"  IsTopazImageProcess=1 : {row[1]}")
print(f"  FrontTopazImage set   : {row[2]}")
print(f"  BackTopazImage set    : {row[3]}")

# Show sample of what FrontTopazImage actually contains
print()
print("=== Sample FrontTopazImage values ===")
cur.execute("""
    SELECT TOP 5 o.OrderID, d.FrontImage, d.FrontTopazImage, d.IsTopazImageProcess
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE ISNULL(d.FrontTopazImage,'') <> ''
""")
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  OrderID            : {r[0]}")
        print(f"  FrontImage         : {r[1]}")
        print(f"  FrontTopazImage    : {r[2]}")
        print(f"  IsTopazImageProcess: {r[3]}")
        print()
else:
    print("  (no rows have FrontTopazImage populated)")

conn.close()
