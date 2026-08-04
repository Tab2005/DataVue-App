"""GA4 查詢並行化的測試（docs/65 / docs/59 P1-2）。

重點不只是「有沒有變快」，而是並行化最容易出事的那一項：**worker thread
不可以碰請求的 SQLAlchemy Session**。下面用一個「一被碰到就爆炸」的假 Session
把這條保證釘住。
"""

import threading
import time

import pytest

from modules.ga4.insights._parallel import run_parallel


# ─── run_parallel 本身 ────────────────────────────────────────────────


@pytest.mark.unit
def test_run_parallel_actually_runs_tasks_concurrently():
    """兩個 task 互等對方到齊才往下走——循序執行會卡在 barrier 直到 timeout。"""
    barrier = threading.Barrier(2, timeout=5)

    def _task(name):
        def _run():
            barrier.wait()  # 循序跑的話這裡會 BrokenBarrierError
            return name
        return _run

    results = run_parallel({"a": _task("a"), "b": _task("b")})

    assert results == {"a": "a", "b": "b"}


@pytest.mark.unit
def test_run_parallel_returns_results_keyed_by_task_name():
    results = run_parallel({
        "first": lambda: 1,
        "second": lambda: 2,
        "third": lambda: 3,
    })
    assert results == {"first": 1, "second": 2, "third": 3}


@pytest.mark.unit
def test_run_parallel_propagates_task_exception():
    """task 的例外要原樣往外傳，呼叫端既有的錯誤處理才不會因為並行而失效。"""
    def _boom():
        raise RuntimeError("GA4 said no")

    with pytest.raises(RuntimeError, match="GA4 said no"):
        run_parallel({"ok": lambda: 1, "boom": _boom})


@pytest.mark.unit
def test_run_parallel_waits_for_every_task_even_when_one_fails():
    """有 task 失敗時，其他 task 也要跑完才離開，不留下背景還在跑的查詢。"""
    finished = []

    def _slow():
        time.sleep(0.05)
        finished.append("slow")
        return "slow"

    def _boom():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        run_parallel({"boom": _boom, "slow": _slow})

    assert finished == ["slow"]


@pytest.mark.unit
def test_run_parallel_single_task_runs_on_calling_thread():
    """只有一支查詢時不值得進 pool。"""
    caller = threading.current_thread().name
    results = run_parallel({"only": lambda: threading.current_thread().name})
    assert results["only"] == caller


@pytest.mark.unit
def test_run_parallel_with_no_tasks():
    assert run_parallel({}) == {}


# ─── credentials 有傳就不碰 user / db ────────────────────────────────


@pytest.mark.unit
def test_get_analytics_skips_credential_lookup_when_credentials_given(mocker):
    from modules.ga4.service import GA4AnalyticsService

    get_credentials = mocker.patch("modules.ga4.service.GA4Client.get_credentials")
    # 憑證直接給，get_analytics 就不該再去 get_credentials（那支會碰 db 並 commit）。
    sentinel_credentials = object()
    # 建 client 的那一步擋下來，不要真的打出去；重點是沒有去查憑證。
    build_data_client = mocker.patch(
        "modules.ga4.service.GA4Client.build_data_client",
        side_effect=RuntimeError("stop here"),
    )

    data, error = GA4AnalyticsService.get_analytics(
        user=mocker.MagicMock(), property_id="123456",
        start_date="2026-08-01", end_date="2026-08-01",
        metrics=["sessions"], dimensions=[], db="a-session",
        credentials=sentinel_credentials,
    )

    get_credentials.assert_not_called()
    # 確認真的拿我們給的憑證往下走，而不是在前面就斷掉了。
    build_data_client.assert_called_once_with(sentinel_credentials)
    assert data is None and error is not None


@pytest.mark.unit
def test_get_analytics_falls_back_to_credential_lookup_without_credentials(mocker):
    from modules.ga4.service import GA4AnalyticsService

    get_credentials = mocker.patch(
        "modules.ga4.service.GA4Client.get_credentials", return_value=None,
    )

    data, error = GA4AnalyticsService.get_analytics(
        user=mocker.MagicMock(), property_id="123456",
        start_date="2026-08-01", end_date="2026-08-01",
        metrics=["sessions"], dimensions=[], db="a-session",
    )

    get_credentials.assert_called_once()
    assert error == "No GA4 credentials found"


