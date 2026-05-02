import pytest
import tomllib

from translator.config import ConfigError, load


def test_missing_file(tmp_path):
    p = tmp_path / "noexist.toml"
    with pytest.raises(ConfigError, match="not found"):
        load(p)


def test_missing_api_key(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('model = "x"\n')
    with pytest.raises(ConfigError, match="api_key"):
        load(p)


def test_empty_api_key(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('api_key = ""\n')
    with pytest.raises(ConfigError, match="api_key"):
        load(p)


def test_defaults(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text('api_key = "k"\n')
    cfg = load(p)
    assert cfg["api_key"] == "k"
    assert cfg["model"] == "MiniMax-M2.5-highspeed"
    assert cfg["endpoint"] == "https://api.minimaxi.com/anthropic/v1/messages"


def test_overrides(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(
        'api_key = "k"\n'
        'model = "MiniMax-Text-01"\n'
        'endpoint = "https://x.test"\n'
    )
    cfg = load(p)
    assert cfg["model"] == "MiniMax-Text-01"
    assert cfg["endpoint"] == "https://x.test"


def test_malformed_toml(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text("api_key = unclosed")
    with pytest.raises(tomllib.TOMLDecodeError):
        load(p)
