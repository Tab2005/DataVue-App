"""
Meta Andromeda - OpenRouter model catalog lookup

給版本總覽/監控頁「換模型前先查」用：查詢一個候選 model id 是否真的存在於
OpenRouter、是否支援評分需要的圖片輸入、實際 serving 端點的 context 上限多大——
避免重演 2026-07-10 的事故（`llama-nemotron-embed-vl-1b-v2:free` 這種根本不存在
或型別不對的模型 id 被設進 env var，一直到跑評分才炸出 400）。

`GET /api/v1/models` 是 OpenRouter 的公開端點，不需要 API Key。
"""

import logging
import time

import httpx

logger = logging.getLogger(__name__)

_CATALOG_CACHE_TTL_SECONDS = 3600.0
_catalog_cache: dict[str, dict] | None = None
_catalog_cache_time: float = 0.0

# 評分請求會送圖片/影片截幀，模型的 input_modalities 沒有 "image" 就直接不適用
_REQUIRED_INPUT_MODALITY = "image"
# 目前評分請求固定要求的輸出上限（見 runtime.py::_DEFAULT_SCORE_MAX_TOKENS），
# 端點的 max_completion_tokens 比這個小，第一次請求就必然失敗
_MIN_RECOMMENDED_MAX_COMPLETION_TOKENS = 8192
# context 太窄的模型即使第一次僥倖過關，稍微長一點的素材/few-shot 就會炸，
# 這個門檻只是提醒，不會擋掉查詢結果
_MIN_RECOMMENDED_CONTEXT_LENGTH = 20000


def _fetch_catalog(force_refresh: bool = False) -> dict[str, dict]:
    """回傳 {model_id: raw_entry} 的完整 OpenRouter 模型目錄（含所有 provider 前綴，
    不像 OpenRouterClient.fetch_remote_models() 那樣過濾成只剩幾家主流廠商——
    Meta Andromeda 用的是 nvidia/ 系列，會被那個過濾器整個濾掉）。"""
    global _catalog_cache, _catalog_cache_time
    now = time.time()
    if not force_refresh and _catalog_cache is not None and (now - _catalog_cache_time < _CATALOG_CACHE_TTL_SECONDS):
        return _catalog_cache

    with httpx.Client(timeout=10.0) as client:
        response = client.get("https://openrouter.ai/api/v1/models")
        response.raise_for_status()
        data = response.json()

    catalog = {m["id"]: m for m in data.get("data", []) if m.get("id")}
    _catalog_cache = catalog
    _catalog_cache_time = now
    return catalog


def validate_candidate_model(model_id: str) -> dict:
    """查詢一個候選 model id，回傳查完就能直接判斷「能不能設」的結構化結果。"""
    model_id = (model_id or "").strip()
    if not model_id:
        return {
            "model_id": model_id,
            "exists": False,
            "ok": False,
            "issues": ["模型 ID 為空"],
            "name": None,
            "supports_image_input": None,
            "context_length": None,
            "max_completion_tokens": None,
            "is_free": None,
        }

    try:
        catalog = _fetch_catalog()
    except Exception as exc:
        logger.warning("[MetaAndromeda] Failed to fetch OpenRouter model catalog: %s", exc)
        return {
            "model_id": model_id,
            "exists": None,
            "ok": False,
            "issues": [f"查詢 OpenRouter 模型目錄失敗：{exc}"],
            "name": None,
            "supports_image_input": None,
            "context_length": None,
            "max_completion_tokens": None,
            "is_free": None,
        }

    entry = catalog.get(model_id)
    if entry is None:
        return {
            "model_id": model_id,
            "exists": False,
            "ok": False,
            "issues": ["這個模型 ID 在 OpenRouter 目錄裡查無資料——可能是打錯字、已下架，或根本不是可用的模型 ID"],
            "name": None,
            "supports_image_input": None,
            "context_length": None,
            "max_completion_tokens": None,
            "is_free": None,
        }

    architecture = entry.get("architecture") or {}
    input_modalities = architecture.get("input_modalities") or []
    supports_image_input = _REQUIRED_INPUT_MODALITY in input_modalities

    top_provider = entry.get("top_provider") or {}
    # top_provider 的欄位才是實際 serving 端點的真實上限，跟頂層 context_length
    # （型號名義上的規格）可能不一致——2026-07-10 那次事故的根因就是只看名字沒查這個
    context_length = top_provider.get("context_length") or entry.get("context_length")
    max_completion_tokens = top_provider.get("max_completion_tokens")

    pricing = entry.get("pricing") or {}
    is_free = pricing.get("prompt") == "0" and pricing.get("completion") == "0"

    issues: list[str] = []
    if not supports_image_input:
        issues.append(
            f"這個模型不支援圖片輸入（input_modalities={input_modalities or '未知'}）——"
            "Meta Andromeda 評分會送素材圖片/影片截幀，這個模型收到會被忽略或直接報錯"
        )
    if context_length is not None and context_length < _MIN_RECOMMENDED_CONTEXT_LENGTH:
        issues.append(
            f"這個模型（端點）context 上限只有 {context_length} tokens，偏窄——"
            "碰到較長的 prompt/few-shot 範例時可能會超出上限而報錯"
        )
    if max_completion_tokens is not None and max_completion_tokens < _MIN_RECOMMENDED_MAX_COMPLETION_TOKENS:
        issues.append(
            f"這個模型（端點）輸出上限只有 {max_completion_tokens} tokens，"
            f"低於評分請求預設要求的 {_MIN_RECOMMENDED_MAX_COMPLETION_TOKENS} tokens——"
            "第一次請求大機率會直接被拒（會自動重試降低輸出上限，但成功率視素材長度而定）"
        )

    return {
        "model_id": model_id,
        "exists": True,
        "ok": not issues,
        "issues": issues,
        "name": entry.get("name"),
        "supports_image_input": supports_image_input,
        "context_length": context_length,
        "max_completion_tokens": max_completion_tokens,
        "is_free": is_free,
    }
