from .conftest import *  # noqa: F401,F403

import modules.meta_andromeda.service.observation_import as observation_import_module


class _SessionProxy:
    """背景匯入 job 以 SessionLocal() 開新 session；測試需把它綁回 db fixture
    的同一個 session（in-memory 測試庫 + 外層 transaction 隔離），否則寫入
    落到開發資料庫且測試查不到。close 改為 no-op，由 fixture 統一收尾。"""

    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        return None


def _bind_background_import_session(monkeypatch, db):
    monkeypatch.setattr(observation_import_module, "SessionLocal", lambda: _SessionProxy(db))


@pytest.mark.unit
def test_meta_andromeda_observation_import_stream_dispatch_and_consume(monkeypatch):
    """docs/24 Wave 2 端對端：enqueue_observation_import_event() 產生的 stream 訊息，
    consume_redis_stream_batch() 能正確依 kind 分流到 add_meta_andromeda_observation_import_job()，
    而不是誤當評分事件處理。"""
    monkeypatch.setattr(settings, "META_ANDROMEDA_REDIS_STREAM_KEY", "meta_andromeda:test_obs_queue")
    monkeypatch.setattr(settings, "META_ANDROMEDA_REDIS_STREAM_GROUP", "meta_andromeda:test_obs_group")
    monkeypatch.setattr(settings, "META_ANDROMEDA_REDIS_STREAM_CONSUMER", "meta_andromeda:test_obs_consumer")

    redis_mock = Mock()
    xadd_calls = []

    def fake_xadd(key, payload):
        xadd_calls.append((key, payload))
        return "1749388800099-0"

    redis_mock.xadd = Mock(side_effect=fake_xadd)
    monkeypatch.setattr(meta_andromeda_queue_host_module, "get_redis_client", lambda: redis_mock)

    import_payload = {
        "account_id": "act_123456789",
        "ad_id": "120000000000099",
        "observation_window_kind": "last_7d",
        "market": "TW",
        "placement_family": "feed",
    }

    dispatch = meta_andromeda_queue_host_module.queue_host_adapter.enqueue_observation_import_event(
        import_payload, user_id="google_user_1", team_id="team_1",
    )
    assert dispatch["accepted"] is True
    assert dispatch["queue_host"] == "redis_stream"
    assert xadd_calls
    stream_key, stream_payload = xadd_calls[0]
    assert stream_key == "meta_andromeda:test_obs_queue"
    assert stream_payload["kind"] == "observation_import"
    assert json.loads(stream_payload["payload"])["ad_id"] == "120000000000099"

    # 模擬 consumer 讀到剛剛送出的這則訊息
    redis_mock.xgroup_create = Mock()
    redis_mock.xreadgroup = Mock(return_value=[
        ("meta_andromeda:test_obs_queue", [("1749388800099-0", stream_payload)])
    ])
    redis_mock.xack = Mock()
    redis_mock.xdel = Mock()

    scheduled = []
    monkeypatch.setattr(
        scheduler_module,
        "add_meta_andromeda_observation_import_job",
        lambda payload, *, user_id, team_id, delay_seconds=0: scheduled.append(
            {"payload": payload, "user_id": user_id, "team_id": team_id, "delay_seconds": delay_seconds}
        ),
    )

    summary = meta_andromeda_queue_host_module.queue_host_adapter.consume_redis_stream_batch()
    assert summary["accepted"] is True
    assert summary["consumed_count"] == 1
    assert scheduled and scheduled[0]["payload"]["ad_id"] == "120000000000099"
    assert scheduled[0]["user_id"] == "google_user_1"
    assert scheduled[0]["team_id"] == "team_1"
    redis_mock.xack.assert_called_once()
    redis_mock.xdel.assert_called_once()


@pytest.mark.unit
def test_meta_andromeda_import_endpoint_dispatches_to_worker_in_web_role(meta_andromeda_access, monkeypatch):
    """docs/24 Wave 2：web 角色下匯入端點應該經 Redis stream 派工給 worker，
    不在本 process 執行 run_observed_facebook_ad_import_job。"""
    monkeypatch.setattr(settings, "SERVICE_ROLE", "web")

    redis_mock = Mock()
    xadd_calls = []
    redis_mock.xadd = Mock(side_effect=lambda key, payload: xadd_calls.append((key, payload)) or "1749388800100-0")
    redis_mock.get = Mock(return_value=None)
    monkeypatch.setattr(redis_cache_module, "get_redis_client", lambda: redis_mock)
    monkeypatch.setattr(meta_andromeda_queue_host_module, "get_redis_client", lambda: redis_mock)

    ran_in_process = {"called": False}

    async def fake_run_job(payload, *, user_id, team_id=None):
        ran_in_process["called"] = True

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "run_observed_facebook_ad_import_job",
        staticmethod(fake_run_job),
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000100",
            "observation_window_kind": "last_7d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 202
    assert xadd_calls, "web 角色下應該經 Redis stream 派工，而不是留在 web process"
    assert xadd_calls[0][1]["kind"] == "observation_import"
    assert json.loads(xadd_calls[0][1]["payload"])["ad_id"] == "120000000000100"
    assert ran_in_process["called"] is False


