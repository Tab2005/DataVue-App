"""Drift repository operations."""

from ._shared import *  # noqa: F401,F403
from ._stats import *  # noqa: F401,F403
from .release_metrics import *  # noqa: F401,F403

def _check_promoted_profile_degradation(db, accuracy: float, spearman_r: float, drift_status: str) -> None:
    """Compare this drift report's accuracy/ρ against the currently promoted
    profile's promotion_baseline (captured from its holdout backtest at promote
    time). Two consecutive degraded periods auto-demotes the profile so a bad
    calibration doesn't silently stay live — this is the "驗證" step the closed
    loop was missing (promote used to be one-way with no feedback)."""
    if drift_status in ("insufficient_data", "insufficient_sample"):
        return  # 樣本不足時 accuracy/ρ 本身不可信，不能拿來判定劣化

    promoted = (
        db.query(MetaAndromedaScoringProfile)
        .filter(MetaAndromedaScoringProfile.is_promoted == True)  # noqa: E712
        .first()
    )
    if promoted is None or not promoted.promotion_baseline:
        return

    baseline_accuracy = promoted.promotion_baseline.get("accuracy")
    baseline_spearman = promoted.promotion_baseline.get("spearman_r")
    if baseline_accuracy is None or baseline_spearman is None:
        return

    degraded = accuracy < baseline_accuracy and spearman_r < baseline_spearman
    if not degraded:
        if promoted.consecutive_degraded_periods:
            promoted.consecutive_degraded_periods = 0
            db.add(promoted)
            db.commit()
        return

    promoted.consecutive_degraded_periods = (promoted.consecutive_degraded_periods or 0) + 1
    if promoted.consecutive_degraded_periods >= 2:
        promoted.is_promoted = False
        promoted.demoted_at = datetime.now(timezone.utc)
        promoted.demoted_reason = (
            f"連續 {promoted.consecutive_degraded_periods} 期表現劣於 promote 前基線"
            f"（baseline accuracy={baseline_accuracy:.3f}/ρ={baseline_spearman:.3f}，"
            f"本期 accuracy={accuracy:.3f}/ρ={spearman_r:.3f}）"
        )
        logger.warning(
            "[MetaAndromeda] Auto-demoted scoring profile '%s': %s",
            promoted.profile_name,
            promoted.demoted_reason,
        )
        db.add(promoted)
        db.commit()
        from ..runtime import invalidate_prompt_cache
        invalidate_prompt_cache()
    else:
        db.add(promoted)
        db.commit()

