from unittest.mock import patch

from services.ai.content_gap_suggester import AIContentGapSuggester


def _suggester():
    with patch("services.ai.content_gap_suggester.ZeaburAIClient") as mock_zeabur_cls:
        mock_zeabur_cls.return_value.generate_content.return_value = ""
        suggester = AIContentGapSuggester(api_key="fake-key", provider="zeabur")
    return suggester, mock_zeabur_cls.return_value


def _openrouter_suggester():
    with patch("services.ai.openrouter_client.OpenRouterClient") as mock_or_cls:
        suggester = AIContentGapSuggester(api_key="fake-key", provider="openrouter")
    return suggester, mock_or_cls.return_value


def test_suggest_directions_empty_missing_keywords_short_circuits():
    suggester, _ = _suggester()
    result = suggester.suggest_directions("https://example.com/page", "頁面標題", [])

    assert result["success"] is True
    assert result["suggestions"] == []


def test_suggest_directions_reports_clear_error_on_empty_ai_response():
    """
    Regression test: an empty AI response (e.g. from a rate-limited free model)
    must surface as a clear "empty response" error, not the previous confusing
    "Failed to parse JSON from response: ..." message.
    """
    suggester, mock_client = _suggester()
    mock_client.generate_content.return_value = ""

    result = suggester.suggest_directions(
        "https://example.com/page",
        "頁面標題",
        [{"query": "kw1", "clicks": 5, "impressions": 100, "position": 8.0}]
    )

    assert result["success"] is False
    assert "empty response" in result["error"]


def test_suggest_directions_uses_streaming_call_for_openrouter():
    """
    Regression test: content gap suggestions for the OpenRouter provider must use
    generate_content_stream (same call pattern as the working GA4 insights AI
    analysis feature in ai_service.py), not the blocking generate_content, since
    some free/rate-limited upstream models only respond correctly to streaming
    requests and silently return empty content on the non-streaming path.
    """
    suggester, mock_client = _openrouter_suggester()
    mock_client.generate_content_stream.return_value = iter([
        '{"suggestions": [{"type": "new_article", "title": "T", ',
        '"outline": ["a"], "target_keywords": ["kw1"], "reasoning": "r"}]}'
    ])

    result = suggester.suggest_directions(
        "https://example.com/page",
        "頁面標題",
        [{"query": "kw1", "clicks": 5, "impressions": 100, "position": 8.0}]
    )

    assert result["success"] is True
    assert len(result["suggestions"]) == 1
    mock_client.generate_content_stream.assert_called_once()
    mock_client.generate_content.assert_not_called()


def test_suggest_directions_parses_valid_json_response():
    suggester, mock_client = _suggester()
    mock_client.generate_content.return_value = '''{
        "suggestions": [
            {
                "type": "new_article",
                "title": "測試標題",
                "outline": ["要點1", "要點2"],
                "target_keywords": ["kw1"],
                "reasoning": "測試理由"
            }
        ]
    }'''

    result = suggester.suggest_directions(
        "https://example.com/page",
        "頁面標題",
        [{"query": "kw1", "clicks": 5, "impressions": 100, "position": 8.0}]
    )

    assert result["success"] is True
    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["type"] == "new_article"