@pytest.mark.asyncio
async def test_meta_andromeda_batch_import_calls_prewarm_exactly_once_before_dispatching_items(monkeypatch):
    """docs/68 B2 第二層修復驗證：批次匯入應該先呼叫一次
    prewarm_facebook_ads_report_cache() 預熱整包報告快取，再逐筆派工。

    這裡直接在服務層攔截呼叫，而不是透過 HTTP 端點 + 觀察 Facebook API
    實際被打幾次來間接驗證：測試環境的 BackgroundTasks 是同一個 process
    內單執行緒依序執行，就算完全不做預熱，第一筆自己的
    fetch_observed_creative_candidate() 也會把結果寫進同一份行程內快取，
    讓後面幾筆「碰巧」命中——這種寫法量不出「有沒有做預熱」的差異，
    正式環境派工到 worker 才是真正需要預熱來避免 thundering herd 的場景。
    直接驗證 prewarm 呼叫本身，才是這個修復實際改變的可觀察行為。"""
    from modules.meta_andromeda.service import MetaAndromedaService

    prewarm_calls = []

    async def fake_prewarm(**kwargs):
        prewarm_calls.append(kwargs)

    dispatch_calls = []

    def fake_dispatch(payload, *, user_id, team_id):
        dispatch_calls.append(payload["ad_id"])
        return True  # 模擬派工成功給 worker，不需要真的跑完整匯入流程

    monkeypatch.setattr(
        "modules.meta_andromeda.service.observation_import.prewarm_facebook_ads_report_cache",
        fake_prewarm,
    )
    monkeypatch.setattr(
        MetaAndromedaService, "dispatch_observed_facebook_ad_import", staticmethod(fake_dispatch),
    )

    class _FailingBackgroundTasks:
        def add_task(self, *a, **kw):
            raise AssertionError("dispatch 已模擬派工成功，不應該退回 background_tasks 執行")

    results = await MetaAndromedaService.queue_observed_facebook_ad_import_batch(
        {
            "account_id": "act_123456789",
            "items": [{"ad_id": "ad_1"}, {"ad_id": "ad_2"}, {"ad_id": "ad_3"}],
            "observation_window_kind": "last_7d",
            "market": "TW",
            "placement_family": "feed",
        },
        user_id="google_user_1",
        team_id=None,
        background_tasks=_FailingBackgroundTasks(),
    )

    # 不管批次有幾筆，預熱只應該發生一次，而且要在派工之前完成。
    assert len(prewarm_calls) == 1
    assert prewarm_calls[0]["account_id"] == "act_123456789"
    assert dispatch_calls == ["ad_1", "ad_2", "ad_3"]
    assert len(results) == 3
    assert all(item["status"] == "accepted" for item in results)


@pytest.mark.unit
def test_meta_andromeda_batch_import_rejects_empty_items(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads/batch",
        json={
            "account_id": "act_123456789",
            "items": [],
            "observation_window_kind": "last_7d",
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
def test_meta_andromeda_batch_import_reuses_single_item_idempotency(
    meta_andromeda_access, monkeypatch,
):
    """docs/68 B2 批次端點應該重用 B5 既有的冪等去重邏輯，而不是重新實作
    一份：批次裡若混入一個已經 in-flight 的 observed_creative_id，該筆
    應回報 already_queued，且不應該再被派工一次。"""
    from modules.meta_andromeda.import_status_store import set_import_status

    dispatch_calls = []

    def fake_dispatch(payload, *, user_id, team_id):
        dispatch_calls.append(payload["ad_id"])
        return True

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "dispatch_observed_facebook_ad_import",
        staticmethod(fake_dispatch),
    )

    async def fake_prewarm(**kwargs):
        return None

    monkeypatch.setattr(
        "modules.meta_andromeda.service.observation_import.prewarm_facebook_ads_report_cache",
        fake_prewarm,
    )

    already_in_flight_id = meta_andromeda_service_module.MetaAndromedaService.build_observed_creative_id(
        "120000000099201", "last_7d",
    )
    set_import_status(already_in_flight_id, observation_status="processing")

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads/batch",
        json={
            "account_id": "act_123456789",
            "items": [
                {"ad_id": "120000000099201"},
                {"ad_id": "120000000099202"},
            ],
            "observation_window_kind": "last_7d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    statuses = {item["observed_creative_id"]: item["status"] for item in payload["items"]}
    assert statuses[already_in_flight_id] == "already_queued"
    # 只有真正需要派工的第二筆才應該呼叫 dispatch，已經 in-flight 的第一筆不應該。
    assert dispatch_calls == ["120000000099202"]


@pytest.mark.unit
def test_meta_andromeda_queue_observed_facebook_ad_import_skips_duplicate_in_flight_dispatch():
    """docs/68 B5 修復驗證：queue_observed_facebook_ad_import() 純服務層行為——
    同一筆觀測（同廣告+同觀測窗口+同日）在前一次仍是 queued/processing 時，第二次
    呼叫應直接回報 already_queued 且不需要再派工；該筆進度轉為 completed 之後，
    則視為已結束，允許重新送出一個新的匯入（不是永久卡住）。"""
    from modules.meta_andromeda.import_status_store import set_import_status

    payload = {
        "account_id": "act_123456789",
        "ad_id": "120000000000666",
        "observation_window_kind": "last_7d",
        "market": "TW",
        "placement_family": "feed",
    }

    first = meta_andromeda_service_module.MetaAndromedaService.queue_observed_facebook_ad_import(payload)
    assert first["status"] == "accepted"
    assert first["_dispatch_needed"] is True

    second = meta_andromeda_service_module.MetaAndromedaService.queue_observed_facebook_ad_import(payload)
    assert second["status"] == "already_queued"
    assert second["_dispatch_needed"] is False
    assert second["observed_creative_id"] == first["observed_creative_id"]

    # 模擬背景 job 已經跑完：completed 之後不該再被當成 in-flight 卡住。
    set_import_status(first["observed_creative_id"], observation_status="completed")
    third = meta_andromeda_service_module.MetaAndromedaService.queue_observed_facebook_ad_import(payload)
    assert third["status"] == "accepted"
    assert third["_dispatch_needed"] is True


@pytest.mark.unit
def test_meta_andromeda_observation_import_endpoint_is_idempotent_for_in_flight_duplicate(
    meta_andromeda_access, monkeypatch,
):
    """docs/68 B5 修復驗證：HTTP 端點層級——同一筆觀測前一次的匯入已經被
    dispatch 出去（模擬 web 角色成功派工給 worker、job 尚未完成）時重複送出，
    第二次應直接回 already_queued，且不應該再呼叫一次
    dispatch_observed_facebook_ad_import()（否則就是排出重複 job）。
    _dispatch_needed 這個內部旗標不應該外洩到 API 回應。"""
    dispatch_calls = []

    def fake_dispatch(payload, *, user_id, team_id):
        dispatch_calls.append(payload)
        return True  # 模擬派工成功，job 留在 worker 端還沒完成

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "dispatch_observed_facebook_ad_import",
        staticmethod(fake_dispatch),
    )

    request_payload = {
        "account_id": "act_123456789",
        "ad_id": "120000000000777",
        "observation_window_kind": "last_7d",
        "market": "TW",
        "placement_family": "feed",
    }

    first_response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads", json=request_payload,
    )
    second_response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads", json=request_payload,
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 202
    first_payload = first_response.json()
    second_payload = second_response.json()

    assert first_payload["status"] == "accepted"
    assert "_dispatch_needed" not in first_payload
    assert second_payload["status"] == "already_queued"
    assert "_dispatch_needed" not in second_payload
    assert second_payload["observed_creative_id"] == first_payload["observed_creative_id"]
    assert len(dispatch_calls) == 1


