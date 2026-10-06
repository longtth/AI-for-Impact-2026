"""Nạp cấu hình và quy ước đường dẫn (prod: %APPDATA%\\rpsbot, --dev: .local/)."""

from __future__ import annotations

import logging
import os
import shutil
import tomllib
from pathlib import Path
from typing import Any

APP_NAME = "rpsbot"
ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_CONFIG = ROOT / "config.example.toml"

log = logging.getLogger(__name__)


def app_dir(dev: bool) -> Path:
    """Thư mục chứa config, log, db cho một chế độ chạy."""
    if dev:
        return ROOT / ".local"
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
    return Path.home() / APP_NAME


def config_path(dev: bool) -> Path:
    return app_dir(dev) / "config.toml"


def log_dir(dev: bool) -> Path:
    return app_dir(dev) / ".log"


def db_path(dev: bool) -> Path:
    return app_dir(dev) / "rpsbot.db"


def init_config(dev: bool) -> Path:
    """Copy config.example.toml sang đường dẫn mặc định; không ghi đè nếu đã có."""
    target = config_path(dev)
    if target.exists():
        log.warning("Config đã tồn tại, bỏ qua (không ghi đè): %s", target)
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EXAMPLE_CONFIG, target)
    log.info("Đã tạo config từ %s -> %s", EXAMPLE_CONFIG, target)
    return target


def load_config(dev: bool) -> dict[str, Any]:
    """Đọc config.toml; nếu chưa `init` thì dùng config.example.toml. Luôn log nguồn config."""
    path = config_path(dev)
    if not path.exists():
        path = EXAMPLE_CONFIG
        log.warning("Chưa có config (hãy chạy `init`), tạm dùng file mẫu")
    log.info("Đã nạp config từ file: %s", path)
    with path.open("rb") as f:
        return tomllib.load(f)
