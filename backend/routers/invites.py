from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import SessionLocal, Team, TeamMember, TeamInvite, User, UserRole
from schemas import InviteCreateResponse, InviteInfoResponse
from dependencies import get_db, get_current_user
import uuid
import secrets
from datetime import datetime, timedelta

router = APIRouter()

BASE_URL = "http://localhost:5173" # Defines Frontend URL for link generation

def get_base_url():
    # Helper to get frontend base URL
    # Ideally from env var in prod
    import os
    return os.getenv("FRONTEND_URL", "http://localhost:5173")

@router.post("/teams/{team_id}/invites", response_model=InviteCreateResponse)
def create_invite_link(
    team_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a 24-hour expiration invite link.
    Only Team Admins can generate links.
    """
    # 1. Verify Team Membership & Role
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if not member or member.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admins can generate invites")

    # 2. Generate Code
    code = secrets.token_urlsafe(16)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    # 3. Save to DB
    invite = TeamInvite(
        team_id=team_id,
        code=code,
        expires_at=expires_at,
        created_by=current_user.id
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    # 4. Construct URL
    url = f"{get_base_url()}/invite/{code}"

    return InviteCreateResponse(
        code=code,
        invite_url=url,
        expires_at=expires_at
    )

@router.get("/invites/{code}", response_model=InviteInfoResponse)
def get_invite_info(code: str, db: Session = Depends(get_db)):
    print(f"DEBUG: Fetching invite for code: {code}", flush=True)
    """
    Public Endpoint: Get Invite Info (Team Name, Expiry) to show on landing page.
    """
    invite = db.query(TeamInvite).filter(TeamInvite.code == code).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # Check Expiry
    is_valid = invite.expires_at > datetime.utcnow()

    # Get Team Info
    team = db.query(Team).filter(Team.id == invite.team_id).first()
    
    # Get Inviter Info
    inviter = db.query(User).filter(User.id == invite.created_by).first()

    return InviteInfoResponse(
        team_id=team.id,
        team_name=team.name if team else "Unknown Team",
        inviter_name=inviter.name if inviter else "Team Admin",
        expires_at=invite.expires_at,
        is_valid=is_valid
    )

@router.post("/invites/{code}/accept")
def accept_invite(
    code: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Confirm joining the team.
    """
    # 1. Validate Invite
    invite = db.query(TeamInvite).filter(TeamInvite.code == code).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite link has expired")

    # 2. Check if already member
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == invite.team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if existing:
        return {"message": "Already a member of this team", "team_id": invite.team_id}

    # 3. Add to Team
    new_member = TeamMember(
        team_id=invite.team_id,
        user_id=current_user.id,
        role=UserRole.MEMBER # Default role for invited users
    )
    db.add(new_member)
    
    # 4. Update Stats
    invite.used_count += 1
    
    db.commit()

    return {"message": "Successfully joined team", "team_id": invite.team_id}
