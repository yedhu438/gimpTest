import pyodbc
from db import get_connection

conn = get_connection(timeout=10)
cursor = conn.cursor()
cursor.execute(
    "SELECT TOP 5 o.OrderID, d.FrontImage, d.FrontImageJSON, d.FrontPreviewImage,"
    " d.BackImage, d.BackImageJSON"
    " FROM tblCustomOrder o"
    " JOIN tblCustomOrderDetails d ON o.idCustomOrder = d.idCustomOrder"
    " WHERE ISNULL(d.FrontImage,'') <> ''"
    " ORDER BY o.DateAdd DESC"
)
for r in cursor.fetchall():
    print('OrderID       :', r[0])
    print('FrontImage    :', r[1])
    print('FrontImageJSON:', str(r[2])[:400] if r[2] else 'NULL')
    print('FrontPreview  :', r[3])
    print('BackImage     :', r[4])
    print('BackImageJSON :', str(r[5])[:400] if r[5] else 'NULL')
    print('-' * 80)
conn.close()
