import pyodbc
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};SERVER=tcp:81.0.219.26,1433;'
    'DATABASE=dbAmazonCustomOrders;UID=CustOrderUser;PWD=CjxcWx9g,ie8?!9PM;'
    'TrustServerCertificate=yes;Encrypt=yes;', timeout=20)
cur = conn.cursor()

# All distinct CustomizationCategory values and counts
print("=== All CustomizationCategory values ===")
cur.execute("""
    SELECT CustomizationCategory, COUNT(*) as cnt
    FROM tblCustomOrderDetails
    GROUP BY CustomizationCategory
    ORDER BY cnt DESC
""")
for r in cur.fetchall():
    print(f"  {str(r[1]).rjust(6)}  '{r[0]}'")

# All SKUs that appear under SemiCustomized
print("\n=== SKUs with CustomizationCategory = 'SemiCustomized' ===")
cur.execute("""
    SELECT o.SKU, COUNT(DISTINCT o.OrderID) as orders
    FROM tblCustomOrder o
    JOIN tblCustomOrderDetails d ON d.idCustomOrder = o.idCustomOrder
    WHERE d.CustomizationCategory = 'SemiCustomized'
    GROUP BY o.SKU
    ORDER BY orders DESC
""")
total = 0
for r in cur.fetchall():
    print(f"  {str(r[1]).rjust(6)}  {r[0]}")
    total += r[1]
print(f"  TOTAL: {total} orders")

conn.close()
