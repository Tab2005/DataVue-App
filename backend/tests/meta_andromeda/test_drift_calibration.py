from .conftest import *  # noqa: F401,F403


@pytest.mark.unit
def test_meta_andromeda_drift_trigger_creates_report_and_alert(meta_andromeda_access, db):
    repository.get_review_queue_detail(db, "ma_evt_20260605_003")
    repository.mark_score_failed(db, "ma_evt_20260605_003", "runtime_failure")
    repository.create_dead_letter(
        db,
        score_event_id="ma_evt_20260605_003",
        queue_host="redis_stream",
        runtime_job_id="job_failure_001",
        failure_stage="runtime",
        attempt_count=1,
        final_error_message="runtime_failure",
        dead_letter_payload={"source": "test"},
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "manual drift review"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["window_kind"] == "last_7d"
    assert payload["drift_status"] == "insufficient_data"

    monitoring = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary").json()
    assert any(report["window_kind"] == "last_7d" for report in monitoring["latest_drift_reports"])


@pytest.mark.unit
def test_meta_andromeda_drift_accuracy_and_mae_calculation(meta_andromeda_access, db):
    from database.models.meta_andromeda import MetaAndromedaObservedCreative, MetaAndromedaScoreEvent
    
    # 清除現有的相關資料，確保測試環境純淨
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.query(MetaAndromedaBacktestRun).delete()
    db.commit()

    # 1. 建立 5 筆預測與真實績效完全吻合的 healthy 數據
    # 區間切分: low < 1.5, 1.5 <= mid < 3.5, high >= 3.5
    test_cases = [
        {"uri": "uri_1", "pred_band": "high", "real_roas": 5.0},  # high == high
        {"uri": "uri_2", "pred_band": "mid", "real_roas": 2.0},   # mid == mid
        {"uri": "uri_3", "pred_band": "low", "real_roas": 0.5},   # low == low
        {"uri": "uri_4", "pred_band": "high", "real_roas": 4.0},  # high == high
        {"uri": "uri_5", "pred_band": "mid", "real_roas": 3.0},   # mid == mid
    ]

    for idx, tc in enumerate(test_cases):
        # 建立 Observed Creative
        obs = MetaAndromedaObservedCreative(
            id=f"test_obs_{idx}",
            asset_uri=tc["uri"],
            source_platform="facebook_ads",
            source_account_id="act_12345",
            ad_id=f"ad_{idx}",
            placement_family="feed",
            market="TW",
            media_type="image",
            observation_window_kind="last_7d",
            observation_window_start="2026-06-09",
            observation_window_end="2026-06-16",
            source_fetched_at="2026-06-16T12:00:00Z",
            performance_snapshot={"roas": tc["real_roas"]}
        )
        db.add(obs)

        # 建立對應的 completed ScoreEvent
        score_evt = MetaAndromedaScoreEvent(
            id=f"test_score_{idx}",
            status="completed",
            asset_uri=tc["uri"],
            asset_type="image",
            request_mode="manual",
            objective="CONVERSIONS",
            placement_family="feed",
            market="TW",
            roas_band=tc["pred_band"]
        )
        db.add(score_evt)

    db.commit()

    # 觸發 Drift 診斷
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "healthy check"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["drift_status"] == "healthy"
    assert payload["report_payload"]["accuracy"] == 1.0
    assert payload["report_payload"]["mae"] == 0.0

    # 2. 修改為預估與實際嚴重偏離的 drifted 數據
    # 5 筆預估都是 high (3)，實際均為 low (1, ROAS=0.5)
    db.query(MetaAndromedaScoreEvent).update({"roas_band": "high"})
    db.commit()
    
    # 重新觸發
    response2 = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "drifted check"},
    )
    assert response2.status_code == 201
    payload2 = response2.json()
    assert payload2["drift_status"] == "drifted"
    assert payload2["report_payload"]["accuracy"] == 0.4
    assert payload2["report_payload"]["mae"] == 0.8


