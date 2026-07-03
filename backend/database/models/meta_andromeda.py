# backend/database/models/meta_andromeda.py
"""Meta Andromeda workflow ORM models"""

import uuid
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, text
from sqlalchemy.orm import relationship

from database.base import Base


class MetaAndromedaAsset(Base):
    __tablename__ = "meta_andromeda_assets"

    id = Column(String, primary_key=True, default=lambda: f"asset_{uuid.uuid4().hex[:10]}")
    asset_uri = Column(String, unique=True, nullable=False, index=True)
    storage_backend = Column(String(50), nullable=False, default="filesystem")
    storage_key = Column(String, nullable=False)
    asset_type = Column(String(20), nullable=False)
    source_filename = Column(String, nullable=False)
    checksum_sha256 = Column(String(128), nullable=False)
    upload_status = Column(String(50), nullable=False, default="stored")
    file_size_bytes = Column(Integer, nullable=False, default=0)
    public_url = Column(String, nullable=True)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    uploader = relationship("User")


class MetaAndromedaObservedCreative(Base):
    __tablename__ = "meta_andromeda_observed_creatives"

    id = Column(String, primary_key=True, default=lambda: f"ma_obs_{uuid.uuid4().hex[:12]}")
    asset_id = Column(String, ForeignKey("meta_andromeda_assets.id"), nullable=True)
    asset_uri = Column(String, nullable=True, index=True)
    source_platform = Column(String(50), nullable=False, index=True)
    source_account_id = Column(String(120), nullable=False, index=True)
    campaign_id = Column(String(120), nullable=True, index=True)
    adset_id = Column(String(120), nullable=True, index=True)
    ad_id = Column(String(120), nullable=False, index=True)
    ad_name = Column(String, nullable=True)
    objective = Column(String(50), nullable=True)
    placement_family = Column(String(50), nullable=False)
    market = Column(String(20), nullable=False)
    primary_text = Column(Text, nullable=True)
    headline = Column(Text, nullable=True)
    cta = Column(String(100), nullable=True)
    media_url = Column(String, nullable=True)
    media_type = Column(String(20), nullable=False, default="unknown")
    performance_snapshot = Column(JSON, nullable=False, default=dict)
    observation_window_kind = Column(String(50), nullable=False, index=True)
    observation_window_start = Column(String(40), nullable=False)
    observation_window_end = Column(String(40), nullable=False)
    source_fetched_at = Column(String(40), nullable=False)
    lineage = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    asset = relationship("MetaAndromedaAsset", backref="observed_creatives")


