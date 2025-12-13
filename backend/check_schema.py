import sqlite3

def check_structure():
    conn = sqlite3.connect("facebook_dashboard.db")
    cursor = conn.cursor()
    
    print("--- Checking 'users' table columns ---")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    found_expires = False
    for col in columns:
        print(col)
        if col[1] == 'token_expires_at':
            found_expires = True
            
    if found_expires:
        print("\n✅ 'token_expires_at' column EXISTS.")
    else:
        print("\n❌ 'token_expires_at' column MISSING!")
        
    conn.close()

if __name__ == "__main__":
    check_structure()