@pytest.mark.unit
def test_meta_andromeda_drift_matching_by_checksum(meta_andromeda_access, db):
    from database.models.meta_andromeda import (
        MetaAndromedaAsset,
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent
    )
    
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.query(MetaAndromedaBacktestRun).delete()
    db.query(MetaAndromedaAsset).delete()
    db.commit()

    checksums = ["sum_1", "sum_2", "sum_3", "sum_4", "sum_5"]
    
    for idx, cs in enumerate(checksums):
        asset_obs = MetaAndromedaAsset(
            id=f"ast_obs_{idx}",
            asset_uri=f"storage://meta-andromeda/obs_{idx}.png",
            storage_backend="filesystem",
            storage_key=f"obs_{idx}.png",
            asset_type="image",
            source_filename=f"obs_{idx}.png",
            checksum_sha256=cs,
        )
        asset_pred = MetaAndromedaAsset(
            id=f"ast_pred_{idx}",
            asset_uri=f"storage://meta-andromeda/pred_{idx}.png",
            storage_backend="filesystem",
            storage_key=f"pred_{idx}.png",
            asset_type="image",
            source_filename=f"pred_{idx}.png",
            checksum_sha256=cs,
        )
        db.add(asset_obs)
        db.add(asset_pred)
        db.flush()

        obs = MetaAndromedaObservedCreative(
            id=f"test_obs_cs_{idx}",
            asset_id=asset_obs.id,
            asset_uri=asset_obs.asset_uri,
            source_platform="facebook_ads",
            source_account_id="act_12345",
            ad_id=f"ad_cs_{idx}",
            placement_family="feed",
            market="TW",
            media_type="image",
            observation_window_kind="last_7d",
            observation_window_start="2026-06-09",
            observation_window_end="2026-06-16",
            source_fetched_at="2026-06-16T12:00:00Z",
            performance_snapshot={"roas": 2.0}
        )
        db.add(obs)

        score_evt = MetaAndromedaScoreEvent(
            id=f"test_score_cs_{idx}",
            status="completed",
            asset_id=asset_pred.id,
            asset_uri=asset_pred.asset_uri,
            asset_type="image",
            request_mode="manual",
            objective="CONVERSIONS",
            placement_family="feed",
            market="TW",
            roas_band="mid"
        )
        db.add(score_evt)

    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "checksum match check"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["drift_status"] == "healthy"
    assert payload["report_payload"]["total_matched"] == 5
    assert payload["report_payload"]["accuracy"] == 1.0


@pytest.mark.unit
def test_meta_andromeda_drift_trigger_does_not_persist_mock_scores(meta_andromeda_access, db):
    from database.models.meta_andromeda import MetaAndromedaObservedCreative, MetaAndromedaScoreEvent

    _clear_meta_andromeda_operational_data(db)

    for idx in range(5):
        db.add(
            MetaAndromedaObservedCreative(
                id=f"no_pred_obs_{idx}",
                asset_uri=f"storage://meta-andromeda/uploads/no-pred-{idx}.png",
                source_platform="facebook_ads",
                source_account_id="act_999",
                ad_id=f"ad_no_pred_{idx}",
                placement_family="feed",
                market="TW",
                media_type="image",
                observation_window_kind="last_7d",
                observation_window_start="2026-06-09",
                observation_window_end="2026-06-16",
                source_fetched_at="2026-06-16T12:00:00Z",
                performance_snapshot={"roas": 1.2 + idx * 0.1},
                lineage={"source": "unit_test"},
            )
        )
    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d", "note": "missing predictions should not backfill"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["drift_status"] == "insufficient_data"
    assert db.query(MetaAndromedaScoreEvent).count() == 0


