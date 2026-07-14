"""ProfileRegistry repository operations."""

from ._shared import *  # noqa: F401,F403
from ._stats import *  # noqa: F401,F403
from .release_metrics import *  # noqa: F401,F403
from .release import PromotionGateError

class ProfileRegistryMixin:
    @staticmethod
    def get_active_base_profile_name(db: Session) -> str:
        """Resolve the scoring-profile name currently used by the runtime.

        This is a profile_name in meta_andromeda_scoring_profiles, NOT a
        model_version from the model registry — the two are different
        namespaces (e.g. "creative_scoring_v2" vs "cand_v2026_06_05_a").
        Mirrors runtime._load_scoring_profile()'s own precedence: the
        globally promoted profile wins, otherwise fall back to the
        registry's configured scoring_profile.
        """
        promoted = (
            db.query(MetaAndromedaScoringProfile)
            .filter(MetaAndromedaScoringProfile.is_promoted == True)  # noqa: E712
            .first()
        )
        if promoted is not None:
            return promoted.profile_name
        return model_registry.get_entry().scoring_profile

    @staticmethod
    def list_scoring_profiles(db: Session) -> list[dict]:
        rows = (
            db.query(MetaAndromedaScoringProfile)
            .order_by(MetaAndromedaScoringProfile.created_at.desc())
            .all()
        )
        return [
            {
                "profile_name": r.profile_name,
                "source": r.source,
                "base_profile_name": r.base_profile_name,
                "calibration_dataset_id": r.calibration_dataset_id,
                "is_promoted": r.is_promoted,
                "promoted_at": r.promoted_at.isoformat() if r.promoted_at else None,
                "bias_summary": r.bias_summary,
                "calibration_guidance": r.calibration_guidance,
                "few_shot_example_count": len(r.few_shot_examples or []),
                "objective_profiles": r.objective_profiles or {},
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    @staticmethod
    def promote_scoring_profile(db: Session, profile_name: str, force: bool = False) -> dict:
        target = db.query(MetaAndromedaScoringProfile).filter(
            MetaAndromedaScoringProfile.profile_name == profile_name
        ).first()
        if target is None:
            raise KeyError(f"Scoring profile not found: {profile_name}")

        # 自動校準產出的 profile 一律要先過 holdout 回測 gate 才能 promote；手動/種子 profile
        # 沒有校準資料集可回測，維持原本行為。force=True 可明確覆寫（供緊急情況使用）。
        backtest_gate_bypassed = False
        if target.source == "calibration_auto" and not force:
            backtest = (target.bias_summary or {}).get("holdout_backtest")
            if not backtest or backtest.get("status") != "evaluated":
                raise PromotionGateError(
                    "holdout_backtest_required",
                    f"Profile '{profile_name}' 尚未執行 holdout 回測，請先呼叫 backtest 端點，"
                    "或帶 force=true 明確略過（不建議）。",
                )
            if not backtest.get("passed_gate"):
                raise PromotionGateError(
                    "holdout_backtest_failed",
                    f"Profile '{profile_name}' 回測未達標：accuracy {backtest.get('baseline_accuracy')} -> "
                    f"{backtest.get('candidate_accuracy')}（Δ={backtest.get('accuracy_delta')}），"
                    f"spearman {backtest.get('baseline_spearman')} -> {backtest.get('candidate_spearman')}"
                    f"（Δ={backtest.get('spearman_delta')}）。可帶 force=true 明確覆寫（不建議）。",
                )
        elif target.source == "calibration_auto" and force:
            backtest_gate_bypassed = True

        db.query(MetaAndromedaScoringProfile).filter(
            MetaAndromedaScoringProfile.is_promoted == True  # noqa: E712
        ).update({"is_promoted": False, "promoted_at": None}, synchronize_session=False)

        now = datetime.now(timezone.utc)
        target.is_promoted = True
        target.promoted_at = now
        target.consecutive_degraded_periods = 0
        target.demoted_at = None
        target.demoted_reason = None

        # 記錄 promote 前基線，供 create_drift_report 在之後每期自動比對是否劣化
        backtest = (target.bias_summary or {}).get("holdout_backtest")
        if backtest and backtest.get("status") == "evaluated":
            target.promotion_baseline = {
                "accuracy": backtest.get("baseline_accuracy"),
                "spearman_r": backtest.get("baseline_spearman"),
                "source": "holdout_backtest",
                "recorded_at": now.isoformat(),
            }

        db.add(target)
        db.commit()

        from ..runtime import invalidate_prompt_cache
        invalidate_prompt_cache()  # clear all so next scoring re-queries the promoted profile

        return {
            "profile_name": target.profile_name,
            "is_promoted": True,
            "promoted_at": now.isoformat(),
            "backtest_gate_bypassed": backtest_gate_bypassed,
        }

    @staticmethod
    def list_model_registry_entries(db: Session) -> list[dict]:
        rows = (
            db.query(MetaAndromedaModelRegistryEntry)
            .order_by(MetaAndromedaModelRegistryEntry.created_at.desc())
            .all()
        )
        return [
            {
                "model_version": r.model_version,
                "provider": r.provider,
                "provider_model": r.provider_model,
                "scoring_profile": r.scoring_profile,
                "release_channel": r.release_channel,
                "is_current_production": r.is_current_production,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    @staticmethod
    def get_effective_scoring_status(db: Session) -> dict:
        """比較「目前實際生效的互動評分設定」與「資料庫 registry 表裡標記為
        production 的那一列」，供監控頁面標示兩者是否一致。

        背景：`model_registry.get_entry()` 的 env override（`META_ANDROMEDA_
        SCORING_PROVIDER` / `_MODEL` / `_MODEL_VERSION`）完全不寫資料庫，只在
        記憶體裡即時生效——只看版本總覽/監控總覽畫面（讀的是 DB 表）的人會
        誤以為「換了環境變數但畫面沒變，是不是沒生效」。用直接比對兩邊實際
        解析出的值（而非重複 get_entry() 內部的 if/elif 分支條件）來判斷是否
        有覆寫，可以不用跟著 get_entry() 的覆寫邏輯同步維護、更不容易漏改。
        """
        resolved = model_registry.get_entry()  # purpose="interactive"：實際評分請求會用的設定

        db_production = (
            db.query(MetaAndromedaModelRegistryEntry)
            .filter(MetaAndromedaModelRegistryEntry.is_current_production == True)  # noqa: E712
            .first()
        )

        is_overridden = (
            db_production is None
            or resolved.provider != db_production.provider
            or resolved.provider_model != db_production.provider_model
            or resolved.model_version != db_production.model_version
        )

        return {
            "resolved_model_version": resolved.model_version,
            "resolved_provider": resolved.provider,
            "resolved_provider_model": resolved.provider_model,
            "resolved_scoring_profile": resolved.scoring_profile,
            "resolved_release_channel": resolved.release_channel,
            "db_production_model_version": db_production.model_version if db_production else None,
            "db_production_provider": db_production.provider if db_production else None,
            "db_production_provider_model": db_production.provider_model if db_production else None,
            "is_overridden": is_overridden,
            "scoring_provider_setting": settings.META_ANDROMEDA_SCORING_PROVIDER,
            # 顯示 os.getenv 的原始值（無 default），跟 model_registry.get_entry() 判斷
            # 「是否明確覆寫」用的是同一個值——否則沒設 env var 時這裡會顯示 config.py 的
            # 隱含預設值，讓人誤以為那是造成 is_overridden 的原因。
            "scoring_model_setting": os.getenv("META_ANDROMEDA_SCORING_MODEL", ""),
            "scoring_model_version_env_set": bool(os.getenv("META_ANDROMEDA_SCORING_MODEL_VERSION")),
        }

    @staticmethod
    def set_backtest_reference_model(db: Session, provider: str, provider_model: str) -> dict:
        """Upsert the single registry row tagged release_channel='backtest_reference' —
        the model evaluate_profile_on_holdout uses instead of falling back to
        current_production (docs/20 P2-3). Scoring/interactive model selection is
        intentionally NOT exposed here — it stays gated behind the release
        approve/rollback workflow (drift + backtest checks) so this can't create a
        second, conflicting way to change what's live for real users."""
        entry = (
            db.query(MetaAndromedaModelRegistryEntry)
            .filter(MetaAndromedaModelRegistryEntry.release_channel == "backtest_reference")
            .first()
        )
        current_production = (
            db.query(MetaAndromedaModelRegistryEntry)
            .filter(MetaAndromedaModelRegistryEntry.is_current_production == True)  # noqa: E712
            .first()
        )
        scoring_profile = current_production.scoring_profile if current_production else "creative_scoring_v2"

        if entry:
            entry.provider = provider
            entry.provider_model = provider_model
            entry.scoring_profile = scoring_profile
        else:
            entry = MetaAndromedaModelRegistryEntry(
                model_version="backtest_reference_model",
                provider=provider,
                provider_model=provider_model,
                scoring_profile=scoring_profile,
                feature_manifest_id="fm_backtest_reference",
                release_channel="backtest_reference",
                source_of_truth="datavue.meta_andromeda.registry",
                is_current_production=False,
            )
            db.add(entry)
        db.commit()
        return {
            "model_version": entry.model_version,
            "provider": entry.provider,
            "provider_model": entry.provider_model,
            "scoring_profile": entry.scoring_profile,
            "release_channel": entry.release_channel,
            "is_current_production": entry.is_current_production,
        }
