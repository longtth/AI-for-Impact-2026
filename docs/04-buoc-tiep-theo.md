# Phần 4. Nhìn lại và bước tiếp theo

## 4.1. Bạn vừa làm được gì

Bạn đã xây một agent từ con số không, không framework, và hiểu từng phần của nó:

```
          ┌──────────────── agent.py: vòng lặp (có giới hạn số bước) ────────────────┐
khách ──► │  LLM  ──(đề xuất gọi tool)──►  ToolExecutor  ──►  shop.py (luật cứng)    │
          │   ▲                              │ guardrail: kiểm tra, xin duyệt        │
          │   └──────── kết quả / lỗi ◄──────┘                                       │
          └──────────────────────────────────────────────────────────────────────────┘
                                   │ log mọi bước ra file
                                   ▼
                              câu trả lời cuối
```

Những ý đáng mang theo:

1. Agent chỉ là **vòng lặp quanh LLM có tool**, không có phép màu nào bên trong.
2. LLM **đề xuất**, code **quyết định thực thi**. Mọi quy tắc cứng, quyền hạn và tiền bạc phải nằm trong code.
3. Agent khó đoán hơn phần mềm thường, nên cần **giới hạn, log, và đánh giá** có hệ thống.
4. Bắt đầu từ giải pháp đơn giản nhất. Nếu bài toán có các bước cố định thì workflow thường tốt hơn agent.

## 4.2. Hướng mở rộng

| Chủ đề | Ý tưởng | Gắn với dự án này |
|---|---|---|
| **Framework / Agent SDK** | Các thư viện đóng gói sẵn vòng lặp, quản lý lịch sử, retry, tracing. Giờ bạn đã hiểu bản chất nên đánh giá chúng dễ hơn | Thử viết lại `agent.py` bằng một SDK và so sánh |
| **Streaming** | Nhận câu trả lời từng phần để giao diện phản hồi nhanh | Hiển thị câu trả lời dần cho khách |
| **Hội thoại nhiều lượt thật** | Agent giữ phiên chat, khách trả lời tiếp khi bot hỏi lại | Hiện mỗi lần `run` là một yêu cầu độc lập |
| **Bộ nhớ dài hạn** | Lưu lịch sử khách qua các phiên để dùng lại | Biết khách hay hoàn tiền thì cảnh giác hơn |
| **RAG** | Tìm tài liệu liên quan rồi đưa vào prompt | Để chính sách hoàn tiền dài hàng chục trang vẫn tra được |
| **MCP** | Chuẩn để cắm tool/nguồn dữ liệu vào agent | Đưa `shop` thành một MCP server dùng được với nhiều agent |
| **Structured output** | Ép LLM trả kết quả đúng định dạng JSON | Phân loại yêu cầu trước khi xử lý |
| **Multi-agent** | Nhiều agent chuyên biệt phối hợp | Agent tiếp nhận, agent kiểm tra gian lận, agent hoàn tiền |
| **Prompt caching** | Giảm chi phí cho phần prompt lặp lại | Cache system prompt và mô tả tool |
| **Tracing / observability** | Công cụ xem chi tiết từng lượt chạy | Thay cho việc đọc file log thủ công |

Thứ tự gợi ý: làm bài tập, rồi eval (3.4), rồi RAG hoặc bộ nhớ, và multi-agent để sau cùng. Đừng thêm độ phức tạp trước khi bạn đo được nó giúp ích.

## 4.3. Bài tập tổng hợp

1. **Phân biệt `stop_reason`:** sửa `agent.py` để tách `max_tokens` thành trường hợp riêng, ghi log cảnh báo, và báo cho người dùng biết câu trả lời bị cắt. Viết test bằng LLM giả.
2. **Chế độ chat:** thêm lệnh `refund-agent chat` giữ `messages` giữa các lượt để khách trả lời khi agent hỏi lại.
3. **Bộ eval:** viết script chạy 10 tình huống với LLM thật, mỗi tình huống 3 lần, và in tỷ lệ đạt cùng tổng token tiêu thụ.
4. **Mở rộng chính sách:** thêm hoàn tiền một phần (hàng đã dùng, hoàn 70%). Quyết định chỗ đặt quy tắc, và cập nhật guardrail để LLM không tự định số tiền.
5. **Đổi nhà cung cấp:** tách phần gọi API ra sau một lớp mỏng để có thể đổi sang model khác mà không sửa vòng lặp. Bạn cần giữ nguyên giao diện nào?

## 4.4. Tài liệu đọc thêm

- Tài liệu chính thức của Anthropic về Messages API và tool use: [docs.claude.com](https://docs.claude.com).
- Bài viết "Building effective agents" của Anthropic: phân biệt workflow và agent, các mẫu thiết kế thường gặp.
- Tài liệu của `uv`: [docs.astral.sh/uv](https://docs.astral.sh/uv/).

Chúc bạn xây dựng agent vui vẻ, và nhớ: **bắt đầu nhỏ, đặt giới hạn, ghi log, kiểm thử.**
