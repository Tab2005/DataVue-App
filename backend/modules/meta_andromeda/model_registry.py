"""
Meta Andromeda model registry
"""

from dataclasses import dataclass

from core.config import settings


@dataclass(frozen=True)
class MetaAndromedaModelEntry:
    model_version: str
    provider: str
    provider_model: str
    scoring_profile: str
    feature_manifest_id: str
    release_channel: str
    source_of_truth: str


class MetaAndromedaModelRegistry:
    def __init__(self) -> None:
        self._entries = {
            "prod_v2026_05_28": MetaAndromedaModelEntry(
                model_version="prod_v2026_05_28",
                provider="openrouter",
                provider_model="deepseek/deepseek-v4-flash",
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
                provider_model="deepseek/deepseek-v4-flash",
                scoring_profile="creative_scoring_v2",
                feature_manifest_id="fm_cand_20260605_a",
                release_channel="candidate",
                source_of_truth="datavue.meta_andromeda.registry",
            ),
            "cand_v2026_06_04_b": MetaAndromedaModelEntry(
                model_version="cand_v2026_06_04_b",
                provider="openrouter",
                provider_model="deepseek/deepseek-v4-flash",
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

    def get_entry(self, model_version: str | None = None) -> MetaAndromedaModelEntry:
        configured_version = model_version or settings.META_ANDROMEDA_SCORING_MODEL_VERSION
        entry = self._entries.get(configured_version)
        if entry is None:
            entry = self._entries["cand_v2026_06_05_a"]

        provider_override = settings.META_ANDROMEDA_SCORING_PROVIDER
        model_override = settings.META_ANDROMEDA_SCORING_MODEL

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
        notes = []
        for model_version in model_versions:
            entry = self._entries.get(model_version)
            if entry is None:
                continue
            notes.append(
                f"{entry.model_version}: {entry.provider} -> {entry.provider_model} [{entry.release_channel}]"
            )
        return notes


model_registry = MetaAndromedaModelRegistry()
