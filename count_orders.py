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

for date in ['2026-06-08', '2026-06-09', '2026-06-10']:
    cur.execute("""
        SELECT
            COUNT(*) AS total_orders,
            SUM(CASE WHEN (ISNULL(d.FrontImage,'')  <> ''
                       OR  ISNULL(d.BackImage,'')   <> ''
                       OR  ISNULL(d.PocketImage,'') <> ''
                       OR  ISNULL(d.SleeveImage,'') <> '') THEN 1 ELSE 0 END) AS image_orders,
            SUM(CASE WHEN (ISNULL(d.FrontImage,'')  = ''
                       AND ISNULL(d.BackImage,'')   = ''
                       AND ISNULL(d.PocketImage,'') = ''
                       AND ISNULL(d.SleeveImage,'') = '') THEN 1 ELSE 0 END) AS text_orders,
            SUM(CASE WHEN d.PrintLocation LIKE '%+%' THEN 1 ELSE 0 END) AS multizone_orders,
            SUM(CASE WHEN o.Quantity > 1 THEN 1 ELSE 0 END) AS multi_qty_orders,
            SUM(CASE WHEN d.IsFrontLocation=1 AND d.IsBackLocation=1 THEN 1 ELSE 0 END) AS front_back,
            SUM(CASE WHEN d.IsSleeveLocation=1 THEN 1 ELSE 0 END) AS with_sleeve
        FROM tblCustomOrder o
        JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
        WHERE CAST(o.DateAdd AS DATE) = ?
    """, date)
    row = cur.fetchone()
    total      = row[0]
    img        = row[1] or 0
    txt        = row[2] or 0
    multi_zone = row[3] or 0
    multi_qty  = row[4] or 0
    fb         = row[5] or 0
    sleeve     = row[6] or 0

    print(f"=== {date} ===")
    print(f"  Total orders      : {total}")
    print(f"  Image orders      : {img}  ({round(img/total*100) if total else 0}%)")
    print(f"  Text-only orders  : {txt}  ({round(txt/total*100) if total else 0}%)")
    print(f"  Multi-zone orders : {multi_zone}")
    print(f"    - Front+Back    : {fb}")
    print(f"    - Has Sleeve    : {sleeve}")
    print(f"  Quantity > 1      : {multi_qty}")
    print()

conn.close()
