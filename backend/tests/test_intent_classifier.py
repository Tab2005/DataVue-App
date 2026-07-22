from unittest.mock import patch

from services.ai.intent_classifier import AIIntentClassifier


def _zeabur_classifier():
    with patch("services.ai.intent_classifier.ZeaburAIClient") as mock_zeabur_cls:
        suggester = AIIntentClassifier(api_key="fake-key", provider="zeabur")
    return suggester, mock_zeabur_cls.return_value


def _openrouter_classifier():
    with patch("services.ai.openrouter_client.OpenRouterClient") as mock_or_cls:
        classifier = AIIntentClassifier(api_key="fake-key", provider="openrouter")
    return classifier, mock_or_cls.return_value


def test_classify_queries_uses_streaming_call_for_openrouter():
    """
    Regression test: search intent classification for the OpenRouter provider must
    use generate_content_stream (same call pattern as the working GA4 insights AI
    analysis feature and AIContentGapSuggester), not the blocking generate_content,
    since some free/rate-limited upstream models silently return empty content on
    the non-streaming path.
    """
    classifier, mock_client = _openrouter_classifier()
    mock_client.generate_content_stream.return_value = iter([
        '{"results": [{"query": "kw1", "primary_intent": "informational", ',
        '"confidence": 0.9, "intent_distribution": {"informational": 0.7, '
        '"commercial": 0.1, "navigational": 0.1, "transactional": 0.1}, "reasoning": "r"}]}'
    ])

    result = classifier.classify_queries(["kw1"])

    assert result["success"] is True
    assert len(result["results"]) == 1
    mock_client.generate_content_stream.assert_called_once()
    mock_client.generate_content.assert_not_called()


def test_classify_queries_reports_clear_error_on_empty_ai_response():
    classifier, mock_client = _zeabur_classifier()
    mock_client.generate_content.return_value = ""

    result = classifier.classify_queries(["kw1"])

    assert result["success"] is False
    assert "empty response" in result["error"]


def test_classify_queries_parses_valid_json_response():
    classifier, mock_client = _zeabur_classifier()
    mock_client.generate_content.return_value = '''{
        "results": [
            {
                "query": "kw1",
                "primary_intent": "commercial",
                "confidence": 0.8,
                "intent_distribution": {"informational": 0.1, "commercial": 0.7, "navigational": 0.1, "transactional": 0.1},
                "reasoning": "測試理由"
            }
        ]
    }'''

    result = classifier.classify_queries(["kw1"])

    assert result["success"] is True
    assert result["results"][0]["primary_intent"] == "commercial"
