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


class GeminiScoringProvider(BaseScoringProvider):
    async def score(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        from services.ai.gemini_client import GoogleGeminiClient

        client = GoogleGeminiClient()
        if client.client is None:
            raise RuntimeError("Gemini client is not configured")

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
        raw = await asyncio.to_thread(
            client.generate_content,
            prompt,
            registry_entry.provider_model,
            system_prompt,
            0.2,
            600,
        )
        parsed = _extract_json_payload(raw)

        prediction_mode = "diagnostic_only" if request_mode == "diagnostic_only" else "diagnostic_plus_roas"
        roas_band = parsed.get("roas_band")
        if prediction_mode == "diagnostic_only":
            roas_band = None

        return {
            "status": "completed",
            "prediction_mode": prediction_mode,
            "overall_score": max(0, min(int(parsed.get("overall_score", 70)), 100)),
            "roas_band": roas_band,
            "model_version": registry_entry.model_version,
            "feature_manifest_id": registry_entry.feature_manifest_id,
            "error_message": None,
            "diagnostic_breakdown": {
                key: str(value) for key, value in (parsed.get("diagnostic_breakdown") or {}).items()
            },
            "roas_prediction": {
                "eligible": prediction_mode == "diagnostic_plus_roas",
                "band": roas_band,
                "confidence": 0.72 if prediction_mode == "diagnostic_plus_roas" else None,
                "reason_if_unavailable": None if prediction_mode == "diagnostic_plus_roas" else "diagnostic only request",
            },
            "risk_tags": [str(item) for item in (parsed.get("risk_tags") or [])],
            "top_positive_drivers": [str(item) for item in (parsed.get("top_positive_drivers") or [])][:3],
            "top_negative_drivers": [str(item) for item in (parsed.get("top_negative_drivers") or [])][:3],
            "explanations": {
                "summary": str(parsed.get("summary") or "Scored by Gemini-backed Meta Andromeda runtime."),
                "top_positive_drivers": [str(item) for item in (parsed.get("top_positive_drivers") or [])][:3],
                "top_risks": [str(item) for item in (parsed.get("top_negative_drivers") or [])][:3],
                "diagnostic_evidence": {
                    "provider": registry_entry.provider,
                    "provider_model": registry_entry.provider_model,
                    "objective": score_payload.get("objective", "purchase"),
                    "placement_family": score_payload.get("placement_family", "all"),
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
            },
        }


def build_heuristic_score_result(score_payload: dict, registry_entry: MetaAndromedaModelEntry, fallback_reason: str | None = None) -> dict:
    asset_type = score_payload["asset_type"]
    objective = score_payload.get("objective", "purchase")
    request_mode = score_payload.get("request_mode", "auto")
    placement_family = score_payload.get("placement_family", "all")
    request_context = score_payload.get("request_context", {})
    prediction_mode = "diagnostic_plus_roas" if request_mode != "diagnostic_only" else "diagnostic_only"

    score = 72 if asset_type == "image" else 67
    if objective == "purchase":
        score += 4
    if objective == "lead":
        score += 1
    if _clip(request_context.get("headline")):
        score += 4
    if _clip(request_context.get("primary_text")):
        score += 3
    if _clip(request_context.get("cta")):
        score += 5
    if placement_family in {"feed", "stories"}:
        score += 2
    score = max(48, min(score, 91))

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
            "confidence": 0.61 if prediction_mode == "diagnostic_plus_roas" else None,
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

        if settings.META_ANDROMEDA_SCORING_PROVIDER == "auto" and provider_name == "gemini" and not settings.GOOGLE_AI_API_KEY:
            provider_name = "heuristic"

        provider: BaseScoringProvider
        if provider_name == "gemini":
            provider = GeminiScoringProvider()
        else:
            provider = HeuristicScoringProvider()

        try:
            return await provider.score(score_payload, registry_entry)
        except Exception as exc:
            logger.warning("Meta Andromeda scoring provider failed: %s", exc)
            if not settings.META_ANDROMEDA_SCORING_ALLOW_FALLBACK:
                raise
            fallback_entry = model_registry.get_entry("candidate_v0")
            return build_heuristic_score_result(
                score_payload,
                fallback_entry,
                fallback_reason=f"{provider_name}:{type(exc).__name__}",
            )


runtime_adapter = MetaAndromedaRuntimeAdapter()
