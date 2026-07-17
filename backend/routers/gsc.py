from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal, User
from dependencies import get_db, get_current_user, require_module
from gsc_service import GSCService
from typing import List, Optional
from pydantic import BaseModel
import logging
import traceback

logger = logging.getLogger(__name__)

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
        sites, error = GSCService.list_sites(user, db)
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
    limit: Optional[int] = Query(None, ge=1, le=25000),
    offset: Optional[int] = Query(0, ge=0),
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
    _: bool = Depends(gsc_module_check)
):
    try:
        dim_list = dimensions.split(",")
        data, error = GSCService.get_analytics(user, site_url, start_date, end_date, dim_list, limit, offset, db)
        if error:
            raise HTTPException(status_code=400, detail=error)
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 3b. Search Appearance Summary (docs/35_GSC_AI_Overview_生成式AI搜尋數據擴充實作規劃.md Phase 1)
# 已知的 AI 相關提示關鍵字，僅用於前端標示疑似項目，不作為硬編碼的判斷依據。
#
# 重要澄清（2026-07-17 查證 Google 官方文件與公告後確認）：Google 於 2026-06-03 推出的
# 「Generative AI performance report」（AI Overview / AI Mode 曝光數據）目前只能在 GSC 後台
# UI 查看（成效 > 搜尋結果 > 生成式 AI），並「未」透過 Search Analytics API 開放——
# searchAppearance 維度與 type 參數都沒有對應的值。也就是說，這個關鍵字比對機制目前
# 保證不會匹配到任何真正的 AI Overview 資料，只是預留給 Google 未來若把它併入
# searchAppearance 維度時的相容處理，前端呈現時必須明確告知使用者這個限制，不能讓
# 「沒有比對到」被誤解為「這個網站沒有 AI Overview 曝光」。
AI_APPEARANCE_HINT_KEYWORDS = ["AI", "OVERVIEW", "GENERATIVE", "SGE"]


