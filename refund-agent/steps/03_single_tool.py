"""Bước 3: một tool, gọi thủ công MỘT lần (chưa có vòng lặp).

Điểm cần thấy:
  1. LLM không tự chạy tool, nó trả về một yêu cầu (block `tool_use`).
  2. Code của ta chạy hàm, rồi gửi kết quả lại bằng block `tool_result`.

Chạy: uv run python steps/03_single_tool.py
"""

import json
from typing import cast

import anthropic
import truststore

from refund_agent.shop import Shop

truststore.inject_into_ssl()

MODEL = "claude-sonnet-5-5"
shop = Shop()

GET_ORDER_TOOL: anthropic.types.ToolParam = {
    "name": "get_order",
    "description": "Tra cứu đơn hàng theo mã đơn và email đặt hàng.",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "customer_email": {"type": "string"},
        },
        "required": ["order_id", "customer_email"],
    },
}

client = anthropic.Anthropic()
messages: list[anthropic.types.MessageParam] = [
    {"role": "user", "content": "Đơn DH1001 của tôi (an@example.com) giao chưa?"}
]

# Lần gọi 1: LLM thấy tool và quyết định dùng nó.
first = client.messages.create(
    model=MODEL, max_tokens=500, tools=[GET_ORDER_TOOL], messages=messages
)
print("stop_reason lần 1:", first.stop_reason)  # -> "tool_use"

tool_call = next(b for b in first.content if b.type == "tool_use")
print("LLM đề xuất gọi:", tool_call.name, tool_call.input)

# Code CỦA TA chạy tool thật.
args = cast(dict[str, str], tool_call.input)
order = shop.find_order(args["order_id"], args["customer_email"])
result = {"status": order.status, "item": order.item} if order else {"error": "không tìm thấy"}
print("Kết quả tool:", result)

# Lần gọi 2: gửi lại lịch sử + kết quả tool để LLM viết câu trả lời cuối.
messages.append({"role": "assistant", "content": first.content})
messages.append(
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            }
        ],
    }
)
second = client.messages.create(
    model=MODEL, max_tokens=500, tools=[GET_ORDER_TOOL], messages=messages
)
print("stop_reason lần 2:", second.stop_reason)  # -> "end_turn"
print(second.content[0].text)  # type: ignore[union-attr]
