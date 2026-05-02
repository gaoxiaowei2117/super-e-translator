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
    timeout: float = 15.0,
) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": PROMPTS[direction]},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
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

            # MiniMax returns HTTP 200 with errors in base_resp (status_code != 0).
            base_resp = body.get("base_resp") or {}
            err_code = base_resp.get("status_code")
            if err_code not in (0, None):
                raise TranslateError(
                    f"MiniMax 错误 {err_code}: {base_resp.get('status_msg', '')}"
                )

            try:
                return body["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError, TypeError, AttributeError) as e:
                raise TranslateError(f"响应解析失败: {str(body)[:200]}") from e

        if r.status_code >= 500 and attempt == 0:
            continue

        raise TranslateError(f"HTTP {r.status_code}: {r.text[:200]}")

    raise TranslateError("unreachable")  # pragma: no cover
