"""
Meta Andromeda model registry
"""

import logging
import os
import threading
import time
from dataclasses import dataclass

from core.config import settings
from .cache_invalidation import publish_invalidation, register_invalidation_handler

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MetaAndromedaModelEntry:
    model_version: str
    provider: str
    provider_model: str
    scoring_profile: str
    feature_manifest_id: str
    release_channel: str
    source_of_truth: str


# 硬編碼清單保留為 DB 不可用時的最後備援（defense in depth），不再是唯一真相來源；
# 正常路徑讀 meta_andromeda_model_registry_entries 表（見 20260703_meta_andromeda_p2_wave3 migration 種子）
_HARDCODED_ENTRIES: dict[str, MetaAndromedaModelEntry] = {
    "prod_v2026_05_28": MetaAndromedaModelEntry(
        model_version="prod_v2026_05_28",
        provider="openrouter",
        provider_model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        scoring_profile="creative_scoring_v1",
        feature_manifest_id="fm_prod_20260528",
        release_channel="production",
        source_of_truth="datavue.meta_andromeda.registry",
    ),
    "prod_v2026_05_12": MetaAndromedaModelEntry(
        model_version="prod_v2026_05_12",
        provider="heuristic",
        provider_model="heuristic://creative_scoring_v0",
        scoring_profile="creative_scoring_v0",
        feature_manifest_id="fm_prod_20260512",
        release_channel="superseded",
        source_of_truth="datavue.meta_andromeda.registry",
    ),
    "cand_v2026_06_05_a": MetaAndromedaModelEntry(
        model_version="cand_v2026_06_05_a",
        provider="openrouter",
        provider_model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        scoring_profile="creative_scoring_v2",
        feature_manifest_id="fm_cand_20260605_a",
        release_channel="candidate",
        source_of_truth="datavue.meta_andromeda.registry",
    ),
    "cand_v2026_06_04_b": MetaAndromedaModelEntry(
        model_version="cand_v2026_06_04_b",
        provider="openrouter",
        provider_model="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
        scoring_profile="creative_scoring_v1",
        feature_manifest_id="fm_cand_20260604_b",
        release_channel="candidate",
        source_of_truth="datavue.meta_andromeda.registry",
    ),
    "candidate_v0": MetaAndromedaModelEntry(
        model_version="candidate_v0",
        provider="heuristic",
        provider_model="heuristic://creative_scoring_v0",
        scoring_profile="creative_scoring_v0",
        feature_manifest_id="fm_candidate_v0",
        release_channel="local_fallback",
        source_of_truth="datavue.meta_andromeda.registry",
    ),
}
_HARDCODED_DEFAULT_VERSION = "cand_v2026_06_05_a"

_REGISTRY_CACHE_TTL_SECONDS = 300

_registry_cache: dict[str, MetaAndromedaModelEntry] = {}
_current_production_cache: str | None = None
_cache_populated = False
_cache_populated_at: float = 0.0
_cache_lock = threading.Lock()


def _row_to_entry(row) -> MetaAndromedaModelEntry:
    return MetaAndromedaModelEntry(
        model_version=row.model_version,
        provider=row.provider,
        provider_model=row.provider_model,
        scoring_profile=row.scoring_profile,
        feature_manifest_id=row.feature_manifest_id,
        release_channel=row.release_channel,
        source_of_truth=row.source_of_truth,
    )


def _load_registry_from_db() -> tuple[dict[str, MetaAndromedaModelEntry], str | None]:
    from database import SessionLocal
    from database.models.meta_andromeda import MetaAndromedaModelRegistryEntry

    db = SessionLocal()
    try:
        rows = db.query(MetaAndromedaModelRegistryEntry).all()
        entries = {row.model_version: _row_to_entry(row) for row in rows}
        current = next((row.model_version for row in rows if row.is_current_production), None)
        return entries, current
    finally:
        db.close()


def _get_cached_registry() -> tuple[dict[str, MetaAndromedaModelEntry], str | None]:
    global _cache_populated, _current_production_cache, _cache_populated_at
    with _cache_lock:
        if _cache_populated and (time.monotonic() - _cache_populated_at) < _REGISTRY_CACHE_TTL_SECONDS:
            return _registry_cache, _current_production_cache

    try:
        entries, current = _load_registry_from_db()
    except Exception as exc:
        logger.warning("[MetaAndromeda] Could not load model registry from DB: %s. Using hardcoded fallback.", exc)
        entries, current = {}, None

    with _cache_lock:
        if entries:
            _registry_cache.clear()
            _registry_cache.update(entries)
            _current_production_cache = current
        _cache_populated = True
        _cache_populated_at = time.monotonic()
        return _registry_cache, _current_production_cache


