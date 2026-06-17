"""
Token Manager Service
處理 Facebook Token 和 AI API Key 的加密儲存與讀取

此模組是從 auth.py 抽取出來的獨立服務，可複用於其他專案
"""

import sys
import logging
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 使用 core 模組的加密功能
from core.security import encrypt_value, decrypt_value

# 資料庫依賴（保持向後相容）
from database import SessionLocal, User, UserRole, Team, TeamMember


class TokenManager:
    """
    Token 管理服務
    
    功能:
    - Facebook Access Token 加密儲存與讀取
    - Team Token 管理
    - AI API Key 加密儲存
    """
    
    # ============================================================
    # 內部加密方法（使用 core.security）
    # ============================================================
    
    @staticmethod
    def _encrypt(message: str) -> Optional[str]:
        """加密字串 (封裝 core.security)"""
        return encrypt_value(message)

    @staticmethod
    def _decrypt(token: str) -> Optional[str]:
        """解密字串 (封裝 core.security)"""
        return decrypt_value(token)

    # ============================================================
    # Facebook Token 管理
    # ============================================================
    
    @staticmethod
    def save_user_token(google_id: str, long_lived_token: str, 
                        app_id: str = None, app_secret: str = None, 
                        expires_in: int = None):
        """
        儲存用戶的 Facebook Token（加密）

        同時寫入舊版 User 表欄位（向後相容）與新版 UserIntegration 表，
        確保 /api/auth/token-status 能正確回傳倒數資訊。
        
        Args:
            google_id: 用戶的 Google ID
            long_lived_token: Facebook 長效 Token
            app_id: Facebook App ID
            app_secret: Facebook App Secret
            expires_in: Token 過期時間（秒）
        """
        from services.integration_service import upsert_user_integration

        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                user_count = session.query(User).count()
                new_role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER
                user = User(google_id=google_id, role=new_role)
                session.add(user)
                session.flush()  # 確保 user.id 可用

            # 加密敏感資料寫入舊欄位（向後相容）
            user.fb_access_token = TokenManager._encrypt(long_lived_token)
            
            if app_id:
                user.fb_app_id = app_id
            if app_secret:
                user.fb_app_secret = TokenManager._encrypt(app_secret)
            
            expires_at = None
            if expires_in:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                user.token_expires_at = expires_at
            
            user.last_login = datetime.now()
            session.commit()

            # 同時寫入新版 UserIntegration 表（讓 token-status API 可直接查詢）
            upsert_user_integration(
                db=session,
                user_id=user.id,
                provider="facebook",
                access_token=long_lived_token,
                token_expiry=expires_at,
                extra_data={"app_id": app_id} if app_id else {},
            )
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def save_team_token(team_id: str, long_lived_token: str, 
                        app_id: str, user_id: str, expires_in: int = None):
        """
        儲存團隊的 Facebook Token
        
        Args:
            team_id: 團隊 ID
            long_lived_token: Facebook 長效 Token
            app_id: Facebook App ID
            user_id: 操作者的 Google ID（需要是團隊管理員）
            expires_in: Token 過期時間（秒）
        """
        session = SessionLocal()
        try:
            # 取得用戶
            user = session.query(User).filter(User.google_id == user_id).first()
            if not user:
                raise Exception("User not found")

            # 檢查權限：Super Admin 或 Team Admin
            is_admin = False
            if user.is_super_admin:
                is_admin = True
            else:
                member = session.query(TeamMember).filter(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user.id,
                    TeamMember.role == UserRole.ADMIN
                ).first()
                if member: 
                    is_admin = True
            
            if not is_admin:
                raise Exception("Permission Denied: Only Team Admins can update tokens.")

            # 更新 Team Token
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise Exception("Team not found")

            team.fb_access_token = TokenManager._encrypt(long_lived_token)
            team.fb_app_id = app_id
            
            if expires_in:
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                team.token_expires_at = expires_at
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_user_token(google_id: str, allow_fallback: bool = True) -> Optional[str]:
        """
        取得用戶的 Facebook Token
        
        Args:
            google_id: 用戶的 Google ID
            allow_fallback: 是否允許降級使用 Admin Token
            
        Returns:
            解密後的 Token，或 None
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                logger.debug(f"[DEBUG_AUTH] User not found: {google_id}")
            elif not user.fb_access_token:
                logger.debug(f"[DEBUG_AUTH] No token for: {google_id}")
            else:
                decrypted = TokenManager._decrypt(user.fb_access_token)
                if decrypted:
                    return decrypted
            
            if not allow_fallback:
                return None

            # Fallback: 使用任一 Admin 的 Token
            admin_user = session.query(User).filter(
                User.role == UserRole.ADMIN,
                User.fb_access_token.isnot(None)
            ).first()

            if admin_user:
                return TokenManager._decrypt(admin_user.fb_access_token)

            return None
        finally:
            session.close()

    @staticmethod
    def get_team_token(team_id: str) -> Optional[str]:
        """
        取得團隊的 Facebook Token
        
        Fallback: 若團隊無 Token，使用團隊 Owner 的 Token
        """
        session = SessionLocal()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                return None
            
            # 優先使用團隊 Token
            if team.fb_access_token:
                return TokenManager._decrypt(team.fb_access_token)
            
            # Fallback: 使用 Owner Token
            if team.owner_id:
                owner = session.query(User).filter(User.id == team.owner_id).first()
                if owner and owner.fb_access_token:
                    logger.info(f"Using Team Owner's Token for Team: {team.name}")
                    return TokenManager._decrypt(owner.fb_access_token)

            return None
        finally:
            session.close()

    @staticmethod
    def exchange_for_long_lived_token(app_id: str, app_secret: str, 
                                       short_lived_token: str, user_id: str, 
                                       team_id: str = None) -> Tuple[bool, str]:
        """
        將短效 Token 換成長效 Token（60 天）
        
        Returns:
            (success, message)
        """
        url = "https://graph.facebook.com/v24.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_lived_token
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if "access_token" in data:
                if team_id:
                    TokenManager.save_team_token(
                        team_id=team_id,
                        long_lived_token=data["access_token"],
                        app_id=app_id,
                        user_id=user_id,
                        expires_in=data.get("expires_in")
                    )
                    return True, f"Token saved to Team (ID: {team_id})."
                else:
                    TokenManager.save_user_token(
                        google_id=user_id,
                        long_lived_token=data["access_token"],
                        app_id=app_id,
                        app_secret=app_secret,
                        expires_in=data.get("expires_in")
                    )
                    return True, "Token exchanged and saved successfully."
            else:
                return False, data.get("error", {}).get("message", "Unknown error")
        except Exception as e:
            return False, str(e)

    # ============================================================
    # AI Settings 管理
    # ============================================================
    
    @staticmethod
    def save_ai_settings(google_id: str, zeabur_api_key: str = None,
                         gemini_api_key: str = None, openrouter_api_key: str = None,
                         ai_provider: str = None, ai_model: str = None) -> bool:
        """
        儲存用戶的 AI 設定（API Key 加密儲存）
        
        Args:
            google_id: 用戶的 Google ID
            zeabur_api_key: Zeabur AI Hub API Key
            gemini_api_key: Google Gemini API Key
            openrouter_api_key: OpenRouter API Key
            ai_provider: 使用的 AI 提供者 ('zeabur', 'gemini' 或 'openrouter')
            ai_model: 使用的 AI 模型名稱
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                raise Exception("User not found")
            
            if zeabur_api_key is not None:
                user.zeabur_api_key = TokenManager._encrypt(zeabur_api_key) if zeabur_api_key else None
            
            if gemini_api_key is not None:
                user.gemini_api_key = TokenManager._encrypt(gemini_api_key) if gemini_api_key else None

            if openrouter_api_key is not None:
                user.openrouter_api_key = TokenManager._encrypt(openrouter_api_key) if openrouter_api_key else None
            
            if ai_provider is not None:
                user.ai_provider = ai_provider
            
            if ai_model is not None:
                user.ai_model = ai_model
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    @staticmethod
    def get_ai_settings(google_id: str) -> Optional[dict]:
        """
        取得用戶的 AI 設定
        
        Returns:
            包含 ai_provider, ai_model, has_zeabur_key, has_gemini_key, has_openrouter_key 的字典
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                return None
            
            return {
                "ai_provider": user.ai_provider if user.ai_provider else "zeabur",
                "ai_model": user.ai_model if user.ai_model else "deepseek/deepseek-v4-flash",
                "has_zeabur_key": bool(user.zeabur_api_key),
                "has_gemini_key": bool(user.gemini_api_key),
                "has_openrouter_key": bool(user.openrouter_api_key)
            }
        finally:
            session.close()
    
    @staticmethod
    def get_ai_api_key(google_id: str, provider: str = None) -> Optional[str]:
        """
        取得解密後的 AI API Key
        
        Args:
            google_id: 用戶的 Google ID
            provider: 'zeabur', 'gemini' 或 'openrouter'（若未指定，使用用戶設定的 provider）
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                return None
            
            active_provider = provider or user.ai_provider or "zeabur"
            
            if active_provider == "openrouter":
                return TokenManager._decrypt(user.openrouter_api_key) if user.openrouter_api_key else None
            elif active_provider == "gemini":
                return TokenManager._decrypt(user.gemini_api_key) if user.gemini_api_key else None
            else:
                return TokenManager._decrypt(user.zeabur_api_key) if user.zeabur_api_key else None
        finally:
            session.close()
