"""
Debug Router
Debug 和診斷端點

此 Router 從 main.py 抽取出來，包含各種測試和診斷端點。
這些端點僅供開發和除錯使用。

警告：生產環境應考慮禁用這些端點。
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import sys
import os

from database import SessionLocal, User, Team, TeamMember, UserRole, engine
from dependencies import get_db, get_current_team, get_super_admin

router = APIRouter(
    prefix="/api/debug", 
    tags=["debug"],
    dependencies=[Depends(get_super_admin)]
)


@router.get("/fix-schema")
def fix_db_schema():
    """修復資料庫 Schema - 添加缺失的欄位。"""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = [c["name"] for c in inspector.get_columns("teams")]
        
        result = {
            "table": "teams",
            "existing_columns": columns,
            "actions_taken": []
        }
        
        if "token_expires_at" not in columns:
            try:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE teams ADD COLUMN token_expires_at TIMESTAMP"))
                    conn.commit()
                result["actions_taken"].append("Added token_expires_at")
            except Exception as e:
                result["actions_taken"].append(f"Failed to add token_expires_at: {e}")
        else:
            result["actions_taken"].append("token_expires_at already exists")
            
        return result
    except Exception as e:
        return {"error": str(e)}


@router.get("/permissions")
def debug_permissions(team_id: str, user: User = Depends(get_super_admin)):
    """檢查用戶在團隊中的權限。"""
    session = SessionLocal()
    try:
        member = session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id
        ).first()
        
        is_admin = False
        if user.is_super_admin:
            is_admin = True
        elif member and member.role == UserRole.ADMIN:
            is_admin = True
            
        return {
            "user_name": user.name,
            "google_id": user.google_id,
            "internal_id": user.id,
            "is_super_admin": user.is_super_admin,
            "team_id": team_id,
            "team_member_role": member.role.value if member else "NOT_MEMBER",
            "computed_is_admin": is_admin
        }
    finally:
        session.close()


@router.get("/super-admin-check")
def debug_super_admin_check(user: User = Depends(get_super_admin)):
    """
    診斷端點：檢查 Super Admin 環境變數和用戶狀態
    """
    super_admin_email_env = os.getenv("SUPER_ADMIN_EMAIL", "NOT_SET")
    
    email_match = False
    if super_admin_email_env and super_admin_email_env != "NOT_SET" and user.email:
        allowed_emails = [e.strip().lower() for e in super_admin_email_env.split(",")]
        email_match = user.email.strip().lower() in allowed_emails
    
    return {
        "diagnosis": "Super Admin Check",
        "user_found": True,
        "user_email_in_db": user.email,
        "is_super_admin_in_db": user.is_super_admin,
        "env_SUPER_ADMIN_EMAIL": super_admin_email_env,
        "email_comparison": {
            "match": email_match
        }
    }


@router.get("/health")
def debug_health():
    """Debug health check with detailed info."""
    db_info = "Unknown"
    try:
        db_url = os.getenv("DATABASE_URL", "")
        if "postgresql" in db_url.lower():
            db_info = "PostgreSQL"
        else:
            db_info = "SQLite"
    except:
        pass
    
    return {
        "status": "ok",
        "database_type": db_info,
        "google_client_id_set": bool(GOOGLE_CLIENT_ID)
    }


@router.get("/test-auction-metrics")
async def test_auction_metrics(
    account_id: str,
    level: str = "all",
    user: User = Depends(get_super_admin),
    team: Team = Depends(get_current_team)
):
    """
    測試 auction_bid 和 auction_competitiveness 指標
    
    Usage: 
        /api/debug/test-auction-metrics?account_id=act_XXXXX
    """
    from async_services import AsyncFacebookService
    
    team_id = team.id if team else None
    results = {}
    
    levels_to_test = ["account", "campaign", "ad"] if level == "all" else [level]
    
    for test_level in levels_to_test:
        try:
            data, error = await AsyncFacebookService.get_analytics_data(
                user_id, account_id, 
                "2024-01-01", "2024-01-31",
                level=test_level,
                team_id=team_id
            )
            results[test_level] = {
                "success": not error,
                "error": error,
                "sample_count": len(data) if isinstance(data, list) else 0
            }
        except Exception as e:
            results[test_level] = {"success": False, "error": str(e)}
    
    return results


@router.get("/check-permissions")
async def check_token_permissions(
    user: User = Depends(get_super_admin),
    team: Team = Depends(get_current_team)
):
    """
    檢查目前 Access Token 的權限範圍
    顯示可以存取哪些 Facebook/Instagram API
    """
    from auth import TokenManager
    
    team_id = team.id if team else None
    token = TokenManager.get_user_token(user_id, team_id=team_id)
    
    if not token:
        return {"error": "No token found", "team_id": team_id}
    
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            # Debug token
            debug_resp = await client.get(
                "https://graph.facebook.com/debug_token",
                params={
                    "input_token": token,
                    "access_token": token
                }
            )
            debug_data = debug_resp.json()
            
            return {
                "token_debug": debug_data,
                "team_id": team_id
            }
    except Exception as e:
        return {"error": str(e)}
