# Training course AI Impact 2026

Khóa 3 buổi x 3 giờ: lập trình **AI Agent** qua một bài toán gần gũi — **RPS Coin Bot**, trợ lý của app
oẳn tù tì ăn coin. Người chơi chat để nạp tiền (1.000 VND = 1 coin, qua payOS), chơi oẳn tù tì cược coin,
xem số dư/lịch sử, đổi quà và hỏi khuyến mãi.

| Buổi                         | Chủ đề                                   | Đầu ra                                                         |
| ---------------------------- | ---------------------------------------- | -------------------------------------------------------------- |
| [Buổi 1](session1/README.md) | Hiểu và sửa một AI Agent                 | Nâng điểm baseline tối thiểu 15 điểm phần trăm (28.6% → ≥ 50%) |
| [Buổi 2](session2/README.md) | Evaluation, Security và Recovery         | 08 ca kiểm thử, 02 ca bảo mật, 01 ca timeout, 01 báo cáo trace |
| [Buổi 3](session3/README.md) | Mock Run và From Prototype to Deployment | 01 bài nộp hợp lệ + 01 bản demo trực tuyến                     |

## Cài đặt (Windows, PowerShell)

Yêu cầu: [uv](https://docs.astral.sh/uv/) và một `ANTHROPIC_API_KEY`.

```powershell
uv sync                                   # cài dependency (gặp lỗi SSL: uv sync --system-certs)
Copy-Item .env.example .env               # điền ANTHROPIC_API_KEY vào .env, KHÔNG commit
uv run python -m agent.cli --dev init     # tạo .local\config.toml từ config.example.toml
uv run python -m evaluator.runner --dev   # chạy public tests (mặc định: model giả lập, miễn phí)
```

Dùng `--dev` khi học: config, log, database nằm trong `.local\` (đã gitignore). Không có `--dev`,
app đọc `%APPDATA%\rpsbot\config.toml` và ghi log vào `%APPDATA%\rpsbot\.log\`.

## Lệnh thường dùng

| Việc                       | Lệnh                                                                    |
| -------------------------- | ----------------------------------------------------------------------- |
| Chat với bot (cần API key) | `uv run python -m agent.cli --dev chat --user alice`                    |
| Chấm public tests          | `uv run python -m evaluator.runner --dev`                               |
| Chấm bằng Claude thật      | `uv run python -m evaluator.runner --dev --llm claude`                  |
| Xuất kết quả JSON          | `uv run python -m evaluator.runner --dev --json-out .local\result.json` |
| Unit test / lint / type    | `uv run pytest` · `uv run ruff check .` · `uv run pyright`              |

Mỗi lần chạy, config đã nạp từ file nào được ghi trong log (`.local\.log\rpsbot.log`).

## Cấu trúc repo

| Thư mục        | Nội dung                                                                                                      |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| `agent/`       | Agent baseline: vòng lặp (`agent.py`), tool (`tools.py`), khuyến mãi, thanh toán, CLI. **Chỗ sinh viên sửa.** |
| `common/`      | Hạ tầng dùng chung: config/`--dev`, logger, SQLite store, client payOS (mock/live)                            |
| `evaluator/`   | Evaluator + `cases_public.json` (public tests)                                                                |
| `data/`        | Luật chơi, danh sách khuyến mãi                                                                               |
| `tests/`       | Unit test cho `common/`                                                                                       |
| `session1..3/` | README từng buổi                                                                                              |
| `instructor/`  | Chỉ dành cho giảng viên: đáp án, hidden tests, kịch bản. **Không phát cho sinh viên.**                        |

## Tài liệu tham khảo

- learnharness.org (tiếng Việt) — dùng từ Buổi 2.
- [Tài liệu payOS](https://payos.vn/docs/) — cho Buổi 3.
