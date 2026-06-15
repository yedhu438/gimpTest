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

print("=== tblCustomOrder columns ===")
cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'tblCustomOrder'
    ORDER BY ORDINAL_POSITION
""")
for row in cur.fetchall():
    col, dtype, maxlen, nullable, default = row
    size = f"({maxlen})" if maxlen else ""
    print(f"  {col:<35} {dtype}{size:<15} null={nullable}  default={default}")

print()
print("=== tblCustomOrderDetails columns ===")
cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'tblCustomOrderDetails'
    ORDER BY ORDINAL_POSITION
""")
for row in cur.fetchall():
    col, dtype, maxlen, nullable, default = row
    size = f"({maxlen})" if maxlen else ""
    print(f"  {col:<35} {dtype}{size:<15} null={nullable}  default={default}")

conn.close()
