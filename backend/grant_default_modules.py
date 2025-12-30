"""為所有現有使用者授予預設模組存取權"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, User, Module, UserModuleAccess


def grant_default_modules():
    """為所有使用者授予 fb_ads 和 gsc 模組存取權"""
    db = SessionLocal()
    try:
        print("🚀 開始授予預設模組權限...")
        
        # 取得所有使用者
        users = db.query(User).all()
        print(f"📊 找到 {len(users)} 位使用者")
        
        # 取得模組
        fb_ads = db.query(Module).filter(Module.key == "fb_ads").first()
        gsc = db.query(Module).filter(Module.key == "gsc").first()
        
        if not fb_ads or not gsc:
            print("❌ 找不到模組！請先執行 seed_permissions.py")
            return
        
        granted_count = 0
        
        for user in users:
            # 為每個使用者授予 fb_ads
            existing_fb = db.query(UserModuleAccess).filter(
                UserModuleAccess.user_id == user.id,
                UserModuleAccess.module_id == fb_ads.id,
                UserModuleAccess.team_id == None
            ).first()
            
            if not existing_fb:
                access = UserModuleAccess(
                    user_id=user.id,
                    module_id=fb_ads.id,
                    team_id=None,
                    enabled=True
                )
                db.add(access)
                granted_count += 1
            
            # 為每個使用者授予 gsc
            existing_gsc = db.query(UserModuleAccess).filter(
                UserModuleAccess.user_id == user.id,
                UserModuleAccess.module_id == gsc.id,
                UserModuleAccess.team_id == None
            ).first()
            
            if not existing_gsc:
                access = UserModuleAccess(
                    user_id=user.id,
                    module_id=gsc.id,
                    team_id=None,
                    enabled=True
                )
                db.add(access)
                granted_count += 1
        
        db.commit()
        
        print(f"\n✅ 完成！")
        print(f"   - 使用者數: {len(users)}")
        print(f"   - 新增權限數: {granted_count}")
        print(f"   - 所有使用者現在都有 fb_ads 和 gsc 模組權限")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    grant_default_modules()
