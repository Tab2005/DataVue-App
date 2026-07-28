"""GA4 insights snapshot share-link tests (docs/39)."""

from modules.ga4.dependencies import require_ga4_insights_view, require_ga4_module
from modules.ga4.insights_router import get_current_user
from database.models.ga4_insights import GA4InsightsSnapshot


def _override_dependencies(app, user, db):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_ga4_module] = lambda: True
    app.dependency_overrides[require_ga4_insights_view] = lambda: True


def _make_snapshot(db, **overrides):
    row = GA4InsightsSnapshot(
        property_id="123456",
        kind="daily_channel",
        date="2026-07-20",
        payload={"dimension": "default_channel_group", "channels": [{"channel": "Direct", "assisting_conversions": 3, "closing_conversions": 5, "ratio": 0.6, "tag": "closer"}]},
        ai_summary="## 一句話總結\n測試摘要",
        **overrides,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_create_share_link_is_idempotent(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)
    snapshot = _make_snapshot(db)

    first = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share")
    assert first.status_code == 200
    token = first.json()["share_token"]
    assert token

    second = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share")
    assert second.status_code == 200
    assert second.json()["share_token"] == token


def test_create_share_link_404_for_missing_snapshot(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)
    resp = client.post("/api/ga4/insights/snapshots/does-not-exist/share")
    assert resp.status_code == 404


def test_get_shared_snapshot_is_public_and_includes_property_id(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)
    snapshot = _make_snapshot(db)
    created = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share")
    token = created.json()["share_token"]

    # 移除 auth 相關 overrides，模擬未登入的公開訪客請求（保留 get_db override，
    # 否則 app 會改用非測試用的真實 DB session）。
    client.app.dependency_overrides.pop(get_current_user, None)
    client.app.dependency_overrides.pop(require_ga4_module, None)
    client.app.dependency_overrides.pop(require_ga4_insights_view, None)

    shared = client.get(f"/api/ga4/insights/share/{token}")
    assert shared.status_code == 200
    body = shared.json()
    assert body["kind"] == "daily_channel"
    assert body["date"] == "2026-07-20"
    assert body["ai_summary"] == "## 一句話總結\n測試摘要"
    assert body["payload"]["channels"][0]["channel"] == "Direct"
    # docs/47 追加：property_id 改回傳，讓分享頁面能顯示是哪個 GA4 屬性的資料
    # （這個值本身不算內部隱私資訊，只有 fetched_by 這類使用者身份資訊才要排除）。
    assert body["property_id"] == "123456"
    assert "fetched_by" not in body


def test_get_shared_snapshot_404_for_unknown_token(client, db, sample_user):
    resp = client.get("/api/ga4/insights/share/does-not-exist")
    assert resp.status_code == 404
