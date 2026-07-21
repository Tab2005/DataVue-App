from unittest.mock import patch, MagicMock

from dependencies import get_current_user
from routers.gsc import gsc_module_check


def _override_dependencies(app, user):
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[gsc_module_check] = lambda: True


def test_content_gap_suggestions_with_provided_missing_keywords(client, sample_user):
    _override_dependencies(client.app, sample_user)

    fake_result = {
        "success": True,
        "model": "deepseek/deepseek-v4-flash",
        "page": "https://example.com/page",
        "suggestions": [
            {
                "type": "new_article",
                "title": "新文章方向",
                "outline": ["要點1", "要點2"],
                "target_keywords": ["kw1", "kw2"],
                "reasoning": "測試理由"
            }
        ]
    }

    with patch("modules.auth.service.TokenManager.get_ai_api_key", return_value="fake-key"), \
         patch("services.ai.content_gap_suggester.AIContentGapSuggester.suggest_directions", return_value=fake_result):
        resp = client.post(
            "/api/gsc/content-gap-suggestions",
            json={
                "site_url": "sc-domain:example.com",
                "page_url": "https://example.com/page",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "missing_keywords": [
                    {"query": "kw1", "clicks": 5, "impressions": 100, "position": 8.0},
                    {"query": "kw2", "clicks": 2, "impressions": 50, "position": 15.0}
                ]
            }
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == "https://example.com/page"
    assert data["keyword_count"] == 2
    assert data["model"] == "deepseek/deepseek-v4-flash"
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["type"] == "new_article"


def test_content_gap_suggestions_no_missing_keywords_short_circuits(client, sample_user):
    _override_dependencies(client.app, sample_user)

    with patch("modules.auth.service.TokenManager.get_ai_api_key", return_value="fake-key"), \
         patch("services.ai.content_gap_suggester.AIContentGapSuggester.suggest_directions") as mock_suggest:
        resp = client.post(
            "/api/gsc/content-gap-suggestions",
            json={
                "site_url": "sc-domain:example.com",
                "page_url": "https://example.com/page",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "missing_keywords": []
            }
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["suggestions"] == []
    assert "message" in data
    mock_suggest.assert_not_called()


def test_content_gap_suggestions_no_api_key_returns_empty_state(client, sample_user):
    _override_dependencies(client.app, sample_user)

    with patch("modules.auth.service.TokenManager.get_ai_api_key", return_value=None), \
         patch.dict("os.environ", {}, clear=False), \
         patch("os.getenv", return_value=None):
        resp = client.post(
            "/api/gsc/content-gap-suggestions",
            json={
                "site_url": "sc-domain:example.com",
                "page_url": "https://example.com/page",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "missing_keywords": [
                    {"query": "kw1", "clicks": 5, "impressions": 100, "position": 8.0}
                ]
            }
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["suggestions"] == []
    assert "API key not configured" in data["message"]


def test_content_gap_suggestions_falls_back_to_keyword_gap_analysis(client, sample_user):
    _override_dependencies(client.app, sample_user)

    gap_result = {
        "page": "https://example.com/page",
        "page_title": "測試頁面",
        "status": "success",
        "results": [
            {"query": "kw1", "clicks": 5, "impressions": 100, "ctr": 0.05, "position": 8.0, "in_content": False},
            {"query": "kw2", "clicks": 2, "impressions": 50, "ctr": 0.04, "position": 15.0, "in_content": True}
        ],
        "total_analyzed": 2,
        "missing_count": 1,
        "total_found_in_gsc": 2
    }

    fake_result = {
        "success": True,
        "model": "deepseek/deepseek-v4-flash",
        "page": "https://example.com/page",
        "suggestions": []
    }

    with patch("routers.gsc._compute_keyword_gap", return_value=gap_result), \
         patch("modules.auth.service.TokenManager.get_ai_api_key", return_value="fake-key"), \
         patch("services.ai.content_gap_suggester.AIContentGapSuggester.suggest_directions", return_value=fake_result) as mock_suggest:
        resp = client.post(
            "/api/gsc/content-gap-suggestions",
            json={
                "site_url": "sc-domain:example.com",
                "page_url": "https://example.com/page",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31"
            }
        )

    assert resp.status_code == 200
    # Only the in_content=False keyword should have been passed to the AI suggester.
    call_args = mock_suggest.call_args
    passed_keywords = call_args.args[2] if len(call_args.args) > 2 else call_args.kwargs.get("missing_keywords")
    assert len(passed_keywords) == 1
    assert passed_keywords[0]["query"] == "kw1"


def test_content_gap_suggestions_uses_user_configured_model(client, sample_user):
    """
    Regression test: the AI model actually requested must follow the user's
    saved ai_model setting (TokenManager.get_ai_settings), not a hardcoded
    default, regardless of which provider/model the frontend passed.
    """
    _override_dependencies(client.app, sample_user)

    mock_instance = MagicMock()
    mock_instance.suggest_directions.return_value = {
        "success": True,
        "model": "nvidia/nemotron-3-ultra:free",
        "page": "https://example.com/page",
        "suggestions": []
    }

    with patch("modules.auth.service.TokenManager.get_ai_api_key", return_value="fake-key"), \
         patch(
             "modules.auth.service.TokenManager.get_ai_settings",
             return_value={"ai_provider": "openrouter", "ai_model": "nvidia/nemotron-3-ultra:free"}
         ), \
         patch("services.ai.AIContentGapSuggester", return_value=mock_instance) as mock_cls:
        resp = client.post(
            "/api/gsc/content-gap-suggestions",
            json={
                "site_url": "sc-domain:example.com",
                "page_url": "https://example.com/page",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "provider": "openrouter",
                "missing_keywords": [
                    {"query": "kw1", "clicks": 5, "impressions": 100, "position": 8.0}
                ]
            }
        )

    assert resp.status_code == 200
    assert resp.json()["model"] == "nvidia/nemotron-3-ultra:free"
    mock_cls.assert_called_once_with(api_key="fake-key", provider="openrouter", model="nvidia/nemotron-3-ultra:free")


def test_content_gap_suggestions_ai_failure_returns_500(client, sample_user):
    _override_dependencies(client.app, sample_user)

    with patch("modules.auth.service.TokenManager.get_ai_api_key", return_value="fake-key"), \
         patch("services.ai.content_gap_suggester.AIContentGapSuggester.suggest_directions",
               return_value={"success": False, "error": "boom", "suggestions": []}):
        resp = client.post(
            "/api/gsc/content-gap-suggestions",
            json={
                "site_url": "sc-domain:example.com",
                "page_url": "https://example.com/page",
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "missing_keywords": [
                    {"query": "kw1", "clicks": 5, "impressions": 100, "position": 8.0}
                ]
            }
        )

    assert resp.status_code == 500
