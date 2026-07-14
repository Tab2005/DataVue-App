from .conftest import *  # noqa: F401,F403



@pytest.mark.unit
def test_meta_andromeda_review_queue_excludes_backtest_scores(db):
    from database.models.meta_andromeda import MetaAndromedaScoreEvent

    _clear_meta_andromeda_operational_data(db)
    db.add(
        MetaAndromedaScoreEvent(
            id="live_evt",
            status="completed",
            asset_uri="asset://live",
            asset_type="image",
            request_mode="manual",
            objective="sales",
            placement_family="feed",
            market="TW",
            overall_score=80,
            roas_band="high",
            diagnostic_breakdown={},
            risk_tags=[],
            top_positive_drivers=[],
            top_negative_drivers=[],
            lineage={"scoring_mode": "ai"},
            request_context={},
        )
    )
    db.add(
        MetaAndromedaScoreEvent(
            id="backtest_evt",
            status="completed",
            asset_uri="asset://bt",
            asset_type="image",
            request_mode="analytics_backtest",
            objective="sales",
            placement_family="feed",
            market="TW",
            overall_score=20,
            roas_band="low",
            diagnostic_breakdown={},
            risk_tags=[],
            top_positive_drivers=[],
            top_negative_drivers=[],
            lineage={"scoring_mode": "ai", "scoring_purpose": "backtest", "backtest_run_id": "ma_bt_001"},
            request_context={"observed_creative_id": "obs_1"},
        )
    )
    db.commit()

    result = repository.list_review_queue(db, limit=25)

    assert result["summary"]["total"] == 1
    assert [item["score_event_id"] for item in result["items"]] == ["live_evt"]


