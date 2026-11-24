"""訊息廣告指標：action 攤平、衍生比率，以及 build_fb_fields 的依賴展開。"""
import pytest

from modules.fb_ads.actions_parsing import MESSAGING_ACTION_FIELDS, apply_messaging_metrics
from modules.fb_ads.metrics_registry import METRICS_REGISTRY, build_fb_fields
from modules.fb_ads.metrics_router import METRICS_REGISTRY as ROUTER_REGISTRY


def _acts(**counts):
    return {MESSAGING_ACTION_FIELDS[k]: v for k, v in counts.items()}


@pytest.mark.unit
class TestApplyMessagingMetrics:
    def test_flattens_all_messaging_actions(self):
        acts = {action_type: i + 1 for i, action_type in enumerate(MESSAGING_ACTION_FIELDS.values())}
        flat = apply_messaging_metrics({"spend": 0}, acts)
        for i, key in enumerate(MESSAGING_ACTION_FIELDS):
            assert flat[key] == i + 1

    def test_missing_actions_default_to_zero(self):
        flat = apply_messaging_metrics({"spend": 100}, {})
        assert all(flat[key] == 0 for key in MESSAGING_ACTION_FIELDS)
        assert flat["cost_per_message"] == 0
        assert flat["messaging_block_rate"] == 0

    def test_derived_rates_use_conversations_started(self):
        acts = _acts(
            messaging_first_reply=20,
            messaging_conversation_started=40,
            messaging_depth_2=10,
            messaging_conversation_replied=30,
            messaging_blocks=2,
        )
        flat = apply_messaging_metrics({"spend": 400.0}, acts)
        assert flat["cost_per_message"] == 20
        assert flat["cost_per_conversation_started"] == 10
        assert flat["messaging_depth_2_rate"] == 25
        assert flat["messaging_reply_rate"] == 75
        assert flat["messaging_block_rate"] == 5


@pytest.mark.unit
class TestRegistry:
    def test_every_messaging_field_is_registered_with_matching_action_type(self):
        for key, action_type in MESSAGING_ACTION_FIELDS.items():
            assert METRICS_REGISTRY[key] == {"source": "actions", "action_type": action_type}

    def test_new_metrics_exposed_in_router_registry(self):
        for key in ("messaging_welcome_message_view", "messaging_blocks",
                    "messaging_block_rate", "cost_per_conversation_started"):
            assert ROUTER_REGISTRY[key]["key"] == key

    def test_calculated_metric_pulls_its_dependencies(self):
        fields = build_fb_fields("messaging_block_rate").split(",")
        assert "actions" in fields

    def test_cost_metric_pulls_spend(self):
        fields = build_fb_fields("cost_per_conversation_started").split(",")
        assert "spend" in fields
        assert "actions" in fields
