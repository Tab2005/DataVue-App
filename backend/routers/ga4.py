"""
GA4 Router
Google Analytics 4 API 端點

實作 GA4 相關的 API 端點：
- POST /api/ga4/authorize - 授權連接
- GET /api/ga4/properties - 取得屬性列表
- GET /api/ga4/report - 取得分析報表
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal, User
from dependencies import get_db, get_current_user, require_module
from ga4_service import GA4Service
from typing import List, Optional
from pydantic import BaseModel
import traceback

router = APIRouter(prefix="/api/ga4", tags=["ga4"])

# Module access check - all GA4 endpoints require 'ga4' module
ga4_module_check = require_module("ga4")

# Pydantic Models
class GA4AuthCode(BaseModel):
    code: str

class GA4Property(BaseModel):
    property_id: str
    display_name: str
    property_name: str
    create_time: Optional[str]
    update_time: Optional[str]
    currency_code: Optional[str]
    time_zone: Optional[str]
    parent: Optional[str]

# 1. Authorize (Exchange Code for Token)
@router.post("/authorize")
def authorize_ga4(auth_data: GA4AuthCode, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    交換前端的授權碼為 access/refresh tokens
    將 tokens 儲存在 User model 中
    """
    try:
        # User 已經由 get_current_user dependency 驗證並取得

        success, message = GA4Service.exchange_code(user, auth_data.code, db)
        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {"status": "success", "message": message}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 2. List Properties
@router.get("/properties")
def list_ga4_properties(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(ga4_module_check)
):
    """
    取得用戶可存取的 GA4 屬性列表
    """
    try:
        properties, error = GA4Service.list_properties(user, db)
        if error:
            raise HTTPException(status_code=400, detail=error)

        return {"properties": properties}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 3. Get Analytics Report
@router.get("/report")
def get_ga4_analytics(
    property_id: str = Query(..., description="GA4 屬性 ID"),
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    metrics: Optional[str] = Query("activeUsers,totalUsers,newUsers,sessions,screenPageViews", description="指標列表，用逗號分隔"),
    dimensions: Optional[str] = Query("date", description="維度列表，用逗號分隔"),
    limit: Optional[int] = Query(None, ge=1, le=100000, description="每頁筆數"),
    offset: Optional[int] = Query(0, ge=0, description="位移"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: bool = Depends(ga4_module_check)
):
    """
    取得 GA4 分析報表資料
    """
    try:
        # 將字串參數轉換為列表
        metrics_list = metrics.split(",") if metrics else None
        
        # 特別處理 dimensions：空字串表示不要任何 dimension（用於獲取去重總數）
        if dimensions == '':
            dimensions_list = []  # 明確傳遞空列表
        elif dimensions:
            dimensions_list = dimensions.split(",")
        else:
            dimensions_list = None  # None 會使用預設值

        data, error = GA4Service.get_analytics(
            user=user,
            property_id=property_id,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics_list,
            dimensions=dimensions_list,
            limit=limit,
            offset=offset,
            db=db
        )

        if error:
            raise HTTPException(status_code=400, detail=error)

        return data

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")