@pytest.mark.unit
def test_sync_calibration_dataset_endpoint(meta_andromeda_access, db):
    from database.models.meta_andromeda import (
        MetaAndromedaCalibrationDataset,
        MetaAndromedaCalibrationItem,
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent,
    )
    
    # 確保資料庫純淨
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.query(MetaAndromedaBacktestRun).delete()
    db.commit()

    # 建立一個有偏差的配對 (pred: high vs real: low)
    obs = MetaAndromedaObservedCreative(
        id="obs_to_calibrate",
        asset_uri="cal_uri_1",
        source_platform="facebook_ads",
        source_account_id="act_12345",
        ad_id="ad_cal_1",
        placement_family="feed",
        market="TW",
        media_type="image",
        observation_window_kind="last_7d",
        observation_window_start="2026-06-09",
        observation_window_end="2026-06-16",
        source_fetched_at="2026-06-16T12:00:00Z",
        performance_snapshot={"roas": 0.5}  # low (1)
    )
    db.add(obs)

    score_evt = MetaAndromedaScoreEvent(
        id="score_to_calibrate",
        status="completed",
        asset_uri="cal_uri_1",
        asset_type="image",
        request_mode="manual",
        objective="CONVERSIONS",
        placement_family="feed",
        market="TW",
        roas_band="high"  # high (3), err = abs(3 - 1) = 2 > 0
    )
    db.add(score_evt)
    db.commit()

    # 呼叫 API 同步
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/calibration/sync",
        json={"window_kind": "last_7d", "excluded_observed_ids": []}
    )
    assert response.status_code == 201
    payload = response.json()
    assert "dataset_id" in payload
    assert payload["synced_count"] == 1
    assert payload["item_count"] == 1
    assert payload["status"] == "queued_for_calibration"
    assert payload["label_policy_version"] == "ma_label_policy_v2"

    # 檢查資料庫中 Observed Creative 的 lineage["calibration"] 是否被寫入
    obs_db = db.query(MetaAndromedaObservedCreative).filter(MetaAndromedaObservedCreative.id == "obs_to_calibrate").first()
    assert obs_db.lineage["calibration"]["dataset_id"] == payload["dataset_id"]
    assert obs_db.lineage["calibration"]["error"] == 2
    assert obs_db.lineage["calibration"]["label_policy_version"] == "ma_label_policy_v2"

    dataset = db.query(MetaAndromedaCalibrationDataset).filter(MetaAndromedaCalibrationDataset.id == payload["dataset_id"]).one()
    item = db.query(MetaAndromedaCalibrationItem).filter(MetaAndromedaCalibrationItem.dataset_id == payload["dataset_id"]).one()
    assert dataset.synced_count == 1
    assert dataset.label_policy_version == "ma_label_policy_v2"
    assert item.prediction_band == "high"
    assert item.observed_band == "low"


@pytest.mark.unit
def test_objective_routing_is_predicted_band_eligible_covers_all_known_groups():
    """docs/23 step 1: is_predicted_band_eligible() 對所有已知 group（含 lead /
    conversion / app）回傳 True，僅 unknown 為 False。"""
    from modules.meta_andromeda.objective_routing import (
        CONVERSION,
        LEAD,
        TRAFFIC,
        AWARENESS,
        ENGAGEMENT,
        VIDEO,
        APP,
        UNKNOWN,
        is_predicted_band_eligible,
        is_roas_band_eligible,
        KNOWN_OBJECTIVE_GROUPS,
    )

    for group in KNOWN_OBJECTIVE_GROUPS:
        assert is_predicted_band_eligible(group) is True, f"{group} 應該是 True"
    assert is_predicted_band_eligible(UNKNOWN) is False

    # 守住原本的 NON_ROAS 路由——heuristic fallback 與 observed_label 邏輯不動
    assert is_roas_band_eligible(TRAFFIC) is False
    assert is_roas_band_eligible(AWARENESS) is False
    assert is_roas_band_eligible(ENGAGEMENT) is False
    assert is_roas_band_eligible(VIDEO) is False
    # conversion / lead / app 走 ROAS/CPA 邏輯
    assert is_roas_band_eligible(CONVERSION) is True
    assert is_roas_band_eligible(LEAD) is True
    assert is_roas_band_eligible(APP) is True


@pytest.mark.unit
def test_default_objective_profiles_make_non_roas_groups_band_eligible():
    """docs/23 step 2: _DEFAULT_OBJECTIVE_PROFILES 把 traffic/awareness/video/
    engagement 的 roas_band_eligible 改為 True，prompt 也不再寫「Set roas_band to
    null」。"""
    from modules.meta_andromeda.runtime import _DEFAULT_OBJECTIVE_PROFILES

    for group in ("traffic", "awareness", "video", "engagement"):
        profile = _DEFAULT_OBJECTIVE_PROFILES[group]
        assert profile["roas_band_eligible"] is True, (
            f"{group} 應該 roas_band_eligible=True（doc/23 step 2）"
        )
        prompt = profile["user_prompt_template"]
        assert "Set roas_band to null" not in prompt, (
            f"{group} prompt 仍含有『Set roas_band to null』，需要改成可比對 band 要求"
        )
        assert "high/mid/low" in prompt, (
            f"{group} prompt 沒要求輸出 high/mid/null band"
        )

    # lead 原本就走這套設計，避免本次改動影響到 lead
    lead_profile = _DEFAULT_OBJECTIVE_PROFILES["lead"]
    assert lead_profile["roas_band_eligible"] is True
    assert "LEAD QUALITY BAND" in lead_profile["user_prompt_template"]


