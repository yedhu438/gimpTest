import pyodbc
from db import get_connection

conn = get_connection(timeout=10)
cursor = conn.cursor()

tables = [row[0] for row in cursor.execute('SELECT name FROM sys.tables ORDER BY name').fetchall()]

for table in tables:
    print('\n=== ' + table + ' ===')
    sql = (
        "SELECT c.name, tp.name, c.max_length, c.is_nullable, c.column_id "
        "FROM sys.columns c "
        "JOIN sys.types tp ON c.user_type_id = tp.user_type_id "
        "WHERE c.object_id = OBJECT_ID('" + table + "') "
        "ORDER BY c.column_id"
    )
    cursor.execute(sql)
    for col in cursor.fetchall():
        nullable = 'NULL' if col[3] else 'NOT NULL'
        dtype = col[1]
        length = ''
        if col[2] > 0 and dtype in ('nvarchar', 'varchar', 'char', 'nchar'):
            length = '(' + str(col[2] // 2 if dtype.startswith('n') else col[2]) + ')'
        elif col[2] == -1 and dtype in ('nvarchar', 'varchar'):
            length = '(MAX)'
        print('  ' + col[0].ljust(40) + ' ' + dtype + length + ' ' + nullable)

conn.close()