class MetaAndromedaScoreEvent(Base):
    __tablename__ = "meta_andromeda_score_events"

    id = Column(String, primary_key=True, default=lambda: f"ma_evt_{uuid.uuid4().hex[:12]}")
    status = Column(String(50), nullable=False)
    runtime_job_id = Column(String(120), nullable=True, index=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    queued_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
    asset_uri = Column(String, nullable=False)
    asset_type = Column(String(20), nullable=False)
    asset_id = Column(String, ForeignKey("meta_andromeda_assets.id"), nullable=True)
    preview_url = Column(String, nullable=True)
    request_mode = Column(String(50), nullable=False)
    objective = Column(String(50), nullable=False)
    placement_family = Column(String(50), nullable=False)
    market = Column(String(20), nullable=False)
    prediction_mode = Column(String(50), nullable=True)
    overall_score = Column(Integer, nullable=True)
    roas_band = Column(String(50), nullable=True)
    model_version = Column(String(100), nullable=True)
    reviewed = Column(Boolean, nullable=False, default=False)
    feedback_count = Column(Integer, nullable=False, default=0)
    latest_feedback_decision = Column(String(50), nullable=True)
    feature_manifest_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    diagnostic_breakdown = Column(JSON, nullable=False, default=dict)
    roas_prediction = Column(JSON, nullable=True)
    risk_tags = Column(JSON, nullable=False, default=list)
    top_positive_drivers = Column(JSON, nullable=False, default=list)
    top_negative_drivers = Column(JSON, nullable=False, default=list)
    explanations = Column(JSON, nullable=True)
    lineage = Column(JSON, nullable=False, default=dict)
    request_context = Column(JSON, nullable=False, default=dict)

    asset = relationship("MetaAndromedaAsset", backref="score_events")


class MetaAndromedaFeedbackEvent(Base):
    __tablename__ = "meta_andromeda_feedback_events"

    id = Column(String, primary_key=True, default=lambda: f"fb_evt_{uuid.uuid4().hex[:8]}")
    score_event_id = Column(String, ForeignKey("meta_andromeda_score_events.id"), nullable=False, index=True)
    reviewer_id = Column(String, nullable=False)
    decision = Column(String(50), nullable=False)
    reason_codes = Column(JSON, nullable=False, default=list)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    score_event = relationship("MetaAndromedaScoreEvent", backref="feedback_events")


class MetaAndromedaReleaseRecord(Base):
    __tablename__ = "meta_andromeda_release_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    record_kind = Column(String(50), nullable=False, index=True)  # current_production / previous_production / candidate
    model_version = Column(String(100), nullable=False, index=True)
    release_status = Column(String(50), nullable=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    pairwise_ranking_accuracy = Column(Float, nullable=False)
    mean_band_error = Column(Float, nullable=False)
    promotion_gate_summary = Column(JSON, nullable=True)
    # "seed"（示範資料，從未實算過）或 "computed"（repository.compute_release_metrics()
    # 從實際 drift-matched pairs 算出）；驅動 Release 工作台的 is_demo_data 標示
    metrics_source = Column(String(20), nullable=False, default="seed")
    metrics_sample_count = Column(Integer, nullable=True)


class MetaAndromedaReleaseEvent(Base):
    __tablename__ = "meta_andromeda_release_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String(50), nullable=False)
    model_version = Column(String(100), nullable=False, index=True)
    actor = Column(String, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(String, nullable=False)


class MetaAndromedaWorkerEvent(Base):
    __tablename__ = "meta_andromeda_worker_events"

    id = Column(String, primary_key=True, default=lambda: f"ma_we_{uuid.uuid4().hex[:12]}")
    score_event_id = Column(String, ForeignKey("meta_andromeda_score_events.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    queue_host = Column(String(50), nullable=False)
    runtime_job_id = Column(String(120), nullable=True, index=True)
    status = Column(String(50), nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=True)
    event_payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    score_event = relationship("MetaAndromedaScoreEvent", backref="worker_events")


class MetaAndromedaDeadLetter(Base):
    __tablename__ = "meta_andromeda_dead_letters"

    id = Column(String, primary_key=True, default=lambda: f"ma_dl_{uuid.uuid4().hex[:12]}")
    score_event_id = Column(String, ForeignKey("meta_andromeda_score_events.id"), nullable=False, index=True)
    queue_host = Column(String(50), nullable=False)
    runtime_job_id = Column(String(120), nullable=True, index=True)
    final_error_message = Column(Text, nullable=False)
    failure_stage = Column(String(50), nullable=False)
    attempt_count = Column(Integer, nullable=False, default=0)
    dead_letter_payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    score_event = relationship("MetaAndromedaScoreEvent", backref="dead_letters")


class MetaAndromedaDriftReport(Base):
    __tablename__ = "meta_andromeda_drift_reports"

    id = Column(String, primary_key=True, default=lambda: f"ma_dr_{uuid.uuid4().hex[:12]}")
    window_kind = Column(String(50), nullable=False, index=True)
    drift_status = Column(String(50), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    severity = Column(String(30), nullable=False, default="info")
    triggered_by = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    report_payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class MetaAndromedaCalibrationDataset(Base):
    __tablename__ = "meta_andromeda_calibration_datasets"

    id = Column(String, primary_key=True, default=lambda: f"cal_ds_{uuid.uuid4().hex[:12]}")
    window_kind = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    label_policy_version = Column(String(50), nullable=False)
    since = Column(String(40), nullable=True)
    until = Column(String(40), nullable=True)
    excluded_observed_ids = Column(JSON, nullable=False, default=list)
    synced_count = Column(Integer, nullable=False, default=0)
    summary = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class MetaAndromedaCalibrationItem(Base):
    __tablename__ = "meta_andromeda_calibration_items"

    id = Column(String, primary_key=True, default=lambda: f"cal_item_{uuid.uuid4().hex[:12]}")
    dataset_id = Column(
        String,
        ForeignKey("meta_andromeda_calibration_datasets.id"),
        nullable=False,
        index=True,
    )
    observed_creative_id = Column(
        String,
        ForeignKey("meta_andromeda_observed_creatives.id"),
        nullable=False,
        index=True,
    )
    score_event_id = Column(
        String,
        ForeignKey("meta_andromeda_score_events.id"),
        nullable=False,
        index=True,
    )
    asset_uri = Column(String, nullable=True, index=True)
    objective = Column(String(50), nullable=True)
    market = Column(String(20), nullable=False)
    placement_family = Column(String(50), nullable=False)
    prediction_band = Column(String(20), nullable=False)
    observed_band = Column(String(20), nullable=False)
    error = Column(Float, nullable=False)
    performance_snapshot = Column(JSON, nullable=False, default=dict)
    label_policy_version = Column(String(50), nullable=False)
    label_thresholds = Column(JSON, nullable=True)
    # "few_shot" (used to build calibration-guidance examples) vs "holdout" (reserved for
    # promote-gate backtest evaluation, never injected into few-shot prompts)
    split = Column(String(20), nullable=True)
    # overall_score from the ScoreEvent that produced prediction_band, kept so the holdout
    # backtest can compute a baseline ranking correlation (Spearman) to compare against the
    # candidate profile's re-scored ranking, not just band accuracy
    baseline_overall_score = Column(Integer, nullable=True)
    # numeric diagnostic_breakdown sub-scores (visual_appeal/copywriting/cta_clarity/...) at
    # scoring time, extracted by runtime._normalize_diagnostic_breakdown(); feeds the P1-1
    # statistical calibration layer
    diagnostic_scores = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    dataset = relationship("MetaAndromedaCalibrationDataset", backref="items")
    observed_creative = relationship("MetaAndromedaObservedCreative")
    score_event = relationship("MetaAndromedaScoreEvent")


class MetaAndromedaScoringProfile(Base):
    __tablename__ = "meta_andromeda_scoring_profiles"

    id = Column(String, primary_key=True, default=lambda: f"sp_{uuid.uuid4().hex[:12]}")
    profile_name = Column(String, nullable=False, unique=True, index=True)
    user_prompt_template = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    calibration_guidance = Column(Text, nullable=True)
    few_shot_examples = Column(JSON, nullable=False, default=list)
    bias_summary = Column(JSON, nullable=True)
    source = Column(String(30), nullable=False, default="seed")
    base_profile_name = Column(String, nullable=True)
    calibration_dataset_id = Column(
        String,
        ForeignKey("meta_andromeda_calibration_datasets.id"),
        nullable=True,
    )
    objective_profiles = Column(JSON, nullable=True)
    is_promoted = Column(Boolean, nullable=False, default=False)
    promoted_at = Column(DateTime, nullable=True)
    # Holdout backtest metrics captured at promote time (band accuracy/ranking accuracy
    # for this profile vs the profile it replaced), used as the baseline for post-promote
    # drift comparisons.
    promotion_baseline = Column(JSON, nullable=True)
    consecutive_degraded_periods = Column(Integer, nullable=False, default=0)
    demoted_at = Column(DateTime, nullable=True)
    demoted_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))

    calibration_dataset = relationship("MetaAndromedaCalibrationDataset")


class MetaAndromedaLabelPolicy(Base):
    """Persisted audit record of the dynamic P33/P67 label thresholds computed
    for a given (scope_key, window_kind), shared by drift reports and
    calibration-dataset sync so both pipelines label the same observed batch
    identically. scope_key is an account_id, or "global" when unscoped."""

    __tablename__ = "meta_andromeda_label_policies"

    id = Column(String, primary_key=True, default=lambda: f"ma_lp_{uuid.uuid4().hex[:12]}")
    scope_key = Column(String(120), nullable=False, index=True)
    window_kind = Column(String(50), nullable=False, index=True)
    label_policy_version = Column(String(50), nullable=False)
    roas_low = Column(Float, nullable=True)
    roas_high = Column(Float, nullable=True)
    roas_method = Column(String(30), nullable=True)
    roas_sample_count = Column(Integer, nullable=False, default=0)
    ctr_low = Column(Float, nullable=True)
    ctr_high = Column(Float, nullable=True)
    ctr_method = Column(String(30), nullable=True)
    ctr_sample_count = Column(Integer, nullable=False, default=0)
    cpc_low = Column(Float, nullable=True)
    cpc_high = Column(Float, nullable=True)
    cpc_method = Column(String(30), nullable=True)
    cpc_sample_count = Column(Integer, nullable=False, default=0)
    cvr_low = Column(Float, nullable=True)
    cvr_high = Column(Float, nullable=True)
    cvr_method = Column(String(30), nullable=True)
    cvr_sample_count = Column(Integer, nullable=False, default=0)
    cpl_low = Column(Float, nullable=True)
    cpl_high = Column(Float, nullable=True)
    cpl_method = Column(String(30), nullable=True)
    cpl_sample_count = Column(Integer, nullable=False, default=0)
    effective_from = Column(DateTime, nullable=False, default=text("CURRENT_TIMESTAMP"))
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class MetaAndromedaConfidenceCalibration(Base):
    """Isotonic (PAVA) mapping from the AI provider's raw overall_score to an
    empirically observed band-accuracy hit rate, fit from CalibrationItem
    history by calibration_stats.fit_confidence_calibration(). Lets the
    runtime's reported "confidence" mean what it claims instead of being a
    hand-written formula (docs/20 task 3.1 / P2-4)."""

    __tablename__ = "meta_andromeda_confidence_calibrations"

    id = Column(String, primary_key=True, default=lambda: f"ma_cc_{uuid.uuid4().hex[:12]}")
    scope_key = Column(String(120), nullable=False, unique=True, index=True)
    calibration_data = Column(JSON, nullable=False, default=dict)
    item_count = Column(Integer, nullable=False, default=0)
    fitted_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))


class MetaAndromedaModelRegistryEntry(Base):
    """DB-backed model registry (docs/20 task 3.2 / P0-6 full version).

    Mirrors model_registry.py's previously hardcoded _entries dict. Exactly one
    row should have is_current_production=True at a time; runtime.model_registry
    reads this table first and falls back to the hardcoded dict only if the
    table is empty or unreachable (defense in depth, not the primary path)."""

    __tablename__ = "meta_andromeda_model_registry_entries"

    id = Column(String, primary_key=True, default=lambda: f"mr_{uuid.uuid4().hex[:12]}")
    model_version = Column(String(100), nullable=False, unique=True, index=True)
    provider = Column(String(50), nullable=False)
    provider_model = Column(String(200), nullable=False)
    scoring_profile = Column(String(120), nullable=False)
    feature_manifest_id = Column(String(100), nullable=False)
    release_channel = Column(String(30), nullable=False)
    source_of_truth = Column(String(120), nullable=False)
    is_current_production = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, default=text("CURRENT_TIMESTAMP"))
