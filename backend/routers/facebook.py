"""
Facebook Router
Facebook Ads API 相關的核心業務端點

此 Router 從 main.py 抽取出來，包含：
- /api/ad-accounts: 取得廣告帳戶列表
- /api/dashboard-data: 取得儀表板資料
- /api/analytics: 取得分析資料
- /api/analytics-trend: 取得趨勢資料
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
import sys
import json

from database import SessionLocal, User, Team, TeamMember, UserRole
from dependencies import get_db, get_current_team, require_module

# Use existing verify_google_token from main.py (will be refactored later)
# For now, import from dependencies or define here
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os

security = HTTPBearer()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Google OAuth token and return user's google_id."""
    token = credentials.credentials
    try:
        id_info = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60
        )
        return id_info['sub']
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")


router = APIRouter(prefix="/api", tags=["facebook"])

# Module access check
fb_ads_check = require_module("fb_ads")


@router.get("/ad-accounts", dependencies=[Depends(fb_ads_check)])
async def get_ad_accounts(
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team),
    db: SessionLocal = Depends(get_db)
):
    """取得用戶可存取的廣告帳戶列表。"""
    from async_services import AsyncFacebookService
    
    team_id = team.id if team else None
    
    # Resolve Owner Status
    current_db_user = db.query(User).filter(User.google_id == user_id).first()
    current_internal_id = current_db_user.id if current_db_user else None
    
    is_owner = False
    if team:
        is_owner = (str(team.owner_id) == str(current_internal_id))

    # Determine Scope
    fetch_team_id = team_id
    if is_owner:
        fetch_team_id = None  # Force User Token for Owner
        
    use_strict = is_owner or (fetch_team_id is None)
    accounts, error = await AsyncFacebookService.get_all_ad_accounts(
        user_id, team_id=fetch_team_id, strict_token=use_strict
    )
    
    # Fallback for Owner
    if (not accounts or error) and is_owner:
        print(f"DEBUG: Primary fetch failed for owner ({error}), retrying...", file=sys.stderr)
        accounts, error = await AsyncFacebookService.get_all_ad_accounts(user_id, team_id=team_id)
    
    if error:
        print(f"❌ Error from FacebookService: {error}", file=sys.stderr)
        return []
        
    # Team Ad Account Isolation
    if team and not is_owner:
        print(f"🔒 Non-Owner Access. Whitelist: {team.visible_ad_account_ids}", file=sys.stderr)
        if team.visible_ad_account_ids:
            try:
                whitelist = json.loads(team.visible_ad_account_ids)
                if isinstance(whitelist, list):
                    whitelist_set = set(str(x) for x in whitelist)
                    filtered_accounts = []
                    
                    for acc in accounts:
                        acc_id = str(acc.get('id', ''))
                        if acc_id in whitelist_set:
                            filtered_accounts.append(acc)
                            continue
                        alt_id = acc_id.replace('act_', '') if 'act_' in acc_id else f'act_{acc_id}'
                        if alt_id in whitelist_set:
                            filtered_accounts.append(acc)
                            
                    accounts = filtered_accounts
                else:
                    accounts = []
            except Exception as e:
                print(f"❌ Whitelist Parse Error: {e}", file=sys.stderr)
                accounts = []
        else:
            accounts = []

    return accounts


@router.get("/dashboard-data", dependencies=[Depends(fb_ads_check)])
async def get_dashboard_data(
    account_id: str = None, 
    days: int = 7, 
    user_id: str = Depends(verify_google_token), 
    team: Team = Depends(get_current_team)
):
    """取得儀表板摘要資料。"""
    from async_services import AsyncFacebookService
    
    team_id = team.id if team else None
    
    if not account_id:
        return {"error": "Account ID is required"}
        
    data, error = await AsyncFacebookService.get_account_insights(
        account_id, user_id, days=days, team_id=team_id
    )
    
    if error:
        return {"error": error}
    return data


@router.get("/analytics", dependencies=[Depends(fb_ads_check)])
async def get_analytics_data(
    account_id: str,
    since: str, 
    until: str, 
    level: str = "account",
    fields: str = None,
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    取得進階分析資料。
    
    Args:
        account_id: Facebook 廣告帳戶 ID
        since: 開始日期 (YYYY-MM-DD)
        until: 結束日期 (YYYY-MM-DD)
        level: 分析層級 (account/campaign/adset/ad)
        fields: 可選的指標欄位（逗號分隔）
    """
    from async_services import AsyncFacebookService
    
    team_id = team.id if team else None
    
    data, error = await AsyncFacebookService.get_custom_report(
        account_id, user_id, since, until, level=level, 
        custom_fields=fields, team_id=team_id
    )
    
    if error:
        return {"error": error}
    return data


@router.get("/analytics-trend", dependencies=[Depends(fb_ads_check)])
async def get_analytics_trend_data(
    account_id: str,
    since: str,
    until: str,
    prev_since: str = None,
    prev_until: str = None,
    user_id: str = Depends(verify_google_token),
    team: Team = Depends(get_current_team)
):
    """
    取得每日趨勢圖表資料。
    """
    from async_services import AsyncFacebookService
    
    team_id = team.id if team else None
    
    data, error = await AsyncFacebookService.get_analytics_trend(
        account_id, user_id, since, until, 
        prev_since=prev_since, prev_until=prev_until,
        team_id=team_id
    )
    
    if error:
        return {"error": error}
    return data
