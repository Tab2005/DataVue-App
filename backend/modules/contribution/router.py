"""
Contribution Module - Router（docs/21 第 3.5 節）

第 1 波任務分階段填入：
  - 1.1：7 端點骨架（/ping 200，其餘 501）
  - 1.3：/data/refresh（背景抓取） + /campaigns（快取表彙總）
  - 1.4：分組讀寫 + analyses 編排 + 背景任務調度

授權邊界：
  - 未授權（無模組存取） → require_module 拋 403（含 'contribution' 字樣）
  - 授權 → /ping 回 200；/campaigns 回 200；/data/refresh 回 202 + 背景抓取

端點 async/sync 慣例（2026-07-08 事故第二型態的修法）：
  - 走同步 SQLAlchemy 的端點一律宣告為 `def`（FastAPI 自動丟 threadpool）。
    `async def` + 同步 DB 查詢會直接在 event loop 執行；psycopg2 等待資料庫
    鎖沒有預設 timeout，一次鎖等待就會把整個 backend（含 /health）無限凍結。
  - 只有真正 await 外部 I/O 或需操作 event loop（背景任務 dispatch）的端點
    維持 `async def`，且其中的同步段落必須包 `asyncio.to_thread`。
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from database import get_db
from .data_source import (
    ContributionAPIError,
    ContributionDataSourceError,
    ContributionFetchError,
    ContributionTokenError,
    fetch_account_daily_metrics,
)
from .dependencies import (
    get_current_contribution_user,
    require_contribution_module,
    require_contribution_operate,
)
from .repository import repository as contribution_repository
from .schemas import (
    AnalysisCreateRequest,
    AnalysisCreateResponse,
    AnalysisDetailResponse,
    AnalysisListResponse,
    AnalysisSummary,
    CampaignGroup,
    CampaignListResponse,
    CampaignSummary,
    DataRefreshResponse,
    GroupsResponse,
    GroupsUpdateRequest,
    GroupsUpdateResponse,
    PingResponse,
)
from .service import (
    GroupValidationRejected,
    GuardrailRejected,
    SnapshotNotFound,
    create_analysis,
    get_or_create_groups,
    get_snapshot,
    list_groups,
    list_snapshots,
    update_groups,
)

logger = logging.getLogger(__name__)

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
def list_campaigns(
    account_id: str = Query(..., description="廣告帳戶 ID（act_ 格式）"),
    metric_key: str = Query("omni_purchase", description="轉換指標鍵"),
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
    db=Depends(get_db),
):
    """列出帳戶近 N 天活動（含花費/轉換彙總），供分組 UI。

    讀取 contribution_daily_metrics 快取表並 GROUP BY campaign_id 彙總；
    若快取為空回空 list（前端會引導使用者先按 /data/refresh 抓取）。
    """
    summaries = contribution_repository.list_campaign_summaries(
        db, account_id=account_id, metric_key=metric_key
    )
    return CampaignListResponse(
        account_id=account_id,
        campaigns=[CampaignSummary(**row) for row in summaries],
        total=len(summaries),
    )


@router.get("/groups", response_model=GroupsResponse)
def get_groups(
    account_id: str = Query(..., description="廣告帳戶 ID"),
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
    db=Depends(get_db),
):
    """讀取活動分組；無則觸發自動分組並回傳。

    觸發規則（service.get_or_create_groups）：
      - 有 manual → 回 manual
      - 僅有 auto → 回 auto
      - 完全無 → 跑 grouping.auto_group() 並寫入
    """
    # updated_by 外鍵指向 users.id（內部 ID），不可用 google_id——曾因取值
    # 順序寫反觸發 ForeignKeyViolation（SQLite 測試不驗外鍵故未攔到）
    user_id = getattr(_user, "id", None)
    rows = get_or_create_groups(db, account_id=account_id, updated_by=user_id)
    source = "manual" if any(r.source == "manual" for r in rows) else "auto"
    return GroupsResponse(
        account_id=account_id,
        groups=[
            CampaignGroup(
                group_key=r.group_key,
                group_name=r.group_name,
                campaign_ids=list(r.campaign_ids or []),
                source=r.source,
            )
            for r in rows
        ],
        source=source if rows else "auto",
    )


@router.put("/groups", response_model=GroupsUpdateResponse)
def update_groups_endpoint(
    body: GroupsUpdateRequest,
    user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_operate),
    db=Depends(get_db),
):
    """覆寫分組（前端編輯後整批提交）；寫入後 source='manual'。

    驗證規則（grouping.validate_manual_groups）：
      - group_key 不可重複
      - 全部活動 ID 必須屬於該帳戶、不可丟失
    失敗回 422（語義錯誤）並列出原因。
    """
    # updated_by → users.id（內部 ID），同 get_groups 的取值規則
    user_id = getattr(user, "id", None)
    payload = [g.model_dump() for g in body.groups]
    try:
        rows = update_groups(
            db,
            account_id=body.account_id,
            groups_payload=payload,
            updated_by=user_id,
        )
    except GroupValidationRejected as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": exc.errors, "missing": exc.missing},
        ) from exc
    return GroupsUpdateResponse(
        account_id=body.account_id,
        groups=[
            CampaignGroup(
                group_key=r.group_key,
                group_name=r.group_name,
                campaign_ids=list(r.campaign_ids or []),
                source=r.source,
            )
            for r in rows
        ],
        updated_count=len(rows),
    )


@router.post(
    "/analyses",
    response_model=AnalysisCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_analysis_endpoint(
    body: AnalysisCreateRequest,
    user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_operate),
    db=Depends(get_db),
):
    """發起 MMM 分析（背景任務）。

    流程：guardrail 預檢 → 建 snapshot(status=queued) → 排程
    （apscheduler → local_async fallback）。回 202 + snapshot_id；
    前端以 GET /analyses/{snapshot_id} 輪詢狀態。
    """
    # created_by → users.id（內部 ID），同 get_groups 的取值規則
    user_id = getattr(user, "id", None)
    try:
        snapshot, queue_host, _mode = create_analysis(
            db,
            account_id=body.account_id,
            date_start=body.date_start,
            date_end=body.date_end,
            metric_key=body.metric_key,
            n_restarts=body.n_restarts,
            holdout_days=body.holdout_days,
            marginal_step=body.marginal_step,
            created_by=user_id,
        )
    except GuardrailRejected as exc:
        # 422 語義錯誤（資料量不足等）
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": exc.violations},
        ) from exc

    if queue_host == "unavailable":
        # scheduler 與 local loop 都不可用：仍建了 snapshot，但明示前端需重試
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="排程器與本機 fallback 皆不可用，請稍後重試",
        )

    msg = {
        "apscheduler": f"已加入背景排程（{snapshot.id}）",
        "local_async": f"已於本機事件迴圈啟動背景分析（{snapshot.id}）",
    }.get(queue_host, f"已啟動分析（{snapshot.id}）")

    return AnalysisCreateResponse(
        snapshot_id=snapshot.id,
        status=snapshot.status,
        account_id=snapshot.account_id,
        queue_host=queue_host,
        message=msg,
    )


@router.get("/analyses", response_model=AnalysisListResponse)
def list_analyses(
    account_id: str = Query(..., description="廣告帳戶 ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
    db=Depends(get_db),
):
    """分析列表（分頁）。"""
    items, total = list_snapshots(
        db, account_id=account_id, page=page, page_size=page_size
    )
    return AnalysisListResponse(
        account_id=account_id,
        analyses=[
            AnalysisSummary(
                snapshot_id=s.id,
                account_id=s.account_id,
                status=s.status,
                date_start=s.date_start,
                date_end=s.date_end,
                created_at=s.created_at,
                completed_at=s.completed_at,
                error_message=s.error_message,
            )
            for s in items
        ],
        total=total,
    )


@router.get("/analyses/{snapshot_id}", response_model=AnalysisDetailResponse)
def get_analysis(
    snapshot_id: str,
    _user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_module),
    db=Depends(get_db),
):
    """單筆分析結果（含 results/diagnostics；processing 時前端輪詢）。"""
    try:
        s = get_snapshot(db, snapshot_id)
    except SnapshotNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"snapshot {snapshot_id} 不存在",
        )
    return AnalysisDetailResponse(
        snapshot_id=s.id,
        account_id=s.account_id,
        status=s.status,
        date_start=s.date_start,
        date_end=s.date_end,
        config=s.config or {},
        results=s.results,
        diagnostics=s.diagnostics,
        error_message=s.error_message,
        runtime_job_id=s.runtime_job_id,
        created_at=s.created_at,
        completed_at=s.completed_at,
    )


@router.post(
    "/data/refresh",
    response_model=DataRefreshResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def refresh_data(
    background_tasks: BackgroundTasks,
    account_id: str = Query(..., description="廣告帳戶 ID"),
    metric_key: str = Query("omni_purchase", description="轉換指標鍵"),
    user=Depends(get_current_contribution_user),
    _access: bool = Depends(require_contribution_operate),
):
    """手動觸發每日資料補抓（背景執行）。

    同步階段：呼叫 `data_source.fetch_account_daily_metrics()` 一次以驗證
    token 與 API 連線（4xx 立即回應，避免背景任務靜默失敗）；若 token 缺失
    / API 拋錯則回 4xx 並附明確錯誤訊息（沿用 fb_ads 慣例，不落明文 token）。
    probe 固定只抓「昨天」單日（`since_until`），與實際全量/增量視窗無關，
    避免同步階段被迫等待 180 天全量抓取而觸發前端逾時（曾實測 >30000ms）。

    注意：刻意不用 `Depends(get_db)` ——若持有一個請求範圍的 DB session
    横跨這段「同步等待 Meta API」的期間，連線會在整趟等待中被佔用；DB
    連線池很小（預設 pool_size=3 + max_overflow=5 = 8），幾次併發的
    「抓取資料」點擊就會把連線池耗盡，導致其他端點（甚至 /health）也一併
    卡住排隊等待連線，讓整個服務看起來完全無回應。改為用短生命週期 session
    只在查詢 db_window 時取用、立刻歸還，Meta API 等待期間不佔用任何連線
    （實測：曾造成整個 backend event loop 卡死逾時，見 docs/21 任務 2.1
    追蹤問題）。

    成功 → 背景任務實際執行抓取 + upsert，前端用 202 + status='accepted'
    表示已進入排程；本端點不阻塞前端等待全量抓取。
    """
    user_id = getattr(user, "google_id", None) or getattr(user, "id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無法識別使用者身分，請重新登入",
        )

    # 增量視窗：若快取已有資料，只補最近 3 天（歸因回補）；首次全量抓 180 天。
    # 短生命週期 session：查完立刻歸還連線，不橫跨後面的 Meta API 等待。
    # to_thread：本端點是 async def，同步 DB 查詢不可直接在 event loop 執行
    # （鎖等待會凍結整個 backend，見檔頭慣例說明）。
    from database import SessionLocal as _SessionLocal

    def _query_window() -> tuple[str, str] | None:
        _db = _SessionLocal()
        try:
            return _get_existing_date_window(_db, account_id, metric_key)
        finally:
            _db.close()

    db_window = await asyncio.to_thread(_query_window)

    yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    try:
        # 同步觸發一次最小抓取驗證 token（僅昨天 1 天），成功即排程全量/增量抓取
        probe = await fetch_account_daily_metrics(
            account_id,
            user_id=user_id,
            metric_key=metric_key,
            since_until=(yesterday, yesterday),
        )
    except ContributionTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except ContributionAPIError as exc:
        # FB API 4xx（權限不足、查詢無效等）→ 回 4xx 給前端
        if exc.code and 400 <= exc.code < 500:
            raise HTTPException(
                status_code=exc.code,
                detail=f"FB API 拒絕請求：{exc}",
            ) from exc
        # 5xx → 包成 502（上游錯誤）
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FB API 5xx 錯誤：{exc}",
        ) from exc
    except ContributionFetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FB API 連線失敗：{exc}",
        ) from exc

    # 背景任務：實際執行全量/增量抓取 + upsert
    background_tasks.add_task(
        _run_refresh_background,
        account_id=account_id,
        user_id=user_id,
        metric_key=metric_key,
        db_window=db_window,
        probe_count=len(probe),
    )

    return DataRefreshResponse(
        account_id=account_id,
        status="accepted",
        message=(
            f"已排程補抓 {account_id} 的 {metric_key} 資料"
            f"（{'增量最近 3 天' if db_window else '全量 180 天'}，"
            f"probe 收到 {len(probe)} 列）"
        ),
    )


def _get_existing_date_window(
    db,
    account_id: str,
    metric_key: str,
) -> tuple[str, str] | None:
    """查詢快取表目前該帳戶該指標的 (min_date, max_date)；無資料回 None。"""
    from sqlalchemy import func, select
    from database.models.contribution import ContributionDailyMetric

    stmt = (
        select(
            func.min(ContributionDailyMetric.date),
            func.max(ContributionDailyMetric.date),
        )
        .where(
            ContributionDailyMetric.account_id == account_id,
            ContributionDailyMetric.metric_key == metric_key,
        )
    )
    row = db.execute(stmt).first()
    if row is None or row[0] is None or row[1] is None:
        return None
    return (row[0], row[1])


async def _run_refresh_background(
    *,
    account_id: str,
    user_id: str,
    metric_key: str,
    db_window: tuple[str, str] | None,
    probe_count: int,
) -> None:
    """背景任務：實際執行抓取 + upsert；錯誤以 log 記錄（不中斷任務）。

    邊抓邊寫：透過 `fetch_account_daily_metrics(on_rows=...)` 每收到一頁
    （≤500 列）即刻寫入並釋放，全程不把整段視窗的列堆在記憶體——全量
    180 天一次累積（每列含完整 actions_payload）曾把 backend 推到 2GB、
    連帶耗盡整台機器資源使所有請求逾時（2026-07-08 事故）。
    """
    from database import SessionLocal

    def _write(rows_dicts: list[dict]) -> int:
        # 同步 DB 段（session 開/寫/commit/close 全部在 thread 內完成，
        # 不佔用事件迴圈執行緒；同一類修法見 refresh_data / get_headers）
        db = SessionLocal()
        try:
            n = contribution_repository.upsert_daily_metrics(db, rows_dicts)
            db.commit()
            return n
        finally:
            db.close()

    fetched = 0
    written = 0

    async def _flush_page(page_rows) -> None:
        nonlocal fetched, written
        if not page_rows:
            return
        fetched += len(page_rows)
        written += await asyncio.to_thread(
            _write, [r.to_dict() for r in page_rows]
        )

    try:
        await fetch_account_daily_metrics(
            account_id,
            user_id=user_id,
            db_window=db_window,
            metric_key=metric_key,
            on_rows=_flush_page,
        )
        logger.info(
            "[Contribution] refresh %s metric=%s window=%s: probe=%d fetched=%d upsert=%d",
            account_id,
            metric_key,
            db_window or "FULL",
            probe_count,
            fetched,
            written,
        )
    except ContributionDataSourceError as exc:
        logger.error(
            "[Contribution] refresh %s failed: %s", account_id, exc
        )
    except Exception as exc:  # 防背景任務將錯誤吞掉
        logger.error(
            "[Contribution] refresh %s unexpected error: %s",
            account_id,
            exc,
            exc_info=True,
        )
