"""ReviewQueue repository operations."""

from . import _shared

class ReviewQueueMixin:
    @staticmethod
    def _score_to_list_item(score: _shared.MetaAndromedaScoreEvent) -> dict:
        rc = ReviewQueueMixin._safe_json_dict(score.request_context)
        return {
            "score_event_id": score.id,
            "status": score.status,
            "runtime_job_id": score.runtime_job_id,
            "created_at": score.created_at,
            "queued_at": score.queued_at,
            "started_at": score.started_at,
            "completed_at": score.completed_at,
            "failed_at": score.failed_at,
            "updated_at": score.updated_at,
            "asset_uri": score.asset_uri,
            "asset_type": score.asset_type,
            "asset_id": score.asset_id,
            "preview_url": score.preview_url,
            "request_mode": score.request_mode,
            "objective": score.objective,
            "objective_group": _shared.resolve_objective_group(score.objective),
            "placement_family": score.placement_family,
            "market": score.market,
            "prediction_mode": score.prediction_mode,
            "overall_score": score.overall_score,
            "roas_band": score.roas_band,
            "model_version": score.model_version,
            "reviewed": score.reviewed,
            "feedback_count": score.feedback_count,
            "latest_feedback_decision": score.latest_feedback_decision,
            "feature_manifest_id": score.feature_manifest_id,
            "error_message": score.error_message,
            "attempt_count": score.attempt_count,
            "source": rc.get("origin") if rc.get("origin") in ("score_lab", "analytics") else (
                "analytics" if rc.get("observed_creative_id") else "score_lab"
            ),
        }

    @staticmethod
    def _safe_json_dict(value) -> dict:
        """Safely coerce a DB JSON column value to a Python dict."""
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            import json as _json
            try:
                parsed = _json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return {}

    @staticmethod
    def _score_to_detail(score: _shared.MetaAndromedaScoreEvent) -> dict:
        payload = ReviewQueueMixin._score_to_list_item(score)
        payload.update(
            {
                "diagnostic_breakdown": score.diagnostic_breakdown or {},
                "roas_prediction": score.roas_prediction,
                "risk_tags": score.risk_tags or [],
                "top_positive_drivers": score.top_positive_drivers or [],
                "top_negative_drivers": score.top_negative_drivers or [],
                "explanations": score.explanations,
                "lineage": score.lineage or {},
                "request_context": ReviewQueueMixin._safe_json_dict(score.request_context),
            }
        )
        return payload

    def delete_score_event(self, db: _shared.Session, score_event_id: str) -> dict:
        score = db.query(_shared.MetaAndromedaScoreEvent).filter(_shared.MetaAndromedaScoreEvent.id == score_event_id).first()
        if score is None:
            raise KeyError(score_event_id)
        db.query(_shared.MetaAndromedaCalibrationItem).filter(_shared.MetaAndromedaCalibrationItem.score_event_id == score_event_id).delete(synchronize_session=False)
        db.query(_shared.MetaAndromedaFeedbackEvent).filter(_shared.MetaAndromedaFeedbackEvent.score_event_id == score_event_id).delete(synchronize_session=False)
        db.query(_shared.MetaAndromedaWorkerEvent).filter(_shared.MetaAndromedaWorkerEvent.score_event_id == score_event_id).delete(synchronize_session=False)
        db.query(_shared.MetaAndromedaDeadLetter).filter(_shared.MetaAndromedaDeadLetter.score_event_id == score_event_id).delete(synchronize_session=False)
        db.delete(score)
        db.commit()
        return {"deleted_score_event_id": score_event_id}

    def batch_delete_score_events(self, db: _shared.Session, score_event_ids: list[str]) -> dict:
        existing = {
            row.id for row in
            db.query(_shared.MetaAndromedaScoreEvent.id)
            .filter(_shared.MetaAndromedaScoreEvent.id.in_(score_event_ids))
            .all()
        }
        not_found = [sid for sid in score_event_ids if sid not in existing]
        if not existing:
            return {"deleted_count": 0, "deleted_ids": [], "not_found_ids": not_found}
        ids = list(existing)
        db.query(_shared.MetaAndromedaCalibrationItem).filter(_shared.MetaAndromedaCalibrationItem.score_event_id.in_(ids)).delete(synchronize_session=False)
        db.query(_shared.MetaAndromedaFeedbackEvent).filter(_shared.MetaAndromedaFeedbackEvent.score_event_id.in_(ids)).delete(synchronize_session=False)
        db.query(_shared.MetaAndromedaWorkerEvent).filter(_shared.MetaAndromedaWorkerEvent.score_event_id.in_(ids)).delete(synchronize_session=False)
        db.query(_shared.MetaAndromedaDeadLetter).filter(_shared.MetaAndromedaDeadLetter.score_event_id.in_(ids)).delete(synchronize_session=False)
        db.query(_shared.MetaAndromedaScoreEvent).filter(_shared.MetaAndromedaScoreEvent.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return {"deleted_count": len(ids), "deleted_ids": ids, "not_found_ids": not_found}

    def list_review_queue(self, db: _shared.Session, status=None, has_observation=None, roas_band=None, limit=25, page=1, search=None, source=None, scoring_engine=None):
        from sqlalchemy import or_  # noqa: PLC0415
        query = db.query(_shared.MetaAndromedaScoreEvent)
        if status:
            query = query.filter(_shared.MetaAndromedaScoreEvent.status == status)
        if roas_band:
            query = query.filter(_shared.MetaAndromedaScoreEvent.roas_band == roas_band)
        # 用 .as_string()（SQL 層 ->>，取出 text）而非裸的 ["key"]（->，取出 json/jsonb）：
        # PostgreSQL 的 json 型別沒有預設的 btree operator class，裸 JSON 運算式無法建
        # index；文字運算式才能建立可用的 expression index（見下方 migration），這是
        # 「篩選來源就逾時」的根因——status/roas_band/created_at 補了索引後，一旦查詢
        # 條件裡混入這種無法用索引的 JSON 判斷，PostgreSQL 還是得整表掃描評估。
        observed_creative_id = _shared.MetaAndromedaScoreEvent.request_context["observed_creative_id"].as_string()
        if source == "analytics":
            query = query.filter(observed_creative_id.isnot(None))
        elif source == "score_lab":
            query = query.filter(observed_creative_id.is_(None))
        if scoring_engine == "ai":
            query = query.filter(
                _shared.MetaAndromedaScoreEvent.lineage["scoring_mode"].as_string() == "ai"
            )
        elif scoring_engine == "heuristic":
            query = query.filter(
                _shared.MetaAndromedaScoreEvent.lineage["scoring_mode"].as_string() == "heuristic"
            )
        if has_observation is True:
            cal_exists = (
                db.query(_shared.MetaAndromedaCalibrationItem.score_event_id)
                .filter(_shared.MetaAndromedaCalibrationItem.score_event_id == _shared.MetaAndromedaScoreEvent.id)
                .correlate(_shared.MetaAndromedaScoreEvent)
                .exists()
            )
            query = query.filter(or_(cal_exists, observed_creative_id.isnot(None)))
        elif has_observation is False:
            cal_exists = (
                db.query(_shared.MetaAndromedaCalibrationItem.score_event_id)
                .filter(_shared.MetaAndromedaCalibrationItem.score_event_id == _shared.MetaAndromedaScoreEvent.id)
                .correlate(_shared.MetaAndromedaScoreEvent)
                .exists()
            )
            query = query.filter(~cal_exists, observed_creative_id.is_(None))
        if search:
            pat = f"%{search}%"
            ad_name_match = (
                db.query(_shared.MetaAndromedaCalibrationItem.score_event_id)
                .join(_shared.MetaAndromedaObservedCreative, _shared.MetaAndromedaCalibrationItem.observed_creative_id == _shared.MetaAndromedaObservedCreative.id)
                .filter(_shared.MetaAndromedaObservedCreative.ad_name.ilike(pat))
                .filter(_shared.MetaAndromedaCalibrationItem.score_event_id == _shared.MetaAndromedaScoreEvent.id)
                .correlate(_shared.MetaAndromedaScoreEvent)
                .exists()
            )
            query = query.filter(
                or_(
                    _shared.MetaAndromedaScoreEvent.id.ilike(pat),
                    _shared.MetaAndromedaScoreEvent.objective.ilike(pat),
                    _shared.MetaAndromedaScoreEvent.placement_family.ilike(pat),
                    _shared.MetaAndromedaScoreEvent.market.ilike(pat),
                    ad_name_match,
                )
            )
        # 排除 backtest 評分事件——過去是把整個查詢結果撈進 Python 再用
        # list comprehension 濾掉，等於每次翻頁都對全表做一次「隱性全表掃描 +
        # 逐列反序列化 lineage JSON」，score_events 表隨匯入/評分持續增長後
        # 就是審核佇列偶發請求逾時（>30000ms）的主因。改成 SQL 層過濾：
        # 沒有 scoring_purpose 鍵（NULL）視為非 backtest，一併納入。
        scoring_purpose = _shared.MetaAndromedaScoreEvent.lineage["scoring_purpose"].as_string()
        query = query.filter(or_(scoring_purpose.is_(None), scoring_purpose != "backtest"))

        total = query.count()
        page = max(1, page)
        offset = (page - 1) * limit
        total_pages = max(1, _shared.math.ceil(total / limit))
        rows = (
            query.order_by(_shared.MetaAndromedaScoreEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        cal_ids: set[str] = set()
        if rows:
            matched = (
                db.query(_shared.MetaAndromedaCalibrationItem.score_event_id)
                .filter(_shared.MetaAndromedaCalibrationItem.score_event_id.in_([r.id for r in rows]))
                .all()
            )
            cal_ids = {m.score_event_id for m in matched}
        ad_name_map: dict[str, str] = {}
        # score.preview_url 欄位一律是 null（見 _score_to_list_item）。原本無條件用
        # ObservedCreative.media_url（原始 Facebook CDN 網址，會過期）頂替，是backend/
        # worker 分離部署下本地縮圖代理讀不到 worker 寫的檔案時的暫時修法（2026-07-10
        # 事故後新增，方案 C，docs/28）。
        #
        # 2026-08-19 修正：docs/28 方案 D（worker 集中化儲存）已於 2026-07-13 上線為生產
        # 架構，backend 對 filesystem 資產一律代理到 worker（見 router/scoring_assets.py
        # preview_asset()），本地縮圖代理已能正常讀到 worker 寫入的檔案，Score Lab 上傳
        # 的縮圖走的正是同一條代理路徑、也確實穩定可用。原本這裡無條件覆蓋 preview_url，
        # 導致每一筆成效分析匯入的縮圖都繼續指向會過期的 FB CDN 網址，即使該筆已經有永久
        # 存好的 asset_uri 也一樣——改成只在 asset_uri 缺值時才退回 media_url。
        # 註：MetaAndromedaScoreEvent.asset_uri 欄位是 nullable=False，素材下載失敗時
        # import_observed_facebook_ad() 根本不會建立 score event（score_status 停在
        # skipped_no_asset），因此就目前的建立路徑而言不會有 asset_uri 為空的 score
        # event；這裡的判斷純粹是防禦性寫法，避免未來建立路徑改變時縮圖整個讀不到。
        preview_url_map: dict[str, str] = {}
        if cal_ids:
            obs_rows = (
                db.query(
                    _shared.MetaAndromedaCalibrationItem.score_event_id,
                    _shared.MetaAndromedaObservedCreative.ad_name,
                    _shared.MetaAndromedaObservedCreative.media_url,
                )
                .join(_shared.MetaAndromedaObservedCreative, _shared.MetaAndromedaCalibrationItem.observed_creative_id == _shared.MetaAndromedaObservedCreative.id)
                .filter(_shared.MetaAndromedaCalibrationItem.score_event_id.in_(cal_ids))
                .all()
            )
            ad_name_map = {r.score_event_id: r.ad_name for r in obs_rows if r.ad_name}
            preview_url_map = {r.score_event_id: r.media_url for r in obs_rows if r.media_url}
        # 補上直連 ObservedCreative（request_context.observed_creative_id）的 ad_name/media_url
        direct_linked: dict[str, str] = {}  # score_event_id -> observed_creative_id
        for row in rows:
            if row.id in cal_ids:
                continue
            rc = ReviewQueueMixin._safe_json_dict(row.request_context)
            obs_id = rc.get("observed_creative_id")
            if obs_id:
                direct_linked[row.id] = obs_id
        if direct_linked:
            direct_obs = (
                db.query(
                    _shared.MetaAndromedaObservedCreative.id,
                    _shared.MetaAndromedaObservedCreative.ad_name,
                    _shared.MetaAndromedaObservedCreative.media_url,
                )
                .filter(_shared.MetaAndromedaObservedCreative.id.in_(direct_linked.values()))
                .all()
            )
            obs_ad_name = {o.id: o.ad_name for o in direct_obs if o.ad_name}
            obs_media_url = {o.id: o.media_url for o in direct_obs if o.media_url}
            for evt_id, obs_id in direct_linked.items():
                if evt_id not in ad_name_map and obs_id in obs_ad_name:
                    ad_name_map[evt_id] = obs_ad_name[obs_id]
                if evt_id not in preview_url_map and obs_id in obs_media_url:
                    preview_url_map[evt_id] = obs_media_url[obs_id]
        items = []
        for row in rows:
            rc = ReviewQueueMixin._safe_json_dict(row.request_context)
            item = self._score_to_list_item(row)
            item["has_observation"] = (row.id in cal_ids) or bool(rc.get("observed_creative_id"))
            item["ad_name"] = ad_name_map.get(row.id)
            if not item.get("preview_url") and not item.get("asset_uri"):
                item["preview_url"] = preview_url_map.get(row.id)
            items.append(item)
        return {
            "items": items,
            "summary": {
                "total": total,
                "page": page,
                "total_pages": total_pages,
                "page_size": limit,
                "status_filter": status,
                "roas_band_filter": roas_band,
                "has_observation_filter": has_observation,
            },
        }

    def get_review_queue_detail(self, db: _shared.Session, score_event_id: str):
        row = db.query(_shared.MetaAndromedaScoreEvent).filter(_shared.MetaAndromedaScoreEvent.id == score_event_id).first()
        if row is None:
            raise KeyError(score_event_id)
        detail = self._score_to_detail(row)
        cal_item = (
            db.query(_shared.MetaAndromedaCalibrationItem)
            .filter(_shared.MetaAndromedaCalibrationItem.score_event_id == score_event_id)
            .first()
        )
        if cal_item:
            obs = (
                db.query(_shared.MetaAndromedaObservedCreative)
                .filter(_shared.MetaAndromedaObservedCreative.id == cal_item.observed_creative_id)
                .first()
            )
            detail["observation"] = {
                "prediction_band": cal_item.prediction_band,
                "observed_band": cal_item.observed_band,
                "error": cal_item.error,
                "performance_snapshot": _shared.deepcopy(cal_item.performance_snapshot or {}),
                "ad_name": obs.ad_name if obs else None,
                "ad_id": obs.ad_id if obs else None,
                "observation_window_kind": obs.observation_window_kind if obs else None,
                "observation_window_start": obs.observation_window_start if obs else None,
                "observation_window_end": obs.observation_window_end if obs else None,
            }
        else:
            # 若此 ScoreEvent 由成效分析匯入自動建立，request_context 會帶有 observed_creative_id
            # 直接從 ObservedCreative 取得實際成效，不必等 CalibrationItem 同步
            rc = self._safe_json_dict(row.request_context)
            linked_obs_id = rc.get("observed_creative_id")
            obs = None
            if linked_obs_id:
                obs = (
                    db.query(_shared.MetaAndromedaObservedCreative)
                    .filter(_shared.MetaAndromedaObservedCreative.id == linked_obs_id)
                    .first()
                )
            if obs and obs.performance_snapshot and float((obs.performance_snapshot or {}).get("spend", 0) or 0) > 0:
                roas_eligible = bool((row.roas_prediction or {}).get("eligible", True))
                pred_band = row.roas_band if roas_eligible else None
                # 單筆查詢無法計算動態百分位門檻，改用該 scope 已持久化的門檻（同 compute_label_thresholds
                # 在樣本不足時的 fallback 順序），避免 NON_ROAS_GROUPS（曝光/點擊型）廣告因 ctr/cpc 門檻
                # 缺值而被 label_observed_band() 一律判為 low
                label_thresholds = _shared.compute_label_thresholds(
                    [obs],
                    db=db,
                    scope_key=obs.source_account_id or "global",
                    window_kind=obs.observation_window_kind,
                )
                real_band, _ = _shared.label_observed_band(obs.objective, obs.performance_snapshot, label_thresholds)
                _band_score = {"low": 1, "mid": 2, "high": 3}
                err = float(abs(_band_score.get(pred_band, 1) - _band_score.get(real_band, 1))) if pred_band else None
                detail["observation"] = {
                    "prediction_band": pred_band,
                    "observed_band": real_band,
                    "error": err,
                    "performance_snapshot": _shared.deepcopy(obs.performance_snapshot or {}),
                    "ad_name": obs.ad_name,
                    "ad_id": obs.ad_id,
                    "observation_window_kind": obs.observation_window_kind,
                    "observation_window_start": obs.observation_window_start,
                    "observation_window_end": obs.observation_window_end,
                }
            else:
                detail["observation"] = None

        # 2026-08-19 修正（見上面 list_review_queue 的完整說明）：只在 asset_uri 缺值時
        # 才退回 ObservedCreative.media_url（原始 Facebook CDN 網址，會過期）當備援
        # preview_url，asset_uri 存在時交由本地縮圖代理（已走 worker 集中化儲存）處理。
        if obs and obs.media_url and not detail.get("preview_url") and not detail.get("asset_uri"):
            detail["preview_url"] = obs.media_url

        # 三方對照（人 vs 模型 vs 市場）：把 reviewer 的歷史回饋跟上面的 AI 預測/市場實績
        # 放在同一個 detail 裡，才看得出 reviewer 說的 hook_soft 之類的判斷是否真的準
        feedback_rows = (
            db.query(_shared.MetaAndromedaFeedbackEvent)
            .filter(_shared.MetaAndromedaFeedbackEvent.score_event_id == score_event_id)
            .order_by(_shared.MetaAndromedaFeedbackEvent.created_at.asc())
            .all()
        )
        detail["feedback_history"] = [
            {
                "feedback_event_id": item.id,
                "reviewer_id": item.reviewer_id,
                "decision": item.decision,
                "reason_codes": item.reason_codes or [],
                "comment": item.comment,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in feedback_rows
        ]
        return detail