class DriftMixin:
    @staticmethod
    def _drift_report_to_dict(report: MetaAndromedaDriftReport) -> dict:
        return {
            "drift_report_id": report.id,
            "window_kind": report.window_kind,
            "drift_status": report.drift_status,
            "summary": report.summary,
            "severity": report.severity,
            "triggered_by": report.triggered_by,
            "note": report.note,
            "report_payload": deepcopy(report.report_payload or {}),
            "created_at": report.created_at.isoformat() if report.created_at else None,
        }

    def create_drift_report(
        self,
        db: Session,
        window_kind: str,
        triggered_by: str | None = None,
        note: str | None = None,
        since: str | None = None,
        until: str | None = None,
        account_id: str | None = None,
    ):
        # 1. 撈取該窗口的所有 Observed Creative (改用區間重疊比對，避免因時區或邊界跨天導致資料遺漏)
        if window_kind == "custom" and since and until:
            range_str = f"[{since} ~ {until}]"
            note = f"{note} {range_str}" if note else range_str
            q = db.query(MetaAndromedaObservedCreative).filter(
                MetaAndromedaObservedCreative.observation_window_end >= since,
                MetaAndromedaObservedCreative.observation_window_start <= until,
            )
        else:
            q = db.query(MetaAndromedaObservedCreative).filter(
                MetaAndromedaObservedCreative.observation_window_kind == window_kind,
            )
        if account_id:
            q = q.filter(MetaAndromedaObservedCreative.source_account_id == account_id)
        # 排除 spend=0 的記錄（未實際投放），避免污染 Spearman 相關計算
        observed_list = [
            obs for obs in q.all()
            if float((obs.performance_snapshot or {}).get("spend", 0) or 0) > 0
        ]
        # 同一 ad_id 若因 custom 窗口區間重疊比對而重複出現，只保留 spend 最大的一筆，
        # 避免同一素材的成效被重複計入統計
        observed_list, deduped_ad_count = _dedupe_observed_by_ad_id(observed_list)

        matched_pairs = []
        correct_count = 0
        total_error = 0.0

        # 區間映射字典
        band_score = {"low": 1, "mid": 2, "high": 3}

        # 動態標籤門檻（ROAS / CTR / CPC / CVR / CPL）：與 sync_calibration_dataset 共用同一套計算方式，
        # 確保同一批 ObservedCreative 在 drift 與校準兩處算出一致的 observed_band；樣本不足時
        # 沿用同 scope_key/window_kind 上一期已持久化的門檻，而非每次都退回全域固定值
        label_policy_scope = account_id or "global"
        label_thresholds = compute_label_thresholds(
            observed_list, db=db, scope_key=label_policy_scope, window_kind=window_kind
        )
        persist_label_policy(db, label_policy_scope, window_kind, label_thresholds)

        # 2. 逐筆進行 Prediction 匹配與比對
        heuristic_fallback_count = 0
        for obs in observed_list:
            pred = match_observed_to_prediction(db, obs)
            if not pred:
                continue

            # 過濾 heuristic fallback 分數：這是規則加減分而非模型預測，與 AI 分數混算會
            # 稀釋/扭曲 accuracy 與 Spearman ρ。獨立統計占比，作為評分服務健康度指標。
            pred_lineage = pred.lineage or {}
            if pred_lineage.get("scoring_purpose") == "backtest":
                continue
            if pred_lineage.get("scoring_mode") == "heuristic":
                heuristic_fallback_count += 1
                continue

            # 提取真實成效 Band（依 objective 路由至對應指標，使用本批次動態門檻）
            real_band, label_detail = label_observed_band(
                obs.objective,
                obs.performance_snapshot,
                label_thresholds,
            )
            real_roas = obs.performance_snapshot.get("roas", 0.0) if obs.performance_snapshot else 0.0

            # 非轉換/lead 廣告（roas_band=null 為正確設計）不應被強制視為 "low" 來計算 accuracy/MAE，
            # 否則模型「正確地不出 band」會被誤記為預測錯誤，污染校準集與健康度判斷
            pred_roas_eligible = (pred.roas_prediction or {}).get("eligible")
            if pred_roas_eligible is None:
                pred_roas_eligible = resolve_objective_group(obs.objective) not in NON_ROAS_GROUPS
            pred_band = pred.roas_band if pred_roas_eligible else None
            band_eligible = pred_band is not None

            # 曝光/觀測期間門檻：小曝光廣告的 ROAS/CTR 噪音極大，觀測期間過短同樣不可靠，
            # 不該與大預算、足夠觀測天數的廣告同權重納入 accuracy
            impressions = int((obs.performance_snapshot or {}).get("impressions", 0) or 0)
            sufficient_delivery = impressions >= MIN_IMPRESSIONS_FOR_ACCURACY
            window_days = _window_days(obs.observation_window_start, obs.observation_window_end)
            immature = window_days is not None and window_days < MIN_OBSERVATION_WINDOW_DAYS
            accuracy_eligible = band_eligible and sufficient_delivery and not immature

            if accuracy_eligible:
                is_match = (pred_band == real_band)
                if is_match:
                    correct_count += 1
                err = abs(band_score.get(pred_band, 1) - band_score.get(real_band, 1))
                total_error += err
            else:
                err = None

            real_spend = float((obs.performance_snapshot or {}).get("spend", 0) or 0)
            request_context = pred.request_context or {}
            origin = request_context.get("origin") if request_context.get("origin") in ("score_lab", "analytics") else "unknown"
            matched_pairs.append({
                "id": obs.id,
                "ad_id": obs.ad_id,
                "ad_name": obs.ad_name,
                "prediction_band": pred_band,
                "band_eligible": band_eligible,
                "sufficient_delivery": sufficient_delivery,
                "immature": immature,
                "accuracy_eligible": accuracy_eligible,
                "impressions": impressions,
                "observed_band": real_band,
                "real_roas": real_roas,
                "real_spend": real_spend,
                "overall_score": pred.overall_score,
                "primary_metric": label_detail["metric"],
                "primary_metric_value": label_detail["value"],
                "error": err,
                "label_policy_version": LABEL_POLICY_VERSION,
                "label_metric": label_detail["metric"],
                "origin": origin,
                "prompt_profile_used": pred_lineage.get("prompt_profile_used"),
            })

        # 3. 計算統計指標（accuracy/MAE 只計入 accuracy_eligible 的項目：band 有效 + 曝光/觀測期間足夠；
        # Spearman 仍使用全部 matched_pairs，樣本量比曝光門檻更重要）
        total_matched = len(matched_pairs)
        band_matched_pairs = [p for p in matched_pairs if p["accuracy_eligible"]]
        total_band_matched = len(band_matched_pairs)
        insufficient_delivery_total = sum(1 for p in matched_pairs if p["band_eligible"] and not p["sufficient_delivery"])
        immature_total = sum(1 for p in matched_pairs if p["immature"])
        accuracy = correct_count / total_band_matched if total_band_matched > 0 else 0.0
        mae = total_error / total_band_matched if total_band_matched > 0 else 0.0
        calibration_candidate_total = sum(1 for item in band_matched_pairs if item["error"] > 0)

        # origin 切片：投放前預測（score_lab）vs 事後補評（analytics），accuracy 分開看才能看出
        # 產品宣稱的「投放前預測」能力，事後補評的素材模型並沒有看過成效
        def _origin_accuracy(origin_key: str) -> dict:
            subset = [p for p in band_matched_pairs if p["origin"] == origin_key]
            if not subset:
                return {"total": 0, "accuracy": None}
            correct = sum(1 for p in subset if p["prediction_band"] == p["observed_band"])
            return {"total": len(subset), "accuracy": round(correct / len(subset), 4)}

        origin_breakdown = {
            "score_lab": _origin_accuracy("score_lab"),
            "analytics": _origin_accuracy("analytics"),
            "unknown": _origin_accuracy("unknown"),
        }

        # Spearman ρ：AI overall_score 排名 vs 主指標排名的相關性
        # 以各廣告的 primary_metric 判斷帳戶類型（purchase→ROAS, lead→CVR/CPL, 其他→CPA）
        # 混合 objective 帳戶以最多筆的指標群組為主
        _metric_counter = Counter(
            p["primary_metric"] for p in matched_pairs
            if p.get("primary_metric") and p.get("primary_metric_value") is not None
        )
        dominant_metric = _metric_counter.most_common(1)[0][0] if _metric_counter else "roas"
        metric_distribution = dict(_metric_counter)

        _eligible = [
            p for p in matched_pairs
            if p.get("primary_metric") == dominant_metric
            and p.get("primary_metric_value") is not None
            and p.get("overall_score") is not None
        ]
        _scores = [float(p["overall_score"])        for p in _eligible]
        _perf   = [float(p["primary_metric_value"]) for p in _eligible]
        spearman_r = _spearman_r(_scores, _perf) if len(_scores) >= 3 else 0.0

        # spend 加權版本：大預算素材的排序對齊更重要；輔助指標，不取代主判據 spearman_r
        _spends = [float(p["real_spend"]) for p in _eligible]
        spearman_r_spend_weighted = (
            _spearman_r_weighted(_scores, _perf, _spends) if len(_scores) >= 3 else 0.0
        )

        # 主指標分布（用於象限判定的 P50 基準）
        _perf_all = sorted(
            float(p["primary_metric_value"]) for p in matched_pairs
            if p.get("primary_metric") == dominant_metric
            and p.get("primary_metric_value") is not None
        )
        perf_median = _perf_all[len(_perf_all) // 2] if _perf_all else 0.0
        perf_std = statistics.stdev(_perf_all) if len(_perf_all) >= 2 else 0.0

        # perf_is_high 應該回答「這期表現是否比上期好」，而非「中位數是否 >= 平均數」
        # （後者只反映分布偏態，右偏分布會永遠判 False，跟表現好壞無關）。
        # 優先與同帳戶上一期 perf_median 比較；沒有基準時才退回舊的分布判定法。
        _prior_report_query = db.query(MetaAndromedaDriftReport).filter(
            MetaAndromedaDriftReport.window_kind == window_kind,
            MetaAndromedaDriftReport.drift_status != "insufficient_data",
        )
        if account_id:
            _prior_report_query = _prior_report_query.filter(
                MetaAndromedaDriftReport.report_payload["account_id"].as_string() == account_id
            )
        _prior_report = _prior_report_query.order_by(MetaAndromedaDriftReport.created_at.desc()).first()
        _prior_perf_median = None
        if _prior_report and _prior_report.report_payload:
            _prior_perf_median = _prior_report.report_payload.get("perf_median")

        if _prior_perf_median is not None:
            perf_is_high = perf_median >= _prior_perf_median
            perf_baseline_method = "prior_period_median"
        else:
            perf_is_high = perf_median >= (sum(_perf_all) / len(_perf_all)) if _perf_all else False
            perf_baseline_method = "distribution_mean_fallback"

        period_diagnosis = _classify_period_state(spearman_r, perf_is_high, dominant_metric)
        metric_label = _METRIC_LABEL.get(dominant_metric, dominant_metric.upper())

        # 4. 判定漂移健康度（主判據：Spearman ρ；輔助資訊：accuracy/MAE）
        # ρ 門檻本身無檢定支撐：n 太小時無論 ρ 高低都不具統計意義，一律標記
        # insufficient_sample，不允許判定為 healthy/warning/drifted 誤導營運決策
        n_spearman = len(_scores)
        MIN_SAMPLES_FOR_DRIFT_VERDICT = 15
        if total_matched < 5:
            drift_status = "insufficient_data"
            severity = "info"

            total_observed = len(observed_list)
            obs_with_asset = sum(1 for obs in observed_list if obs.asset_id or obs.asset_uri)
            total_completed_scores = db.query(MetaAndromedaScoreEvent).filter(
                MetaAndromedaScoreEvent.status == "completed"
            ).count()
            total_failed_scores = db.query(MetaAndromedaScoreEvent).filter(
                MetaAndromedaScoreEvent.status == "failed"
            ).count()
            total_pending_scores = db.query(MetaAndromedaScoreEvent).filter(
                MetaAndromedaScoreEvent.status.in_(["queued", "started", "processing"])
            ).count()

            summary = (
                f"數據量不足 (僅成功匹配 {total_matched} 筆)。"
                f"診斷：區間內匯入廣告 {total_observed} 筆，"
                f"其中 {obs_with_asset} 筆具有素材檔案。"
                f"Prediction / ScoreEvent 累積統計：{total_completed_scores} 筆已完成，"
                f"{total_failed_scores} 筆失敗，{total_pending_scores} 筆處理/排隊中。"
                "請確認素材是否已在評分工作台完成評估，或確認背景任務與 AI 服務是否正常運作。"
            )
        elif n_spearman < MIN_SAMPLES_FOR_DRIFT_VERDICT:
            drift_status = "insufficient_sample"
            severity = "info"
            summary = (
                f"已匹配 {total_matched} 筆，但用於排名相關性計算的樣本僅 {n_spearman} 筆"
                f"（< {MIN_SAMPLES_FOR_DRIFT_VERDICT}），ρ={spearman_r:.3f} 統計上不具判定意義，"
                "暫不判定 healthy/warning/drifted，僅供參考。建議累積更多觀測樣本後再檢視。"
            )
        elif spearman_r >= 0.30:
            drift_status = "healthy"
            severity = "info"
            summary = (
                f"模型排名能力穩定 (ρ={spearman_r:.3f}, Accuracy: {accuracy:.1%})，"
                f"創意評分與實際 {metric_label} 排名具正相關，"
                f"投放狀態：{period_diagnosis['label']}。"
            )
        elif spearman_r >= 0.10:
            drift_status = "warning"
            severity = "medium"
            summary = (
                f"模型排名能力偏弱 (ρ={spearman_r:.3f}, Accuracy: {accuracy:.1%})，"
                f"創意評分與 {metric_label} 排名相關性不足，"
                f"投放狀態：{period_diagnosis['label']}。請密切關注。"
            )
        else:
            drift_status = "drifted"
            severity = "high"
            summary = (
                f"模型排名能力已失效 (ρ={spearman_r:.3f}, Accuracy: {accuracy:.1%})，"
                f"創意評分無法有效預測相對 {metric_label} 表現，建議進行資料校準。"
            )
    
        # 5. 寫入資料庫
        report = MetaAndromedaDriftReport(
            window_kind=window_kind,
            drift_status=drift_status,
            summary=summary,
            severity=severity,
            triggered_by=triggered_by,
            note=note,
            report_payload={
                "total_observed": len(observed_list),
                "total_matched": total_matched,
                "total_band_matched": total_band_matched,
                "deduped_ad_count": deduped_ad_count,
                "insufficient_delivery_total": insufficient_delivery_total,
                "immature_total": immature_total,
                "min_impressions_for_accuracy": MIN_IMPRESSIONS_FOR_ACCURACY,
                "min_observation_window_days": MIN_OBSERVATION_WINDOW_DAYS,
                "match_rate": round(total_matched / len(observed_list), 4) if observed_list else 0.0,
                "obs_with_asset": sum(1 for obs in observed_list if obs.asset_id or obs.asset_uri),
                "total_completed_scores": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status == "completed").count(),
                "total_failed_scores": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status == "failed").count(),
                "total_pending_scores": db.query(MetaAndromedaScoreEvent).filter(MetaAndromedaScoreEvent.status.in_(["queued", "started", "processing"])).count(),
                "accuracy": round(accuracy, 4),
                "mae": round(mae, 4),
                "spearman_r": round(spearman_r, 4),
                "spearman_r_spend_weighted": round(spearman_r_spend_weighted, 4),
                "spearman_sample_count": n_spearman,
                "dominant_metric": dominant_metric,
                "metric_distribution": metric_distribution,
                "perf_median": round(perf_median, 4),
                "perf_std": round(perf_std, 4),
                "perf_baseline_method": perf_baseline_method,
                "period_diagnosis": period_diagnosis,
                "calibration_candidate_total": calibration_candidate_total,
                "label_policy_version": LABEL_POLICY_VERSION,
                "heuristic_fallback_total": heuristic_fallback_count,
                "heuristic_fallback_rate": (
                    round(heuristic_fallback_count / (total_matched + heuristic_fallback_count), 4)
                    if (total_matched + heuristic_fallback_count) else 0.0
                ),
                "origin_breakdown": origin_breakdown,
                "roas_band_thresholds": {
                    "low_below": round(label_thresholds["roas"]["thresholds"][0], 2) if label_thresholds["roas"]["thresholds"] else None,
                    "high_above": round(label_thresholds["roas"]["thresholds"][1], 2) if label_thresholds["roas"]["thresholds"] else None,
                    "method": label_thresholds["roas"]["method"],
                    "sample_count": label_thresholds["roas"]["sample_count"],
                },
                "ctr_band_thresholds": {
                    "low_below": round(label_thresholds["ctr"]["thresholds"][0], 4) if label_thresholds["ctr"]["thresholds"] else None,
                    "high_above": round(label_thresholds["ctr"]["thresholds"][1], 4) if label_thresholds["ctr"]["thresholds"] else None,
                    "method": label_thresholds["ctr"]["method"],
                    "sample_count": label_thresholds["ctr"]["sample_count"],
                },
                "cpc_band_thresholds": {
                    "low_above": round(label_thresholds["cpc"]["thresholds"][0], 2) if label_thresholds["cpc"]["thresholds"] else None,
                    "high_below": round(label_thresholds["cpc"]["thresholds"][1], 2) if label_thresholds["cpc"]["thresholds"] else None,
                    "method": label_thresholds["cpc"]["method"],
                    "sample_count": label_thresholds["cpc"]["sample_count"],
                },
                "cvr_band_thresholds": {
                    "low_below": round(label_thresholds["cvr"]["thresholds"][0], 4) if label_thresholds["cvr"]["thresholds"] else None,
                    "high_above": round(label_thresholds["cvr"]["thresholds"][1], 4) if label_thresholds["cvr"]["thresholds"] else None,
                    "method": label_thresholds["cvr"]["method"],
                    "sample_count": label_thresholds["cvr"]["sample_count"],
                },
                "cpl_band_thresholds": {
                    "low_above": round(label_thresholds["cpl"]["thresholds"][0], 2) if label_thresholds["cpl"]["thresholds"] else None,
                    "high_below": round(label_thresholds["cpl"]["thresholds"][1], 2) if label_thresholds["cpl"]["thresholds"] else None,
                    "method": label_thresholds["cpl"]["method"],
                    "sample_count": label_thresholds["cpl"]["sample_count"],
                },
                "traffic_ad_total": label_thresholds["traffic_total"],
                "lead_ad_total": label_thresholds["lead_total"],
                "lead_ad_with_metric_total": label_thresholds["lead_with_metric_total"],
                "lead_metric_coverage": (
                    round(label_thresholds["lead_with_metric_total"] / label_thresholds["lead_total"], 4)
                    if label_thresholds["lead_total"] else None
                ),
                "matched_details": matched_pairs,
                "since": since,
                "until": until,
                "account_id": account_id,
            }
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # Promote 後追蹤：與這個 promoted profile 的 promote 前基線比較，連續劣化自動降級
        _check_promoted_profile_degradation(db, accuracy, spearman_r, drift_status)

        return self._drift_report_to_dict(report)
