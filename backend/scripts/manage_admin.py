#!/usr/bin/env python3
"""
Super Admin 管理工具
用於管理 Facebook Dashboard 的超級管理員帳號

使用方式:
    python manage_admin.py list                    # 列出所有 Super Admin
    python manage_admin.py grant user@example.com  # 授予 Super Admin 權限
    python manage_admin.py revoke user@example.com # 撤銷 Super Admin 權限
    python manage_admin.py check user@example.com  # 檢查用戶狀態

環境變數:
    DATABASE_URL: PostgreSQL 連線字串 (Zeabur 用)
    若未設定，將使用本地 SQLite 資料庫
"""

import sys
import os
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from database import User, UserRole

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # PostgreSQL (Zeabur)
    engine = create_engine(DATABASE_URL)
    print(f"🔗 Connected to PostgreSQL")
else:
    # SQLite (Local)
    DB_PATH = Path(__file__).parent / "facebook_dashboard.db"
    engine = create_engine(f"sqlite:///{DB_PATH}")
    print(f"🔗 Connected to SQLite: {DB_PATH}")

Session = sessionmaker(bind=engine)


def list_admins():
    """列出所有 Super Admin"""
    session = Session()
    try:
        admins = session.query(User).filter(User.is_super_admin == True).all()
        
        if not admins:
            print("\n⚠️  目前沒有任何 Super Admin")
            return
        
        print(f"\n👑 Super Admin 列表 ({len(admins)} 位):")
        print("-" * 60)
        for admin in admins:
            print(f"  • {admin.email}")
            print(f"    ID: {admin.id[:8]}...")
            print(f"    Name: {admin.name}")
            print(f"    Role: {admin.role}")
            print()
    finally:
        session.close()


def grant_admin(email: str):
    """授予 Super Admin 權限"""
    session = Session()
    try:
        user = session.query(User).filter(
            func.lower(User.email) == email.lower()
        ).first()
        
        if not user:
            print(f"\n❌ 找不到用戶: {email}")
            print("   請確認該用戶已經登入過系統")
            return False
        
        if user.is_super_admin:
            print(f"\n✓ 用戶 {email} 已經是 Super Admin")
            return True
        
        user.is_super_admin = True
        user.role = UserRole.ADMIN
        session.commit()
        
        print(f"\n✅ 成功授予 Super Admin 權限: {email}")
        return True
    finally:
        session.close()


def revoke_admin(email: str):
    """撤銷 Super Admin 權限"""
    session = Session()
    try:
        user = session.query(User).filter(
            func.lower(User.email) == email.lower()
        ).first()
        
        if not user:
            print(f"\n❌ 找不到用戶: {email}")
            return False
        
        if not user.is_super_admin:
            print(f"\n✓ 用戶 {email} 本來就不是 Super Admin")
            return True
        
        # 安全檢查：確保至少保留一個 Super Admin
        admin_count = session.query(User).filter(User.is_super_admin == True).count()
        if admin_count <= 1:
            print(f"\n❌ 無法撤銷: {email} 是唯一的 Super Admin")
            print("   系統必須保留至少一位 Super Admin")
            return False
        
        user.is_super_admin = False
        session.commit()
        
        print(f"\n✅ 成功撤銷 Super Admin 權限: {email}")
        return True
    finally:
        session.close()


def check_user(email: str):
    """檢查用戶狀態"""
    session = Session()
    try:
        user = session.query(User).filter(
            func.lower(User.email) == email.lower()
        ).first()
        
        if not user:
            print(f"\n❌ 找不到用戶: {email}")
            return
        
        print(f"\n📋 用戶資訊: {email}")
        print("-" * 40)
        print(f"  ID:            {user.id}")
        print(f"  Name:          {user.name}")
        print(f"  Email:         {user.email}")
        print(f"  Role:          {user.role}")
        print(f"  Super Admin:   {'✅ Yes' if user.is_super_admin else '❌ No'}")
        print(f"  Status:        {user.status}")
    finally:
        session.close()


def print_usage():
    """印出使用說明"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║            Super Admin 管理工具                               ║
╠══════════════════════════════════════════════════════════════╣
║  使用方式:                                                    ║
║    python manage_admin.py <command> [email]                  ║
║                                                              ║
║  指令:                                                        ║
║    list                    列出所有 Super Admin              ║
║    grant <email>           授予 Super Admin 權限             ║
║    revoke <email>          撤銷 Super Admin 權限             ║
║    check <email>           檢查用戶狀態                       ║
║                                                              ║
║  範例:                                                        ║
║    python manage_admin.py list                               ║
║    python manage_admin.py grant user@example.com             ║
║    python manage_admin.py revoke user@example.com            ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_admins()
    
    elif command == "grant":
        if len(sys.argv) < 3:
            print("❌ 請提供 email 地址")
            print("   用法: python manage_admin.py grant user@example.com")
            sys.exit(1)
        grant_admin(sys.argv[2])
    
    elif command == "revoke":
        if len(sys.argv) < 3:
            print("❌ 請提供 email 地址")
            print("   用法: python manage_admin.py revoke user@example.com")
            sys.exit(1)
        revoke_admin(sys.argv[2])
    
    elif command == "check":
        if len(sys.argv) < 3:
            print("❌ 請提供 email 地址")
            print("   用法: python manage_admin.py check user@example.com")
            sys.exit(1)
        check_user(sys.argv[2])
    
    elif command in ["help", "-h", "--help"]:
        print_usage()
    
    else:
        print(f"❌ 未知指令: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
