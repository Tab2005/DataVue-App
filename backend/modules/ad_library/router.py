"""
Ad Library Module - Router（docs/73、docs/74）

端點 async/sync 慣例（同 contribution，2026-07-08 事故修法）：
  - 走同步 SQLAlchemy 的端點一律宣告為 `def`（FastAPI 丟 threadpool）
  - 只有需要 await 外部 I/O 的端點（/accounts、/media）維持 `async def`，
    且在等待外部 I/O 前先釋放 DB session
"""

from __future__ import annotations

import asyncio
import csv
import io
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from database import get_db
from database.models.team import Team
from modules.ai_hub.service import AIService
from modules.auth.dependencies import get_current_team, get_current_user
from modules.auth.service import TokenManager
from modules.fb_ads import accounts_service

from . import ai_analysis, ai_context, comparisons, hierarchy, repository
from .dependencies import (
    accessible_account_ids,
    require_ad_library_module,
    resolve_token_scope,
    verify_account_access_or_403,
    verify_resource_access_or_404,
)
from .media import build_media_response
from .schemas import (
    AdAssetInsightsResponse,
    AdLibraryItemResponse,
    AdLibraryListResponse,
    AssetInsightEntry,
    AdLibraryTreeResponse,
    AiAnalysisRequest,
    AdsetDetailResponse,
    CampaignDetailResponse,
    ComparisonsResponse,
    ContentDetailResponse,
    ContentListResponse,
    ContentResponse,
    RefreshJobResponse,
    RefreshRequest,
)
from .service import run_refresh

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/ad-library",
    tags=["ad_library"],
    dependencies=[Depends(require_ad_library_module)],
)

MAX_PAGE_SIZE = 100
EXPORT_LIMIT = 5000
KEY_PATTERN = "^[0-9a-f]{64}$"
CONTENT_NOTE = (
    "ad_count／impressions／clicks／spend 為使用此元件的廣告整體成效：一則廣告包含多個元件時，"
    "成效會分別計入每個元件，僅供參考。asset_metrics 為動態素材廣告依元件拆分的實際成效。"
)
ASSET_INSIGHTS_NOTE = (
    "動態素材廣告的元件成效由 Meta 依元件拆分，可直接比較同一則廣告內各段文案、各張素材的表現。"
    "Meta 僅提供曝光、點擊、花費、觸及，CTR 為點擊 ÷ 曝光。"
)
ASSET_KIND_ORDER = ("primary_text", "headline", "description", "image", "video")


def _job_to_response(job) -> RefreshJobResponse:
    return RefreshJobResponse(
        job_id=job.id,
        account_id=job.account_id,
        status=job.status,
        ads_fetched=job.ads_fetched or 0,
        campaigns_fetched=job.campaigns_fetched or 0,
        adsets_fetched=job.adsets_fetched or 0,
        asset_insights_ads=job.asset_insights_ads or 0,
        media_stored=job.media_stored or 0,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


def _item_to_response(item, counts: dict | None = None) -> AdLibraryItemResponse:
    counts = counts or {"copy": {}, "media": {}}
    return AdLibraryItemResponse(
        id=item.id,
        account_id=item.account_id,
        ad_id=item.ad_id,
        ad_name=item.ad_name,
        campaign_id=item.campaign_id,
        campaign_name=item.campaign_name,
        adset_id=item.adset_id,
        adset_name=item.adset_name,
        objective=item.objective,
        effective_status=item.effective_status,
        media_type=item.media_type,
        primary_texts=item.primary_texts or [],
        headlines=item.headlines or [],
        descriptions=item.descriptions or [],
        cta_types=item.cta_types or [],
        link_url=item.link_url,
        media=[
            {"kind": m.get("kind") or "image", "asset_id": m.get("asset_id"), "fb_url": m.get("fb_url")}
            for m in item.media or []
        ],
        preview_link=item.preview_link,
        copy_key=item.copy_key,
        media_key=item.media_key,
        same_copy_count=max(counts["copy"].get(item.copy_key, 1) - 1, 0) if item.copy_key else 0,
        same_media_count=max(counts["media"].get(item.media_key, 1) - 1, 0) if item.media_key else 0,
        impressions=item.impressions or 0,
        reach=item.reach or 0,
        clicks=item.clicks or 0,
        spend=item.spend or 0.0,
        ctr=item.ctr or 0.0,
        ad_created_at=item.ad_created_at,
        ad_updated_at=item.ad_updated_at,
        fetched_at=item.fetched_at,
    )


@router.get("/ping")
def ping():
    return {"module": "ad_library", "status": "ok"}


@router.get("/accounts")
async def list_accounts(
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
):
    """本模組可用的廣告帳號（已套用團隊白名單）。

    不直接依賴 fb_ads 的 /api/ad-accounts：只有 ad_library 權限、沒有 fb_ads
    權限的使用者也要能選帳號。
    """
    scope = resolve_token_scope(user, team)
    accounts, error = await accounts_service.get_all_ad_accounts(
        user.google_id, team_id=scope["token_team_id"], strict_token=scope["strict_token"]
    )
    if (not accounts or error) and scope["fallback_team_id"]:
        accounts, error = await accounts_service.get_all_ad_accounts(user.google_id, team_id=scope["fallback_team_id"])
    if error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"無法取得廣告帳戶：{error}")
    allowed = await accessible_account_ids(user, team)
    return [acc for acc in accounts or [] if acc.get("id") in allowed]


