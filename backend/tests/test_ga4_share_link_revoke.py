"""
GA4 分享連結撤銷測試（docs/63；修 docs/59 P1-3）

docs/59 P1-3：`share_token` 一旦產生就永久有效，沒有 revoke 端點——
「對一個『把 GA4 數據公開給未登入者』的功能來說⋯⋯誤發給錯的人之後沒有任何
補救手段。」

本檔驗證新增的 `DELETE /snapshots/{id}/share`：

  1. 撤銷後公開端點立刻 404
  2. 以「來源快照」為單位整組撤銷（凍結模式下同一分頁會累積多條連結）
  3. 撤銷是軟刪除——列與 payload 保留，只是 `revoked_at` 有值
  4. **撤銷後再分享不會沿用被撤銷的 token**（否則撤銷等於被悄悄還原）
  5. 可重複執行、跨快照不誤傷、授權沿用 docs/60 的屬性檢查
"""

import pytest

from database.models.ga4_insights import GA4InsightsSnapshot, GA4SharedSnapshot
from modules.ga4.dependencies import require_ga4_insights_view, require_ga4_module
from modules.ga4.insights_router import get_current_user
from modules.ga4.repository import repository

PROPERTY_ID = "123456"
OTHER_PROPERTY_ID = "999999"
KIND = "landing_page"
DATE = "2026-07-20"


def _override_dependencies(app, user):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_ga4_module] = lambda: True
    app.dependency_overrides[require_ga4_insights_view] = lambda: True


def _drop_auth_overrides(app):
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(require_ga4_module, None)
    app.dependency_overrides.pop(require_ga4_insights_view, None)


def _make_snapshot(db, user, *, property_id=PROPERTY_ID, kind=KIND, sessions=100, ai_summary="解讀"):
    row = GA4InsightsSnapshot(
        property_id=property_id, kind=kind, date=DATE,
        payload={"landing_pages": [{"landingPage": "/shop", "sessions": sessions}]},
        ai_summary=ai_summary, fetched_by=user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _share(client, snapshot_id):
    resp = client.post(f"/api/ga4/insights/snapshots/{snapshot_id}/share")
    assert resp.status_code == 200
    return resp.json()["share_token"]


@pytest.mark.integration
def test_revoke_makes_shared_link_return_404(client, db, sample_user, ga4_property_access):
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user)
    token = _share(client, snapshot.id)

    # 撤銷前連結可用
    _drop_auth_overrides(client.app)
    assert client.get(f"/api/ga4/insights/share/{token}").status_code == 200

    _override_dependencies(client.app, sample_user)
    resp = client.delete(f"/api/ga4/insights/snapshots/{snapshot.id}/share")
    assert resp.status_code == 200
    assert resp.json() == {"status": "revoked", "snapshot_id": snapshot.id, "revoked_count": 1}

    _drop_auth_overrides(client.app)
    assert client.get(f"/api/ga4/insights/share/{token}").status_code == 404


@pytest.mark.integration
def test_revoke_is_a_soft_delete_that_keeps_the_record(client, db, sample_user, ga4_property_access):
    """治理需求：要查得出「什麼內容曾經被公開出去、何時收回」，所以列與
    payload 都保留，只是標記 revoked_at。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user, sessions=137)
    token = _share(client, snapshot.id)

    client.delete(f"/api/ga4/insights/snapshots/{snapshot.id}/share")

    row = db.query(GA4SharedSnapshot).filter_by(share_token=token).one()
    assert row.revoked_at is not None
    assert row.payload["landing_pages"][0]["sessions"] == 137   # 內容仍留存可稽核


@pytest.mark.integration
def test_revoke_covers_every_link_created_from_the_snapshot(client, db, sample_user, ga4_property_access):
    """凍結模式下同一個分頁每次改動後再分享都會多一條連結（docs/61），
    而 UI 沒有「我發過哪些連結」的清單——撤銷必須是整組，否則收不乾淨。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user, sessions=100)
    first_token = _share(client, snapshot.id)

    # 模擬重新載入分頁拿到新數據後再分享 → 第二條連結
    repository.upsert_snapshot(
        db, property_id=PROPERTY_ID, kind=KIND, date=DATE,
        payload={"landing_pages": [{"landingPage": "/shop", "sessions": 137}]},
        fetched_by=sample_user.id,
    )
    db.commit()
    second_token = _share(client, snapshot.id)
    assert second_token != first_token

    resp = client.delete(f"/api/ga4/insights/snapshots/{snapshot.id}/share")
    assert resp.json()["revoked_count"] == 2

    _drop_auth_overrides(client.app)
    assert client.get(f"/api/ga4/insights/share/{first_token}").status_code == 404
    assert client.get(f"/api/ga4/insights/share/{second_token}").status_code == 404


