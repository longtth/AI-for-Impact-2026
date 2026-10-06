"""Tạo đơn nạp tiền và xử lý webhook payOS."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from agent import promotions
from common.store import Order

if TYPE_CHECKING:
    from agent.tools import Ctx

log = logging.getLogger(__name__)


def create_order(ctx: Ctx, order_code: int, amount_vnd: int, promo_code: str | None) -> None:
    ctx.store.create_order(Order(order_code, ctx.user_id, amount_vnd, promo_code, "PENDING"))
    log.info("Tạo đơn nạp %s: %s VND, user=%s", order_code, amount_vnd, ctx.user_id)


def handle_webhook(ctx: Ctx, payload: dict[str, Any]) -> dict[str, Any]:
    """Nhận webhook payOS: kiểm tra chữ ký rồi cộng coin cho đơn tương ứng."""
    if not ctx.payos.verify_webhook(payload):
        log.warning("Webhook sai chữ ký, từ chối")
        return {"ok": False, "error": "invalid signature"}
    order = ctx.store.get_order(int(payload["data"]["orderCode"]))
    if order is None:
        return {"ok": False, "error": "unknown order"}
    coins = order.amount_vnd // ctx.vnd_per_coin
    promo = promotions.find_promotion(order.promo_code, ctx.today)
    bonus = int(promo["bonus_coin"]) if promo else 0
    ctx.store.add_txn(order.user_id, "topup", coins + bonus, f"order {order.order_code}")
    ctx.store.set_order_status(order.order_code, "PAID")
    log.info("Đã cộng %s coin (bonus %s) cho order %s", coins + bonus, bonus, order.order_code)
    return {"ok": True, "credited": coins + bonus}
