from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from naver_land_watcher.models import AppConfig, ComplexConfig


class ConfigError(ValueError):
    pass


def load_config(config_path: str) -> AppConfig:
    load_dotenv()
    raw = _read_yaml(config_path)
    complexes = [ComplexConfig(**item) for item in raw.get("complexes", [])]
    if not complexes:
        raise ConfigError("At least one complex config is required.")

    return AppConfig(
        complexes=complexes,
        poll_interval_seconds=int(raw.get("poll_interval_seconds", 120)),
        jitter_seconds=int(raw.get("jitter_seconds", 20)),
        request_timeout_seconds=int(raw.get("request_timeout_seconds", 10)),
        max_retries=int(raw.get("max_retries", 4)),
        backoff_base_seconds=float(raw.get("backoff_base_seconds", 1.5)),
        detect_updates=bool(raw.get("detect_updates", True)),
        database_path=str(raw.get("database_path", "./watcher.db")),
        user_agent=str(raw.get("user_agent", "Mozilla/5.0")),
    )


def _read_yaml(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError("Config file must be a YAML mapping.")
    return data


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value
