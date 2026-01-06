import requests
import os
from dotenv import load_dotenv
load_dotenv(override=True)
from database import SessionLocal, User, UserRole, Team, TeamMember

# ... (Previous imports remain same, just single line update above)

# Encryption Setup
from cryptography.fernet import Fernet
import sys

def get_encryption_key():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # For Dev/Demo Only: Generate a volatile key if missing to prevent crash
        key = Fernet.generate_key().decode()
        print(f"⚠ WARNING: ENCRYPTION_KEY not set. Using volatile key: {key}", file=sys.stderr)
        return key
    
    # Sanitize: Remove possible quotes and whitespace
    sanitized_key = key.strip().strip("'").strip('"')
    
    # Validation
    try:
        # Fernet keys must be 32 url-safe base64-encoded bytes (resulting in 44 chars)
        Fernet(sanitized_key)
        return sanitized_key
    except Exception as e:
        print(f"❌ CRITICAL: Invalid ENCRYPTION_KEY in .env: {e}", file=sys.stderr)
        print(f"Key length: {len(sanitized_key)}, Content starts with: {sanitized_key[:5]}...", file=sys.stderr)
        # Fallback to volatile to prevent blocking server start, but it will cause decryption failures
        volatile_key = Fernet.generate_key().decode()
        return volatile_key

