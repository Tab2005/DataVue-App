"""IG 個人檔案與 6 秒影片觀看指標：欄位攤平、註冊表，以及帳號層級 IG 瀏覽數的補值。"""
from unittest.mock import MagicMock

import pytest

from modules.fb_ads import analytics_service
from modules.fb_ads.analytics_service import _process_flat_row
from modules.fb_ads.metrics_registry import build_fb_fields
from modules.fb_ads.metrics_router import METRICS_REGISTRY as ROUTER_REGISTRY


def _row(**extra):
    row = {"spend": "300", "impressions": "3000"}
    row.update(extra)
    return row


@pytest.mark.unit
class TestFlatten:
    def test_six_second_views_rate_and_cost(self):
        flat = _process_flat_row(
            _row(video_6_sec_watched_actions=[{"action_type": "video_view", "value": "600"}]),
            "campaign", {},
        )
        assert flat["video_6_sec_views"] == 600
        assert flat["video_6_sec_view_rate"] == 20
        assert flat["cost_per_6_sec_video_view"] == 0.5

    def test_ig_profile_fields_are_ints(self):
        flat = _process_flat_row(_row(instagram_profile_visits="12", instagram_profile_follow="3"), "ad", {})
        assert flat["instagram_profile_visits"] == 12
        assert flat["instagram_profile_follow"] == 3

    def test_missing_fields_default_to_zero(self):
        flat = _process_flat_row(_row(impressions="0", spend="0"), "account", {})
        for key in ("video_6_sec_views", "video_6_sec_view_rate", "cost_per_6_sec_video_view",
                    "instagram_profile_visits", "instagram_profile_follow"):
            assert flat[key] == 0


@pytest.mark.unit
class TestRegistry:
    def test_direct_fields_requested_from_meta(self):
        fields = build_fb_fields("instagram_profile_visits,instagram_profile_follow,video_6_sec_views").split(",")
        assert {"instagram_profile_visits", "instagram_profile_follow", "video_6_sec_watched_actions"} <= set(fields)

    def test_rate_pulls_dependencies(self):
        fields = build_fb_fields("video_6_sec_view_rate").split(",")
        assert {"video_6_sec_watched_actions", "impressions"} <= set(fields)

    def test_router_exposes_new_metrics(self):
        for key in ("instagram_profile_visits", "instagram_profile_follow", "video_6_sec_views",
                    "video_6_sec_view_rate", "cost_per_6_sec_video_view"):
            assert ROUTER_REGISTRY[key]["key"] == key


def _resp(payload):
    r = MagicMock()
    r.json.return_value = payload
    return r


class _FakeClient:
    """依 params.level 回傳對應的假 insights 回應。"""

    def __init__(self, by_level):
        self.by_level = by_level
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, headers=None, params=None):
        self.calls.append(params)
        return _resp(self.by_level[(params or {}).get("level")])


@pytest.fixture
def fake_meta(monkeypatch):
    monkeypatch.setattr(analytics_service, "get_analytics_cache", lambda *a, **k: None)
    monkeypatch.setattr(analytics_service, "set_analytics_cache", lambda *a, **k: None)
    monkeypatch.setattr(analytics_service, "get_headers", lambda *a, **k: {"Authorization": "Bearer x"})

    def install(by_level):
        client = _FakeClient(by_level)
        monkeypatch.setattr(analytics_service.httpx, "AsyncClient", lambda *a, **k: client)
        return client
    return install


@pytest.mark.unit
class TestAccountLevelIgVisitsFallback:
    async def test_sums_campaign_level_when_account_row_lacks_field(self, fake_meta):
        client = fake_meta({
            "account": {"data": [{"spend": "100", "impressions": "1000", "instagram_profile_follow": "14"}]},
            "campaign": {"data": [{"instagram_profile_visits": "100"}, {"instagram_profile_visits": "20"}]},
        })
        rows = await analytics_service.get_custom_report(
            "act_1", "u", "2026-11-01", "2026-11-30", level="account",
            custom_fields="instagram_profile_visits,instagram_profile_follow",
        )
        assert rows[0]["instagram_profile_visits"] == 120
        assert rows[0]["instagram_profile_follow"] == 14
        assert [c["level"] for c in client.calls] == ["account", "campaign"]

    async def test_no_extra_request_when_metric_not_requested(self, fake_meta):
        client = fake_meta({"account": {"data": [{"spend": "100", "impressions": "1000"}]}})
        rows = await analytics_service.get_custom_report(
            "act_1", "u", "2026-11-01", "2026-11-30", level="account", custom_fields="spend",
        )
        assert rows[0]["instagram_profile_visits"] == 0
        assert len(client.calls) == 1

    async def test_fallback_error_keeps_zero(self, fake_meta):
        fake_meta({
            "account": {"data": [{"spend": "100", "impressions": "1000"}]},
            "campaign": {"error": {"message": "boom"}},
        })
        rows = await analytics_service.get_custom_report(
            "act_1", "u", "2026-11-01", "2026-11-30", level="account",
            custom_fields="instagram_profile_visits",
        )
        assert rows[0]["instagram_profile_visits"] == 0