@pytest.mark.unit
def test_validate_provider_result_preserves_band_for_non_roas_groups():
    """docs/23 step 3: AI provider 對 traffic/awareness/video/engagement 真的回
    band 時，_validate_provider_result 不會把它強制 null 掉。"""
    from modules.meta_andromeda.runtime import _validate_provider_result
    from modules.meta_andromeda.model_registry import model_registry

    registry_entry = model_registry.get_entry("candidate_v0")

    for group, band in (
        ("traffic", "high"),
        ("awareness", "mid"),
        ("video", "low"),
        ("engagement", "high"),
    ):
        parsed = {
            "overall_score": 72,
            "roas_band": band,
            "top_positive_drivers": ["測試"],
            "top_negative_drivers": [],
            "risk_tags": [],
            "diagnostic_breakdown": {
                "thumb_stop": {"score": 70, "reasoning": "test"},
            },
            "summary": f"{group} 評分測試",
        }
        result = _validate_provider_result(
            parsed,
            {
                "asset_type": "image",
                "objective": group,
                "request_mode": "auto",
                "placement_family": "feed",
                "market": "TW",
                "request_context": {
                    "headline": "h",
                    "primary_text": "p",
                    "cta": "c",
                    "objective": group,
                    "placement_family": "feed",
                    "market": "TW",
                },
            },
            registry_entry,
            roas_band_eligible=True,
            objective_group=group,
        )
        assert result["roas_band"] == band, f"{group} 的 band 應該被保留為 {band}"
        assert result["roas_prediction"]["band"] == band
        assert result["roas_prediction"]["eligible"] is True
        assert result["prediction_mode"] == "diagnostic_plus_roas"
        assert result["lineage"]["objective_group"] == group


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "objective,expected_group,expected_metric_focus",
    [
        ("traffic", "traffic", "ctr"),
        ("link_clicks", "traffic", "ctr"),
        ("outcome_traffic", "traffic", "ctr"),
        ("brand_awareness", "awareness", "cpm_reach"),
        ("reach", "awareness", "cpm_reach"),
        ("video_views", "video", "vtr"),
        ("outcome_engagement", "engagement", "engagement_rate"),
        ("post_engagement", "engagement", "engagement_rate"),
    ],
)
async def test_non_roas_objectives_resolve_to_correct_group_and_metric_focus(
    objective, expected_group, expected_metric_focus
):
    """docs/23 step 5: 4 個 group（含其常見 objective alias）都解析到正確的
    objective_group，且 prompt profile 的 metric_focus 也正確——這是「觀測端
    labeling.py 走 CTR/CPC 邏輯」與「預測端 prompt 走潛力 band 邏輯」兩條路由
    共用的路由表，必須一致。"""
    from modules.meta_andromeda.objective_routing import resolve_objective_group
    from modules.meta_andromeda.runtime import _DEFAULT_OBJECTIVE_PROFILES

    assert resolve_objective_group(objective) == expected_group
    assert _DEFAULT_OBJECTIVE_PROFILES[expected_group]["metric_focus"] == expected_metric_focus


