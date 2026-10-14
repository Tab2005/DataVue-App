"""
Ad Library 模組測試（docs/73）

  1. normalizer：單圖、影片、輪播、動態創意四種 creative 的文案攤平
  2. data_source：分頁、上限截斷、rate limit 部分成功
  3. service：圖片依 image_hash 去重只落地一次
  4. router：模組權限、帳號白名單 403、跨帳號 id 查詢 404
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from database import Module, Team, TeamMember, UserModuleAccess, UserRole
from database.models.ad_library import AdLibraryItem, AdLibraryRefreshJob
from database.models.meta_andromeda import MetaAndromedaAsset
from main import app
from modules.ad_library import data_source, service
from modules.ad_library.normalizer import normalize_ad
from modules.auth import dependencies as auth_dependencies
from modules.fb_ads import accounts_service


# ── 1. normalizer ──────────────────────────────────────────────────────
def test_normalize_single_image_ad():
    ad = {
        "id": "111",
        "name": "春季主打",
        "effective_status": "ACTIVE",
        "created_time": "2026-03-01T10:00:00+0800",
        "campaign": {"id": "c1", "name": "春季活動", "objective": "OUTCOME_SALES"},
        "creative": {
            "image_hash": "h1",
            "image_url": "https://cdn/img1.jpg",
            "object_story_spec": {
                "page_id": "p1",
                "link_data": {
                    "message": "限時 8 折",
                    "name": "立即選購",
                    "description": "全館免運",
                    "link": "https://shop.example.com",
                    "call_to_action": {"type": "SHOP_NOW"},
                },
            },
        },
        "insights": {"data": [{"impressions": "1200", "spend": "35.5", "clicks": "40", "ctr": "3.33"}]},
    }
    row = normalize_ad(ad, account_id="act_1")
    assert row["media_type"] == "image"
    assert row["primary_texts"] == ["限時 8 折"]
    assert row["headlines"] == ["立即選購"]
    assert row["descriptions"] == ["全館免運"]
    assert row["cta_types"] == ["SHOP_NOW"]
    assert row["link_url"] == "https://shop.example.com"
    assert row["page_id"] == "p1"
    assert row["media"] == [
        {"kind": "image", "fb_url": "https://cdn/img1.jpg", "image_hash": "h1", "video_id": None, "asset_id": None}
    ]
    assert row["impressions"] == 1200 and row["spend"] == 35.5
    assert row["ad_created_at"].hour == 2  # 轉成 UTC
    assert "限時 8 折" in row["search_text"]


def test_normalize_video_ad():
    ad = {
        "id": "222",
        "creative": {
            "video_id": "v1",
            "thumbnail_url": "https://cdn/thumb.jpg",
            "object_story_spec": {
                "video_data": {
                    "message": "看影片了解更多",
                    "title": "新品開箱",
                    "call_to_action": {"type": "LEARN_MORE", "value": {"link": "https://x.example"}},
                },
            },
        },
    }
    row = normalize_ad(ad, account_id="act_1")
    assert row["media_type"] == "video"
    assert row["primary_texts"] == ["看影片了解更多"]
    assert row["headlines"] == ["新品開箱"]
    assert row["link_url"] == "https://x.example"
    assert row["media"][0]["kind"] == "video_thumbnail"
    assert row["media"][0]["fb_url"] == "https://cdn/thumb.jpg"
    assert row["impressions"] == 0  # 無 insights


def test_normalize_carousel_ad():
    ad = {
        "id": "333",
        "creative": {
            "object_story_spec": {
                "link_data": {
                    "message": "三款熱銷",
                    "child_attachments": [
                        {"name": "A 款", "description": "藍", "picture": "https://cdn/a.jpg", "image_hash": "ha"},
                        {"name": "B 款", "description": "紅", "picture": "https://cdn/b.jpg", "image_hash": "hb"},
                        {"name": "A 款", "picture": "https://cdn/a.jpg", "image_hash": "ha"},
                    ],
                },
            },
        },
    }
    row = normalize_ad(ad, account_id="act_1")
    assert row["media_type"] == "carousel"
    assert row["headlines"] == ["A 款", "B 款"]
    assert row["descriptions"] == ["藍", "紅"]
    assert len(row["media"]) == 3


def test_normalize_dynamic_creative_keeps_all_variants():
    ad = {
        "id": "444",
        "creative": {
            "body": "fallback body",
            "asset_feed_spec": {
                "bodies": [{"text": "文案一"}, {"text": "文案二"}, {"text": "文案一"}],
                "titles": [{"text": "標題一"}, {"text": "標題二"}],
                "descriptions": [{"text": "說明"}],
                "call_to_action_types": ["SHOP_NOW", "LEARN_MORE"],
                "link_urls": [{"website_url": "https://dyn.example"}],
                "images": [{"hash": "d1", "url": "https://cdn/d1.jpg"}],
            },
        },
    }
    row = normalize_ad(ad, account_id="act_1")
    assert row["media_type"] == "dynamic"
    assert row["primary_texts"] == ["文案一", "文案二"]
    assert row["headlines"] == ["標題一", "標題二"]
    assert row["cta_types"] == ["SHOP_NOW", "LEARN_MORE"]
    assert row["link_url"] == "https://dyn.example"
    assert row["media"][0]["image_hash"] == "d1"


def test_normalize_falls_back_to_creative_body_title():
    ad = {"id": "555", "creative": {"body": "只有 body", "title": "只有 title", "call_to_action_type": "SIGN_UP"}}
    row = normalize_ad(ad, account_id="act_1")
    assert row["primary_texts"] == ["只有 body"]
    assert row["headlines"] == ["只有 title"]
    assert row["cta_types"] == ["SIGN_UP"]


# ── 2. data_source ─────────────────────────────────────────────────────
class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, pages):
        self._pages = list(pages)
        self.calls = 0

    async def get(self, url, headers=None, params=None):
        self.calls += 1
        return _FakeResp(self._pages.pop(0))


def _page(ids, next_url=None):
    payload = {"data": [{"id": i} for i in ids]}
    if next_url:
        payload["paging"] = {"next": next_url}
    return payload


@pytest.mark.asyncio
async def test_fetch_ads_paginates_and_respects_max():
    client = _FakeClient([_page(["1", "2"], "n1"), _page(["3", "4"], "n2"), _page(["5"])])
    seen = []

    async def on_page(ads):
        seen.extend(a["id"] for a in ads)

    with patch.object(data_source, "get_headers", return_value={"Authorization": "Bearer x"}), \
         patch.object(data_source, "INTER_PAGE_SLEEP_SEC", 0):
        result = await data_source.fetch_ads(
            "act_1", user_id="g", team_id=None, strict_token=True,
            on_page=on_page, max_ads=3, client=client,
        )
    assert seen == ["1", "2", "3"]
    assert result == {"fetched": 3, "truncated": True, "rate_limited": False}


@pytest.mark.asyncio
async def test_fetch_ads_rate_limit_after_first_page_is_partial():
    client = _FakeClient([_page(["1"], "n1"), {"error": {"code": 17, "message": "User request limit reached"}}])

    async def on_page(ads):
        pass

    with patch.object(data_source, "get_headers", return_value={"Authorization": "Bearer x"}), \
         patch.object(data_source, "INTER_PAGE_SLEEP_SEC", 0):
        result = await data_source.fetch_ads(
            "act_1", user_id="g", team_id=None, strict_token=True, on_page=on_page, client=client,
        )
    assert result["rate_limited"] is True and result["fetched"] == 1


@pytest.mark.asyncio
async def test_fetch_ads_without_token_raises():
    with patch.object(data_source, "get_headers", return_value=None):
        with pytest.raises(data_source.AdLibraryTokenError):
            await data_source.fetch_ads(
                "act_1", user_id="g", team_id=None, strict_token=True, on_page=AsyncMock(),
            )


@pytest.mark.asyncio
async def test_fetch_ads_error_on_first_page_raises():
    client = _FakeClient([{"error": {"code": 190, "message": "Invalid OAuth access token"}}])
    with patch.object(data_source, "get_headers", return_value={"Authorization": "Bearer x"}):
        with pytest.raises(data_source.AdLibraryAPIError):
            await data_source.fetch_ads(
                "act_1", user_id="g", team_id=None, strict_token=True, on_page=AsyncMock(), client=client,
            )


# ── 3. service：圖片去重 ───────────────────────────────────────────────
@pytest.mark.asyncio
async def test_media_resolver_dedupes_by_image_hash():
    download = AsyncMock(return_value=(b"img", "image/jpeg"))
    store = AsyncMock(return_value={"asset_id": "asset_1", "asset_uri": "uri_1"})
    with patch.object(service, "download_image", download), patch.object(service, "store_image", store):
        resolver = service._MediaResolver(known={}, uploaded_by="u1", client=None)
        entries = [
            {"kind": "image", "fb_url": "https://cdn/a.jpg?sig=1", "image_hash": "h1", "asset_id": None},
            {"kind": "image", "fb_url": "https://cdn/a.jpg?sig=2", "image_hash": "h1", "asset_id": None},
        ]
        import asyncio as _asyncio

        await _asyncio.gather(*(resolver.resolve(e) for e in entries))
    assert download.await_count == 1
    assert store.await_count == 1
    assert all(e["asset_id"] == "asset_1" for e in entries)
    assert resolver.stored == 1


@pytest.mark.asyncio
async def test_media_resolver_reuses_known_assets():
    download = AsyncMock()
    with patch.object(service, "download_image", download):
        resolver = service._MediaResolver(
            known={"hash:h1": {"asset_id": "old", "asset_uri": "old_uri"}}, uploaded_by="u1", client=None,
        )
        entry = {"kind": "image", "fb_url": "https://cdn/new.jpg", "image_hash": "h1", "asset_id": None}
        await resolver.resolve(entry)
    download.assert_not_awaited()
    assert entry["asset_id"] == "old"


# ── 4. router 授權 ─────────────────────────────────────────────────────
@pytest.fixture
def ad_library_client(client, db, sample_user):
    module = db.query(Module).filter(Module.key == "ad_library").first()
    if module is None:
        module = Module(key="ad_library", name="廣告文案庫", enabled=True, sort_order=6)
        db.add(module)
        db.flush()
    db.add(UserModuleAccess(user_id=sample_user.id, module_id=module.id, enabled=True))
    db.commit()

    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db
    app.dependency_overrides[auth_dependencies.get_current_team] = lambda: None
    yield client, sample_user
    app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_db, None)
    app.dependency_overrides.pop(auth_dependencies.get_current_team, None)


def _mine(ids=("act_mine",)):
    return patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": i, "name": i} for i in ids], None)),
    )


def _add_item(db, account_id, ad_id="1", **extra):
    item = AdLibraryItem(
        account_id=account_id, ad_id=ad_id, media_type="image",
        primary_texts=extra.pop("primary_texts", ["文案"]), headlines=[], descriptions=[], cta_types=[],
        media=extra.pop("media", []), impressions=extra.pop("impressions", 0), reach=0, clicks=0,
        spend=0.0, ctr=0.0, search_text=extra.pop("search_text", "文案"), **extra,
    )
    db.add(item)
    db.commit()
    return item


@pytest.mark.integration
def test_without_module_access_is_forbidden(client, db, sample_user):
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: sample_user
    app.dependency_overrides[auth_dependencies.get_db] = lambda: db
    try:
        resp = client.get("/api/ad-library/ping")
    finally:
        app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
        app.dependency_overrides.pop(auth_dependencies.get_db, None)
    assert resp.status_code == 403


@pytest.mark.integration
def test_list_ads_denies_account_outside_scope(ad_library_client):
    client, _ = ad_library_client
    with _mine():
        resp = client.get("/api/ad-library/ads?account_id=act_not_mine")
    assert resp.status_code == 403


@pytest.mark.integration
def test_export_and_refresh_deny_account_outside_scope(ad_library_client):
    client, _ = ad_library_client
    with _mine():
        assert client.get("/api/ad-library/ads/export?account_id=act_not_mine").status_code == 403
        assert client.post("/api/ad-library/refresh", json={"account_id": "act_not_mine"}).status_code == 403


@pytest.mark.integration
def test_list_ads_filters_and_sorts(ad_library_client, db):
    client, _ = ad_library_client
    _add_item(db, "act_mine", "1", impressions=10, search_text="夏季 特價", primary_texts=["夏季特價"])
    _add_item(db, "act_mine", "2", impressions=50, search_text="冬季 新品", primary_texts=["冬季新品"])
    _add_item(db, "act_other", "3", impressions=999)
    with _mine():
        resp = client.get("/api/ad-library/ads?account_id=act_mine&sort=impressions&order=desc")
        searched = client.get("/api/ad-library/ads?account_id=act_mine&q=夏季")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert [i["ad_id"] for i in body["items"]] == ["2", "1"]
    assert [i["ad_id"] for i in searched.json()["items"]] == ["1"]


@pytest.mark.integration
def test_get_ad_of_other_account_returns_404(ad_library_client, db):
    client, _ = ad_library_client
    item = _add_item(db, "act_other", "9")
    with _mine():
        resp = client.get(f"/api/ad-library/ads/{item.id}")
    assert resp.status_code == 404


@pytest.mark.integration
def test_refresh_job_of_other_account_returns_404(ad_library_client, db, sample_user):
    client, user = ad_library_client
    job = AdLibraryRefreshJob(account_id="act_other", requested_by=user.id, status="succeeded",
                              ads_fetched=0, media_stored=0)
    db.add(job)
    db.commit()
    with _mine():
        resp = client.get(f"/api/ad-library/refresh/{job.id}")
    assert resp.status_code == 404


@pytest.mark.integration
def test_media_of_other_account_returns_404(ad_library_client, db):
    client, _ = ad_library_client
    asset = MetaAndromedaAsset(
        asset_uri="ma://asset_x", storage_backend="filesystem", storage_key="k/x.jpg",
        asset_type="image", source_filename="x.jpg", checksum_sha256="0", file_size_bytes=1,
    )
    db.add(asset)
    db.commit()
    _add_item(db, "act_other", "7", media=[{"kind": "image", "asset_id": asset.id, "asset_uri": asset.asset_uri}])
    with _mine():
        resp = client.get(f"/api/ad-library/media/{asset.id}")
    assert resp.status_code == 404


@pytest.mark.integration
def test_media_not_referenced_by_ad_library_returns_404(ad_library_client, db):
    """只被 Meta Andromeda 使用、沒被任何廣告文案引用的素材不可經本端點讀取。"""
    client, _ = ad_library_client
    asset = MetaAndromedaAsset(
        asset_uri="ma://asset_y", storage_backend="filesystem", storage_key="k/y.jpg",
        asset_type="image", source_filename="y.jpg", checksum_sha256="0", file_size_bytes=1,
    )
    db.add(asset)
    db.commit()
    with _mine():
        resp = client.get(f"/api/ad-library/media/{asset.id}")
    assert resp.status_code == 404


@pytest.mark.integration
def test_refresh_creates_job_and_rejects_concurrent(ad_library_client, db):
    client, _ = ad_library_client
    with _mine(), patch("modules.ad_library.router.run_refresh", new=AsyncMock()) as run:
        first = client.post("/api/ad-library/refresh", json={"account_id": "act_mine"})
        second = client.post("/api/ad-library/refresh", json={"account_id": "act_mine"})
    assert first.status_code == 202
    assert first.json()["status"] == "queued"
    assert run.await_count == 1
    assert second.status_code == 409


@pytest.mark.integration
def test_accounts_applies_team_whitelist(ad_library_client, db):
    client, user = ad_library_client
    team = Team(name="Whitelist Team", owner_id="someone_else",
                visible_ad_account_ids=json.dumps(["act_ok"]))
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role=UserRole.VIEWER))
    db.commit()
    app.dependency_overrides[auth_dependencies.get_current_team] = lambda: team
    with _mine(("act_ok", "act_hidden")):
        resp = client.get("/api/ad-library/accounts")
    assert resp.status_code == 200
    assert [a["id"] for a in resp.json()] == ["act_ok"]