@pytest.mark.unit
def test_meta_andromeda_review_queue_supports_filters(meta_andromeda_access):
    response = meta_andromeda_access.get(
        "/api/meta-andromeda/review-queue",
        params={"status": "completed", "reviewed": "false", "limit": 30},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["status_filter"] == "completed"
    assert payload["summary"]["reviewed_filter"] is False
    assert payload["items"]
    assert all(item["status"] == "completed" for item in payload["items"])
    assert all(item["reviewed"] is False for item in payload["items"])


@pytest.mark.unit
def test_meta_andromeda_review_queue_detail_returns_selected_item(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/review-queue/ma_evt_20260605_001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["score_event_id"] == "ma_evt_20260605_001"
    assert payload["status"] == "completed"
    assert payload["top_positive_drivers"]


@pytest.mark.unit
def test_meta_andromeda_review_queue_falls_back_to_observed_media_url_for_preview(meta_andromeda_access, db):
    """成效分析匯入的素材，score_event.preview_url 一律是 null（本地 storage 縮圖代理
    在 backend/worker 分離部署下讀不到 worker 寫的檔案，見 2026-07-10 事故）。list 跟
    detail 兩個端點都應該退回用 ObservedCreative.media_url（原始 Facebook CDN 網址）
    當 preview_url，讓前端縮圖直接從那邊載，不用等本地 storage 修好。"""
    from database.models.meta_andromeda import MetaAndromedaObservedCreative, MetaAndromedaScoreEvent

    obs = MetaAndromedaObservedCreative(
        id="obs_preview_fallback_test",
        asset_uri="storage://meta-andromeda/uploads/preview_fallback.jpg",
        media_url="https://scontent.xx.fbcdn.net/v/preview_fallback.jpg",
        source_platform="facebook_ads",
        source_account_id="act_12345",
        ad_id="ad_preview_fallback",
        ad_name="Preview Fallback Ad",
        placement_family="feed",
        market="TW",
        media_type="image",
        observation_window_kind="last_7d",
        observation_window_start="2026-07-02",
        observation_window_end="2026-07-09",
        source_fetched_at="2026-07-09T12:00:00Z",
        performance_snapshot={},
    )
    db.add(obs)

    score_evt = MetaAndromedaScoreEvent(
        id="score_preview_fallback_test",
        status="completed",
        asset_uri="storage://meta-andromeda/uploads/preview_fallback.jpg",
        asset_type="image",
        preview_url=None,
        request_mode="auto",
        objective="OUTCOME_SALES",
        placement_family="feed",
        market="TW",
        request_context={"origin": "analytics", "observed_creative_id": "obs_preview_fallback_test"},
    )
    db.add(score_evt)
    db.commit()

    list_response = meta_andromeda_access.get(
        "/api/meta-andromeda/review-queue",
        params={"search": "score_preview_fallback_test", "limit": 30},
    )
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert any(
        item["score_event_id"] == "score_preview_fallback_test"
        and item["preview_url"] == "https://scontent.xx.fbcdn.net/v/preview_fallback.jpg"
        for item in items
    )

    detail_response = meta_andromeda_access.get("/api/meta-andromeda/review-queue/score_preview_fallback_test")
    assert detail_response.status_code == 200
    assert detail_response.json()["preview_url"] == "https://scontent.xx.fbcdn.net/v/preview_fallback.jpg"


@pytest.mark.unit
def test_meta_andromeda_feedback_timeline_returns_read_only_entries(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/scores/ma_evt_20260605_002/feedback")

    assert response.status_code == 200
    payload = response.json()
    assert payload["score_event_id"] == "ma_evt_20260605_002"
    assert payload["feedback"]
    assert payload["feedback"][0]["decision"] == "revise"


@pytest.mark.unit
def test_meta_andromeda_feedback_submit_updates_timeline(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/scores/ma_evt_20260605_001/feedback",
        json={
            "decision": "approve",
            "reason_codes": ["ready_for_release"],
            "comment": "Looks good.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["decision"] == "approve"
    assert payload["reason_codes"] == ["ready_for_release"]

    timeline = meta_andromeda_access.get("/api/meta-andromeda/scores/ma_evt_20260605_001/feedback")
    assert timeline.status_code == 200
    timeline_payload = timeline.json()
    assert timeline_payload["feedback"]
    assert timeline_payload["feedback"][-1]["decision"] == "approve"


@pytest.mark.unit
def test_meta_andromeda_team_member_can_submit_feedback_in_team_workspace(
    meta_andromeda_permission_client,
    db,
):
    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )

    response = client.post(
        "/api/meta-andromeda/scores/ma_evt_20260605_001/feedback",
        headers={"X-Team-ID": team.id},
        json={
            "decision": "approve",
            "reason_codes": ["team_member_feedback"],
            "comment": "Feedback is allowed for team members.",
        },
    )

    assert response.status_code == 201
    assert response.json()["decision"] == "approve"


@pytest.mark.unit
def test_score_to_list_item_includes_objective_group():
    """docs/23 step 3: _score_to_list_item 把 objective_group 加進 payload，detail
    頁前端才能動態決定該顯示哪個 band 標籤。"""
    from modules.meta_andromeda.repository import MetaAndromedaRepository
    from database.models.meta_andromeda import MetaAndromedaScoreEvent

    class _Stub:
        id = "evt_x"
        status = "completed"
        runtime_job_id = None
        created_at = None
        queued_at = None
        started_at = None
        completed_at = None
        failed_at = None
        updated_at = None
        asset_uri = "storage://x.png"
        asset_type = "image"
        asset_id = "asset_x"
        preview_url = None
        request_mode = "auto"
        objective = "traffic"
        placement_family = "feed"
        market = "TW"
        prediction_mode = "diagnostic_plus_roas"
        overall_score = 70
        roas_band = "high"
        model_version = "v1"
        reviewed = False
        feedback_count = 0
        latest_feedback_decision = None
        feature_manifest_id = None
        error_message = None
        attempt_count = 0
        request_context = {}
        # _score_to_detail 也會讀這些欄位，stub 必須具備
        diagnostic_breakdown = {}
        roas_prediction = None
        risk_tags = []
        top_positive_drivers = []
        top_negative_drivers = []
        explanations = None
        lineage = {}

    item = MetaAndromedaRepository._score_to_list_item(_Stub())
    assert item["objective"] == "traffic"
    assert item["objective_group"] == "traffic"

    # _score_to_detail 透過 _score_to_list_item 組裝，detail 頁 payload 也會有
    detail = MetaAndromedaRepository._score_to_detail(_Stub())
    assert detail["objective_group"] == "traffic"
