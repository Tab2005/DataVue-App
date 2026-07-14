"""Release repository operations."""

from ._shared import *  # noqa: F401,F403
from ._stats import *  # noqa: F401,F403
from .release_metrics import *  # noqa: F401,F403


class PromotionGateError(Exception):
    """Raised when a scoring profile promotion does not pass its gate."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class ReleaseCandidateExistsError(Exception):
    pass


def _switch_model_registry_production(db, model_version: str) -> None:
    """Flip is_current_production in the DB-backed model registry so runtime's
    model_registry.get_entry() actually starts using the newly approved/rolled-back
    model_version — the missing link that made Release approve/rollback a no-op
    on scoring behavior before (docs/19 P0-6)."""
    from database.models.meta_andromeda import MetaAndromedaModelRegistryEntry

    target = (
        db.query(MetaAndromedaModelRegistryEntry)
        .filter(MetaAndromedaModelRegistryEntry.model_version == model_version)
        .first()
    )
    if target is None:
        logger.warning(
            "[MetaAndromeda] Release action referenced model_version '%s' with no matching "
            "model_registry_entries row — runtime will keep using whatever is currently "
            "is_current_production until a registry entry for this version is added.",
            model_version,
        )
        return

    db.query(MetaAndromedaModelRegistryEntry).filter(
        MetaAndromedaModelRegistryEntry.is_current_production == True  # noqa: E712
    ).update({"is_current_production": False}, synchronize_session=False)
    target.is_current_production = True
    db.add(target)
    db.commit()

    from ..model_registry import invalidate_registry_cache
    invalidate_registry_cache()

class ReleaseMixin:
    @staticmethod
    def _backtest_run_to_dict(run: MetaAndromedaBacktestRun) -> dict:
        return {
            "run_id": run.id,
            "provider": run.provider,
            "provider_model": run.provider_model,
            "status": run.status,
            "note": run.note,
            "sample_limit": run.sample_limit,
            "total_count": run.total_count,
            "processed_count": run.processed_count,
            "success_count": run.success_count,
            "failed_count": run.failed_count,
            "sample_count": run.sample_count,
            "pairwise_ranking_accuracy": run.pairwise_ranking_accuracy,
            "mean_band_error": run.mean_band_error,
            "error_message": run.error_message,
            "result_summary": deepcopy(run.result_summary or {}),
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        }

    def get_release_overview(self, db: Session):
        # 若資料表為空，主動執行一次種子數據播種
        if db.query(MetaAndromedaReleaseRecord).count() == 0:
            try:
                self.ensure_seed_data(db)
            except Exception as e:
                logger.error("[MetaAndromeda] Auto-seeding on release overview request failed: %s", e)

        records = db.query(MetaAndromedaReleaseRecord).all()
        
        # 安全獲取 record，避免 StopIteration 導致 500 錯誤
        current = next((item for item in records if item.record_kind == "current_production"), None)
        previous = next((item for item in records if item.record_kind == "previous_production"), None)
        candidates = [item for item in records if item.record_kind == "candidate"]
        history = db.query(MetaAndromedaReleaseEvent).order_by(MetaAndromedaReleaseEvent.created_at.desc()).all()
        latest_calibration = (
            db.query(MetaAndromedaCalibrationDataset)
            .order_by(MetaAndromedaCalibrationDataset.created_at.desc())
            .first()
        )
        
        # 回傳 dict 封裝與預設備用 fallback
        current_dict = self._release_record_to_dict(current) if current else {
            "model_version": "prod_v2026_05_28",
            "release_status": "production",
            "approved_by": "system",
            "approved_at": "",
            "pairwise_ranking_accuracy": 0.85,
            "mean_band_error": 0.15,
            "is_demo_data": True,
        }
        previous_dict = self._release_record_to_dict(previous) if previous else {
            "model_version": "prod_v2026_05_12",
            "release_status": "archived",
            "approved_by": "system",
            "approved_at": "",
            "pairwise_ranking_accuracy": 0.82,
            "mean_band_error": 0.18,
            "is_demo_data": True,
        }

        current_is_demo = bool(current_dict.get("is_demo_data", True))
        return {
            "current_production": current_dict,
            "previous_production": previous_dict,
            "candidates": [self._release_record_to_dict(item) for item in candidates],
            "history": [self._release_event_to_dict(item) for item in history],
            "data_source": "seed_demo" if current_is_demo else "computed",
            "is_demo_data": current_is_demo,
            "notes": [
                (
                    "⚠️ pairwise_ranking_accuracy / mean_band_error 目前為示範資料（seed），尚未呼叫過 "
                    "POST /release/{model_version}/refresh-metrics 從 drift report 實際配對結果計算。"
                    if current_is_demo else
                    "✅ pairwise_ranking_accuracy / mean_band_error 已從 drift report 實際配對結果計算。"
                ),
                "Release actions now persist to DataVue DB and switch the DB-backed model registry's "
                "is_current_production, so approve/rollback now actually changes which model runtime uses.",
                "Release metadata is now aligned with the Meta Andromeda registry source of truth.",
                (
                    f"Latest calibration dataset: {latest_calibration.id} "
                    f"({latest_calibration.synced_count} items, policy {latest_calibration.label_policy_version})"
                    if latest_calibration
                    else "No calibration dataset has been materialized yet."
                ),
                *model_registry.list_registry_notes(
                    [current_dict["model_version"], previous_dict["model_version"], *[item.model_version for item in candidates]]
                ),
            ],
        }

    @staticmethod
    def _release_record_to_dict(record: MetaAndromedaReleaseRecord) -> dict:
        payload = {
            "model_version": record.model_version,
            "release_status": record.release_status,
            "approved_by": record.approved_by or "",
            "approved_at": record.approved_at or "",
            "pairwise_ranking_accuracy": record.pairwise_ranking_accuracy,
            "mean_band_error": record.mean_band_error,
            # metrics_source=="computed" 代表已用 refresh_release_metrics()（drift-matched pairs）
            # 實算過；否則仍是 seed/手動輸入，不代表真實模型表現（見 docs/19 P0-6）
            "is_demo_data": getattr(record, "metrics_source", "seed") != "computed",
        }
        if record.record_kind == "candidate":
            payload["created_at"] = record.created_at
            payload["promotion_gate_summary"] = deepcopy(record.promotion_gate_summary or {})
        return payload

    @staticmethod
    def _release_event_to_dict(event: MetaAndromedaReleaseEvent) -> dict:
        note = event.note or ""
        forced = note.startswith(RELEASE_FORCE_NOTE_PREFIX)
        if forced:
            note = note[len(RELEASE_FORCE_NOTE_PREFIX):].strip()
        return {
            "action": event.action,
            "model_version": event.model_version,
            "actor": event.actor,
            "created_at": event.created_at,
            "note": note,
            "forced": forced,
        }

    def create_release_candidate(
        self,
        db: Session,
        *,
        model_version: str,
        provider: str,
        provider_model: str,
        scoring_profile: str | None,
        actor: str,
        note: str | None,
    ) -> dict:
        """建立一筆新的候選版本（release_status="candidate"），讓 approve/rollback
        流程不再被種子資料鎖死——過去唯一能建立 candidate 的地方是一次性的
        `SEED_RELEASE_RECORDS`（只在表為空時執行一次），沒有 API 能新增候選，
        這是「正式評分模型無法像回測模型一樣自由切換」的根本原因（approve
        本身其實沒有強制的 backtest gate，只要求 model_version 對應的
        candidate record 存在）。

        同時 upsert 對應的 `MetaAndromedaModelRegistryEntry`（release_channel=
        "candidate"）——approve 時 `_switch_model_registry_production()` 是靠
        model_version 去查這張表，若只建立 release record 而沒有對應的
        registry entry，approve 會靜默失敗（只記 warning，`is_current_production`
        不會真的切換），所以兩者必須一起建立才能保證 approve 真的生效。

        `model_version` 不可與現有 registry entry 重複（避免誤蓋掉正式/回測
        用的既有設定）；`scoring_profile` 留空時沿用目前 production 的設定，
        讓操作者只想換模型時不必連帶處理 prompt/校準邏輯。
        """
        existing_entry = (
            db.query(MetaAndromedaModelRegistryEntry)
            .filter(MetaAndromedaModelRegistryEntry.model_version == model_version)
            .first()
        )
        if existing_entry is not None:
            raise ReleaseCandidateExistsError(
                f"model_version '{model_version}' 已存在於 model registry"
                f"（release_channel={existing_entry.release_channel}），請換一個名稱"
            )
        existing_record = (
            db.query(MetaAndromedaReleaseRecord)
            .filter(MetaAndromedaReleaseRecord.model_version == model_version)
            .first()
        )
        if existing_record is not None:
            raise ReleaseCandidateExistsError(
                f"model_version '{model_version}' 已存在一筆 release record"
                f"（record_kind={existing_record.record_kind}），請換一個名稱"
            )

        current_production = (
            db.query(MetaAndromedaModelRegistryEntry)
            .filter(MetaAndromedaModelRegistryEntry.is_current_production == True)  # noqa: E712
            .first()
        )
        resolved_scoring_profile = (
            scoring_profile
            or (current_production.scoring_profile if current_production else "creative_scoring_v2")
        )

        now = datetime.now(timezone.utc)
        db.add(
            MetaAndromedaModelRegistryEntry(
                model_version=model_version,
                provider=provider,
                provider_model=provider_model,
                scoring_profile=resolved_scoring_profile,
                feature_manifest_id=f"fm_cand_{now.strftime('%Y%m%d%H%M%S')}",
                release_channel="candidate",
                source_of_truth="datavue.meta_andromeda.registry",
                is_current_production=False,
            )
        )
        db.add(
            MetaAndromedaReleaseRecord(
                record_kind="candidate",
                model_version=model_version,
                release_status="candidate",
                approved_by=None,
                approved_at=None,
                created_at=now.isoformat(),
                pairwise_ranking_accuracy=0.0,
                mean_band_error=0.0,
                promotion_gate_summary=None,
                metrics_source="seed",
                metrics_sample_count=None,
            )
        )
        db.add(
            MetaAndromedaReleaseEvent(
                action="create_candidate",
                model_version=model_version,
                actor=actor,
                note=note,
                created_at=now.isoformat(),
            )
        )
        db.commit()

        from ..model_registry import invalidate_registry_cache
        invalidate_registry_cache()

        return {
            "model_version": model_version,
            "release_status": "candidate",
            "created_at": now.isoformat(),
            "pairwise_ranking_accuracy": 0.0,
            "mean_band_error": 0.0,
            "promotion_gate_summary": {},
            "is_demo_data": True,
        }

    def perform_release_action(self, db: Session, action: str, model_version: str, actor: str, note: str | None, force: bool = False):
        current = db.query(MetaAndromedaReleaseRecord).filter(MetaAndromedaReleaseRecord.record_kind == "current_production").first()
        previous = db.query(MetaAndromedaReleaseRecord).filter(MetaAndromedaReleaseRecord.record_kind == "previous_production").first()
        candidate = (
            db.query(MetaAndromedaReleaseRecord)
            .filter(
                MetaAndromedaReleaseRecord.record_kind == "candidate",
                MetaAndromedaReleaseRecord.model_version == model_version,
            )
            .first()
        )

        created_at = datetime.now(timezone.utc).isoformat()
        if action in {"approve", "reject"} and candidate is None:
            raise KeyError(model_version)

        gate_payload = {"forced": False}
        if action == "approve":
            gate_payload = _assert_release_gate(candidate, force=force, note=note)
            previous.model_version = current.model_version
            previous.release_status = "superseded"
            previous.approved_by = current.approved_by
            previous.approved_at = current.approved_at
            previous.created_at = current.created_at
            previous.pairwise_ranking_accuracy = current.pairwise_ranking_accuracy
            previous.mean_band_error = current.mean_band_error
            previous.metrics_source = current.metrics_source
            previous.metrics_sample_count = current.metrics_sample_count

            current.model_version = candidate.model_version
            current.release_status = "production"
            current.approved_by = actor
            current.approved_at = created_at
            current.created_at = created_at
            current.pairwise_ranking_accuracy = candidate.pairwise_ranking_accuracy
            current.mean_band_error = candidate.mean_band_error
            current.metrics_source = candidate.metrics_source
            current.metrics_sample_count = candidate.metrics_sample_count
            candidate.release_status = "approved"

            # Runtime 真正切換：把新 current_production 的 model_version 標記為 DB registry 的
            # is_current_production，下一次 model_registry.get_entry() 就會用它（P0-6 完整版核心）
            _switch_model_registry_production(db, current.model_version)
        elif action == "reject":
            candidate.release_status = "rejected"
        elif action == "rollback":
            current_snapshot = {
                "model_version": current.model_version,
                "approved_by": current.approved_by,
                "approved_at": current.approved_at,
                "created_at": current.created_at,
                "pairwise_ranking_accuracy": current.pairwise_ranking_accuracy,
                "mean_band_error": current.mean_band_error,
                "metrics_source": current.metrics_source,
                "metrics_sample_count": current.metrics_sample_count,
            }
            current.model_version = previous.model_version
            current.release_status = "production"
            current.approved_by = actor
            current.approved_at = created_at
            current.created_at = created_at
            current.pairwise_ranking_accuracy = previous.pairwise_ranking_accuracy
            current.mean_band_error = previous.mean_band_error
            current.metrics_source = previous.metrics_source
            current.metrics_sample_count = previous.metrics_sample_count

            previous.model_version = current_snapshot["model_version"]
            previous.release_status = "superseded"
            previous.approved_by = current_snapshot["approved_by"]
            previous.approved_at = current_snapshot["approved_at"]
            previous.created_at = current_snapshot["created_at"]
            previous.pairwise_ranking_accuracy = current_snapshot["pairwise_ranking_accuracy"]
            previous.mean_band_error = current_snapshot["mean_band_error"]
            previous.metrics_source = current_snapshot["metrics_source"]
            previous.metrics_sample_count = current_snapshot["metrics_sample_count"]

            _switch_model_registry_production(db, current.model_version)

        event_note = note
        if action == "approve" and gate_payload.get("forced"):
            event_note = f"{RELEASE_FORCE_NOTE_PREFIX} {note or ''}".strip()
        event = MetaAndromedaReleaseEvent(
            action=action,
            model_version=model_version,
            actor=actor,
            note=event_note,
            created_at=created_at,
        )
        db.add(event)
        db.commit()
        return {
            "status": "ok",
            "action": action,
            "model_version": model_version,
            "actor": actor,
            "created_at": created_at,
            "note": note,
            "forced": bool(gate_payload.get("forced")),
            "release_gate": gate_payload,
        }


    @staticmethod
    def create_backtest_run(
        db: Session,
        *,
        provider_model: str,
        sample_limit: int | None = None,
        note: str | None = None,
        provider: str = "openrouter",
    ) -> dict:
        now = datetime.now(timezone.utc)
        run = MetaAndromedaBacktestRun(
            provider=provider,
            provider_model=provider_model,
            status="queued",
            note=note,
            sample_limit=sample_limit,
            created_at=now,
            updated_at=now,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return ReleaseMixin._backtest_run_to_dict(run)

    @staticmethod
    def list_backtest_runs(db: Session, limit: int = 20) -> dict:
        rows = (
            db.query(MetaAndromedaBacktestRun)
            .order_by(MetaAndromedaBacktestRun.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .all()
        )
        return {
            "runs": [ReleaseMixin._backtest_run_to_dict(row) for row in rows],
            "total": len(rows),
        }

    @staticmethod
    def get_backtest_run(db: Session, run_id: str) -> dict:
        run = db.query(MetaAndromedaBacktestRun).filter(MetaAndromedaBacktestRun.id == run_id).first()
        if run is None:
            raise KeyError(run_id)
        return ReleaseMixin._backtest_run_to_dict(run)

    @staticmethod
    def update_backtest_run(db: Session, run_id: str, **updates) -> dict:
        run = db.query(MetaAndromedaBacktestRun).filter(MetaAndromedaBacktestRun.id == run_id).first()
        if run is None:
            raise KeyError(run_id)
        for key, value in updates.items():
            if hasattr(run, key):
                setattr(run, key, value)
        run.updated_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()
        db.refresh(run)
        return ReleaseMixin._backtest_run_to_dict(run)

    @staticmethod
    def complete_backtest_run_metrics(db: Session, run_id: str) -> dict:
        run = db.query(MetaAndromedaBacktestRun).filter(MetaAndromedaBacktestRun.id == run_id).first()
        if run is None:
            raise KeyError(run_id)
        metrics = compute_backtest_run_metrics(db, run_id)
        run.sample_count = int(metrics.get("sample_count") or 0)
        run.result_summary = deepcopy(metrics)
        if metrics.get("status") == "computed":
            run.pairwise_ranking_accuracy = metrics.get("pairwise_ranking_accuracy")
            run.mean_band_error = metrics.get("mean_band_error")
        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        run.updated_at = run.completed_at
        db.add(run)
        db.commit()
        db.refresh(run)
        return ReleaseMixin._backtest_run_to_dict(run)

    @staticmethod
    def refresh_release_metrics(db: Session, model_version: str) -> dict:
        """Compute real pairwise ranking accuracy / mean band error for `model_version`
        from historical drift-matched pairs and write it back onto whichever release
        record(s) reference this model_version (current/previous/candidate)."""
        metrics = compute_release_metrics(db, model_version)
        if metrics["status"] != "computed":
            return metrics

        records = db.query(MetaAndromedaReleaseRecord).filter(
            MetaAndromedaReleaseRecord.model_version == model_version
        ).all()
        for record in records:
            record.pairwise_ranking_accuracy = metrics["pairwise_ranking_accuracy"]
            record.mean_band_error = metrics["mean_band_error"]
            record.metrics_source = "computed"
            record.metrics_sample_count = metrics["sample_count"]
            db.add(record)
        db.commit()
        return metrics

    @staticmethod
    def list_release_metric_pairs(db: Session, model_version: str, *, sort: str = "mismatch", limit: int = 50) -> dict:
        return list_release_metric_pairs(db, model_version, sort=sort, limit=limit)
