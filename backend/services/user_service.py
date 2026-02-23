"""
User Service
提供使用者建立、Super Admin 同步、模組存取授予等業務邏輯

使用方式:
    from services.user_service import get_or_create_user, sync_super_admin_status, grant_default_module_access
"""

import os
import logging
from sqlalchemy.orm import Session
from database import User, UserRole, UserStatus, Module, UserModuleAccess

logger = logging.getLogger(__name__)


def get_or_create_user(
    db: Session,
    google_id: str,
    email: str,
    name: str,
    picture: str,
) -> tuple[User, bool]:
    """
    依 google_id 取得使用者，若不存在則自動建立。

    Returns:
        (user, created): user 物件與是否新建立的布林值
    """
    user = db.query(User).filter(User.google_id == google_id).first()

    if user:
        # 更新使用者資料（名稱或 email 可能變更）
        changed = False
        if user.email != email:
            user.email = email
            changed = True
        if user.name != name:
            user.name = name
            changed = True
        if changed:
            db.commit()
            db.refresh(user)
        return user, False

    # 建立新使用者
    user_count = db.query(User).count()
    new_role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER

    new_user = User(
        google_id=google_id,
        email=email,
        name=name,
        role=new_role,
        status=UserStatus.ACTIVE,
        is_super_admin=(user_count == 0),  # 第一位使用者為 Super Admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    masked_email = f"{email[:3]}***@{email.split('@')[-1]}" if email and '@' in email else "unknown"
    logger.info(f"[UserService] 新使用者已建立: {masked_email} ({new_role})")
    return new_user, True


def sync_super_admin_status(db: Session, user: User) -> bool:
    """
    依 SUPER_ADMIN_EMAIL 環境變數檢查並同步 Super Admin 狀態。
    支援逗號分隔的多個 email。

    Returns:
        若狀態有變更返回 True
    """
    super_admin_env = os.getenv("SUPER_ADMIN_EMAIL", "")
    if not super_admin_env:
        return False

    allowed_emails = {e.strip().lower() for e in super_admin_env.split(",") if e.strip()}
    should_be_super_admin = user.email.lower() in allowed_emails if user.email else False

    if should_be_super_admin and not user.is_super_admin:
        user.is_super_admin = True
        user.role = UserRole.ADMIN

        # 確保 Super Admin 擁有所有模組存取權
        try:
            modules = db.query(Module).all()
            for module in modules:
                existing = db.query(UserModuleAccess).filter(
                    UserModuleAccess.user_id == user.id,
                    UserModuleAccess.module_id == module.id,
                    UserModuleAccess.team_id.is_(None),
                ).first()
                if not existing:
                    db.add(UserModuleAccess(
                        user_id=user.id,
                        module_id=module.id,
                        team_id=None,
                        enabled=True,
                    ))
                elif not existing.enabled:
                    existing.enabled = True
        except Exception as mod_err:
            logger.warning(f"[UserService] 同步模組存取失敗: {mod_err}")

        db.commit()
        db.refresh(user)
        masked_email = f"{user.email[:3]}***@{user.email.split('@')[-1]}" if user.email and '@' in user.email else "unknown"
        logger.info(f"[UserService] 已授予 Super Admin: {masked_email}")
        return True

    return False


def grant_default_module_access(db: Session, user: User) -> list[str]:
    """
    為新使用者授予預設模組存取權限（fb_ads、gsc）。

    Returns:
        已授予的模組 key 列表
    """
    default_module_keys = ["fb_ads", "gsc"]
    granted = []

    for module_key in default_module_keys:
        module = db.query(Module).filter(Module.key == module_key).first()
        if not module:
            continue

        existing = db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user.id,
            UserModuleAccess.module_id == module.id,
            UserModuleAccess.team_id.is_(None),
        ).first()

        if not existing:
            db.add(UserModuleAccess(
                user_id=user.id,
                module_id=module.id,
                team_id=None,
                enabled=True,
            ))
            granted.append(module_key)

    if granted:
        db.commit()
        masked_email = f"{user.email[:3]}***@{user.email.split('@')[-1]}" if user.email and '@' in user.email else "unknown"
        logger.info(f"[UserService] 為 {masked_email} 授予預設模組: {granted}")

    return granted
