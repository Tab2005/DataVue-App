import sqlite3
conn = sqlite3.connect('facebook_dashboard.db')
cursor = conn.execute("SELECT id, name, user_id, team_id, created_at FROM saved_views")
rows = cursor.fetchall()
print(f"=== saved_views 資料表 ({len(rows)} 筆) ===")
for row in rows:
    print(f"  ID: {row[0][:8]}... | Name: {row[1]} | User: {row[2][:8] if row[2] else 'None'}... | Team: {row[3] or 'None'} | Created: {row[4]}")
conn.close()