@pytest.mark.unit
def test_meta_andromeda_observation_import_accepts_supported_window_contract(meta_andromeda_access, db, monkeypatch):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Contract Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=payload.get("primary_text"),
            headline=payload.get("headline"),
            cta=payload.get("cta"),
            media_url="https://cdn.example.com/contract-ad.png",
            media_type="image",
            performance_snapshot={},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"contract-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )
    _bind_background_import_session(monkeypatch, db)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    # 匯入自 2026-06-22 起為完整背景工作流：202 立即回應只保證受理，
    # asset_uri 由背景 job 產生後透過輪詢狀態端點取得（TestClient 會在
    # 回應後同步執行 BackgroundTasks，因此這裡能直接查到最終狀態）。
    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["source"]["platform"] == "facebook_ads"
    assert payload["source"]["account_id"] == "act_123456789"
    assert payload["source"]["ad_id"] == "120000000000012"
    assert payload["asset_uri"] is None
    assert payload["observation_window"]["kind"] == "last_30d"
    assert payload["observed_creative_id"].startswith("ma_obs_")

    status_response = meta_andromeda_access.get(
        f"/api/meta-andromeda/evaluations/import/facebook-ads/{payload['observed_creative_id']}/status"
    )
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["observation_status"] == "completed"
    assert status_payload["asset_uri"].startswith("storage://meta-andromeda/")


