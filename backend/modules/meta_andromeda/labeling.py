"""
Meta Andromeda Module - shared observed-band labeling, matching, and
label-threshold computation.

Single source of truth used by both drift-report generation
(repository.create_drift_report) and calibration-dataset sync
(repository.sync_calibration_dataset). Prior to this module the two call
sites duplicated (and diverged on) the observed<->prediction matching
strategy and the dynamic P33/P67 threshold computation, which meant the
same ObservedCreative could be labeled differently by each pipeline.
"""

import uuid
from datetime import datetime, timezone

from database.models.meta_andromeda import MetaAndromedaAsset, MetaAndromedaScoreEvent

from .objective_routing import LEAD, NON_ROAS_GROUPS, resolve_objective_group

LABEL_POLICY_VERSION = "ma_label_policy_v2"

# 5 筆資料的 P33/P67 幾乎是隨機數；上修至 20 才具備基本統計意義
MIN_SAMPLES_FOR_DYNAMIC_THRESHOLD = 20

_ROAS_FALLBACK_LOW = 3.0
_ROAS_FALLBACK_HIGH = 6.0
_CVR_FALLBACK_LOW = 0.03
_CVR_FALLBACK_HIGH = 0.08
_CPL_FALLBACK_HIGH = 350.0
_CPL_FALLBACK_LOW = 150.0
_CPA_FALLBACK_LOW = 120.0
_CPA_FALLBACK_HIGH = 300.0


