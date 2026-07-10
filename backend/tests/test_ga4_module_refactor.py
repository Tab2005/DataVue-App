"""
GA4 模組化重構驗證（docs/22 第 0 波）

`ga4_service.py`（642 行單體）的邏輯已拆分至：
- `modules/ga4/client.py`（`GA4Client`）：OAuth / Admin API / Data API RunReport 底層封裝
- `modules/ga4/service.py`（`GA4AnalyticsService`）：報表組裝、快取、週報資料

`ga4_service.GA4Service` 保留為薄轉發層，確保既有呼叫端（`routers/ga4.py`、
`services/report_service.py`）零改動。本檔案驗證：
1. 轉發層每個方法都「真的」轉呼叫新模組（而非重新實作、產生邏輯漂移）。
2. 新模組本身的報表組裝行為（型別轉換、快取、無憑證錯誤）與重構前一致。
3. 既有 `/api/ga4/properties`、`/api/ga4/report` 端點透過轉發層仍正常運作。
"""
from unittest.mock import MagicMock

import pytest


class _FakeValue:
    def __init__(self, value):
        self.value = value


class _FakeRow:
    def __init__(self, dimension_values, metric_values):
        self.dimension_values = [_FakeValue(v) for v in dimension_values]
        self.metric_values = [_FakeValue(v) for v in metric_values]


class _FakeReportResponse:
    def __init__(self, rows, row_count=None):
        self.rows = rows
        self.row_count = row_count if row_count is not None else len(rows)


# ─── 1. 轉發層必須「真的」呼叫新模組 ──────────────────────────────
@pytest.mark.unit
def test_ga4_service_exchange_code_forwards_to_client(mocker):
    from ga4_service import GA4Service

    mock_exchange = mocker.patch(
        "ga4_service.GA4Client.exchange_code", return_value=(True, "ok")
    )
    user = MagicMock()
    result = GA4Service.exchange_code(user, "auth-code", db="db-session")

    mock_exchange.assert_called_once_with(user, "auth-code", "db-session")
    assert result == (True, "ok")


@pytest.mark.unit
def test_ga4_service_get_credentials_forwards_to_client(mocker):
    from ga4_service import GA4Service

    mock_creds = mocker.patch(
        "ga4_service.GA4Client.get_credentials", return_value="fake-creds"
    )
    user = MagicMock()
    result = GA4Service.get_credentials(user, db="db-session")

    mock_creds.assert_called_once_with(user, "db-session")
    assert result == "fake-creds"


@pytest.mark.unit
def test_ga4_service_list_properties_forwards_to_client(mocker):
    from ga4_service import GA4Service

    mock_list = mocker.patch(
        "ga4_service.GA4Client.list_properties",
        return_value=([{"property_id": "123"}], None),
    )
    user = MagicMock()
    result = GA4Service.list_properties(user, db="db-session")

    mock_list.assert_called_once_with(user, "db-session")
    assert result == ([{"property_id": "123"}], None)


@pytest.mark.unit
def test_ga4_service_get_analytics_forwards_to_analytics_service(mocker):
    from ga4_service import GA4Service

    mock_get_analytics = mocker.patch(
        "ga4_service.GA4AnalyticsService.get_analytics",
        return_value=({"rows": []}, None),
    )
    user = MagicMock()
    result = GA4Service.get_analytics(
        user=user,
        property_id="123456",
        start_date="2026-07-01",
        end_date="2026-07-07",
        metrics=["sessions"],
        dimensions=["date"],
        limit=10,
        offset=5,
        db="db-session",
    )

    mock_get_analytics.assert_called_once_with(
        user=user,
        property_id="123456",
        start_date="2026-07-01",
        end_date="2026-07-07",
        metrics=["sessions"],
        dimensions=["date"],
        limit=10,
        offset=5,
        db="db-session",
    )
    assert result == ({"rows": []}, None)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ga4_service_get_weekly_report_data_forwards_to_analytics_service(mocker):
    from ga4_service import GA4Service
    from unittest.mock import AsyncMock

    mock_weekly = mocker.patch(
        "ga4_service.GA4AnalyticsService.get_weekly_report_data",
        new_callable=AsyncMock,
        return_value={"summary": {}},
    )
    user = MagicMock()
    result = await GA4Service.get_weekly_report_data(
        user=user,
        property_id="123456",
        since="2026-07-01",
        until="2026-07-07",
        selected_metrics=["sessions"],
        db="db-session",
    )

    mock_weekly.assert_called_once_with(
        user=user,
        property_id="123456",
        since="2026-07-01",
        until="2026-07-07",
        selected_metrics=["sessions"],
        db="db-session",
    )
    assert result == {"summary": {}}


