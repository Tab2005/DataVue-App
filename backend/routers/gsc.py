from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal, User
from dependencies import get_db, get_current_user, require_module
from gsc_service import GSCService
from typing import List, Optional
from pydantic import BaseModel
import traceback

router = APIRouter(prefix="/api/gsc", tags=["gsc"])

# Module access check - all GSC endpoints require 'gsc' module
gsc_module_check = require_module("gsc")

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

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 2. List Sites
@router.get("/sites")
def list_sites(
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
    _: bool = Depends(gsc_module_check)
):
    try:
        sites, error = GSCService.list_sites(user)
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return sites
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 3. Get Analytics
@router.get("/analytics")
def get_gsc_analytics(
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: Optional[str] = "date",
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
    _: bool = Depends(gsc_module_check)
):
    try:
        dim_list = dimensions.split(",")
        data, error = GSCService.get_analytics(user, site_url, start_date, end_date, dim_list)
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 4. Fetch Page Titles
class PageTitlesRequest(BaseModel):
    urls: List[str]

@router.post("/page-titles")
async def get_page_titles(
    request: PageTitlesRequest,
    user: User = Depends(get_current_user)
):
    """
    Fetches page titles by scraping the provided URLs.
    Returns a dictionary mapping URL to title.
    """
    import httpx
    from bs4 import BeautifulSoup
    import asyncio
    
    async def fetch_title(client: httpx.AsyncClient, url: str) -> tuple:
        try:
            response = await client.get(url, timeout=5.0, follow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    return (url, title_tag.get_text().strip())
            return (url, None)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return (url, None)
    
    try:
        # Limit to 50 URLs to balance performance and coverage
        urls_to_fetch = request.urls[:50]
        
        async with httpx.AsyncClient(
            headers={'User-Agent': 'Mozilla/5.0 (compatible; GSCDashboard/1.0)'}
        ) as client:
            tasks = [fetch_title(client, url) for url in urls_to_fetch]
            results = await asyncio.gather(*tasks)
        
        # Convert to dictionary
        titles = {url: title for url, title in results if title}
        return titles
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch titles: {str(e)}")
