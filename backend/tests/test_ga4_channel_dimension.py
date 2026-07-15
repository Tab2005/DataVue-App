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


# ─── docs/34 第三波：小樣本比例穩健化 ────────────────────────────────
@pytest.mark.unit
def test_get_channels_marks_insufficient_data_below_min_sample(mocker, db, sample_user):
    """實測案例（2026-07-15，HUKUROU property）：開發0/收單6，比例=0.00，
    總量 6 < CHANNEL_MIN_SAMPLE(10)，不該再被貼上「主攻型」（close）。"""
    from modules.ga4.insights_service import GA4InsightsService

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["sessionDefaultChannelGroup"]:
            return {"rows": [{"sessionDefaultChannelGroup": "Email", "conversions": 6}]}, None
        return {"rows": []}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_channels(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    row = snapshot.payload["channels"][0]
    assert row["channel"] == "Email"
    assert row["tag"] == "insufficient_data"
    # 比例數字仍照算並保留給前端顯示（只是不貼強分類標籤），不應被清成 None
    assert row["ratio"] == 0.0


@pytest.mark.unit
@pytest.mark.parametrize(
    "closing,assisting,expected_tag",
    [
        (9, 0, "insufficient_data"),   # 總量 9 < 10 門檻，即使 closing>0 也不分類
        (10, 0, "close"),              # 總量剛好 = 10 門檻，恢復正常分類（ratio 0.0 < 0.7 -> close）
    ],
)
def test_get_channels_min_sample_boundary(mocker, db, sample_user, closing, assisting, expected_tag):
    from modules.ga4.insights_service import GA4InsightsService

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["sessionDefaultChannelGroup"]:
            return {"rows": [{"sessionDefaultChannelGroup": "Direct", "conversions": closing}]}, None
        rows = [{"firstUserDefaultChannelGroup": "Direct", "conversions": assisting}] if assisting else []
        return {"rows": rows}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = GA4InsightsService.get_channels(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert snapshot.payload["channels"][0]["tag"] == expected_tag


@pytest.mark.unit
def test_get_channels_min_sample_respects_override(mocker, db, sample_user):
    """門檻可調整（正式環境經由 `GA4_CHANNEL_MIN_SAMPLE` 環境變數在啟動時設定）。
    這裡直接 patch 模組常數驗證行為，不用 importlib.reload——reload 會在同一
    程序內就地重建整個模組（其他檔案 import 時拿到的 GA4InsightsService 參照
    不會跟著換，且若在環境變數還原前就 reload 會把常數污染到其他測試），風險
    遠高於直接 patch 這顆已知的模組級常數。"""
    import modules.ga4.insights_service as insights_service_module

    mocker.patch.object(insights_service_module, "CHANNEL_MIN_SAMPLE", 0)

    def fake_get_analytics(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        if dimensions == ["sessionDefaultChannelGroup"]:
            return {"rows": [{"sessionDefaultChannelGroup": "Email", "conversions": 6}]}, None
        return {"rows": []}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=fake_get_analytics)

    snapshot = insights_service_module.GA4InsightsService.get_channels(
        db, user=sample_user, property_id="123456", days=7
    )
    db.commit()

    # 門檻關閉（0）後，退回原本「收單>0 就分類」的行為
    assert snapshot.payload["channels"][0]["tag"] == "close"


# ─── docs/34 第一波：歸因模式揭露 ────────────────────────────────────
@pytest.mark.unit
def test_get_channels_attribution_model_unknown_without_credentials(mocker, db, sample_user):
    """sample_user 沒有 ga4_access_token，get_credentials 回 None，
    應優雅回退 "unknown"，不能讓渠道對照卡片掛掉。"""
    from modules.ga4.insights_service import GA4InsightsService

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", return_value=({"rows": []}, None))

    snapshot = GA4InsightsService.get_channels(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert snapshot.payload["attribution_model"] == "unknown"


@pytest.mark.unit
def test_get_channels_attribution_model_normalizes_and_caches(mocker, db, sample_user):
    """Admin API 回傳的 enum 名稱應正規化為 "data_driven"；24 小時內重複呼叫
    不應重打 Admin API（驗證快取生效）。"""
    from modules.ga4.insights_service import GA4InsightsService

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", return_value=({"rows": []}, None))
    get_attr_mock = mocker.patch(
        "modules.ga4.insights_service.GA4Client.get_attribution_settings",
        return_value=("PAID_AND_ORGANIC_CHANNELS_DATA_DRIVEN", None),
    )

    first = GA4InsightsService.get_channels(db, user=sample_user, property_id="123456", days=7)
    db.commit()
    assert first.payload["attribution_model"] == "data_driven"
    assert get_attr_mock.call_count == 1

    second = GA4InsightsService.get_channels(db, user=sample_user, property_id="123456", days=7)
    db.commit()
    assert second.payload["attribution_model"] == "data_driven"
    assert get_attr_mock.call_count == 1  # 命中快取，沒有再打一次 Admin API


@pytest.mark.unit
def test_get_channels_attribution_model_falls_back_to_stale_cache_on_error(mocker, db, sample_user):
    """快取過期後若 Admin API 查詢失敗，寧可回傳上一次快取到的值，也不要
    直接判 unknown（設定極少變動，比起丟失資訊，用舊值更合理）。"""
    from datetime import datetime, timedelta

    from modules.ga4.insights_service import (
        ATTRIBUTION_SETTINGS_DATE,
        ATTRIBUTION_SETTINGS_KIND,
        GA4InsightsService,
        repository,
    )

    stale = repository.upsert_snapshot(
        db, property_id="123456", kind=ATTRIBUTION_SETTINGS_KIND, date=ATTRIBUTION_SETTINGS_DATE,
        payload={"attribution_model": "data_driven", "raw_model": "PAID_AND_ORGANIC_CHANNELS_DATA_DRIVEN"},
        fetched_by=sample_user.id,
    )
    stale.fetched_at = datetime.utcnow() - timedelta(hours=25)
    db.commit()

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", return_value=({"rows": []}, None))
    mocker.patch(
        "modules.ga4.insights_service.GA4Client.get_attribution_settings",
        return_value=(None, "boom"),
    )

    snapshot = GA4InsightsService.get_channels(db, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert snapshot.payload["attribution_model"] == "data_driven"


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
