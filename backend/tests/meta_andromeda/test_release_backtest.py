from .conftest import *  # noqa: F401,F403


@pytest.mark.unit
def test_meta_andromeda_create_backtest_run_queues_isolated_run(meta_andromeda_access, monkeypatch):
    monkeypatch.setattr(
        meta_andromeda_router_module,
        "asyncio",
        meta_andromeda_router_module.asyncio,
    )
    monkeypatch.setattr(
        "modules.meta_andromeda.model_catalog.validate_candidate_model",
        lambda model_id: {"model_id": model_id, "ok": True, "exists": True, "issues": []},
    )
    queued = []
    monkeypatch.setattr(scheduler_module, "add_meta_andromeda_backtest_run_job", lambda run_id: queued.append(run_id))

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/backtest/runs",
        json={"provider_model": "openrouter/test-model", "sample_limit": 5, "note": "candidate check"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["provider_model"] == "openrouter/test-model"
    assert payload["status"] == "queued"
    assert payload["sample_limit"] == 5
    assert queued == [payload["run_id"]]



@pytest.mark.unit
def test_meta_andromeda_create_backtest_run_rejects_invalid_model(meta_andromeda_access, monkeypatch):
    monkeypatch.setattr(
        "modules.meta_andromeda.model_catalog.validate_candidate_model",
        lambda model_id: {"model_id": model_id, "ok": False, "exists": False, "issues": ["not found"]},
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/backtest/runs",
        json={"provider_model": "missing/model", "sample_limit": 5},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["validation"]["ok"] is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "role,expected_report_jobs,expected_ma_jobs",
    [
        ("all", True, True),
        ("web", True, False),
        ("worker", False, True),
    ],
)
def test_scheduler_role_flags_resolve_correctly(role, expected_report_jobs, expected_ma_jobs):
    """docs/24 Wave 2：SERVICE_ROLE 決定 start_scheduler() 該註冊哪些 job。
    all 維持拆分前行為；web 只留週報排程；worker 只留 Meta Andromeda 排程。
    """
    run_report_jobs, run_meta_andromeda_jobs = scheduler_module._resolve_scheduler_role_flags(role)
    assert run_report_jobs is expected_report_jobs
    assert run_meta_andromeda_jobs is expected_ma_jobs


@pytest.mark.unit
def test_meta_andromeda_release_metrics_refresh_job_registered_daily(monkeypatch):
    """docs/32 第3波：worker 排程需每日 UTC 02:00 自動刷新 production release metrics。"""
    calls = []

    class FakeScheduler:
        def add_job(self, *args, **kwargs):
            calls.append({"args": args, "kwargs": kwargs})
            return {"job_id": kwargs.get("id")}

    monkeypatch.setattr(scheduler_module, "scheduler", FakeScheduler())

    job = scheduler_module.add_meta_andromeda_release_metrics_refresh_job()

    assert job == {"job_id": scheduler_module.META_ANDROMEDA_RELEASE_METRICS_REFRESH_JOB_ID}
    assert calls
    kwargs = calls[0]["kwargs"]
    assert calls[0]["args"][0] is scheduler_module.refresh_meta_andromeda_release_metrics
    assert kwargs["id"] == scheduler_module.META_ANDROMEDA_RELEASE_METRICS_REFRESH_JOB_ID
    assert kwargs["replace_existing"] is True
    assert kwargs["coalesce"] is True
    assert kwargs["max_instances"] == 1
    assert "hour='2'" in str(kwargs["trigger"])
    assert "minute='0'" in str(kwargs["trigger"])


@pytest.mark.unit
def test_meta_andromeda_release_metrics_refresh_handles_insufficient_data(monkeypatch):
    """docs/32 第3波：insufficient_data 是正常結果，job 不應丟例外或中斷其他排程。"""
    calls = []

    class SessionProxy:
        def close(self):
            calls.append(("close", None))

    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: SessionProxy())
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "get_release_overview",
        staticmethod(lambda db: {"current_production": {"model_version": "prod_refresh_test"}}),
    )
    monkeypatch.setattr(
        meta_andromeda_service_module.MetaAndromedaService,
        "refresh_release_metrics",
        staticmethod(lambda db, model_version: calls.append(("refresh", model_version)) or {
            "status": "insufficient_data",
            "sample_count": 2,
        }),
    )

    asyncio.run(scheduler_module.refresh_meta_andromeda_release_metrics())

    assert ("refresh", "prod_refresh_test") in calls
    assert ("close", None) in calls


