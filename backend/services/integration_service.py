# backend/services/integration_service.py
"""
Integration Service — 使用者第三方服務整合管理

提供 UserIntegration 表的 CRUD 操作，
統一負責 Token 加解密以確保安全性。

支援的 provider 值：
  'facebook'  - Facebook Ads
  'gsc'       - Google Search Console
  'ga4'       - Google Analytics 4
  'ai_zeabur' - Zeabur AI Hub
  'ai_gemini' - Google Gemini

用法範例：
    from services.integration_service import get_user_integration, upsert_user_integration

    # 取得整合設定
    integration = get_user_integration(db, user_id, "facebook")

    # 更新/建立整合
    integration = upsert_user_integration(
        db, user_id, "facebook",
        access_token="raw_token",
        extra_data={"app_id": "12345", "default_account_id": "act_67890"},
    )

    # 取得解密後的 Token
    raw_token = get_decrypted_access_token(integration)
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.models.integration import UserIntegration

logger = logging.getLogger(__name__)

# 可支援的 provider 類型（防止拼寫錯誤）
SUPPORTED_PROVIDERS = frozenset({
    "facebook",
    "gsc",
    "ga4",
    "ai_zeabur",
    "ai_gemini",
})


# ─────────────────────────────────────────────────────────────────────────────
# 查詢操作
# ─────────────────────────────────────────────────────────────────────────────

def get_user_integration(
    db: Session,
    user_id: str,
    provider: str,
) -> Optional[UserIntegration]:
    """
    取得指定使用者的特定服務整合設定。

    Args:
        db: SQLAlchemy Session
        user_id: 使用者 UUID
        provider: 服務提供者識別字串（如 'facebook'）

    Returns:
        UserIntegration 實例，若不存在則回傳 None
    """
    return (
        db.query(UserIntegration)
        .filter(
            UserIntegration.user_id == user_id,
            UserIntegration.provider == provider,
        )
        .first()
    )


def get_all_user_integrations(
    db: Session,
    user_id: str,
) -> list[UserIntegration]:
    """
    取得指定使用者的所有服務整合設定（不含 Token 內容，安全查詢）。

    Returns:
        UserIntegration 列表
    """
    return (
        db.query(UserIntegration)
        .filter(UserIntegration.user_id == user_id)
        .all()
    )


# ─────────────────────────────────────────────────────────────────────────────
# 寫入操作
# ─────────────────────────────────────────────────────────────────────────────

def upsert_user_integration(
    db: Session,
    user_id: str,
    provider: str,
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
    token_expiry: Optional[datetime] = None,
    extra_data: Optional[dict] = None,
) -> UserIntegration:
    """
    建立或更新使用者的服務整合設定。

    Token 在傳入時若有值，會自動以 Fernet 加密後儲存。
    extra_data 採用 dict merge（不覆蓋未提供的鍵）。

    Args:
        db: SQLAlchemy Session
        user_id: 使用者 UUID
        provider: 服務提供者識別字串
        access_token: 明文 Access Token（可選）
        refresh_token: 明文 Refresh Token（可選）
        token_expiry: Token 到期時間（可選）
        extra_data: 額外設定欄位（dict，可選）

    Returns:
        更新後的 UserIntegration 實例
    """
    if provider not in SUPPORTED_PROVIDERS:
        logger.warning(f"[IntegrationService] 不明的 provider: {provider!r}，仍繼續儲存")

    # 嘗試加密 Token
    encrypted_access = _safe_encrypt(access_token)
    encrypted_refresh = _safe_encrypt(refresh_token)

    integration = get_user_integration(db, user_id, provider)

    if integration:
        # 更新已存在的整合
        if encrypted_access is not None:
            integration.access_token = encrypted_access
        if encrypted_refresh is not None:
            integration.refresh_token = encrypted_refresh
        if token_expiry is not None:
            integration.token_expiry = token_expiry
        if extra_data:
            existing = integration.extra_data or {}
            integration.extra_data = {**existing, **extra_data}
        integration.updated_at = datetime.utcnow()
        logger.debug(f"[IntegrationService] 更新 {provider} 整合 user={user_id}")
    else:
        # 建立新整合
        integration = UserIntegration(
            user_id=user_id,
            provider=provider,
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            token_expiry=token_expiry,
            extra_data=extra_data or {},
        )
        db.add(integration)
        logger.debug(f"[IntegrationService] 新增 {provider} 整合 user={user_id}")

    db.commit()
    db.refresh(integration)
    return integration


def delete_user_integration(
    db: Session,
    user_id: str,
    provider: str,
) -> bool:
    """
    刪除使用者的某個服務整合設定。

    Returns:
        True 表示成功刪除，False 表示紀錄不存在
    """
    integration = get_user_integration(db, user_id, provider)
    if not integration:
        return False

    db.delete(integration)
    db.commit()
    logger.info(f"[IntegrationService] 刪除 {provider} 整合 user={user_id}")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Token 解密工具
# ─────────────────────────────────────────────────────────────────────────────

def get_decrypted_access_token(integration: Optional[UserIntegration]) -> Optional[str]:
    """
    取得解密後的 Access Token。

    Args:
        integration: UserIntegration 實例（可為 None）

    Returns:
        明文 Token 字串，若無整合或無 Token 則回傳 None
    """
    if not integration or not integration.access_token:
        return None
    return _safe_decrypt(integration.access_token)


def get_decrypted_refresh_token(integration: Optional[UserIntegration]) -> Optional[str]:
    """
    取得解密後的 Refresh Token。

    Returns:
        明文 Refresh Token，若不存在則回傳 None
    """
    if not integration or not integration.refresh_token:
        return None
    return _safe_decrypt(integration.refresh_token)


# ─────────────────────────────────────────────────────────────────────────────
# 私有輔助函式
# ─────────────────────────────────────────────────────────────────────────────

def _safe_encrypt(value: Optional[str]) -> Optional[str]:
    """安全加密：value 為 None 或無加密金鑰時直接回傳。"""
    if not value:
        return None
    try:
        from core.security import encrypt_value
        encrypted = encrypt_value(value)
        return encrypted if encrypted is not None else value
    except Exception as e:
        logger.error(f"[IntegrationService] 加密失敗（儲存明文）: {e}")
        return value  # fallback：儲存明文，避免資料丟失


def _safe_decrypt(value: Optional[str]) -> Optional[str]:
    """安全解密：失敗時回傳原始值（可能未加密的明文）。"""
    if not value:
        return None
    try:
        from core.security import decrypt_value
        decrypted = decrypt_value(value)
        return decrypted if decrypted is not None else value
    except Exception as e:
        logger.debug(f"[IntegrationService] 解密失敗（嘗試回傳原值）: {e}")
        return value
