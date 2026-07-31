"""
GA4 分享連結凍結副本測試（docs/61；修 docs/59 P0-1）

docs/59 P0-1 的重現情境：

    使用者開啟到達頁分頁          → 建立快照
    產生 AI 解讀                  → ai_summary 寫入
    產生分享連結、寄給客戶        → share_token 建立
    使用者當天再次開啟同一個分頁  → upsert 覆寫 payload、ai_summary 被清成 None
    客戶此時打開連結              → 連結有效，但解讀是空的，數字也跟寄出時不同

原因是 `share_token` 掛在會被 upsert 覆寫的工作快照上。docs/61 改成分享當下
複製一份不可變副本，token 掛在副本上。本檔用**同一個情境**驗證修好了。
"""

import importlib.util
from pathlib import Path

import pytest

from database.models.ga4_insights import GA4InsightsSnapshot, GA4SharedSnapshot
from modules.ga4.dependencies import require_ga4_insights_view, require_ga4_module
from modules.ga4.insights_router import get_current_user
from modules.ga4.repository import repository

PROPERTY_ID = "123456"
KIND = "landing_page"
DATE = "2026-07-20"


def _override_dependencies(app, user):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_ga4_module] = lambda: True
    app.dependency_overrides[require_ga4_insights_view] = lambda: True


def _drop_auth_overrides(app):
    """模擬未登入的公開訪客（保留 get_db override，否則會連到真實 DB）。"""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_ga4_module, None)
    app.dependency_overrides.pop(require_ga4_insights_view, None)


def _make_snapshot(db, user, *, sessions=100, ai_summary=None):
    row = GA4InsightsSnapshot(
        property_id=PROPERTY_ID,
        kind=KIND,
        date=DATE,
        payload={"landing_pages": [{"landingPage": "/shop", "sessions": sessions}]},
        ai_summary=ai_summary,
        fetched_by=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _reload_tab(db, user, *, sessions):
    """模擬使用者重新載入分頁：走真正的 upsert_snapshot，不是手動改欄位。"""
    row = repository.upsert_snapshot(
        db,
        property_id=PROPERTY_ID,
        kind=KIND,
        date=DATE,
        payload={"landing_pages": [{"landingPage": "/shop", "sessions": sessions}]},
        fetched_by=user.id,
    )
    db.commit()
    db.refresh(row)
    return row


# ─── docs/59 P0-1 的原始重現情境 ────────────────────────────────────
@pytest.mark.integration
def test_shared_link_is_frozen_against_tab_reload(client, db, sample_user, ga4_property_access):
    """分享後重新載入分頁，連結內容必須維持分享當下的樣子。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user, sessions=100, ai_summary="## 一句話總結\n寄出時的解讀")

    token = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()["share_token"]

    # 使用者當天再次開啟同一個分頁：payload 換成 137、ai_summary 被清成 None
    reloaded = _reload_tab(db, sample_user, sessions=137)
    assert reloaded.id == snapshot.id           # 確實是同一列被覆寫（upsert 語意沒變）
    assert reloaded.ai_summary is None
    assert reloaded.payload["landing_pages"][0]["sessions"] == 137

    _drop_auth_overrides(client.app)
    shared = client.get(f"/api/ga4/insights/share/{token}")

    assert shared.status_code == 200
    body = shared.json()
    # 修好前這裡會是 137 / None
    assert body["payload"]["landing_pages"][0]["sessions"] == 100
    assert body["ai_summary"] == "## 一句話總結\n寄出時的解讀"
    assert body["property_id"] == PROPERTY_ID
    assert body["kind"] == KIND
    assert body["date"] == DATE


@pytest.mark.integration
def test_shared_link_is_frozen_against_later_ai_summary_rewrite(
    client, db, sample_user, ga4_property_access
):
    """分享後把來源快照的 AI 解讀改掉，已分享的連結不受影響。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user, ai_summary="分享當下的解讀")

    token = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()["share_token"]

    client.put(
        f"/api/ga4/insights/snapshots/{snapshot.id}/ai-summary",
        json={"ai_summary": "後來重新解讀的內容"},
    )

    _drop_auth_overrides(client.app)
    body = client.get(f"/api/ga4/insights/share/{token}").json()
    assert body["ai_summary"] == "分享當下的解讀"


