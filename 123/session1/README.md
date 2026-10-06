# Buổi 1 — Hiểu và sửa một AI Agent (3 giờ)

## Mục tiêu
- Giải thích được 5 khái niệm: **Model – Tool – Agent – Harness – Evaluation**.
- Đọc được vòng lặp agent và chỉ ra chỗ harness (không phải model) quyết định hành vi.
- Sửa 3 lỗi trong RPS Coin Bot và chứng minh bằng điểm evaluator.

## Chuẩn bị trước buổi
Đã làm xong phần [Cài đặt](../README.md#cài-đặt-windows-powershell). Kiểm tra: `uv run python -m evaluator.runner --dev`
in ra `ĐIỂM: 4/14 = 28.6%`. Đó là điểm baseline của cả lớp.

## Timeline
| Thời gian | Nội dung |
|---|---|
| 0:00–0:30 | 5 khái niệm nền tảng (xem bên dưới) |
| 0:30–1:00 | Giảng viên chạy baseline, đọc từng dòng PASS/FAIL |
| 1:00–2:00 | Thực hành: sửa 3 lỗi |
| 2:00–2:45 | Chạy lại evaluator, so sánh điểm, mỗi đội trình bày 1 lỗi |
| 2:45–3:00 | Tổng kết |

## 1. Năm khái niệm (30')
| Khái niệm | Trong repo |
|---|---|
| **Model** | Claude — chỉ sinh văn bản/yêu cầu gọi tool (`ClaudeLLM` trong `agent/agent.py`) |
| **Tool** | Hàm thật mà model được phép gọi: `top_up`, `play_rps`... (`agent/tools.py`) |
| **Agent** | Vòng lặp: model → `tool_use` → chạy tool → `tool_result` → model... (`run_turn`) |
| **Harness** | Mọi thứ bao quanh model: schema, validate, xác nhận, log, ví, cổng thanh toán |
| **Evaluation** | Chấm theo *trạng thái thật* (số dư, đơn hàng), không chấm theo câu model nói |

Ý chính: model có thể "muốn" cược 1000 coin hay dùng mã hết hạn — **harness mới là chỗ chặn**. Vì vậy evaluator
mặc định dùng model giả lập có kịch bản: cùng một kịch bản, harness sửa đúng thì điểm tăng.

## 2. Đọc báo cáo baseline (30')
Mỗi dòng: `[PASS|FAIL] nhóm id: mô tả` kèm lý do. 14 case chia 4 nhóm: `basic`, `approval`, `promotion`, `schema`.
Case `FAIL` đọc kỹ dòng `-` bên dưới: nó nói *kết quả thật* khác *kết quả mong đợi* thế nào.

## 3. Thực hành: 3 lỗi (60')
Chia 3 người/đội, mỗi người nhận 1 lỗi rồi ghép lại. Chỉ sửa trong `agent/`.

### Lỗi A — Approval gate (`agent/agent.py`)
Giao dịch từ **500 coin** trở lên (cược, nạp 500.000 VND, đổi quà, hoàn tiền) phải được người chơi xác nhận.
- Gợi ý: hàm `needs_approval` đang luôn trả `False`. `coin_value` (trong `agent/tools.py`) đã quy mọi tool ra coin;
  ngưỡng nằm ở `ctx.approval_threshold`.
- Đừng chặn nhầm: cược 10 coin không được hỏi xác nhận (có case kiểm tra điều này).
- Case liên quan: `approval_*`.

### Lỗi B — Khuyến mãi hết hạn (`agent/promotions.py`)
`list_promotions` và `find_promotion` ignore ngày. Chỉ khuyến mãi có `valid_from <= hôm nay <= valid_to`
mới được liệt kê và được cộng bonus. "Hôm nay" là `ctx.today` (cố định `2026-10-05` trong config).
- Chú ý ranh giới: `BACKTOSCHOOL` kết thúc 30/09.
- Case liên quan: `promo_*`.

### Lỗi C — Tool schema (`agent/tools.py`)
Schema của `play_rps` quá lỏng: mô tả chỉ là `"play"`, `bet` là chuỗi, `move` không giới hạn.
1. Sửa schema: `move` có `enum`, `bet` là `integer` với `minimum: 1`, thêm `description` rõ ràng.
2. **Schema chỉ là lời nhắc cho model — harness vẫn phải kiểm tra lại** khi thực thi. Validate `args` trong
   `execute_tool` (gợi ý: thư viện `jsonschema` đã có sẵn trong dependency) và trả `{"error": ...}` thay vì crash.
- Case liên quan: `schema_*`.

## 4. Chạy lại và so sánh (45')
```powershell
uv run python -m evaluator.runner --dev --json-out .local\after.json
```
Ghi lại: điểm trước → sau, và với mỗi lỗi: *nguyên nhân gốc* và *một case suýt sửa sai* (ví dụ chặn nhầm cược nhỏ).
Tùy chọn, nếu còn thời gian: chạy `--llm claude` và xem model thật có gọi tool giống kịch bản không.

## Lỗi thường gặp
- Sửa schema nhưng quên validate lúc chạy → case `schema_non_numeric_bet` vẫn crash.
- Dùng `>` thay vì `>=` ở ngưỡng 500 coin.
- So sánh ngày dạng chuỗi khi chưa chuẩn hóa → dùng `date.fromisoformat`.
- Sửa evaluator hay `cases_public.json` cho dễ qua: **không hợp lệ**, điểm tính trên bộ test gốc.

## Yêu cầu đầu ra
Mỗi đội nâng điểm baseline **tối thiểu 15 điểm phần trăm** (28.6% → ít nhất 7/14 = 50%, tức sửa thêm tối thiểu 3 case) và nộp file
`.local\after.json` cùng 3–5 dòng mô tả lỗi đã sửa.

## Đọc thêm
- Anthropic: tài liệu *Tool use* (định nghĩa tool, `tool_use`/`tool_result`).
- Buổi 2 sẽ dùng chính repo này để viết test và tấn công/phòng thủ.