# ─── 2. modules/ga4/service.py 的報表組裝行為與重構前一致 ─────────
@pytest.mark.unit
def test_get_analytics_no_credentials_returns_error(mocker):
    from modules.ga4.service import GA4AnalyticsService

    mocker.patch("modules.ga4.service.GA4Client.get_credentials", return_value=None)

    result, error = GA4AnalyticsService.get_analytics(
        user=MagicMock(),
        property_id="123456",
        start_date="2026-07-01",
        end_date="2026-07-07",
    )

    assert result is None
    assert error == "No GA4 credentials found"


@pytest.mark.unit
def test_get_analytics_converts_rows_by_type_and_caches_result(mocker):
    from modules.ga4.service import GA4AnalyticsService

    mocker.patch("modules.ga4.service.GA4Client.get_credentials", return_value=MagicMock())

    fake_data_client = MagicMock()
    fake_data_client.run_report.return_value = _FakeReportResponse(
        [
            _FakeRow(["20260701"], ["10", "1.5"]),
            _FakeRow(["20260702"], ["20", "2.25"]),
        ]
    )
    mocker.patch(
        "modules.ga4.service.GA4Client.build_data_client", return_value=fake_data_client
    )

    mocker.patch("modules.ga4.service.cache_get", return_value=None)
    mock_cache_set = mocker.patch("modules.ga4.service.cache_set")

    result, error = GA4AnalyticsService.get_analytics(
        user=MagicMock(),
        property_id="123456",
        start_date="2026-07-01",
        end_date="2026-07-02",
        metrics=["sessions", "bounceRate"],
        dimensions=["date"],
    )

    assert error is None
    # date 維度：YYYYMMDD -> YYYY-MM-DD；整數/浮點指標依欄位型別轉換
    assert result["rows"] == [
        {"date": "2026-07-01", "sessions": 10, "bounceRate": 1.5},
        {"date": "2026-07-02", "sessions": 20, "bounceRate": 2.25},
    ]
    assert result["property_id"] == "123456"
    mock_cache_set.assert_called_once()


@pytest.mark.unit
def test_get_analytics_returns_cached_result_without_calling_api(mocker):
    from modules.ga4.service import GA4AnalyticsService

    mocker.patch("modules.ga4.service.GA4Client.get_credentials", return_value=MagicMock())
    fake_data_client = MagicMock()
    mocker.patch(
        "modules.ga4.service.GA4Client.build_data_client", return_value=fake_data_client
    )
    cached_payload = {
        "property_id": "123456",
        "date_range": {"start_date": "2026-07-01", "end_date": "2026-07-02"},
        "dimensions": ["date"],
        "metrics": ["sessions"],
        "row_count": 1,
        "total_row_count": 1,
        "limit": None,
        "offset": 0,
        "rows": [{"date": "2026-07-01", "sessions": 10}],
    }
    mocker.patch("modules.ga4.service.cache_get", return_value=cached_payload)

    result, error = GA4AnalyticsService.get_analytics(
        user=MagicMock(),
        property_id="123456",
        start_date="2026-07-01",
        end_date="2026-07-02",
        metrics=["sessions"],
        dimensions=["date"],
    )

    assert error is None
    assert result == cached_payload
    # 快取命中時不應真的打 GA4 Data API（build_data_client 會被建構，但
    # run_report 不會被呼叫——與重構前行為一致）
    fake_data_client.run_report.assert_not_called()


