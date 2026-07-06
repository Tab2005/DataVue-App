"""
Contribution Module - Router（docs/21 第 3.5 節）

第 1 波任務 1.1：掛載 7 個端點，全部套 require_module("contribution")。
  - GET  /ping               ：最小健康檢查（回 200，證明模組掛載 + 授權通過）
  - 其餘 6 端點               ：本波回 501 Not Implemented，於任務 1.3／1.4 填入

授權邊界：
  - 未授權（無模組存取） → require_module 拋 403（含 'contribution' 字樣）
  - 授權 → /ping 回 200，其餘回 501
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from database import get_db
from .dependencies import (
    get_current_contribution_user,
    require_contribution_module,
    require_contribution_operate,
)
from .schemas import (
    AnalysisCreateRequest,
    AnalysisCreateResponse,
    AnalysisDetailResponse,
    AnalysisListResponse,
    CampaignListResponse,
    DataRefreshResponse,
    GroupsResponse,
    GroupsUpdateRequest,
    GroupsUpdateResponse,
    PingResponse,
)

router = APIRouter()


@router.get("/ping", response_model=PingResponse)
async def ping(
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
):
    """最小健康檢查端點，用於驗證模組已掛載且授權通過（同 Andromeda 首切片）。"""
    return PingResponse(
        status="ok",
        module="contribution",
        message="MMM 廣告活動貢獻衡量模組已掛載（骨架階段）",
    )


@router.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns(
    account_id: str = Query(..., description="廣告帳戶 ID（act_ 格式）"),
    days: int = Query(180, ge=1, le=365, description="回溯天數"),
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
    db=Depends(get_db),
):
    """列出帳戶近 N 天活動（含花費/轉換彙總），供分組 UI。任務 1.3 實作。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="contribution.campaigns 由任務 1.3（資料抓取與快取）實作",
    )


@router.get("/groups", response_model=GroupsResponse)
async def get_groups(
    account_id: str = Query(..., description="廣告帳戶 ID"),
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
    db=Depends(get_db),
):
    """讀取活動分組；無則觸發自動分組並回傳。任務 1.4 實作。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="contribution.groups 由任務 1.4（分組與分析編排）實作",
    )


@router.put("/groups", response_model=GroupsUpdateResponse)
async def update_groups(
    body: GroupsUpdateRequest,
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_operate),
    db=Depends(get_db),
):
    """覆寫分組（前端編輯後整批提交）。任務 1.4 實作。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="contribution.groups (PUT) 由任務 1.4（分組與分析編排）實作",
    )


@router.post(
    "/analyses",
    response_model=AnalysisCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_analysis(
    body: AnalysisCreateRequest,
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_operate),
    db=Depends(get_db),
):
    """發起 MMM 分析（背景任務，回 202 + snapshot_id）。任務 1.4 實作。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="contribution.analyses (POST) 由任務 1.4（分組與分析編排）實作",
    )


@router.get("/analyses", response_model=AnalysisListResponse)
async def list_analyses(
    account_id: str = Query(..., description="廣告帳戶 ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
    db=Depends(get_db),
):
    """分析列表（分頁）。任務 1.4 實作。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="contribution.analyses (GET list) 由任務 1.4（分組與分析編排）實作",
    )


@router.get("/analyses/{snapshot_id}", response_model=AnalysisDetailResponse)
async def get_analysis(
    snapshot_id: str,
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
    db=Depends(get_db),
):
    """單筆分析結果（含 results/diagnostics；processing 時前端輪詢）。任務 1.4 實作。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="contribution.analyses/{id} 由任務 1.4（分組與分析編排）實作",
    )


@router.post("/data/refresh", response_model=DataRefreshResponse)
async def refresh_data(
    account_id: str = Query(..., description="廣告帳戶 ID"),
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_operate),
    db=Depends(get_db),
):
    """手動觸發每日資料補抓（背景執行）。任務 1.3 實作。"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="contribution.data/refresh 由任務 1.3（資料抓取與快取）實作",
    )
