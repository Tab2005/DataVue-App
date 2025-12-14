from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from database import UserRole, UserStatus
import uuid

# Base Schema (Shared properties)
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.ACTIVE

# Schema for Reading (Return to client)
class UserResponse(UserBase):
    id: str
    google_id: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_super_admin: bool = False

    class Config:
        from_attributes = True

# Schema for Creating (Internal/Admin)
class UserCreate(UserBase):
    google_id: str

# Schema for Updating (Admin)
class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

# --- Team Schemas ---

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: str

class TeamResponse(TeamBase):
    id: str
    owner_id: Optional[str] = None
    created_at: Optional[datetime] = None
    visible_ad_account_ids: Optional[str] = None # JSON string
    # Don't return fb_access_token to frontend by default for security

    class Config:
        from_attributes = True

class TeamAdAccountsUpdate(BaseModel):
    ad_account_ids: List[str]

class TeamMemberResponse(BaseModel):
    team_id: str
    user_id: str
    role: UserRole
    joined_at: Optional[datetime] = None
    
    # Optional: Include User details if performing a join
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True

class TeamMemberUpdate(BaseModel):
    role: UserRole

# --- Invite Schemas ---

class InviteCreateResponse(BaseModel):
    code: str
    invite_url: str
    expires_at: datetime

class InviteInfoResponse(BaseModel):
    team_id: str
    team_name: str
    inviter_name: Optional[str] = None
    expires_at: datetime
    is_valid: bool