@router.post("/refresh", response_model=RefreshJobResponse, status_code=status.HTTP_202_ACCEPTED)
def start_refresh(
    payload: RefreshRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    account_id = payload.account_id
    verify_account_access_or_403(account_id, team=team, user=user)

    if repository.get_active_job(db, account_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="此帳號正在刷新中，請稍候")

    job = repository.create_job(
        db, account_id=account_id, team_id=team.id if team else None, requested_by=user.id
    )
    response = _job_to_response(job)
    background_tasks.add_task(
        run_refresh,
        job_id=job.id,
        account_id=account_id,
        google_id=user.google_id,
        user_id=user.id,
        **resolve_token_scope(user, team),
    )
    return response


@router.get("/refresh/{job_id}", response_model=RefreshJobResponse)
def get_refresh_job(
    job_id: str,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    not_found = f"刷新任務 {job_id} 不存在"
    job = repository.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found)
    verify_resource_access_or_404(job.account_id, team=team, user=user, not_found_detail=not_found)
    return _job_to_response(job)


@router.get("/ads", response_model=AdLibraryListResponse)
def list_ads(
    account_id: str = Query(...),
    status_filter: str | None = Query(None, alias="status", pattern="^(active|paused|other)$"),
    media_type: str | None = Query(None, pattern="^(image|video|carousel|dynamic)$"),
    q: str | None = Query(None, max_length=200),
    sort: str = Query("impressions", pattern="^(impressions|spend|ctr|created)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=MAX_PAGE_SIZE),
    copy_key: str | None = Query(None, pattern=KEY_PATTERN),
    media_key: str | None = Query(None, pattern=KEY_PATTERN),
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    verify_account_access_or_403(account_id, team=team, user=user)
    repository.ensure_contents(db, account_id)
    items, total = repository.list_items(
        db,
        account_id=account_id,
        status=status_filter,
        media_type=media_type,
        q=q,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
        copy_key=copy_key,
        media_key=media_key,
    )
    counts = repository.same_key_counts(db, account_id, items)
    latest_job = repository.get_latest_job(db, account_id)
    return AdLibraryListResponse(
        items=[_item_to_response(i, counts) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        latest_job=_job_to_response(latest_job) if latest_job else None,
    )


@router.get("/ads/export")
def export_ads(
    account_id: str = Query(...),
    status_filter: str | None = Query(None, alias="status", pattern="^(active|paused|other)$"),
    media_type: str | None = Query(None, pattern="^(image|video|carousel|dynamic)$"),
    q: str | None = Query(None, max_length=200),
    sort: str = Query("impressions", pattern="^(impressions|spend|ctr|created)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    copy_key: str | None = Query(None, pattern=KEY_PATTERN),
    media_key: str | None = Query(None, pattern=KEY_PATTERN),
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    verify_account_access_or_403(account_id, team=team, user=user)
    items, _total = repository.list_items(
        db,
        account_id=account_id,
        status=status_filter,
        media_type=media_type,
        q=q,
        sort=sort,
        order=order,
        page=1,
        page_size=EXPORT_LIMIT,
        copy_key=copy_key,
        media_key=media_key,
    )

    buf = io.StringIO()
    buf.write("﻿")  # UTF-8 BOM，Excel 直接開啟不亂碼
    writer = csv.writer(buf)
    writer.writerow([
        "廣告 ID", "廣告名稱", "行銷活動", "狀態", "素材類型", "主要文字", "標題", "說明",
        "CTA", "連結", "曝光", "觸及", "點擊", "花費", "CTR(%)", "建立時間",
    ])
    for item in items:
        writer.writerow([
            item.ad_id,
            _csv_safe(item.ad_name),
            _csv_safe(item.campaign_name),
            item.effective_status or "",
            item.media_type,
            _csv_safe("\n---\n".join(item.primary_texts or [])),
            _csv_safe(" / ".join(item.headlines or [])),
            _csv_safe(" / ".join(item.descriptions or [])),
            " / ".join(item.cta_types or []),
            _csv_safe(item.link_url),
            item.impressions or 0,
            item.reach or 0,
            item.clicks or 0,
            round(item.spend or 0.0, 2),
            round(item.ctr or 0.0, 2),
            item.ad_created_at.isoformat() if item.ad_created_at else "",
        ])

    filename = f"ad_library_{account_id}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _csv_safe(value) -> str:
    """防 CSV 公式注入：以 = + - @ 開頭的文字前置單引號。"""
    s = "" if value is None else str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


@router.get("/ads/{item_id}", response_model=AdLibraryItemResponse)
def get_ad(
    item_id: str,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    not_found = f"廣告 {item_id} 不存在"
    item = repository.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found)
    verify_resource_access_or_404(item.account_id, team=team, user=user, not_found_detail=not_found)
    return _item_to_response(item)


@router.get("/tree", response_model=AdLibraryTreeResponse)
def get_tree(
    account_id: str = Query(...),
    status_filter: str | None = Query(None, alias="status", pattern="^(active|paused|other)$"),
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    """docs/74：帳號底下的行銷活動 → 廣告組合 → 廣告。"""
    verify_account_access_or_403(account_id, team=team, user=user)
    campaigns, adsets, items = repository.load_hierarchy(db, account_id)
    latest_job = repository.get_latest_job(db, account_id)
    return AdLibraryTreeResponse(
        account_id=account_id,
        campaigns=hierarchy.build_tree(campaigns, adsets, items, status=status_filter),
        latest_job=_job_to_response(latest_job) if latest_job else None,
    )


@router.get("/campaigns/{row_id}", response_model=CampaignDetailResponse)
def get_campaign(
    row_id: str,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    not_found = f"行銷活動 {row_id} 不存在"
    campaign = repository.get_campaign(db, row_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found)
    verify_resource_access_or_404(campaign.account_id, team=team, user=user, not_found_detail=not_found)
    adsets = repository.list_adsets_for_campaign(db, campaign.account_id, campaign.campaign_id)
    node = hierarchy.campaign_node(campaign, [])
    node.pop("adsets")
    adset_nodes = []
    for adset in adsets:
        adset_node = hierarchy.adset_node(adset, [])
        adset_node.pop("ads")
        adset_nodes.append(adset_node)
    return CampaignDetailResponse(campaign=node, adsets=hierarchy.sort_by_spend(adset_nodes))


@router.get("/adsets/{row_id}", response_model=AdsetDetailResponse)
def get_adset(
    row_id: str,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    not_found = f"廣告組合 {row_id} 不存在"
    adset = repository.get_adset(db, row_id)
    if adset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found)
    verify_resource_access_or_404(adset.account_id, team=team, user=user, not_found_detail=not_found)
    items = repository.list_items_for_adset(db, adset.account_id, adset.adset_id)
    node = hierarchy.adset_node(adset, [])
    node.pop("ads")
    # 詳情頁才帶完整原始設定（樹狀列表只帶摘要，避免回應過大）
    node.update({
        "campaign_id": adset.campaign_id,
        "targeting": adset.targeting,
        "promoted_object": adset.promoted_object,
        "attribution_spec": adset.attribution_spec,
    })
    return AdsetDetailResponse(
        adset=node, ads=hierarchy.sort_by_spend([hierarchy.ad_node(i) for i in items])
    )


@router.get("/comparisons", response_model=ComparisonsResponse)
def get_comparisons(
    account_id: str = Query(...),
    scope: str = Query("adset", pattern="^(adset|campaign)$"),
    relation: str | None = Query(None, pattern="^(media_test|copy_test|duplicate)$"),
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    """docs/74 第二節：同範圍內的素材測試、文案測試與重複投放。"""
    verify_account_access_or_403(account_id, team=team, user=user)
    repository.ensure_contents(db, account_id)
    items = repository.list_comparison_items(db, account_id)
    result = comparisons.build_comparisons(items, scope=scope, relation=relation)
    return ComparisonsResponse(account_id=account_id, **result)


def _content_to_response(content, ad_count=0, adset_count=0, campaign_count=0,
                         impressions=0, clicks=0, spend=0.0, asset_metrics=None) -> ContentResponse:
    return ContentResponse(
        id=content.id,
        kind=content.kind,
        text_value=content.text_value,
        image_hash=content.image_hash,
        video_id=content.video_id,
        asset_id=content.asset_id,
        ad_count=ad_count or 0,
        adset_count=adset_count or 0,
        campaign_count=campaign_count or 0,
        impressions=int(impressions or 0),
        clicks=int(clicks or 0),
        spend=float(spend or 0.0),
        ctr=(clicks / impressions * 100) if impressions else 0.0,
        first_seen_at=content.first_seen_at,
        last_seen_at=content.last_seen_at,
        asset_metrics=asset_metrics,
    )


@router.get("/contents", response_model=ContentListResponse)
def list_contents(
    account_id: str = Query(...),
    kind: str | None = Query(None, pattern="^(primary_text|headline|description|image|video)$"),
    q: str | None = Query(None, max_length=200),
    sort: str = Query("ads", pattern="^(ads|spend|impressions|ctr)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=MAX_PAGE_SIZE),
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    """docs/74 第二節：內容元件清單（文案段落、圖片、影片）與使用情形。"""
    verify_account_access_or_403(account_id, team=team, user=user)
    repository.ensure_contents(db, account_id)
    rows, total = repository.list_contents(
        db, account_id=account_id, kind=kind, q=q, sort=sort, page=page, page_size=page_size
    )
    asset_metrics = repository.asset_metrics_for_contents(db, [row[0].id for row in rows])
    return ContentListResponse(
        items=[_content_to_response(*row, asset_metrics=asset_metrics.get(row[0].id)) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        note=CONTENT_NOTE,
    )


@router.get("/contents/{content_id}", response_model=ContentDetailResponse)
def get_content(
    content_id: str,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    not_found = f"內容元件 {content_id} 不存在"
    content = repository.get_content(db, content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found)
    verify_resource_access_or_404(content.account_id, team=team, user=user, not_found_detail=not_found)
    items = repository.list_items_for_content(db, content_id)
    impressions = sum(i.impressions or 0 for i in items)
    clicks = sum(i.clicks or 0 for i in items)
    return ContentDetailResponse(
        content=_content_to_response(
            content,
            ad_count=len(items),
            adset_count=len({i.adset_id for i in items if i.adset_id}),
            campaign_count=len({i.campaign_id for i in items if i.campaign_id}),
            impressions=impressions,
            clicks=clicks,
            spend=sum(i.spend or 0.0 for i in items),
            asset_metrics=repository.asset_metrics_for_contents(db, [content_id]).get(content_id),
        ),
        ads=hierarchy.sort_by_spend([comparisons.ad_summary(i) for i in items]),
    )


@router.get("/ads/{item_id}/asset-insights", response_model=AdAssetInsightsResponse)
def get_ad_asset_insights(
    item_id: str,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    """docs/74 第 3 階段：動態素材廣告的元件成效。"""
    not_found = f"廣告 {item_id} 不存在"
    item = repository.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found)
    verify_resource_access_or_404(item.account_id, team=team, user=user, not_found_detail=not_found)

    entries: dict[str, list[AssetInsightEntry]] = {kind: [] for kind in ASSET_KIND_ORDER}
    fetched_at = None
    for insight, content in repository.asset_insights_for_ad(db, item.account_id, item.ad_id):
        fetched_at = max(fetched_at, insight.fetched_at) if fetched_at else insight.fetched_at
        entries.setdefault(insight.kind, []).append(AssetInsightEntry(
            content_id=content.id,
            kind=insight.kind,
            text_value=content.text_value,
            image_hash=content.image_hash,
            video_id=content.video_id,
            asset_id=content.asset_id,
            impressions=insight.impressions or 0,
            reach=insight.reach or 0,
            clicks=insight.clicks or 0,
            spend=insight.spend or 0.0,
            ctr=(insight.clicks / insight.impressions * 100) if insight.impressions else 0.0,
        ))
    return AdAssetInsightsResponse(
        item_id=item.id,
        ad_id=item.ad_id,
        fetched_at=fetched_at,
        entries={kind: rows for kind, rows in entries.items() if rows},
        note=ASSET_INSIGHTS_NOTE,
    )


@router.get("/ai-context")
def get_ai_context(
    account_id: str = Query(...),
    campaign_id: str | None = Query(None, max_length=64),
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    """docs/74 第 4 階段：給 AI 分析用的精簡 JSON。

    不帶 campaign_id → 各行銷活動摘要；帶 campaign_id → 該行銷活動的完整脈絡
    （行銷活動不屬於此帳號時回 404）。
    """
    verify_account_access_or_403(account_id, team=team, user=user)
    repository.ensure_contents(db, account_id)
    currency = repository.account_currency(db, account_id)
    if not campaign_id:
        campaigns, adsets, items = repository.load_hierarchy(db, account_id)
        return ai_context.build_account_summary(
            account_id=account_id,
            currency=currency,
            tree=hierarchy.build_tree(campaigns, adsets, items),
            items=items,
        )
    bundle = repository.load_campaign_bundle(db, account_id, campaign_id)
    if bundle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"行銷活動 {campaign_id} 不存在")
    return ai_context.build_campaign_context(
        account_id=account_id, currency=currency, campaign_id=campaign_id, **bundle
    )


def _build_campaign_ai_context(db, account_id: str, campaign_id: str) -> dict | None:
    """docs/75：送給模型的脈絡（已套用字數上限）；行銷活動不存在時回 None。"""
    repository.ensure_contents(db, account_id)
    bundle = repository.load_campaign_bundle(db, account_id, campaign_id)
    if bundle is None:
        return None
    context = ai_context.build_campaign_context(
        account_id=account_id,
        currency=repository.account_currency(db, account_id),
        campaign_id=campaign_id,
        **bundle,
    )
    return ai_analysis.fit_context(context)


def _user_ai_model(user, requested: str | None = None) -> str:
    if requested:
        return requested
    settings = TokenManager.get_ai_settings(user.google_id) or {}
    return settings.get("ai_model") or ai_analysis.DEFAULT_MODEL


def _open_session():
    """串流結束後寫入結果用的短 session（測試會替換）。"""
    from database import SessionLocal

    return SessionLocal()


def _analysis_to_dict(row) -> dict | None:
    if row is None:
        return None
    return {
        "id": row.id,
        "model": row.model,
        "status": row.status,
        "content": row.content,
        "context_hash": row.context_hash,
        "context_chars": row.context_chars,
        "created_at": row.created_at,
    }


@router.get("/ai-analysis")
def get_ai_analysis(
    account_id: str = Query(...),
    campaign_id: str = Query(..., max_length=64),
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    """docs/75：最近一次分析結果，以及目前資料的脈絡雜湊（判斷是否需要重新分析）。"""
    verify_account_access_or_403(account_id, team=team, user=user)
    context = _build_campaign_ai_context(db, account_id, campaign_id)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"行銷活動 {campaign_id} 不存在")
    current_hash = ai_analysis.context_hash(context)
    latest = repository.latest_ai_analysis(db, account_id, campaign_id)
    latest_job = repository.get_latest_job(db, account_id)
    return {
        "analysis": _analysis_to_dict(latest),
        "is_stale": bool(latest) and latest.context_hash != current_hash,
        "context_hash": current_hash,
        "context_chars": len(ai_analysis.serialize(context)),
        "model": _user_ai_model(user),
        "has_api_key": bool(TokenManager.get_ai_api_key(user.google_id)),
        "data_fetched_at": latest_job.finished_at if latest_job else None,
    }


@router.post("/ai-analysis")
def start_ai_analysis(
    payload: AiAnalysisRequest,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    """docs/75：串流產生行銷活動 AI 分析，結束後保存（中斷或模型回錯時以 failed 保存已收到的部分）。"""
    account_id, campaign_id = payload.account_id, payload.campaign_id
    verify_account_access_or_403(account_id, team=team, user=user)
    api_key = TokenManager.get_ai_api_key(user.google_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="尚未設定 AI API Key，請先到「設定 → OpenRouter」填入。",
        )
    context = _build_campaign_ai_context(db, account_id, campaign_id)
    if context is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"行銷活動 {campaign_id} 不存在")

    model = _user_ai_model(user, payload.model)
    current_hash = ai_analysis.context_hash(context)
    context_chars = len(ai_analysis.serialize(context))
    user_id = user.id
    # 脈絡已組好，串流（可能數十秒）期間不持有 DB 連線（2026-07-08、2026-08-07 連線池事故）
    db.close()

    def stream():
        chunks: list[str] = []
        completed = False
        try:
            for chunk in AIService.analyze_data(
                data=context,
                context=ai_analysis.PROMPT_CONTEXT,
                api_key=api_key,
                model=model,
                report_type=ai_analysis.REPORT_TYPE,
            ):
                chunks.append(chunk)
                yield chunk
            completed = True
        finally:
            content = "".join(chunks)
            result_status = "succeeded" if completed and not ai_analysis.is_error_output(content) else "failed"
            session = _open_session()
            try:
                repository.save_ai_analysis(
                    session,
                    account_id=account_id,
                    campaign_id=campaign_id,
                    requested_by=user_id,
                    model=model,
                    context_hash=current_hash,
                    context_chars=context_chars,
                    content=content,
                    status=result_status,
                )
            except Exception:
                logger.error("[AdLibrary] failed to save AI analysis for %s/%s", account_id, campaign_id, exc_info=True)
            finally:
                session.close()

    return StreamingResponse(
        stream(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Context-Hash": current_hash},
    )


@router.get("/media/{asset_id}")
async def get_media(
    asset_id: str,
    user=Depends(get_current_user),
    team: Team | None = Depends(get_current_team),
    db=Depends(get_db),
):
    not_found = "素材不存在"
    found = await asyncio.to_thread(repository.find_media_owner, db, asset_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found)
    owners, asset = found
    asset_uri = asset.asset_uri
    storage_backend = asset.storage_backend
    # 已取得所需 metadata，先釋放 DB 連線再做跨服務代理（同 meta_andromeda preview_asset，
    # 2026-08-07 連線池事故）；asset 純量欄位已載入，關閉後仍可存取
    await asyncio.to_thread(db.close)

    if not owners & await accessible_account_ids(user, team):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=not_found)

    response = await build_media_response(asset_uri=asset_uri, storage_backend=storage_backend, asset=asset)
    response.headers["Cache-Control"] = "private, max-age=86400"
    return response
