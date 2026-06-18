import sys, os
sys.path.insert(0, r'C:\gimpTest')
from dotenv import load_dotenv
load_dotenv(r'C:\gimpTest\.env')
import pyodbc

ORDER_ID = '206-7243076-3097949'

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=' + os.environ['DB_SERVER'] + ';'
    'DATABASE=' + os.environ['DB_NAME'] + ';'
    'UID=' + os.environ['DB_UID'] + ';'
    'PWD=' + os.environ['DB_PWD'] + ';'
    'TrustServerCertificate=yes;'
)
cur = conn.cursor()
cur.execute("""
    SELECT
        o.OrderID, o.SKU, o.Quantity, o.ItemType, o.IsShipped, o.Notes, o.DateAdd,
        d.idCustomOrderDetails,
        d.PrintLocation,
        d.IsFrontLocation, d.IsBackLocation, d.IsPocketLocation, d.IsSleeveLocation,
        d.FrontImage,   d.FrontText,   d.FrontFonts,   d.FrontColours,   d.FrontPreviewImage,
        d.BackImage,    d.BackText,    d.BackFonts,    d.BackColours,    d.BackPreviewImage,
        d.PocketImage,  d.PocketText,  d.PocketFonts,  d.PocketColours,  d.PocketPreviewImage,
        d.SleeveImage,  d.SleeveText,  d.SleeveFonts,  d.SleeveColours,  d.SleevePreviewImage,
        d.IsOrderProcess, d.IsDesignComplete, d.ProcessBy,
        d.IsTopazImageProcess, d.Topaz_Processed,
        d.FrontTopazImage, d.BackTopazImage, d.PocketTopazImage, d.SleeveTopazImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID = ?
""", ORDER_ID)

cols = [c[0] for c in cur.description]
rows = cur.fetchall()
print(f"Order: {ORDER_ID}")
print(f"Rows found: {len(rows)}")
print()
for i, row in enumerate(rows, 1):
    print(f"=== Row {i} ===")
    for col, val in zip(cols, row):
        print(f"  {col}: {val}")
    print()
conn.close()
