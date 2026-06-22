import pyodbc
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:81.0.219.26,1433;'
    'DATABASE=dbAmazonCustomOrders;UID=CustOrderUser;PWD=CjxcWx9g,ie8?!9PM;'
    'TrustServerCertificate=yes;Encrypt=yes;', timeout=20)
cur = conn.cursor()
cur.execute("""
    SELECT o.SKU, COUNT(DISTINCT o.OrderID) as orders, COUNT(*) as rows
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON d.idCustomOrder = o.idCustomOrder
    WHERE (o.SKU LIKE 'Football%' OR o.SKU LIKE 'PPFBall%'
        OR o.SKU LIKE 'PEngFB%' OR o.SKU LIKE 'Scotland_Football%'
        OR o.SKU LIKE 'EngFootball%')
      AND d.IsDesignComplete = 0
    GROUP BY o.SKU
    ORDER BY orders DESC
""")
total = 0
for row in cur.fetchall():
    print(str(row[1]).rjust(6) + '  rows=' + str(row[2]).rjust(5) + '  ' + str(row[0]))
    total += row[1]
print('TOTAL: ' + str(total) + ' orders')
conn.close()
