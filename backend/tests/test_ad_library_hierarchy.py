"""
Ad Library 階層結構測試（docs/74 第一節）

1. currency / normalizer：預算換算、行銷活動與廣告組合欄位、targeting 摘要
2. hierarchy.build_tree：完整樹、佔位節點、狀態篩選
3. data_source：campaigns 分頁、帳號資訊錯誤
4. service.run_refresh：抓取順序、rate limit 停止、token fallback
5. router：/tree、/campaigns/{id}、/adsets/{id} 授權
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from database import Module, UserModuleAccess
from database.models.ad_library import AdLibraryAdset, AdLibraryCampaign, AdLibraryItem
from main import app
from modules.ad_library import data_source, hierarchy, repository, service
from modules.ad_library.currency import to_major_unit
from modules.ad_library.normalizer import normalize_adset, normalize_campaign, summarize_targeting
from modules.auth import dependencies as auth_dependencies
from modules.fb_ads import accounts_service


# ── 1. currency / normalizer ───────────────────────────────────────────
def test_to_major_unit_respects_currency_offset():
    assert to_major_unit(50000, "TWD") == 50000
    assert to_major_unit(50000, "USD") == 500
    assert to_major_unit(None, "TWD") is None
    assert to_major_unit(1000, None) == 10


def test_normalize_campaign_keeps_budget_in_minor_units():
    row = normalize_campaign(
        {
            "id": "c1",
            "name": "春季活動",
            "objective": "OUTCOME_SALES",
            "effective_status": "ACTIVE",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "daily_budget": "50000",
            "special_ad_categories": [],
            "start_time": "2026-03-01T08:00:00+0800",
            "insights": {"data": [{"impressions": "1000", "clicks": "20", "spend": "300.5", "ctr": "2.0"}]},
        },
        account_id="act_1",
        currency="TWD",
    )
    assert row["campaign_id"] == "c1"
    assert row["daily_budget"] == 50000
    assert row["lifetime_budget"] is None
    assert row["currency"] == "TWD"
    assert row["start_time"].hour == 0  # 轉成 UTC
    assert row["impressions"] == 1000 and row["spend"] == 300.5
    assert "insights" not in row["raw"]


def test_normalize_adset_summarizes_targeting():
    row = normalize_adset(
        {
            "id": "s1",
            "campaign_id": "c1",
            "optimization_goal": "OFFSITE_CONVERSIONS",
            "bid_amount": "1200",
            "is_dynamic_creative": True,
            "targeting": {
                "age_min": 25,
                "age_max": 45,
                "genders": [2],
                "geo_locations": {"countries": ["TW"], "regions": [{"key": "1", "name": "台北市"}]},
                "flexible_spec": [{"interests": [{"id": "6003", "name": "保養品"}]}],
                "custom_audiences": [{"id": "ca1", "name": "官網訪客 30 天"}],
                "targeting_automation": {"advantage_audience": 1},
                "publisher_platforms": ["facebook", "instagram"],
            },
            "promoted_object": {"pixel_id": "p1", "custom_event_type": "PURCHASE"},
        },
        account_id="act_1",
        currency="TWD",
    )
    summary = row["targeting_summary"]
    assert summary["age_min"] == 25 and summary["age_max"] == 45
    assert summary["genders"] == ["female"]
    assert summary["countries"] == ["TW"]
    assert summary["regions"] == ["台北市"]
    assert summary["interests"] == ["保養品"]
    assert summary["custom_audiences"] == ["官網訪客 30 天"]
    assert summary["advantage_audience"] is True
    assert summary["publisher_platforms"] == ["facebook", "instagram"]
    assert row["bid_amount"] == 1200
    assert row["is_dynamic_creative"] is True
    assert row["promoted_object"]["custom_event_type"] == "PURCHASE"


def test_summarize_targeting_tolerates_missing_or_malformed():
    summary = summarize_targeting(None)
    assert summary["genders"] == [] and summary["advantage_audience"] is False
    summary = summarize_targeting({"genders": ["x"], "geo_locations": "bad", "flexible_spec": ["bad"]})
    assert summary["genders"] == [] and summary["countries"] == []


# ── 2. hierarchy.build_tree ────────────────────────────────────────────
def _metrics(spend=0.0, impressions=0, clicks=0):
    return dict(impressions=impressions, reach=0, clicks=clicks, spend=spend, ctr=0.0)


def _campaign(campaign_id, *, status="ACTIVE", spend=0.0, daily_budget=None):
    return SimpleNamespace(
        id=f"row_{campaign_id}", campaign_id=campaign_id, name=f"活動 {campaign_id}", objective="OUTCOME_SALES",
        status=status, effective_status=status, buying_type="AUCTION", bid_strategy=None,
        smart_promotion_type=None, daily_budget=daily_budget, lifetime_budget=None, currency="TWD",
        special_ad_categories=[], start_time=None, stop_time=None, **_metrics(spend),
    )


def _adset(adset_id, campaign_id, *, spend=0.0):
    return SimpleNamespace(
        id=f"row_{adset_id}", adset_id=adset_id, campaign_id=campaign_id, name=f"組合 {adset_id}",
        status="ACTIVE", effective_status="ACTIVE", optimization_goal="LINK_CLICKS", billing_event="IMPRESSIONS",
        bid_strategy=None, bid_amount=None, destination_type=None, is_dynamic_creative=False,
        daily_budget=30000, lifetime_budget=None, currency="TWD", targeting_summary={"age_min": 18},
        start_time=None, end_time=None, **_metrics(spend),
    )


def _ad(ad_id, campaign_id, adset_id, *, spend=0.0, impressions=0, clicks=0, campaign_name=None, adset_name=None):
    return SimpleNamespace(
        id=f"row_{ad_id}", ad_id=ad_id, ad_name=f"廣告 {ad_id}", campaign_id=campaign_id,
        campaign_name=campaign_name, adset_id=adset_id, adset_name=adset_name, objective="OUTCOME_SALES",
        effective_status="ACTIVE", media_type="image", primary_texts=["文案" * 100], headlines=["標題"],
        media=[{"kind": "image", "asset_id": "a1", "fb_url": "https://cdn/x.jpg"}],
        copy_key=None, media_key=None, **_metrics(spend, impressions, clicks),
    )


def test_build_tree_nests_and_sorts_by_spend():
    tree = hierarchy.build_tree(
        [_campaign("c1", spend=10, daily_budget=50000), _campaign("c2", spend=99)],
        [_adset("s1", "c1", spend=1), _adset("s2", "c1", spend=5)],
        [_ad("a1", "c1", "s1", spend=1), _ad("a2", "c1", "s1", spend=3), _ad("a3", "c1", "s2")],
    )
    assert [c["campaign_id"] for c in tree] == ["c2", "c1"]
    c1 = tree[1]
    assert c1["budget_level"] == "campaign"
    assert c1["daily_budget"] == 50000  # TWD offset 1
    assert [s["adset_id"] for s in c1["adsets"]] == ["s2", "s1"]
    s1 = c1["adsets"][1]
    assert s1["daily_budget"] == 30000 and s1["targeting_summary"] == {"age_min": 18}
    assert [a["ad_id"] for a in s1["ads"]] == ["a2", "a1"]
    ad = s1["ads"][0]
    assert ad["primary_text"].endswith("…") and len(ad["primary_text"]) == hierarchy.AD_TEXT_PREVIEW_CHARS + 1
    assert ad["thumbnail"]["asset_id"] == "a1"
    assert tree[0]["adsets"] == []


def test_build_tree_adds_placeholders_for_missing_settings():
    """docs/74 上線前抓的舊資料：只有廣告、沒有上層設定。"""
    tree = hierarchy.build_tree(
        [],
        [],
        [
            _ad("a1", "c9", "s9", spend=2, impressions=100, clicks=5, campaign_name="舊活動", adset_name="舊組合"),
            _ad("a2", "c9", "s9", spend=3, impressions=100, clicks=5, campaign_name="舊活動", adset_name="舊組合"),
            _ad("a3", "c9", None, spend=1),
        ],
    )
    assert len(tree) == 1
    campaign = tree[0]
    assert campaign["settings_available"] is False
    assert campaign["name"] == "舊活動"
    assert campaign["metrics"]["spend"] == 6
    adset = next(s for s in campaign["adsets"] if s["adset_id"] == "s9")
    assert adset["settings_available"] is False and adset["name"] == "舊組合"
    assert adset["metrics"]["ctr"] == 5.0
    assert adset["metrics"]["reach"] is None
    assert any(s["adset_id"] is None for s in campaign["adsets"])


def test_build_tree_status_filter_applies_to_campaign_level_only():
    tree = hierarchy.build_tree(
        [_campaign("c1", status="ACTIVE"), _campaign("c2", status="PAUSED")],
        [_adset("s1", "c1"), _adset("s2", "c2")],
        [_ad("a1", "c1", "s1"), _ad("a2", "c2", "s2"), _ad("a9", "c9", "s9")],
        status="active",
    )
    assert [c["campaign_id"] for c in tree] == ["c1"]
    assert [a["ad_id"] for a in tree[0]["adsets"][0]["ads"]] == ["a1"]

    other = hierarchy.build_tree(
        [_campaign("c1", status="ACTIVE")], [], [_ad("a9", "c9", "s9")], status="other"
    )
    assert [c["campaign_id"] for c in other] == ["c9"]


# ── 3. data_source ─────────────────────────────────────────────────────
class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, pages):
        self._pages = list(pages)
        self.urls = []
        self.params = []

    async def get(self, url, headers=None, params=None):
        self.urls.append(url)
        self.params.append(params)
        return _FakeResp(self._pages.pop(0))


@pytest.mark.asyncio
async def test_fetch_campaigns_paginates_with_campaign_fields():
    client = _FakeClient([
        {"data": [{"id": "c1"}], "paging": {"next": "n1"}},
        {"data": [{"id": "c2"}]},
    ])
    seen = []

    async def on_page(page):
        seen.extend(c["id"] for c in page)

    with patch.object(data_source, "get_headers", return_value={"Authorization": "Bearer x"}), \
         patch.object(data_source, "INTER_PAGE_SLEEP_SEC", 0):
        result = await data_source.fetch_campaigns(
            "act_1", user_id="g", team_id=None, strict_token=True, on_page=on_page, client=client,
        )
    assert seen == ["c1", "c2"]
    assert result == {"fetched": 2, "truncated": False, "rate_limited": False}
    assert client.urls[0].endswith("/act_1/campaigns")
    assert "daily_budget" in client.params[0]["fields"]


@pytest.mark.asyncio
async def test_fetch_account_info_error_raises():
    client = _FakeClient([{"error": {"code": 190, "message": "Invalid OAuth access token"}}])
    with patch.object(data_source, "get_headers", return_value={"Authorization": "Bearer x"}):
        with pytest.raises(data_source.AdLibraryAPIError):
            await data_source.fetch_account_info(
                "act_1", user_id="g", team_id=None, strict_token=True, client=client,
            )


# ── 4. service.run_refresh ─────────────────────────────────────────────
class _FakeDb:
    """取代 service._db：記錄呼叫、不碰真 DB。"""

    def __init__(self, dynamic_ads=None):
        self.calls = []
        self.dynamic_ads = dynamic_ads or []

    async def __call__(self, fn, *args, **kwargs):
        self.calls.append((fn.__name__, args, kwargs))
        if fn is repository.known_image_assets:
            return {}
        if fn is repository.dynamic_ads_for_asset_insights:
            return self.dynamic_ads, len(self.dynamic_ads)
        return None

    def job_updates(self):
        return [kwargs for name, _args, kwargs in self.calls if name == "update_job"]


def _stage(pages, *, rate_limited=False):
    async def fetch(account_id, *, user_id, team_id, strict_token, on_page):
        for page in pages:
            await on_page(page)
        return {"fetched": sum(len(p) for p in pages), "truncated": False, "rate_limited": rate_limited}

    return AsyncMock(side_effect=fetch)


def _refresh_kwargs(**extra):
    return dict(
        job_id="job_1", account_id="act_1", google_id="g", user_id="u",
        token_team_id=None, strict_token=True, **extra,
    )


@pytest.mark.asyncio
async def test_run_refresh_fetches_all_levels_in_order():
    fake_db = _FakeDb()
    campaigns = _stage([[{"id": "c1", "daily_budget": "100"}]])
    adsets = _stage([[{"id": "s1", "campaign_id": "c1"}], [{"id": "s2", "campaign_id": "c1"}]])
    ads = _stage([[{"id": "a1"}]])
    with patch.object(service, "_db", fake_db), \
         patch.object(service, "fetch_account_info", AsyncMock(return_value={"currency": "TWD"})), \
         patch.object(service, "fetch_campaigns", campaigns), \
         patch.object(service, "fetch_adsets", adsets), \
         patch.object(service, "fetch_ads", ads):
        await service.run_refresh(**_refresh_kwargs())

    upserts = [(name, args[0]) for name, args, _ in fake_db.calls if name.startswith("upsert_")]
    assert [name for name, _ in upserts] == ["upsert_campaigns", "upsert_adsets", "upsert_adsets", "upsert_items"]
    assert upserts[0][1][0]["currency"] == "TWD"
    final = fake_db.job_updates()[-1]
    assert final["status"] == "succeeded"
    assert (final["campaigns_fetched"], final["adsets_fetched"], final["ads_fetched"]) == (1, 2, 1)


@pytest.mark.asyncio
async def test_run_refresh_stops_after_rate_limit_and_marks_partial():
    fake_db = _FakeDb()
    ads = _stage([[{"id": "a1"}]])
    with patch.object(service, "_db", fake_db), \
         patch.object(service, "fetch_account_info", AsyncMock(return_value={"currency": "USD"})), \
         patch.object(service, "fetch_campaigns", _stage([[{"id": "c1"}]])), \
         patch.object(service, "fetch_adsets", AsyncMock(side_effect=data_source.AdLibraryAPIError("limit", fb_code=17))), \
         patch.object(service, "fetch_ads", ads):
        await service.run_refresh(**_refresh_kwargs())

    ads.assert_not_awaited()
    final = fake_db.job_updates()[-1]
    assert final["status"] == "partial"
    assert "廣告組合" in final["error"]
    assert final["campaigns_fetched"] == 1


@pytest.mark.asyncio
async def test_run_refresh_falls_back_to_team_token():
    fake_db = _FakeDb()
    account_info = AsyncMock(side_effect=[data_source.AdLibraryTokenError("no token"), {"currency": "TWD"}])
    campaigns = _stage([])
    with patch.object(service, "_db", fake_db), \
         patch.object(service, "fetch_account_info", account_info), \
         patch.object(service, "fetch_campaigns", campaigns), \
         patch.object(service, "fetch_adsets", _stage([])), \
         patch.object(service, "fetch_ads", _stage([])):
        await service.run_refresh(**_refresh_kwargs(fallback_team_id="team_1"))

    assert campaigns.await_args.kwargs["team_id"] == "team_1"
    assert campaigns.await_args.kwargs["strict_token"] is False
    assert fake_db.job_updates()[-1]["status"] == "succeeded"


@pytest.mark.asyncio
async def test_run_refresh_without_fallback_fails():
    fake_db = _FakeDb()
    with patch.object(service, "_db", fake_db), \
         patch.object(service, "fetch_account_info", AsyncMock(side_effect=data_source.AdLibraryTokenError("no token"))):
        await service.run_refresh(**_refresh_kwargs())
    final = fake_db.job_updates()[-1]
    assert final["status"] == "failed" and final["error"] == "no token"


# ── 5. router ──────────────────────────────────────────────────────────
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


def _seed(db, account_id):
    campaign = AdLibraryCampaign(
        account_id=account_id, campaign_id=f"{account_id}_c1", name="活動", effective_status="ACTIVE",
        daily_budget=50000, currency="TWD", special_ad_categories=[],
        impressions=0, reach=0, clicks=0, spend=5.0, ctr=0.0,
    )
    adset = AdLibraryAdset(
        account_id=account_id, adset_id=f"{account_id}_s1", campaign_id=f"{account_id}_c1", name="組合",
        effective_status="ACTIVE", currency="TWD", targeting={"age_min": 20},
        targeting_summary={"age_min": 20}, impressions=0, reach=0, clicks=0, spend=5.0, ctr=0.0,
    )
    item = AdLibraryItem(
        account_id=account_id, ad_id=f"{account_id}_a1", campaign_id=f"{account_id}_c1",
        adset_id=f"{account_id}_s1", media_type="image", primary_texts=["文案"], headlines=[],
        descriptions=[], cta_types=[], media=[], impressions=0, reach=0, clicks=0, spend=5.0, ctr=0.0,
    )
    db.add_all([campaign, adset, item])
    db.commit()
    return campaign, adset, item


@pytest.mark.integration
def test_tree_returns_nested_hierarchy(ad_library_client, db):
    _seed(db, "act_mine")
    with _mine():
        resp = ad_library_client.get("/api/ad-library/tree", params={"account_id": "act_mine"})
    assert resp.status_code == 200
    body = resp.json()
    campaign = body["campaigns"][0]
    assert campaign["daily_budget"] == 50000
    assert campaign["adsets"][0]["ads"][0]["ad_id"] == "act_mine_a1"


@pytest.mark.integration
def test_tree_denies_account_outside_scope(ad_library_client):
    with _mine():
        resp = ad_library_client.get("/api/ad-library/tree", params={"account_id": "act_other"})
    assert resp.status_code == 403


@pytest.mark.integration
def test_campaign_and_adset_detail(ad_library_client, db):
    campaign, adset, _item = _seed(db, "act_mine")
    with _mine():
        c_resp = ad_library_client.get(f"/api/ad-library/campaigns/{campaign.id}")
        s_resp = ad_library_client.get(f"/api/ad-library/adsets/{adset.id}")
    assert c_resp.status_code == 200
    assert [s["adset_id"] for s in c_resp.json()["adsets"]] == ["act_mine_s1"]
    assert s_resp.status_code == 200
    assert s_resp.json()["adset"]["targeting"] == {"age_min": 20}
    assert [a["ad_id"] for a in s_resp.json()["ads"]] == ["act_mine_a1"]


@pytest.mark.integration
def test_campaign_and_adset_of_other_account_return_404(ad_library_client, db):
    campaign, adset, _item = _seed(db, "act_other")
    with _mine():
        c_resp = ad_library_client.get(f"/api/ad-library/campaigns/{campaign.id}")
        s_resp = ad_library_client.get(f"/api/ad-library/adsets/{adset.id}")
        missing = ad_library_client.get("/api/ad-library/adsets/nope")
    assert c_resp.status_code == 404
    assert s_resp.status_code == 404
    assert missing.status_code == 404
    assert s_resp.json()["detail"] == f"廣告組合 {adset.id} 不存在"
