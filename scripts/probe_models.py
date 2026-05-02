"""Probe which MiniMax models the configured API key has access to."""
import sys

import httpx

from translator import config

CANDIDATES = [
    "MiniMax-Text-01",
    "abab6.5-chat",
    "abab6.5s-chat",
    "abab6.5t-chat",
    "abab6.5g-chat",
    "abab6-chat",
    "abab5.5-chat",
    "abab5.5s-chat",
]


def probe(model: str, *, api_key: str, endpoint: str) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 4,
    }
    r = httpx.post(
        endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10,
    )
    if r.status_code >= 400:
        return f"HTTP {r.status_code}"
    base = (r.json().get("base_resp") or {})
    code = base.get("status_code")
    if code in (0, None):
        return "OK"
    return f"{code} {base.get('status_msg', '')}"


def main() -> int:
    cfg = config.load()
    print(f"endpoint: {cfg['endpoint']}")
    print(f"key: {cfg['api_key'][:8]}…\n")
    for m in CANDIDATES:
        try:
            result = probe(m, api_key=cfg["api_key"], endpoint=cfg["endpoint"])
        except httpx.RequestError as e:
            result = f"network: {e}"
        marker = "✅" if result == "OK" else "❌"
        print(f"{marker} {m:<22} {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
