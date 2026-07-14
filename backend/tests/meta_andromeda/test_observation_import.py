from .conftest import *  # noqa: F401,F403


@pytest.mark.unit
def test_meta_andromeda_observation_import_stream_dispatch_and_consume(monkeypatch):
    """docs/24 Wave 2 端對端：enqueue_observation_import_event() 產生的 stream 訊息，
    consume_redis_stream_batch() 能正確依 kind 分流到 add_meta_andromeda_observation_import_job()，
    而不是誤當評分事件處理。"""
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_KEY", "meta_andromeda:test_obs_queue")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_GROUP", "meta_andromeda:test_obs_group")
    monkeypatch.setenv("META_ANDROMEDA_REDIS_STREAM_CONSUMER", "meta_andromeda:test_obs_consumer")

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
    monkeypatch.setenv("SERVICE_ROLE", "web")

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


@pytest.mark.unit
def test_meta_andromeda_observation_import_accepts_supported_window_contract(meta_andromeda_access, monkeypatch):
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

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["source"]["platform"] == "facebook_ads"
    assert payload["source"]["account_id"] == "act_123456789"
    assert payload["source"]["ad_id"] == "120000000000012"
    assert payload["asset_uri"].startswith("storage://meta-andromeda/")
    assert payload["observation_window"]["kind"] == "last_30d"
    assert payload["observation_window"]["start"]
    assert payload["observation_window"]["end"]
    assert payload["observed_creative_id"].startswith("ma_obs_")


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
def test_meta_andromeda_observation_import_uses_facebook_importer(meta_andromeda_access, monkeypatch):
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
    assert payload["source"]["ad_id"] == "120000000000012"
    assert payload["asset_uri"].startswith("storage://meta-andromeda/")
    assert payload["performance_snapshot"]["purchases"] == 14
    assert payload["performance_snapshot"]["roas"] == 2.85
    assert payload["observation_window"]["kind"] == "last_30d"


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

    stored_asset = db.query(MetaAndromedaAsset).filter(MetaAndromedaAsset.asset_uri == payload["asset_uri"]).one()
    observed = (
        db.query(MetaAndromedaObservedCreative)
        .filter(MetaAndromedaObservedCreative.id == payload["observed_creative_id"])
        .one()
    )

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

    assert response.status_code == 202
    payload = response.json()
    assert payload["score_event_id"] is None
    assert payload["score_status"] == "queued_background"
    assert payload["runtime_job_id"] is None

    score_event = (
        db.query(MetaAndromedaScoreEvent)
        .filter(MetaAndromedaScoreEvent.asset_uri == payload["asset_uri"])
        .one()
    )
    assert score_event.status == "queued"
    assert score_event.asset_uri == payload["asset_uri"]
    assert score_event.runtime_job_id.startswith("ma_score_")


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

    assert response.status_code == 400
    assert (response.json().get("detail") or response.json().get("error")) == "observed_media_url_host_not_allowed"


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
