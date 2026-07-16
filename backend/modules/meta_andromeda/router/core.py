"""Core routes for Meta Andromeda."""

from __future__ import annotations

from ._shared import *

router = APIRouter()


@router.get("/ping", response_model=PingResponse)
async def ping(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
):
    """Minimal health endpoint for the first integration slice."""
    return MetaAndromedaService.get_ping_payload()


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """Read-only overview endpoint for the second integration slice."""
    return MetaAndromedaService.get_overview_payload()


@router.get("/runtime-health", response_model=RuntimeHealthResponse, include_in_schema=False)
@router.get("/runtime/health", response_model=RuntimeHealthResponse)
async def runtime_health(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
    db=Depends(get_db),
):
    """Shared-runtime readiness summary for Meta Andromeda on the current host."""
    return MetaAndromedaService.get_runtime_health(db)


@router.get("/runtime/ai-ready", response_model=AiReadyResponse)
async def runtime_ai_ready(
    _user=Depends(get_current_meta_andromeda_user),
    _access: bool = Depends(require_meta_andromeda_module),
):
    """輕量連線確認：檢查 AI 評分設定是否正常，不實際呼叫 AI 模型。"""
    from core.config import settings
    from modules.auth.service import TokenManager

    provider = settings.META_ANDROMEDA_SCORING_PROVIDER
    allow_fallback = settings.META_ANDROMEDA_SCORING_ALLOW_FALLBACK

    # 優先查後台個人設定的 API Key（與實際評分流程一致）
    db_key = None
    if _user and _user.google_id:
        try:
            db_key = TokenManager.get_ai_api_key(_user.google_id, provider="openrouter")
        except Exception:
            pass

    # 再 fallback 至環境變數（OPENROUTER_API_KEY 或 ZEABUR_AI_HUB_API_KEY）
    api_key_configured = bool(db_key) or bool(settings.OPENROUTER_API_KEY)

    if provider == "heuristic":
        return AiReadyResponse(
            ready=False,
            provider="heuristic",
            api_key_configured=False,
            allow_fallback=allow_fallback,
            warning="評分服務設定為啟發式備用模式，批次評分不會使用 AI 模型。",
        )

    if provider == "openrouter" or provider == "auto":
        if not api_key_configured:
            return AiReadyResponse(
                ready=False,
                provider=provider,
                api_key_configured=False,
                allow_fallback=allow_fallback,
                warning="未設定 OpenRouter API Key，批次評分將使用啟發式備用模式，評分準確度較低。",
            )
        return AiReadyResponse(
            ready=True,
            provider=provider,
            api_key_configured=True,
            allow_fallback=allow_fallback,
            warning=None,
        )

    return AiReadyResponse(
        ready=False,
        provider=provider,
        api_key_configured=api_key_configured,
        allow_fallback=allow_fallback,
        warning=f"未知的評分 Provider：{provider}，批次評分將使用備用模式。",
    )
