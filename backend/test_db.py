import os
import sys
sys.path.append('.')

from database import SessionLocal, User
from sqlalchemy import text

# 檢查資料庫連接
print("Testing database connection...")

try:
    session = SessionLocal()
    print("Session created successfully")

    # 嘗試簡單的查詢
    result = session.execute(text("SELECT 1")).fetchone()
    print(f"Simple query result: {result}")

    # 檢查 users 表
    result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")).fetchone()
    if result:
        print("Users table exists")
    else:
        print("Users table does NOT exist")

    # 嘗試查詢 users
    try:
        users = session.query(User).limit(1).all()
        print(f"Found {len(users)} users")
    except Exception as e:
        print(f"Error querying users: {e}")

    session.close()
    print("Test completed")

except Exception as e:
    print(f"Database error: {e}")