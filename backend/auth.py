import requests
import os
from dotenv import load_dotenv
from database import SessionLocal, User
from cryptography.fernet import Fernet

# Load environment variables from .env file
load_dotenv()

# Initialize Encryption
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
try:
    cipher_suite = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None
except Exception as e:
    print(f"⚠️ Encryption Key Error: {str(e)}")
    print("⚠️ Encryption disabled. Fix ENCRYPTION_KEY in .env or Zeabur settings.")
    cipher_suite = None

class TokenManager:
    @staticmethod
    def _encrypt(value):
        if not value or not cipher_suite:
            return value
        try:
            return cipher_suite.encrypt(value.encode()).decode()
        except Exception:
            return value

    @staticmethod
    def _decrypt(value):
        if not value or not cipher_suite:
            return value
        try:
            return cipher_suite.decrypt(value.encode()).decode()
        except Exception:
            # Lazy Migration: If decryption fails (e.g. old plaintext data), return original
            return value

    @staticmethod
    def save_user_token(google_id, long_lived_token, app_id=None, app_secret=None):
        """Save or update user's Facebook token in the database (Encrypted)."""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if not user:
                user = User(google_id=google_id)
                session.add(user)
            
            # Encrypt sensitive data
            user.fb_access_token = TokenManager._encrypt(long_lived_token)
            
            if app_id:
                user.fb_app_id = app_id
            if app_secret:
                # Encrypt App Secret too
                user.fb_app_secret = TokenManager._encrypt(app_secret)
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def get_user_token(google_id):
        """Retrieve the long-lived token for a specific user (Decrypted)."""
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.google_id == google_id).first()
            if user:
                return TokenManager._decrypt(user.fb_access_token)
            return None
        finally:
            session.close()

    @staticmethod
    def exchange_for_long_lived_token(app_id, app_secret, short_lived_token, user_id):
        """
        Exchange a short-lived user access token for a long-lived one (60 days).
        https://developers.facebook.com/docs/facebook-login/guides/access-tokens/get-long-lived
        """
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
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
                TokenManager.save_user_token(
                    google_id=user_id,
                    long_lived_token=data["access_token"],
                    app_id=app_id,
                    app_secret=app_secret
                )
                return True, "Token exchanged and saved successfully."
            else:
                return False, data.get("error", {}).get("message", "Unknown error during token exchange.")
        except Exception as e:
            return False, str(e)
