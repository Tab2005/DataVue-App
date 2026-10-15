"""
Ad Library 動態素材元件成效測試（docs/74 第 3 階段）

1. asset_insights：breakdown 回傳列解析、要查哪些 breakdown
2. data_source.fetch_ad_asset_insights：分頁、單一 breakdown 失敗略過、rate limit 往外拋
3. service：刷新流程的元件成效階段
4. repository / router：寫入、對回既有元件、授權
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from database import Module, UserModuleAccess
from database.models.ad_library import AdLibraryAssetInsight, AdLibraryContent, AdLibraryItem
from main import app
from modules.ad_library import data_source, repository, service
from modules.ad_library.asset_insights import breakdowns_for_ad, parse_asset_rows
from modules.ad_library.fingerprint import text_fingerprint
from modules.auth import dependencies as auth_dependencies
from modules.fb_ads import accounts_service

from tests.test_ad_library_hierarchy import _FakeDb, _refresh_kwargs, _stage


# ── 1. asset_insights ──────────────────────────────────────────────────
def test_parse_body_asset_rows_matches_text_fingerprint():
    entries, skipped = parse_asset_rows("body_asset", [
        {"body_asset": {"text": "限時優惠！ ", "id": "605"}, "impressions": "100", "clicks": "5", "spend": "12.5", "reach": "80"},
        {"body_asset": {"text": "限時優惠!", "id": "605"}, "impressions": "50", "clicks": "1", "spend": "2", "reach": "90"},
        {"body_asset": {"text": "", "id": "606"}, "impressions": "9"},
    ])
    assert skipped == 1
    assert len(entries) == 1
    entry = entries[0]
    assert entry["kind"] == "primary_text"
    assert entry["fingerprint"] == text_fingerprint("限時優惠!")
    assert (entry["impressions"], entry["clicks"], entry["spend"], entry["reach"]) == (150, 6, 14.5, 90)
    assert entry["fb_asset_id"] == "605"


def test_parse_image_and_video_rows():
    images, skipped = parse_asset_rows("image_asset", [
        {"image_asset": {"hash": "h1", "url": "https://cdn/1.jpg", "id": "1"}, "impressions": "10"},
        {"image_asset": {"url": "https://cdn/2.jpg", "id": "2"}, "impressions": "10"},
    ])
    assert [e["fingerprint"] for e in images] == ["img:h1"] and skipped == 1
    # video_asset 欄位官方未寫明：只認 video_id，不拿 asset id 猜
    videos, skipped = parse_asset_rows("video_asset", [
        {"video_asset": {"video_id": "v1", "id": "9"}, "impressions": "10"},
        {"video_asset": {"id": "10"}, "impressions": "10"},
    ])
    assert [e["fingerprint"] for e in videos] == ["vid:v1"] and skipped == 1


def test_breakdowns_for_ad_only_queries_present_components():
    ad = {
        "primary_texts": ["a"], "headlines": [], "descriptions": ["d"],
        "media": [{"kind": "image"}, {"kind": "video_thumbnail"}],
    }
    assert breakdowns_for_ad(ad) == ["body_asset", "description_asset", "image_asset", "video_asset"]
    assert breakdowns_for_ad({"primary_texts": [], "media": []}) == []


# ── 2. data_source ─────────────────────────────────────────────────────
class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, pages):
        self._pages = list(pages)
        self.params = []

    async def get(self, url, headers=None, params=None):
        self.params.append(params)
        return _FakeResp(self._pages.pop(0))


@pytest.mark.asyncio
async def test_fetch_ad_asset_insights_paginates_and_skips_unsupported_breakdown():
    client = _FakeClient([
        {"data": [{"body_asset": {"text": "a"}}], "paging": {"next": "n1"}},
        {"data": [{"body_asset": {"text": "b"}}]},
        {"error": {"code": 100, "message": "Invalid breakdown"}},
    ])
    with patch.object(data_source, "get_headers", return_value={"Authorization": "Bearer x"}), \
         patch.object(data_source, "INTER_PAGE_SLEEP_SEC", 0):
        result = await data_source.fetch_ad_asset_insights(
            "ad_1", ["body_asset", "video_asset"], user_id="g", team_id=None, strict_token=True,
            fields="impressions", client=client,
        )
    assert [r["body_asset"]["text"] for r in result["body_asset"]] == ["a", "b"]
    assert result["video_asset"] == []
    assert client.params[0]["breakdowns"] == "body_asset"
    assert client.params[0]["date_preset"] == "maximum"


@pytest.mark.asyncio
async def test_fetch_ad_asset_insights_raises_on_rate_limit():
    client = _FakeClient([{"error": {"code": 17, "message": "limit"}}])
    with patch.object(data_source, "get_headers", return_value={"Authorization": "Bearer x"}), \
         patch.object(data_source, "INTER_PAGE_SLEEP_SEC", 0):
        with pytest.raises(data_source.AdLibraryAPIError) as exc_info:
            await data_source.fetch_ad_asset_insights(
                "ad_1", ["body_asset"], user_id="g", team_id=None, strict_token=True,
                fields="impressions", client=client,
            )
    assert exc_info.value.fb_code == 17


# ── 3. service ─────────────────────────────────────────────────────────
_DYNAMIC_AD = {"ad_id": "a1", "primary_texts": ["文案"], "headlines": [], "descriptions": [], "media": [{"kind": "image"}]}


def _base_patches(fake_db, asset_fetch):
    return [
        patch.object(service, "_db", fake_db),
        patch.object(service, "fetch_account_info", AsyncMock(return_value={"currency": "TWD"})),
        patch.object(service, "fetch_campaigns", _stage([])),
        patch.object(service, "fetch_adsets", _stage([])),
        patch.object(service, "fetch_ads", _stage([])),
        patch.object(service, "fetch_ad_asset_insights", asset_fetch),
    ]


async def _run(fake_db, asset_fetch, **kwargs):
    patches = _base_patches(fake_db, asset_fetch)
    for p in patches:
        p.start()
    try:
        await service.run_refresh(**_refresh_kwargs(**kwargs))
    finally:
        for p in patches:
            p.stop()


@pytest.mark.asyncio
async def test_run_refresh_stores_asset_insights_for_dynamic_ads():
    fake_db = _FakeDb(dynamic_ads=[_DYNAMIC_AD, {**_DYNAMIC_AD, "ad_id": "a2"}])
    asset_fetch = AsyncMock(return_value={
        "body_asset": [{"body_asset": {"text": "文案"}, "impressions": "10", "clicks": "1", "spend": "1"}],
        "image_asset": [{"image_asset": {"hash": "h1"}, "impressions": "10"}],
    })
    await _run(fake_db, asset_fetch)

    assert asset_fetch.await_count == 2
    assert asset_fetch.await_args.args[1] == ["body_asset", "image_asset"]
    writes = [args for name, args, _ in fake_db.calls if name == "replace_asset_insights"]
    assert [w[1] for w in writes] == ["a1", "a2"]
    assert {e["kind"] for e in writes[0][2]} == {"primary_text", "image"}
    final = fake_db.job_updates()[-1]
    assert final["status"] == "succeeded" and final["asset_insights_ads"] == 2


@pytest.mark.asyncio
async def test_run_refresh_asset_rate_limit_is_partial_not_failed():
    fake_db = _FakeDb(dynamic_ads=[_DYNAMIC_AD])
    asset_fetch = AsyncMock(side_effect=data_source.AdLibraryAPIError("limit", fb_code=80004))
    await _run(fake_db, asset_fetch)
    final = fake_db.job_updates()[-1]
    assert final["status"] == "partial"
    assert "元件成效" in final["error"]


@pytest.mark.asyncio
async def test_run_refresh_skips_asset_stage_after_earlier_rate_limit():
    fake_db = _FakeDb(dynamic_ads=[_DYNAMIC_AD])
    asset_fetch = AsyncMock()
    patches = _base_patches(fake_db, asset_fetch)
    patches[4] = patch.object(service, "fetch_ads", _stage([], rate_limited=True))
    for p in patches:
        p.start()
    try:
        await service.run_refresh(**_refresh_kwargs())
    finally:
        for p in patches:
            p.stop()
    asset_fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_refresh_notes_when_dynamic_ads_exceed_cap():
    fake_db = _FakeDb(dynamic_ads=[_DYNAMIC_AD])
    original = fake_db.__call__

    async def call(fn, *args, **kwargs):
        if fn is repository.dynamic_ads_for_asset_insights:
            fake_db.calls.append((fn.__name__, args, kwargs))
            return [_DYNAMIC_AD], 150
        return await original(fn, *args, **kwargs)

    asset_fetch = AsyncMock(return_value={})
    patches = _base_patches(call, asset_fetch)
    for p in patches:
        p.start()
    try:
        await service.run_refresh(**_refresh_kwargs())
    finally:
        for p in patches:
            p.stop()
    final = fake_db.job_updates()[-1]
    assert final["status"] == "succeeded"
    assert "150" in final["error"]


# ── 4. repository / router ─────────────────────────────────────────────
def _dynamic_row(account_id, ad_id, *, spend=1.0, impressions=100):
    return {
        "account_id": account_id, "ad_id": ad_id, "ad_name": ad_id, "campaign_id": "c1", "campaign_name": "活動",
        "adset_id": "s1", "adset_name": "組合", "objective": None, "effective_status": "ACTIVE",
        "page_id": None, "media_type": "dynamic", "primary_texts": ["文案甲", "文案乙"], "headlines": [],
        "descriptions": [], "cta_types": [], "link_url": None,
        "media": [{"kind": "image", "fb_url": None, "image_hash": "h1", "video_id": None, "asset_id": "asset_h1"}],
        "preview_link": None, "search_text": "", "ad_created_at": None, "ad_updated_at": None,
        "impressions": impressions, "reach": 0, "clicks": 1, "spend": spend, "ctr": 1.0,
    }


def _entries(**metrics):
    body, _ = parse_asset_rows("body_asset", [
        {"body_asset": {"text": "文案甲", "id": "1"}, "impressions": "300", "clicks": "9", "spend": "30", **metrics},
        {"body_asset": {"text": "文案乙", "id": "2"}, "impressions": "100", "clicks": "1", "spend": "10"},
    ])
    image, _ = parse_asset_rows("image_asset", [{"image_asset": {"hash": "h1"}, "impressions": "400", "clicks": "10"}])
    return body + image


@pytest.mark.integration
def test_dynamic_ads_for_asset_insights_orders_by_spend(db):
    repository.upsert_items(db, [
        _dynamic_row("act_d", "a1", spend=1), _dynamic_row("act_d", "a2", spend=9),
        _dynamic_row("act_d", "a3", impressions=0),
    ])
    ads, total = repository.dynamic_ads_for_asset_insights(db, "act_d", limit=1)
    assert total == 2
    assert [a["ad_id"] for a in ads] == ["a2"]


@pytest.mark.integration
def test_replace_asset_insights_reuses_contents_and_replaces_rows(db):
    repository.upsert_items(db, [_dynamic_row("act_d", "a1")])
    contents_before = db.query(AdLibraryContent).filter_by(account_id="act_d").count()

    assert repository.replace_asset_insights(db, "act_d", "a1", _entries()) == 3
    assert db.query(AdLibraryContent).filter_by(account_id="act_d").count() == contents_before
    repository.replace_asset_insights(db, "act_d", "a1", _entries()[:1])
    rows = db.query(AdLibraryAssetInsight).filter_by(account_id="act_d", ad_id="a1").all()
    assert len(rows) == 1 and rows[0].impressions == 300


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
    yield client
    app.dependency_overrides.pop(auth_dependencies.get_current_user, None)
    app.dependency_overrides.pop(auth_dependencies.get_db, None)
    app.dependency_overrides.pop(auth_dependencies.get_current_team, None)


def _mine(ids=("act_mine",)):
    return patch.object(
        accounts_service, "get_all_ad_accounts",
        new=AsyncMock(return_value=([{"id": i, "name": i} for i in ids], None)),
    )


@pytest.mark.integration
def test_ad_asset_insights_endpoint(ad_library_client, db):
    repository.upsert_items(db, [_dynamic_row("act_mine", "a1")])
    repository.replace_asset_insights(db, "act_mine", "a1", _entries())
    item = db.query(AdLibraryItem).filter_by(account_id="act_mine", ad_id="a1").one()
    with _mine():
        resp = ad_library_client.get(f"/api/ad-library/ads/{item.id}/asset-insights")
        contents = ad_library_client.get(
            "/api/ad-library/contents", params={"account_id": "act_mine", "kind": "primary_text", "q": "文案甲"}
        )
    assert resp.status_code == 200
    body = resp.json()
    assert list(body["entries"]) == ["primary_text", "image"]
    texts = body["entries"]["primary_text"]
    assert [t["text_value"] for t in texts] == ["文案甲", "文案乙"]
    assert texts[0]["ctr"] == 3.0
    assert body["entries"]["image"][0]["asset_id"] == "asset_h1"
    assert body["note"]
    metrics = contents.json()["items"][0]["asset_metrics"]
    assert metrics["impressions"] == 300 and metrics["ads"] == 1


@pytest.mark.integration
def test_ad_asset_insights_of_other_account_returns_404(ad_library_client, db):
    repository.upsert_items(db, [_dynamic_row("act_other", "a1")])
    item = db.query(AdLibraryItem).filter_by(account_id="act_other", ad_id="a1").one()
    with _mine():
        resp = ad_library_client.get(f"/api/ad-library/ads/{item.id}/asset-insights")
        missing = ad_library_client.get("/api/ad-library/ads/nope/asset-insights")
    assert resp.status_code == 404
    assert missing.status_code == 404


@pytest.mark.integration
def test_ad_asset_insights_video_uses_ad_thumbnail(ad_library_client, db):
    row = _dynamic_row("act_mine", "v1ad")
    row["media"] = [{"kind": "video_thumbnail", "fb_url": None, "image_hash": "th", "video_id": "vid9",
                     "asset_id": "asset_thumb9"}]
    repository.upsert_items(db, [row])
    videos, _ = parse_asset_rows("video_asset", [{"video_asset": {"video_id": "vid9", "id": "1"}, "impressions": "10"}])
    repository.replace_asset_insights(db, "act_mine", "v1ad", videos)
    item = db.query(AdLibraryItem).filter_by(account_id="act_mine", ad_id="v1ad").one()
    with _mine():
        resp = ad_library_client.get(f"/api/ad-library/ads/{item.id}/asset-insights")
    assert resp.json()["entries"]["video"][0]["asset_id"] == "asset_thumb9"


def test_parse_skips_catalog_template_text_assets():
    entries, skipped = parse_asset_rows("title_asset", [
        {"title_asset": {"text": "{{product.name}}"}, "impressions": "10"},
        {"title_asset": {"text": "立即購買"}, "impressions": "5"},
    ])
    assert [e["text_value"] for e in entries] == ["立即購買"] and skipped == 1


# ── 2026-10-15 第二次試跑後：影片縮圖補抓 ───────────────────────────────
@pytest.mark.asyncio
async def test_fetch_video_pictures_batches_and_skips_errors():
    ids = [f"v{i}" for i in range(51)]
    client = _FakeClient([
        {f"v{i}": {"picture": f"https://cdn/{i}.jpg", "id": f"v{i}"} for i in range(50)},
        {"error": {"code": 100, "message": "bad"}},
    ])
    with patch.object(data_source, "get_headers", return_value={"Authorization": "Bearer x"}):
        pictures = await data_source.fetch_video_pictures(
            ids, user_id="g", team_id=None, strict_token=True, client=client,
        )
    assert len(pictures) == 50 and pictures["v0"] == "https://cdn/0.jpg"
    assert client.params[0]["fields"] == "picture"
    assert client.params[0]["ids"].count(",") == 49
    assert client.params[1]["ids"] == "v50"


@pytest.mark.asyncio
async def test_run_refresh_fills_missing_video_thumbnails():
    fake_db = _FakeDb()
    ad = {
        "id": "a1",
        "creative": {"asset_feed_spec": {
            "bodies": [{"text": "文案"}],
            "videos": [{"video_id": "vid1"}, {"video_id": "vid2", "thumbnail_url": "https://cdn/has.jpg"}],
        }},
    }
    pictures = AsyncMock(return_value={"vid1": "https://cdn/vid1.jpg"})
    download = AsyncMock(return_value=(b"img", "image/jpeg"))
    store = AsyncMock(side_effect=lambda **kw: {"asset_id": f"asset_{kw['filename_stem']}", "asset_uri": "u"})
    patches = _base_patches(fake_db, AsyncMock(return_value={}))
    patches[4] = patch.object(service, "fetch_ads", _stage([[ad]]))
    patches += [
        patch.object(service, "fetch_video_pictures", pictures),
        patch.object(service, "download_image", download),
        patch.object(service, "store_image", store),
    ]
    _start = [p.start() for p in patches]  # noqa: F841
    try:
        await service.run_refresh(**_refresh_kwargs())
    finally:
        for p in patches:
            p.stop()

    assert pictures.await_args.args[0] == ["vid1"]  # 已有縮圖的 vid2 不重抓
    rows = [args[0] for name, args, _ in fake_db.calls if name == "upsert_items"][0]
    media = {m["video_id"]: m for m in rows[0]["media"]}
    assert media["vid1"]["fb_url"] == "https://cdn/vid1.jpg"
    assert media["vid1"]["asset_id"]
