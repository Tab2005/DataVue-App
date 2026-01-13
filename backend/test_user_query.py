import os
import sys
sys.path.append('.')

from database import SessionLocal, User

print("Testing User query...")

try:
    session = SessionLocal()
    print("Session created")

    # 嘗試查詢用戶
    user = session.query(User).filter(User.email == 'tabchen2005@gmail.com').first()
    print(f"User found: {user}")

    session.close()
    print("Test completed successfully")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()