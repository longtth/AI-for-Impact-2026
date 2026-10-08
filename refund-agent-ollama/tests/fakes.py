"""Client giả lập: phát lại một kịch bản các phản hồi của Ollama, không cần chạy server."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any


def tool_call(name: str, **args: Any) -> SimpleNamespace:
    return SimpleNamespace(function=SimpleNamespace(name=name, arguments=args))


def reply(text: str = "", *calls: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(
        message=SimpleNamespace(role="assistant", content=text, tool_calls=list(calls) or None),
        done_reason="stop",
        prompt_eval_count=100,
        eval_count=20,
    )


class FakeOllama:
    def __init__(self, script: list[SimpleNamespace]) -> None:
        self.script = list(script)
        self.calls: list[dict[str, Any]] = []

    def chat(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.script.pop(0)
