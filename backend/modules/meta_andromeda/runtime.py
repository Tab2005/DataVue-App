"""
Meta Andromeda Module - Runtime adapter
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from core.config import settings
from .model_registry import MetaAndromedaModelEntry, model_registry


logger = logging.getLogger(__name__)
VALID_ROAS_BANDS = {"high", "mid", "low"}
LABEL_POLICY_VERSION = "ma_label_policy_v1"


def _clip(value: str | None, limit: int = 140) -> str:
    if not value:
        return ""
    return value.strip()[:limit]


def _extract_json_payload(raw_text: str) -> dict:
    candidate = raw_text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _normalize_string_list(value, field_name: str, *, limit: int | None = None) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name}_must_be_list")
    normalized = [str(item).strip() for item in value if str(item).strip()]
    return normalized[:limit] if limit is not None else normalized


def _normalize_diagnostic_breakdown(value) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("diagnostic_breakdown_must_be_object")
    return {str(key): str(item) for key, item in value.items()}


def _build_multimodal_user_content(prompt: str, score_payload: dict) -> list[dict]:
    user_content = [{"type": "text", "text": prompt}]
    request_context = score_payload.get("request_context", {})
    image_url = (
        request_context.get("asset_public_url")
        or request_context.get("preview_url")
        or request_context.get("asset_source_url")
        or score_payload.get("preview_url")
        or score_payload.get("asset_uri")
    )
    if score_payload.get("asset_type") == "image" and isinstance(image_url, str):
        normalized_url = image_url.strip()
        if normalized_url.startswith(("http://", "https://")):
            user_content.append({"type": "image_url", "image_url": {"url": normalized_url}})
    return user_content


def _compute_signal_completeness(score_payload: dict) -> tuple[float, dict]:
    request_context = score_payload.get("request_context", {})
    components = {
        "headline": 1.0 if _clip(request_context.get("headline")) else 0.0,
        "primary_text": 1.0 if _clip(request_context.get("primary_text")) else 0.0,
        "cta": 1.0 if _clip(request_context.get("cta")) else 0.0,
        "image_signal": 1.0 if any(part.get("type") == "image_url" for part in _build_multimodal_user_content("", score_payload)[1:]) else 0.0,
        "objective": 1.0 if _clip(request_context.get("objective") or score_payload.get("objective")) else 0.0,
        "placement_family": 1.0 if _clip(request_context.get("placement_family") or score_payload.get("placement_family")) else 0.0,
        "market": 1.0 if _clip(request_context.get("market") or score_payload.get("market")) else 0.0,
    }
    completeness = sum(components.values()) / len(components)
    return completeness, components


def _compute_confidence(score_payload: dict, *, scoring_mode: str, used_multimodal: bool, fallback_reason: str | None = None) -> tuple[float | None, dict]:
    if score_payload.get("request_mode") == "diagnostic_only":
        return None, {"reason": "diagnostic_only_request"}

    completeness, components = _compute_signal_completeness(score_payload)
    base = 0.42 if scoring_mode == "heuristic" else 0.58
    confidence = base + completeness * (0.26 if scoring_mode == "heuristic" else 0.24)
    if used_multimodal:
        confidence += 0.06
    if fallback_reason:
        confidence -= 0.12
    return max(0.18, min(round(confidence, 4), 0.92)), {
        "signal_completeness": round(completeness, 4),
        "components": components,
        "used_multimodal": used_multimodal,
        "fallback": bool(fallback_reason),
    }


def _validate_provider_result(parsed: dict, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
    prediction_mode = "diagnostic_only" if score_payload.get("request_mode") == "diagnostic_only" else "diagnostic_plus_roas"
    used_multimodal = len(_build_multimodal_user_content("", score_payload)) > 1
    confidence, confidence_detail = _compute_confidence(
        score_payload,
        scoring_mode="ai",
        used_multimodal=used_multimodal,
    )

    raw_score = parsed.get("overall_score")
    if raw_score is None:
        raise ValueError("provider_missing_overall_score")
    try:
        overall_score = int(raw_score)
    except (TypeError, ValueError) as exc:
        raise ValueError("provider_invalid_overall_score") from exc
    if overall_score < 0 or overall_score > 100:
        raise ValueError("provider_invalid_overall_score")

    roas_band = parsed.get("roas_band")
    if prediction_mode == "diagnostic_only":
        roas_band = None
    elif roas_band is not None:
        roas_band = str(roas_band).lower().strip()
        if roas_band not in VALID_ROAS_BANDS:
            raise ValueError("provider_invalid_roas_band")

    top_positive_drivers = _normalize_string_list(parsed.get("top_positive_drivers"), "top_positive_drivers", limit=3)
    top_negative_drivers = _normalize_string_list(parsed.get("top_negative_drivers"), "top_negative_drivers", limit=3)
    risk_tags = _normalize_string_list(parsed.get("risk_tags"), "risk_tags")
    diagnostic_breakdown = _normalize_diagnostic_breakdown(parsed.get("diagnostic_breakdown"))
    summary = str(parsed.get("summary") or "Scored by OpenRouter-backed Meta Andromeda runtime.").strip()

    return {
        "status": "completed",
        "prediction_mode": prediction_mode,
        "overall_score": overall_score,
        "roas_band": roas_band,
        "model_version": registry_entry.model_version,
        "feature_manifest_id": registry_entry.feature_manifest_id,
        "error_message": None,
        "diagnostic_breakdown": diagnostic_breakdown,
        "roas_prediction": {
            "eligible": prediction_mode == "diagnostic_plus_roas",
            "band": roas_band,
            "confidence": confidence,
            "reason_if_unavailable": None if prediction_mode == "diagnostic_plus_roas" else "diagnostic only request",
        },
        "risk_tags": risk_tags,
        "top_positive_drivers": top_positive_drivers,
        "top_negative_drivers": top_negative_drivers,
        "explanations": {
            "summary": summary,
            "top_positive_drivers": top_positive_drivers,
            "top_risks": top_negative_drivers,
            "diagnostic_evidence": {
                "provider": registry_entry.provider,
                "provider_model": registry_entry.provider_model,
                "objective": score_payload.get("objective", "purchase"),
                "placement_family": score_payload.get("placement_family", "all"),
                "confidence_detail": confidence_detail,
            },
        },
        "lineage": {
            "source_ingest_batch_id": f"runtime_batch_{uuid4().hex[:6]}",
            "feature_manifest_id": registry_entry.feature_manifest_id,
            "registry_model_version": registry_entry.model_version,
            "registry_provider": registry_entry.provider,
            "provider_model": registry_entry.provider_model,
            "registry_profile": registry_entry.scoring_profile,
            "registry_source": registry_entry.source_of_truth,
            "scoring_mode": "ai",
            "label_policy_version": LABEL_POLICY_VERSION,
        },
    }


class BaseScoringProvider:
    async def score(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        raise NotImplementedError


class HeuristicScoringProvider(BaseScoringProvider):
    async def score(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        forced_delay_ms = int(score_payload.get("request_context", {}).get("forced_delay_ms") or 0)
        if forced_delay_ms > 0:
            await asyncio.sleep(forced_delay_ms / 1000)
        if score_payload.get("request_context", {}).get("force_failure"):
            raise RuntimeError("forced_runtime_failure")
        return build_heuristic_score_result(score_payload, registry_entry)


class OpenRouterScoringProvider(BaseScoringProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def score(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        from services.ai.openrouter_client import OpenRouterClient
        import openai

        client = OpenRouterClient(api_key=self.api_key)
        if client.client is None:
            raise RuntimeError("OpenRouter client is not configured")

        request_context = score_payload.get("request_context", {})
        request_mode = score_payload.get("request_mode", "auto")
        prompt = (
            "You are the Meta Andromeda creative scoring runtime.\n"
            "Return JSON only with keys: overall_score, roas_band, top_positive_drivers, "
            "top_negative_drivers, risk_tags, diagnostic_breakdown, summary.\n"
            "Use overall_score as integer 0-100.\n"
            "Use roas_band as one of high/mid/low/null.\n"
            "Use diagnostic_breakdown values as short strings.\n"
            "All textual outputs (summary, top_positive_drivers, top_negative_drivers) MUST be in Traditional Chinese.\n"
            f"Asset type: {score_payload['asset_type']}\n"
            f"Objective: {score_payload.get('objective', 'purchase')}\n"
            f"Placement family: {score_payload.get('placement_family', 'all')}\n"
            f"Market: {score_payload.get('market', 'TW')}\n"
            f"Request mode: {request_mode}\n"
            f"Headline: {_clip(request_context.get('headline'))}\n"
            f"Primary text: {_clip(request_context.get('primary_text'))}\n"
            f"CTA: {_clip(request_context.get('cta'))}\n"
        )
        system_prompt = (
            "Score ad creatives conservatively. Keep explanations short. "
            "Prefer stable judgments over hype. "
            "All explanations, summaries, and drivers MUST be written in Traditional Chinese (繁體中文)."
        )
        user_content = _build_multimodal_user_content(prompt, score_payload)
        raw = None
        max_retries = 3
        backoff = 2.0
        for attempt in range(max_retries):
            try:
                raw = await asyncio.to_thread(
                    client.generate_content,
                    prompt,
                    registry_entry.provider_model,
                    system_prompt,
                    0.2,
                    600,
                    settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS,
                    user_content,
                )
                break
            except Exception as e:
                is_rate_limit = False
                if isinstance(e, openai.RateLimitError):
                    is_rate_limit = True
                elif hasattr(e, "status_code") and e.status_code == 429:
                    is_rate_limit = True
                elif "429" in str(e) or "resource_exhausted" in str(e).lower() or "exhausted" in str(e).lower() or "rate_limit" in str(e).lower():
                    is_rate_limit = True
                
                if is_rate_limit and attempt < max_retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(
                        "[MetaAndromeda] OpenRouter 429 Rate Limit hit. Retrying in %.1fs... (Attempt %d/%d)",
                        sleep_time,
                        attempt + 1,
                        max_retries
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    raise
        parsed = _extract_json_payload(raw)

        return _validate_provider_result(parsed, score_payload, registry_entry)


def build_heuristic_score_result(score_payload: dict, registry_entry: MetaAndromedaModelEntry, fallback_reason: str | None = None) -> dict:
    asset_type = score_payload["asset_type"]
    objective = score_payload.get("objective", "purchase")
    request_mode = score_payload.get("request_mode", "auto")
    placement_family = score_payload.get("placement_family", "all")
    request_context = score_payload.get("request_context", {})
    prediction_mode = "diagnostic_plus_roas" if request_mode != "diagnostic_only" else "diagnostic_only"

    score = 56 if asset_type == "image" else 52
    if objective == "purchase":
        score += 3
    elif objective == "lead":
        score += 2
    if _clip(request_context.get("headline")):
        score += 8
    else:
        score -= 5
    if _clip(request_context.get("primary_text")):
        score += 8
    else:
        score -= 6
    if _clip(request_context.get("cta")):
        score += 10
    else:
        score -= 5
    if placement_family in {"feed", "stories"}:
        score += 4
    if not _clip(request_context.get("headline")) and not _clip(request_context.get("primary_text")) and not _clip(request_context.get("cta")):
        score -= 8
    score = max(24, min(score, 88))

    used_multimodal = len(_build_multimodal_user_content("", score_payload)) > 1
    confidence, confidence_detail = _compute_confidence(
        score_payload,
        scoring_mode="heuristic",
        used_multimodal=used_multimodal,
        fallback_reason=fallback_reason,
    )

    if score >= 80:
        roas_band = "high"
    elif score >= 66:
        roas_band = "mid"
    else:
        roas_band = "low"

    top_positive_drivers = []
    if _clip(request_context.get("cta")):
        top_positive_drivers.append("明確的行動呼籲 (CTA)")
    if _clip(request_context.get("headline")):
        top_positive_drivers.append("包含廣告標題")
    if placement_family in {"feed", "stories"}:
        top_positive_drivers.append("版位適配良好")
    if not top_positive_drivers:
        top_positive_drivers.append("基礎素材完整度良好")

    top_negative_drivers = []
    if not _clip(request_context.get("headline")):
        top_negative_drivers.append("缺少廣告標題")
    if not _clip(request_context.get("primary_text")):
        top_negative_drivers.append("缺少主要文字")
    if fallback_reason:
        top_negative_drivers.append("已啟用 AI 執行期備用方案")
    if not top_negative_drivers:
        top_negative_drivers.append("細部調整需人工審核")

    risk_tags = ["heuristic_runtime"]
    if fallback_reason:
        risk_tags.append("provider_fallback")

    return {
        "status": "completed",
        "prediction_mode": prediction_mode,
        "overall_score": score,
        "roas_band": roas_band if prediction_mode == "diagnostic_plus_roas" else None,
        "model_version": registry_entry.model_version,
        "feature_manifest_id": registry_entry.feature_manifest_id,
        "error_message": None,
        "diagnostic_breakdown": {
            "hook_strength": "good" if _clip(request_context.get("headline")) else "needs_work",
            "cta_presence": "clear" if _clip(request_context.get("cta")) else "missing",
            "placement_fit": "good" if placement_family in {"feed", "stories"} else "neutral",
        },
        "roas_prediction": {
            "eligible": prediction_mode == "diagnostic_plus_roas",
            "band": roas_band if prediction_mode == "diagnostic_plus_roas" else None,
            "confidence": confidence,
            "reason_if_unavailable": None if prediction_mode == "diagnostic_plus_roas" else "diagnostic only request",
        },
        "risk_tags": risk_tags,
        "top_positive_drivers": top_positive_drivers[:3],
        "top_negative_drivers": top_negative_drivers[:3],
        "explanations": {
            "summary": "由 DataVue 註冊表支援的啟發式執行程序完成評分。",
            "top_positive_drivers": top_positive_drivers[:3],
            "top_risks": top_negative_drivers[:3],
            "diagnostic_evidence": {
                "provider": registry_entry.provider,
                "provider_model": registry_entry.provider_model,
                "objective": objective,
                "placement_family": placement_family,
                "confidence_detail": confidence_detail,
            },
        },
        "lineage": {
            "source_ingest_batch_id": f"runtime_batch_{uuid4().hex[:6]}",
            "feature_manifest_id": registry_entry.feature_manifest_id,
            "registry_model_version": registry_entry.model_version,
            "registry_provider": registry_entry.provider,
            "provider_model": registry_entry.provider_model,
            "registry_profile": registry_entry.scoring_profile,
            "registry_source": registry_entry.source_of_truth,
            "scoring_mode": "heuristic",
            "fallback_reason": fallback_reason or "",
            "label_policy_version": LABEL_POLICY_VERSION,
        },
    }


class MetaAndromedaRuntimeAdapter:
    """Registry-backed runtime adapter for queued score processing."""

    @staticmethod
    def build_score_submission(payload: dict) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "score_event_id": f"ma_evt_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:4]}",
            "status": "queued",
            "runtime_job_id": None,
            "created_at": now,
            "queued_at": now,
            "started_at": None,
            "completed_at": None,
            "failed_at": None,
            "updated_at": now,
            "asset_uri": payload["asset_uri"],
            "asset_type": payload["asset_type"],
            "asset_id": payload.get("asset_id"),
            "preview_url": None,
            "request_mode": payload.get("request_mode", "auto"),
            "objective": payload.get("objective", "purchase"),
            "placement_family": payload.get("placement_family", "all"),
            "market": payload.get("market", "TW"),
            "prediction_mode": None,
            "overall_score": None,
            "roas_band": None,
            "model_version": None,
            "reviewed": False,
            "feedback_count": 0,
            "latest_feedback_decision": None,
            "feature_manifest_id": None,
            "error_message": None,
            "attempt_count": 0,
            "diagnostic_breakdown": {},
            "roas_prediction": None,
            "risk_tags": [],
            "top_positive_drivers": [],
            "top_negative_drivers": [],
            "explanations": None,
            "lineage": {},
            "request_context": {
                "headline": payload.get("headline"),
                "primary_text": payload.get("primary_text"),
                "cta": payload.get("cta"),
                "objective": payload.get("objective", "purchase"),
                "placement_family": payload.get("placement_family", "all"),
                "market": payload.get("market", "TW"),
                "request_mode": payload.get("request_mode", "auto"),
            },
        }

    @staticmethod
    async def generate_score_result(score_payload: dict) -> dict:
        """Run registry-backed scoring with optional AI provider fallback."""
        await asyncio.sleep(0.05)
        registry_entry = model_registry.get_entry()
        provider_name = registry_entry.provider
        import os

        # 嘗試從資料庫讀取該素材上傳者的 API 金鑰
        db_key = None
        asset_id = score_payload.get("asset_id")
        if asset_id:
            try:
                from database import SessionLocal
                from database.models.meta_andromeda import MetaAndromedaAsset
                from database.models.user import User
                from modules.auth.service import TokenManager

                db_session = SessionLocal()
                try:
                    asset = db_session.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.id == asset_id).first()
                    if asset and asset.uploaded_by:
                        user = db_session.query(User).filter(User.id == asset.uploaded_by).first()
                        if user and user.google_id:
                            db_key = TokenManager.get_ai_api_key(user.google_id, provider="openrouter")
                    if asset:
                        request_context = score_payload.setdefault("request_context", {})
                        request_context.setdefault("asset_public_url", asset.public_url)
                        request_context.setdefault("asset_source_url", asset.asset_uri)
                finally:
                    db_session.close()
            except Exception as e:
                logger.error(f"[MetaAndromeda] Failed to retrieve DB API key for asset {asset_id}: {e}")

        openrouter_key = db_key or os.getenv("OPENROUTER_API_KEY")
        zeabur_key = os.getenv("ZEABUR_AI_HUB_API_KEY")

        logger.warning(
            "[MetaAndromeda] generate_score_result. DB Key present: %s, OPENROUTER_API_KEY len: %s, provider_override: %s",
            bool(db_key),
            len(openrouter_key) if openrouter_key else 0,
            settings.META_ANDROMEDA_SCORING_PROVIDER
        )

        if settings.META_ANDROMEDA_SCORING_PROVIDER == "heuristic":
            provider_name = "heuristic"
        elif settings.META_ANDROMEDA_SCORING_PROVIDER == "openrouter":
            provider_name = "openrouter"
        else:
            has_any_openrouter_key = bool(openrouter_key) or bool(settings.OPENROUTER_API_KEY)
            if provider_name == "openrouter" and not has_any_openrouter_key:
                provider_name = "heuristic"

        provider: BaseScoringProvider
        if provider_name == "openrouter":
            provider = OpenRouterScoringProvider(api_key=openrouter_key)
        else:
            provider = HeuristicScoringProvider()

        try:
            return await provider.score(score_payload, registry_entry)
        except Exception as exc:
            logger.warning("Meta Andromeda scoring provider failed: %s", exc)
            if not settings.META_ANDROMENS_SCORING_ALLOW_FALLBACK if hasattr(settings, "META_ANDROMENS_SCORING_ALLOW_FALLBACK") else not settings.META_ANDROMEDA_SCORING_ALLOW_FALLBACK:
                raise
            fallback_entry = model_registry.get_entry("candidate_v0")
            err_detail = str(exc).replace("\n", " ")
            return build_heuristic_score_result(
                score_payload,
                fallback_entry,
                fallback_reason=f"{provider_name}:{type(exc).__name__} ({err_detail[:120]})",
            )


runtime_adapter = MetaAndromedaRuntimeAdapter()