@pytest.mark.integration
def test_resharing_after_revoke_issues_a_brand_new_token(client, db, sample_user, ga4_property_access):
    """關鍵：撤銷後再分享**不可**沿用被撤銷的 token——否則撤銷等於被悄悄還原，
    原本已經失效的連結會突然又能打開。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user)
    old_token = _share(client, snapshot.id)

    client.delete(f"/api/ga4/insights/snapshots/{snapshot.id}/share")

    # 內容完全沒變（沿用 token 的條件成立），但舊的已撤銷，必須另發一條
    new_token = _share(client, snapshot.id)
    assert new_token != old_token

    _drop_auth_overrides(client.app)
    assert client.get(f"/api/ga4/insights/share/{old_token}").status_code == 404
    assert client.get(f"/api/ga4/insights/share/{new_token}").status_code == 200


@pytest.mark.integration
def test_revoke_is_repeatable_and_reports_zero_when_nothing_active(
    client, db, sample_user, ga4_property_access
):
    """可重複執行：使用者連按兩次撤銷不該看到錯誤；從未分享過也不回 404
    （否則「這個快照有沒有分享過」會從狀態碼洩漏出去）。"""
    _override_dependencies(client.app, sample_user)
    snapshot = _make_snapshot(db, sample_user)

    never_shared = client.delete(f"/api/ga4/insights/snapshots/{snapshot.id}/share")
    assert never_shared.status_code == 200
    assert never_shared.json()["revoked_count"] == 0

    _share(client, snapshot.id)
    assert client.delete(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()["revoked_count"] == 1
    assert client.delete(f"/api/ga4/insights/snapshots/{snapshot.id}/share").json()["revoked_count"] == 0


@pytest.mark.integration
def test_revoke_does_not_touch_other_snapshots_links(client, db, sample_user, ga4_property_access):
    _override_dependencies(client.app, sample_user)
    target = _make_snapshot(db, sample_user, kind="landing_page")
    bystander = _make_snapshot(db, sample_user, kind="item")

    target_token = _share(client, target.id)
    bystander_token = _share(client, bystander.id)

    client.delete(f"/api/ga4/insights/snapshots/{target.id}/share")

    _drop_auth_overrides(client.app)
    assert client.get(f"/api/ga4/insights/share/{target_token}").status_code == 404
    assert client.get(f"/api/ga4/insights/share/{bystander_token}").status_code == 200


@pytest.mark.integration
def test_revoke_on_other_property_snapshot_returns_404(client, db, sample_user, ga4_property_access):
    """授權沿用 docs/60：別人屬性的快照回 404，且該連結不受影響。

    別人的快照必須 `fetched_by` 不是自己——否則「這個使用者抓過這個 property」
    的快路徑會成立，那就不是跨租戶情境了。分享副本直接經 repository 建立，
    因為攻擊者本來就無法透過端點對別人的屬性產生連結。
    """
    _override_dependencies(client.app, sample_user)
    victim = GA4InsightsSnapshot(
        property_id=OTHER_PROPERTY_ID, kind=KIND, date=DATE,
        payload={"landing_pages": []}, ai_summary="別人的解讀", fetched_by=None,
    )
    db.add(victim)
    db.commit()
    db.refresh(victim)
    victim_copy = repository.create_shared_snapshot(db, source=victim)
    db.commit()
    token = victim_copy.share_token

    resp = client.delete(f"/api/ga4/insights/snapshots/{victim.id}/share")
    assert resp.status_code == 404
    assert resp.json()["error"] == "Snapshot not found"

    row = db.query(GA4SharedSnapshot).filter_by(share_token=token).one()
    assert row.revoked_at is None


@pytest.mark.integration
def test_revoke_on_missing_snapshot_returns_404(client, db, sample_user, ga4_property_access):
    _override_dependencies(client.app, sample_user)
    resp = client.delete("/api/ga4/insights/snapshots/does-not-exist/share")
    assert resp.status_code == 404
