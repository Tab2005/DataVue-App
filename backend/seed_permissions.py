"""執行權限系統初始資料 Seeding"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Module, Permission, Role, RolePermission
from seeds.permission_seeds import MODULES, PERMISSIONS, ROLES, ROLE_PERMISSIONS


def seed_permissions():
    """Seed 權限系統初始資料"""
    db = SessionLocal()
    try:
        print("🚀 開始 Seeding 權限系統...")
        
        # 1. Seed Modules
        print("\n📦 建立模組...")
        module_map = {}
        for m in MODULES:
            existing = db.query(Module).filter(Module.key == m["key"]).first()
            if not existing:
                module = Module(**m)
                db.add(module)
                db.flush()
                module_map[m["key"]] = module.id
                print(f"  ✅ Created module: {m['key']} ({m['name']})")
            else:
                module_map[m["key"]] = existing.id
                print(f"  ⏭️ Module exists: {m['key']}")

        # 2. Seed Permissions
        print("\n🔑 建立權限...")
        permission_map = {}
        for module_key, perms in PERMISSIONS.items():
            module_id = module_map.get(module_key)
            if not module_id:
                print(f"  ⚠️ Module not found: {module_key}")
                continue
            for p in perms:
                existing = db.query(Permission).filter(Permission.key == p["key"]).first()
                if not existing:
                    perm = Permission(
                        module_id=module_id,
                        **p
                    )
                    db.add(perm)
                    db.flush()
                    permission_map[p["key"]] = perm.id
                    print(f"  ✅ Created permission: {p['key']}")
                else:
                    permission_map[p["key"]] = existing.id

        # 3. Seed Roles
        print("\n👥 建立角色...")
        role_map = {}
        for r in ROLES:
            existing = db.query(Role).filter(Role.key == r["key"]).first()
            if not existing:
                role = Role(**r)
                db.add(role)
                db.flush()
                role_map[r["key"]] = role.id
                print(f"  ✅ Created role: {r['key']} ({r['name']})")
            else:
                role_map[r["key"]] = existing.id
                print(f"  ⏭️ Role exists: {r['key']}")

        # 4. Seed Role Permissions
        print("\n🔗 建立角色-權限關聯...")
        for role_key, perms in ROLE_PERMISSIONS.items():
            role_id = role_map.get(role_key)
            if not role_id:
                continue
            
            # 處理 "*" 全部權限
            if perms == ["*"]:
                perms = list(permission_map.keys())
            
            added_count = 0
            for perm_key in perms:
                perm_id = permission_map.get(perm_key)
                if not perm_id:
                    continue
                existing = db.query(RolePermission).filter(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == perm_id
                ).first()
                if not existing:
                    rp = RolePermission(role_id=role_id, permission_id=perm_id)
                    db.add(rp)
                    added_count += 1
            
            if added_count > 0:
                print(f"  ✅ {role_key}: 新增 {added_count} 個權限")

        db.commit()
        print("\n🎉 權限系統 Seeding 完成!")
        print(f"   - 模組: {len(module_map)}")
        print(f"   - 權限: {len(permission_map)}")
        print(f"   - 角色: {len(role_map)}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_permissions()
