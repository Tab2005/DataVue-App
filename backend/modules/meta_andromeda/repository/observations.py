"""Observation repository operations."""

from ._shared import *  # noqa: F401,F403
from ._stats import *  # noqa: F401,F403
from .release_metrics import *  # noqa: F401,F403

SEED_REVIEW_QUEUE = [
    {
        "id": "ma_evt_20260605_001",
        "status": "completed",
        "runtime_job_id": "ma_score_ma_evt_20260605_001",
        "created_at": datetime(2026, 6, 5, 9, 15, tzinfo=timezone.utc),
        "queued_at": datetime(2026, 6, 5, 9, 15, tzinfo=timezone.utc),
        "started_at": datetime(2026, 6, 5, 9, 15, 10, tzinfo=timezone.utc),
        "completed_at": datetime(2026, 6, 5, 9, 18, tzinfo=timezone.utc),
        "failed_at": None,
        "updated_at": datetime(2026, 6, 5, 9, 18, tzinfo=timezone.utc),
        "asset_uri": "storage://meta-andromeda/assets/creative_001.png",
        "asset_type": "image",
        "asset_id": "creative_001",
        "preview_url": None,
        "request_mode": "diagnostic_plus_roas",
        "objective": "purchase",
        "placement_family": "feed",
        "market": "TW",
        "prediction_mode": "diagnostic_plus_roas",
        "overall_score": 82,
        "roas_band": "high",
        "model_version": "candidate_v0",
        "reviewed": False,
        "feedback_count": 0,
        "latest_feedback_decision": None,
        "feature_manifest_id": "fm_001",
        "error_message": None,
        "attempt_count": 1,
        "diagnostic_breakdown": {
            "hook_strength": "strong",
            "cta_presence": "clear",
            "placement_fit": "good",
        },
        "roas_prediction": {
            "eligible": True,
            "band": "high",
            "confidence": 0.74,
            "reason_if_unavailable": None,
        },
        "risk_tags": ["text_density_watch"],
        "top_positive_drivers": ["strong opening hook", "clear CTA", "offer visibility"],
        "top_negative_drivers": ["text density slightly high"],
        "explanations": {
            "summary": "Creative is ready for reviewer inspection with strong purchase intent signals.",
            "top_positive_drivers": ["strong opening hook", "clear CTA", "offer visibility"],
            "top_risks": ["text density slightly high"],
            "diagnostic_evidence": {
                "headline": "限時優惠訊號清楚",
                "cta": "立即購買明確",
            },
        },
        "lineage": {
            "source_ingest_batch_id": "seed_batch_001",
            "feature_manifest_id": "fm_001",
        },
        "request_context": {},
    },
    {
        "id": "ma_evt_20260605_002",
        "status": "completed",
        "runtime_job_id": "ma_score_ma_evt_20260605_002",
        "created_at": datetime(2026, 6, 5, 8, 40, tzinfo=timezone.utc),
        "queued_at": datetime(2026, 6, 5, 8, 40, tzinfo=timezone.utc),
        "started_at": datetime(2026, 6, 5, 8, 40, 15, tzinfo=timezone.utc),
        "completed_at": datetime(2026, 6, 5, 8, 43, tzinfo=timezone.utc),
        "failed_at": None,
        "updated_at": datetime(2026, 6, 5, 8, 43, tzinfo=timezone.utc),
        "asset_uri": "storage://meta-andromeda/assets/creative_002.mp4",
        "asset_type": "video",
        "asset_id": "creative_002",
        "preview_url": None,
        "request_mode": "diagnostic_plus_roas",
        "objective": "lead",
        "placement_family": "reels",
        "market": "TW",
        "prediction_mode": "diagnostic_plus_roas",
        "overall_score": 61,
        "roas_band": "mid",
        "model_version": "candidate_v0",
        "reviewed": True,
        "feedback_count": 1,
        "latest_feedback_decision": "revise",
        "feature_manifest_id": "fm_002",
        "error_message": None,
        "attempt_count": 1,
        "diagnostic_breakdown": {
            "hook_strength": "medium",
            "cta_presence": "moderate",
            "placement_fit": "good",
        },
        "roas_prediction": {
            "eligible": True,
            "band": "mid",
            "confidence": 0.63,
            "reason_if_unavailable": None,
        },
        "risk_tags": ["hook_not_sharp_enough", "offer_visibility"],
        "top_positive_drivers": ["good reel pacing", "clean branding"],
        "top_negative_drivers": ["hook not sharp enough", "offer visibility can improve"],
        "explanations": {
            "summary": "Creative is usable but likely needs revision before release.",
            "top_positive_drivers": ["good reel pacing", "clean branding"],
            "top_risks": ["hook not sharp enough", "offer visibility can improve"],
            "diagnostic_evidence": {
                "video_pacing": "節奏穩定",
                "offer": "優惠露出偏晚",
            },
        },
        "lineage": {
            "source_ingest_batch_id": "seed_batch_002",
            "feature_manifest_id": "fm_002",
        },
        "request_context": {},
    },
    {
        "id": "ma_evt_20260605_003",
        "status": "queued",
        "runtime_job_id": "ma_score_ma_evt_20260605_003",
        "created_at": datetime(2026, 6, 5, 8, 5, tzinfo=timezone.utc),
        "queued_at": datetime(2026, 6, 5, 8, 5, tzinfo=timezone.utc),
        "started_at": None,
        "completed_at": None,
        "failed_at": None,
        "updated_at": datetime(2026, 6, 5, 8, 5, tzinfo=timezone.utc),
        "asset_uri": "storage://meta-andromeda/assets/creative_003.png",
        "asset_type": "image",
        "asset_id": "creative_003",
        "preview_url": None,
        "request_mode": "auto",
        "objective": "purchase",
        "placement_family": "stories",
        "market": "TW",
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
        "request_context": {},
    },
]

