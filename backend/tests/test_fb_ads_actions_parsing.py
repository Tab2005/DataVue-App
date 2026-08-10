"""
Facebook Ads insights 聚合純函式單元測試（P2-3 補強測試覆蓋）

`modules/fb_ads/actions_parsing.py` 是「insights 聚合」的核心：把 Facebook
Graph API 回傳的 `actions`/`action_values` 陣列攤平成扁平 dict、計算
KPI 卡片與趨勢圖表要用的衍生指標。這個模組完全是無 I/O 的純函式，卻是
`services/facebook_service.py`（舊）與 `modules/fb_ads/_base.py`（現行
async 服務）共用的計算核心，過去從未有任何測試直接涵蓋，只能透過端到端
的 API 回應間接驗證。
"""
import pytest

from modules.fb_ads.actions_parsing import (
    calculate_change,
    format_charts,
    format_kpi,
    get_video_action_value,
    process_actions,
)


@pytest.mark.unit
class TestProcessActions:
    def test_parses_actions_list_into_dict(self):
        data = {"actions": [{"action_type": "purchase", "value": "10"}]}
        assert process_actions(data) == {"purchase": 10.0}

    def test_parses_action_values_with_val_suffix(self):
        data = {"action_values": [{"action_type": "purchase", "value": "199.5"}]}
        assert process_actions(data) == {"purchase_val": 199.5}

    def test_combines_actions_and_action_values(self):
        data = {
            "actions": [{"action_type": "add_to_cart", "value": "3"}],
            "action_values": [{"action_type": "add_to_cart", "value": "45.0"}],
        }
        assert process_actions(data) == {"add_to_cart": 3.0, "add_to_cart_val": 45.0}

    def test_missing_keys_returns_empty_dict(self):
        assert process_actions({}) == {}


@pytest.mark.unit
class TestGetVideoActionValue:
    def test_extracts_first_value_from_action_list(self):
        row = {"video_p25_watched_actions": [{"action_type": "video_view", "value": "42"}]}
        assert get_video_action_value(row, "video_p25_watched_actions") == 42.0

    def test_missing_field_returns_zero(self):
        assert get_video_action_value({}, "video_p25_watched_actions") == 0

    def test_empty_list_returns_zero(self):
        assert get_video_action_value({"video_p25_watched_actions": []}, "video_p25_watched_actions") == 0

    def test_malformed_value_returns_zero_instead_of_raising(self):
        row = {"video_p25_watched_actions": [{"action_type": "video_view", "value": "not-a-number"}]}
        assert get_video_action_value(row, "video_p25_watched_actions") == 0


@pytest.mark.unit
class TestCalculateChange:
    def test_positive_change_has_plus_sign(self):
        assert calculate_change(120, 100) == "+20.00%"

    def test_negative_change_has_minus_sign(self):
        assert calculate_change(80, 100) == "-20.00%"

    def test_zero_previous_and_zero_current_is_zero_percent(self):
        assert calculate_change(0, 0) == "+0%"

    def test_zero_previous_with_positive_current_is_simplified_infinity(self):
        assert calculate_change(50, 0) == "+100%"


@pytest.mark.unit
class TestFormatCharts:
    def test_formats_and_sorts_by_date(self):
        data_list = [
            {"date_start": "2026-07-02", "spend": "20", "impressions": "200"},
            {"date_start": "2026-07-01", "spend": "10", "impressions": "100"},
        ]
        result = format_charts(data_list)
        assert [row["name"] for row in result] == ["07-01", "07-02"]
        assert result[0]["spend"] == 10.0
        assert result[0]["impressions"] == 100

    def test_extracts_purchases_and_roas_from_actions(self):
        data_list = [
            {
                "date_start": "2026-07-01",
                "actions": [{"action_type": "purchase", "value": "5"}],
                "purchase_roas": [{"action_type": "purchase_roas", "value": "3.5"}],
            }
        ]
        result = format_charts(data_list)
        assert result[0]["purchases"] == 5.0
        assert result[0]["roas"] == 3.5

    def test_missing_optional_fields_default_to_zero(self):
        result = format_charts([{"date_start": "2026-07-01"}])
        assert result[0]["spend"] == 0.0
        assert result[0]["purchases"] == 0
        assert result[0]["roas"] == 0.0


@pytest.mark.unit
class TestFormatKpi:
    def _base_row(self, spend, impressions, link_clicks, purchases, purchase_value):
        return {
            "spend": str(spend),
            "impressions": str(impressions),
            "inline_link_clicks": str(link_clicks),
            "actions": [{"action_type": "purchase", "value": str(purchases)}],
            "action_values": [{"action_type": "purchase", "value": str(purchase_value)}],
        }

    def test_computes_spend_metric_with_currency_formatting(self):
        cur = self._base_row(1000, 10000, 100, 5, 5000)
        prev = self._base_row(800, 8000, 80, 4, 4000)

        metrics = format_kpi(cur, prev)

        assert metrics["spend"]["value"] == "$1,000"
        assert metrics["spend"]["previous"] == "($800)"
        assert metrics["spend"]["is_increase"] is True

    def test_derived_cpa_uses_purchase_count_from_actions(self):
        # spend=1000, purchases=5 -> CPA = 200
        cur = self._base_row(1000, 10000, 100, 5, 5000)
        prev = self._base_row(800, 8000, 80, 4, 4000)

        metrics = format_kpi(cur, prev)

        assert metrics["cpa"]["raw_value"] == pytest.approx(200.0)

    def test_zero_previous_value_yields_100_percent_change_when_current_positive(self):
        cur = self._base_row(1000, 10000, 100, 5, 5000)
        prev = self._base_row(0, 0, 0, 0, 0)

        metrics = format_kpi(cur, prev)

        assert metrics["spend"]["change"] == "+100.0%"

    def test_zero_purchases_does_not_raise_division_error(self):
        cur = self._base_row(1000, 10000, 100, 0, 0)
        prev = self._base_row(800, 8000, 80, 0, 0)

        metrics = format_kpi(cur, prev)

        assert metrics["cpa"]["raw_value"] == 0.0
