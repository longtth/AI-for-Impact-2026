# Buổi 3 — Mock Run và From Prototype to Deployment (3 giờ)

## Mục tiêu
- Trải nghiệm đúng quy trình ngày thi kỹ thuật và đọc bảng điểm.
- Đưa agent từ prototype lên bản chạy ổn định, truy cập được qua mạng.
- Dựng video demo và thuyết trình ngắn, rõ ràng.

## Chuẩn bị trước buổi
- Repo đội đã qua Buổi 1–2, `uv run pytest` và evaluator chạy được.
- Máy chạy được `git`, `uv`; có tài khoản nền tảng hosting (giảng viên thông báo) và, nếu dùng payOS thật,
  tài khoản payOS (`PAYOS_CLIENT_ID`, `PAYOS_API_KEY`, `PAYOS_CHECKSUM_KEY` trong `.env`).

## Timeline
| Thời gian | Nội dung |
|---|---|
| 0:00–1:30 | Mock run: mô phỏng ngày thi |
| 1:30–1:45 | Nghỉ, xem bảng điểm |
| 1:45–2:45 | Tích hợp API, triển khai/hosting, đóng gói demo |
| 2:45–3:00 | Kỹ năng video và thuyết trình |

## 1. Mock run (90')
Quy trình y như ngày thi, có đồng hồ đếm ngược:
1. **Nhận repository** của đề mô phỏng (bản rút gọn, có lỗi mới ngoài những lỗi đã học).
2. **Chạy bộ kiểm thử** (`uv run python -m evaluator.runner --dev`) để biết điểm xuất phát.
3. **Sửa lỗi** — ưu tiên theo điểm/độ khó, commit nhỏ.
4. **Nộp bài** theo cách ban tổ chức hướng dẫn trong buổi (định dạng/đường dẫn nộp được công bố ngày mock run).
5. **Đọc bảng điểm**, xác định lỗi còn lại.

Ban Tổ chức đồng thời kiểm tra hệ thống chấm: nộp trùng, nộp sai định dạng, nhiều đội nộp cùng lúc.
Ghi lại mọi điều bất thường bạn gặp (thông báo lỗi khó hiểu, chậm...) — đó là phản hồi cho BTC.

## 2. Tích hợp API và triển khai (60')
Mục tiêu: một URL công khai mà người khác mở được và chat/chơi được.
1. **Bọc agent thành API HTTP** (gợi ý FastAPI): `POST /chat`, `POST /webhooks/payos`, `GET /health`.
   Tái dùng `run_turn` (`agent/agent.py`) và `payments.handle_webhook` (`agent/payments.py`) — không viết lại logic.
2. **Secret**: chỉ đọc từ biến môi trường của nền tảng; không commit `.env`.
3. **payOS thật (tùy chọn)**: đặt `payos.mode = "live"` trong config; cấu hình URL webhook trong payOS trỏ tới
   `https://<domain>/webhooks/payos`. Webhook phải kiểm tra chữ ký và idempotent (đã làm ở Buổi 2).
   Chế độ `live` trong `common/payos_client.py` chưa được kiểm thử với tài khoản thật — đối chiếu tài liệu payOS.
4. **Ổn định cho demo**: dùng dữ liệu mẫu cố định, `agent.today` cố định, có phương án dự phòng
   (kịch bản đã ghi sẵn) khi mạng/LLM lỗi, chạy thử từ máy khác.
5. **Checklist trước khi gửi link**: `/health` trả OK · không lộ secret/PII trong log · mở link từ mạng khác
   (điện thoại 4G) · restart dịch vụ vẫn chạy.

## 3. Video demo và thuyết trình (15')
Kịch bản 3 phút: vấn đề (10s) → demo chính (90s: nạp → chơi → đổi quà) → một tình huống an toàn
(từ chối cược lớn khi chưa xác nhận, chặn khuyến mãi hết hạn) (40s) → kết quả evaluator + bài học (30s).
Mẹo: thu màn hình 1080p, phóng to font terminal, chuẩn bị sẵn từng bước, nói chậm, có phụ đề.

## Lỗi thường gặp
- Quên cấu hình biến môi trường trên máy chủ → `ANTHROPIC_API_KEY` thiếu.
- Webhook trả lỗi 500 → payOS gửi lại nhiều lần; xử lý idempotent là bắt buộc.
- Demo phụ thuộc mạng/LLM mà không có phương án dự phòng.

## Yêu cầu đầu ra
- **01 bài nộp hợp lệ** qua hệ thống chấm của mock run.
- **01 bản demo trực tuyến** truy cập được (link + video 3 phút).

## Đọc thêm
- Tài liệu payOS (payment link, webhook, chữ ký).
- Tài liệu của nền tảng hosting được chọn.
