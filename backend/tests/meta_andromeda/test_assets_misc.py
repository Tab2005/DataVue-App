from .conftest import *  # noqa: F401,F403


@pytest.mark.unit
def test_meta_andromeda_ping_returns_payload(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/ping")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["module"] == "meta_andromeda"


@pytest.mark.unit
def test_meta_andromeda_upload_persists_file_to_storage_root(meta_andromeda_access, db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
    _install_internal_worker_httpx_proxy(monkeypatch, db)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={
            "asset_type": "image",
            "source_filename": "creative-test.png",
        },
        files={"file": ("creative-test.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["storage_backend"] == "filesystem"
    assert payload["storage_key"].endswith("creative-test.png")
    stored_path = tmp_path / payload["storage_key"]
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"fake-image-bytes"


@pytest.mark.unit
def test_meta_andromeda_upload_supports_s3_compatible_storage(meta_andromeda_access, db, monkeypatch):
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_BACKEND", "s3_compatible")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_S3_BUCKET", "meta-andromeda-assets")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_S3_REGION", "ap-northeast-1")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL", "https://minio.example.com")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_KEY_PREFIX", "shared/meta-andromeda")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL", "https://cdn.example.com/meta-andromeda")
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
    _install_internal_worker_httpx_proxy(monkeypatch, db)

    captured = {}

    class FakeS3Client:
        def upload_fileobj(self, Fileobj, Bucket, Key, ExtraArgs=None):
            captured["bytes"] = Fileobj.read()
            captured["bucket"] = Bucket
            captured["key"] = Key
            captured["extra_args"] = ExtraArgs or {}

    monkeypatch.setattr(
        meta_andromeda_storage_module.MetaAndromedaStorageAdapter,
        "_build_s3_client",
        lambda: FakeS3Client(),
    )

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={
            "asset_type": "image",
            "source_filename": "creative-object.png",
        },
        files={"file": ("creative-object.png", b"object-image-bytes", "image/png")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["storage_backend"] == "s3_compatible"
    assert payload["storage_key"].startswith("shared/meta-andromeda/uploads/")
    assert payload["public_url"].startswith("https://cdn.example.com/meta-andromeda/")
    assert captured["bucket"] == "meta-andromeda-assets"
    assert captured["bytes"] == b"object-image-bytes"
    assert captured["extra_args"]["ContentType"] == "image/png"


@pytest.mark.unit
def test_meta_andromeda_preview_proxies_filesystem_asset_from_internal_worker(meta_andromeda_access, db, tmp_path, monkeypatch):
    # SERVICE_ROLE=all 時預覽直接本地回應（不經 worker 代理）；要驗證
    # 「經內部 worker 代理」路徑必須切到 web 角色（見 scoring_assets.py）。
    monkeypatch.setattr(settings, "SERVICE_ROLE", "web")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
    _install_internal_worker_httpx_proxy(monkeypatch, db)

    upload_response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={"asset_type": "image", "source_filename": "preview-proxy.png"},
        files={"file": ("preview-proxy.png", b"proxy-image-bytes", "image/png")},
    )
    assert upload_response.status_code == 201
    payload = upload_response.json()

    response = meta_andromeda_access.get("/api/meta-andromeda/assets/preview", params={"uri": payload["asset_uri"]})

    assert response.status_code == 200
    assert response.content == b"proxy-image-bytes"
    assert response.headers["content-type"].startswith("image/png")
    assert response.headers["x-meta-andromeda-storage-key"] == payload["storage_key"]


@pytest.mark.unit
def test_meta_andromeda_preview_returns_404_when_internal_worker_returns_404(meta_andromeda_access, db, tmp_path, monkeypatch):
    # 同上：只有非 all 角色才會走 proxy_asset_preview_response 代理路徑。
    monkeypatch.setattr(settings, "SERVICE_ROLE", "web")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
    _install_internal_worker_httpx_proxy(monkeypatch, db)

    upload_response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={"asset_type": "image", "source_filename": "preview-local-fallback.png"},
        files={"file": ("preview-local-fallback.png", b"local-fallback-bytes", "image/png")},
    )
    assert upload_response.status_code == 201
    payload = upload_response.json()

    async def fake_proxy(uri: str):
        raise meta_andromeda_internal_gateway_module.MetaAndromedaInternalWorkerGatewayError(
            status_code=404,
            detail="Asset not found for URI",
        )

    monkeypatch.setattr(meta_andromeda_router_module, "proxy_asset_preview_response", fake_proxy)

    response = meta_andromeda_access.get("/api/meta-andromeda/assets/preview", params={"uri": payload["asset_uri"]})

    assert response.status_code == 404
    assert response.json()["detail"] == "Asset not found for URI"


