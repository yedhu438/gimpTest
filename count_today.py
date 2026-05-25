"""
count_today.py  —  count unprocessed orders for today.
Usage:  python count_today.py
"""
import os, pyodbc
from datetime import date

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

today = date.today().strftime("%Y-%m-%d")
conn  = pyodbc.connect(CONN)
cur   = conn.cursor()
cur.execute(f"""
    SELECT COUNT(DISTINCT o.OrderID) as Orders, COUNT(*) as Items
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE CAST(o.DateAdd AS DATE) = '{today}'
    AND (d.IsDesignComplete = 0 OR d.IsDesignComplete IS NULL)
""")
r = cur.fetchone()
print(f"Date          : {today}")
print(f"Unique orders : {r[0]}")
print(f"Total items   : {r[1]}")
conn.close()
