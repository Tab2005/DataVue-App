"""FeedbackCalibration repository operations."""

from ._shared import *  # noqa: F401,F403
from ._stats import *  # noqa: F401,F403
from .release_metrics import *  # noqa: F401,F403

class FeedbackCalibrationMixin:
    def list_feedback(self, db: Session, score_event_id: str):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
        feedback = (
            db.query(MetaAndromedaFeedbackEvent)
            .filter(MetaAndromedaFeedbackEvent.score_event_id == score_event_id)
            .order_by(MetaAndromedaFeedbackEvent.created_at.asc())
            .all()
        )
        return {
            "score_event_id": score_event_id,
            "feedback": [
                {
                    "feedback_event_id": item.id,
                    "score_event_id": item.score_event_id,
                    "reviewer_id": item.reviewer_id,
                    "decision": item.decision,
                    "reason_codes": item.reason_codes or [],
                    "comment": item.comment,
                    "created_at": item.created_at.isoformat(),
                }
                for item in feedback
            ],
        }

    def submit_feedback(self, db: Session, score_event_id: str, reviewer_id: str, decision: str, reason_codes=None, comment=None):
        score = db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)

        feedback = MetaAndromedaFeedbackEvent(
            score_event_id=score_event_id,
            reviewer_id=reviewer_id,
            decision=decision,
            reason_codes=reason_codes or [],
            comment=comment,
        )
        score.reviewed = True
        score.feedback_count += 1
        score.latest_feedback_decision = decision
        score.updated_at = datetime.now(timezone.utc)

        # 分歧樣本自動標記為校準候選：reviewer 明確拒絕高分素材、或核准低分素材，代表人的判斷
        # 與模型判斷方向相反，值得後續人工複核是否要納入 prompt 校準（人工弱標籤，與市場成效
        # 標籤分開權重，不直接當市場 ground truth 用，因為市場數據還沒回來）
        overall_score = score.overall_score
        is_divergent = (
            overall_score is not None
            and (
                (decision == "reject" and overall_score >= 70)
                or (decision == "approve" and overall_score <= 40)
            )
        )
        if is_divergent:
            lineage = dict(score.lineage or {})
            lineage["human_feedback_flag"] = {
                "decision": decision,
                "overall_score": overall_score,
                "reason_codes": reason_codes or [],
                "flagged_at": datetime.now(timezone.utc).isoformat(),
                "note": "reviewer decision diverges from AI score direction; candidate for manual calibration review",
            }
            score.lineage = lineage
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(score, "lineage")

        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return {
            "feedback_event_id": feedback.id,
            "score_event_id": feedback.score_event_id,
            "reviewer_id": feedback.reviewer_id,
            "decision": feedback.decision,
            "reason_codes": feedback.reason_codes or [],
            "comment": feedback.comment,
            "created_at": feedback.created_at.isoformat(),
            "flagged_for_calibration_review": is_divergent,
        }

    @staticmethod
    def list_feedback_calibration_candidates(db: Session, limit: int = 50) -> list[dict]:
        """Score events whose human review diverged from the AI's own score
        (submit_feedback's human_feedback_flag), surfaced for an operator to
        manually decide whether to fold into the next calibration round."""
        rows = (
            db.query(MetaAndromedaScoreEvent)
            .filter(MetaAndromedaScoreEvent.status == "completed")
            .order_by(MetaAndromedaScoreEvent.updated_at.desc())
            .limit(500)
            .all()
        )
        candidates = []
        for row in rows:
            flag = (row.lineage or {}).get("human_feedback_flag")
            if not flag:
                continue
            candidates.append({
                "score_event_id": row.id,
                "asset_uri": row.asset_uri,
                "overall_score": row.overall_score,
                "roas_band": row.roas_band,
                **flag,
            })
            if len(candidates) >= limit:
                break
        return candidates

    @staticmethod
    def analyze_feedback_reason_codes(db: Session) -> dict:
        """Validate reviewer feedback against market ground truth: for each
        reason_code, how often did the score events it was attached to end up
        matching (or diverging from) their later-observed market band? This is
        "reviewer 說 hook_soft 的素材是否真的表現差" made concrete — it tells you
        whether to trust a given reason_code's signal or the model's own band.
        """
        feedback_rows = db.query(MetaAndromedaFeedbackEvent).all()
        if not feedback_rows:
            return {"total_feedback_events": 0, "reason_code_breakdown": {}}

        score_ids = {f.score_event_id for f in feedback_rows}
        cal_items = (
            db.query(MetaAndromedaCalibrationItem)
            .filter(MetaAndromedaCalibrationItem.score_event_id.in_(score_ids))
            .all()
        )
        band_by_score_id = {item.score_event_id: item for item in cal_items}

        breakdown: dict[str, dict] = {}
        for fb in feedback_rows:
            cal_item = band_by_score_id.get(fb.score_event_id)
            for code in (fb.reason_codes or []):
                bucket = breakdown.setdefault(code, {
                    "total": 0,
                    "with_market_data": 0,
                    "reviewer_matched_market": 0,
                })
                bucket["total"] += 1
                if cal_item is None:
                    continue
                bucket["with_market_data"] += 1
                # reject/revise 代表 reviewer 認為素材有問題；若市場實績也落在 low/mid（非 high），
                # 視為 reviewer 判斷與市場一致
                reviewer_flagged_weak = fb.decision in ("reject", "revise")
                market_confirms_weak = cal_item.observed_band in ("low", "mid")
                if reviewer_flagged_weak == market_confirms_weak:
                    bucket["reviewer_matched_market"] += 1

        for code, bucket in breakdown.items():
            bucket["reviewer_market_agreement_rate"] = (
                round(bucket["reviewer_matched_market"] / bucket["with_market_data"], 4)
                if bucket["with_market_data"] else None
            )

        return {"total_feedback_events": len(feedback_rows), "reason_code_breakdown": breakdown}

    def sync_calibration_dataset(
        self,
        db: Session,
        window_kind: str,
        excluded_observed_ids: list[str],
    ) -> dict:
        # 1. 撈取該窗口的所有 Observed Creative
        observed_list = (
            db.query(MetaAndromedaObservedCreative)
            .filter(MetaAndromedaObservedCreative.observation_window_kind == window_kind)
            .all()
        )
        
        import uuid
        dataset_id = f"cal_ds_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        synced_count = 0
        matched_count = 0
        error_item_count = 0
        skipped_not_band_eligible = 0
        skipped_heuristic = 0
        skipped_insufficient_delivery = 0
        skipped_immature = 0
        band_score = {"low": 1, "mid": 2, "high": 3}
        dataset = MetaAndromedaCalibrationDataset(
            id=dataset_id,
            window_kind=window_kind,
            status="no_data_to_sync",
            label_policy_version=LABEL_POLICY_VERSION,
            excluded_observed_ids=excluded_observed_ids or [],
            synced_count=0,
            summary={},
        )
        db.add(dataset)

        # 動態標籤門檻：與 create_drift_report 共用同一套計算方式，確保同一批
        # ObservedCreative 在 drift 與校準兩處算出一致的 observed_band；樣本不足時沿用
        # 上一期已持久化的門檻
        eligible_observed_list = [obs for obs in observed_list if obs.id not in excluded_observed_ids]
        eligible_observed_list, _deduped_ad_count = _dedupe_observed_by_ad_id(eligible_observed_list)
        label_thresholds = compute_label_thresholds(
            eligible_observed_list, db=db, scope_key="global", window_kind=window_kind
        )
        persist_label_policy(db, "global", window_kind, label_thresholds)

        # 2. 篩選有偏差且未被排除的進行標記
        for obs in eligible_observed_list:
            # 排除 spend=0 的記錄（廣告未實際投放，成效數據無意義）
            if float((obs.performance_snapshot or {}).get("spend", 0) or 0) <= 0:
                continue
            if not obs.asset_uri and not (obs.asset and obs.asset.checksum_sha256):
                continue

            # 曝光/觀測期間門檻：與 drift report 一致，小曝光或觀測期過短的樣本不進校準集
            impressions = int((obs.performance_snapshot or {}).get("impressions", 0) or 0)
            if impressions < MIN_IMPRESSIONS_FOR_ACCURACY:
                skipped_insufficient_delivery += 1
                continue
            window_days = _window_days(obs.observation_window_start, obs.observation_window_end)
            if window_days is not None and window_days < MIN_OBSERVATION_WINDOW_DAYS:
                skipped_immature += 1
                continue

            # 尋找匹配的 Completed ScoreEvent（與 drift report 使用同一套 checksum→asset_uri 匹配邏輯）
            pred = match_observed_to_prediction(db, obs)

            if not pred:
                continue

            pred_lineage = pred.lineage or {}
            if pred_lineage.get("scoring_purpose") == "backtest":
                continue

            # heuristic fallback 分數是規則加減分而非模型判斷，不該被拿來「校準模型」
            if pred_lineage.get("scoring_mode") == "heuristic":
                skipped_heuristic += 1
                continue
            matched_count += 1

            real_band, label_detail = label_observed_band(obs.objective, obs.performance_snapshot, label_thresholds)

            # 非轉換/lead 廣告（roas_band=null 為正確設計）不進入校準集，避免模型「正確不出 band」
            # 被誤判為預測錯誤而拉偏 prompt 校準方向
            pred_roas_eligible = (pred.roas_prediction or {}).get("eligible")
            if pred_roas_eligible is None:
                pred_roas_eligible = resolve_objective_group(obs.objective) not in NON_ROAS_GROUPS
            if not pred_roas_eligible or pred.roas_band is None:
                skipped_not_band_eligible += 1
                continue
            pred_band = pred.roas_band

            # 同時收錄有偏差（err>0，校準用）與正確配對（err=0，對照組/回測 holdout 用）的項目，
            # 不再只收 err>0——正確配對是驗證校準有沒有把「本來就對的」判斷帶偏的唯一依據
            err = abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1))
            item_id = f"cal_item_{uuid.uuid4().hex[:12]}"
            if err > 0:
                error_item_count += 1
                lineage = deepcopy(obs.lineage or {})
                lineage["calibration"] = {
                    "dataset_id": dataset_id,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                    "prediction_band": pred_band,
                    "observed_band": real_band,
                    "error": err,
                    "label_policy_version": LABEL_POLICY_VERSION,
                    "label_metric": label_detail["metric"],
                }
                obs.lineage = lineage
            db.add(
                MetaAndromedaCalibrationItem(
                    id=item_id,
                    dataset_id=dataset_id,
                    observed_creative_id=obs.id,
                    score_event_id=pred.id,
                    asset_uri=obs.asset_uri,
                    objective=obs.objective,
                    market=obs.market,
                    placement_family=obs.placement_family,
                    prediction_band=pred_band,
                    observed_band=real_band,
                    error=float(err),
                    performance_snapshot=deepcopy(obs.performance_snapshot or {}),
                    label_policy_version=LABEL_POLICY_VERSION,
                    label_thresholds=deepcopy(label_thresholds),
                    baseline_overall_score=pred.overall_score,
                    diagnostic_scores=deepcopy((pred.lineage or {}).get("diagnostic_scores") or {}),
                )
            )
            synced_count += 1
        dataset.synced_count = synced_count
        dataset.status = "queued_for_calibration" if error_item_count > 0 else "no_data_to_sync"
        dataset.summary = {
            "matched_count": matched_count,
            "error_item_count": error_item_count,
            "correct_item_count": synced_count - error_item_count,
            "excluded_count": len(excluded_observed_ids or []),
            "skipped_not_band_eligible": skipped_not_band_eligible,
            "skipped_heuristic": skipped_heuristic,
            "skipped_insufficient_delivery": skipped_insufficient_delivery,
            "skipped_immature": skipped_immature,
            "deduped_ad_count": _deduped_ad_count,
            "label_policy_version": LABEL_POLICY_VERSION,
        }
        db.commit()

        # 每次同步後重新擬合信心校準層（純 Python、資料量小，直接同步跑，不需要排程）
        try:
            from ..calibration_stats import fit_confidence_calibration
            fit_confidence_calibration(db)
        except Exception as exc:
            logger.warning("[MetaAndromeda] Confidence calibration refit failed: %s", exc)

        return {
            "dataset_id": dataset_id,
            "synced_count": synced_count,
            "error_item_count": error_item_count,
            "status": dataset.status,
            "item_count": synced_count,
            "label_policy_version": LABEL_POLICY_VERSION,
        }