@pytest.mark.unit
def test_meta_andromeda_observation_import_rejects_unsupported_window_kind(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_14d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 422


@pytest.mark.unit
def test_meta_andromeda_facebook_importer_normalizes_ad_row():
    from modules.meta_andromeda.importers.facebook_ads_importer import normalize_facebook_ad_row

    candidate = normalize_facebook_ad_row(
        row={
            "campaign_id": "120000000000010",
            "adset_id": "120000000000011",
            "ad_id": "120000000000012",
            "name": "Summer Promo Ad 01",
            "objective": "OUTCOME_SALES",
            "image_url": "https://cdn.example.com/creative.png",
            "spend": 1200.5,
            "impressions": 18234,
            "clicks": 321,
            "purchases": 14,
            "purchase_value": 4800,
            "roas": 2.85,
            "ctr": 1.76,
            "cpc": 3.74,
        },
        account_id="act_123456789",
        market="TW",
        placement_family="feed",
        primary_text="Primary copy",
        headline="Headline copy",
        cta="SHOP_NOW",
        observation_window_kind="last_30d",
        observation_window_start="2026-05-17",
        observation_window_end="2026-06-15",
        source_fetched_at="2026-06-15T00:00:00Z",
    )

    assert candidate.source_platform == "facebook_ads"
    assert candidate.source_account_id == "act_123456789"
    assert candidate.campaign_id == "120000000000010"
    assert candidate.adset_id == "120000000000011"
    assert candidate.ad_id == "120000000000012"
    assert candidate.ad_name == "Summer Promo Ad 01"
    assert candidate.media_url == "https://cdn.example.com/creative.png"
    assert candidate.media_type == "image"
    assert candidate.performance_snapshot["purchases"] == 14
    assert candidate.performance_snapshot["roas"] == 2.85
    assert candidate.observation_window_kind == "last_30d"
    assert candidate.observation_window_start == "2026-05-17"
    assert candidate.observation_window_end == "2026-06-15"


@pytest.mark.unit
def test_meta_andromeda_facebook_importer_normalizes_video_ad_row():
    """docs/68 B3：row 帶 video_id 時應判為 media_type='video'，media_url 此刻
    仍是 FB 廣告清單 API 給的縮圖（真正的影片來源要在
    fetch_observed_creative_candidate() 內另外解析，見下方測試）。"""
    from modules.meta_andromeda.importers.facebook_ads_importer import normalize_facebook_ad_row

    candidate = normalize_facebook_ad_row(
        row={
            "campaign_id": "120000000000010",
            "adset_id": "120000000000011",
            "ad_id": "120000000000099",
            "name": "Video Ad 01",
            "objective": "OUTCOME_SALES",
            "image_url": "https://scontent.xx.fbcdn.net/thumb.jpg",
            "video_id": "998877665544",
            "spend": 500.0,
            "impressions": 9000,
            "clicks": 120,
            "purchases": 5,
            "purchase_value": 1500,
            "roas": 3.0,
            "ctr": 1.33,
            "cpc": 4.16,
        },
        account_id="act_123456789",
        market="TW",
        placement_family="feed",
        primary_text=None,
        headline=None,
        cta=None,
        observation_window_kind="last_30d",
        observation_window_start="2026-05-17",
        observation_window_end="2026-06-15",
        source_fetched_at="2026-06-15T00:00:00Z",
    )

    assert candidate.media_type == "video"
    assert candidate.media_url == "https://scontent.xx.fbcdn.net/thumb.jpg"
    assert candidate.media_degraded_reason is None


@pytest.mark.unit
async def test_meta_andromeda_fetch_observed_creative_candidate_resolves_video_source(monkeypatch):
    """docs/68 B3：video_id 存在且來源解析成功時，media_url 應改指向真正可
    下載的影片來源，而不是停留在縮圖。"""
    import modules.meta_andromeda.importers.facebook_ads_importer as facebook_ads_importer_module

    async def fake_report_fetcher(**kwargs):
        return [{
            "ad_id": "120000000099100",
            "campaign_id": "120000000000010",
            "adset_id": "120000000000011",
            "name": "Video Ad Resolvable",
            "objective": "OUTCOME_SALES",
            "image_url": "https://scontent.xx.fbcdn.net/thumb_100.jpg",
            "video_id": "111222333444",
            "spend": 300.0,
        }]

    class _FakeVideoResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    class _FakeVideoAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def get(self, url, headers=None, params=None):
            assert "111222333444" in url
            return _FakeVideoResponse({"source": "https://video-abc.xx.fbcdn.net/actual_video.mp4"})

    monkeypatch.setattr(facebook_ads_importer_module, "get_headers", lambda *a, **kw: {"Authorization": "Bearer FAKE"})
    monkeypatch.setattr(facebook_ads_importer_module.httpx, "AsyncClient", lambda *a, **kw: _FakeVideoAsyncClient())

    candidate = await facebook_ads_importer_module.fetch_observed_creative_candidate(
        account_id="act_123456789",
        ad_id="120000000099100",
        user_id="google_user_1",
        observation_window_kind="last_30d",
        market="TW",
        placement_family="feed",
        primary_text=None,
        headline=None,
        cta=None,
        report_fetcher=fake_report_fetcher,
    )

    assert candidate.media_type == "video"
    assert candidate.media_url == "https://video-abc.xx.fbcdn.net/actual_video.mp4"
    assert candidate.media_degraded_reason is None


@pytest.mark.unit
async def test_meta_andromeda_fetch_observed_creative_candidate_falls_back_when_video_source_unavailable(monkeypatch):
    """docs/68 B3：影片來源解析失敗（例如權限不足、影片已刪除）時，應優雅
    退化為以縮圖當靜態圖片評分，而不是讓整個匯入失敗。"""
    import modules.meta_andromeda.importers.facebook_ads_importer as facebook_ads_importer_module

    async def fake_report_fetcher(**kwargs):
        return [{
            "ad_id": "120000000099200",
            "campaign_id": "120000000000010",
            "adset_id": "120000000000011",
            "name": "Video Ad Unresolvable",
            "objective": "OUTCOME_SALES",
            "image_url": "https://scontent.xx.fbcdn.net/thumb_200.jpg",
            "video_id": "555666777888",
            "spend": 300.0,
        }]

    # get_headers 回傳 None 模擬「無可用的存取權杖」，_fetch_facebook_video_source_url
    # 應短路回傳 None，交由 _resolve_video_candidate 退化為 image。
    monkeypatch.setattr(facebook_ads_importer_module, "get_headers", lambda *a, **kw: None)

    candidate = await facebook_ads_importer_module.fetch_observed_creative_candidate(
        account_id="act_123456789",
        ad_id="120000000099200",
        user_id="google_user_1",
        observation_window_kind="last_30d",
        market="TW",
        placement_family="feed",
        primary_text=None,
        headline=None,
        cta=None,
        report_fetcher=fake_report_fetcher,
    )

    assert candidate.media_type == "image"
    assert candidate.media_url == "https://scontent.xx.fbcdn.net/thumb_200.jpg"
    assert candidate.media_degraded_reason == "video_source_unavailable_fallback_to_thumbnail"


@pytest.mark.unit
def test_meta_andromeda_observation_import_uses_facebook_importer(meta_andromeda_access, db, monkeypatch):
    from database import MetaAndromedaObservedCreative
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Imported Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=payload["primary_text"],
            headline=payload["headline"],
            cta=payload["cta"],
            media_url="https://cdn.example.com/imported-ad.png",
            media_type="image",
            performance_snapshot={
                "spend": 1200.5,
                "impressions": 18234,
                "clicks": 321,
                "purchases": 14,
                "purchase_value": 4800,
                "roas": 2.85,
                "ctr": 1.76,
                "cpc": 3.74,
            },
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"imported-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )
    _bind_background_import_session(monkeypatch, db)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
            "primary_text": "Primary copy",
            "headline": "Headline copy",
            "cta": "SHOP_NOW",
        },
    )

    # 202 立即回應不含成效快照（由背景 job 呼叫 importer 後寫入 DB），
    # importer 是否被正確使用改由背景完成後的 DB 紀錄驗證。
    assert response.status_code == 202
    payload = response.json()
    assert payload["source"]["ad_id"] == "120000000000012"
    assert payload["observation_window"]["kind"] == "last_30d"

    observed = (
        db.query(MetaAndromedaObservedCreative)
        .filter(MetaAndromedaObservedCreative.id == payload["observed_creative_id"])
        .one()
    )
    assert observed.asset_uri.startswith("storage://meta-andromeda/")
    assert observed.performance_snapshot["purchases"] == 14
    assert observed.performance_snapshot["roas"] == 2.85
    assert observed.observation_window_kind == "last_30d"


