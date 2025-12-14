import sqlite3
import os

db_path = "facebook_dashboard.db"

if not os.path.exists(db_path):
    print(f"❌ DB File not found at {db_path}")
else:
    print(f"✅ DB File found at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(teams)")
        columns = cursor.fetchall()
        print("--- Columns in 'teams' ---")
        found = False
        for col in columns:
            print(col) # (cid, name, type, notnull, dflt_value, pk)
            if col[1] == 'visible_ad_account_ids':
                found = True
        
        if found:
            print("\n✅ visible_ad_account_ids is PRESENT.")
        else:
            print("\n❌ visible_ad_account_ids is MISSING.")
            
    except Exception as e:
        print(f"Error querying DB: {e}")
    finally:
        conn.close()
