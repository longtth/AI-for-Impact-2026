"""Bước 1: gọi LLM một lần. Đây là "hello world" thật sự.

Chạy: uv run python steps/01_hello_llm.py
Cần biến môi trường ANTHROPIC_API_KEY.
"""

import anthropic
import truststore

truststore.inject_into_ssl()  # tin CA của hệ điều hành (hữu ích sau proxy công ty)

MODEL = "claude-sonnet-5-5"

client = anthropic.Anthropic()  # tự đọc ANTHROPIC_API_KEY từ môi trường

response = client.messages.create(
    model=MODEL,
    max_tokens=300,
    messages=[{"role": "user", "content": "Chính sách hoàn tiền thường gồm những ý chính nào?"}],
)

print(response.content[0].text)  # type: ignore[union-attr]
print("---")
print("stop_reason:", response.stop_reason)
print("token vào/ra:", response.usage.input_tokens, "/", response.usage.output_tokens)
