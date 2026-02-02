from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from datetime import datetime, timezone
import os
import logging
from database import SessionLocal, User, Team
from auth import TokenManager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
security = HTTPBearer()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Google OAuth token and return user's google_id."""
    token = credentials.credentials
    try:
        # P.S. We could use verify_google_token_basic from dependencies if we wanted to unify more,
        # but for now, we keep the logic extracted.
        id_info = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60
        )
        return id_info['sub']
    except Exception as e:
        logger.error(f"Google Token Verification Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {e}"
        )

class ExchangeRequest(BaseModel):
    app_id: str
    app_secret: str
    short_token: str
    team_id: Optional[str] = None

@router.post("/exchange-token")
def exchange_token_endpoint(request: ExchangeRequest, user_id: str = Depends(verify_google_token)):
    """Exchange short-lived token for long-lived token."""
    success, message = TokenManager.exchange_for_long_lived_token(
        request.app_id, 
        request.app_secret, 
        request.short_token,
        user_id,
        team_id=request.team_id
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@router.get("/token-status")
def get_token_status(team_id: Optional[str] = None, user_id: str = Depends(verify_google_token)):
    """Check the expiration status of the user's OR team's Facebook token."""
    session = SessionLocal()
    try:
        target = None
        if team_id:
            target = session.query(Team).filter(Team.id == team_id).first()
        else:
            target = session.query(User).filter(User.google_id == user_id).first()
        
        token_exists = False
        if target and hasattr(target, 'fb_access_token') and target.fb_access_token:
            token_exists = len(str(target.fb_access_token)) > 10
        
        if not target or not target.token_expires_at:
            return {
                "expires_at": None,
                "days_remaining": None,
                "is_expired": False,
                "token_exists": token_exists
            }
        
        now = datetime.now(timezone.utc)
        expires_at = target.token_expires_at
        
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
             
        delta = expires_at - now
        days_remaining = delta.days
        
        return {
            "expires_at": expires_at.isoformat(),
            "days_remaining": days_remaining,
            "is_expired": days_remaining < 0,
            "token_exists": token_exists
        }
    except Exception as e:
        logger.error(f"Token Status Error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
    finally:
        session.close()
