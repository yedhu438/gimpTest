"""
download_order_images.py  —  download all customer images for a given OrderID.
Usage:  python download_order_images.py 205-1289169-6851545
"""
import sys, os, json, urllib.request, pyodbc

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

BASE_URL = "http://www.crssoft.co.uk/CustomOrderImages/"
ORDER_ID = sys.argv[1] if len(sys.argv) > 1 else "205-1289169-6851545"
SAVE_DIR = os.path.join(r"C:\gimpTest\Output\OrderImages", ORDER_ID)
os.makedirs(SAVE_DIR, exist_ok=True)

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
    SELECT o.SKU, d.FrontImage, d.FrontImageJSON, d.BackImage, d.BackImageJSON,
           d.PocketImage, d.SleeveImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID = ?
""", ORDER_ID)
rows = cur.fetchall()
conn.close()

def get_filenames(img, img_json):
    if img_json:
        try:
            return list(json.loads(img_json).values())
        except Exception:
            pass
    return [img] if img else []

def download(filename, label):
    if not filename:
        return
    url  = BASE_URL + filename.strip()
    dest = os.path.join(SAVE_DIR, filename.strip())
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  [OK]   {label}: {dest}")
    except Exception as e:
        print(f"  [FAIL] {label} ({url}): {e}")

print(f"Downloading images for {ORDER_ID}\n")
for row in rows:
    sku, fi, fj, bi, bj, pi, si = row
    print(f"SKU: {sku}")
    for f in get_filenames(fi, fj): download(f, "Front")
    for f in get_filenames(bi, bj): download(f, "Back")
    if pi: download(pi, "Pocket")
    if si: download(si, "Sleeve")
    print()

print(f"Saved to: {SAVE_DIR}")