@pytest.mark.unit
def test_meta_andromeda_observation_import_persists_asset_and_observed_record(
    meta_andromeda_access,
    db,
    monkeypatch,
):
    from database import MetaAndromedaAsset, MetaAndromedaObservedCreative
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Persisted Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=payload["primary_text"],
            headline=payload["headline"],
            cta=payload["cta"],
            media_url="https://cdn.example.com/persisted-ad.png",
            media_type="image",
            performance_snapshot={
                "spend": 1200.5,
                "impressions": 18234,
                "clicks": 321,
                "purchases": 14,
                "purchase_value": 4800,
                "roas": 2.85,
                "ctr": 1.76,
                "cpc": 3.74,
            },
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"persisted-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )
    _bind_background_import_session(monkeypatch, db)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
            "primary_text": "Primary copy",
            "headline": "Headline copy",
            "cta": "SHOP_NOW",
        },
    )

    assert response.status_code == 202
    payload = response.json()

    # asset_uri 由背景 job 產生（_bind_background_import_session 已把背景
    # session 綁回測試 session），202 回應中為 None：改由 ObservedCreative
    # 紀錄反查出實際儲存的 asset。
    observed = (
        db.query(MetaAndromedaObservedCreative)
        .filter(MetaAndromedaObservedCreative.id == payload["observed_creative_id"])
        .one()
    )
    stored_asset = db.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.asset_uri == observed.asset_uri).one()

    assert stored_asset.asset_type == "image"
    assert stored_asset.source_filename == "120000000000012.png"
    assert observed.asset_id == stored_asset.id
    assert observed.ad_id == "120000000000012"
    assert observed.source_platform == "facebook_ads"
    assert observed.performance_snapshot["purchases"] == 14
    assert observed.observation_window_kind == "last_30d"


@pytest.mark.unit
def test_meta_andromeda_observation_import_auto_creates_score_event(
    meta_andromeda_access,
    db,
    monkeypatch,
):
    from database import MetaAndromedaScoreEvent
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Auto Score Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text="Primary copy",
            headline="Headline copy",
            cta="SHOP_NOW",
            media_url="https://cdn.example.com/auto-score-ad.png",
            media_type="image",
            performance_snapshot={"roas": 2.85},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"auto-score-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.queue_host_adapter,
        "enqueue_score_event",
        lambda score_event_id, delay_seconds=1.0: {
            "accepted": True,
            "queue_host": "database_queue",
            "dispatch_mode": "db_backlog",
            "delay_seconds": delay_seconds,
        },
    )
    _bind_background_import_session(monkeypatch, db)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    # 202 立即回應時評分事件尚未建立（score_status 為 pending_observation），
    # 背景 job 完成匯入後才自動建立並派工評分事件。
    assert response.status_code == 202
    payload = response.json()
    assert payload["score_event_id"] is None
    assert payload["score_status"] == "pending_observation"
    assert payload["runtime_job_id"] is None

    status_payload = meta_andromeda_access.get(
        f"/api/meta-andromeda/evaluations/import/facebook-ads/{payload['observed_creative_id']}/status"
    ).json()
    assert status_payload["observation_status"] == "completed"
    assert status_payload["asset_uri"].startswith("storage://meta-andromeda/")

    score_event = (
        db.query(MetaAndromedaScoreEvent)
        .filter(MetaAndromedaScoreEvent.asset_uri == status_payload["asset_uri"])
        .one()
    )
    assert score_event.status == "queued"
    assert score_event.runtime_job_id.startswith("ma_score_")


