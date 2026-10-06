"""Evaluator: chạy test case qua agent thật và chấm theo TRẠNG THÁI (ví, đơn, kết quả tool).

Mặc định dùng model giả lập có kịch bản (`scripted`): miễn phí, lặp lại được, chỉ kiểm tra
harness (approval gate, lọc khuyến mãi, validate schema). `--llm claude` cho model thật tự
quyết định tool call từ trường `prompt`.
"""

from __future__ import annotations

import argparse
import itertools
import json
import logging
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

import truststore
from dotenv import load_dotenv

from agent import payments
from agent.agent import LLM, ClaudeLLM, run_turn
from agent.cli import build_ctx
from agent.tools import TOOLS
from common import config
from common.logger import setup_logging
from common.store import Store

log = logging.getLogger("evaluator")
DEFAULT_CASES = Path(__file__).parent / "cases_public.json"
USER = "alice"
START_BALANCE = 5000


class ScriptedLLM:
    """Model giả: lần lượt phát ra các tool call trong `script`, rồi trả lời kết thúc."""

    def __init__(self, script: list[dict[str, Any]]) -> None:
        self.calls = list(script)
        self.ids = itertools.count(1)

    def complete(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not self.calls:
            return [{"type": "text", "text": "Xong."}]
        call = self.calls.pop(0)
        return [
            {
                "type": "tool_use",
                "id": f"toolu_{next(self.ids)}",
                "name": call["name"],
                "input": call["input"],
            }
        ]


def check_play_rps_schema() -> list[str]:
    tool = next(t for t in TOOLS if t["name"] == "play_rps")
    props = tool["input_schema"].get("properties", {})
    errors: list[str] = []
    if set(props.get("move", {}).get("enum", [])) != {"rock", "paper", "scissors"}:
        errors.append("move thiếu enum [rock, paper, scissors]")
    bet = props.get("bet", {})
    if bet.get("type") != "integer" or bet.get("minimum", 0) < 1:
        errors.append("bet phải là integer với minimum >= 1")
    if len(tool.get("description", "")) < 20:
        errors.append("description của tool quá ngắn")
    return errors


def evaluate_expect(expect: dict[str, Any], store: Store, outputs: list[str]) -> list[str]:
    errors: list[str] = []
    types = {t["type"] for t in store.txns(USER)}
    joined = "\n".join(outputs)
    if "balance" in expect and store.balance(USER) != expect["balance"]:
        errors.append(f"số dư = {store.balance(USER)}, mong đợi {expect['balance']}")
    if "orders" in expect and len(store.orders()) != expect["orders"]:
        errors.append(f"số đơn = {len(store.orders())}, mong đợi {expect['orders']}")
    for t in expect.get("txn_types_absent", []):
        if t in types:
            errors.append(f"không được có giao dịch loại '{t}'")
    for t in expect.get("txn_types_present", []):
        if t not in types:
            errors.append(f"thiếu giao dịch loại '{t}'")
    for s in expect.get("output_includes", []):
        if s not in joined:
            errors.append(f"kết quả tool phải chứa '{s}'")
    for s in expect.get("output_excludes", []):
        if s in joined:
            errors.append(f"kết quả tool không được chứa '{s}'")
    return errors


def run_case(case: dict[str, Any], cfg: dict[str, Any], llm_mode: str) -> list[str]:
    """Trả về danh sách lỗi; rỗng nghĩa là PASS."""
    if case.get("static_check") == "play_rps_schema":
        return check_play_rps_schema()
    store = Store()
    store.seed({USER: START_BALANCE})
    approve = case.get("approver", "allow") == "allow"
    ctx = build_ctx(cfg, store, USER, lambda name, args: approve)
    ctx.rng = random.Random(0)
    llm: LLM = (
        ScriptedLLM(case["script"])
        if llm_mode == "scripted"
        else ClaudeLLM(cfg["llm"]["model"], cfg["llm"].get("max_tokens", 1024))
    )
    try:
        turn = run_turn(llm, ctx, [], case["prompt"], cfg["llm"].get("max_turns", 8))
        if case.get("pay_orders"):
            for order in store.orders("PENDING"):
                hook = ctx.payos.build_webhook(order.order_code, order.amount_vnd)
                payments.handle_webhook(ctx, hook)
    except Exception as exc:  # crash của agent/tool cũng là lỗi cần chấm
        return [f"crash: {type(exc).__name__}: {exc}"]
    return evaluate_expect(case["expect"], store, [c["output"] for c in turn.tool_calls])


def main() -> None:
    parser = argparse.ArgumentParser(prog="evaluator.runner")
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--llm", choices=["scripted", "claude"], default="scripted")
    parser.add_argument("--json-out", type=Path, help="ghi kết quả chi tiết ra file JSON")
    args = parser.parse_args()

    truststore.inject_into_ssl()
    load_dotenv()
    setup_logging(config.log_dir(args.dev), console=False)
    cfg = config.load_config(args.dev)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    log.info("Chạy %s case từ %s (llm=%s)", len(cases), args.cases, args.llm)

    by_area: dict[str, list[bool]] = defaultdict(list)
    results: list[dict[str, Any]] = []
    for case in cases:
        errors = run_case(case, cfg, args.llm)
        ok = not errors
        by_area[case["area"]].append(ok)
        results.append({"id": case["id"], "area": case["area"], "passed": ok, "errors": errors})
        print(f"[{'PASS' if ok else 'FAIL'}] {case['area']:<10} {case['id']}: {case['title']}")
        for e in errors:
            print(f"         - {e}")

    total = [r["passed"] for r in results]
    print("\nTheo nhóm:")
    for area, flags in by_area.items():
        print(f"  {area:<10} {sum(flags)}/{len(flags)}")
    score = 100 * sum(total) / len(total)
    print(f"\nĐIỂM: {sum(total)}/{len(total)} = {score:.1f}%")
    log.info("Điểm evaluator: %.1f%%", score)
    if args.json_out:
        args.json_out.write_text(
            json.dumps({"score": score, "results": results}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
