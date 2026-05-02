import json

import httpx
import pytest

from translator.minimax import TranslateError, translate

API_KEY = "test-key"
ENDPOINT = "https://api.test/anthropic/v1/messages"
MODEL = "test-model"


def _ok(text="你好"):
    """Anthropic-style success body with a single text block."""
    return {"content": [{"type": "text", "text": text}]}


def _call(direction="auto→zh", text="hello"):
    return translate(
        text, direction, api_key=API_KEY, model=MODEL, endpoint=ENDPOINT
    )


def test_returns_translation(httpx_mock):
    httpx_mock.add_response(json=_ok("你好"))
    assert _call() == "你好"


def test_request_shape(httpx_mock):
    httpx_mock.add_response(json=_ok())
    _call()
    req = httpx_mock.get_request()
    assert req.url == ENDPOINT
    assert req.method == "POST"
    assert req.headers["authorization"] == f"Bearer {API_KEY}"
    assert req.headers["anthropic-version"] == "2023-06-01"
    body = json.loads(req.read())
    assert body["model"] == MODEL
    assert "Simplified Chinese" in body["system"]
    # Anthropic format: messages[0].content is a list of blocks
    assert body["messages"][0]["content"][0]["text"] == "hello"
    assert body["messages"][0]["content"][0]["type"] == "text"


def test_zh_to_en_uses_english_prompt(httpx_mock):
    httpx_mock.add_response(json=_ok("hi"))
    _call(direction="zh→en", text="你好")
    body = json.loads(httpx_mock.get_request().read())
    assert "English" in body["system"]


def test_strips_whitespace_from_translation(httpx_mock):
    httpx_mock.add_response(json=_ok("  hello  \n"))
    assert _call() == "hello"


def test_concatenates_multiple_text_blocks(httpx_mock):
    httpx_mock.add_response(
        json={"content": [
            {"type": "text", "text": "Hello "},
            {"type": "text", "text": "world"},
        ]}
    )
    assert _call() == "Hello world"


def test_skips_thinking_blocks(httpx_mock):
    httpx_mock.add_response(
        json={"content": [
            {"type": "thinking", "thinking": "let me think..."},
            {"type": "text", "text": "你好"},
        ]}
    )
    assert _call() == "你好"


def test_4xx_raises_with_anthropic_error_message(httpx_mock):
    httpx_mock.add_response(
        status_code=401,
        json={"type": "error", "error": {"message": "invalid api key"}},
    )
    with pytest.raises(TranslateError, match="401.*invalid api key"):
        _call()


def test_4xx_falls_back_to_raw_text_when_no_error_envelope(httpx_mock):
    httpx_mock.add_response(status_code=400, text="bad request")
    with pytest.raises(TranslateError, match="400.*bad request"):
        _call()


def test_5xx_retries_then_succeeds(httpx_mock):
    httpx_mock.add_response(status_code=500, text="server error")
    httpx_mock.add_response(json=_ok("你好"))
    assert _call() == "你好"


def test_5xx_persistent_fails(httpx_mock):
    httpx_mock.add_response(status_code=500, text="err1")
    httpx_mock.add_response(status_code=500, text="err2")
    with pytest.raises(TranslateError, match="500"):
        _call()


def test_network_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("dns fail"))
    with pytest.raises(TranslateError, match="网络"):
        _call()


def test_malformed_response_no_content(httpx_mock):
    httpx_mock.add_response(json={"unexpected": "shape"})
    with pytest.raises(TranslateError, match="解析"):
        _call()


def test_empty_text_blocks(httpx_mock):
    httpx_mock.add_response(json={"content": [{"type": "thinking", "thinking": "..."}]})
    with pytest.raises(TranslateError, match="无 text"):
        _call()