def _invalidate_registry_cache_local(_scope_key: str | None = None) -> None:
    global _cache_populated
    with _cache_lock:
        _cache_populated = False
        _registry_cache.clear()


def invalidate_registry_cache() -> None:
    """Call after any write to meta_andromeda_model_registry_entries (approve/rollback)
    so the next get_entry() re-reads the DB instead of serving a stale
    current_production — and notify sibling workers via Redis pub/sub (P2-7)
    so a multi-worker deployment doesn't keep scoring on the old model."""
    publish_invalidation("model_registry", None)


register_invalidation_handler("model_registry", _invalidate_registry_cache_local)


class MetaAndromedaModelRegistry:
    def get_entry(self, model_version: str | None = None, *, purpose: str = "interactive") -> MetaAndromedaModelEntry:
        """purpose="interactive" (default): normal Score Lab / observation scoring,
        picks the DB current_production entry — should be fast/cheap.
        purpose="backtest": holdout backtest / calibration re-scoring, prefers a
        registry entry tagged release_channel="backtest_reference" (a deliberately
        stronger/more expensive model an operator can configure) so ρ/accuracy
        comparisons aren't bottlenecked by the cheap interactive model's ceiling;
        falls back to current_production if no such entry exists (docs/20 P2-3).
        """
        entries, current_production = _get_cached_registry()
        # DB 表尚未 migrate 或完全讀不到資料時退回硬編碼清單，確保評分服務不因此中斷
        if not entries:
            entries = _HARDCODED_ENTRIES
            current_production = None

        if model_version:
            configured_version = model_version
        elif purpose == "backtest" and (backtest_entry := next(
            (e for e in entries.values() if e.release_channel == "backtest_reference"), None
        )):
            configured_version = backtest_entry.model_version
        else:
            # env 覆寫保留為 ops escape hatch：只有「明確設定」時才生效（os.getenv 無 default，
            # 與 core.config.settings 的隱含預設值區分開），否則一律看 DB 的 current_production
            env_override = os.getenv("META_ANDROMEDA_SCORING_MODEL_VERSION")
            if env_override:
                configured_version = env_override
            elif current_production:
                configured_version = current_production
            else:
                configured_version = settings.META_ANDROMEDA_SCORING_MODEL_VERSION

        entry = entries.get(configured_version)
        if entry is None:
            entry = entries.get(_HARDCODED_DEFAULT_VERSION) or _HARDCODED_ENTRIES[_HARDCODED_DEFAULT_VERSION]

        provider_override = settings.META_ANDROMEDA_SCORING_PROVIDER
        # 這個 env var 預設就非空（見 core/config.py 的預設值），等於「一律生效」的 ops escape
        # hatch——但那是為了讓「互動評分」不受 DB 影響、可用 env 快速鎖定模型；回測要用的正是
        # 「跟互動評分不同的模型」，若這裡不排除 purpose="backtest"，這個 hatch 會直接蓋掉
        # backtest_reference entry 解析出的 provider_model，讓「回測專用模型」設定形同虛設。
        model_override = settings.META_ANDROMEDA_SCORING_MODEL if purpose != "backtest" else None

        if provider_override == "heuristic":
            return MetaAndromedaModelEntry(
                model_version="candidate_v0",
                provider="heuristic",
                provider_model="heuristic://creative_scoring_v0",
                scoring_profile="creative_scoring_v0",
                feature_manifest_id="fm_candidate_v0",
                release_channel="local_fallback",
                source_of_truth=entry.source_of_truth,
            )

        if provider_override == "openrouter" and model_override:
            return MetaAndromedaModelEntry(
                model_version=entry.model_version,
                provider="openrouter",
                provider_model=model_override,
                scoring_profile=entry.scoring_profile,
                feature_manifest_id=entry.feature_manifest_id,
                release_channel=entry.release_channel,
                source_of_truth=entry.source_of_truth,
            )

        if provider_override == "auto" and model_override and entry.provider == "openrouter":
            return MetaAndromedaModelEntry(
                model_version=entry.model_version,
                provider=entry.provider,
                provider_model=model_override,
                scoring_profile=entry.scoring_profile,
                feature_manifest_id=entry.feature_manifest_id,
                release_channel=entry.release_channel,
                source_of_truth=entry.source_of_truth,
            )

        return entry

    def list_registry_notes(self, model_versions: list[str]) -> list[str]:
        entries, _ = _get_cached_registry()
        if not entries:
            entries = _HARDCODED_ENTRIES
        notes = []
        for model_version in model_versions:
            entry = entries.get(model_version)
            if entry is None:
                continue
            notes.append(
                f"{entry.model_version}: {entry.provider} -> {entry.provider_model} [{entry.release_channel}]"
            )
        return notes


model_registry = MetaAndromedaModelRegistry()