@pytest.mark.unit
def test_get_active_host_web_role_never_dispatches_locally(monkeypatch):
    """docs/24 Wave 2：web 角色下 get_active_host() 絕不能回 apscheduler/local_async，
    否則評分負載又會跑回 web process 的 event loop，等於沒拆分。"""
    monkeypatch.setenv("SERVICE_ROLE", "web")

    # 明確設定的 redis_stream/database_queue/external_webhook 原樣尊重
    monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", "database_queue")
    assert meta_andromeda_queue_host_module.queue_host_adapter.get_active_host() == "database_queue"

    monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", "external_webhook")
    assert meta_andromeda_queue_host_module.queue_host_adapter.get_active_host() == "external_webhook"

    # auto / apscheduler / local_async 一律收斂成 redis_stream（Redis 可用時）
    redis_mock = Mock()
    monkeypatch.setattr(meta_andromeda_queue_host_module, "get_redis_client", lambda: redis_mock)
    for configured in ("auto", "apscheduler", "local_async"):
        monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", configured)
        assert meta_andromeda_queue_host_module.queue_host_adapter.get_active_host() == "redis_stream"

    # Redis 不可用時退回 database_queue，讓 worker 的 sweeper 補派工
    monkeypatch.setattr(meta_andromeda_queue_host_module, "get_redis_client", lambda: None)
    monkeypatch.setenv("META_ANDROMEDA_QUEUE_HOST", "auto")
    assert meta_andromeda_queue_host_module.queue_host_adapter.get_active_host() == "database_queue"


