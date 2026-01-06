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


# 5. Page Intent Analysis (AI-powered)
class PageIntentRequest(BaseModel):
    site_url: str           # GSC site URL (e.g., "sc-domain:example.com")
    page_url: str           # Page URL to analyze
    start_date: str         # YYYY-MM-DD
    end_date: str           # YYYY-MM-DD
    top_n: Optional[int] = 50  # Number of keywords to analyze (default 50)
    keywords: Optional[List[str]] = None  # Optional: specific keywords to analyze (skip GSC fetch)
    provider: Optional[str] = "zeabur"  # AI provider: "zeabur" or "gemini"
    ai_api_key: Optional[str] = None  # Optional: user-provided API key

@router.post("/page-intents")
async def get_page_intents(
    request: PageIntentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(gsc_module_check)
):
    """
    Analyze search intent for a specific page using AI.
    
    Fetches top keywords for the page from GSC, then uses AI to classify
    each keyword's search intent (informational, commercial, navigational, transactional).
    
    Returns:
        - Primary intent for the page
        - Intent distribution percentages
        - Keywords with individual intent classifications
    """
    import os
    from services.ai import AIIntentClassifier
    
    try:
        # Check if specific keywords were provided (skip GSC fetch if so)
        if request.keywords and len(request.keywords) > 0:
            # Use provided keywords directly - this is for "continue analysis" scenario
            top_queries = [{"query": kw, "clicks": 0, "impressions": 0, "ctr": 0, "position": 0} for kw in request.keywords[:request.top_n]]
            page_queries = top_queries  # For continue analysis, page_queries equals top_queries
        else:
            # Step 1: Fetch keywords for this page from GSC
            query_data, error = GSCService.get_analytics(
                user,
                request.site_url,
                request.start_date,
                request.end_date,
                dimensions=['page', 'query']
            )
            
            if error:
                raise HTTPException(status_code=400, detail=f"GSC Error: {error}")
            
            # Step 2: Filter keywords for the specified page
            page_queries = []
            for row in query_data:
                keys = row.get('keys', [])
                if len(keys) >= 2 and keys[0] == request.page_url:
                    page_queries.append({
                        "query": keys[1],
                        "clicks": row.get('clicks', 0),
                        "impressions": row.get('impressions', 0),
                        "ctr": row.get('ctr', 0),
                        "position": row.get('position', 0)
                    })
            
            if not page_queries:
                return {
                    "page": request.page_url,
                    "primary_intent": "unknown",
                    "intent_distribution": {
                        "informational": 0.25,
                        "commercial": 0.25,
                        "navigational": 0.25,
                        "transactional": 0.25
                    },
                    "keywords": [],
                    "message": "No keywords found for this page",
                    "model": None
                }
            
            # Step 3: Sort by clicks and take top N
            page_queries.sort(key=lambda x: x['clicks'], reverse=True)
            top_queries = page_queries[:request.top_n]
        
        # Step 4: Determine AI provider and API key
        provider = request.provider or "zeabur"
        
        if provider == "gemini":
            # Use Google Gemini direct API
            api_key = request.ai_api_key or os.getenv("GOOGLE_AI_API_KEY")
            if not api_key:
                return {
                    "page": request.page_url,
                    "primary_intent": "unknown",
                    "intent_distribution": {
                        "informational": 0.25,
                        "commercial": 0.25,
                        "navigational": 0.25,
                        "transactional": 0.25
                    },
                    "keywords": [
                        {
                            "query": q["query"],
                            "clicks": q["clicks"],
                            "impressions": q["impressions"],
                            "position": q["position"],
                            "intent": "unknown",
                            "confidence": 0
                        }
                        for q in top_queries
                    ],
                    "message": "Google AI API key not configured",
                    "model": None
                }
        else:
            # Use Zeabur AI Hub (default)
            api_key = request.ai_api_key or os.getenv("ZEABUR_AI_HUB_API_KEY")
            if not api_key:
                return {
                    "page": request.page_url,
                    "primary_intent": "unknown",
                    "intent_distribution": {
                        "informational": 0.25,
                        "commercial": 0.25,
                        "navigational": 0.25,
                        "transactional": 0.25
                    },
                    "keywords": [
                        {
                            "query": q["query"],
                            "clicks": q["clicks"],
                            "impressions": q["impressions"],
                            "position": q["position"],
                            "intent": "unknown",
                            "confidence": 0
                        }
                        for q in top_queries
                    ],
                    "message": "AI API key not configured",
                    "model": None
                }
        
        # Step 5: Use AI to classify intents
        classifier = AIIntentClassifier(api_key=api_key, provider=provider)
        query_texts = [q["query"] for q in top_queries]
        
        result = classifier.classify_queries(query_texts)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"AI Classification failed: {result.get('error')}"
            )
        
        # Step 6: Combine GSC data with AI results
        ai_results = result.get("results", [])
        keywords_with_intent = []
        
        for i, q in enumerate(top_queries):
            ai_item = ai_results[i] if i < len(ai_results) else {}
            keywords_with_intent.append({
                "query": q["query"],
                "clicks": q["clicks"],
                "impressions": q["impressions"],
                "position": round(q["position"], 1),
                "intent": ai_item.get("primary_intent", "unknown"),
                "confidence": ai_item.get("confidence", 0),
                "intent_distribution": ai_item.get("intent_distribution", {})
            })
        
        # Step 7: Calculate page-level intent (weighted by clicks)
        total_clicks = sum(q["clicks"] for q in top_queries) or 1
        page_distribution = {
            "informational": 0.0,
            "commercial": 0.0,
            "navigational": 0.0,
            "transactional": 0.0
        }
        
        for i, kw in enumerate(keywords_with_intent):
            weight = top_queries[i]["clicks"] / total_clicks
            dist = kw.get("intent_distribution", {})
            for intent_type in page_distribution:
                page_distribution[intent_type] += dist.get(intent_type, 0.25) * weight
        
        primary_intent = max(page_distribution, key=page_distribution.get)
        
        return {
            "page": request.page_url,
            "primary_intent": primary_intent,
            "intent_distribution": {
                k: round(v, 3) for k, v in page_distribution.items()
            },
            "keywords": keywords_with_intent,
            "keyword_count": len(keywords_with_intent),
            "total_keywords": len(page_queries),
            "model": classifier.model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Intent analysis failed: {str(e)}")