@pytest.mark.unit
def test_meta_andromeda_observation_import_reuses_existing_ai_score_by_checksum(
    meta_andromeda_access,
    db,
    monkeypatch,
):
    """docs/68 A1 修復驗證：同一素材（相同 bytes → 相同 checksum）在不同觀測窗口
    匯入時，即使每次都會存成一個全新隨機 asset_uri 的資產，也應重用既有的
    completed + AI 模式評分，而不是每個窗口都重新呼叫一次 AI（修復前 asset_uri
    精確比對永遠不會命中，此測試在修復前會失敗）。"""
    from datetime import UTC, datetime

    from database import MetaAndromedaAsset, MetaAndromedaScoreEvent
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate
    from modules.meta_andromeda.storage import storage_adapter

    # meta_andromeda_access fixture 已呼叫 ensure_seed_data() 灌入固定的 seed 評分事件，
    # 用 baseline 而非硬編絕對數量，避免耦合到 seed 資料筆數。
    baseline_score_event_count = db.query(MetaAndromedaScoreEvent).count()

    shared_file_bytes = b"same-creative-bytes-across-observation-windows"

    # 模擬「第一個觀測窗口」已完成的 AI 評分：用 storage_adapter 實際存出一份
    # 資產，確保 checksum 與稍後背景匯入下載到的 bytes 完全一致，但 asset_uri
    # 刻意不同（如同真實情況：每次匯入都是獨立下載、獨立存檔）。
    first_window_asset_record = storage_adapter.store_asset(
        file_bytes=shared_file_bytes,
        asset_type="image",
        source_filename="first_window.png",
    )
    first_window_asset = MetaAndromedaAsset(**first_window_asset_record)
    db.add(first_window_asset)
    db.flush()

    existing_score_event = MetaAndromedaScoreEvent(
        id="ma_evt_existing_ai_score",
        status="completed",
        runtime_job_id="ma_score_existing",
        created_at=datetime.now(UTC),
        queued_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        asset_uri=first_window_asset.asset_uri,
        asset_type="image",
        asset_id=first_window_asset.id,
        request_mode="auto",
        objective="purchase",
        placement_family="all",
        market="TW",
        overall_score=72,
        roas_band="mid",
        model_version="test-model-v1",
        lineage={"scoring_mode": "ai"},
        request_context={"observed_creative_id": "ma_obs_first_window"},
    )
    db.add(existing_score_event)
    db.commit()

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Second Window Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://cdn.example.com/second-window-ad.png",
            media_type="image",
            performance_snapshot={"roas": 3.1},
            observation_window_kind="lifetime",
            observation_window_start="2023-08-08",
            observation_window_end="2026-08-07",
            source_fetched_at="2026-08-07T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": shared_file_bytes,
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )
    _bind_background_import_session(monkeypatch, db)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000099099",
            "observation_window_kind": "lifetime",
            "market": "TW",
            "placement_family": "feed",
        },
    )
    assert response.status_code == 202
    payload = response.json()

    status_payload = meta_andromeda_access.get(
        f"/api/meta-andromeda/evaluations/import/facebook-ads/{payload['observed_creative_id']}/status"
    ).json()

    # 內容相同（checksum 相同）但 asset_uri 不同的第二次匯入，應直接重用既有
    # AI 評分事件，而不是再建一筆新的評分事件、再打一次 AI。
    assert status_payload["score_status"] == "completed"
    assert status_payload["score_event_id"] == "ma_evt_existing_ai_score"

    # 重用既有評分後，總筆數只比 baseline 多我們手動建立的那一筆
    # existing_score_event，匯入流程本身沒有再新增評分事件。
    assert db.query(MetaAndromedaScoreEvent).count() == baseline_score_event_count + 1

    db.refresh(existing_score_event)
    assert payload["observed_creative_id"] in existing_score_event.lineage["linked_observation_ids"]


@pytest.mark.unit
def test_meta_andromeda_observation_import_dedupes_asset_by_checksum(
    meta_andromeda_access,
    db,
    monkeypatch,
):
    """docs/68 A2 修復驗證：兩次觀測匯入（不同廣告、不同觀測窗口）下載到位元組
    完全相同的素材時，第二次應直接沿用既有資產（相同 asset_id/asset_uri），
    而不是再寫一份重複檔案、多建一筆資產紀錄（修復前每次匯入都是獨立下載，
    完全不查重，此測試在修復前會失敗）。"""
    from database import MetaAndromedaAsset, MetaAndromedaObservedCreative
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    shared_file_bytes = b"identical-creative-bytes-for-dedup-test"
    # meta_andromeda_access fixture 已呼叫 ensure_seed_data() 灌入固定的 seed 資產，
    # 用 baseline 而非硬編絕對數量，避免耦合到 seed 資料筆數。
    baseline_asset_count = db.query(MetaAndromedaAsset).count()

    def make_fake_fetch(ad_name):
        async def fake_fetch_observed_creative_candidate(**kwargs):
            payload = kwargs["payload"]
            return ObservedCreativeCandidate(
                source_platform="facebook_ads",
                source_account_id=payload["account_id"],
                campaign_id="120000000000010",
                adset_id="120000000000011",
                ad_id=payload["ad_id"],
                ad_name=ad_name,
                objective="OUTCOME_SALES",
                placement_family=payload["placement_family"],
                market=payload["market"],
                primary_text=None,
                headline=None,
                cta=None,
                media_url=f"https://cdn.example.com/{payload['ad_id']}.png",
                media_type="image",
                performance_snapshot={"roas": 2.0},
                observation_window_kind=payload["observation_window_kind"],
                observation_window_start="2026-07-01",
                observation_window_end="2026-08-06",
                source_fetched_at="2026-08-06T00:00:00Z",
            )
        return fake_fetch_observed_creative_candidate

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": shared_file_bytes,
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )
    _bind_background_import_session(monkeypatch, db)

    # 第一次匯入：正常存出一份新資產。
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(make_fake_fetch("Dedup Ad First")),
    )
    first_payload = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000099001",
            "observation_window_kind": "last_7d",
            "market": "TW",
            "placement_family": "feed",
        },
    ).json()

    first_observed = (
        db.query(MetaAndromedaObservedCreative)
        .filter(MetaAndromedaObservedCreative.id == first_payload["observed_creative_id"])
        .one()
    )
    assert db.query(MetaAndromedaAsset).count() == baseline_asset_count + 1

    # 第二次匯入：不同廣告、不同觀測窗口，但下載到的位元組（checksum）完全相同，
    # 應直接沿用第一次的資產，不再新增資產紀錄。
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(make_fake_fetch("Dedup Ad Second")),
    )
    second_payload = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000099002",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    ).json()

    second_observed = (
        db.query(MetaAndromedaObservedCreative)
        .filter(MetaAndromedaObservedCreative.id == second_payload["observed_creative_id"])
        .one()
    )

    assert second_observed.asset_id == first_observed.asset_id
    assert second_observed.asset_uri == first_observed.asset_uri
    assert db.query(MetaAndromedaAsset).count() == baseline_asset_count + 1