def match_observed_to_prediction(db, obs) -> MetaAndromedaScoreEvent | None:
    """Match an ObservedCreative to its most recent completed ScoreEvent.

    Checksum-based matching (via sibling assets sharing the same file hash)
    takes priority over asset_uri exact matching, since a re-uploaded or
    re-downloaded asset gets a fresh random asset_uri but keeps the same
    checksum.
    """
    pred = None
    if obs.asset and obs.asset.checksum_sha256:
        sibling_assets = (
            db.query(MetaAndromedaAsset.id)
            .filter(MetaAndromedaAsset.checksum_sha256 == obs.asset.checksum_sha256)
            .all()
        )
        sibling_asset_ids = [a[0] for a in sibling_assets] if sibling_assets else []
        if sibling_asset_ids:
            pred = (
                db.query(MetaAndromedaScoreEvent)
                .filter(
                    MetaAndromedaScoreEvent.asset_id.in_(sibling_asset_ids),
                    MetaAndromedaScoreEvent.status == "completed",
                )
                .order_by(MetaAndromedaScoreEvent.completed_at.desc())
                .first()
            )

    if not pred and obs.asset_uri:
        pred = (
            db.query(MetaAndromedaScoreEvent)
            .filter(
                MetaAndromedaScoreEvent.asset_uri == obs.asset_uri,
                MetaAndromedaScoreEvent.status == "completed",
            )
            .order_by(MetaAndromedaScoreEvent.completed_at.desc())
            .first()
        )
    return pred


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolation percentile (numpy's default 'linear' method).

    Replaces the previous biased-index lookup (values[int(len*pct)]), which
    systematically skews toward the high end of the distribution.
    """
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    idx = pct * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac


def _load_prior_policy(db, scope_key: str | None, window_kind: str | None):
    if db is None or not scope_key or not window_kind:
        return None
    from database.models.meta_andromeda import MetaAndromedaLabelPolicy

    return (
        db.query(MetaAndromedaLabelPolicy)
        .filter(
            MetaAndromedaLabelPolicy.scope_key == scope_key,
            MetaAndromedaLabelPolicy.window_kind == window_kind,
        )
        .first()
    )


def _resolve_dynamic_threshold(
    values: list[float],
    *,
    reverse: bool,
    prior_low: float | None,
    prior_high: float | None,
    prior_sample_count: int,
) -> tuple[tuple[float, float] | None, str, int]:
    """Compute a P33/P67 threshold pair for one metric.

    reverse=True is for lower-is-better metrics (CPC/CPL): the returned tuple
    is (P67, P33) to match label_observed_band()'s "low_t, high_t" unpacking
    convention for those metrics. When the current batch doesn't clear
    MIN_SAMPLES_FOR_DYNAMIC_THRESHOLD, fall back to the last persisted policy
    for this scope rather than immediately dropping to the global fixed
    fallback — a single small batch shouldn't reset the label boundary.
    """
    if len(values) >= MIN_SAMPLES_FOR_DYNAMIC_THRESHOLD:
        p33, p67 = _percentile(values, 0.33), _percentile(values, 0.67)
        thresholds = (p67, p33) if reverse else (p33, p67)
        return thresholds, "percentile_p33_p67", len(values)
    if prior_low is not None and prior_high is not None:
        return (prior_low, prior_high), "persisted_prior", prior_sample_count or 0
    return None, "fixed_fallback", len(values)


def compute_label_thresholds(
    observed_list: list,
    *,
    db=None,
    scope_key: str | None = None,
    window_kind: str | None = None,
) -> dict:
    """Compute dynamic P33/P67 label thresholds for a batch of ObservedCreative rows.

    Groups are routed via the shared resolve_objective_group() so the
    threshold pools always match the same grouping the prompt/runtime uses.
    Pass db/scope_key/window_kind to enable falling back to the last
    persisted MetaAndromedaLabelPolicy when the current batch is too small.
    """
    prior = _load_prior_policy(db, scope_key, window_kind)

    roas_values = sorted(
        float(obs.performance_snapshot["roas"])
        for obs in observed_list
        if obs.performance_snapshot
        and obs.performance_snapshot.get("roas") is not None
        and resolve_objective_group(obs.objective) not in NON_ROAS_GROUPS
        and resolve_objective_group(obs.objective) != LEAD
    )
    roas_thresholds, roas_method, roas_sample_count = _resolve_dynamic_threshold(
        roas_values,
        reverse=False,
        prior_low=prior.roas_low if prior else None,
        prior_high=prior.roas_high if prior else None,
        prior_sample_count=prior.roas_sample_count if prior else 0,
    )

    traffic_obs = [obs for obs in observed_list if resolve_objective_group(obs.objective) in NON_ROAS_GROUPS]
    ctr_values = sorted(
        float(obs.performance_snapshot["ctr"])
        for obs in traffic_obs
        if obs.performance_snapshot and obs.performance_snapshot.get("ctr")
    )
    ctr_thresholds, ctr_method, ctr_sample_count = _resolve_dynamic_threshold(
        ctr_values,
        reverse=False,
        prior_low=prior.ctr_low if prior else None,
        prior_high=prior.ctr_high if prior else None,
        prior_sample_count=prior.ctr_sample_count if prior else 0,
    )

    cpc_values = sorted(
        float(obs.performance_snapshot["cpc"])
        for obs in traffic_obs
        if obs.performance_snapshot
        and obs.performance_snapshot.get("cpc")
        and float(obs.performance_snapshot["cpc"]) > 0
    )
    cpc_thresholds, cpc_method, cpc_sample_count = _resolve_dynamic_threshold(
        cpc_values,
        reverse=True,
        prior_low=prior.cpc_low if prior else None,
        prior_high=prior.cpc_high if prior else None,
        prior_sample_count=prior.cpc_sample_count if prior else 0,
    )

    lead_obs = [obs for obs in observed_list if resolve_objective_group(obs.objective) == LEAD]
    cvr_values = sorted(
        float(obs.performance_snapshot["cvr"])
        for obs in lead_obs
        if obs.performance_snapshot and obs.performance_snapshot.get("cvr") is not None
    )
    cvr_thresholds, cvr_method, cvr_sample_count = _resolve_dynamic_threshold(
        cvr_values,
        reverse=False,
        prior_low=prior.cvr_low if prior else None,
        prior_high=prior.cvr_high if prior else None,
        prior_sample_count=prior.cvr_sample_count if prior else 0,
    )

    cpl_values = sorted(
        float(obs.performance_snapshot["cpl"])
        for obs in lead_obs
        if obs.performance_snapshot
        and obs.performance_snapshot.get("cpl") is not None
        and float(obs.performance_snapshot["cpl"]) > 0
    )
    cpl_thresholds, cpl_method, cpl_sample_count = _resolve_dynamic_threshold(
        cpl_values,
        reverse=True,
        prior_low=prior.cpl_low if prior else None,
        prior_high=prior.cpl_high if prior else None,
        prior_sample_count=prior.cpl_sample_count if prior else 0,
    )

    lead_with_metric_total = sum(
        1
        for obs in lead_obs
        if obs.performance_snapshot
        and (
            obs.performance_snapshot.get("cvr") is not None
            or obs.performance_snapshot.get("cpl") is not None
        )
    )

    return {
        "roas": {"thresholds": roas_thresholds, "method": roas_method, "sample_count": roas_sample_count},
        "ctr": {"thresholds": ctr_thresholds, "method": ctr_method, "sample_count": ctr_sample_count},
        "cpc": {"thresholds": cpc_thresholds, "method": cpc_method, "sample_count": cpc_sample_count},
        "cvr": {"thresholds": cvr_thresholds, "method": cvr_method, "sample_count": cvr_sample_count},
        "cpl": {"thresholds": cpl_thresholds, "method": cpl_method, "sample_count": cpl_sample_count},
        "traffic_total": len(traffic_obs),
        "lead_total": len(lead_obs),
        "lead_with_metric_total": lead_with_metric_total,
    }


def label_observed_band(
    objective: str | None,
    performance_snapshot: dict | None,
    label_thresholds: dict | None = None,
) -> tuple[str, dict]:
    """Resolve the observed roas_band for one ObservedCreative row.

    label_thresholds is the dict returned by compute_label_thresholds();
    when omitted (e.g. single-record lookups where percentiles are
    meaningless), each metric falls back to its fixed threshold.
    """
    label_thresholds = label_thresholds or {}
    snapshot = performance_snapshot or {}
    group = resolve_objective_group(objective)

    if group == LEAD:
        cvr = snapshot.get("cvr")
        if cvr is not None:
            value = float(cvr)
            low_t, high_t = (label_thresholds.get("cvr") or {}).get("thresholds") or (
                _CVR_FALLBACK_LOW,
                _CVR_FALLBACK_HIGH,
            )
            if value >= high_t:
                return "high", {"metric": "cvr", "value": value}
            if value >= low_t:
                return "mid", {"metric": "cvr", "value": value}
            return "low", {"metric": "cvr", "value": value}

        cpl = snapshot.get("cpl")
        if cpl is not None:
            value = float(cpl)
            low_t, high_t = (label_thresholds.get("cpl") or {}).get("thresholds") or (
                _CPL_FALLBACK_HIGH,
                _CPL_FALLBACK_LOW,
            )
            if value <= high_t:
                return "high", {"metric": "cpl", "value": value}
            if value <= low_t:
                return "mid", {"metric": "cpl", "value": value}
            return "low", {"metric": "cpl", "value": value}

        return "low", {"metric": "fallback_lead", "value": None}

    if group in NON_ROAS_GROUPS:
        ctr = snapshot.get("ctr")
        ctr_thresholds = (label_thresholds.get("ctr") or {}).get("thresholds")
        if ctr is not None and ctr_thresholds:
            value = float(ctr)
            low_t, high_t = ctr_thresholds
            if value >= high_t:
                return "high", {"metric": "ctr", "value": value}
            if value >= low_t:
                return "mid", {"metric": "ctr", "value": value}
            return "low", {"metric": "ctr", "value": value}

        cpc = snapshot.get("cpc")
        cpc_thresholds = (label_thresholds.get("cpc") or {}).get("thresholds")
        if cpc is not None and cpc_thresholds and float(cpc) > 0:
            value = float(cpc)
            low_t, high_t = cpc_thresholds
            if value <= high_t:
                return "high", {"metric": "cpc", "value": value}
            if value <= low_t:
                return "mid", {"metric": "cpc", "value": value}
            return "low", {"metric": "cpc", "value": value}

        return "low", {"metric": "fallback_traffic", "value": None}

    # conversion / app / unknown
    roas = snapshot.get("roas")
    if roas is not None:
        value = float(roas)
        low_t, high_t = (label_thresholds.get("roas") or {}).get("thresholds") or (
            _ROAS_FALLBACK_LOW,
            _ROAS_FALLBACK_HIGH,
        )
        if value < low_t:
            return "low", {"metric": "roas", "value": value}
        if value < high_t:
            return "mid", {"metric": "roas", "value": value}
        return "high", {"metric": "roas", "value": value}

    cpa = snapshot.get("cpa")
    if cpa is not None:
        value = float(cpa)
        if value <= _CPA_FALLBACK_LOW:
            return "high", {"metric": "cpa", "value": value}
        if value <= _CPA_FALLBACK_HIGH:
            return "mid", {"metric": "cpa", "value": value}
        return "low", {"metric": "cpa", "value": value}

    return "low", {"metric": "fallback", "value": None}


def persist_label_policy(db, scope_key: str, window_kind: str, thresholds: dict) -> None:
    """Upsert the dynamic thresholds computed for (scope_key, window_kind) as an audit record."""
    from database.models.meta_andromeda import MetaAndromedaLabelPolicy

    existing = (
        db.query(MetaAndromedaLabelPolicy)
        .filter(
            MetaAndromedaLabelPolicy.scope_key == scope_key,
            MetaAndromedaLabelPolicy.window_kind == window_kind,
        )
        .first()
    )

    roas = thresholds.get("roas") or {}
    ctr = thresholds.get("ctr") or {}
    cpc = thresholds.get("cpc") or {}
    cvr = thresholds.get("cvr") or {}
    cpl = thresholds.get("cpl") or {}
    roas_t = roas.get("thresholds") or (None, None)
    ctr_t = ctr.get("thresholds") or (None, None)
    cpc_t = cpc.get("thresholds") or (None, None)
    cvr_t = cvr.get("thresholds") or (None, None)
    cpl_t = cpl.get("thresholds") or (None, None)

    values = dict(
        window_kind=window_kind,
        label_policy_version=LABEL_POLICY_VERSION,
        roas_low=roas_t[0],
        roas_high=roas_t[1],
        roas_method=roas.get("method"),
        roas_sample_count=roas.get("sample_count", 0),
        ctr_low=ctr_t[0],
        ctr_high=ctr_t[1],
        ctr_method=ctr.get("method"),
        ctr_sample_count=ctr.get("sample_count", 0),
        cpc_low=cpc_t[0],
        cpc_high=cpc_t[1],
        cpc_method=cpc.get("method"),
        cpc_sample_count=cpc.get("sample_count", 0),
        cvr_low=cvr_t[0],
        cvr_high=cvr_t[1],
        cvr_method=cvr.get("method"),
        cvr_sample_count=cvr.get("sample_count", 0),
        cpl_low=cpl_t[0],
        cpl_high=cpl_t[1],
        cpl_method=cpl.get("method"),
        cpl_sample_count=cpl.get("sample_count", 0),
        effective_from=datetime.now(timezone.utc),
    )

    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
    else:
        db.add(MetaAndromedaLabelPolicy(id=f"ma_lp_{uuid.uuid4().hex[:12]}", scope_key=scope_key, **values))
    db.commit()
