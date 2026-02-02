"""
修復超級管理員權限腳本

用於解決部署後超級管理員權限丟失的問題。

使用方式:
    # 直接指定 email
    python scripts/fix_super_admin.py tabchen2005@gmail.com
    
    # 使用環境變數 SUPER_ADMIN_EMAIL
    python scripts/fix_super_admin.py

也可以透過 API 呼叫（需要在 main.py 中註冊）:
    POST /api/admin/fix-super-admin
"""

import sys
import os

# 確保能夠 import 上層目錄的模組
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, User, UserRole, Module, UserModuleAccess


def fix_super_admin(email: str = None):
    """
    修復超級管理員權限
    
    Args:
        email: 要設為超級管理員的 email，若為 None 則使用 SUPER_ADMIN_EMAIL 環境變數
    """
    if not email:
        email = os.getenv("SUPER_ADMIN_EMAIL", "").strip()
    
    if not email:
        print("❌ 請提供 email 參數或設定 SUPER_ADMIN_EMAIL 環境變數")
        return False
    
    # 支援逗號分隔的多個 email
    emails = [e.strip().lower() for e in email.split(",") if e.strip()]
    
    if not emails:
        print("❌ 沒有有效的 email 地址")
        return False
    
    session = SessionLocal()
    try:
        print("=" * 60)
        print("🔧 超級管理員權限修復工具")
        print("=" * 60)
        
        # 先列出所有用戶
        print("\n📋 現有用戶列表:")
        all_users = session.query(User).all()
        for u in all_users:
            status = "✅ Super Admin" if u.is_super_admin else "  一般用戶"
            print(f"  {status} | {u.email} | Role: {u.role}")
        
        print(f"\n🎯 要修復的 email: {emails}")
        
        fixed_count = 0
        for target_email in emails:
            user = session.query(User).filter(User.email == target_email).first()
            
            if not user:
                print(f"\n⚠️ 用戶 {target_email} 不存在，將在該用戶首次登入時自動設定")
                continue
            
            print(f"\n👤 處理用戶: {user.email}")
            print(f"   當前狀態: is_super_admin={user.is_super_admin}, role={user.role}")
            
            changes_made = False
            
            # 1. 設定 is_super_admin
            if not user.is_super_admin:
                user.is_super_admin = True
                print("   ✅ 設定 is_super_admin = True")
                changes_made = True
            else:
                print("   ℹ️ is_super_admin 已經是 True")
            
            # 2. 確保 role 是 ADMIN
            if user.role != UserRole.ADMIN:
                user.role = UserRole.ADMIN
                print("   ✅ 設定 role = ADMIN")
                changes_made = True
            else:
                print("   ℹ️ role 已經是 ADMIN")
            
            # 3. 確保有所有模組的存取權限
            modules = session.query(Module).all()
            for module in modules:
                # 檢查是否已有該模組的存取權限（個人工作區）
                access = session.query(UserModuleAccess).filter(
                    UserModuleAccess.user_id == user.id,
                    UserModuleAccess.module_id == module.id,
                    UserModuleAccess.team_id.is_(None)
                ).first()
                
                if not access:
                    access = UserModuleAccess(
                        user_id=user.id,
                        module_id=module.id,
                        team_id=None,
                        enabled=True
                    )
                    session.add(access)
                    print(f"   ✅ 新增模組存取權限: {module.key}")
                    changes_made = True
                elif not access.enabled:
                    access.enabled = True
                    print(f"   ✅ 啟用模組存取權限: {module.key}")
                    changes_made = True
                else:
                    print(f"   ℹ️ 已有模組存取權限: {module.key}")
            
            if changes_made:
                fixed_count += 1
        
        if fixed_count > 0:
            session.commit()
            print(f"\n✅ 成功修復 {fixed_count} 個用戶的超級管理員權限")
        else:
            print("\nℹ️ 沒有需要修復的項目")
        
        # 驗證修復結果
        print("\n📋 修復後用戶列表:")
        all_users = session.query(User).all()
        for u in all_users:
            status = "✅ Super Admin" if u.is_super_admin else "  一般用戶"
            print(f"  {status} | {u.email} | Role: {u.role}")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def diagnose():
    """診斷權限問題"""
    session = SessionLocal()
    try:
        print("=" * 60)
        print("🔍 權限診斷報告")
        print("=" * 60)
        
        # 1. 檢查環境變數
        super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "")
        db_url = os.getenv("DATABASE_URL", "")
        print(f"\n📌 環境變數:")
        print(f"   SUPER_ADMIN_EMAIL: {super_admin_email or '(未設定)'}")
        print(f"   DATABASE_URL: {'PostgreSQL' if 'postgresql' in db_url.lower() else 'SQLite' if not db_url else db_url[:50]}")
        
        # 2. 檢查用戶
        print(f"\n👥 用戶統計:")
        total_users = session.query(User).count()
        super_admins = session.query(User).filter(User.is_super_admin == True).count()
        print(f"   總用戶數: {total_users}")
        print(f"   超級管理員數: {super_admins}")
        
        # 3. 檢查模組
        print(f"\n📦 模組統計:")
        modules = session.query(Module).all()
        for m in modules:
            print(f"   {m.key}: enabled={m.enabled}")
        
        # 4. 列出所有用戶詳情
        print(f"\n📋 用戶詳細列表:")
        users = session.query(User).all()
        for u in users:
            print(f"\n   👤 {u.email}")
            print(f"      ID: {u.id}")
            print(f"      is_super_admin: {u.is_super_admin}")
            print(f"      role: {u.role}")
            
            # 列出模組存取權限
            accesses = session.query(UserModuleAccess).filter(
                UserModuleAccess.user_id == u.id,
                UserModuleAccess.team_id.is_(None)
            ).all()
            print(f"      模組存取:")
            for a in accesses:
                module = session.query(Module).filter(Module.id == a.module_id).first()
                print(f"        - {module.key if module else a.module_id}: enabled={a.enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="超級管理員權限修復工具")
    parser.add_argument("email", nargs="?", help="要設為超級管理員的 email（可選，預設使用 SUPER_ADMIN_EMAIL 環境變數）")
    parser.add_argument("--diagnose", "-d", action="store_true", help="只執行診斷，不修改資料")
    
    args = parser.parse_args()
    
    if args.diagnose:
        diagnose()
    else:
        fix_super_admin(args.email)
