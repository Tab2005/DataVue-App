from datetime import datetime, timedelta
import os
import sys
import json
import asyncio
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from database import User
from auth import TokenManager

# Simple in-memory cache for GSC analytics data
# Format: { cache_key: { 'data': [...], 'expires_at': timestamp } }
_gsc_cache = {}
_CACHE_TTL = 300  # 5 minutes

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
        Features:
        - In-memory caching (5 min TTL)
        - Parallel batch fetching (3 concurrent requests)
        - Auto-pagination up to 25,000 rows
        """
        global _gsc_cache
        
        # Generate cache key
        dim_str = ','.join(sorted(dimensions)) if isinstance(dimensions, list) else dimensions
        cache_key = f"{site_url}:{start_date}:{end_date}:{dim_str}"
        
        # Check cache
        if cache_key in _gsc_cache:
            cached = _gsc_cache[cache_key]
            if time.time() < cached['expires_at']:
                print(f"[GSC Cache] HIT - returning {len(cached['data'])} cached rows")
                return cached['data'], None
            else:
                # Expired, remove from cache
                del _gsc_cache[cache_key]
                print(f"[GSC Cache] EXPIRED - refetching")
        
        creds = GSCService.get_credentials(user)
        if not creds:
            return None, "No GSC credentials found"
            
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            batch_size = 1000
            max_rows = 25000
            concurrent_batches = 3  # Reduced from 5 to avoid SSL errors
            
            def fetch_batch(creds_dict, start_row):
                """Fetch a single batch of rows with its own service instance"""
                try:
                    # Create independent credentials and service for each thread
                    thread_creds = Credentials(
                        token=creds_dict['token'],
                        refresh_token=creds_dict['refresh_token'],
                        token_uri=creds_dict['token_uri'],
                        client_id=creds_dict['client_id'],
                        client_secret=creds_dict['client_secret'],
                        scopes=creds_dict['scopes']
                    )
                    thread_service = build('searchconsole', 'v1', credentials=thread_creds)
                    
                    request = {
                        'startDate': start_date,
                        'endDate': end_date,
                        'dimensions': dimensions,
                        'rowLimit': batch_size,
                        'startRow': start_row
                    }
                    response = thread_service.searchanalytics().query(siteUrl=site_url, body=request).execute()
                    return start_row, response.get('rows', []), None
                except Exception as e:
                    return start_row, [], str(e)
            
            # Prepare credentials dict for passing to threads
            creds_dict = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }
            
            
            all_rows = []
            start_row = 0
            
            start_time = time.time()
            
            while start_row < max_rows:
                # Prepare batch of start_rows for parallel fetching
                batch_starts = []
                for i in range(concurrent_batches):
                    batch_start = start_row + (i * batch_size)
                    if batch_start < max_rows:
                        batch_starts.append(batch_start)
                
                if not batch_starts:
                    break
                
                # Fetch in parallel using ThreadPoolExecutor
                batch_results = {}
                should_stop = False
                
                with ThreadPoolExecutor(max_workers=concurrent_batches) as executor:
                    futures = {executor.submit(fetch_batch, creds_dict, bs): bs for bs in batch_starts}
                    
                    for future in as_completed(futures):
                        try:
                            batch_start, rows, error = future.result()
                            if error:
                                print(f"[GSC Parallel] Error at batch {batch_start}: {error}")
                            batch_results[batch_start] = rows
                            
                            if len(rows) < batch_size:
                                should_stop = True
                        except Exception as e:
                            print(f"[GSC Parallel] Exception in future: {e}")
                
                # Add results in order
                for bs in sorted(batch_results.keys()):
                    rows = batch_results[bs]
                    if rows:
                        all_rows.extend(rows)
                    if not rows or len(rows) < batch_size:
                        should_stop = True
                        break
                
                if should_stop:
                    break
                    
                start_row += concurrent_batches * batch_size
                print(f"[GSC Parallel] Loaded {len(all_rows)} rows so far...")
            
            elapsed = time.time() - start_time
            print(f"[GSC Parallel] Total: {len(all_rows)} rows in {elapsed:.2f}s")
            
            # Store in cache
            _gsc_cache[cache_key] = {
                'data': all_rows,
                'expires_at': time.time() + _CACHE_TTL
            }
            
            return all_rows, None
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None, str(e)
