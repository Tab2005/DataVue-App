from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import SessionLocal, User, UserRole, UserStatus, Team, TeamMember
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import sys

# Reuse the existing security scheme
security = HTTPBearer()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_google_token_basic(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Basic verification that returns the full Google Token Info (ID, Email, Name).
    """
    token = credentials.credentials
    try:
        # P.S. Ideally cache the validation or use a library that handles caching certs
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=60)
        return id_info
    except Exception as e:
        print(f"Token Verification Critical Error: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication Error ({type(e).__name__}): {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    id_info: dict = Depends(verify_google_token_basic), 
    db = Depends(get_db)
) -> User:
    """
    Fetch the full User object from DB based on the verified Google ID.
    Syncs basic profile info (Email, Name) from Google Token.
    """
    google_id = id_info['sub']
    email = id_info.get('email')
    name = id_info.get('name')
    
    user = db.query(User).filter(User.google_id == google_id).first()
    
    if not user:
        print(f"DEBUG: User {google_id} not found. Auto-Registering...", file=sys.stderr)
        
        # Check if this is the FIRST user ever (Global Super Admin candidate)
        user_count = db.query(User).count()
        new_role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER
        
        user = User(
            google_id=google_id, 
            email=email,
            name=name,
            role=new_role,
            status=UserStatus.ACTIVE,
            is_super_admin=(user_count == 0) # First user is Super Admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Auto-Registered: {name} ({email}) as {new_role}", file=sys.stderr)
    else:
        # Auto-Update Profile if missing or changed
        if user.email != email or user.name != name:
             user.email = email
             user.name = name
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.now()
    db.commit()
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.status != UserStatus.ACTIVE:
        print(f"DEBUG: User {current_user.google_id} is INACTIVE", file=sys.stderr)
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    # Allow Super Admin to bypass specific role checks
    if current_user.is_super_admin:
        return current_user

    print(f"DEBUG: Checking Admin Privileges for {current_user.google_id}. Role: {current_user.role}", file=sys.stderr)
    if current_user.role != UserRole.ADMIN:
        print(f"Access Denied: User is not ADMIN", file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_super_admin:
        print(f"Access Denied: User {current_user.email} is NOT Super Admin", file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Super Admin privileges required"
        )
    return current_user

def get_current_team(
    x_team_id: str = Header(None),
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_db)
) -> Team:
    """
    Validates that the user is a member of the requested Team ID (via Header).
    returns the Team object if valid.
    """
    if not x_team_id:
        # If no team header, we might return None or Default Team?
        # For strict multi-tenant, we should require it, OR return None and let endpoint decide.
        return None

    # Verify Membership
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == x_team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if not membership and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Not a member of this team")

    team = db.query(Team).filter(Team.id == x_team_id).first()
    if not team:
         raise HTTPException(status_code=404, detail="Team not found")
         
    return team
