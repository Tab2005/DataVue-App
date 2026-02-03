from datetime import datetime, timedelta
import os
import sys
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session
from database import User
from auth import TokenManager
from cache import generate_cache_key, get_cached, set_cached, analytics_cache
from redis_cache import get_cached_redis, set_cached_redis


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
                
                response = requests.post(token_url, data=data, timeout=30)
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
                    response = requests.post(token_url, data=data, timeout=30)
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
    def get_credentials(user: User, db: Session = None):
        """
        Constructs google.oauth2.credentials.Credentials from user's stored tokens.
        Handles token refresh if expired.
        
        Args:
            user: User object
            db: Database session (optional, for updating refreshed token)
        """
        if not user.gsc_access_token or not user.gsc_refresh_token:
            return None
        
        token = user.gsc_access_token
        refresh_token = user.gsc_refresh_token
        
        # 取得 expiry 時間（如果有的話）
        expiry = user.gsc_expires_at if hasattr(user, 'gsc_expires_at') else None
        
        creds = Credentials(
            token=token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=GSCService.SCOPES,
            expiry=expiry  # 加入 expiry 讓 expired 檢查正確運作
        )
        
        # 檢查是否需要刷新 token
        needs_refresh = False
        if expiry:
            from datetime import datetime
            if creds.expired or (expiry - datetime.utcnow()).total_seconds() < 300:
                needs_refresh = True
        
        if needs_refresh and db:
            try:
                from google.auth.transport.requests import Request as GoogleAuthRequest
                creds.refresh(GoogleAuthRequest())
                print("[GSC] Token refreshed successfully")
                # 回寫新 token 到資料庫
                from datetime import datetime, timedelta
                user.gsc_access_token = creds.token
                user.gsc_expires_at = datetime.utcnow() + timedelta(seconds=3600)
                db.commit()
                print("[GSC] New token saved to database")
            except Exception as e:
                print(f"[GSC] Token refresh failed: {e}")
                # 不返回 None，讓 googleapiclient 嘗試自動刷新
        
        return creds

    @staticmethod
    def list_sites(user: User, db: Session = None):
        """
        Lists all sites verified in GSC for the user.
        """
        creds = GSCService.get_credentials(user, db)
        if not creds:
            return None, "No GSC credentials found"
            
        try:
            service = build('searchconsole', 'v1', credentials=creds)
            site_list = service.sites().list().execute()
            return site_list.get('siteEntry', []), None
        except Exception as e:
            return None, str(e)

    @staticmethod
    def get_analytics(user: User, site_url: str, start_date: str, end_date: str, dimensions=['date'], limit: int = None, offset: int = 0, db: Session = None, dimension_filters: list = None):
        """
        Fetches search analytics data (clicks, impressions, ctr, position).
        Paginates through all available data from the GSC API and uses a cache.
        Supports dimension_filters for server-side filtering.
        """
        # 1. Generate Cache Key
        cache_params = {
            "dimensions": sorted(dimensions),
            "filters": dimension_filters
        }
        
        base_cache_key = generate_cache_key(
            "gsc_analytics",
            user.id,
            site_url,
            start_date,
            end_date,
            json.dumps(cache_params, sort_keys=True)
        )

        page_cache_key = None
        if (limit is not None and limit > 0) or (offset and offset > 0):
            page_cache_key = generate_cache_key(
                "gsc_analytics_page",
                user.id,
                site_url,
                start_date,
                end_date,
                json.dumps(cache_params, sort_keys=True),
                str(offset or 0),
                str(limit) if limit is not None else ""
            )

        # 2. Check Cache (Redis -> In-memory fallback)
        use_redis = bool(os.getenv("REDIS_URL"))
        redis_ttl = int(os.getenv("GSC_REDIS_TTL_SECONDS", "900"))

        if use_redis:
            if limit is None and (offset is None or offset == 0):
                cached_data = get_cached_redis(base_cache_key)
                if cached_data is not None:
                    print(f"[GSC REDIS HIT] Returning {len(cached_data)} rows.")
                    return cached_data, None
            else:
                cached_full = get_cached_redis(base_cache_key)
                if cached_full is not None:
                    sliced = cached_full[offset or 0: (offset or 0) + limit] if limit else cached_full[offset or 0:]
                    return sliced, None

                if page_cache_key:
                    cached_page = get_cached_redis(page_cache_key)
                    if cached_page is not None:
                        return cached_page, None

        if limit is None and (offset is None or offset == 0):
            cached_data = get_cached(analytics_cache, base_cache_key)
            if cached_data is not None:
                return cached_data, None
        else:
            cached_full = get_cached(analytics_cache, base_cache_key)
            if cached_full is not None:
                sliced = cached_full[offset or 0: (offset or 0) + limit] if limit else cached_full[offset or 0:]
                return sliced, None

            if page_cache_key:
                cached_page = get_cached(analytics_cache, page_cache_key)
                if cached_page is not None:
                    return cached_page, None

        creds = GSCService.get_credentials(user, db)
        if not creds:
            return None, "No GSC credentials found"
            
        try:
            service = build('searchconsole', 'v1', credentials=creds)
            
            all_rows = []

            # Prepare API request body
            request_body = {
                'startDate': start_date,
                'endDate': end_date,
                'dimensions': dimensions
            }
            
            if dimension_filters:
                request_body['dimensionFilterGroups'] = [{
                    'filters': dimension_filters
                }]

            if limit is not None or (offset and offset > 0):
                request_body['rowLimit'] = limit or 25000
                request_body['startRow'] = offset or 0

                response = service.searchanalytics().query(siteUrl=site_url, body=request_body).execute()
                all_rows = response.get('rows', [])
            else:
                start_row = 0
                batch_size = 25000

                while True:
                    request_body['rowLimit'] = batch_size
                    request_body['startRow'] = start_row

                    response = service.searchanalytics().query(siteUrl=site_url, body=request_body).execute()
                    rows = response.get('rows', [])

                    if not rows:
                        break

                    all_rows.extend(rows)
                    if len(rows) < batch_size:
                        break

                    start_row += batch_size
                    print(f"[GSC Pagination] Loaded {len(all_rows)} rows so far...")

            # 3. Set Cache
            redis_set = False
            if use_redis:
                if limit is not None or (offset and offset > 0):
                    if page_cache_key:
                        redis_set = set_cached_redis(page_cache_key, all_rows, redis_ttl)
                else:
                    redis_set = set_cached_redis(base_cache_key, all_rows, redis_ttl)

            if not use_redis or not redis_set:
                if limit is not None or (offset and offset > 0):
                    if page_cache_key:
                        set_cached(analytics_cache, page_cache_key, all_rows)
                else:
                    set_cached(analytics_cache, base_cache_key, all_rows)

            return all_rows, None
        except Exception as e:
            return None, str(e)

