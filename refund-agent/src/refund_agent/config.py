"""Đường dẫn và nạp cấu hình. Chế độ prod và --dev khác nhau ở thư mục gốc dữ liệu."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "refund-agent"
EXAMPLE_CONFIG = Path(__file__).parent / "config.example.toml"
SOURCE_ROOT = Path(__file__).resolve().parents[2]  # thư mục chứa pyproject.toml


def app_dir(dev: bool) -> Path:
    """Thư mục chứa config + log của một chế độ chạy.

    - prod: %APPDATA%\\refund-agent (Windows) hoặc ~/refund-agent (Linux)
    - dev : <source root>/.local
    """
    if dev:
        return SOURCE_ROOT / ".local"
    appdata = os.environ.get("APPDATA")
    return Path(appdata) / APP_NAME if appdata else Path.home() / APP_NAME


def config_path(dev: bool) -> Path:
    return app_dir(dev) / "config.toml"


def log_dir(dev: bool) -> Path:
    return app_dir(dev) / ".log"


@dataclass(frozen=True)
class Config:
    model: str
    max_tokens: int
    max_steps: int
    approval_threshold_vnd: int


def load_config(path: Path) -> Config:
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return Config(
        model=str(raw["model"]),
        max_tokens=int(raw["max_tokens"]),
        max_steps=int(raw["max_steps"]),
        approval_threshold_vnd=int(raw["approval_threshold_vnd"]),
    )
