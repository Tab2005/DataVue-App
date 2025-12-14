import sqlite3

def check_structure():
    conn = sqlite3.connect('facebook_dashboard.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(teams)")
    columns = cursor.fetchall()
    print("Columns in 'teams' table:")
    found = False
    for col in columns:
        print(col)
        if col[1] == 'visible_ad_account_ids':
            found = True
    
    if found:
        print("\n✅ visible_ad_account_ids column FOUND.")
    else:
        print("\n❌ visible_ad_account_ids column NOT FOUND.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        check_structure()
    except Exception as e:
        print(f"ERROR: {e}")

