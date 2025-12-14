from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from database import User, Team, TeamMember, UserRole
from schemas import TeamCreate, TeamResponse, TeamMemberResponse, TeamMemberUpdate, TeamUpdate
from dependencies import get_db, get_current_user, get_admin_user

router = APIRouter(
    tags=["teams"]
)

@router.post("/", response_model=TeamResponse)
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new team. 
    The creator automatically becomes the OWNER/ADMIN of the team.
    """
    # Create Team
    new_team = Team(
        name=team_data.name,
        owner_id=current_user.id
    )
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    
    # Add Creator as Team Member (Admin)
    member = TeamMember(
        team_id=new_team.id,
        user_id=current_user.id,
        role=UserRole.ADMIN
    )
    db.add(member)
    db.commit()
    
    return new_team

@router.get("/me", response_model=List[TeamResponse])
def get_my_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all teams the current user belongs to.
    """
    # Join TeamMember to find teams
    teams = db.query(Team).join(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    return teams

@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # TODO: Verify membership
):
    """
    Get generic team info.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check membership
    member_check = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    # Allow Super Admin to bypass? Or restrict strictly?
    # For now, strict membership check unless super admin.
    if not member_check and not getattr(current_user, 'is_super_admin', False):
         raise HTTPException(status_code=403, detail="Not a member of this team")

    return team

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
def get_team_members(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check membership
    member_check = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if not member_check and not getattr(current_user, 'is_super_admin', False):
         raise HTTPException(status_code=403, detail="Not a member of this team")

    # Eager load user data
    from sqlalchemy.orm import joinedload
    members = db.query(TeamMember).options(joinedload(TeamMember.user)).filter(TeamMember.team_id == team_id).all()
    return members

@router.delete("/{team_id}/members/{user_id}", status_code=204)
def remove_team_member(
    team_id: str,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 2. Check Requester Permissions (Must be Team Admin/Owner or Super Admin)
    requester_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    is_team_admin = requester_membership and requester_membership.role == UserRole.ADMIN
    is_super_admin = getattr(current_user, 'is_super_admin', False)

    if not is_team_admin and not is_super_admin:
        raise HTTPException(status_code=403, detail="Only Team Admins can remove members")

    # 3. Check Target Membership
    target_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()

    if not target_membership:
        raise HTTPException(status_code=404, detail="User is not a member of this team")

    # 4. Protect Owner
    if team.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the Team Owner")

    # 5. Remove
    db.delete(target_membership)
    db.commit()
    return

@router.put("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
def update_team_member_role(
    team_id: str,
    user_id: str,
    role_data: TeamMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # 2. Check Permissions (Requester must be Admin)
    requester_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    is_team_admin = requester_membership and requester_membership.role == UserRole.ADMIN
    is_super_admin = getattr(current_user, 'is_super_admin', False)

    if not is_team_admin and not is_super_admin:
        raise HTTPException(status_code=403, detail="Only Team Admins can manage roles")

    # 3. Check Target
    target_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()

    if not target_membership:
        raise HTTPException(status_code=404, detail="Member not found")

    # 4. Protect Owner Role (Owner must remain ADMIN)
    # Actually, owner role in TeamMember should stay ADMIN. 
    # If target is owner, prevent demotion to VIEWER/MEMBER?
    if team.owner_id == user_id and role_data.role != UserRole.ADMIN:
         raise HTTPException(status_code=400, detail="Team Owner must be an Admin")

    target_membership.role = role_data.role
    db.commit()
    db.refresh(target_membership)
    return target_membership

@router.put("/{team_id}", response_model=TeamResponse)
def update_team(team_id: str, team_update: TeamUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check permission: Owner or Admin
    member = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id).first()
    
    is_owner = (team.owner_id == current_user.id)
    is_admin = (member and member.role == UserRole.ADMIN)
    
    if not is_owner and not is_admin:
        if not getattr(current_user, 'is_super_admin', False):
            raise HTTPException(status_code=403, detail="Not authorized to update team settings")
    
    team.name = team_update.name
    db.commit()
    db.refresh(team)
    return team

@router.delete("/{team_id}")
def delete_team(team_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check permission: OWNER ONLY (or Super Admin)
    # Note: team.owner_id is the string ID of the owner
    if team.owner_id != current_user.id and not getattr(current_user, 'is_super_admin', False):
         raise HTTPException(status_code=403, detail="Only the Team Owner can delete the team")
    

from schemas import TeamAdAccountsUpdate
import json

@router.put("/{team_id}/ad_accounts", response_model=TeamResponse)
def update_team_ad_accounts(
    team_id: str,
    update_data: TeamAdAccountsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check Permission: Only Owner can manage ad accounts
    if team.owner_id != current_user.id:
         raise HTTPException(status_code=403, detail="Only the Team Owner can manage ad account visibility")

    # Serialize List -> JSON String
    # Start of list e.g. ["act_123", "act_45"]
    team.visible_ad_account_ids = json.dumps(update_data.ad_account_ids)
    
    db.commit()
    db.refresh(team)
    return team