# ─── 並行查詢完全不碰請求 Session ─────────────────────────────────────


class _ExplodingSession:
    """一被 worker thread 碰到就記錄下來的假 Session。

    請求執行緒（建立它的那條）怎麼用都可以；只要有別條執行緒碰到任何屬性，
    就把該執行緒名字記下來——測試據此斷言 worker 完全沒碰過它。
    """

    def __init__(self, real_session):
        object.__setattr__(self, "_real", real_session)
        object.__setattr__(self, "_owner", threading.current_thread().ident)
        object.__setattr__(self, "foreign_thread_access", [])

    def __getattr__(self, name):
        if threading.current_thread().ident != object.__getattribute__(self, "_owner"):
            object.__getattribute__(self, "foreign_thread_access").append(
                (threading.current_thread().name, name)
            )
        return getattr(object.__getattribute__(self, "_real"), name)


def _landing_page_stub(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
    # 並行的查詢一律不該帶著 db 進來——帶了就代表 worker 有機會碰到 Session。
    assert db is None, f"parallel query received a db session: {dimensions}"
    if dimensions == ["landingPage", "eventName"]:
        return {"rows": []}, None
    return {
        "rows": [{
            "landingPage": "/products/a", "sessions": 40, "engagementRate": 0.5,
            "keyEvents": 2, "bounceRate": 0.3, "sessionKeyEventRate": 0.05,
        }]
    }, None


@pytest.mark.unit
def test_landing_pages_parallel_queries_never_touch_the_request_session(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=_landing_page_stub)
    guarded = _ExplodingSession(db)

    snapshot = GA4InsightsService.get_landing_pages(
        guarded, user=sample_user, property_id="123456", days=7, compare=True,
    )
    db.commit()

    assert guarded.foreign_thread_access == []
    assert snapshot.payload["landing_pages"][0]["landingPage"] == "/products/a"


def _items_stub(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
    assert db is None, f"parallel query received a db session: {dimensions}"
    if dimensions == ["itemName", "itemCategory"]:
        return {"rows": [{"itemName": "P1", "itemCategory": "Apparel", "itemsViewed": 100}]}, None
    if metrics == ["itemsViewed"]:
        return {"rows": [{"itemName": "P1", "itemsViewed": 50}]}, None
    return {
        "rows": [{
            "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20,
            "itemsPurchased": 10, "itemRevenue": 500.0,
            "cartToViewRate": 0.2, "purchaseToViewRate": 0.1,
        }]
    }, None


@pytest.mark.unit
def test_items_parallel_queries_never_touch_the_request_session(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=_items_stub)
    guarded = _ExplodingSession(db)

    snapshot = GA4InsightsService.get_items(
        guarded, user=sample_user, property_id="123456", days=7, compare=True,
    )
    db.commit()

    assert guarded.foreign_thread_access == []
    assert snapshot.payload["items"][0]["itemName"] == "P1"


@pytest.mark.unit
def test_item_landing_cross_parallel_queries_never_touch_the_request_session(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    def _stub(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        assert db is None, f"parallel query received a db session: {dimensions}"
        if dimensions == ["itemName", "landingPage"]:
            return {"rows": [{"itemName": "P1", "landingPage": "/p/1", "itemsViewed": 80}]}, None
        if dimensions == ["landingPage"]:
            return {"rows": [{"landingPage": "/p/1", "sessions": 200, "sessionKeyEventRate": 0.02, "bounceRate": 0.4}]}, None
        return {
            "rows": [{
                "itemName": "P1", "itemsViewed": 100, "itemsAddedToCart": 20,
                "itemsPurchased": 10, "itemRevenue": 500.0,
                "cartToViewRate": 0.2, "purchaseToViewRate": 0.1,
            }]
        }, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=_stub)
    guarded = _ExplodingSession(db)

    snapshot = GA4InsightsService.get_item_landing_cross(
        guarded, user=sample_user, property_id="123456", days=7, compare=True,
    )
    db.commit()

    assert guarded.foreign_thread_access == []
    assert snapshot.payload["items"][0]["itemName"] == "P1"


@pytest.mark.unit
def test_channels_parallel_queries_never_touch_the_request_session(mocker, db, sample_user):
    from modules.ga4.insights_service import GA4InsightsService

    def _stub(*, user, property_id, start_date, end_date, metrics, dimensions, db=None, **_):
        assert db is None, f"parallel query received a db session: {dimensions}"
        return {"rows": [{dimensions[0]: "google / organic", "keyEvents": 30}]}, None

    mocker.patch("modules.ga4.insights_service.GA4Service.get_analytics", side_effect=_stub)
    mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._get_attribution_model",
        return_value="last_click",
    )
    guarded = _ExplodingSession(db)

    snapshot = GA4InsightsService.get_channels(guarded, user=sample_user, property_id="123456", days=7)
    db.commit()

    assert guarded.foreign_thread_access == []
    assert snapshot.payload["channels"][0]["channel"] == "google / organic"


# ─── 儀表板基線取樣並行後結果不變 ────────────────────────────────────


@pytest.mark.unit
def test_dashboard_baseline_samples_run_in_parallel_and_keep_date_order(mocker):
    """8 個取樣日並行抓，samples 內容仍依歷史日期順序，不受完成先後影響。"""
    from modules.ga4.insights_service import GA4InsightsService

    seen_threads = set()
    captured = {}

    def fake_fetch(*, user, property_id, date_value, api_metric, db, by_hour=False, current_hour=None, credentials=None):
        assert db is None, "baseline sample received a db session"
        seen_threads.add(threading.current_thread().name)
        # 讓後面的日期先回，故意打亂完成順序。
        time.sleep(0.02 if date_value.endswith("-01") else 0.0)
        return float(date_value[-2:]), []

    mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._fetch_metric_total",
        side_effect=fake_fetch,
    )
    mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._historical_dates",
        return_value=["2026-07-01", "2026-07-08", "2026-07-15", "2026-07-22"],
    )
    mocker.patch(
        "modules.ga4.insights.dashboard.build_expected_range",
        side_effect=lambda samples, sensitivity: captured.setdefault("samples", list(samples)) and None,
    )

    from modules.ga4.insights.dashboard import _compute_metric_baseline

    _compute_metric_baseline(
        user=mocker.MagicMock(), property_id="123456", api_metric="keyEvents",
        now_local=None, current_hour=12, db=None, observed=10.0,
    )

    assert captured["samples"] == [1.0, 8.0, 15.0, 22.0]
    assert len(seen_threads) > 1  # 真的有分到不同執行緒


