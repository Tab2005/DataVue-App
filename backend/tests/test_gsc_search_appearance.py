from unittest.mock import patch

from dependencies import get_current_user
from routers.gsc import gsc_module_check


def _override_dependencies(app, user):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[gsc_module_check] = lambda: True


def test_search_appearance_summary_no_data(client, sample_user):
    _override_dependencies(client.app, sample_user)

    with patch("routers.gsc.GSCService.get_analytics", return_value=([], None)):
        resp = client.get(
            "/api/gsc/search-appearance-summary",
            params={"site_url": "sc-domain:example.com", "start_date": "2026-01-01", "end_date": "2026-01-31"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["has_data"] is False
    assert data["total_clicks"] == 0
    assert data["total_impressions"] == 0
    assert data["types"] == []


def test_search_appearance_summary_computes_shares_and_ai_hint(client, sample_user):
    _override_dependencies(client.app, sample_user)

    appearance_rows = [
        {"keys": ["AMP_BLUE_LINK"], "clicks": 30, "impressions": 300, "ctr": 0.1, "position": 5.0},
        {"keys": ["AI_OVERVIEW"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 3.0},
        {"keys": ["RICHCARD"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 6.0},
    ]
    total_rows = [
        {"keys": ["2026-01-01"], "clicks": 25, "impressions": 250, "ctr": 0.1, "position": 4.0},
        {"keys": ["2026-01-02"], "clicks": 25, "impressions": 250, "ctr": 0.1, "position": 4.0},
    ]

    def fake_get_analytics(user, site_url, start_date, end_date, dimensions=None, **kwargs):
        if dimensions == ["searchAppearance"]:
            return appearance_rows, None
        if dimensions == ["date"]:
            return total_rows, None
        return [], None

    with patch("routers.gsc.GSCService.get_analytics", side_effect=fake_get_analytics):
        resp = client.get(
            "/api/gsc/search-appearance-summary",
            params={"site_url": "sc-domain:example.com", "start_date": "2026-01-01", "end_date": "2026-01-31"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["has_data"] is True
    assert data["total_clicks"] == 50
    assert data["total_impressions"] == 500

    types = data["types"]
    # Sorted by clicks desc; AMP_BLUE_LINK should lead.
    assert types[0]["search_appearance"] == "AMP_BLUE_LINK"
    assert types[0]["clicks"] == 30
    assert types[0]["click_share"] == 0.6
    assert types[0]["is_ai_related_hint"] is False

    ai_row = next(t for t in types if t["search_appearance"] == "AI_OVERVIEW")
    assert ai_row["is_ai_related_hint"] is True
    assert ai_row["click_share"] == 0.2
    assert ai_row["impression_share"] == 0.2

    non_ai_row = next(t for t in types if t["search_appearance"] == "RICHCARD")
    assert non_ai_row["is_ai_related_hint"] is False


def test_search_appearance_summary_propagates_error(client, sample_user):
    _override_dependencies(client.app, sample_user)

    with patch("routers.gsc.GSCService.get_analytics", return_value=(None, "boom")):
        resp = client.get(
            "/api/gsc/search-appearance-summary",
            params={"site_url": "sc-domain:example.com", "start_date": "2026-01-01", "end_date": "2026-01-31"},
        )

    assert resp.status_code == 400
    assert resp.json()["error"] == "boom"