@pytest.mark.unit
def test_meta_andromeda_release_overview_returns_candidates_and_notes(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/release/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_production"]["release_status"] == "production"
    assert payload["previous_production"]["release_status"] == "superseded"
    assert payload["candidates"]
    assert payload["history"]
    assert payload["notes"]


def _reset_metric_pair_tables(db):
    """清空觀測/評分事件表：label 門檻與配對都掃全表，殘留資料會污染排序與 band 判定。"""
    from database.models.meta_andromeda import MetaAndromedaObservedCreative, MetaAndromedaScoreEvent

    db.query(MetaAndromedaObservedCreative).delete()
    db.query(MetaAndromedaScoreEvent).delete()
    db.query(MetaAndromedaBacktestRun).delete()
    db.commit()


def _seed_metric_pair(db, idx: str, *, model_version: str, overall_score: float, pred_band: str, roas: float, spend: float = 100.0):
    """建一組可被 _collect_release_metric_pairs 配對的 ObservedCreative + completed ScoreEvent。

    roas 門檻在樣本 < 20 且無 prior policy 時退回固定 3.0/6.0：<3 → low、3-6 → mid、>6 → high。
    """
    from database.models.meta_andromeda import MetaAndromedaObservedCreative, MetaAndromedaScoreEvent

    obs = MetaAndromedaObservedCreative(
        id=f"mp_obs_{idx}",
        asset_uri=f"storage://meta-andromeda/metric-pairs/{idx}.png",
        source_platform="facebook_ads",
        source_account_id="act_mp",
        ad_id=f"ad_mp_{idx}",
        ad_name=f"素材 {idx}",
        objective="CONVERSIONS",
        placement_family="feed",
        market="TW",
        media_type="image",
        media_url=f"https://scontent.example.com/{idx}.jpg",
        observation_window_kind="last_7d",
        observation_window_start="2026-07-01",
        observation_window_end="2026-07-07",
        source_fetched_at="2026-07-08T00:00:00Z",
        performance_snapshot={"roas": roas, "spend": spend},
    )
    db.add(obs)
    evt = MetaAndromedaScoreEvent(
        id=f"mp_evt_{idx}",
        status="completed",
        asset_uri=obs.asset_uri,
        asset_type="image",
        request_mode="manual",
        objective="CONVERSIONS",
        placement_family="feed",
        market="TW",
        overall_score=overall_score,
        roas_band=pred_band,
        roas_prediction={"eligible": True},
        lineage={"registry_model_version": model_version, "scoring_mode": "ai"},
    )
    db.add(evt)


@pytest.mark.unit
def test_meta_andromeda_release_metric_pairs_mismatch_sort(meta_andromeda_access, db):
    """docs/32 任務 1.1：配對明細端點欄位完整、mismatch 排序讓高分低效浮最上面，
    且明細筆數與 compute_release_metrics 的 sample_count 一致（共用配對邏輯）。"""
    mv = "mp_test_model_v1"
    _reset_metric_pair_tables(db)
    # A：高分(92) × 實際 low(roas 1.0)、預測 high → band_gap 2（高分低效，應排最前）
    _seed_metric_pair(db, "a", model_version=mv, overall_score=92, pred_band="high", roas=1.0)
    # B：低分(40) × 實際 high(roas 8.0)、預測 low → band_gap 2（低分高效）
    _seed_metric_pair(db, "b", model_version=mv, overall_score=40, pred_band="low", roas=8.0)
    # C：中分(70) × 實際 mid(roas 4.0)、預測 mid → band_gap 0
    _seed_metric_pair(db, "c", model_version=mv, overall_score=70, pred_band="mid", roas=4.0)
    db.commit()

    response = meta_andromeda_access.get(f"/api/meta-andromeda/release/{mv}/metric-pairs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 3
    assert payload["sort"] == "mismatch"
    ids = [item["observed_creative_id"] for item in payload["items"]]
    assert ids == ["mp_obs_a", "mp_obs_b", "mp_obs_c"]

    top = payload["items"][0]
    assert top["score_event_id"] == "mp_evt_a"
    assert top["pred_band"] == "high"
    assert top["real_band"] == "low"
    assert top["band_gap"] == 2
    assert top["overall_score"] == 92
    assert top["label_value"] == 1.0
    assert top["spend"] == 100.0
    assert top["media_url"].startswith("https://")
    assert top["asset_uri"].startswith("storage://")
    assert top["observation_window_kind"] == "last_7d"

    # 與聚合指標同一份配對邏輯：sample_count 必須一致
    metrics = repository.refresh_release_metrics(db, mv)
    assert metrics["sample_count"] == 3


@pytest.mark.unit
def test_meta_andromeda_release_metric_pairs_score_vs_perf_sort(meta_andromeda_access, db):
    """score_vs_perf 排序：依模型總分降冪，perf_rank 標出實際成效名次（1 = 最好）。"""
    mv = "mp_test_model_v2"
    _reset_metric_pair_tables(db)
    _seed_metric_pair(db, "d", model_version=mv, overall_score=92, pred_band="high", roas=1.0)
    _seed_metric_pair(db, "e", model_version=mv, overall_score=40, pred_band="low", roas=8.0)
    _seed_metric_pair(db, "f", model_version=mv, overall_score=70, pred_band="mid", roas=4.0)
    db.commit()

    response = meta_andromeda_access.get(
        f"/api/meta-andromeda/release/{mv}/metric-pairs?sort=score_vs_perf&limit=2"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 3
    assert len(payload["items"]) == 2  # limit 生效，但 sample_count 仍為全量
    ids = [item["observed_creative_id"] for item in payload["items"]]
    assert ids == ["mp_obs_d", "mp_obs_f"]  # 92 → 70
    # 分數最高的 d 實際成效最差（roas 1.0）→ perf_rank 3
    assert payload["items"][0]["perf_rank"] == 3


@pytest.mark.unit
def test_meta_andromeda_release_metric_pairs_empty(meta_andromeda_access):
    """無配對資料時回空陣列與 sample_count 0，不報錯。"""
    response = meta_andromeda_access.get("/api/meta-andromeda/release/no_such_model/metric-pairs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_count"] == 0
    assert payload["items"] == []


@pytest.mark.unit
def test_meta_andromeda_release_approve_updates_history(meta_andromeda_access, db):
    _mark_release_candidate_metrics(db, "cand_v2026_06_05_a", accuracy=0.62)
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/approve",
        json={"model_version": "cand_v2026_06_05_a", "note": "Ship it"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "approve"
    assert payload["model_version"] == "cand_v2026_06_05_a"

    overview = meta_andromeda_access.get("/api/meta-andromeda/release/overview")
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert overview_payload["history"][0]["action"] == "approve"


@pytest.mark.unit
def test_meta_andromeda_release_approve_blocks_uncomputed_candidate(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/approve",
        json={"model_version": "cand_v2026_06_05_a", "note": "try seed metrics"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "release_metrics_not_computed"
    assert detail["details"]["metrics_source"] == "seed"



@pytest.mark.unit
def test_meta_andromeda_release_approve_blocks_low_accuracy_candidate(meta_andromeda_access, db):
    _mark_release_candidate_metrics(db, "cand_v2026_06_05_a", accuracy=0.54)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/approve",
        json={"model_version": "cand_v2026_06_05_a", "note": "accuracy too low"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "release_accuracy_below_threshold"
    assert detail["details"]["threshold"] == 0.55



@pytest.mark.unit
def test_meta_andromeda_release_approve_force_requires_note(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/approve",
        json={"model_version": "cand_v2026_06_05_a", "force": True, "note": ""},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "force_note_required"



@pytest.mark.unit
def test_meta_andromeda_release_approve_force_bypasses_gate_and_marks_history(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/approve",
        json={"model_version": "cand_v2026_06_05_a", "force": True, "note": "emergency model switch"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["forced"] is True
    assert payload["release_gate"]["forced"] is True

    overview = meta_andromeda_access.get("/api/meta-andromeda/release/overview")
    history = overview.json()["history"][0]
    assert history["action"] == "approve"
    assert history["forced"] is True
    assert history["note"] == "emergency model switch"



@pytest.mark.unit
def test_meta_andromeda_release_rollback_ignores_accuracy_gate(meta_andromeda_access, db):
    _mark_release_candidate_metrics(db, "cand_v2026_06_05_a", accuracy=0.62)
    approve = meta_andromeda_access.post(
        "/api/meta-andromeda/release/approve",
        json={"model_version": "cand_v2026_06_05_a", "note": "ship qualifying model"},
    )
    assert approve.status_code == 200

    rollback = meta_andromeda_access.post(
        "/api/meta-andromeda/release/rollback",
        json={"model_version": "cand_v2026_06_05_a", "note": "rollback should always work"},
    )

    assert rollback.status_code == 200
    assert rollback.json()["action"] == "rollback"


@pytest.mark.unit
def test_meta_andromeda_create_release_candidate_appears_in_overview(meta_andromeda_access):
    """新增候選版本：正式評分模型過去只能在種子資料建立的候選之間切換，
    這個端點補上「自由新增候選」的入口（優化方向 1）。"""
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/candidates",
        json={
            "model_version": "cand_v2026_09_01_manual",
            "provider": "openrouter",
            "provider_model": "some-org/some-new-model:free",
            "note": "手動測試新候選",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["model_version"] == "cand_v2026_09_01_manual"
    assert payload["release_status"] == "candidate"
    assert payload["is_demo_data"] is True

    overview = meta_andromeda_access.get("/api/meta-andromeda/release/overview")
    assert overview.status_code == 200
    candidate_versions = [c["model_version"] for c in overview.json()["candidates"]]
    assert "cand_v2026_09_01_manual" in candidate_versions

    # 歷史紀錄也應留下一筆稽核事件
    assert overview.json()["history"][0]["action"] == "create_candidate"
    assert overview.json()["history"][0]["model_version"] == "cand_v2026_09_01_manual"


@pytest.mark.unit
def test_meta_andromeda_create_release_candidate_inherits_production_scoring_profile(meta_andromeda_access, db):
    """未指定 scoring_profile 時應沿用目前 production 的設定，讓操作者只想
    換模型時不必連帶處理 prompt/校準邏輯。

    注意：`ensure_seed_data()` 不會建立 `MetaAndromedaModelRegistryEntry`
    （那張表只由正式環境的 Alembic migration 種子資料填入，測試 DB 是空的），
    故這裡先手動插入一筆 is_current_production=True 的 registry entry 來
    模擬「目前線上已有一顆模型」的情境。"""
    from database.models.meta_andromeda import MetaAndromedaModelRegistryEntry

    db.add(MetaAndromedaModelRegistryEntry(
        model_version="prod_test_existing",
        provider="openrouter",
        provider_model="some-org/existing-prod-model:free",
        scoring_profile="creative_scoring_v_test",
        feature_manifest_id="fm_test_existing",
        release_channel="production",
        source_of_truth="datavue.meta_andromeda.registry",
        is_current_production=True,
    ))
    db.commit()

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/candidates",
        json={
            "model_version": "cand_v2026_09_01_inherit",
            "provider": "openrouter",
            "provider_model": "some-org/another-model:free",
        },
    )
    assert response.status_code == 201

    entry = (
        db.query(MetaAndromedaModelRegistryEntry)
        .filter(MetaAndromedaModelRegistryEntry.model_version == "cand_v2026_09_01_inherit")
        .first()
    )
    assert entry is not None
    assert entry.release_channel == "candidate"
    assert entry.is_current_production is False
    assert entry.scoring_profile == "creative_scoring_v_test"


@pytest.mark.unit
def test_meta_andromeda_create_release_candidate_rejects_duplicate_model_version(meta_andromeda_access):
    """model_version 已存在於 registry（例如既有的 production/candidate/
    backtest_reference 版本）時應回 409，避免誤蓋掉既有設定。"""
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/release/candidates",
        json={
            # 種子資料裡既有的 current_production model_version
            "model_version": "prod_v2026_05_28",
            "provider": "openrouter",
            "provider_model": "some-org/duplicate-model:free",
        },
    )
    assert response.status_code == 409


@pytest.mark.unit
def test_meta_andromeda_created_candidate_can_be_approved_to_production(meta_andromeda_access, db, monkeypatch):
    """端到端：新增的候選版本可以直接走既有的 approve 流程上線，且 runtime
    的 model_registry 真的會切換過去（不是只有 release record 變了）。

    `model_registry._load_registry_from_db()` 內部用 `from database import
    SessionLocal` 開全新 session（非 request-scoped 的 `db` fixture）——測試
    的 `db` fixture 是綁在單一 connection 上、測試結束才 rollback 的交易，
    另開一個 session 在 SQLite 下看不到這筆尚未真正 commit 到底層的資料，
    故需 monkeypatch `database.SessionLocal` 讓它改用同一個 session（同檔案
    第 2757 行既有測試已用過的手法）。

    另外，本機/測試環境的 `META_ANDROMEDA_SCORING_PROVIDER` 若設為
    "heuristic"（避免測試時打真實 API 的常見設定），`get_entry()` 會直接
    短路回傳硬編碼的 heuristic entry，完全跳過 DB registry 解析——這與本測試
    要驗證的「DB 是否真的切換」無關，故用 `monkeypatch.setenv` 暫時覆寫為
    "auto"。同時 `META_ANDROMEDA_SCORING_MODEL`（若設定為非空字串）在
    provider="auto" 時也會覆蓋 entry 的 `provider_model`（`get_entry()` 的
    ops escape hatch 設計），故一併清空，才能驗證「DB 裡真正存的
    provider_model」而不是被 env 覆寫後的值。"""
    from modules.meta_andromeda.model_registry import model_registry, invalidate_registry_cache

    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "auto")
    monkeypatch.setenv("META_ANDROMEDA_SCORING_MODEL", "")

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr("database.SessionLocal", lambda: SessionProxy(db))

    create_resp = meta_andromeda_access.post(
        "/api/meta-andromeda/release/candidates",
        json={
            "model_version": "cand_v2026_09_01_e2e",
            "provider": "openrouter",
            "provider_model": "some-org/e2e-model:free",
        },
    )
    assert create_resp.status_code == 201
    _mark_release_candidate_metrics(db, "cand_v2026_09_01_e2e", accuracy=0.64)

    approve_resp = meta_andromeda_access.post(
        "/api/meta-andromeda/release/approve",
        json={"model_version": "cand_v2026_09_01_e2e", "note": "approve manually created candidate"},
    )
    assert approve_resp.status_code == 200

    invalidate_registry_cache()
    entry = model_registry.get_entry()
    assert entry.model_version == "cand_v2026_09_01_e2e"
    assert entry.provider_model == "some-org/e2e-model:free"


@pytest.mark.unit
def test_effective_scoring_status_reports_no_override_when_env_matches_db(meta_andromeda_access, db, monkeypatch):
    """沒有任何 env override 生效時，resolved 應與 DB 的 production 列完全一致
    （`is_overridden=False`）——驗證比對邏輯本身在「一致」情境下不會誤報。"""
    from database.models.meta_andromeda import MetaAndromedaModelRegistryEntry
    from modules.meta_andromeda.model_registry import invalidate_registry_cache

    db.add(MetaAndromedaModelRegistryEntry(
        model_version="prod_test_effective_match",
        provider="openrouter",
        provider_model="some-org/effective-match:free",
        scoring_profile="creative_scoring_v_test",
        feature_manifest_id="fm_test_effective_match",
        release_channel="production",
        source_of_truth="datavue.meta_andromeda.registry",
        is_current_production=True,
    ))
    db.commit()

    # 清空所有可能生效的 env override，讓 get_entry() 原樣回傳 DB 該列
    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "auto")
    monkeypatch.setenv("META_ANDROMEDA_SCORING_MODEL", "")
    monkeypatch.delenv("META_ANDROMEDA_SCORING_MODEL_VERSION", raising=False)

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr("database.SessionLocal", lambda: SessionProxy(db))
    invalidate_registry_cache()

    response = meta_andromeda_access.get("/api/meta-andromeda/monitoring/model-registry/effective")
    assert response.status_code == 200
    body = response.json()
    assert body["is_overridden"] is False
    assert body["resolved_model_version"] == "prod_test_effective_match"
    assert body["resolved_provider_model"] == "some-org/effective-match:free"
    assert body["db_production_model_version"] == "prod_test_effective_match"
    assert body["db_production_provider_model"] == "some-org/effective-match:free"


@pytest.mark.unit
def test_effective_scoring_status_flags_override_from_env_model(meta_andromeda_access, db, monkeypatch):
    """`META_ANDROMEDA_SCORING_MODEL` 覆寫生效時（provider=auto 且 DB production
    的 provider 為 openrouter），resolved 應顯示 env 覆寫後的模型，`db_production_*`
    仍顯示 DB 原本存的值，`is_overridden=True`——這是這次新增端點要解決的核心
    情境：畫面（DB 值）與實際評分（env 覆寫後的值）不一致時要能被看出來。"""
    from database.models.meta_andromeda import MetaAndromedaModelRegistryEntry
    from modules.meta_andromeda.model_registry import invalidate_registry_cache

    db.add(MetaAndromedaModelRegistryEntry(
        model_version="prod_test_effective_override",
        provider="openrouter",
        provider_model="some-org/original-db-model:free",
        scoring_profile="creative_scoring_v_test",
        feature_manifest_id="fm_test_effective_override",
        release_channel="production",
        source_of_truth="datavue.meta_andromeda.registry",
        is_current_production=True,
    ))
    db.commit()

    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "auto")
    monkeypatch.setenv("META_ANDROMEDA_SCORING_MODEL", "some-org/env-forced-model:free")
    monkeypatch.delenv("META_ANDROMEDA_SCORING_MODEL_VERSION", raising=False)

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr("database.SessionLocal", lambda: SessionProxy(db))
    invalidate_registry_cache()

    response = meta_andromeda_access.get("/api/meta-andromeda/monitoring/model-registry/effective")
    assert response.status_code == 200
    body = response.json()
    assert body["is_overridden"] is True
    assert body["resolved_provider_model"] == "some-org/env-forced-model:free"
    assert body["db_production_model_version"] == "prod_test_effective_override"
    assert body["db_production_provider_model"] == "some-org/original-db-model:free"
    assert body["scoring_model_setting"] == "some-org/env-forced-model:free"


@pytest.mark.unit
def test_validate_candidate_model_reports_ok_for_valid_model(meta_andromeda_access, monkeypatch):
    """換模型前先查：真的存在、支援圖片輸入、context/輸出上限都夠的模型應該回 ok=True。"""
    from modules.meta_andromeda import model_catalog

    monkeypatch.setattr(model_catalog, "_fetch_catalog", lambda force_refresh=False: {
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": {
            "id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "name": "NVIDIA: Nemotron 3 Nano Omni (free)",
            "context_length": 256000,
            "architecture": {"input_modalities": ["text", "image", "video"], "output_modalities": ["text"]},
            "top_provider": {"context_length": 256000, "max_completion_tokens": 65536},
            "pricing": {"prompt": "0", "completion": "0"},
        },
    })

    response = meta_andromeda_access.get(
        "/api/meta-andromeda/monitoring/model-registry/validate-candidate",
        params={"model_id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is True
    assert body["ok"] is True
    assert body["issues"] == []
    assert body["supports_image_input"] is True
    assert body["context_length"] == 256000
    assert body["max_completion_tokens"] == 65536
    assert body["is_free"] is True


@pytest.mark.unit
def test_validate_candidate_model_reports_not_found(meta_andromeda_access, monkeypatch):
    """查無此模型 ID（打錯字/已下架/根本不是真的模型）應該明確回報，而不是讓 ops
    直到跑評分才發現（2026-07-10 事故：`llama-nemotron-embed-vl-1b-v2:free` 就是這種）。"""
    from modules.meta_andromeda import model_catalog

    monkeypatch.setattr(model_catalog, "_fetch_catalog", lambda force_refresh=False: {})

    response = meta_andromeda_access.get(
        "/api/meta-andromeda/monitoring/model-registry/validate-candidate",
        params={"model_id": "nvidia/llama-nemotron-embed-vl-1b-v2:free"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is False
    assert body["ok"] is False
    assert body["issues"]


@pytest.mark.unit
def test_validate_candidate_model_flags_missing_image_support_and_narrow_context(meta_andromeda_access, monkeypatch):
    """存在但不支援圖片輸入、或端點 context/輸出上限太小的模型，應該被標記出來
    （不是直接判定不存在，而是明確列出「能不能用」的具體理由）。"""
    from modules.meta_andromeda import model_catalog

    monkeypatch.setattr(model_catalog, "_fetch_catalog", lambda force_refresh=False: {
        "some-org/text-only-narrow:free": {
            "id": "some-org/text-only-narrow:free",
            "name": "Text Only Narrow",
            "context_length": 10240,
            "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]},
            "top_provider": {"context_length": 10240, "max_completion_tokens": 4096},
            "pricing": {"prompt": "0", "completion": "0"},
        },
    })

    response = meta_andromeda_access.get(
        "/api/meta-andromeda/monitoring/model-registry/validate-candidate",
        params={"model_id": "some-org/text-only-narrow:free"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is True
    assert body["ok"] is False
    assert body["supports_image_input"] is False
    assert len(body["issues"]) == 3  # 不支援圖片 + context 太窄 + 輸出上限太小
