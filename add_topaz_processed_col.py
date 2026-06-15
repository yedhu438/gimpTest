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

# Check if column already exists
cur.execute("""
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'tblCustomOrderDetails'
    AND COLUMN_NAME = 'Topaz_Processed'
""")
exists = cur.fetchone()[0]

if exists:
    print('Column Topaz_Processed already exists — skipping ALTER')
else:
    cur.execute('ALTER TABLE tblCustomOrderDetails ADD Topaz_Processed bit NULL DEFAULT NULL')
    conn.commit()
    print('Column Topaz_Processed added successfully (bit, NULL default)')

# Verify
cur.execute("""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'tblCustomOrderDetails'
    AND COLUMN_NAME = 'Topaz_Processed'
""")
row = cur.fetchone()
print(f'Verified: {row[0]}  type={row[1]}  nullable={row[2]}  default={row[3]}')
conn.close()
