import sqlite3
conn = sqlite3.connect('facebook_dashboard.db')
conn.execute("UPDATE alembic_version SET version_num = '230a10d75894'")
conn.commit()
print('Alembic version fixed to 230a10d75894!')
conn.close()
