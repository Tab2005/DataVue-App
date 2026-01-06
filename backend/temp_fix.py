import sqlite3
c = sqlite3.connect('facebook_dashboard.db')
c.execute("UPDATE users SET is_super_admin = 0 WHERE email = 'info@ecohukurou.com.tw'")
c.commit()
print('Done! Removed super admin from info@ecohukurou.com.tw')
