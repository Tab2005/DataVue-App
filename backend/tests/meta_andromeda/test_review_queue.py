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
def test_meta_andromeda_review_queue_filters_by_source_and_has_observation(db):
    """使用者回報：篩選「評分工作台」或「成效分析匯入」（source 參數）會請求
    逾時。根因是 request_context["observed_creative_id"] 用裸的 JSON 運算式
    （PostgreSQL 對應 ->，回傳 json，沒有 btree operator class，建不了
    index），改用 .as_string()（對應 ->>，回傳 text，可建 index）後，這裡
    驗證篩選結果語意完全不變：source=analytics 只回傳有連結觀測素材的
    事件，source=score_lab 只回傳沒有的；has_observation 的兩個分支
    （True 用 or_ 合併 EXISTS 子查詢、False 用 ~EXISTS 排除）也一併重寫，
    這裡一併驗證行為不變。"""
    from database.models.meta_andromeda import MetaAndromedaScoreEvent

    _clear_meta_andromeda_operational_data(db)
    db.add(
        MetaAndromedaScoreEvent(
            id="analytics_evt",
            status="completed",
            asset_uri="asset://analytics",
            asset_type="image",
            request_mode="auto",
            objective="sales",
            placement_family="feed",
            market="TW",
            diagnostic_breakdown={},
            risk_tags=[],
            top_positive_drivers=[],
            top_negative_drivers=[],
            lineage={"scoring_mode": "ai"},
            request_context={"origin": "analytics", "observed_creative_id": "obs_1"},
        )
    )
    db.add(
        MetaAndromedaScoreEvent(
            id="score_lab_evt",
            status="completed",
            asset_uri="asset://score_lab",
            asset_type="image",
            request_mode="manual",
            objective="sales",
            placement_family="feed",
            market="TW",
            diagnostic_breakdown={},
            risk_tags=[],
            top_positive_drivers=[],
            top_negative_drivers=[],
            lineage={"scoring_mode": "ai"},
            request_context={"origin": "score_lab"},
        )
    )
    db.commit()

    analytics_result = repository.list_review_queue(db, source="analytics", limit=25)
    assert [item["score_event_id"] for item in analytics_result["items"]] == ["analytics_evt"]

    score_lab_result = repository.list_review_queue(db, source="score_lab", limit=25)
    assert [item["score_event_id"] for item in score_lab_result["items"]] == ["score_lab_evt"]

    matched_result = repository.list_review_queue(db, has_observation=True, limit=25)
    assert [item["score_event_id"] for item in matched_result["items"]] == ["analytics_evt"]

    unmatched_result = repository.list_review_queue(db, has_observation=False, limit=25)
    assert [item["score_event_id"] for item in unmatched_result["items"]] == ["score_lab_evt"]


@pytest.mark.unit
def test_meta_andromeda_review_queue_paginates_at_sql_level(db):
    """list_review_queue() 過去是把符合條件的整批結果撈進 Python 再用
    list slicing 分頁，資料量大時會拖慢審核佇列頁面（見使用者回報的
    請求逾時）。改成 SQL 層 LIMIT/OFFSET 後，這裡驗證分頁語意不變：
    total 是「排除 backtest 後」符合篩選條件的總筆數、每頁筆數正確、
    跨頁不重複不遺漏、且維持 created_at 由新到舊排序。"""
    from datetime import UTC, datetime, timedelta

    from database.models.meta_andromeda import MetaAndromedaScoreEvent

    _clear_meta_andromeda_operational_data(db)
    base_time = datetime(2026, 8, 1, tzinfo=UTC)
    total_rows = 7
    for i in range(total_rows):
        db.add(
            MetaAndromedaScoreEvent(
                id=f"page_evt_{i}",
                status="completed",
                created_at=base_time + timedelta(minutes=i),
                asset_uri=f"asset://page_{i}",
                asset_type="image",
                request_mode="manual",
                objective="sales",
                placement_family="feed",
                market="TW",
                overall_score=50,
                diagnostic_breakdown={},
                risk_tags=[],
                top_positive_drivers=[],
                top_negative_drivers=[],
                lineage={"scoring_mode": "ai"},
                request_context={},
            )
        )
    db.commit()

    page_size = 3
    page_1 = repository.list_review_queue(db, limit=page_size, page=1)
    page_2 = repository.list_review_queue(db, limit=page_size, page=2)
    page_3 = repository.list_review_queue(db, limit=page_size, page=3)

    assert page_1["summary"]["total"] == total_rows
    assert page_1["summary"]["total_pages"] == 3
    assert len(page_1["items"]) == page_size
    assert len(page_2["items"]) == page_size
    assert len(page_3["items"]) == 1  # 最後一頁只剩 1 筆（7 筆 / 每頁 3 筆）

    # created_at 新到舊排序：page_evt_6 最新，應排在第一頁最前面。
    assert page_1["items"][0]["score_event_id"] == "page_evt_6"

    all_ids_across_pages = [
        item["score_event_id"]
        for page in (page_1, page_2, page_3)
        for item in page["items"]
    ]
    # 跨頁串起來應該剛好是全部 7 筆、不重複、不遺漏。
    assert len(all_ids_across_pages) == total_rows
    assert len(set(all_ids_across_pages)) == total_rows
    assert set(all_ids_across_pages) == {f"page_evt_{i}" for i in range(total_rows)}


