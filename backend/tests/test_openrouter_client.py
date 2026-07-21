from unittest.mock import MagicMock

import pytest

from services.ai.openrouter_client import OpenRouterClient


def _client_with_mocked_create(create_return):
    client = OpenRouterClient(api_key="fake-key")
    mock_completions = MagicMock()
    mock_completions.create.return_value = create_return
    mock_chat = MagicMock()
    mock_chat.completions = mock_completions
    mock_with_options = MagicMock()
    mock_with_options.chat = mock_chat
    client.client = MagicMock()
    client.client.with_options.return_value = mock_with_options
    return client


def test_generate_content_raises_with_upstream_error_message_when_no_choices():
    """
    Regression test: when the upstream provider (e.g. a rate-limited free model)
    returns a response with no choices but an error payload, generate_content must
    raise with that error message instead of silently returning an empty string
    (which previously surfaced as a confusing "Failed to parse JSON" error downstream).
    """
    fake_response = MagicMock()
    fake_response.choices = None
    fake_response.error = {
        "message": "Upstream error from Nvidia: ResourceExhausted: Worker local total request limit reached (32/32)",
        "code": 502,
    }

    client = _client_with_mocked_create(fake_response)

    with pytest.raises(RuntimeError, match="Upstream error from Nvidia"):
        client.generate_content(prompt="hi", model="nvidia/nemotron-3-ultra-550b-a55b:free")


def test_generate_content_raises_generic_message_when_no_choices_and_no_error():
    fake_response = MagicMock()
    fake_response.choices = None
    fake_response.error = None

    client = _client_with_mocked_create(fake_response)

    with pytest.raises(RuntimeError, match="no choices"):
        client.generate_content(prompt="hi", model="some/model")


def test_generate_content_returns_content_when_choices_present():
    fake_message = MagicMock()
    fake_message.content = "hello world"
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]

    client = _client_with_mocked_create(fake_response)

    assert client.generate_content(prompt="hi", model="some/model") == "hello world"
