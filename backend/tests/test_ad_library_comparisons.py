"""
Ad Library 內容元件與比對測試（docs/74 第二節）

1. fingerprint：文字正規化、copy_key / media_key 規則
2. comparisons.build_comparisons：素材測試、文案測試、重複投放
3. repository：upsert 時同步元件、舊資料補建
4. router：/comparisons、/contents、/ads 的同文案計數與授權
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from database import Module, UserModuleAccess
from database.models.ad_library import AdLibraryAdContent, AdLibraryContent, AdLibraryItem
from main import app
from modules.ad_library import comparisons, repository
from modules.ad_library.fingerprint import extract_components, normalize_text
from modules.auth import dependencies as auth_dependencies
from modules.fb_ads import accounts_service


# ── 1. fingerprint ─────────────────────────────────────────────────────
def test_normalize_text_unifies_width_newlines_and_spaces():
    assert normalize_text("ＡＢＣ　１２３！") == "ABC 123!"
    assert normalize_text("第一行  \r\n第二行\r\n\r\n\r\n\r\n第三行\n") == "第一行\n第二行\n\n第三行"
    assert normalize_text("  ") == ""
    assert normalize_text(None) == ""


def _item(texts=("文案",), headlines=(), media=(), media_type="image"):
    return {
        "primary_texts": list(texts),
        "headlines": list(headlines),
        "descriptions": [],
        "media": list(media),
        "media_type": media_type,
    }


def _img(h, asset_id=None):
    return {"kind": "image", "fb_url": f"https://cdn/{h}.jpg", "image_hash": h, "video_id": None, "asset_id": asset_id}


def test_copy_key_ignores_whitespace_and_width_but_keeps_emoji():
    base = extract_components(_item(texts=["限時優惠！"]))["copy_key"]
    assert extract_components(_item(texts=["限時優惠!  "]))["copy_key"] == base
    assert extract_components(_item(texts=["限時優惠！🔥"]))["copy_key"] != base


def test_copy_key_distinguishes_primary_text_from_headline():
    a = extract_components(_item(texts=["A"], headlines=["B"]))["copy_key"]
    b = extract_components(_item(texts=["B"], headlines=["A"]))["copy_key"]
    assert a != b


def test_media_key_order_matters_only_for_carousel():
    m1, m2 = _img("h1"), _img("h2")
    carousel_a = extract_components(_item(media=[m1, m2], media_type="carousel"))["media_key"]
    carousel_b = extract_components(_item(media=[m2, m1], media_type="carousel"))["media_key"]
    dynamic_a = extract_components(_item(media=[m1, m2], media_type="dynamic"))["media_key"]
    dynamic_b = extract_components(_item(media=[m2, m1], media_type="dynamic"))["media_key"]
    assert carousel_a != carousel_b
    assert dynamic_a == dynamic_b


def test_media_key_is_none_when_any_media_lacks_identity():
    no_hash = {"kind": "image", "fb_url": "https://cdn/x.jpg", "image_hash": None, "video_id": None, "asset_id": None}
    assert extract_components(_item(media=[_img("h1"), no_hash], media_type="carousel"))["media_key"] is None
    thumb_only = {"kind": "video_thumbnail", "fb_url": "https://cdn/t.jpg", "image_hash": "thumb", "video_id": None}
    assert extract_components(_item(media=[thumb_only], media_type="video"))["media_key"] is None
    video = {"kind": "video_thumbnail", "fb_url": "https://cdn/t.jpg", "image_hash": "thumb", "video_id": "v1"}
    result = extract_components(_item(media=[video], media_type="video"))
    assert result["media_key"] is not None
    assert [c["kind"] for c in result["components"] if c["kind"] in ("image", "video")] == ["video"]


def test_components_dedupe_texts_and_repeated_carousel_images():
    result = extract_components(_item(texts=["同一段", "同一段 "], media=[_img("h1"), _img("h1")], media_type="carousel"))
    kinds = [c["kind"] for c in result["components"]]
    assert kinds.count("primary_text") == 1
    assert kinds.count("image") == 1
    assert extract_components(_item(texts=[], media=[]))["copy_key"] is None


# ── 2. comparisons ─────────────────────────────────────────────────────
def _ad(ad_id, copy_key, media_key, *, adset="s1", campaign="c1", spend=1.0, impressions=100, clicks=1):
    return SimpleNamespace(
        id=f"row_{ad_id}", ad_id=ad_id, ad_name=ad_id, campaign_id=campaign, campaign_name=f"活動{campaign}",
        adset_id=adset, adset_name=f"組合{adset}", objective=None, effective_status="ACTIVE",
        media_type="image", primary_texts=[f"文案{copy_key}"], headlines=[], descriptions=[],
        media=[{"kind": "image", "asset_id": f"asset_{media_key}", "fb_url": None}],
        copy_key=copy_key, media_key=media_key,
        impressions=impressions, reach=0, clicks=clicks, spend=spend, ctr=0.0,
    )


def test_comparisons_doc_example_finds_media_and_copy_tests():
    """docs/74 範例：廣告 1（T1+M1）、2（T1+M2）、3（T2+M1）。"""
    result = comparisons.build_comparisons([_ad("1", "T1", "M1"), _ad("2", "T1", "M2"), _ad("3", "T2", "M1")])
    assert result["counts"] == {"media_test": 1, "copy_test": 1, "duplicate": 0}
    media_test = next(g for g in result["groups"] if g["relation"] == "media_test")
    assert media_test["fixed"]["key"] == "T1"
    assert sorted(v["key"] for v in media_test["variants"]) == ["M1", "M2"]
    copy_test = next(g for g in result["groups"] if g["relation"] == "copy_test")
    assert copy_test["fixed"]["key"] == "M1"
    assert sorted(v["key"] for v in copy_test["variants"]) == ["T1", "T2"]
    assert copy_test["scope"] == {"level": "adset", "id": "s1", "name": "組合s1", "campaign_id": "c1", "campaign_name": "活動c1"}


def test_comparisons_duplicates_and_independent_ads():
    result = comparisons.build_comparisons([_ad("1", "T1", "M1"), _ad("2", "T1", "M1"), _ad("3", "T9", "M9")])
    assert result["counts"] == {"media_test": 0, "copy_test": 0, "duplicate": 1}
    dup = result["groups"][0]
    assert [a["ad_id"] for a in dup["variants"][0]["ads"]] == ["1", "2"]
    assert dup["metrics"]["impressions"] == 200


def test_comparisons_skip_ads_without_media_key():
    result = comparisons.build_comparisons([_ad("1", "T1", "M1"), _ad("2", "T1", None)])
    assert result["groups"] == []
    assert result["coverage"] == {"ads": 2, "without_copy_key": 0, "without_media_key": 1}


def test_comparisons_scope_campaign_crosses_adsets_and_relation_filter():
    ads = [_ad("1", "T1", "M1", adset="s1"), _ad("2", "T1", "M2", adset="s2")]
    assert comparisons.build_comparisons(ads, scope="adset")["groups"] == []
    result = comparisons.build_comparisons(ads, scope="campaign", relation="media_test")
    assert len(result["groups"]) == 1
    adset_names = {a["adset_name"] for v in result["groups"][0]["variants"] for a in v["ads"]}
    assert adset_names == {"組合s1", "組合s2"}
    assert comparisons.build_comparisons(ads, scope="campaign", relation="copy_test")["groups"] == []


def test_comparisons_variant_metrics_and_sorting():
    result = comparisons.build_comparisons([
        _ad("1", "T1", "M1", spend=1, impressions=100, clicks=1),
        _ad("2", "T1", "M2", spend=9, impressions=100, clicks=5),
        _ad("3", "T1", "M2", spend=1, impressions=100, clicks=5),
    ])
    group = result["groups"][0]
    assert [v["key"] for v in group["variants"]] == ["M2", "M1"]
    assert group["variants"][0]["metrics"]["ctr"] == 5.0
    assert group["variants"][0]["metrics"]["spend"] == 10


# ── 3. repository ──────────────────────────────────────────────────────
def _row(account_id, ad_id, texts, media_hashes, *, adset_id="s1", spend=0.0):
    return {
        "account_id": account_id, "ad_id": ad_id, "ad_name": ad_id, "campaign_id": "c1", "campaign_name": "活動",
        "adset_id": adset_id, "adset_name": "組合", "objective": None, "effective_status": "ACTIVE",
        "page_id": None, "media_type": "image", "primary_texts": list(texts), "headlines": [], "descriptions": [],
        "cta_types": [], "link_url": None, "media": [_img(h, asset_id=f"asset_{h}") for h in media_hashes],
        "preview_link": None, "search_text": "", "ad_created_at": None, "ad_updated_at": None,
        "impressions": 100, "reach": 0, "clicks": 1, "spend": spend, "ctr": 1.0,
    }


@pytest.mark.integration
def test_upsert_items_syncs_contents_and_keys(db):
    repository.upsert_items(db, [
        _row("act_r", "1", ["共用文案"], ["h1"]),
        _row("act_r", "2", ["共用文案"], ["h2"]),
    ])
    items = {i.ad_id: i for i in db.query(AdLibraryItem).filter_by(account_id="act_r")}
    assert items["1"].copy_key == items["2"].copy_key
    assert items["1"].media_key != items["2"].media_key
    texts = db.query(AdLibraryContent).filter_by(account_id="act_r", kind="primary_text").all()
    assert len(texts) == 1
    image = db.query(AdLibraryContent).filter_by(account_id="act_r", kind="image", image_hash="h1").one()
    assert image.asset_id == "asset_h1"
    assert db.query(AdLibraryAdContent).filter_by(content_id=texts[0].id).count() == 2

    # 文案改了：舊關聯移除、新元件建立
    repository.upsert_items(db, [_row("act_r", "1", ["新文案"], ["h1"])])
    db.expire_all()
    assert db.query(AdLibraryAdContent).filter_by(content_id=texts[0].id).count() == 1
    assert db.query(AdLibraryItem).filter_by(account_id="act_r", ad_id="1").one().copy_key != items["2"].copy_key


@pytest.mark.integration
def test_ensure_contents_backfills_items_fetched_before_phase_two(db):
    for ad_id in ("1", "2"):
        db.add(AdLibraryItem(
            account_id="act_old", ad_id=ad_id, media_type="image", primary_texts=["舊文案"], headlines=[],
            descriptions=[], cta_types=[], media=[_img(f"h{ad_id}")], impressions=0, reach=0, clicks=0,
            spend=0.0, ctr=0.0,
        ))
    db.commit()
    assert repository.ensure_contents(db, "act_old") is True
    keys = {i.copy_key for i in db.query(AdLibraryItem).filter_by(account_id="act_old")}
    assert len(keys) == 1 and None not in keys
    assert repository.ensure_contents(db, "act_old") is False
    assert repository.ensure_contents(db, "act_empty") is False


# ── 4. router ──────────────────────────────────────────────────────────
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


def _seed_test(db, account_id="act_mine"):
    repository.upsert_items(db, [
        _row(account_id, "1", ["T1"], ["m1"], spend=1),
        _row(account_id, "2", ["T1"], ["m2"], spend=2),
        _row(account_id, "3", ["T2"], ["m1"], spend=3),
    ])


@pytest.mark.integration
def test_comparisons_endpoint(ad_library_client, db):
    _seed_test(db)
    with _mine():
        resp = ad_library_client.get("/api/ad-library/comparisons", params={"account_id": "act_mine"})
        filtered = ad_library_client.get(
            "/api/ad-library/comparisons", params={"account_id": "act_mine", "relation": "copy_test"}
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["counts"] == {"media_test": 1, "copy_test": 1, "duplicate": 0}
    assert body["note"]
    assert [g["relation"] for g in filtered.json()["groups"]] == ["copy_test"]


@pytest.mark.integration
def test_comparisons_and_contents_deny_account_outside_scope(ad_library_client):
    with _mine():
        for path in ("/api/ad-library/comparisons", "/api/ad-library/contents"):
            resp = ad_library_client.get(path, params={"account_id": "act_other"})
            assert resp.status_code == 403, path


@pytest.mark.integration
def test_ads_include_same_key_counts_and_filter_by_key(ad_library_client, db):
    _seed_test(db)
    with _mine():
        resp = ad_library_client.get("/api/ad-library/ads", params={"account_id": "act_mine", "sort": "spend"})
    items = {i["ad_id"]: i for i in resp.json()["items"]}
    assert items["1"]["same_copy_count"] == 1  # 廣告 2 同文案
    assert items["1"]["same_media_count"] == 1  # 廣告 3 同素材
    assert items["2"]["same_media_count"] == 0

    with _mine():
        resp = ad_library_client.get(
            "/api/ad-library/ads", params={"account_id": "act_mine", "copy_key": items["1"]["copy_key"]}
        )
        bad = ad_library_client.get("/api/ad-library/ads", params={"account_id": "act_mine", "copy_key": "x' or 1=1"})
    assert sorted(i["ad_id"] for i in resp.json()["items"]) == ["1", "2"]
    assert bad.status_code == 422


@pytest.mark.integration
def test_contents_list_and_detail(ad_library_client, db):
    _seed_test(db)
    with _mine():
        resp = ad_library_client.get(
            "/api/ad-library/contents", params={"account_id": "act_mine", "kind": "primary_text"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        top = body["items"][0]
        assert top["text_value"] == "T1" and top["ad_count"] == 2 and top["spend"] == 3
        detail = ad_library_client.get(f"/api/ad-library/contents/{top['id']}")
        by_ctr = ad_library_client.get(
            "/api/ad-library/contents", params={"account_id": "act_mine", "sort": "ctr", "q": "T2"}
        )
    assert detail.status_code == 200
    assert sorted(a["ad_id"] for a in detail.json()["ads"]) == ["1", "2"]
    assert detail.json()["content"]["ad_count"] == 2
    assert [i["text_value"] for i in by_ctr.json()["items"]] == ["T2"]


@pytest.mark.integration
def test_content_of_other_account_returns_404(ad_library_client, db):
    _seed_test(db, "act_other")
    content = db.query(AdLibraryContent).filter_by(account_id="act_other").first()
    with _mine():
        resp = ad_library_client.get(f"/api/ad-library/contents/{content.id}")
        missing = ad_library_client.get("/api/ad-library/contents/nope")
    assert resp.status_code == 404
    assert missing.status_code == 404
