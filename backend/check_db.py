import sqlite3
c = sqlite3.connect('facebook_dashboard.db')
r = c.execute("SELECT email, ai_provider, gemini_api_key FROM users WHERE email = 'tabchen2005@gmail.com'").fetchall()
print("Result:", r)
if r:
    print(f"  Email: {r[0][0]}")
    print(f"  AI Provider: {r[0][1]}")
    print(f"  Gemini Key (first 20 chars): {r[0][2][:20] if r[0][2] else 'None'}...")
