"""Khuyến mãi nạp coin, đọc từ data/promotions.json."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from common.config import ROOT

PROMOTIONS_FILE = ROOT / "data" / "promotions.json"


def load_promotions() -> list[dict[str, Any]]:
    return list(json.loads(PROMOTIONS_FILE.read_text(encoding="utf-8")))


def list_promotions(today: date) -> list[dict[str, Any]]:
    """Danh sách khuyến mãi trả cho người chơi."""
    return [p for p in load_promotions() if _is_active(p, today)]


def _is_active(promo: dict[str, Any], today: date) -> bool:
    return date.fromisoformat(promo["valid_from"]) <= today <= date.fromisoformat(promo["valid_to"])


def find_promotion(code: str | None, today: date) -> dict[str, Any] | None:
    """Tìm khuyến mãi theo mã để cộng bonus coin khi nạp tiền."""
    if not code:
        return None
    return next((p for p in list_promotions(today) if p["code"] == code.upper()), None)