@pytest.mark.unit
def test_meta_andromeda_observation_import_denies_without_fb_ads_module_access(
    meta_andromeda_permission_client,
    db,
    monkeypatch,
):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Denied Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://cdn.example.com/denied-ad.png",
            media_type="image",
            performance_snapshot={},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"denied-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )
    _grant_team_role_permission(
        db,
        role_key="team_member",
        permission_key="fb_ads:analytics:view",
        permission_name="數據查看",
        module_key="fb_ads",
        module_name="FB Ads",
    )
    db.commit()

    response = client.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        headers={"X-Team-ID": team.id},
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 403
    assert "fb_ads" in response.text


@pytest.mark.unit
def test_meta_andromeda_observation_import_denies_without_fb_ads_analytics_permission(
    meta_andromeda_permission_client,
    db,
    monkeypatch,
):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Denied Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://cdn.example.com/denied-ad.png",
            media_type="image",
            performance_snapshot={},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"denied-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )
    _grant_team_module_access(
        db,
        user_id=user.id,
        team_id=team.id,
        module_key="fb_ads",
        module_name="FB Ads",
    )
    db.commit()

    response = client.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        headers={"X-Team-ID": team.id},
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 403
    assert "fb_ads:analytics:view" in response.text


@pytest.mark.unit
def test_meta_andromeda_observation_import_allows_with_fb_ads_module_and_permission(
    meta_andromeda_permission_client,
    db,
    monkeypatch,
):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Allowed Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://cdn.example.com/allowed-ad.png",
            media_type="image",
            performance_snapshot={"purchases": 14, "roas": 2.85},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    async def fake_download_observed_asset_snapshot(*, media_url: str, ad_id: str, media_type: str):
        return {
            "file_bytes": b"allowed-image-bytes",
            "source_filename": f"{ad_id}.png",
            "content_type": "image/png",
            "asset_type": media_type,
        }

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_download_observed_asset_snapshot",
        staticmethod(fake_download_observed_asset_snapshot),
    )

    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.MEMBER,
        role_key="team_member",
    )
    _grant_team_module_access(
        db,
        user_id=user.id,
        team_id=team.id,
        module_key="fb_ads",
        module_name="FB Ads",
    )
    _grant_team_role_permission(
        db,
        role_key="team_member",
        permission_key="fb_ads:analytics:view",
        permission_name="數據查看",
        module_key="fb_ads",
        module_name="FB Ads",
    )
    db.commit()

    response = client.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        headers={"X-Team-ID": team.id},
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    assert response.status_code == 202
    assert response.json()["source"]["ad_id"] == "120000000000012"


@pytest.mark.unit
def test_meta_andromeda_observation_import_rejects_disallowed_media_host(meta_andromeda_access, monkeypatch):
    from modules.meta_andromeda.schemas import ObservedCreativeCandidate

    async def fake_fetch_observed_creative_candidate(**kwargs):
        payload = kwargs["payload"]
        return ObservedCreativeCandidate(
            source_platform="facebook_ads",
            source_account_id=payload["account_id"],
            campaign_id="120000000000010",
            adset_id="120000000000011",
            ad_id=payload["ad_id"],
            ad_name="Blocked Host Ad",
            objective="OUTCOME_SALES",
            placement_family=payload["placement_family"],
            market=payload["market"],
            primary_text=None,
            headline=None,
            cta=None,
            media_url="https://evil.example.net/blocked.png",
            media_type="image",
            performance_snapshot={"roas": 2.0},
            observation_window_kind="last_30d",
            observation_window_start="2026-05-17",
            observation_window_end="2026-06-15",
            source_fetched_at="2026-06-15T00:00:00Z",
        )

    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "_fetch_observed_facebook_ad_candidate",
        staticmethod(fake_fetch_observed_creative_candidate),
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/evaluations/import/facebook-ads",
        json={
            "account_id": "act_123456789",
            "ad_id": "120000000000012",
            "observation_window_kind": "last_30d",
            "market": "TW",
            "placement_family": "feed",
        },
    )

    # 背景工作流下請求一律先受理（202），media host 白名單驗證在背景 job
    # 執行，失敗結果透過輪詢狀態端點呈現（前端據此顯示「匯入失敗」徽章）。
    assert response.status_code == 202
    observed_creative_id = response.json()["observed_creative_id"]

    status_payload = meta_andromeda_access.get(
        f"/api/meta-andromeda/evaluations/import/facebook-ads/{observed_creative_id}/status"
    ).json()
    assert status_payload["observation_status"] == "failed"
    assert status_payload["observation_message"] == "observed_media_url_host_not_allowed"
    assert status_payload["score_status"] == "blocked_by_observation_failure"


class _FakeStreamResponse:
    """模擬 httpx 的串流回應：headers 固定、body 依 chunks 逐塊供
    aiter_bytes() 消費，並記錄實際被消費的 chunk 數，供測試驗證超限時
    是否有提早中止、不繼續讀完剩餘內容。"""

    def __init__(self, *, headers=None, chunks=None, status_code=200):
        self.headers = headers or {}
        self._chunks = list(chunks or [])
        self.status_code = status_code
        self.consumed_chunk_count = 0

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    async def aiter_bytes(self):
        for chunk in self._chunks:
            self.consumed_chunk_count += 1
            yield chunk


class _FakeStreamContextManager:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, *exc_info):
        return False


class _FakeAsyncClientForDownload:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    def stream(self, method, url):
        return _FakeStreamContextManager(self._response)


