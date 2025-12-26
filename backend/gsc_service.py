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
            # Create a flow instance to exchange the code
            # IMPORTANT: Do NOT specify scopes here - let Google use the scopes from the auth code
            # This avoids "Scope has changed" errors when scopes in code differ from what we specify
            
            from google_auth_oauthlib.flow import Flow
            
            client_config = {
                "web": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            
            # Use None for scopes to accept whatever was granted in the authorization
            flow = Flow.from_client_config(
                client_config,
                scopes=None,  # Accept granted scopes from auth code
                redirect_uri="postmessage"  # Standard for React Google Login 'response_type="code"'
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Update User
            user.gsc_access_token = credentials.token
            user.gsc_refresh_token = credentials.refresh_token
            # Calculate expiration locally if needed, or store raw expiry
            # user.gsc_expires_at = ... (Optional for now, refresh token is key)
            
            db.commit()
            return True, "Successfully connected to Google Search Console"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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
