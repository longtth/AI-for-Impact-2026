"""Vòng lặp agent: prompt -> model -> tool_use -> tool_result -> ... -> câu trả lời."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

from agent.tools import TOOLS, Ctx, coin_value, execute_tool

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là RPS Coin Bot, trợ lý của app oẳn tù tì ăn coin.
Hôm nay là {today}. Người chơi hiện tại: {user_id}.
Luật: 1.000 VND = 1 coin. Thắng ván nhận thêm số coin đã cược, thua mất số đã cược.
Luôn dùng tool để lấy số liệu thật, không tự bịa số dư hay kết quả. Trả lời ngắn gọn, thân thiện."""


class LLM(Protocol):
    def complete(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Trả về các block: {"type":"text","text"} hoặc {"type":"tool_use","id","name","input"}."""
        ...


class ClaudeLLM:
    def __init__(self, model: str, max_tokens: int = 1024) -> None:
        import anthropic

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("Thiếu ANTHROPIC_API_KEY (xem .env.example)")
        self.client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens

    def complete(
        self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=messages,  # type: ignore[arg-type]
            tools=tools,  # type: ignore[arg-type]
        )
        log.info("usage in=%s out=%s", resp.usage.input_tokens, resp.usage.output_tokens)
        blocks: list[dict[str, Any]] = []
        for b in resp.content:
            if b.type == "text":
                blocks.append({"type": "text", "text": b.text})
            elif b.type == "tool_use":
                blocks.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
        return blocks


@dataclass
class TurnResult:
    text: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


def needs_approval(name: str, args: dict[str, Any], ctx: Ctx) -> bool:
    """Hành động nào phải được người chơi xác nhận trước khi thực hiện."""
    return False


def run_turn(
    llm: LLM,
    ctx: Ctx,
    history: list[dict[str, Any]],
    user_message: str,
    max_turns: int = 8,
) -> TurnResult:
    """Xử lý một lượt chat của người chơi; `history` được cập nhật tại chỗ."""
    system = SYSTEM_PROMPT.format(today=ctx.today.isoformat(), user_id=ctx.user_id)
    history.append({"role": "user", "content": user_message})
    result = TurnResult(text="")
    for _ in range(max_turns):
        blocks = llm.complete(system, history, TOOLS)
        history.append({"role": "assistant", "content": blocks})
        tool_uses = [b for b in blocks if b["type"] == "tool_use"]
        if not tool_uses:
            result.text = "\n".join(b["text"] for b in blocks if b["type"] == "text")
            return result
        tool_results: list[dict[str, Any]] = []
        for use in tool_uses:
            name, args = use["name"], use["input"]
            if needs_approval(name, args, ctx) and not ctx.approver(name, args):
                output = '{"error": "Người chơi đã từ chối xác nhận"}'
            else:
                output = execute_tool(name, args, ctx)
            log.info("tool %s(%s) -> %s", name, args, output)
            result.tool_calls.append({"name": name, "input": args, "output": output})
            tool_results.append(
                {"type": "tool_result", "tool_use_id": use["id"], "content": output}
            )
        history.append({"role": "user", "content": tool_results})
    result.text = "(Dừng: vượt quá số vòng tool tối đa)"
    return result


__all__ = ["LLM", "ClaudeLLM", "TurnResult", "needs_approval", "run_turn", "coin_value"]
