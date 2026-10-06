"""CLI: `init` tạo config, `chat` trò chuyện với RPS Coin Bot. Dùng --dev để chạy dưới .local/."""

from __future__ import annotations

import argparse
import logging
import random
from datetime import date
from typing import Any

import truststore
from dotenv import load_dotenv

from agent import payments
from agent.agent import ClaudeLLM, run_turn
from agent.tools import Ctx
from common import config
from common.logger import setup_logging
from common.payos_client import PayOSClient
from common.store import Store

log = logging.getLogger("agent.cli")


def build_ctx(cfg: dict[str, Any], store: Store, user_id: str, approver: Any = None) -> Ctx:
    today_cfg = cfg.get("agent", {}).get("today")
    ctx = Ctx(
        user_id=user_id,
        store=store,
        payos=PayOSClient(cfg.get("payos", {}).get("mode", "mock")),
        today=date.fromisoformat(today_cfg) if today_cfg else date.today(),
        vnd_per_coin=cfg.get("wallet", {}).get("vnd_per_coin", 1000),
        approval_threshold=cfg.get("wallet", {}).get("approval_threshold_coin", 500),
        rng=random.Random(),
    )
    if approver:
        ctx.approver = approver
    return ctx


def ask_user(name: str, args: dict[str, Any]) -> bool:
    return input(f"[XÁC NHẬN] {name} {args} — đồng ý? (y/n): ").strip().lower() == "y"


def cmd_chat(args: argparse.Namespace) -> None:
    cfg = config.load_config(args.dev)
    db_file = config.db_path(args.dev)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    store = Store(str(db_file))
    store.seed()
    ctx = build_ctx(cfg, store, args.user, ask_user)
    llm = ClaudeLLM(cfg["llm"]["model"], cfg["llm"].get("max_tokens", 1024))
    history: list[dict[str, Any]] = []
    print(f"RPS Coin Bot (user={args.user}).")
    print("Gõ /pay <order_code> để giả lập webhook, /quit để thoát.")
    while True:
        line = input("> ").strip()
        if line in ("/quit", "/exit"):
            break
        if line.startswith("/pay "):
            order = store.get_order(int(line.split()[1]))
            if order:
                payload = ctx.payos.build_webhook(order.order_code, order.amount_vnd)
                print(payments.handle_webhook(ctx, payload))
            continue
        if line:
            print(run_turn(llm, ctx, history, line, cfg["llm"].get("max_turns", 8)).text)


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent.cli", description="RPS Coin Bot")
    parser.add_argument("--dev", action="store_true", help="dùng .local/ thay cho %%APPDATA%%")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="tạo config.toml từ config.example.toml")
    chat = sub.add_parser("chat", help="chat với bot")
    chat.add_argument("--user", default="alice")
    args = parser.parse_args()

    truststore.inject_into_ssl()
    load_dotenv()
    setup_logging(config.log_dir(args.dev))
    if args.command == "init":
        print(f"Config: {config.init_config(args.dev)}")
    else:
        cmd_chat(args)


if __name__ == "__main__":
    main()