# ─── 重複點擊「產生分享連結」的語意 ─────────────────────────────────
@pytest.mark.integration
def test_resharing_unchanged_snapshot_reuses_the_same_token(
    client, db, sample_user, ga4_property_access
):
    """內容沒變就沿用同一個 token——連點兩下不該產生兩條連結。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user, ai_summary="解讀")

    first = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()
    second = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()

    assert first["share_token"] == second["share_token"]
    assert db.query(GA4SharedSnapshot).count() == 1


@pytest.mark.integration
def test_resharing_after_data_changed_freezes_a_new_copy(
    client, db, sample_user, ga4_property_access
):
    """重新載入拿到新數據後再分享，該分享的是眼前這份，且舊連結仍指向舊內容。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user, sessions=100, ai_summary="早上的解讀")

    old_token = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()["share_token"]

    _reload_tab(db, sample_user, sessions=137)
    new_token = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()["share_token"]

    assert new_token != old_token
    assert db.query(GA4SharedSnapshot).count() == 2

    _drop_auth_overrides(client.app)
    old_body = client.get(f"/api/ga4/insights/share/{old_token}").json()
    new_body = client.get(f"/api/ga4/insights/share/{new_token}").json()

    assert old_body["payload"]["landing_pages"][0]["sessions"] == 100
    assert old_body["ai_summary"] == "早上的解讀"
    assert new_body["payload"]["landing_pages"][0]["sessions"] == 137
    assert new_body["ai_summary"] is None  # upsert 已把來源的解讀清掉，凍結的就是這個狀態


# ─── 副本本身的性質 ─────────────────────────────────────────────────
@pytest.mark.integration
def test_shared_endpoint_does_not_leak_internal_fields(client, db, sample_user, ga4_property_access):
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user, ai_summary="解讀")
    token = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()["share_token"]

    _drop_auth_overrides(client.app)
    body = client.get(f"/api/ga4/insights/share/{token}").json()

    for leaked in ("fetched_by", "created_by", "source_snapshot_id", "id"):
        assert leaked not in body


@pytest.mark.integration
def test_share_response_reports_source_snapshot_id(client, db, sample_user, ga4_property_access):
    """回應的 `snapshot_id` 仍是「被分享的那筆工作快照」（欄位語意不變），
    凍結副本自己的 id 另立欄位。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user)

    body = client.post(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()

    assert body["snapshot_id"] == snapshot.id
    assert body["shared_snapshot_id"].startswith("gss_")
    assert body["shared_snapshot_id"] != snapshot.id


@pytest.mark.integration
def test_unknown_share_token_returns_404(client, db, sample_user):
    assert client.get("/api/ga4/insights/share/does-not-exist").status_code == 404


# ─── migration 的資料搬移：既有連結不能失效 ─────────────────────────
def _load_migration_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "alembic" / "versions" / "20260731_ga4_shared_snapshots.py"
    )
    spec = importlib.util.spec_from_file_location("ga4_shared_snapshots_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.integration
def test_migration_backfills_existing_share_links(client, db, sample_user):
    """docs/39 時代掛在工作快照上的舊 token，migration 後仍要能打得開。"""
    migration = _load_migration_module()

    legacy = GA4InsightsSnapshot(
        property_id=PROPERTY_ID,
        kind=KIND,
        date=DATE,
        payload={"landing_pages": [{"landingPage": "/shop", "sessions": 42}]},
        ai_summary="舊連結的解讀",
        share_token="legacy_token_abc",
        fetched_by=sample_user.id,
    )
    db.add(legacy)
    db.commit()

    migration._backfill_existing_share_links(db.connection())
    db.commit()

    copied = db.query(GA4SharedSnapshot).filter_by(share_token="legacy_token_abc").one()
    assert copied.payload["landing_pages"][0]["sessions"] == 42
    assert copied.ai_summary == "舊連結的解讀"
    assert copied.source_snapshot_id == legacy.id

    # 舊連結透過公開端點仍打得開
    resp = client.get("/api/ga4/insights/share/legacy_token_abc")
    assert resp.status_code == 200
    assert resp.json()["ai_summary"] == "舊連結的解讀"


@pytest.mark.integration
def test_migration_backfill_is_idempotent(db, sample_user):
    """重跑 migration 不該把同一個 token 搬第二次（unique 會炸）。"""
    migration = _load_migration_module()

    db.add(GA4InsightsSnapshot(
        property_id=PROPERTY_ID, kind=KIND, date=DATE,
        payload={"x": 1}, share_token="legacy_token_xyz", fetched_by=sample_user.id,
    ))
    db.commit()

    migration._backfill_existing_share_links(db.connection())
    db.commit()
    migration._backfill_existing_share_links(db.connection())
    db.commit()

    assert db.query(GA4SharedSnapshot).filter_by(share_token="legacy_token_xyz").count() == 1