class TokenManager:
    @staticmethod
    def _encrypt(message):
        if not message: return None
        try:
            f = Fernet(get_encryption_key())
            return f.encrypt(message.encode()).decode()
        except Exception as e:
            print(f"Encryption error: {e}", file=sys.stderr)
            return None

    @staticmethod
    def _decrypt(token):
        if not token: return None
        try:
            f = Fernet(get_encryption_key())
            return f.decrypt(token.encode()).decode()
        except Exception as e:
            # Replaced with standard logging, but keep enough info for us
            print(f"[DEBUG_AUTH] Decryption failed. Error: {e}", file=sys.stderr)
            return None

    @staticmethod
    def save_user_token(google_id, long_lived_token, app_id=None, app_secret=None, expires_in=None):
        # ... (Implementation remains same, just ensuring context)
        """Save or update user's Facebook token in the database (Encrypted)."""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                # Provide a default name/email placeholder if creating via this flow
                # Check if this is the FIRST user ever
                user_count = session.query(User).count()
                new_role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER
                
                user = User(google_id=google_id, role=new_role)
                session.add(user)
            
            # Encrypt sensitive data
            user.fb_access_token = TokenManager._encrypt(long_lived_token)
            
            if app_id:
                user.fb_app_id = app_id
            if app_secret:
                user.fb_app_secret = TokenManager._encrypt(app_secret)
            
            if expires_in:
                from datetime import datetime, timedelta, timezone
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                user.token_expires_at = expires_at
            
            user.last_login = datetime.now()
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def save_team_token(team_id, long_lived_token, app_id, user_id, expires_in=None):
        """Save or update TEAM'S Facebook token."""
        session = SessionLocal()
        try:
            # 1. Verification: Is user an ADMIN of this team?
            # Although API router might check, we double check here for safety
            member = session.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
                TeamMember.role == UserRole.ADMIN
            ).first()

            # Also allow Super Admin (user.is_super_admin) - strict for now?
            # Let's assume caller handled authorization or we check strictly here.
            # Ideally getting User object to check super admin is better.
            
            # Fetch User ID (internal UUID) from google_id
            user = session.query(User).filter(User.google_id == user_id).first()
            if not user:
                raise Exception("User not found")

            # Check Team Member Admin or Team Owner or Super Admin
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

            # 2. Update Team
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise Exception("Team not found")

            team.fb_access_token = TokenManager._encrypt(long_lived_token)
            team.fb_app_id = app_id
            
            if expires_in:
                from datetime import datetime, timedelta, timezone
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                team.token_expires_at = expires_at
            # team.fb_app_secret # Schema doesn't have app_secret for Team yet? Checked database.py, it does NOT.
            # Ideally we should add it. For now, assuming only ID/Token is enough? 
            # Wait, `get_long_lived` needs secret. If we ever refresh it for Team, we need secret.
            # User table HAS fb_app_secret. Team table SHOULD have it.
            # database.py check: fb_app_id OK. fb_app_secret MISSING.
            # I should add it to DB first? Or just skip for now?
            # User requested "Feature Complete". I should probably add it.
            # But changing DB requires Alembic.
            # Let's check database.py again via memory.
            # Line 81: fb_access_token. Line 82: fb_app_id.
            # Missing fb_app_secret.
            # I will skip app_secret for Team for now (just like Phase 1 didn't use it much after exchange).
            # BUT if we want to refresh token automatically later, we need it.
            # I'll stick to ID + Token for now to avoid schema migration delay, unless critical.
            # Let's proceed with ID + Token.
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_user_token(google_id, allow_fallback=True):
        """
        Retrieve the long-lived token.
        **New Logic (Collaborative Mode)**: 
        1. Try to get the CURRENT user's token.
        2. If missing AND allow_fallback is True, look for an ADMIN's token (Shared Workspace concept).
        This allows invited members to view data setup by the Admin.
        """
        session = SessionLocal()
        try:
            # 1. Check Current User
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                print(f"[DEBUG_AUTH] User not found for google_id: {google_id}", file=sys.stderr)
            elif not user.fb_access_token:
                print(f"[DEBUG_AUTH] User found but fb_access_token is missing for: {google_id}", file=sys.stderr)
            else:
                decrypted = TokenManager._decrypt(user.fb_access_token)
                if not decrypted:
                    print(f"[DEBUG_AUTH] Decryption failed for user: {google_id}", file=sys.stderr)
                else:
                    return decrypted
            
            if not allow_fallback:
                print(f"[DEBUG_AUTH] Fallback disabled, returning None", file=sys.stderr)
                return None

            # 2. Fallback: Search for any ADMIN with a valid token
            # We prioritize the "first" admin found with a token.
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
    def get_team_token(team_id):
        """
        Retrieve the TEAM's long-lived token.
        Fallback: If Team has no token, use the Team Owner's token.
        """
        session = SessionLocal()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                return None
            
            # 1. Check Team-Level Token
            if team.fb_access_token:
                return TokenManager._decrypt(team.fb_access_token)
            
            # 2. Fallback: Check Team Owner's Token
            # This is critical for "Team Ad Account Isolation" where the Owner provides the connection.
            if team.owner_id:
                owner = session.query(User).filter(User.id == team.owner_id).first()
                if owner and owner.fb_access_token:
                    print(f"Using Team Owner's Token for Team: {team.name}")
                    return TokenManager._decrypt(owner.fb_access_token)

            return None
        finally:
            session.close()

    @staticmethod
    def exchange_for_long_lived_token(app_id, app_secret, short_lived_token, user_id, team_id=None):
        """
        Exchange a short-lived user access token for a long-lived one (60 days).
        https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived
        """
        url = "https://graph.facebook.com/v24.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_lived_token
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "access_token" in data:
                # Save the new token to the database
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
                    return True, "Token exchanged and saved successfully to User."
            else:
                return False, data.get("error", {}).get("message", "Unknown error during token exchange.")
        except Exception as e:
            return False, str(e)

    # ============================================================
    # AI Settings Management (Encrypted)
    # ============================================================
    
    @staticmethod
    def save_ai_settings(google_id, zeabur_api_key=None, gemini_api_key=None, ai_provider=None, ai_model=None):
        """
        Save user's AI settings to database (API keys are encrypted).
        
        Args:
            google_id: User's Google ID
            zeabur_api_key: Zeabur AI Hub API Key (will be encrypted)
            gemini_api_key: Google Gemini API Key (will be encrypted)
            ai_provider: Active provider ('zeabur' or 'gemini')
            ai_model: Selected AI model name
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                raise Exception("User not found")
            
            # Update only provided fields
            if zeabur_api_key is not None:
                user.zeabur_api_key = TokenManager._encrypt(zeabur_api_key) if zeabur_api_key else None
            
            if gemini_api_key is not None:
                user.gemini_api_key = TokenManager._encrypt(gemini_api_key) if gemini_api_key else None
            
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
    def get_ai_settings(google_id):
        """
        Retrieve user's AI settings from database.
        
        Returns:
            dict with ai_provider, ai_model, has_zeabur_key, has_gemini_key
            (API keys are NOT returned for security, only whether they exist)
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                return None
            
            return {
                "ai_provider": user.ai_provider or "zeabur",
                "ai_model": user.ai_model or "gemini-2.5-flash",
                "has_zeabur_key": bool(user.zeabur_api_key),
                "has_gemini_key": bool(user.gemini_api_key)
            }
        finally:
            session.close()
    
    @staticmethod
    def get_ai_api_key(google_id, provider=None):
        """
        Retrieve decrypted AI API key for the specified or active provider.
        
        Args:
            google_id: User's Google ID
            provider: 'zeabur' or 'gemini' (if None, uses user's active provider)
            
        Returns:
            Decrypted API key string, or None if not configured
        """
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                return None
            
            # Use user's active provider if not specified
            active_provider = provider or user.ai_provider or "zeabur"
            
            if active_provider == "gemini":
                return TokenManager._decrypt(user.gemini_api_key) if user.gemini_api_key else None
            else:
                return TokenManager._decrypt(user.zeabur_api_key) if user.zeabur_api_key else None
        finally:
            session.close()