SEED_FEEDBACK = [
    {
        "id": "fb_evt_001",
        "score_event_id": "ma_evt_20260605_002",
        "reviewer_id": "reviewer_01",
        "decision": "revise",
        "reason_codes": ["hook_soft", "offer_late"],
        "comment": "Hook 可再更直接，優惠露出還可以提早。",
        "created_at": datetime(2026, 6, 5, 8, 55, tzinfo=timezone.utc),
    }
]

SEED_RELEASE_RECORDS = [
    {
        "record_kind": "current_production",
        "model_version": "prod_v2026_05_28",
        "release_status": "production",
        "approved_by": "operator_01",
        "approved_at": "2026-05-28T09:30:00Z",
        "created_at": "2026-05-28T09:30:00Z",
        "pairwise_ranking_accuracy": 0.74,
        "mean_band_error": 0.19,
        "promotion_gate_summary": None,
    },
    {
        "record_kind": "previous_production",
        "model_version": "prod_v2026_05_12",
        "release_status": "superseded",
        "approved_by": "operator_01",
        "approved_at": "2026-05-12T08:20:00Z",
        "created_at": "2026-05-12T08:20:00Z",
        "pairwise_ranking_accuracy": 0.69,
        "mean_band_error": 0.23,
        "promotion_gate_summary": None,
    },
    {
        "record_kind": "candidate",
        "model_version": "cand_v2026_06_05_a",
        "release_status": "candidate",
        "approved_by": None,
        "approved_at": None,
        "created_at": "2026-06-05T07:00:00Z",
        "pairwise_ranking_accuracy": 0.78,
        "mean_band_error": 0.17,
        "promotion_gate_summary": {
            "sample_size_ok": True,
            "beats_naive_baseline": True,
            "not_worse_than_production": True,
            "calibration_ok": True,
        },
    },
    {
        "record_kind": "candidate",
        "model_version": "cand_v2026_06_04_b",
        "release_status": "candidate",
        "approved_by": None,
        "approved_at": None,
        "created_at": "2026-06-04T15:10:00Z",
        "pairwise_ranking_accuracy": 0.71,
        "mean_band_error": 0.21,
        "promotion_gate_summary": {
            "sample_size_ok": True,
            "beats_naive_baseline": True,
            "not_worse_than_production": False,
            "calibration_ok": True,
        },
    },
]

SEED_RELEASE_EVENTS = [
    {
        "action": "approve",
        "model_version": "prod_v2026_05_28",
        "actor": "operator_01",
        "created_at": "2026-05-28T09:30:00Z",
        "note": "Promoted after holdout metrics cleared all gates.",
    },
    {
        "action": "rollback",
        "model_version": "prod_v2026_05_12",
        "actor": "operator_02",
        "created_at": "2026-05-13T10:05:00Z",
        "note": "Rolled back due to calibration anomaly.",
    },
]

SEED_DRIFT_REPORTS = [
    {
        "window_kind": "last_24h",
        "drift_status": "stable",
        "summary": "Seed baseline shows no material drift in the initial DataVue bootstrap window.",
        "severity": "info",
        "triggered_by": "system_seed",
        "note": "Bootstrap drift baseline for Meta Andromeda monitoring.",
        "report_payload": {
            "score_total": 3,
            "completed_total": 2,
            "failed_total": 0,
            "dead_letter_total": 0,
            "retrying_total": 0,
            "high_ratio": 0.5,
            "mid_ratio": 0.5,
            "low_ratio": 0.0,
        },
    },
]

