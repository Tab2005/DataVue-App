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


# ─── 串流中途錯誤與標頭（OpenRouter 文件：api_reference/streaming） ───────────
from types import SimpleNamespace


def _chunk(content=None, finish_reason=None, error=None, with_choice=True):
    choices = (
        [SimpleNamespace(delta=SimpleNamespace(content=content), finish_reason=finish_reason)]
        if with_choice else []
    )
    chunk = SimpleNamespace(choices=choices)
    if error is not None:
        chunk.error = error
    return chunk


def _stream_client(chunks):
    client = OpenRouterClient(api_key="fake-key")
    client.client = MagicMock()
    client.client.chat.completions.create.return_value = iter(chunks)
    return client


def test_stream_yields_content_normally():
    client = _stream_client([_chunk("Hel"), _chunk("lo"), _chunk(None, finish_reason="stop")])
    assert "".join(client.generate_content_stream("hi")) == "Hello"


def test_stream_raises_on_error_chunk_that_still_has_choices():
    """OpenRouter 在串流中途出錯時回 HTTP 200 + 帶 error 與 finish_reason=error 的 chunk。"""
    client = _stream_client([
        _chunk("partial "),
        _chunk(None, finish_reason="error", error={"code": 502, "message": "Provider disconnected"}),
    ])
    with pytest.raises(RuntimeError, match="Provider disconnected"):
        list(client.generate_content_stream("hi"))


def test_stream_raises_on_finish_reason_error_without_error_payload():
    client = _stream_client([_chunk(None, finish_reason="error")])
    with pytest.raises(RuntimeError, match="finish_reason=error"):
        list(client.generate_content_stream("hi"))


def test_stream_raises_on_error_chunk_without_choices():
    client = _stream_client([_chunk(with_choice=False, error={"message": "Rate limited upstream"})])
    with pytest.raises(RuntimeError, match="Rate limited upstream"):
        list(client.generate_content_stream("hi"))


def test_stream_skips_empty_keepalive_chunks():
    client = _stream_client([_chunk(with_choice=False), _chunk("ok")])
    assert list(client.generate_content_stream("hi")) == ["ok"]


def test_generate_content_raises_when_finish_reason_error_and_no_content():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=""), finish_reason="error")],
        error={"message": "Upstream timeout"},
    )
    client = _client_with_mocked_create(response)
    with pytest.raises(RuntimeError, match="Upstream timeout"):
        client.generate_content(prompt="hi", model="some/model")


def test_sends_openrouter_attribution_headers():
    headers = OpenRouterClient(api_key="fake-key").client.default_headers
    assert headers["HTTP-Referer"] == "https://datavue.sitetegy.com"
    assert headers["X-OpenRouter-Title"] == "DataVue-App"
    assert headers["X-Title"] == "DataVue-App"
