"""Các tool của RPS Coin Bot: schema gửi cho model + hàm thực thi."""

from __future__ import annotations

import json
import logging
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from agent import payments, promotions
from common.payos_client import PayOSClient
from common.store import Store

log = logging.getLogger(__name__)

REWARDS = {"sticker": 20, "ao_thun": 300, "voucher_tra_sua": 600}
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


@dataclass
class Ctx:
    """Ngữ cảnh một phiên: ai đang chat, ví, cổng thanh toán, ngày hiện tại."""

    user_id: str
    store: Store
    payos: PayOSClient
    today: date
    vnd_per_coin: int = 1000
    approval_threshold: int = 500
    approver: Callable[[str, dict[str, Any]], bool] = lambda name, args: True
    rng: random.Random = field(default_factory=random.Random)


TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_balance",
        "description": "Xem số dư coin của người chơi hiện tại.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "top_up",
        "description": "Tạo link thanh toán payOS để nạp tiền lấy coin (1.000 VND = 1 coin).",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount_vnd": {"type": "integer", "description": "Số tiền VND, bội số của 1000"},
                "promo_code": {"type": "string", "description": "Mã khuyến mãi (nếu có)"},
            },
            "required": ["amount_vnd"],
        },
    },
    {
        "name": "play_rps",
        "description": "play",
        "input_schema": {
            "type": "object",
            "properties": {"move": {"type": "string"}, "bet": {"type": "string"}},
            "required": ["move", "bet"],
        },
    },
    {
        "name": "get_promotions",
        "description": "Liệt kê các khuyến mãi nạp tiền.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "redeem_reward",
        "description": "Đổi coin lấy quà: sticker (20), ao_thun (300), voucher_tra_sua (600).",
        "input_schema": {
            "type": "object",
            "properties": {"item": {"type": "string"}},
            "required": ["item"],
        },
    },
    {
        "name": "get_history",
        "description": "Xem lịch sử giao dịch coin của người chơi hiện tại.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "refund",
        "description": "Hoàn tác một giao dịch theo txn_id.",
        "input_schema": {
            "type": "object",
            "properties": {"txn_id": {"type": "integer"}},
            "required": ["txn_id"],
        },
    },
]


def _get_balance(args: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    return {"balance": ctx.store.balance(ctx.user_id)}


def _top_up(args: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    amount = int(args["amount_vnd"])
    order_code = ctx.store.next_order_code()
    link = ctx.payos.create_payment_link(order_code, amount, f"Nap coin {ctx.user_id}")
    payments.create_order(ctx, order_code, amount, args.get("promo_code"))
    return {"order_code": order_code, "checkout_url": link["data"]["checkoutUrl"]}


def _play_rps(args: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    move, bet = args["move"], int(args["bet"])
    if bet > ctx.store.balance(ctx.user_id):
        return {"error": "Số dư không đủ"}
    opponent = ctx.rng.choice(sorted(BEATS))
    if move == opponent:
        outcome, delta = "draw", 0
    elif BEATS[move] == opponent:
        outcome, delta = "win", bet
    else:
        outcome, delta = "lose", -bet
    ctx.store.add_txn(ctx.user_id, "play", delta, f"{move} vs {opponent}: {outcome}")
    return {"opponent": opponent, "outcome": outcome, "delta": delta,
            "balance": ctx.store.balance(ctx.user_id)}


def _get_promotions(args: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    return {"promotions": promotions.list_promotions(ctx.today)}


def _redeem_reward(args: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    item = args["item"]
    price = REWARDS.get(item)
    if price is None:
        return {"error": f"Không có quà {item}"}
    if price > ctx.store.balance(ctx.user_id):
        return {"error": "Số dư không đủ"}
    ctx.store.add_txn(ctx.user_id, "redeem", -price, item)
    return {"redeemed": item, "balance": ctx.store.balance(ctx.user_id)}


def _get_history(args: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    return {"history": ctx.store.txns(ctx.user_id)}


def _refund(args: dict[str, Any], ctx: Ctx) -> dict[str, Any]:
    txn_id = int(args["txn_id"])
    txn = next((t for t in ctx.store.txns() if t["id"] == txn_id), None)
    if txn is None:
        return {"error": f"Không có giao dịch {txn_id}"}
    ctx.store.add_txn(txn["user_id"], "refund", -txn["delta"], f"hoàn giao dịch {txn_id}")
    return {"refunded": txn_id}


HANDLERS: dict[str, Callable[[dict[str, Any], Ctx], dict[str, Any]]] = {
    "get_balance": _get_balance,
    "top_up": _top_up,
    "play_rps": _play_rps,
    "get_promotions": _get_promotions,
    "redeem_reward": _redeem_reward,
    "get_history": _get_history,
    "refund": _refund,
}


def coin_value(name: str, args: dict[str, Any], ctx: Ctx) -> int:
    """Giá trị giao dịch quy ra coin, dùng để quyết định có cần xác nhận hay không."""
    try:
        if name == "play_rps":
            return abs(int(args["bet"]))
        if name == "top_up":
            return int(args["amount_vnd"]) // ctx.vnd_per_coin
        if name == "redeem_reward":
            return REWARDS.get(args["item"], 0)
        if name == "refund":
            txn_id = int(args["txn_id"])
            return next((abs(t["delta"]) for t in ctx.store.txns() if t["id"] == txn_id), 0)
    except (KeyError, TypeError, ValueError):
        return 0
    return 0


def execute_tool(name: str, args: dict[str, Any], ctx: Ctx) -> str:
    """Chạy tool, trả kết quả dạng JSON string để đưa lại cho model."""
    handler = HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"Tool không tồn tại: {name}"})
    result = handler(args, ctx)
    return json.dumps(result, ensure_ascii=False)
