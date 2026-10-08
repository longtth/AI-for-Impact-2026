"""CLI: `refund-agent-ollama [--dev] init` và `refund-agent-ollama [--dev] run "<yêu cầu>"`."""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from typing import cast

from refund_agent.agent import ChatClient, run_agent
from refund_agent.config import EXAMPLE_CONFIG, config_path, load_config, log_dir
from refund_agent.logger import setup_logging
from refund_agent.shop import Shop
from refund_agent.tools import ToolExecutor

logger = logging.getLogger("refund_agent.cli")


def cmd_init(dev: bool) -> int:
    target = config_path(dev)
    if target.exists():
        print(f"Cảnh báo: config đã tồn tại, không ghi đè: {target}")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(EXAMPLE_CONFIG, target)
    print(f"Đã tạo config: {target}")
    return 0


def ask_human(question: str) -> bool:
    """Human-in-the-loop trên terminal."""
    answer = input(f"\n[CẦN DUYỆT] {question} [y/N]: ")
    return answer.strip().lower() in {"y", "yes", "c", "có"}


def cmd_run(dev: bool, message: str) -> int:
    log_file = setup_logging(log_dir(dev))
    path = config_path(dev)
    if not path.exists():
        logger.error(
            "Không thấy config: %s. Hãy chạy `refund-agent-ollama%s init` trước.",
            path,
            " --dev" if dev else "",
        )
        return 1
    config = load_config(path)
    logger.info("Đã nạp config từ file: %s (log ghi tại %s)", path, log_file)

    import ollama  # import trễ để `init` chạy được khi chưa cài/chạy Ollama

    client = ollama.Client(host=config.host)
    shop = Shop()
    executor = ToolExecutor(shop, config.approval_threshold_vnd, ask_human)
    logger.info("Yêu cầu của khách: %s (model %s @ %s)", message, config.model, config.host)

    try:
        result = run_agent(
            cast(ChatClient, client),  # ollama.Client khớp giao diện chat(**kwargs)
            executor,
            message,
            model=config.model,
            max_tokens=config.max_tokens,
            max_steps=config.max_steps,
            num_ctx=config.num_ctx,
        )
    except ConnectionError:
        logger.error(
            "Không kết nối được Ollama tại %s. Đã cài và chạy `ollama serve` chưa?", config.host
        )
        return 1
    except ollama.ResponseError as exc:
        hint = f" Hãy chạy `ollama pull {config.model}`." if exc.status_code == 404 else ""
        logger.error("Ollama báo lỗi (%s): %s.%s", exc.status_code, exc.error, hint)
        return 1

    logger.info(
        "Kết thúc: %d bước, %d token vào, %d token ra, hoàn thành=%s",
        result.steps,
        result.input_tokens,
        result.output_tokens,
        result.finished,
    )
    print(f"\n{result.text}")
    return 0 if result.finished else 2


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="refund-agent-ollama", description="Agent xử lý hoàn tiền (Ollama)"
    )
    parser.add_argument("--dev", action="store_true", help="đọc/ghi config và log ở .local/")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="tạo config mặc định")
    run_p = sub.add_parser("run", help="xử lý một yêu cầu hoàn tiền")
    run_p.add_argument("message", nargs="+", help="nội dung yêu cầu của khách")
    args = parser.parse_args(argv)

    if args.command == "init":
        return cmd_init(args.dev)
    return cmd_run(args.dev, " ".join(args.message))


if __name__ == "__main__":
    raise SystemExit(main())
