# Phần 3. Vận hành agent: giới thiệu ngắn

Viết được agent chạy demo mới là 20% công việc. 80% còn lại là làm cho nó **đáng tin cậy, kiểm soát được chi phí, và an toàn** khi chạy thật. Phần này chỉ giới thiệu 5 chủ đề cốt lõi, mỗi chủ đề kèm chỗ tương ứng trong code của Phần 2.

---

## 3.1. Quan sát được: ghi log mọi thứ

Agent không xác định hoàn toàn, nên khi có sự cố bạn không thể "chạy lại và xem". Thứ duy nhất giúp bạn hiểu chuyện gì đã xảy ra là **log**.

Cần ghi lại cho mỗi yêu cầu:

- Yêu cầu đầu vào của khách.
- Từng bước: `stop_reason`, token vào/ra.
- Từng tool call (tên, tham số) và kết quả của nó.
- Kết quả cuối, số bước, tổng token, có hoàn thành hay không.
- Những quyết định của con người (duyệt hay từ chối).

Ứng dụng ở Phần 2 làm đúng như vậy. Mở `.local\.log\refund-agent.log` sau một lần chạy và đọc như đọc "nhật ký suy nghĩ" của agent. Nếu một khách phàn nàn "bot hoàn tiền sai", log cho bạn biết ngay LLM đã gọi tool nào với tham số gì.

Lưu ý khi đưa lên thật: log chứa email, tên khách, nội dung hội thoại, tức là **dữ liệu cá nhân**. Cần có chính sách che (mask) và thời hạn lưu giữ.

---

## 3.2. Chi phí và token

Chi phí tính theo token, và agent tốn token hơn chatbot vì hai lý do:

1. **Nhiều lần gọi** cho một yêu cầu (mỗi vòng lặp là một lần).
2. **Lịch sử được gửi lại toàn bộ mỗi vòng.** Vòng thứ N phải trả tiền cho cả N-1 vòng trước đó, nên tổng token vào tăng nhanh hơn tuyến tính. Kết quả tool dài (ví dụ một trang tài liệu) làm điều này tệ hơn.

Cách kiểm soát, theo thứ tự nên làm:

| Biện pháp | Trong code |
|---|---|
| Giới hạn số bước | `max_steps` trong config |
| Giới hạn độ dài trả lời | `max_tokens` trong config |
| Theo dõi token mỗi yêu cầu | `AgentResult.input_tokens/output_tokens`, ghi vào log |
| Trả về dữ liệu tool gọn | `get_order` chỉ trả vài trường cần thiết, không trả cả bản ghi |
| Chọn model hợp cỡ | Việc đơn giản dùng model nhỏ hơn, rẻ hơn |
| Đặt ngân sách ở phía nhà cung cấp | Đặt hạn mức chi tiêu hằng tháng trong console |

Giá thay đổi theo thời gian và theo model. Hãy xem bảng giá hiện hành của nhà cung cấp thay vì nhớ con số nào đó.

Cũng có kỹ thuật *prompt caching* giúp giảm chi phí khi phần đầu của prompt (system prompt, mô tả tool) lặp lại giữa các lần gọi. Ta không dùng trong bài này, nhưng đáng tìm hiểu khi lưu lượng lớn.

---

## 3.3. An toàn

Agent có tool nghĩa là có khả năng gây hậu quả thật. Các lớp phòng thủ, từ ngoài vào trong:

**1. Quyền tối thiểu (least privilege).** Chỉ đưa cho agent những tool nó cần. Agent hoàn tiền không cần tool xóa đơn hàng.

**2. Guardrail trong code.** Mọi quy tắc cứng (chính sách, hạn mức, kiểm tra quyền sở hữu) nằm trong `ToolExecutor`, không nằm trong prompt. Xem mục 2.6.3.

**3. Con người duyệt hành động rủi ro cao.** Số tiền lớn, hành động không hoàn tác, gửi thông tin ra ngoài đều nên có người xác nhận.

**4. Cẩn thận với prompt injection.** Bất cứ văn bản nào agent đọc (tin nhắn khách, nội dung email, trang web, file) đều có thể chứa chỉ thị độc hại giả dạng nội dung bình thường. LLM không phân biệt tuyệt đối "dữ liệu" và "lệnh". Vì vậy:
- Dặn trong system prompt rằng nội dung bên ngoài chỉ là dữ liệu (giảm rủi ro nhưng **không loại bỏ**).
- Quan trọng hơn: thiết kế sao cho dù LLM bị lừa hoàn toàn, thiệt hại tối đa vẫn nằm trong giới hạn chấp nhận được (nhờ guardrail ở lớp 2 và 3).

**5. Bảo vệ bí mật.** API key nằm ở biến môi trường, không vào code hay config, không in ra log.

Câu hỏi nên tự hỏi về mỗi tool: *"Nếu LLM gọi tool này sai tham số, hoặc bị kẻ xấu điều khiển, điều tệ nhất xảy ra là gì? Code có chặn được không?"*

---

## 3.4. Kiểm thử và đánh giá