@pytest.mark.unit
async def test_meta_andromeda_download_observed_asset_rejects_by_content_length_without_reading_body(monkeypatch):
    """docs/68 B4 修復驗證：Content-Length 已宣告超過上限時應直接中止，
    完全不消費 body（不呼叫 aiter_bytes 的任何一塊），而不是像修復前那樣
    先把整個檔案讀進記憶體才拒絕。"""
    monkeypatch.setattr(settings, "META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES", 100)

    fake_response = _FakeStreamResponse(
        headers={"content-length": "999999", "content-type": "image/png"},
        chunks=[b"x" * 50, b"x" * 50, b"x" * 50],
    )
    monkeypatch.setattr(
        observation_import_module.httpx,
        "AsyncClient",
        lambda *a, **kw: _FakeAsyncClientForDownload(fake_response),
    )

    with pytest.raises(observation_import_module.MetaAndromedaValidationError) as exc_info:
        await observation_import_module.MetaAndromedaService._download_observed_asset_snapshot(
            media_url="https://scontent.xx.fbcdn.net/oversized.png",
            ad_id="120000000000900",
            media_type="image",
        )

    assert exc_info.value.detail == "observed_media_too_large"
    assert exc_info.value.status_code == 413
    assert fake_response.consumed_chunk_count == 0


@pytest.mark.unit
async def test_meta_andromeda_download_observed_asset_aborts_mid_stream_without_content_length(monkeypatch):
    """docs/68 B4 修復驗證：伺服器沒給 Content-Length（或謊報）時，邊讀邊
    累計位元組，一旦超限立刻中止，不繼續讀完剩餘的 chunk。"""
    monkeypatch.setattr(settings, "META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES", 100)

    fake_response = _FakeStreamResponse(
        headers={"content-type": "image/png"},  # 無 content-length
        chunks=[b"x" * 60, b"x" * 60, b"x" * 60, b"x" * 60],  # 累計到第 2 塊就已超過 100 bytes
    )
    monkeypatch.setattr(
        observation_import_module.httpx,
        "AsyncClient",
        lambda *a, **kw: _FakeAsyncClientForDownload(fake_response),
    )

    with pytest.raises(observation_import_module.MetaAndromedaValidationError) as exc_info:
        await observation_import_module.MetaAndromedaService._download_observed_asset_snapshot(
            media_url="https://scontent.xx.fbcdn.net/oversized.png",
            ad_id="120000000000901",
            media_type="image",
        )

    assert exc_info.value.detail == "observed_media_too_large"
    assert exc_info.value.status_code == 413
    # 第 2 塊消費完後累計已達 120 bytes > 100，應立刻中止，第 3、4 塊完全不會被讀取。
    assert fake_response.consumed_chunk_count == 2


@pytest.mark.unit
async def test_meta_andromeda_download_observed_asset_succeeds_under_limit(monkeypatch):
    """docs/68 B4 修復驗證：串流化後，正常大小的檔案仍能完整組回原始
    bytes，行為與修復前一致（回歸驗證，非新增能力）。"""
    monkeypatch.setattr(settings, "META_ANDROMEDA_OBSERVED_DOWNLOAD_MAX_BYTES", 1000)

    expected_bytes = b"png-bytes-part-1" + b"png-bytes-part-2"
    fake_response = _FakeStreamResponse(
        headers={"content-length": str(len(expected_bytes)), "content-type": "image/png"},
        chunks=[b"png-bytes-part-1", b"png-bytes-part-2"],
    )
    monkeypatch.setattr(
        observation_import_module.httpx,
        "AsyncClient",
        lambda *a, **kw: _FakeAsyncClientForDownload(fake_response),
    )

    snapshot = await observation_import_module.MetaAndromedaService._download_observed_asset_snapshot(
        media_url="https://scontent.xx.fbcdn.net/ok.png",
        ad_id="120000000000902",
        media_type="image",
    )

    assert snapshot["file_bytes"] == expected_bytes
    assert snapshot["content_type"] == "image/png"
    assert snapshot["asset_type"] == "image"
    assert snapshot["source_filename"] == "ok.png"
    assert fake_response.consumed_chunk_count == 2


@pytest.mark.unit
def test_meta_andromeda_team_user_without_module_access_is_denied_read_only_endpoint(
    meta_andromeda_permission_client,
    db,
):
    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.VIEWER,
        role_key="team_viewer",
        grant_module_access=False,
    )

    response = client.get("/api/meta-andromeda/overview", headers={"X-Team-ID": team.id})

    assert response.status_code == 403
    assert "meta_andromeda" in response.text


@pytest.mark.unit
def test_meta_andromeda_team_viewer_can_read_overview_with_team_module_access(
    meta_andromeda_permission_client,
    db,
):
    client, user = meta_andromeda_permission_client
    team = _setup_meta_andromeda_team_access(
        db,
        user,
        membership_role=UserRole.VIEWER,
        role_key="team_viewer",
    )

    response = client.get("/api/meta-andromeda/overview", headers={"X-Team-ID": team.id})

    assert response.status_code == 200
    assert response.json()["module"]["key"] == "meta_andromeda"


@pytest.mark.unit
def test_meta_andromeda_team_member_can_trigger_drift_report_and_approve_release(
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

    _mark_release_candidate_metrics(db, "cand_v2026_06_05_a", accuracy=0.61)

    drift_response = client.post(
        "/api/meta-andromeda/drift:trigger",
        headers={"X-Team-ID": team.id},
        json={"window_kind": "last_7d", "note": "member can operate with module access"},
    )
    release_response = client.post(
        "/api/meta-andromeda/release/approve",
        headers={"X-Team-ID": team.id},
        json={"model_version": "cand_v2026_06_05_a", "note": "member can release with module access"},
    )

    assert drift_response.status_code == 201
    assert drift_response.json()["window_kind"] == "last_7d"
    assert release_response.status_code == 200
    assert release_response.json()["action"] == "approve"
