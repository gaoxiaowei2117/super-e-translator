"""MiniMax client.

Two endpoints in use:

- Text translation: Anthropic-compatible Messages API at
  /anthropic/v1/messages. Response `content` is a list of blocks; we keep
  only type=="text" blocks and drop type=="thinking" (M2 reasoning chain).
- Image translation: coding-plan VLM endpoint at /v1/coding_plan/vlm.
  Request takes a base64 data URL image; response uses the older
  base_resp envelope with `content` as a plain string.
"""
import base64

import httpx

VLM_ENDPOINT = "https://api.minimaxi.com/v1/coding_plan/vlm"

VLM_PROMPT_EN_TO_ZH = (
    "Translate all English text in this image to Simplified Chinese. "
    "Output only the translation as continuous text, preserving paragraph "
    "structure. If no English text is found, output exactly: [未检测到英文]"
)

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

DICTIONARY_PROMPT = (
    "Look up the English word and produce a compact dictionary entry in this "
    "exact format:\n"
    "/<IPA>/\n"
    "<POS>. <meaning>；<meaning>；...\n"
    "<POS>. <meaning>；<meaning>；...\n"
    "\n"
    "Rules:\n"
    "- Use standard POS abbreviations: n., v., adj., adv., prep., conj., int., "
    "pron., det.\n"
    "- One line per POS, most common first.\n"
    "- Separate Chinese meanings with full-width semicolons (；).\n"
    "- IPA must be enclosed in slashes.\n"
    "- Output ONLY the entry — no markdown, no preamble, no explanation.\n"
    "- If the word is not a valid English word, output exactly: [未找到该单词]"
)


class TranslateError(Exception):
    pass


def _anthropic_chat(
    system: str,
    user_text: str,
    *,
    api_key: str,
    model: str,
    endpoint: str,
    timeout: float,
) -> str:
    """POST to MiniMax Anthropic-compatible Messages API, return the text reply.

    Concatenates all `type=="text"` blocks from `content`; drops `thinking`.
    Retries once on 5xx. Raises TranslateError on any failure.
    """
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": system,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": user_text}]}
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


def translate(
    text: str,
    direction: str,
    *,
    api_key: str,
    model: str,
    endpoint: str,
    timeout: float = 30.0,
) -> str:
    return _anthropic_chat(
        PROMPTS[direction], text,
        api_key=api_key, model=model, endpoint=endpoint, timeout=timeout,
    )


def lookup_word(
    word: str,
    *,
    api_key: str,
    model: str,
    endpoint: str,
    timeout: float = 30.0,
) -> str:
    """Look up an English word; return formatted dict entry (IPA + POS lines)."""
    return _anthropic_chat(
        DICTIONARY_PROMPT, word,
        api_key=api_key, model=model, endpoint=endpoint, timeout=timeout,
    )


def translate_image(
    png_bytes: bytes,
    *,
    api_key: str,
    prompt: str = VLM_PROMPT_EN_TO_ZH,
    endpoint: str = VLM_ENDPOINT,
    timeout: float = 60.0,
) -> str:
    """Send a PNG image to MiniMax VLM and return the model's text reply."""
    data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    payload = {"prompt": prompt, "image_url": data_url}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "MM-API-Source": "Minimax-MCP",
        "Content-Type": "application/json",
    }

    try:
        r = httpx.post(endpoint, json=payload, headers=headers, timeout=timeout)
    except httpx.RequestError as e:
        raise TranslateError(f"网络错误: {e}") from e

    if r.status_code >= 400:
        raise TranslateError(f"HTTP {r.status_code}: {r.text[:200]}")

    try:
        body = r.json()
    except ValueError as e:
        raise TranslateError(f"响应解析失败: {r.text[:200]}") from e

    base_resp = body.get("base_resp") or {}
    err_code = base_resp.get("status_code")
    if err_code not in (0, None):
        raise TranslateError(
            f"MiniMax 错误 {err_code}: {base_resp.get('status_msg', '')}"
        )

    content = (body.get("content") or "").strip()
    if not content:
        raise TranslateError(f"响应中无 content: {str(body)[:200]}")
    return content
