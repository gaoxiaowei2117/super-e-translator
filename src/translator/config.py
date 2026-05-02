import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "translator" / "config.toml"

DEFAULT_MODEL = "MiniMax-M2.5-highspeed"
DEFAULT_ENDPOINT = "https://api.minimaxi.com/anthropic/v1/messages"


class ConfigError(Exception):
    pass


def load(path: Path = CONFIG_PATH) -> dict:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    data = tomllib.loads(path.read_text())
    api_key = data.get("api_key", "").strip()
    if not api_key:
        raise ConfigError(f"api_key not set in {path}")
    return {
        "api_key": api_key,
        "model": data.get("model", DEFAULT_MODEL),
        "endpoint": data.get("endpoint", DEFAULT_ENDPOINT),
    }
