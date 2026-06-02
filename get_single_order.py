import sys
sys.path.insert(0, r"C:\Users\yedhu\Desktop\gimpTest")
from db import get_connection

conn = get_connection()
cur  = conn.cursor()
cur.execute("""
    SELECT o.OrderID, o.SKU, o.DateAdd,
        d.FrontText, d.FrontFonts, d.FrontColours, d.FrontImage,
        d.BackText,  d.BackFonts,  d.BackColours,  d.BackImage
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder
    WHERE o.OrderID = '206-7975042-3405128'
""")
r = cur.fetchone()
conn.close()
print(f"OrderID   : {r[0]}")
print(f"SKU       : {r[1]}")
print(f"Date      : {r[2]}")
print(f"FrontText : {r[3]}")
print(f"FrontFont : {r[4]}")
print(f"FrontColor: {r[5]}")
print(f"FrontImage: {r[6]}")
print(f"BackText  : {r[7]}")
print(f"BackFont  : {r[8]}")
print(f"BackColor : {r[9]}")
print(f"BackImage : {r[10]}")