@pytest.mark.asyncio
async def test_non_roas_group_end_to_end_ai_band_flows_through_to_detail(
    meta_andromeda_access, db, monkeypatch
):
    """docs/23 step 5: traffic 素材的 AI band 應該一路從 mock provider →
    _validate_provider_result → DB score_event → get_review_queue_detail 都被保
    留下來，不會被任何 gate 強制 null。"""
    from database.models.meta_andromeda import MetaAndromedaScoreEvent
    from modules.meta_andromeda.runtime import runtime_adapter, invalidate_prompt_cache
    from services.ai.openrouter_client import OpenRouterClient

    # 確保 prompt profile 是 migration 後的最新版（process 內 _prompt_profile_cache
    # 可能在更早的測試中 cache 過舊的 prompt）
    invalidate_prompt_cache()

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "openrouter")

    def fake_init(self, api_key=None):
        self.api_key = api_key or "test-openrouter-key"
        self.client = object()
        self.model_name = "google/gemini-3.5-flash"

    def fake_generate_content(
        self, prompt, model, system_prompt, temperature, max_tokens, timeout_seconds, user_content
    ):
        # 確認 prompt 真的在向模型要求可比對 band（doc/23 step 2）
        assert "CTR POTENTIAL BAND" in prompt or "roas_band" in prompt
        return json.dumps(
            {
                "overall_score": 78,
                "roas_band": "high",
                "top_positive_drivers": ["thumb-stop 強"],
                "top_negative_drivers": [],
                "risk_tags": [],
                "diagnostic_breakdown": {
                    "thumb_stop": {"score": 80, "reasoning": "test"},
                },
                "summary": "traffic 評分測試",
            }
        )

    monkeypatch.setattr(OpenRouterClient, "__init__", fake_init)
    monkeypatch.setattr(OpenRouterClient, "generate_content", fake_generate_content)

    # 模擬一筆 traffic 素材的 score_event 已經 queued
    score_event = MetaAndromedaScoreEvent(
        id="ma_evt_docs23_traffic_e2e",
        status="queued",
        asset_uri="storage://docs23-traffic.png",
        asset_type="image",
        request_mode="auto",
        objective="traffic",
        placement_family="feed",
        market="TW",
    )
    db.add(score_event)
    db.commit()
    repository.mark_score_processing(db, score_event.id)

    current = repository.get_review_queue_detail(db, score_event.id)
    result = await runtime_adapter.generate_score_result(current)
    repository.mark_score_completed(db, score_event.id, result)

    detail = repository.get_review_queue_detail(db, score_event.id)
    assert detail["status"] == "completed"
    assert detail["objective_group"] == "traffic"
    assert detail["roas_band"] == "high"
    assert detail["roas_prediction"]["band"] == "high"
    assert detail["roas_prediction"]["eligible"] is True
    # 觀測端 labeling 走 NON_ROAS 路由用 CTR/CPC，這層是另一條邏輯，不影響
    assert detail["prediction_mode"] == "diagnostic_plus_roas"


@pytest.mark.unit
def test_non_roas_group_enters_calibration_dataset_when_band_predicted(meta_andromeda_access, db):
    """docs/23 step 5: sync_calibration_dataset 對 traffic 等非 ROAS 群組，只要
    pred.roas_band 非 null 就要納入校準集（之前會被 skipped_not_band_eligible 排除）。"""
    from database.models.meta_andromeda import (
        MetaAndromedaCalibrationDataset,
        MetaAndromedaCalibrationItem,
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent,
    )

    # 確保資料庫乾淨
    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.query(MetaAndromedaBacktestRun).delete()
    db.commit()

    obs = MetaAndromedaObservedCreative(
        id="obs_docs23_traffic",
        asset_uri="docs23_traffic_uri",
        source_platform="facebook_ads",
        source_account_id="act_traffic",
        ad_id="ad_docs23_traffic",
        objective="traffic",  # sync_calibration_dataset 會把這個寫進 CalibrationItem.objective
        placement_family="feed",
        market="TW",
        media_type="image",
        observation_window_kind="last_7d",
        observation_window_start="2026-06-09",
        observation_window_end="2026-06-16",
        source_fetched_at="2026-06-16T12:00:00Z",
        # traffic 走 CTR：CTR 高=好（label_detail.metric=ctr）
        performance_snapshot={"spend": 100.0, "impressions": 5000, "clicks": 250, "ctr": 5.0},
    )
    db.add(obs)

    score_evt = MetaAndromedaScoreEvent(
        id="score_docs23_traffic",
        status="completed",
        asset_uri="docs23_traffic_uri",
        asset_type="image",
        request_mode="auto",
        objective="traffic",  # 非 ROAS 群組
        placement_family="feed",
        market="TW",
        roas_band="high",  # AI 真的回 band（doc/23 step 2 之後這才會發生）
        roas_prediction={"eligible": True, "band": "high", "confidence": 0.7, "reason_if_unavailable": None},
        lineage={"scoring_mode": "ai", "diagnostic_scores": {}},
    )
    db.add(score_evt)
    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/calibration/sync",
        json={"window_kind": "last_7d", "excluded_observed_ids": []},
    )
    assert response.status_code == 201
    payload = response.json()

    dataset = (
        db.query(MetaAndromedaCalibrationDataset)
        .filter(MetaAndromedaCalibrationDataset.id == payload["dataset_id"])
        .one()
    )
    # 之前這個值會是 skipped_not_band_eligible=1, synced_count=0；現在應該 synced_count=1
    assert dataset.summary["skipped_not_band_eligible"] == 0
    assert payload["synced_count"] == 1

    item = (
        db.query(MetaAndromedaCalibrationItem)
        .filter(MetaAndromedaCalibrationItem.dataset_id == payload["dataset_id"])
        .one()
    )
    assert item.objective == "traffic"
    assert item.prediction_band == "high"
    assert item.observed_band in ("high", "mid", "low")  # 動態門檻算出來的 band


