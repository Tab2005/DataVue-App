import sqlite3
conn = sqlite3.connect('facebook_dashboard.db')
cursor = conn.cursor()

# 檢查所有表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Tables in database:')
for table in tables:
    print(' ', table[0])

# 檢查 users 表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="users"')
user_table = cursor.fetchone()
if user_table:
    print('\nUsers table exists')
    cursor.execute('PRAGMA table_info(users)')
    columns = cursor.fetchall()
    print('Users table columns:')
    for col in columns:
        print(f'  {col[1]} - {col[2]} - pk: {col[5]}')
else:
    print('\nUsers table does NOT exist!')

conn.close()