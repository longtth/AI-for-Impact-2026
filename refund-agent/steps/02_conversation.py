"""Bước 2: system prompt và hội thoại nhiều lượt.

Điểm cần thấy: LLM KHÔNG nhớ gì. Mỗi lần gọi ta gửi lại TOÀN BỘ lịch sử.

Chạy: uv run python steps/02_conversation.py
"""

import anthropic
import truststore

truststore.inject_into_ssl()

MODEL = "claude-sonnet-5-5"
SYSTEM = (
    "Bạn là trợ lý chăm sóc khách hàng của cửa hàng online. "
    "Trả lời tiếng Việt, lịch sự, ngắn gọn. Chưa có công cụ nào, nên đừng giả vờ tra cứu đơn."
)

# SYSTEM = ("")

client = anthropic.Anthropic()
history: list[anthropic.types.MessageParam] = []


def say(user_text: str) -> str:
    history.append({"role": "user", "content": user_text})
    response = client.messages.create(model=MODEL, max_tokens=300, system=SYSTEM, messages=history)
    # print("".join(block.text for block in response.content if block.type == "text"))

    answer = "".join(block.text for block in response.content if block.type == "text")
    history.append({"role": "assistant", "content": answer})
    print(f"Khách: {user_text}\nBot  : {answer}\n(lịch sử hiện có {len(history)} message)\n")
    return answer


say("Tôi muốn hoàn tiền cái tai nghe vừa mua.")
say("Mã đơn của tôi là DH1001.")  # nhờ có lịch sử, bot biết "đơn" này nói về tai nghe