@router.get("/search-appearance-summary")
def get_search_appearance_summary(
    site_url: str,
    start_date: str,
    end_date: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(gsc_module_check)
):
    """
    彙總 searchAppearance 維度成效（AMP、Rich Result、Merchant Listing 等既有搜尋外觀類型）。

    不含 AI Overview / AI Mode 數據：Google 尚未透過 API 開放該報表，詳見上方
    AI_APPEARANCE_HINT_KEYWORDS 註解。

    注意：同一次搜尋結果可能同時符合多種 searchAppearance 類型（例如同時是 AMP 又是
    Rich Result），各列的 clicks/impressions 直接加總會重複計算。因此占比分母改用
    dimensions=["date"] 的加總作為全站總量，而非加總 searchAppearance 各列。
    """
    try:
        appearance_rows, error = GSCService.get_analytics(
            user, site_url, start_date, end_date,
            dimensions=["searchAppearance"], db=db
        )
        if error:
            raise HTTPException(status_code=400, detail=error)

        if not appearance_rows:
            return {
                "has_data": False,
                "total_clicks": 0,
                "total_impressions": 0,
                "types": [],
            }

        total_rows, total_error = GSCService.get_analytics(
            user, site_url, start_date, end_date,
            dimensions=["date"], db=db
        )
        if total_error:
            raise HTTPException(status_code=400, detail=total_error)

        total_clicks = sum(r.get("clicks", 0) for r in (total_rows or []))
        total_impressions = sum(r.get("impressions", 0) for r in (total_rows or []))

        types = []
        for row in appearance_rows:
            keys = row.get("keys") or []
            key = keys[0] if keys else "(unknown)"
            clicks = row.get("clicks", 0)
            impressions = row.get("impressions", 0)
            types.append({
                "search_appearance": key,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": row.get("ctr", 0),
                "position": row.get("position", 0),
                "click_share": (clicks / total_clicks) if total_clicks else 0,
                "impression_share": (impressions / total_impressions) if total_impressions else 0,
                "is_ai_related_hint": any(kw in key.upper() for kw in AI_APPEARANCE_HINT_KEYWORDS),
            })

        types.sort(key=lambda t: t["clicks"], reverse=True)

        return {
            "has_data": True,
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "types": types,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 4. Fetch Page Titles (with Database Caching)
class PageTitlesRequest(BaseModel):
    urls: List[str]
    force_refresh: Optional[bool] = False

@router.post("/page-titles")
async def get_page_titles(
    request: PageTitlesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches page titles with database caching.
    - First checks database for cached titles
    - Only fetches uncached URLs via HTTP
    - Stores newly fetched titles in database
    - force_refresh=True ignores cache and re-fetches all
    
    Returns a dictionary mapping URL to title.
    """
    import httpx
    from bs4 import BeautifulSoup
    import asyncio
    from datetime import datetime
    from database import PageTitle
    import uuid
    
    async def fetch_title(client: httpx.AsyncClient, url: str) -> tuple:
        """Fetch a single page title via HTTP."""
        # Skip invalid URLs
        if not url.startswith(('http://', 'https://')):
            logger.warning(f"Skipping invalid URL (no protocol): {url}")
            return (url, None)
        
        try:
            response = await client.get(url, timeout=3.0, follow_redirects=True)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    return (url, title_tag.get_text().strip())
            return (url, None)
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return (url, None)
    
    try:
        # Limit to 50 URLs
        urls_to_process = request.urls[:50]
        
        # Filter out invalid URLs early
        valid_urls = [u for u in urls_to_process if u.startswith(('http://', 'https://'))]
        
        result_titles = {}
        urls_to_fetch = []
        
        if not request.force_refresh:
            # Check database cache first
            cached_titles = db.query(PageTitle).filter(PageTitle.url.in_(valid_urls)).all()
            cached_map = {pt.url: pt.title for pt in cached_titles}
            
            # Separate cached from uncached
            for url in valid_urls:
                if url in cached_map and cached_map[url]:
                    result_titles[url] = cached_map[url]
                else:
                    urls_to_fetch.append(url)
            
            logger.debug(f"[PageTitles] Cache hit: {len(result_titles)}, Need fetch: {len(urls_to_fetch)}")
        else:
            # Force refresh - fetch all
            urls_to_fetch = valid_urls
            logger.debug(f"[PageTitles] Force refresh: fetching {len(urls_to_fetch)} URLs")
        
        # Fetch uncached URLs
        if urls_to_fetch:
            async with httpx.AsyncClient(
                headers={'User-Agent': 'Mozilla/5.0 (compatible; DataVue/1.0)'},
                timeout=httpx.Timeout(3.0, connect=2.0)
            ) as client:
                tasks = [fetch_title(client, url) for url in urls_to_fetch]
                fetched_results = await asyncio.gather(*tasks)
            
            # Store new titles in database
            for url, title in fetched_results:
                if title:
                    result_titles[url] = title
                    
                    # Upsert to database
                    existing = db.query(PageTitle).filter(PageTitle.url == url).first()
                    if existing:
                        existing.title = title
                        existing.fetched_at = datetime.utcnow()
                    else:
                        new_entry = PageTitle(
                            id=str(uuid.uuid4()),
                            url=url,
                            title=title,
                            fetched_at=datetime.utcnow()
                        )
                        db.add(new_entry)
            
            db.commit()
            logger.debug(f"[PageTitles] Stored {len([t for _, t in fetched_results if t])} new titles")
        
        return result_titles
        
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
                dimensions=['page', 'query'],
                limit=None,
                offset=0,
                db=db
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
        
        # Step 4: Determine AI provider and get API key from encrypted storage
        provider = request.provider or "zeabur"
        
        # Try to get API key from user's encrypted settings in database first
        from modules.auth.service import TokenManager
        api_key = TokenManager.get_ai_api_key(user.google_id, provider=provider)
        
        # Fallback to request parameter or environment variable
        if not api_key:
            if provider == "gemini":
                api_key = request.ai_api_key or os.getenv("GOOGLE_AI_API_KEY")
            else:
                api_key = request.ai_api_key or os.getenv("ZEABUR_AI_HUB_API_KEY")
        
        if not api_key:
            provider_name = "Google Gemini" if provider == "gemini" else "Zeabur AI Hub"
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
                "message": f"{provider_name} API key not configured",
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
# 6. Keyword Gap Analysis
class KeywordGapRequest(BaseModel):
    site_url: str           # GSC site URL
    page_url: str           # Specific page URL to analyze
    start_date: str         # YYYY-MM-DD
    end_date: str           # YYYY-MM-DD
    top_n: Optional[int] = 100

@router.post("/keyword-gap")
async def analyze_keyword_gap(
    request: KeywordGapRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(gsc_module_check)
):
    """
    Analyzes the "gap" between keywords the page ranks for vs. keywords present in the content.
    1. Fetches top keywords for the page from GSC.
    2. Scrapes the actual content of the page.
    3. Checks if each keyword exists in the content.
    """
    import httpx
    from bs4 import BeautifulSoup
    import re
    
    try:
        # Step 1: Fetch GSC Keywords for this specific page using server-side filtering
        # Prepare dimension filters
        # Use 'contains' instead of 'equals' for more robustness with trailing slashes/protocols
        dimension_filters = [
            {
                "dimension": "page",
                "operator": "contains",
                "expression": request.page_url.rstrip('/')
            }
        ]
        
        logger.info(f"[Gap Analysis] Fetching GSC data for {request.page_url} ({request.start_date} to {request.end_date})")
        query_data, error = GSCService.get_analytics(
            user,
            request.site_url,
            request.start_date,
            request.end_date,
            dimensions=['page', 'query'],
            limit=None,
            offset=0,
            db=db,
            dimension_filters=dimension_filters
        )
        
        if error:
            logger.warning(f"[Gap Analysis] GSC Error: {error}")
            raise HTTPException(status_code=400, detail=f"GSC Error: {error}")
            
        # Structure the keywords results
        page_keywords = []
        target_url_clean = request.page_url.rstrip('/')
        
        for row in query_data:
            keys = row.get('keys', [])
            if len(keys) >= 2:
                row_url_clean = keys[0].rstrip('/')
                if row_url_clean == target_url_clean:
                    page_keywords.append({
                        "query": keys[1],
                        "clicks": row.get('clicks', 0),
                        "impressions": row.get('impressions', 0),
                        "ctr": row.get('ctr', 0),
                        "position": row.get('position', 0)
                    })
        
        logger.debug(f"[Gap Analysis] Found {len(page_keywords)} total keywords for page.")
        
        # Sort and limit
        page_keywords.sort(key=lambda x: x['clicks'], reverse=True)
        
        # Support "All" keywords if top_n is 0 or negative
        if request.top_n and request.top_n > 0:
            top_page_keywords = page_keywords[:request.top_n]
        else:
            top_page_keywords = page_keywords
            
        if not top_page_keywords:
            return {
                "page": request.page_url,
                "status": "no_data",
                "message": "No GSC data found for this URL in the given period.",
                "results": [],
                "total_analyzed": 0,
                "missing_count": 0,
                "total_found_in_gsc": len(page_keywords)
            }
            
        # Step 2: Scrape Page Content
        content_text = ""
        page_title = ""
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
                resp = await client.get(request.page_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Get title
                    title_tag = soup.find('title')
                    page_title = title_tag.get_text().strip() if title_tag else ""
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.extract()
                        
                    # Get text and clean up whitespace
                    content_text = soup.get_text(separator=' ', strip=True).lower()
                else:
                    raise Exception(f"Failed to fetch page: HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"Scraping error for {request.page_url}: {e}")
            # We continue even if scraping fails, marking all as "unknown" content status
            return {
                "page": request.page_url,
                "status": "scrape_failed",
                "message": f"Could not fetch page content: {str(e)}",
                "results": top_page_keywords,
                "total_analyzed": len(top_page_keywords),
                "missing_count": len(top_page_keywords), # Default to all missing if we can't scrape
                "total_found_in_gsc": len(page_keywords)
            }

        # Step 3: Match Keywords in Content
        results = []
        for kw in top_page_keywords:
            query = kw['query'].lower()
            # Basic matching: check if query exists as a string
            # Better matching: use regex for word boundaries if it's alphanumeric
            is_present = False
            if query in content_text:
                is_present = True
            
            results.append({
                **kw,
                "in_content": is_present
            })
            
        return {
            "page": request.page_url,
            "page_title": page_title,
            "status": "success",
            "results": results,
            "total_analyzed": len(results),
            "missing_count": len([r for r in results if not r['in_content']]),
            "total_found_in_gsc": len(page_keywords)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")
