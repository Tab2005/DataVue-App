"""
Meta Andromeda Module - Runtime adapter
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from core.config import settings
from .cache_invalidation import publish_invalidation, register_invalidation_handler
from .model_registry import MetaAndromedaModelEntry, model_registry
from .objective_routing import is_roas_band_eligible, resolve_objective_group
from .labeling import LABEL_POLICY_VERSION
from .confidence import (
    VALID_ROAS_BANDS,
    _aggregate_self_consistency_samples,
    _build_multimodal_user_content,
    _clip,
    _compute_confidence,
    _resolve_self_consistency_sample_count,
)
from .heuristic import build_heuristic_score_result
from .prompt_profiles import (
    _DEFAULT_OBJECTIVE_PROFILES,
    _DIAGNOSTIC_SCORE_FORMAT_INSTRUCTION,
    _FALLBACK_SYSTEM_PROMPT,
    _FALLBACK_USER_PROMPT_TEMPLATE,
    _load_scoring_profile,
    _resolve_active_profile,
    invalidate_prompt_cache,
)
from .result_parsing import _extract_json_payload, _validate_provider_result


logger = logging.getLogger(__name__)
VALID_ROAS_BANDS = {"high", "mid", "low"}

# TTL 作為多 worker 快取失效的底線：即使 Redis pub/sub 通知因故沒送達（worker 啟動時機、
# 網路抖動等），5 分鐘後也會自動視為過期重新查 DB，不會無限期卡在舊 prompt
# 附加於每個 objective_group prompt 之後（統一在 render 時 append，而非逐一改寫每份 prompt
# template），要求 diagnostic_breakdown 每個維度輸出結構化數值分數，供統計校準層使用
# OpenRouter/OpenAI-style structured-output schema (docs/20 P2-2). Not every model routed
# through OpenRouter honors response_format, so this is tried first and callers must fall
# back to the existing regex-based _extract_json_payload() path on any failure — never assume
# a model actually obeys the schema.
_SCORE_RESPONSE_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "meta_andromeda_creative_score",
        "strict": False,
        "schema": {
            "type": "object",
            "properties": {
                "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
                "roas_band": {"type": ["string", "null"], "enum": ["high", "mid", "low", None]},
                "top_positive_drivers": {"type": "array", "items": {"type": "string"}},
                "top_negative_drivers": {"type": "array", "items": {"type": "string"}},
                "risk_tags": {"type": "array", "items": {"type": "string"}},
                "diagnostic_breakdown": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "reasoning": {"type": "string"},
                        },
                    },
                },
                "summary": {"type": "string"},
            },
            "required": ["overall_score", "summary"],
        },
    },
}

# 評分請求的預設輸出上限。部分（尤其 free 版）模型在 OpenRouter 上實際 serving 端點的
# context 上限，跟型號名稱給人的印象差很多（例如曾誤設的 `llama-nemotron-embed-vl-1b-v2:
# free`，端點回報上限只有 10240 tokens）——直接調高這個預設值只會讓「prompt + max_tokens
# 超過端點真實上限」更容易發生，不解決問題；真正需要的是下面 `_shrink_max_tokens_for_
# context_error()` 這種按實際錯誤動態退讓的機制。
_DEFAULT_SCORE_MAX_TOKENS = 8192
_MIN_SCORE_MAX_TOKENS = 512
_CONTEXT_ERROR_SAFETY_MARGIN = 256

# OpenRouter 400 錯誤的標準格式："This endpoint's maximum context length is 10240 tokens.
# However, you requested about 10500 tokens (10000 of text input, 500 in the output)."
_CONTEXT_LENGTH_ERROR_RE = re.compile(
    r"maximum context length is (\d+) tokens.*?\((\d+) of text input",
    re.IGNORECASE | re.DOTALL,
)


def _shrink_max_tokens_for_context_error(exc: Exception, current_max_tokens: int) -> int | None:
    """解析 OpenRouter 的 context-length-exceeded 錯誤訊息，算出一個塞得下該端點真實上限
    的 max_tokens 讓呼叫端重試——用實際錯誤回饋動態退讓，而不是要求 ops 為每個候選模型
    手動猜一個夠小的固定值。訊息格式不符預期（provider 換了措辭）或算出來的值沒有比目前
    小，回傳 None，讓呼叫端照原本的邏輯直接放棄重試。"""
    match = _CONTEXT_LENGTH_ERROR_RE.search(str(exc))
    if not match:
        return None
    context_limit, input_tokens = int(match.group(1)), int(match.group(2))
    safe_max_tokens = context_limit - input_tokens - _CONTEXT_ERROR_SAFETY_MARGIN
    if safe_max_tokens < _MIN_SCORE_MAX_TOKENS or safe_max_tokens >= current_max_tokens:
        return None
    return safe_max_tokens
def resolve_openrouter_api_key_for_asset(db_session, asset_id: str | None) -> str | None:
    """Look up the OpenRouter API key belonging to whoever uploaded this asset — the
    same per-user, DB-stored key resolution MetaAndromedaRuntime.generate_score_result
    uses for live scoring — falling back to the raw OPENROUTER_API_KEY env var.

    Any code path that talks to OpenRouter directly (calibration_pipeline.py's LLM
    guidance generator and holdout backtest scorer both did this) MUST go through here
    instead of reading settings.OPENROUTER_API_KEY alone: in deployments where the
    working key lives per-user in the DB rather than as a container env var, that
    shortcut makes every such call fail with "OpenRouter client is not configured"
    (2026-07-03 incident: broke the holdout backtest — 0/22 items scored — and silently
    degraded LLM calibration-guidance generation to its hardcoded template fallback).
    """
    if asset_id:
        try:
            from database.models.meta_andromeda import MetaAndromedaAsset
            from database.models.user import User
            from modules.auth.service import TokenManager

            asset = db_session.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.id == asset_id).first()
            if asset and asset.uploaded_by:
                user = db_session.query(User).filter(User.id == asset.uploaded_by).first()
                if user and user.google_id:
                    db_key = TokenManager.get_ai_api_key(user.google_id, provider="openrouter")
                    if db_key:
                        return db_key
        except Exception as exc:
            logger.warning(
                "[MetaAndromeda] Failed to resolve per-user OpenRouter key for asset %s: %s",
                asset_id, exc,
            )
    return settings.OPENROUTER_API_KEY
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
    def __init__(self, api_key: str | None = None, force_profile_name: str | None = None):
        self.api_key = api_key
        # 回測用：強制使用指定 profile_name，忽略 is_promoted 全域覆蓋，
        # 才能在別的 profile 已上線時仍獨立評估候選 profile
        self.force_profile_name = force_profile_name

    def _build_prompt(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        request_context = score_payload.get("request_context", {})
        if not isinstance(request_context, dict):
            request_context = {}
        request_mode = score_payload.get("request_mode", "auto")

        if self.force_profile_name:
            base_profile = _load_scoring_profile(self.force_profile_name, ignore_promoted=True)
        else:
            base_profile = _load_scoring_profile(registry_entry.scoring_profile)
        objective_group = resolve_objective_group(score_payload.get("objective"))
        active_profile = _resolve_active_profile(base_profile, objective_group)
        _fmt = {
            "asset_type": score_payload.get("asset_type", "image"),
            "objective": score_payload.get("objective", "purchase"),
            "placement_family": score_payload.get("placement_family", "all"),
            "market": score_payload.get("market", "TW"),
            "request_mode": request_mode,
            "headline": _clip(request_context.get("headline")),
            "primary_text": _clip(request_context.get("primary_text")),
            "cta": _clip(request_context.get("cta")),
        }
        prompt = active_profile["user_prompt_template"].format_map(_fmt)
        prompt += _DIAGNOSTIC_SCORE_FORMAT_INSTRUCTION
        if active_profile.get("calibration_guidance"):
            prompt += f"\n\n{active_profile['calibration_guidance']}"
        few_shot_examples = active_profile.get("few_shot_examples")
        few_shot_image_blocks: list[dict] = []
        if few_shot_examples and isinstance(few_shot_examples, list):
            from .calibration_pipeline import format_few_shot_content
            few_shot_text, few_shot_image_blocks = format_few_shot_content(few_shot_examples)
            prompt += few_shot_text
        system_prompt = active_profile["system_prompt"]
        user_content = _build_multimodal_user_content(prompt, score_payload)
        # few-shot 圖片附加在主素材圖片之後，讓模型能實際「看到」校準範例，而非只靠文字描述
        user_content.extend(few_shot_image_blocks)
        return {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "user_content": user_content,
            "active_profile": active_profile,
            "objective_group": objective_group,
        }

    @staticmethod
    async def _call_provider_once(
        client,
        prompt: str,
        system_prompt: str,
        user_content,
        registry_entry: MetaAndromedaModelEntry,
        *,
        use_structured_output: bool,
    ) -> dict:
        """One full attempt (with its own rate-limit retry loop), returning the
        parsed JSON payload. use_structured_output tries response_format=
        json_schema first (P2-2) as a fast pre-attempt — any failure there
        (model doesn't support it, malformed response, ...) falls through to
        the existing, already-battle-tested regex-parsed retry loop unchanged.
        """
        import openai

        if use_structured_output:
            try:
                raw = await asyncio.to_thread(
                    client.generate_content,
                    prompt,
                    registry_entry.provider_model,
                    system_prompt,
                    0.2,
                    8192,
                    settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS,
                    user_content,
                    _SCORE_RESPONSE_JSON_SCHEMA,
                )
                if raw and raw.strip():
                    return _extract_json_payload(raw)
            except Exception as exc:
                logger.info(
                    "[MetaAndromeda] Structured output attempt failed (%s), falling back to regex-parsed prompt.",
                    exc,
                )

        raw = None
        max_retries = 3
        backoff = 2.0
        max_tokens = _DEFAULT_SCORE_MAX_TOKENS
        for attempt in range(max_retries):
            try:
                raw = await asyncio.to_thread(
                    client.generate_content,
                    prompt,
                    registry_entry.provider_model,
                    system_prompt,
                    0.2,
                    max_tokens,
                    settings.META_ANDROMEDA_SCORE_TIMEOUT_SECONDS,
                    user_content,
                )
                if not raw or not raw.strip():
                    if attempt < max_retries - 1:
                        sleep_time = backoff * (2 ** attempt)
                        logger.warning(
                            "[MetaAndromeda] OpenRouter returned empty response. Retrying in %.1fs... (Attempt %d/%d)",
                            sleep_time, attempt + 1, max_retries,
                        )
                        await asyncio.sleep(sleep_time)
                        continue
                break
            except Exception as e:
                is_rate_limit = False
                if isinstance(e, openai.RateLimitError):
                    is_rate_limit = True
                elif hasattr(e, "status_code") and e.status_code == 429:
                    is_rate_limit = True
                elif "429" in str(e) or "resource_exhausted" in str(e).lower() or "exhausted" in str(e).lower() or "rate_limit" in str(e).lower():
                    is_rate_limit = True

                shrunk_max_tokens = _shrink_max_tokens_for_context_error(e, max_tokens)

                if is_rate_limit and attempt < max_retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(
                        "[MetaAndromeda] OpenRouter 429 Rate Limit hit. Retrying in %.1fs... (Attempt %d/%d)",
                        sleep_time,
                        attempt + 1,
                        max_retries
                    )
                    await asyncio.sleep(sleep_time)
                elif shrunk_max_tokens is not None and attempt < max_retries - 1:
                    max_tokens = shrunk_max_tokens
                    logger.warning(
                        "[MetaAndromeda] OpenRouter context length exceeded for model %s, retrying with "
                        "max_tokens=%d (Attempt %d/%d)",
                        registry_entry.provider_model, max_tokens, attempt + 1, max_retries,
                    )
                else:
                    raise
        return _extract_json_payload(raw)

    async def score(self, score_payload: dict, registry_entry: MetaAndromedaModelEntry) -> dict:
        from services.ai.openrouter_client import OpenRouterClient

        client = OpenRouterClient(api_key=self.api_key)
        if client.client is None:
            raise RuntimeError("OpenRouter client is not configured")

        built = self._build_prompt(score_payload, registry_entry)
        prompt = built["prompt"]
        system_prompt = built["system_prompt"]
        user_content = built["user_content"]
        active_profile = built["active_profile"]
        objective_group = built["objective_group"]

        sample_count = _resolve_self_consistency_sample_count(score_payload)
        use_structured_output = settings.META_ANDROMEDA_STRUCTURED_OUTPUT_ENABLED

        if sample_count <= 1:
            parsed = await self._call_provider_once(
                client, prompt, system_prompt, user_content, registry_entry,
                use_structured_output=use_structured_output,
            )
        else:
            # 依序取樣（非併發）：避免對本來就嚴格限流的 provider 一次炸出 N 倍請求，
            # 用延遲換取穩定性——這類請求本來就是背景非互動流程，不急著在幾秒內回應
            samples = []
            for i in range(sample_count):
                try:
                    sample = await self._call_provider_once(
                        client, prompt, system_prompt, user_content, registry_entry,
                        use_structured_output=use_structured_output,
                    )
                    samples.append(sample)
                except Exception as exc:
                    logger.warning(
                        "[MetaAndromeda] Self-consistency sample %d/%d failed: %s",
                        i + 1, sample_count, exc,
                    )
            if not samples:
                raise RuntimeError("self_consistency_all_samples_failed")
            parsed = _aggregate_self_consistency_samples(samples)

        return _validate_provider_result(
            parsed,
            score_payload,
            registry_entry,
            roas_band_eligible=active_profile.get("roas_band_eligible", True),
            objective_group=objective_group,
            prompt_profile_used=active_profile.get("resolved_profile_name"),
        )
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
                "origin": "score_lab",
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
    def _prepare_asset_context(score_payload: dict) -> str | None:
        """同步阻塞版本的素材準備：DB 查詢上傳者金鑰、讀檔/S3 下載、base64 編碼、
        ffmpeg keyframe 抽取。這些全是阻塞 I/O，必須透過 asyncio.to_thread 呼叫，
        不可直接 await（否則會卡住 FastAPI 的 event loop，見 docs/24 Wave 1）。

        直接 mutate score_payload["request_context"]；回傳素材上傳者自己的
        OpenRouter API 金鑰（若有）。
        """
        db_key = None
        asset_id = score_payload.get("asset_id")
        if not asset_id:
            return db_key

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

                    # 若為內部儲存協議，將其轉為 Base64 Data URI 直接傳送給 AI
                    if asset.asset_uri.startswith("storage://") and asset.asset_type == "image":
                        try:
                            import base64
                            from pathlib import Path

                            if asset.storage_backend == "filesystem":
                                storage_root = Path(settings.META_ANDROMEDA_STORAGE_ROOT)
                                safe_path = (storage_root / asset.storage_key).resolve()
                                if safe_path.relative_to(storage_root.resolve()) and safe_path.exists():
                                    file_bytes = safe_path.read_bytes()
                                    mime = "image/png"
                                    if asset.source_filename.lower().endswith((".jpg", ".jpeg")):
                                        mime = "image/jpeg"
                                    elif asset.source_filename.lower().endswith(".webp"):
                                        mime = "image/webp"
                                    elif asset.source_filename.lower().endswith(".gif"):
                                        mime = "image/gif"
                                    base64_str = base64.b64encode(file_bytes).decode("utf-8")
                                    request_context["asset_public_url"] = f"data:{mime};base64,{base64_str}"

                            elif asset.storage_backend == "s3_compatible":
                                from .storage import storage_adapter
                                client = storage_adapter._build_s3_client()
                                bucket = settings.META_ANDROMEDA_STORAGE_S3_BUCKET
                                response = client.get_object(Bucket=bucket, Key=asset.storage_key)
                                file_bytes = response['Body'].read()
                                mime = response.get('ContentType', 'image/png')
                                base64_str = base64.b64encode(file_bytes).decode("utf-8")
                                request_context["asset_public_url"] = f"data:{mime};base64,{base64_str}"
                        except Exception as parse_exc:
                            logger.error(f"[MetaAndromeda] Base64 encoding failed for asset {asset_id}: {parse_exc}")

                    # 影片素材：抽 keyframes 多圖傳入，讓模型能實際「看到」內容而非只憑文案盲評。
                    # 任何失敗（ffmpeg 不存在、檔案損毀、逾時）都優雅退化為空列表，之後在
                    # _validate_provider_result 標記 video_content_not_inspected 並顯著調降 confidence。
                    elif asset.asset_uri.startswith("storage://") and asset.asset_type == "video":
                        try:
                            from .video_utils import extract_video_keyframes_base64

                            video_bytes = None
                            if asset.storage_backend == "filesystem":
                                from pathlib import Path
                                storage_root = Path(settings.META_ANDROMEDA_STORAGE_ROOT)
                                safe_path = (storage_root / asset.storage_key).resolve()
                                if safe_path.relative_to(storage_root.resolve()) and safe_path.exists():
                                    video_bytes = safe_path.read_bytes()
                            elif asset.storage_backend == "s3_compatible":
                                from .storage import storage_adapter
                                client = storage_adapter._build_s3_client()
                                bucket = settings.META_ANDROMEDA_STORAGE_S3_BUCKET
                                response = client.get_object(Bucket=bucket, Key=asset.storage_key)
                                video_bytes = response['Body'].read()

                            if video_bytes:
                                keyframe_urls = extract_video_keyframes_base64(video_bytes)
                                if keyframe_urls:
                                    request_context["video_keyframe_urls"] = keyframe_urls
                        except Exception as parse_exc:
                            logger.warning(f"[MetaAndromeda] Video keyframe extraction failed for asset {asset_id}: {parse_exc}")
            finally:
                db_session.close()
        except Exception as e:
            logger.error(f"[MetaAndromeda] Failed to retrieve DB API key for asset {asset_id}: {e}")

        return db_key

    @staticmethod
    async def generate_score_result(score_payload: dict) -> dict:
        """Run registry-backed scoring with optional AI provider fallback."""
        request_context = score_payload.get("request_context", {})
        if not isinstance(request_context, dict):
            request_context = {}
        backtest_provider_model = request_context.get("backtest_provider_model")
        if request_context.get("scoring_purpose") == "backtest" and backtest_provider_model:
            base_entry = model_registry.get_entry(purpose="backtest")
            registry_entry = MetaAndromedaModelEntry(
                model_version=f"backtest:{backtest_provider_model}",
                provider="openrouter",
                provider_model=backtest_provider_model,
                scoring_profile=base_entry.scoring_profile,
                feature_manifest_id=f"fm_backtest_{uuid4().hex[:8]}",
                release_channel="backtest_run",
                source_of_truth="datavue.meta_andromeda.backtest_run",
            )
        else:
            purpose = "backtest" if request_context.get("is_backtest") else "interactive"
            registry_entry = model_registry.get_entry(purpose=purpose)
        provider_name = registry_entry.provider

        # 素材準備（DB 查詢、讀檔、base64、S3 下載、ffmpeg 抽幀）是同步阻塞 I/O，
        # 丟到 thread 執行避免卡住 event loop（docs/24 Wave 1）。
        db_key = await asyncio.to_thread(
            MetaAndromedaRuntimeAdapter._prepare_asset_context, score_payload
        )

        openrouter_key = db_key or settings.OPENROUTER_API_KEY

        logger.debug(
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
            logger.warning("Meta Andromeda scoring provider failed: %s", exc, exc_info=True)
            if not settings.META_ANDROMEDA_SCORING_ALLOW_FALLBACK:
                raise
            fallback_entry = model_registry.get_entry("candidate_v0")
            err_detail = str(exc).replace("\n", " ")
            return build_heuristic_score_result(
                score_payload,
                fallback_entry,
                fallback_reason=f"{provider_name}:{type(exc).__name__} ({err_detail[:120]})",
            )


runtime_adapter = MetaAndromedaRuntimeAdapter()
