import json

import httpx
import pytest

from translator.minimax import TranslateError, translate

API_KEY = "test-key"
ENDPOINT = "https://api.test/v1/chat"
MODEL = "test-model"


def _ok(content="你好"):
    return {"choices": [{"message": {"content": content}}]}


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
    body = json.loads(req.read())
    assert body["model"] == MODEL
    assert body["messages"][1]["content"] == "hello"
    assert "Simplified Chinese" in body["messages"][0]["content"]


def test_zh_to_en_uses_english_prompt(httpx_mock):
    httpx_mock.add_response(json=_ok("hi"))
    _call(direction="zh→en", text="你好")
    body = json.loads(httpx_mock.get_request().read())
    assert "English" in body["messages"][0]["content"]


def test_strips_whitespace_from_translation(httpx_mock):
    httpx_mock.add_response(json=_ok("  hello  \n"))
    assert _call() == "hello"


def test_4xx_raises(httpx_mock):
    httpx_mock.add_response(status_code=401, text="unauthorized")
    with pytest.raises(TranslateError, match="401"):
        _call()


def test_5xx_retries_then_succeeds(httpx_mock):
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(json=_ok("你好"))
    assert _call() == "你好"


def test_5xx_persistent_fails(httpx_mock):
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(status_code=500)
    with pytest.raises(TranslateError, match="500"):
        _call()


def test_network_error(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("dns fail"))
    with pytest.raises(TranslateError, match="网络"):
        _call()


def test_malformed_response(httpx_mock):
    httpx_mock.add_response(json={"unexpected": "shape"})
    with pytest.raises(TranslateError, match="解析"):
        _call()
