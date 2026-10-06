# Dành cho giảng viên — KHÔNG phát cho sinh viên

Thư mục này (và `instructor/hidden/`, đã gitignore) chứa đáp án và hidden tests. Khi phát repo cho sinh viên,
dùng bản đã xóa `instructor/`.

## Đáp án Buổi 1
`instructor/solution/agent/` chứa bản `agent.py`, `promotions.py`, `tools.py` đã sửa. Kết quả đã kiểm chứng:
- Baseline: **4/14 = 28.6%**.
- Bản đáp án: **14/14 = 100%**. Ngưỡng +15 điểm phần trăm = đạt ít nhất 7/14 (50%), tức sửa thêm tối thiểu 3 case — chỉ cần xong trọn một lỗi nhóm `approval` hoặc `promotion` là đủ.

Xem khác biệt: `git diff --no-index agent instructor/solution/agent`.

| Lỗi | Sửa |
|---|---|
| Approval gate | `needs_approval` → `coin_value(name, args, ctx) >= ctx.approval_threshold` |
| Khuyến mãi hết hạn | Lọc theo `valid_from <= today <= valid_to` trong `list_promotions`; `find_promotion` dùng lại hàm đó |
| Tool schema | `enum` cho `move`, `integer` + `minimum` cho `bet`, mô tả rõ; `jsonschema.validate` trong `execute_tool` |

## Điểm yếu cố ý cho Buổi 2 (không có trong public tests)
- `handle_webhook` không idempotent: gửi lặp cộng coin nhiều lần.
- `refund` không kiểm tra quyền admin và cho hoàn giao dịch của người khác.
- `play_rps`/`top_up` chưa xử lý timeout/retry; log chưa che PII.
- Prompt injection: system prompt không có phòng thủ nào; chưa có case JSON hỗ trợ lượt chat nhiều bước từ
  tool result độc hại (có thể mở rộng định dạng case nếu cần).

## Hidden tests
`instructor/hidden/cases_hidden.json` (6 case): `uv run python -m evaluator.runner --dev --cases instructor\hidden\cases_hidden.json`.
Bản baseline đạt 2/6; bản đáp án Buổi 1 cần đạt 6/6 (nếu không, đáp án thiếu xử lý biên — ví dụ mã viết thường).

## Việc ban tổ chức cần chuẩn bị cho Buổi 3
- Đề mock run (repo rút gọn có lỗi mới), hệ thống nhận bài và bảng điểm, hướng dẫn nộp bài.
- Nền tảng hosting miễn phí, ngân sách/API key Claude cho từng đội, quy trình cấp tài khoản payOS (nếu dùng live).