@pytest.mark.unit
def test_dashboard_baseline_skips_failed_samples(mocker):
    """單一取樣失敗只跳過該筆，其餘照算（並行化前後同樣的容錯行為）。"""
    from modules.ga4.insights_service import GA4InsightsService

    captured = {}

    def fake_fetch(*, user, property_id, date_value, api_metric, db, by_hour=False, current_hour=None, credentials=None):
        if date_value == "2026-07-08":
            raise RuntimeError("GA4 data unavailable")
        return float(date_value[-2:]), []

    mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._fetch_metric_total",
        side_effect=fake_fetch,
    )
    mocker.patch(
        "modules.ga4.insights_service.GA4InsightsService._historical_dates",
        return_value=["2026-07-01", "2026-07-08", "2026-07-15"],
    )
    mocker.patch(
        "modules.ga4.insights.dashboard.build_expected_range",
        side_effect=lambda samples, sensitivity: captured.setdefault("samples", list(samples)) and None,
    )

    from modules.ga4.insights.dashboard import _compute_metric_baseline

    _compute_metric_baseline(
        user=mocker.MagicMock(), property_id="123456", api_metric="keyEvents",
        now_local=None, current_hour=12, db=None, observed=10.0,
    )

    assert captured["samples"] == [1.0, 15.0]