@pytest.mark.unit
def test_meta_andromeda_review_queue_uses_sql_level_limit_offset(db):
    """docs/68 追加修復驗證：上面那個「分頁輸出正確」的測試測不出效能問題
    ——把整批結果撈進 Python 再用 list slicing 切頁，跟直接用 SQL
    LIMIT/OFFSET，兩者的「輸出結果」本來就應該一樣，差別只在有沒有把
    不需要的資料庫列也撈出來，這正是使用者回報的請求逾時（>30000ms）
    根因。這裡直接攔截實際送往資料庫的 SQL 語句文字，確認真的有下
    LIMIT，而不是只驗證分頁計算邏輯。"""
    from sqlalchemy import event

    from database.models.meta_andromeda import MetaAndromedaScoreEvent

    _clear_meta_andromeda_operational_data(db)
    for i in range(5):
        db.add(
            MetaAndromedaScoreEvent(
                id=f"limit_check_evt_{i}",
                status="completed",
                asset_uri=f"asset://limit_check_{i}",
                asset_type="image",
                request_mode="manual",
                objective="sales",
                placement_family="feed",
                market="TW",
                diagnostic_breakdown={},
                risk_tags=[],
                top_positive_drivers=[],
                top_negative_drivers=[],
                lineage={},
                request_context={},
            )
        )
    db.commit()

    executed_statements = []

    def _capture(conn, cursor, statement, parameters, context, executemany):
        executed_statements.append(statement)

    bind = db.get_bind()
    event.listen(bind, "before_cursor_execute", _capture)
    try:
        repository.list_review_queue(db, limit=2, page=1)
    finally:
        event.remove(bind, "before_cursor_execute", _capture)

    select_statements = [s for s in executed_statements if s.strip().upper().startswith("SELECT")]
    assert select_statements
    assert any("LIMIT" in s.upper() for s in select_statements), (
        "list_review_queue() 應該用 SQL 層 LIMIT 分頁，而不是把整批結果撈進 "
        "Python 再切頁；實際送出的 SELECT 語句都沒有 LIMIT，代表分頁又退化 "
        "回全表撈取了。"
    )


@pytest.mark.unit
def test_meta_andromeda_review_queue_supports_filters(meta_andromeda_access):
    # 2026-06-26 審核佇列改版為評估紀錄後，reviewed 篩選參數已移除；
    # 現行篩選為 status / roas_band / has_observation / search / source /
    # scoring_engine（見 router/review_queue.py）。
    response = meta_andromeda_access.get(
        "/api/meta-andromeda/review-queue",
        params={"status": "completed", "page_size": 30},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["status_filter"] == "completed"
    assert payload["items"]
    assert all(item["status"] == "completed" for item in payload["items"])

    band_response = meta_andromeda_access.get(
        "/api/meta-andromeda/review-queue",
        params={"status": "completed", "roas_band": "high", "page_size": 30},
    )

    assert band_response.status_code == 200
    band_payload = band_response.json()
    assert band_payload["summary"]["roas_band_filter"] == "high"
    assert all(item["roas_band"] == "high" for item in band_payload["items"])


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