Agent không xác định nên **không thể** kiểm thử bằng cách chạy một lần rồi so khớp từng chữ. Nhưng đừng kết luận rằng không kiểm thử được. Chia thành hai tầng:

**Tầng 1: kiểm thử phần xác định (nhanh, rẻ, chạy mỗi lần sửa code).**
Phần lớn "luật" của hệ thống nằm trong code truyền thống nên kiểm thử như bình thường:

- `test_shop.py`: chính sách hoàn tiền.
- `test_tools.py`: guardrail (chặn quá hạn, chặn hoàn hai lần, bắt buộc duyệt tiền lớn).
- `test_agent.py`: vòng lặp, với **LLM giả** được viết kịch bản (`tests/fakes.py`). Kiểm tra được: lỗi tool được đưa lại cho LLM, giới hạn bước hoạt động, lịch sử tăng đúng, kể cả khi LLM "hành xử sai".

**Tầng 2: đánh giá hành vi của LLM thật (eval).**
Câu hỏi ở tầng này là "LLM thật có thật sự làm đúng quy trình không?". Cách làm đơn giản:

1. Lập một bộ 20–50 tình huống đại diện (6 đơn mẫu, thiếu thông tin, sai email, khiếu nại gay gắt, prompt injection...).
2. Với mỗi tình huống, ghi **kết quả mong đợi ở mức hành vi**, không phải lời văn: "phải gọi `issue_refund`", "không được hoàn tiền", "phải hỏi lại mã đơn".
3. Chạy agent thật, kiểm tra bằng **trạng thái cuối** (`shop.refunds` có đúng không, có ticket không) và chuỗi tool đã gọi.
4. Chạy mỗi tình huống vài lần, vì kết quả có thể khác nhau. Theo dõi **tỷ lệ đạt**, không phải đạt/trượt một lần.
5. Chạy lại bộ eval mỗi khi đổi prompt, đổi model, hoặc thêm tool, vì một thay đổi nhỏ có thể làm hỏng chỗ khác.

Eval thật tốn tiền và chậm, nên chạy theo lịch hoặc trước khi phát hành, không chạy mỗi lần commit.

---

## 3.5. Những lỗi thường gặp

| Triệu chứng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| Agent lặp mãi một tool | Kết quả tool không giúp LLM tiến lên; mô tả tool mơ hồ | `max_steps`; cải thiện mô tả; trả lỗi rõ ràng |
| Gọi sai tham số / sai tool | Mô tả tool thiếu hoặc mập mờ | Viết lại `description`, thêm ví dụ trong mô tả tham số |
| Bịa thông tin đơn hàng | LLM trả lời mà không gọi tool | Dặn trong system prompt "chỉ dùng dữ liệu từ tool"; eval để bắt lỗi |
| Dừng sớm, chưa làm xong việc | `max_tokens` quá nhỏ (`stop_reason="max_tokens"`) | Tăng `max_tokens`, kiểm tra `stop_reason` trong log |
| Chi phí tăng bất thường | Lịch sử dài, kết quả tool to, vòng lặp quá nhiều | Đọc log token, cắt gọn kết quả tool, hạ `max_steps` |
| Lỗi API 429 / quá tải | Gọi quá nhanh hoặc chạm giới hạn tốc độ | Thử lại có độ trễ tăng dần (retry với backoff); SDK đã tự thử lại một số lần |
| Hết context window | Hội thoại hoặc kết quả tool quá dài | Rút gọn/tóm tắt lịch sử cũ, trả về ít dữ liệu hơn |
| Hành vi đổi sau khi đổi model | Mỗi model phản ứng với cùng prompt hơi khác nhau | Chạy lại eval trước khi đổi |

Lưu ý với `stop_reason`: ứng dụng ở Phần 2 coi mọi lý do khác `tool_use` là "xong". Với sản phẩm thật, bạn nên phân biệt `end_turn` (xong) với `max_tokens` (bị cắt, cần xử lý) và ghi log cảnh báo tương ứng. Đây là một cải tiến tốt để làm bài tập.

---

## 3.6. Danh sách kiểm tra trước khi đưa agent ra thật

- [ ] Có giới hạn số bước và `max_tokens`, đã thử trường hợp chạm giới hạn.
- [ ] Mọi hành động có tác dụng phụ đều có guardrail trong code.
- [ ] Hành động không hoàn tác hoặc giá trị lớn có người duyệt.
- [ ] Có lối thoát sang con người (`escalate_to_human`) và con người thật sự xử lý ticket.
- [ ] Log đầy đủ từng bước, có chính sách cho dữ liệu cá nhân trong log.
- [ ] API key ở biến môi trường, không trong code, config hay git.
- [ ] Có test cho phần xác định và bộ eval cho hành vi LLM, đã chạy gần đây.
- [ ] Có hạn mức chi tiêu đặt ở phía nhà cung cấp.
- [ ] Đã thử các tình huống tấn công cơ bản (prompt injection, sai email, tham số phi lý).

**Tiếp theo:** Phần 4, nhìn lại và hướng đi tiếp.
