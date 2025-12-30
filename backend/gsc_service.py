from datetime import datetime, timedelta
import os
import sys
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from database import User
from auth import TokenManager

class GSCService:
    """
    Service for Google Search Console Integration.
    Handles authentication, token management, and data fetching.
    """
    
    # Scopes required for GSC
    SCOPES = [
        'https://www.googleapis.com/auth/webmasters.readonly',
        'openid',
        'email',
        'profile'
    ]
    
    @staticmethod
    def exchange_code(user: User, code: str, db: Session):
        """
        Exchanges the authorization code for access/refresh tokens and updates the User model.
        """
        try:
            # Try manual token exchange using requests to debug/bypass library issues
            import requests
            
            client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
            
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": "postmessage",
                "grant_type": "authorization_code"
            }
            
            print(f"DEBUG: Attempting manual token exchange with clientId={client_id[:10]}... and SecretPrefix={client_secret[:3] if client_secret else 'NONE'}...")
            print(f"DEBUG: Auth Code Length: {len(code)}")

            # Try multiple redirect_uris to handle different frontend configurations
            redirect_uris = [
                "postmessage", 
                "http://localhost:5173", 
                "http://localhost:5173/"
            ]
            
            response = None
            success = False
            
            # 1. Standard attempts with Secret
            for uri in redirect_uris:
                print(f"DEBUG: Trying URI='{uri}' WITH SECRET")
                data["redirect_uri"] = uri
                data["client_secret"] = client_secret # Ensure secret is there
                
                response = requests.post(token_url, data=data)
                print(f"DEBUG: Status: {response.status_code}")
                
                if response.status_code == 200:
                    success = True
                    break
                
                err = response.json().get('error')
                print(f"DEBUG: Error: {err}")
                
            # 2. If all failed, try WITHOUT Secret (in case it's treated as Public Client)
            if not success:
               print("DEBUG: Trying attempts WITHOUT SECRET")
               del data["client_secret"]
               for uri in redirect_uris:
                    print(f"DEBUG: Trying URI='{uri}' NO SECRET")
                    data["redirect_uri"] = uri
                    response = requests.post(token_url, data=data)
                    print(f"DEBUG: Status: {response.status_code}")
                    if response.status_code == 200:
                        success = True
                        break
                    print(f"DEBUG: Error: {response.json().get('error')}")

            if not success:
                error_detail = response.json() if response else {"error": "Unknown"}
                print(f"ERROR BODY: {error_detail}")
                return False, f"Google Auth Error: {error_detail.get('error')} - {error_detail.get('error_description')}"
                
            tokens = response.json()
            
            # Update User
            user.gsc_access_token = tokens.get("access_token")
                
            if not success:
                error_detail = response.json() if response else {"error": "Unknown"}
                print(f"ERROR BODY: {error_detail}")
                return False, f"Google Auth Error: {error_detail.get('error')} - {error_detail.get('error_description')}"
                
            tokens = response.json()
            
            # Update User
            user.gsc_access_token = tokens.get("access_token")
            # Refresh token might not be returned if not requested (access_type=offline) 
            # or if user already approved properly. 
            if "refresh_token" in tokens:
                user.gsc_refresh_token = tokens.get("refresh_token")
            
            user.gsc_expires_at = datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
            
            db.commit()
            return True, "Successfully connected to Google Search Console"
            
        except Exception as e:
            import traceback
            print("=== GSC AUTH ERROR START ===")
            traceback.print_exc()
            print("=== GSC AUTH ERROR END ===")
            return False, str(e)

    @staticmethod
    def get_credentials(user: User):
        """
        Constructs google.oauth2.credentials.Credentials from user's stored tokens.
        Handles token refresh if expired.
        """
        if not user.gsc_access_token or not user.gsc_refresh_token:
            return None
        
        # specific to how we stored them (encrypted or raw? Assuming raw for now based on database.py)
        # Ideally should use TokenManager for encryption, but for MVP let's check database.py approach
        # The database.py definition: gsc_access_token = Column(String)
        
        # Check if we need to decrypt (Assuming standard practice in this codebase is manual encryption if sensitive)
        # For this step, I'll assume they are stored as raw strings for simplicity, 
        # OR use TokenManager if it has generic encrypt/decrypt.
        # Checking auth.py previously, TokenManager handles FB tokens. 
        # I will implement basic storage first.
        
        token = user.gsc_access_token
        refresh_token = user.gsc_refresh_token
        
        creds = Credentials(
            token=token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=GSCService.SCOPES
        )
        return creds

    @staticmethod
    def list_sites(user: User):
        """
        Lists all sites verified in GSC for the user.
        """
        creds = GSCService.get_credentials(user)
        if not creds:
            return None, "No GSC credentials found"
            
        try:
            service = build('searchconsole', 'v1', credentials=creds)
            site_list = service.sites().list().execute()
            return site_list.get('siteEntry', []), None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_analytics(user: User, site_url: str, start_date: str, end_date: str, dimensions=['date']):
        """
        Fetches search analytics data (clicks, impressions, ctr, position).
        """
        creds = GSCService.get_credentials(user)
        if not creds:
            return None, "No GSC credentials found"
            
        try:
            service = build('searchconsole', 'v1', credentials=creds)
            request = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions,
                'rowLimit': 1000
            }
            response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
            return response.get('rows', []), None
        except Exception as e:
            return None, str(e)
