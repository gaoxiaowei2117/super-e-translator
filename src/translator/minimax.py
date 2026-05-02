"""MiniMax client (Anthropic-compatible API).

MiniMax's current text models (M2 series) are exposed via an Anthropic-style
Messages API at https://api.minimaxi.com/anthropic/v1/messages.

Response `content` is a list of blocks; we keep only `type=="text"` blocks
and drop `type=="thinking"` (M2 reasoning chain).
"""
import httpx

PROMPTS = {
    "auto→zh": (
        "You are a translator. Translate the user message to Simplified Chinese. "
        "Output only the translation, no explanation."
    ),
    "zh→en": (
        "You are a translator. Translate the user message to English. "
        "Output only the translation, no explanation."
    ),
}


class TranslateError(Exception):
    pass


def translate(
    text: str,
    direction: str,
    *,
    api_key: str,
    model: str,
    endpoint: str,
    timeout: float = 30.0,
) -> str:
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": PROMPTS[direction],
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": text}]}
        ],
        "temperature": 1.0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    for attempt in range(2):
        try:
            r = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
        except httpx.RequestError as e:
            raise TranslateError(f"网络错误: {e}") from e

        if r.status_code < 400:
            try:
                body = r.json()
            except ValueError as e:
                raise TranslateError(f"响应解析失败: {r.text[:200]}") from e

            try:
                blocks = body["content"]
                texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
                result = "".join(texts).strip()
            except (KeyError, IndexError, TypeError, AttributeError) as e:
                raise TranslateError(f"响应解析失败: {str(body)[:200]}") from e

            if not result:
                raise TranslateError(f"响应中无 text 内容: {str(body)[:200]}")
            return result

        if r.status_code >= 500 and attempt == 0:
            continue

        # Anthropic-style error envelope: {"type": "error", "error": {"message": "..."}}
        try:
            err = r.json().get("error") or {}
            msg = err.get("message") or r.text[:200]
        except ValueError:
            msg = r.text[:200]
        raise TranslateError(f"HTTP {r.status_code}: {msg}")

    raise TranslateError("unreachable")  # pragma: no cover
