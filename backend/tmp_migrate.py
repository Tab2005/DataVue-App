import sqlite3
import os

db_path = 'facebook_dashboard.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE weekly_reports ADD COLUMN share_token VARCHAR")
        cursor.execute("CREATE UNIQUE INDEX ix_weekly_reports_share_token ON weekly_reports (share_token)")
        conn.commit()
        print("Success: Added share_token column and index.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Error: {db_path} not found.")
