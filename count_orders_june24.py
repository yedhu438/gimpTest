import sys
sys.path.insert(0, r"C:\gimpTest")
from db import get_connection

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM tblCustomOrder WHERE CAST(DateAdd AS DATE) = '2026-06-24'")
print("Orders placed on 2026-06-24:", cur.fetchone()[0])
conn.close()
