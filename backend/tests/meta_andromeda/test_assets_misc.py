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
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
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
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_BACKEND", "s3_compatible")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_S3_BUCKET", "meta-andromeda-assets")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_S3_REGION", "ap-northeast-1")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL", "https://minio.example.com")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_KEY_PREFIX", "shared/meta-andromeda")
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL", "https://cdn.example.com/meta-andromeda")
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
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
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
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
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
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
def test_meta_andromeda_internal_asset_route_rejects_missing_auth(db, tmp_path, monkeypatch):
    monkeypatch.setenv("META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")

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
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")

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
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_BASE_URL", "http://meta-andromeda-worker.zeabur.internal")
    monkeypatch.setenv("META_ANDROMEDA_INTERNAL_WORKER_TOKEN", "worker-token")
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
    assert payload["summary"]["current_slice"] == "queue_host_observability_enabled"
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

    monkeypatch.setenv("META_ANDROMEDA_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setenv("META_ANDROMEDA_SCORING_PROVIDER", "openrouter")

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