@pytest.mark.unit
def test_get_analytics_splits_requests_over_ten_metrics(mocker):
    from modules.ga4.service import GA4AnalyticsService

    metrics = [f"metric{i}" for i in range(12)]
    mock_recurse = mocker.patch.object(
        GA4AnalyticsService,
        "get_analytics",
        wraps=GA4AnalyticsService.get_analytics,
    )
    mocker.patch("modules.ga4.service.GA4Client.get_credentials", return_value=MagicMock())

    def _fake_run_report(request):
        return _FakeReportResponse([_FakeRow(["20260701"], ["1"] * len(request.metrics))])

    fake_data_client = MagicMock()
    fake_data_client.run_report.side_effect = _fake_run_report
    mocker.patch("modules.ga4.service.GA4Client.build_data_client", return_value=fake_data_client)
    mocker.patch("modules.ga4.service.cache_get", return_value=None)
    mocker.patch("modules.ga4.service.cache_set")

    result, error = GA4AnalyticsService.get_analytics(
        user=MagicMock(),
        property_id="123456",
        start_date="2026-07-01",
        end_date="2026-07-01",
        metrics=metrics,
        dimensions=["date"],
    )

    assert error is None
    # 12 個指標拆成 10 + 2 兩批請求，合併回單一 row
    assert fake_data_client.run_report.call_count == 2
    assert set(result["rows"][0].keys()) == {"date", *metrics}


# ─── 3. 既有 API 端點透過轉發層仍正常運作 ──────────────────────────
@pytest.mark.integration
def test_ga4_properties_endpoint_still_works_through_forwarding_layer(
    client, db, sample_user, mocker
):
    import routers.ga4 as ga4_router_module
    from dependencies import get_current_user as root_get_current_user
    from main import app

    mocker.patch(
        "ga4_service.GA4Client.list_properties",
        return_value=([{"property_id": "123456", "display_name": "Demo"}], None),
    )
    app.dependency_overrides[root_get_current_user] = lambda: sample_user
    app.dependency_overrides[ga4_router_module.ga4_module_check] = lambda: True
    try:
        response = client.get("/api/ga4/properties")
    finally:
        app.dependency_overrides.pop(root_get_current_user, None)
        app.dependency_overrides.pop(ga4_router_module.ga4_module_check, None)

    assert response.status_code == 200
    assert response.json() == {
        "properties": [{"property_id": "123456", "display_name": "Demo"}]
    }


@pytest.mark.integration
def test_ga4_report_endpoint_still_works_through_forwarding_layer(
    client, db, sample_user, mocker
):
    import routers.ga4 as ga4_router_module
    from dependencies import get_current_user as root_get_current_user
    from main import app

    fake_result = {
        "property_id": "123456",
        "date_range": {"start_date": "2026-07-01", "end_date": "2026-07-07"},
        "dimensions": ["date"],
        "metrics": ["sessions"],
        "row_count": 1,
        "total_row_count": 1,
        "limit": None,
        "offset": 0,
        "rows": [{"date": "2026-07-01", "sessions": 10}],
    }
    mocker.patch(
        "ga4_service.GA4AnalyticsService.get_analytics",
        return_value=(fake_result, None),
    )
    app.dependency_overrides[root_get_current_user] = lambda: sample_user
    app.dependency_overrides[ga4_router_module.ga4_module_check] = lambda: True
    try:
        response = client.get(
            "/api/ga4/report",
            params={
                "property_id": "123456",
                "start_date": "2026-07-01",
                "end_date": "2026-07-07",
            },
        )
    finally:
        app.dependency_overrides.pop(root_get_current_user, None)
        app.dependency_overrides.pop(ga4_router_module.ga4_module_check, None)

    assert response.status_code == 200
    assert response.json() == fake_result
