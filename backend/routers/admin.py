from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
from database import User, Team, TeamMember
from dependencies import get_super_admin, get_db
from schemas import UserResponse, TeamResponse

router = APIRouter(
    prefix="/api/admin",
    tags=["Super Admin"],
    dependencies=[Depends(get_super_admin)]
)

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    team_count = db.query(Team).count()
    return {
        "user_count": user_count,
        "team_count": team_count
    }

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    # Return all users, newest first
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users

@router.get("/teams", response_model=List[TeamResponse])
def get_all_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).order_by(Team.created_at.desc()).all()
    return teams

@router.delete("/users/{user_id}")
def delete_user_force(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete associated data if needed, or rely on cascade
    db.delete(user)
    db.commit()
    return {"message": f"User {user.email} deleted"}