class ObservationMixin:
    def ensure_seed_data(self, db: Session):
        if db.query(MetaAndromedaScoreEvent).count() == 0:
            for item in SEED_REVIEW_QUEUE:
                asset = db.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.id == item["asset_id"]).first()
                if asset is None:
                    asset = MetaAndromedaAsset(
                        id=item["asset_id"],
                        asset_uri=item["asset_uri"],
                        storage_backend="seed",
                        storage_key=f"seed/{item['asset_id']}",
                        asset_type=item["asset_type"],
                        source_filename=f"{item['asset_id']}.{ 'png' if item['asset_type'] == 'image' else 'mp4'}",
                        checksum_sha256=f"seed_{item['asset_id']}",
                        upload_status="seeded",
                        file_size_bytes=0,
                        public_url=None,
                        uploaded_by=None,
                        uploaded_at=item["created_at"],
                    )
                    db.add(asset)

                db.add(MetaAndromedaScoreEvent(**item))

            for item in SEED_FEEDBACK:
                db.add(MetaAndromedaFeedbackEvent(**item))

        if db.query(MetaAndromedaReleaseRecord).count() == 0:
            for item in SEED_RELEASE_RECORDS:
                db.add(MetaAndromedaReleaseRecord(**item))

        if db.query(MetaAndromedaReleaseEvent).count() == 0:
            for item in SEED_RELEASE_EVENTS:
                db.add(MetaAndromedaReleaseEvent(**item))

        if db.query(MetaAndromedaDriftReport).count() == 0:
            for item in SEED_DRIFT_REPORTS:
                db.add(MetaAndromedaDriftReport(**item))

        db.commit()

    def get_asset_by_uri(self, db: Session, asset_uri: str) -> MetaAndromedaAsset | None:
        """根據 asset_uri 查詢已上傳的 MetaAndromedaAsset"""
        return db.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.asset_uri == asset_uri).first()

    def create_uploaded_asset(self, db: Session, asset_record: dict):
        asset = MetaAndromedaAsset(**asset_record)
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return {
            "asset_uri": asset.asset_uri,
            "asset_id": asset.id,
            "storage_backend": asset.storage_backend,
            "storage_key": asset.storage_key,
            "asset_type": asset.asset_type,
            "checksum_sha256": asset.checksum_sha256,
            "upload_status": asset.upload_status,
            "source_filename": asset.source_filename,
            "file_size_bytes": asset.file_size_bytes,
            "public_url": asset.public_url,
            "uploaded_at": asset.uploaded_at.isoformat(),
        }

    def create_observed_creative(self, db: Session, observed_record: dict):
        existing = db.query(MetaAndromedaObservedCreative).filter(
            MetaAndromedaObservedCreative.id == observed_record["id"]
        ).first()

        if existing:
            for key, val in observed_record.items():
                if key != "id":
                    setattr(existing, key, val)
            db.commit()
            db.refresh(existing)
            observed = existing
        else:
            observed = MetaAndromedaObservedCreative(**observed_record)
            db.add(observed)
            db.commit()
            db.refresh(observed)
        return {
            "observed_creative_id": observed.id,
            "asset_id": observed.asset_id,
            "asset_uri": observed.asset_uri,
            "source_platform": observed.source_platform,
            "source_account_id": observed.source_account_id,
            "campaign_id": observed.campaign_id,
            "adset_id": observed.adset_id,
            "ad_id": observed.ad_id,
            "ad_name": observed.ad_name,
            "objective": observed.objective,
            "placement_family": observed.placement_family,
            "market": observed.market,
            "primary_text": observed.primary_text,
            "headline": observed.headline,
            "cta": observed.cta,
            "media_url": observed.media_url,
            "media_type": observed.media_type,
            "performance_snapshot": deepcopy(observed.performance_snapshot or {}),
            "observation_window_kind": observed.observation_window_kind,
            "observation_window_start": observed.observation_window_start,
            "observation_window_end": observed.observation_window_end,
            "source_fetched_at": observed.source_fetched_at,
            "lineage": deepcopy(observed.lineage or {}),
            "created_at": observed.created_at.isoformat() if observed.created_at else None,
        }

    def get_observed_creative(self, db: Session, observed_creative_id: str):
        observed = (
            db.query(MetaAndromedaObservedCreative)
            .filter(MetaAndromedaObservedCreative.id == observed_creative_id)
            .first()
        )
        if observed is None:
            return None
        return {
            "observed_creative_id": observed.id,
            "asset_id": observed.asset_id,
            "asset_uri": observed.asset_uri,
            "media_type": observed.media_type,
            "created_at": observed.created_at.isoformat() if observed.created_at else None,
        }

    def get_latest_score_event_for_observation(self, db: Session, observed_creative_id: str):
        score = (
            db.query(MetaAndromedaScoreEvent)
            .filter(
                MetaAndromedaScoreEvent.request_context["observed_creative_id"].as_string() == observed_creative_id
            )
            .order_by(MetaAndromedaScoreEvent.created_at.desc())
            .first()
        )
        if score is None:
            observed = self.get_observed_creative(db, observed_creative_id)
            if not observed or not observed.get("asset_uri"):
                return None
            score = (
                db.query(MetaAndromedaScoreEvent)
                .filter(MetaAndromedaScoreEvent.asset_uri == observed["asset_uri"])
                .order_by(MetaAndromedaScoreEvent.created_at.desc())
                .first()
            )
            if score is None:
                return None
        return self._score_to_detail(score)
