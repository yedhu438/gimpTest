"""
find_front_back_orders.py  —  list unprocessed orders with both front and back images.
Usage:  python find_front_back_orders.py
"""
import os, pyodbc

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

_srv = os.environ.get("DB_SERVER", r"localhost\SQLEXPRESS")
_db  = os.environ.get("DB_NAME",   "dbAmazonCustomOrders")
_uid = os.environ.get("DB_UID",    "")
_pwd = os.environ.get("DB_PWD",    "")

if _uid and _pwd:
    CONN = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={_srv};DATABASE={_db};UID={_uid};PWD={_pwd};TrustServerCertificate=yes;"
else:
    CONN = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={_srv};DATABASE={_db};Trusted_Connection=yes;TrustServerCertificate=yes;"

conn = pyodbc.connect(CONN)
cur  = conn.cursor()
cur.execute("""
    SELECT TOP 5
        o.OrderID, o.SKU,
        d.FrontImage, d.BackImage, d.FrontText, d.BackText
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE
        ISNULL(d.FrontImage, '') <> '' AND
        ISNULL(d.BackImage,  '') <> '' AND
        d.FrontImage LIKE '63%' AND
        d.BackImage  LIKE '63%' AND
        (d.IsDesignComplete = 0 OR d.IsDesignComplete IS NULL)
    ORDER BY o.DateAdd DESC
""")
rows = cur.fetchall()
print(f"Found {len(rows)} orders with front + back images:\n")
for r in rows:
    print(f"  OrderID : {r[0]}  SKU: {r[1]}")
    print(f"  Front   : {r[2]}  Back: {r[3]}")
    if r[4]: print(f"  FText   : {r[4].strip()}")
    if r[5]: print(f"  BText   : {r[5].strip()}")
    print()
conn.close()
