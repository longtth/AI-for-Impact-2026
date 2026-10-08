"""Bước 1: gọi LLM một lần. Đây là "hello world" thật sự.

Chạy: uv run python steps/01_hello_llm.py
Cần biến môi trường ANTHROPIC_API_KEY.
"""

import os

import anthropic
import truststore

truststore.inject_into_ssl()  # tin CA của hệ điều hành (hữu ích sau proxy công ty)

MODEL = "claude-sonnet-5-5"

# .strip() vì key copy/paste hay dính "\n" ở cuối -> "Illegal header value"
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())

response = client.messages.create(
    model=MODEL,
    max_tokens=2000,  # chừa chỗ cho phần thinking, nếu không có thể không còn token cho text
    messages=[{"role": "user", "content": "Chính sách hoàn tiền thường gồm những ý chính nào?"}],
)

# content có thể chứa ThinkingBlock trước TextBlock -> chỉ lấy các khối text
print("".join(block.text for block in response.content if block.type == "text"))
print("---")
print("stop_reason:", response.stop_reason)
print("token vào/ra:", response.usage.input_tokens, "/", response.usage.output_tokens)