@pytest.mark.unit
def test_meta_andromeda_preview_releases_db_connection_before_proxy_call(
    meta_andromeda_access, db, tmp_path, monkeypatch,
):
    """2026-08-07 事故修復驗證：preview_asset() 查完資產 metadata 後應該
    立刻釋放 DB 連線，才去打代理請求給 worker——不能讓連線一路握到跨服務
    HTTP 呼叫做完，否則審核佇列列表頁一次渲染 25 張縮圖、瀏覽器同時發出
    多個預覽請求時就會把連線池吃光（正式環境 pool_size=10+overflow=10，
    QueuePool 逾時 30 秒）。這裡直接攔截呼叫順序：db.close() 必須先於
    代理呼叫發生。"""
    from fastapi import Response

    monkeypatch.setattr(settings, "SERVICE_ROLE", "web")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
    _install_internal_worker_httpx_proxy(monkeypatch, db)

    upload_response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={"asset_type": "image", "source_filename": "close-order.png"},
        files={"file": ("close-order.png", b"close-order-bytes", "image/png")},
    )
    assert upload_response.status_code == 201
    payload = upload_response.json()

    call_order = []
    original_close = db.close

    def tracking_close():
        call_order.append("db_closed")
        return original_close()

    monkeypatch.setattr(db, "close", tracking_close)

    async def tracking_proxy(uri: str):
        call_order.append("proxy_called")
        return Response(content=b"ok", media_type="image/png")

    monkeypatch.setattr(meta_andromeda_router_module, "proxy_asset_preview_response", tracking_proxy)

    response = meta_andromeda_access.get(
        "/api/meta-andromeda/assets/preview", params={"uri": payload["asset_uri"]}
    )

    assert response.status_code == 200
    assert call_order == ["db_closed", "proxy_called"]


@pytest.mark.unit
def test_meta_andromeda_upload_releases_db_connection_before_proxy_call(
    meta_andromeda_access, db, tmp_path, monkeypatch,
):
    """2026-08-07 事故修復驗證（upload_asset 版本）：非 all 角色下的代理上傳
    分支完全不需要 db——但前面的 get_current_meta_andromeda_user /
    require_meta_andromeda_operate 依賴已經用同一個 session 查過使用者與
    權限，連線早已 checkout。應該在代理上傳給 worker（檔案可能比縮圖大
    很多，等待更久）之前就先釋放，而不是握到整個上傳完成才放。"""
    monkeypatch.setattr(settings, "SERVICE_ROLE", "web")
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
    _install_internal_worker_httpx_proxy(monkeypatch, db)

    call_order = []
    original_close = db.close

    def tracking_close():
        call_order.append("db_closed")
        return original_close()

    monkeypatch.setattr(db, "close", tracking_close)

    real_proxy = meta_andromeda_router_module.proxy_asset_upload_response

    async def tracking_proxy(**kwargs):
        call_order.append("proxy_called")
        return await real_proxy(**kwargs)

    monkeypatch.setattr(meta_andromeda_router_module, "proxy_asset_upload_response", tracking_proxy)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={"asset_type": "image", "source_filename": "upload-close-order.png"},
        files={"file": ("upload-close-order.png", b"upload-close-order-bytes", "image/png")},
    )

    assert response.status_code == 201
    assert call_order == ["db_closed", "proxy_called"]


