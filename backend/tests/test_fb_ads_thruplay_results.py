"""ThruPlay 改用正確欄位、成果（results）解析。"""
import pytest

from modules.fb_ads.analytics_service import _parse_results, _process_flat_row
from modules.fb_ads.metrics_registry import build_fb_fields
from modules.fb_ads.metrics_router import METRICS_REGISTRY as ROUTER_REGISTRY


def _row(**extra):
    row = {"spend": "1000", "impressions": "10000"}
    row.update(extra)
    return row


@pytest.mark.unit
class TestThruPlay:
    def test_thruplay_uses_thruplay_field_not_3s_video_view(self):
        flat = _process_flat_row(_row(
            actions=[{"action_type": "video_view", "value": "900"}],
            video_thruplay_watched_actions=[{"action_type": "video_view", "value": "400"}],
        ), "campaign", {})
        assert flat["video_views"] == 900
        assert flat["video_thruplay"] == 400
        assert flat["cost_per_thruplay"] == 2.5

    def test_missing_thruplay_is_zero(self):
        flat = _process_flat_row(_row(actions=[{"action_type": "video_view", "value": "900"}]), "campaign", {})
        assert flat["video_thruplay"] == 0
        assert flat["cost_per_thruplay"] == 0

    def test_registry_requests_thruplay_field(self):
        fields = build_fb_fields("cost_per_thruplay").split(",")
        assert "video_thruplay_watched_actions" in fields
        assert "spend" in fields


PURCHASE = [{"indicator": "actions:offsite_conversion.fb_pixel_purchase",
             "values": [{"value": "517", "attribution_windows": ["default"]}]}]


@pytest.mark.unit
class TestResults:
    def test_parse_value_and_label(self):
        assert _parse_results(PURCHASE) == (517, "購買")

    def test_indicator_without_values_is_zero(self):
        assert _parse_results([{"indicator": "actions:onsite_conversion.messaging_conversation_started_7d"}]) == (0, "開始對話")

    def test_unknown_type_falls_back_to_action_type(self):
        assert _parse_results([{"indicator": "actions:some_new_action", "values": [{"value": "3"}]}]) == (3, "some_new_action")

    def test_mixed_objectives_have_no_total(self):
        assert _parse_results([{"indicator": "mixed"}]) == (None, "多種")

    def test_missing_field_is_none(self):
        assert _parse_results(None) == (None, "")
        assert _parse_results([]) == (None, "")

    def test_flat_row_cost_per_result(self):
        flat = _process_flat_row(_row(spend="119197", results=PURCHASE), "campaign", {})
        assert flat["results"] == 517
        assert flat["result_type"] == "購買"
        assert flat["cost_per_result"] == pytest.approx(230.555, rel=1e-4)

    def test_account_level_without_results_is_none(self):
        flat = _process_flat_row(_row(), "account", {})
        assert flat["results"] is None
        assert flat["cost_per_result"] is None

    def test_registry_and_router(self):
        fields = build_fb_fields("cost_per_result").split(",")
        assert {"results", "spend"} <= set(fields)
        for key in ("results", "result_type", "cost_per_result", "video_thruplay", "cost_per_thruplay"):
            assert ROUTER_REGISTRY[key]["key"] == key
