import pyodbc, os
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

try:
    conn = pyodbc.connect(CONN)
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tblCustomOrderDetails WHERE ISNULL(FrontPreviewImage, '') <> ''")
    print(f"Orders with FrontPreviewImage populated: {cur.fetchone()[0]}")

    cur.execute("""
        SELECT TOP 5 o.OrderID, d.FrontPreviewImage, d.FrontImage
        FROM tblCustomOrder o
        JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
        WHERE ISNULL(d.FrontPreviewImage, '') <> ''
        ORDER BY o.DateAdd DESC
    """)
    print("\nSample rows:")
    for r in cur.fetchall():
        print(f"  OrderID={r[0]}  FrontPreviewImage={r[1]}  FrontImage={r[2]}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
