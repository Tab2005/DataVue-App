"""
Ad Library AI 脈絡測試（docs/74 第 4 階段第 12 步）

/ai-context：帳號摘要、單一行銷活動脈絡（短代號、比對組、元件成效、附註）與授權。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from database import Module, UserModuleAccess
from database.models.ad_library import AdLibraryAdset, AdLibraryCampaign
from main import app
from modules.ad_library import ai_context, repository
from modules.ad_library.asset_insights import parse_asset_rows
from modules.auth import dependencies as auth_dependencies
from modules.fb_ads import accounts_service


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


def _row(ad_id, texts, hashes, *, adset_id="s1", media_type="image", spend=1.0):
    return {
        "account_id": "act_mine", "ad_id": ad_id, "ad_name": f"廣告{ad_id}", "campaign_id": "c1",
        "campaign_name": "春季活動", "adset_id": adset_id, "adset_name": f"組合{adset_id}",
        "objective": "OUTCOME_SALES", "effective_status": "ACTIVE", "page_id": None, "media_type": media_type,
        "primary_texts": list(texts), "headlines": ["立即購買"], "descriptions": [], "cta_types": ["SHOP_NOW"],
        "link_url": "https://shop.example.com",
        "media": [{"kind": "image", "fb_url": None, "image_hash": h, "video_id": None, "asset_id": None} for h in hashes],
        "preview_link": None, "search_text": "", "ad_created_at": None, "ad_updated_at": None,
        "impressions": 1000, "reach": 800, "clicks": 10, "spend": spend, "ctr": 1.0,
    }


def _seed(db):
    db.add(AdLibraryCampaign(
        account_id="act_mine", campaign_id="c1", name="春季活動", objective="OUTCOME_SALES",
        effective_status="ACTIVE", daily_budget=50000, currency="TWD", special_ad_categories=[],
        impressions=4000, reach=3000, clicks=40, spend=10.0, ctr=1.0,
    ))
    db.add(AdLibraryAdset(
        account_id="act_mine", adset_id="s1", campaign_id="c1", name="女性 25-45", effective_status="ACTIVE",
        optimization_goal="OFFSITE_CONVERSIONS", currency="TWD", bid_amount=1200,
        targeting={"age_min": 25}, targeting_summary={"age_min": 25, "age_max": 45, "genders": ["female"],
                                                      "interests": [], "advantage_audience": False},
        impressions=3000, reach=2000, clicks=30, spend=6.0, ctr=1.0,
    ))
    db.commit()
    repository.upsert_items(db, [
        _row("a1", ["共用文案"], ["m1"], spend=3),
        _row("a2", ["共用文案"], ["m2"], spend=2),
        _row("a3", ["另一段文案"], ["m1"], spend=1),
        _row("a4", ["動態甲", "動態乙"], ["m1", "m3"], adset_id="s2", media_type="dynamic", spend=4),
    ])
    body, _ = parse_asset_rows("body_asset", [
        {"body_asset": {"text": "動態甲"}, "impressions": "600", "clicks": "9", "spend": "3"},
        {"body_asset": {"text": "動態乙"}, "impressions": "400", "clicks": "1", "spend": "1"},
    ])
    repository.replace_asset_insights(db, "act_mine", "a4", body)


@pytest.mark.integration
def test_ai_context_account_summary(ad_library_client, db):
    _seed(db)
    with _mine():
        resp = ad_library_client.get("/api/ad-library/ai-context", params={"account_id": "act_mine"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["account"] == {"account_id": "act_mine", "currency": "TWD"}
    campaign = body["campaigns"][0]
    assert campaign["campaign_id"] == "c1"
    assert campaign["daily_budget"] == 50000
    assert campaign["adset_count"] == 2 and campaign["ad_count"] == 4
    assert campaign["comparisons"] == {"media_test": 1, "copy_test": 1}


@pytest.mark.integration
def test_ai_context_campaign_uses_refs_and_includes_comparisons(ad_library_client, db):
    _seed(db)
    with _mine():
        resp = ad_library_client.get(
            "/api/ad-library/ai-context", params={"account_id": "act_mine", "campaign_id": "c1"}
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == ai_context.SCHEMA_VERSION
    assert body["campaign"]["budget_level"] == "campaign"

    contents = body["contents"]
    shared = [ref for ref, c in contents.items() if c.get("text") == "共用文案"]
    assert len(shared) == 1  # 同一段文案只列一次
    headline_refs = [ref for ref, c in contents.items() if c["kind"] == "headline"]
    assert headline_refs == ["H1"]

    adsets = {a["adset_id"]: a for a in body["adsets"]}
    s1 = adsets["s1"]
    assert s1["bid_amount"] == 1200  # TWD offset 1
    assert s1["targeting"] == {"age_min": 25, "age_max": 45, "genders": ["female"]}
    ads = {a["ad_id"]: a for a in s1["ads"]}
    assert ads["a1"]["copy"]["primary_text"] == shared
    assert ads["a1"]["copy"]["headline"] == ["H1"]
    assert ads["a1"]["metrics"] == {"impressions": 1000, "clicks": 10, "spend": 3.0, "ctr": 1.0, "reach": 800}

    assert adsets["s2"]["settings_available"] is False
    dynamic = adsets["s2"]["ads"][0]
    assert [r["impressions"] for r in dynamic["asset_results"]] == [600, 400]
    assert contents[dynamic["asset_results"][0]["ref"]]["text"] == "動態甲"

    relations = sorted(c["relation"] for c in body["comparisons"])
    assert relations == ["copy_test", "media_test"]
    media_test = next(c for c in body["comparisons"] if c["relation"] == "media_test")
    assert media_test["fixed_refs"][0] == shared[0]
    assert sorted(v["ad_ids"][0] for v in media_test["variants"]) == ["a1", "a2"]
    assert all(v["refs"] and v["refs"][0].startswith("I") for v in media_test["variants"])

    notes = " ".join(body["notes"])
    assert ai_context.ATTRIBUTION_NOTE in notes
    assert ai_context.MISSING_SETTINGS_NOTE in notes
    assert ai_context.ASSET_RESULTS_NOTE in notes
    assert ai_context.COMPARISON_SCOPE_NOTE in notes


@pytest.mark.integration
def test_ai_context_truncates_large_campaigns(ad_library_client, db):
    _seed(db)
    with _mine(), patch.object(ai_context, "MAX_ADS_PER_CAMPAIGN", 2):
        resp = ad_library_client.get(
            "/api/ad-library/ai-context", params={"account_id": "act_mine", "campaign_id": "c1"}
        )
    body = resp.json()
    assert sum(len(a["ads"]) for a in body["adsets"]) == 2
    assert any("只列出花費最高的 2 則" in n for n in body["notes"])


@pytest.mark.integration
def test_ai_context_authorization(ad_library_client, db):
    _seed(db)
    with _mine():
        outside = ad_library_client.get("/api/ad-library/ai-context", params={"account_id": "act_other"})
        missing = ad_library_client.get(
            "/api/ad-library/ai-context", params={"account_id": "act_mine", "campaign_id": "nope"}
        )
    assert outside.status_code == 403
    assert missing.status_code == 404


@pytest.mark.integration
def test_ai_context_campaign_of_other_account_is_404(ad_library_client, db):
    _seed(db)
    with _mine(("act_mine", "act_x")):
        resp = ad_library_client.get(
            "/api/ad-library/ai-context", params={"account_id": "act_x", "campaign_id": "c1"}
        )
    assert resp.status_code == 404