@pytest.mark.unit
def test_meta_andromeda_internal_asset_route_rejects_missing_auth(db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")

    asset_record = meta_andromeda_storage_module.storage_adapter.store_asset(
        file_bytes=b"internal-image-bytes",
        asset_type="image",
        source_filename="internal-preview.png",
        uploaded_by=None,
        content_type="image/png",
    )
    created = repository.create_uploaded_asset(db, asset_record)

    test_app = FastAPI()
    test_app.include_router(meta_andromeda_internal_router)

    def override_get_db():
        yield db

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as client:
        response = client.get("/internal/meta-andromeda/assets/raw", params={"uri": created["asset_uri"]})

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_internal_worker_token"


@pytest.mark.unit
def test_meta_andromeda_internal_upload_route_rejects_missing_auth(db, monkeypatch):
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")

    test_app = FastAPI()
    test_app.include_router(meta_andromeda_internal_router)

    def override_get_db():
        yield db

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as client:
        response = client.post(
            "/internal/meta-andromeda/assets",
            data={
                "asset_type": "image",
                "source_filename": "blocked.png",
            },
            files={"file": ("blocked.png", b"blocked", "image/png")},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid_internal_worker_token"


@pytest.mark.unit
def test_meta_andromeda_upload_rejects_empty_file(meta_andromeda_access, db, monkeypatch):
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setattr(settings, "META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
    _install_internal_worker_httpx_proxy(monkeypatch, db)

    response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={
            "asset_type": "image",
            "source_filename": "empty.png",
        },
        files={"file": ("empty.png", b"", "image/png")},
    )

    assert response.status_code == 400
    assert (response.json().get("detail") or response.json().get("error")) == "upload_empty_file"


@pytest.mark.unit
def test_meta_andromeda_upload_rejects_mime_extension_mismatch(meta_andromeda_access):
    response = meta_andromeda_access.post(
        "/api/meta-andromeda/assets:upload",
        data={
            "asset_type": "image",
            "source_filename": "creative.png",
        },
        files={"file": ("creative.png", b"fake-bytes", "video/mp4")},
    )

    assert response.status_code == 415
    assert (response.json().get("detail") or response.json().get("error")) == "upload_mime_not_allowed"


@pytest.mark.unit
def test_meta_andromeda_overview_returns_current_integration_state(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"]["key"] == "meta_andromeda"
    assert payload["summary"]["integration_status"] == "in_progress"
    assert payload["summary"]["current_slice"] == "db_backed_scoring_profiles_and_calibration_pipeline"
    assert any(item["key"] == "review_queue" for item in payload["capabilities"])


@pytest.mark.unit
def test_meta_andromeda_monitoring_timeline_returns_event_detail(meta_andromeda_access):
    response = meta_andromeda_access.get("/api/meta-andromeda/monitoring/score-events/ma_evt_20260605_002/timeline")

    assert response.status_code == 200
    payload = response.json()
    assert payload["score_event"]["score_event_id"] == "ma_evt_20260605_002"
    assert "worker_events" in payload
    assert "dead_letters" in payload
    assert payload["feedback"]


@pytest.mark.unit
def test_meta_andromeda_monitoring_summary_does_not_reseed_read_path(meta_andromeda_access, db):
    from database.models.meta_andromeda import (
        MetaAndromedaDriftReport,
        MetaAndromedaScoreEvent,
        MetaAndromedaWorkerEvent,
    )

    _clear_meta_andromeda_operational_data(db)

    response = meta_andromeda_access.get("/api/meta-andromeda/monitoring/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["latest_drift_reports"] == []
    assert payload["worker_host"]["recent_events"] == []
    assert db.query(MetaAndromedaScoreEvent).count() == 0
    assert db.query(MetaAndromedaWorkerEvent).count() == 0
    assert db.query(MetaAndromedaDriftReport).count() == 0


@pytest.mark.asyncio
async def test_meta_andromeda_storage_image_is_encoded_and_sent_as_data_uri(
    db,
    sample_admin_user,
    tmp_path,
    monkeypatch,
):
    from database.models.meta_andromeda import MetaAndromedaAsset
    from modules.meta_andromeda.runtime import runtime_adapter
    from services.ai.openrouter_client import OpenRouterClient

    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY_ENV", "test-openrouter-key")
    monkeypatch.setattr(settings, "META_ANDROMEDA_SCORING_PROVIDER", "openrouter")

    storage_key = "uploads/test/base64-vision.png"
    stored_path = tmp_path / storage_key
    stored_path.parent.mkdir(parents=True, exist_ok=True)
    stored_path.write_bytes(b"fake-image-bytes-for-base64")

    asset = MetaAndromedaAsset(
        id="asset_base64_multimodal",
        asset_uri="storage://meta-andromeda/uploads/test/base64-vision.png",
        storage_backend="filesystem",
        storage_key=storage_key,
        asset_type="image",
        source_filename="base64-vision.png",
        checksum_sha256="checksum-base64-vision",
        file_size_bytes=len(b"fake-image-bytes-for-base64"),
        uploaded_by=sample_admin_user.id,
    )
    db.add(asset)
    db.commit()

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr("database.SessionLocal", lambda: SessionProxy(db))

    captured = {}

    def fake_init(self, api_key=None):
        self.api_key = api_key or "test-openrouter-key"
        self.client = object()
        self.model_name = "google/gemini-3.5-flash"

    def fake_generate_content(
        self,
        prompt,
        model,
        system_prompt,
        temperature,
        max_tokens,
        timeout_seconds,
        user_content,
    ):
        captured["model"] = model
        captured["user_content"] = user_content
        return json.dumps(
            {
                "overall_score": 83,
                "roas_band": "high",
                "top_positive_drivers": ["CTA 清楚"],
                "top_negative_drivers": ["文案略多"],
                "risk_tags": [],
                "diagnostic_breakdown": {"cta_presence": "清楚"},
                "summary": "模型已收到圖片資料。",
            }
        )

    monkeypatch.setattr(OpenRouterClient, "__init__", fake_init)
    monkeypatch.setattr(OpenRouterClient, "generate_content", fake_generate_content)

    result = await runtime_adapter.generate_score_result(
        {
            "asset_id": asset.id,
            "asset_uri": asset.asset_uri,
            "asset_type": "image",
            "request_mode": "auto",
            "objective": "purchase",
            "placement_family": "feed",
            "market": "TW",
            "request_context": {
                "headline": "限時優惠",
                "primary_text": "立即點擊",
                "cta": "Shop Now",
            },
        }
    )

    assert result["status"] == "completed"
    assert captured["model"]
    image_parts = [part for part in captured["user_content"] if part.get("type") == "image_url"]
    assert len(image_parts) == 1
    assert image_parts[0]["image_url"]["url"].startswith("data:image/png;base64,")


@pytest.mark.unit
def test_meta_andromeda_resolve_openrouter_key_uses_shared_per_user_lookup(db, sample_admin_user, monkeypatch):
    """docs/68 A4 修復驗證：resolve_openrouter_api_key_for_asset()（供
    calibration_pipeline 等直連 OpenRouter 的路徑使用）與
    _resolve_per_user_openrouter_key()（供 _prepare_asset_context 使用）
    現在共用同一段 asset → uploaded_by → user → TokenManager 查詢邏輯，
    對同一筆資產應解析出一致的個人金鑰，而不是各自實作一份、日後改一邊
    忘了改另一邊（2026-07-03 事故的成因）。"""
    from database.models.meta_andromeda import MetaAndromedaAsset
    from modules.auth.service import TokenManager
    from modules.meta_andromeda.runtime import (
        _resolve_per_user_openrouter_key,
        resolve_openrouter_api_key_for_asset,
    )

    asset = MetaAndromedaAsset(
        id="asset_a4_per_user_key",
        asset_uri="storage://meta-andromeda/uploads/a4-test.png",
        storage_backend="filesystem",
        storage_key="uploads/a4-test.png",
        asset_type="image",
        source_filename="a4-test.png",
        checksum_sha256="checksum-a4-test",
        file_size_bytes=100,
        uploaded_by=sample_admin_user.id,
    )
    db.add(asset)
    db.commit()

    monkeypatch.setattr(
        TokenManager, "get_ai_api_key", staticmethod(lambda google_id, provider=None: "per-user-fake-key")
    )

    assert _resolve_per_user_openrouter_key(db, asset) == "per-user-fake-key"
    assert resolve_openrouter_api_key_for_asset(db, asset.id) == "per-user-fake-key"


@pytest.mark.unit
def test_meta_andromeda_resolve_openrouter_key_falls_back_when_no_per_user_key(db, monkeypatch):
    """docs/68 A4：資產無上傳者時，resolve_openrouter_api_key_for_asset()
    應退回 settings.OPENROUTER_API_KEY，而 _resolve_per_user_openrouter_key()
    則維持回傳 None——這個區分是 _prepare_asset_context() 用來判斷「這把金鑰
    究竟是不是使用者自己的」所需要的語意，合併重複邏輯時不能弄丟。"""
    from database.models.meta_andromeda import MetaAndromedaAsset
    from modules.meta_andromeda.runtime import (
        _resolve_per_user_openrouter_key,
        resolve_openrouter_api_key_for_asset,
    )

    monkeypatch.setattr(settings, "OPENROUTER_API_KEY_ENV", "env-fallback-key")

    asset_without_uploader = MetaAndromedaAsset(
        id="asset_a4_no_uploader",
        asset_uri="storage://meta-andromeda/uploads/a4-no-uploader.png",
        storage_backend="filesystem",
        storage_key="uploads/a4-no-uploader.png",
        asset_type="image",
        source_filename="a4-no-uploader.png",
        checksum_sha256="checksum-a4-no-uploader",
        file_size_bytes=100,
        uploaded_by=None,
    )
    db.add(asset_without_uploader)
    db.commit()

    assert _resolve_per_user_openrouter_key(db, asset_without_uploader) is None
    assert resolve_openrouter_api_key_for_asset(db, asset_without_uploader.id) == "env-fallback-key"
    # asset_id 為 None（未指定素材）時同樣直接退回設定值。
    assert resolve_openrouter_api_key_for_asset(db, None) == "env-fallback-key"


@pytest.mark.unit
def test_meta_andromeda_prepare_asset_context_blocks_path_traversal_outside_storage_root(
    db, sample_admin_user, tmp_path, monkeypatch, caplog,
):
    """docs/68 A6 修復驗證：storage_key 解析後若跑出 storage root 之外
    （路徑穿越），is_relative_to() 應正確判斷為 False 並乾淨地跳過讀檔。

    修復前的安全結果其實「碰巧」一樣正確——relative_to() 對不在 root 底下
    的路徑是拋 ValueError，被外層籠統的 except Exception 吃掉，一樣不會讀到
    檔案——但語意是錯的：那個例外會被誤記錄成「Base64 encoding failed」，
    掩蓋了這其實是一次路徑穿越嘗試。這裡除了驗證素材內容沒被讀出來，也用
    caplog 驗證「不會產生那則誤導性錯誤訊息」，這才是本次修復實際改變的
    可觀察行為（修復前這個測試若只斷言 asset_public_url 不會通過，因為
    舊寫法本來就意外擋得住）。"""
    import logging

    from database.models.meta_andromeda import MetaAndromedaAsset
    from modules.meta_andromeda.runtime import MetaAndromedaRuntimeAdapter

    storage_root = tmp_path / "storage_root"
    storage_root.mkdir()
    monkeypatch.setattr(settings, "META_ANDROMEDA_STORAGE_ROOT", str(storage_root))

    # storage root 之外放一個真實檔案，storage_key 用 ../ 試圖跳出去讀它。
    outside_secret = tmp_path / "outside_secret.png"
    outside_secret.write_bytes(b"should-not-be-readable")

    asset = MetaAndromedaAsset(
        id="asset_path_traversal",
        asset_uri="storage://meta-andromeda/../outside_secret.png",
        storage_backend="filesystem",
        storage_key="../outside_secret.png",
        asset_type="image",
        source_filename="outside_secret.png",
        checksum_sha256="checksum-outside-secret",
        file_size_bytes=len(b"should-not-be-readable"),
        uploaded_by=sample_admin_user.id,
        public_url="https://cdn.example.com/fallback.png",
    )
    db.add(asset)
    db.commit()

    class SessionProxy:
        def __init__(self, session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def close(self):
            return None

    monkeypatch.setattr("database.SessionLocal", lambda: SessionProxy(db))

    score_payload = {"asset_id": asset.id, "request_context": {}}
    with caplog.at_level(logging.ERROR):
        MetaAndromedaRuntimeAdapter._prepare_asset_context(score_payload)

    request_context = score_payload["request_context"]
    # 路徑穿越被擋下：asset_public_url 應維持 fallback 的 public_url，
    # 而不是被替換成讀到 outside_secret.png 內容編碼出的 base64 data URI。
    assert request_context["asset_public_url"] == "https://cdn.example.com/fallback.png"
    assert "base64," not in (request_context.get("asset_public_url") or "")
    # 修復前 relative_to() 拋出的 ValueError 會被誤記錄成「Base64 encoding
    # failed」，把一次路徑穿越嘗試偽裝成無害的編碼錯誤；修復後 is_relative_to()
    # 乾淨地判斷為 False、不進入 except 分支，不應該有這則誤導性錯誤訊息。
    assert not any("Base64 encoding failed" in record.message for record in caplog.records)


def test_meta_andromeda_image_auto_compression():
    import io
    from PIL import Image, ImageDraw
    from modules.meta_andromeda.service import MetaAndromedaService

    # 1. 生成一個大於 400KB 的大圖片以觸發壓縮
    img = Image.new("RGB", (1500, 1500), color="blue")
    draw = ImageDraw.Draw(img)
    # 加入高頻噪點線條使檔案增大
    for i in range(0, 1500, 4):
        draw.line((0, i, 1500, i), fill="red", width=2)
        draw.line((i, 0, i, 1500), fill="green", width=2)
        
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    large_bytes = buf.getvalue()
    
    # 確保產生的測試圖大於 400KB
    assert len(large_bytes) > 400 * 1024

    # 2. 調用壓縮功能
    compressed_bytes = MetaAndromedaService._compress_image(
        large_bytes, "test_large.jpg", "image/jpeg"
    )

    # 3. 驗證壓縮結果
    assert len(compressed_bytes) < len(large_bytes)

    # 讀取壓縮後的圖片，確認尺寸最長邊被限制在 1200 像素以內
    compressed_img = Image.open(io.BytesIO(compressed_bytes))
    width, height = compressed_img.size
    assert max(width, height) <= 1200
