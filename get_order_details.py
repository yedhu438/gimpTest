"""
get_order_details.py  —  print all DB fields for a given OrderID.
Usage:  python get_order_details.py 205-1289169-6851545
"""
import sys, os, pyodbc

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

BASE_URL = "http://www.crssoft.co.uk/CustomOrderImages/"
ORDER_ID = sys.argv[1] if len(sys.argv) > 1 else "205-5204771-7080368"

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
cur.execute("SELECT o.*, d.* FROM tblCustomOrder o JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder WHERE o.OrderID = ?", ORDER_ID)
cols = [c[0] for c in cur.description]
rows = cur.fetchall()
conn.close()

if not rows:
    print(f"Order {ORDER_ID} not found.")
    sys.exit(1)

for row in rows:
    data = dict(zip(cols, row))
    print("=" * 60)
    for col, val in data.items():
        if val is None or val == "":
            continue
        if "Image" in col and val and not str(val).startswith("http"):
            print(f"  {col:<35}: {BASE_URL}{val}")
        else:
            print(f"  {col:<35}: {val}")
    print()
