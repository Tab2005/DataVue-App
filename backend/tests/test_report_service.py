from unittest.mock import AsyncMock

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_report_content_passes_team_id(mocker):
    mock_custom_report = AsyncMock(return_value=[{"spend": 100, "impressions": 1000, "inline_link_clicks": 10}])
    mock_trend_report = AsyncMock(return_value=[])

    mocker.patch("modules.fb_ads.analytics_service.get_custom_report", mock_custom_report)
    mocker.patch("modules.fb_ads.trends_service.get_analytics_trend", mock_trend_report)

    from services.report_service import generate_report_content

    await generate_report_content(
        db=None,
        ad_account_id="act_123",
        since="2026-04-01",
        until="2026-04-07",
        breakdown="campaign",
        selected_metrics=["spend", "roas"],
        google_id="google-user-1",
        team_id="team-1",
    )

    assert mock_custom_report.await_args.kwargs["team_id"] == "team-1"
    assert mock_trend_report.await_args.kwargs["team_id"] == "team-1"