# Hello World with AGENT Development

Một bài viết dài hướng dẫn sinh viên có hiểu biết cơ bản về lập trình và phần mềm cách **xây dựng và vận hành một agent đơn giản**. Xuyên suốt bài là một ví dụ thực tế: **agent xử lý yêu cầu hoàn tiền** cho cửa hàng online, viết bằng Python và Claude API, không dùng framework.

## Mục lục

| Phần | Nội dung |
|---|---|
| [1. Khái niệm](01-khai-niem.md) | Phần mềm truyền thống, LLM, chatbot / workflow / agent, các thuật ngữ liên quan |
| [2. Xây agent](02-xay-agent.md) | Từ gọi LLM một lần đến vòng lặp agent hoàn chỉnh, guardrail, config, log |
| [3. Vận hành](03-van-hanh.md) | Log, chi phí, an toàn, kiểm thử và đánh giá, lỗi thường gặp (giới thiệu ngắn) |
| [4. Bước tiếp theo](04-buoc-tiep-theo.md) | Tổng kết, hướng mở rộng, bài tập tổng hợp |

Nên đọc theo thứ tự. Phần 2 có code chạy được trong thư mục `refund-agent/`.

## Chạy nhanh

Cần [uv](https://docs.astral.sh/uv/) và Python 3.11+.

```powershell
cd refund-agent
uv sync
uv run pytest -q            # kiểm tra môi trường, không cần API key, không tốn tiền

$env:ANTHROPIC_API_KEY = "sk-ant-..."   # chỉ đặt trong terminal, không ghi vào file
uv run python steps/01_hello_llm.py     # các bước học: 01 -> 04
uv run refund-agent --dev init          # tạo .local\config.toml
uv run refund-agent --dev run "Tôi muốn hoàn tiền đơn DH1001, email an@example.com"
```

## Cấu trúc thư mục

```
01-khai-niem.md ... 04-buoc-tiep-theo.md   bài viết
refund-agent/
├── steps/     4 script học tăng dần (cần API key)
├── src/       ứng dụng hoàn chỉnh: shop, tools, agent, config, logger, cli
└── tests/     test bằng LLM giả lập (không cần API key)
```