@pytest.mark.unit
def test_non_roas_group_enters_drift_report_accuracy_when_band_predicted(meta_andromeda_access, db):
    """docs/23 step 5: create_drift_report 對 traffic 等非 ROAS 群組，只要
    pred.roas_band 非 null 就要納入 accuracy/MAE 計算（之前會被
    `if not pred_roas_eligible: continue` 排除）。"""
    from database.models.meta_andromeda import (
        MetaAndromedaObservedCreative,
        MetaAndromedaScoreEvent,
    )
    from datetime import datetime, timezone

    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.query(MetaAndromedaBacktestRun).delete()
    db.commit()

    obs = MetaAndromedaObservedCreative(
        id="obs_docs23_awareness_drift",
        asset_uri="docs23_awareness_uri",
        source_platform="facebook_ads",
        source_account_id="act_aware",
        ad_id="ad_docs23_awareness",
        objective="brand_awareness",  # labeling.label_observed_band 用這個路由觀測端 metric
        placement_family="feed",
        market="TW",
        media_type="image",
        observation_window_kind="last_7d",
        observation_window_start="2026-06-09",
        observation_window_end="2026-06-16",
        source_fetched_at="2026-06-16T12:00:00Z",
        # awareness 走 CPM/Reach 觀測
        performance_snapshot={"spend": 100.0, "impressions": 5000, "reach": 4000, "cpm": 20.0},
    )
    db.add(obs)

    base = datetime(2026, 6, 16, 12, 0, tzinfo=timezone.utc)
    score_evt = MetaAndromedaScoreEvent(
        id="score_docs23_awareness_drift",
        status="completed",
        asset_uri="docs23_awareness_uri",
        asset_type="image",
        request_mode="auto",
        objective="brand_awareness",
        placement_family="feed",
        market="TW",
        completed_at=base,
        roas_band="mid",
        roas_prediction={"eligible": True, "band": "mid", "confidence": 0.7, "reason_if_unavailable": None},
        lineage={"scoring_mode": "ai", "diagnostic_scores": {}},
    )
    db.add(score_evt)
    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/drift:trigger",
        json={"window_kind": "last_7d"},
    )
    assert response.status_code in (200, 201)
    payload = response.json()
    # docs/23 真正要驗的：traffic/awareness/video/engagement 的素材在 drift
    # report 不再被 skipped_not_band_eligible 排除，會進入 accuracy/MAE 計算。
    # 回傳欄位不是 `matched_count`，而是 `report_payload.total_band_matched` +
    # `matched_details[].band_eligible=true` 兩條線索（小樣本時 drift_status
    # 仍會是 `insufficient_data`，那是另一條獨立邏輯，不影響本次目標）。
    report_payload = payload.get("report_payload", {})
    assert report_payload.get("total_band_matched", 0) >= 1
    matched = report_payload.get("matched_details", [])
    assert matched, "expected at least one matched_details entry for awareness"
    assert matched[0].get("band_eligible") is True


@pytest.mark.unit
def test_heuristic_fallback_still_skips_band_for_non_roas_groups():
    """docs/23 step 4.3.1: heuristic 規則引擎在 traffic/awareness/video/
    engagement 仍不應該湊 band 出來，維持降級模式的明確標示。"""
    from modules.meta_andromeda.runtime import build_heuristic_score_result
    from modules.meta_andromeda.model_registry import model_registry

    registry_entry = model_registry.get_entry("candidate_v0")
    for objective in ("traffic", "brand_awareness", "video_views", "post_engagement"):
        result = build_heuristic_score_result(
            {
                "asset_type": "image",
                "objective": objective,
                "request_mode": "auto",
                "placement_family": "feed",
                "request_context": {
                    "headline": "標題",
                    "primary_text": "內文",
                    "cta": "立即了解",
                    "objective": objective,
                    "placement_family": "feed",
                    "market": "TW",
                },
            },
            registry_entry,
        )
        assert result["roas_band"] is None, (
            f"{objective} 的 heuristic fallback 不該湊 band，會誤導下游"
        )
        assert result["roas_prediction"]["eligible"] is False
        assert result["prediction_mode"] == "diagnostic_only"
