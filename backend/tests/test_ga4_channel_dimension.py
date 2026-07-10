"""
GA4 渠道對照維度切換驗證（docs/22 第 4 波，追加）

涵蓋：
- `CHANNEL_DIMENSION_MAP` 白名單對映（5 選項各自送出正確的一對 GA4 維度）
- snapshot kind 命名：預設維度沿用 `daily_channel`（向後相容）、其餘維度加
  `:{key}` 後綴，互不覆寫
- 高基數保護：channel 數 > 20 時依（收單+開發）轉換數排序截斷前 20，
  payload 標記 `truncated`/`total_row_count`
- 非白名單 `dimension` 直呼 service 拋 ValueError；經 API 呼叫回 422
"""
from unittest.mock import MagicMock

import pytest

from modules.ga4.dependencies import (
    require_ga4_insights_manage_alerts,
    require_ga4_insights_view,
    require_ga4_module,
)
from modules.ga4.insights_router import get_current_user


def _override_dependencies(app, user, db):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_ga4_module] = lambda: True
    app.dependency_overrides[require_ga4_insights_view] = lambda: True
    app.dependency_overrides[require_ga4_insights_manage_alerts] = lambda: True


# ─── 維度白名單對映 ──────────────────────────────────────────────────
@pytest.mark.unit
@pytest.mark.parametrize(
    "dimension,expected_session_dim,expected_first_user_dim",
    [
        ("default_channel_group", "sessionDefaultChannelGroup", "firstUserDefaultChannelGroup"),
        ("source_medium", "sessionSourceMedium", "firstUserSourceMedium"),
        ("source", "sessionSource", "firstUserSource"),
        ("medium", "sessionMedium", "firstUserMedium"),
        ("campaign", "sessionCampaignName", "firstUserCampaignName"),
    ],
)
def test_get_channels_uses_correct_dimension_pair(mocker, db, sample_user, dimension, expected_session_dim, expected_first_user_dim):
    from modules.ga4.insights_service import GA4InsightsService

    calls = []

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        calls.append(dimensions[0])
        return {"rows": [{dimensions[0]: "Organic Search", "conversions": 10}]}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_channels(db, user=sample_user, property_id="123456", days=7, dimension=dimension)
    db.commit()

    assert calls == [expected_session_dim, expected_first_user_dim]
    assert snapshot.payload["dimension"] == dimension


@pytest.mark.unit
def test_get_channels_kind_naming_default_vs_non_default(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        return_value=({"rows": []}, None),
    )

    default_snapshot = GA4InsightsService.get_channels(
        db, user=sample_user, property_id="123456", days=7, dimension="default_channel_group"
    )
    db.commit()
    assert default_snapshot.kind == "daily_channel"

    source_medium_snapshot = GA4InsightsService.get_channels(
        db, user=sample_user, property_id="123456", days=7, dimension="source_medium"
    )
    db.commit()
    assert source_medium_snapshot.kind == "daily_channel:source_medium"
    # 不同維度各自獨立存放，不是同一列被覆寫
    assert source_medium_snapshot.id != default_snapshot.id


@pytest.mark.unit
def test_get_channels_rejects_unknown_dimension():
    from modules.ga4.insights_service import GA4InsightsService

    with pytest.raises(ValueError):
        GA4InsightsService.get_channels(
            db=None, user=MagicMock(), property_id="123456", days=7, dimension="not_a_real_dimension"
        )


# ─── 高基數保護：top-20 截斷 ────────────────────────────────────────
@pytest.mark.unit
def test_get_channels_truncates_to_top_20_by_combined_conversions(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    # 25 個不同的 source/medium 組合，收單轉換數依序遞減：channel-0 最高
    session_rows = [{"sessionSourceMedium": f"channel-{i}", "conversions": 100 - i} for i in range(25)]
    first_user_rows = [{"firstUserSourceMedium": f"channel-{i}", "conversions": 1} for i in range(25)]

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["sessionSourceMedium"]:
            return {"rows": session_rows}, None
        return {"rows": first_user_rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_channels(
        db, user=sample_user, property_id="123456", days=7, dimension="source_medium"
    )
    db.commit()

    assert snapshot.payload["truncated"] is True
    assert snapshot.payload["total_row_count"] == 25
    assert len(snapshot.payload["channels"]) == 20
    # 最高（收單+開發）轉換數的 channel-0 應在截斷後仍保留，且排在最前面
    assert snapshot.payload["channels"][0]["channel"] == "channel-0"
    # 最低的幾名（channel-20..24）應被截斷掉
    kept = {row["channel"] for row in snapshot.payload["channels"]}
    assert "channel-24" not in kept


# ─── router：422 驗證 + 端到端 ──────────────────────────────────────
@pytest.mark.integration
def test_channels_endpoint_accepts_valid_dimension(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        return_value=({"rows": []}, None),
    )

    resp = client.get(
        "/api/ga4/insights/channels",
        params={"property_id": "123456", "days": 7, "dimension": "campaign"},
    )
    assert resp.status_code == 200
    assert resp.json()["payload"]["dimension"] == "campaign"


@pytest.mark.integration
def test_channels_endpoint_rejects_unknown_dimension_with_422(client, db, sample_user):
    _override_dependencies(client.app, sample_user, db)

    resp = client.get(
        "/api/ga4/insights/channels",
        params={"property_id": "123456", "days": 7, "dimension": "not_a_real_dimension"},
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_channels_endpoint_defaults_to_default_channel_group(client, db, sample_user, mocker):
    _override_dependencies(client.app, sample_user, db)
    mocker.patch(
        "modules.ga4.insights_service.GA4Service.get_analytics",
        return_value=({"rows": []}, None),
    )

    resp = client.get("/api/ga4/insights/channels", params={"property_id": "123456"})
    assert resp.status_code == 200
    assert resp.json()["payload"]["dimension"] == "default_channel_group"
