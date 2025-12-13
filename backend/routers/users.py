from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import User, UserRole
from schemas import UserResponse, UserCreate, UserUpdate
from dependencies import get_db, get_admin_user, get_current_user

router = APIRouter(
    tags=["users"]
)

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db), 
    admin: User = Depends(get_admin_user)
):
    """
    List all users. Only accessible by Admins.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db), 
    admin: User = Depends(get_admin_user)
):
    """
    Create/Invite a new user. Only accessible by Admins.
    """
    db_user = db.query(User).filter(User.google_id == user.google_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    # We can also check email uniqueness if provided
    if user.email:
        db_email = db.query(User).filter(User.email == user.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        google_id=user.google_id,
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile. Accessible by any authenticated user.
    """
    return current_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db), 
    admin: User = Depends(get_admin_user)
):
    """
    Update user role or status. Only accessible by Admins.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent Admin from demoting themselves if they are the last admin?
    # (Simplified for now: just update)
    
    if user_update.role:
        db_user.role = user_update.role
    if user_update.status:
        db_user.status = user_update.status
        
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(
    user_id: str, 
    db: Session = Depends(get_db), 
    admin: User = Depends(get_admin_user)
):
    """
    Delete a user. Only accessible by Admins.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}
