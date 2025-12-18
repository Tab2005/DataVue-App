"""
Saved Views API - CRUD operations for metric view configurations.
Supports both personal views (user_id) and team views (team_id).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from database import SessionLocal, SavedView, User
import json
import uuid
from datetime import datetime
from dependencies import get_current_user

router = APIRouter(prefix="/api/saved-views", tags=["saved_views"])

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Models
class SavedViewCreate(BaseModel):
    name: str
    metrics: List[str]
    team_id: Optional[str] = None  # If None, it's a personal view


class SavedViewResponse(BaseModel):
    id: str
    name: str
    metrics: List[str]
    user_id: Optional[str]
    team_id: Optional[str]
    created_at: str
    is_personal: bool


class MigrateRequest(BaseModel):
    views: List[dict]  # Views from localStorage


# --- ENDPOINTS ---

@router.get("", response_model=List[SavedViewResponse])
async def get_saved_views(
    team_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all saved views for a user.
    Returns personal views + team views (if team_id is provided).
    """
    user_id = current_user.id
    views = []
    
    # Get personal views
    personal_views = db.query(SavedView).filter(SavedView.user_id == user_id).all()
    for v in personal_views:
        views.append({
            "id": v.id,
            "name": v.name,
            "metrics": json.loads(v.metrics),
            "user_id": v.user_id,
            "team_id": v.team_id,
            "created_at": v.created_at.isoformat() if v.created_at else "",
            "is_personal": True
        })
    
    # Get team views (if team_id provided)
    if team_id:
        team_views = db.query(SavedView).filter(SavedView.team_id == team_id).all()
        for v in team_views:
            views.append({
                "id": v.id,
                "name": v.name,
                "metrics": json.loads(v.metrics),
                "user_id": v.user_id,
                "team_id": v.team_id,
                "created_at": v.created_at.isoformat() if v.created_at else "",
                "is_personal": False
            })
    
    return views


@router.post("", response_model=SavedViewResponse)
async def create_saved_view(
    data: SavedViewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new saved view."""
    import sys
    print(f"DEBUG: create_saved_view called with data: {data}", file=sys.stderr)
    user_id = current_user.id
    new_view = SavedView(
        id=str(uuid.uuid4()),
        name=data.name,
        metrics=json.dumps(data.metrics),
        user_id=user_id if not data.team_id else None,
        team_id=data.team_id,
        created_by=user_id,
        created_at=datetime.utcnow()
    )
    
    db.add(new_view)
    db.commit()
    db.refresh(new_view)
    
    return {
        "id": new_view.id,
        "name": new_view.name,
        "metrics": json.loads(new_view.metrics),
        "user_id": new_view.user_id,
        "team_id": new_view.team_id,
        "created_at": new_view.created_at.isoformat() if new_view.created_at else "",
        "is_personal": new_view.team_id is None
    }


@router.delete("/{view_id}")
async def delete_saved_view(
    view_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a saved view.
    User can only delete their own personal views or views they created.
    """
    user_id = current_user.id
    view = db.query(SavedView).filter(SavedView.id == view_id).first()
    
    if not view:
        raise HTTPException(status_code=404, detail="View not found")
    
    # Authorization check
    can_delete = (view.user_id == user_id) or (view.created_by == user_id)
    if not can_delete:
        raise HTTPException(status_code=403, detail="Not authorized to delete this view")
    
    db.delete(view)
    db.commit()
    
    return {"message": "View deleted successfully"}


@router.post("/migrate")
async def migrate_from_localStorage(
    data: MigrateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Migrate views from localStorage to database.
    This is called once when user first loads the app after the upgrade.
    """
    user_id = current_user.id
    migrated_count = 0
    
    for view_data in data.views:
        # Check if view with same name already exists
        existing = db.query(SavedView).filter(
            SavedView.user_id == user_id,
            SavedView.name == view_data.get("name", "")
        ).first()
        
        if existing:
            continue  # Skip duplicate
        
        new_view = SavedView(
            id=str(uuid.uuid4()),
            name=view_data.get("name", "Untitled"),
            metrics=json.dumps(view_data.get("metrics", [])),
            user_id=user_id,
            team_id=None,  # All migrated views are personal
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        
        db.add(new_view)
        migrated_count += 1
    
    db.commit()
    
    return {
        "message": f"Migration complete. {migrated_count} views migrated.",
        "migrated_count": migrated_count
    }
