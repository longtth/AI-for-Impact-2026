"""Client giả lập: phát lại một kịch bản các phản hồi của LLM, không cần API key."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any


def text(t: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=t)


def tool_use(id_: str, name: str, **inp: Any) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=id_, name=name, input=inp)


def reply(*blocks: SimpleNamespace, stop: str | None = None) -> SimpleNamespace:
    has_tool = any(b.type == "tool_use" for b in blocks)
    return SimpleNamespace(
        content=list(blocks),
        stop_reason=stop or ("tool_use" if has_tool else "end_turn"),
        usage=SimpleNamespace(input_tokens=100, output_tokens=20),
    )


class FakeMessages:
    def __init__(self, script: list[SimpleNamespace]) -> None:
        self.script = list(script)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.script.pop(0)
