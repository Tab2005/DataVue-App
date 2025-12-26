from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal, User
from dependencies import get_db, get_current_user
from gsc_service import GSCService
from typing import List, Optional
from pydantic import BaseModel
import traceback

router = APIRouter(prefix="/api/gsc", tags=["gsc"])

# Pydantic Models
class GSCAuthCode(BaseModel):
    code: str

class SiteListResponse(BaseModel):
    siteUrl: str
    permissionLevel: str

# 1. Authorize (Exchange Code for Token)
@router.post("/authorize")
def authorize_gsc(auth_data: GSCAuthCode, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Exchanges the authorization code from frontend for access/refresh tokens.
    Stores them in the User model.
    """
    try:
        # User is already verified and fetched by get_current_user dependency
        
        success, message = GSCService.exchange_code(user, auth_data.code, db)
        if not success:
            raise HTTPException(status_code=400, detail=message)
            
        return {"status": "success", "message": message}

    except Exception as e:
        traceback.print_exc()
        # Removed file logging to avoid PermissionError on Windows
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 2. List Sites
@router.get("/sites")
def list_sites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        sites, error = GSCService.list_sites(user)
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return sites
    except Exception as e:
        traceback.print_exc()
        # Removed file logging to avoid PermissionError on Windows
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 3. Get Analytics
@router.get("/analytics")
def get_gsc_analytics(
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: Optional[str] = "date",
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        dim_list = dimensions.split(",")
        data, error = GSCService.get_analytics(user, site_url, start_date, end_date, dim_list)
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return data
    except Exception as e:
        traceback.print_exc()
        # Removed file logging to avoid PermissionError on Windows
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
