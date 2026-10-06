# Phần 1. Khái niệm: từ phần mềm truyền thống đến agent

Mục tiêu của phần này: sau khi đọc xong, bạn giải thích được **agent là gì**, nó khác **phần mềm truyền thống**, **chatbot** và **workflow** ở điểm nào, và biết các thuật ngữ sẽ gặp lại trong Phần 2 khi tự viết code.

Phần này không có code. Hãy đọc chậm, vì mọi thứ sau đó đều dựa vào các khái niệm ở đây.

---

## 1.1. Phần mềm truyền thống là gì?

Phần mềm truyền thống là chương trình mà **lập trình viên viết sẵn mọi quy tắc**. Với cùng một đầu vào, nó luôn cho cùng một đầu ra.

Ví dụ: một hàm tính tiền ship.

```python
def phi_ship(khoang_cach_km: float) -> int:
    if khoang_cach_km <= 5:
        return 15_000
    if khoang_cach_km <= 20:
        return 30_000
    return 50_000
```

Đặc điểm:

| Đặc điểm | Ý nghĩa |
|---|---|
| **Xác định (deterministic)** | Cùng đầu vào cho cùng đầu ra, kiểm thử bằng `assert` được |
| **Quy tắc tường minh** | Muốn chương trình làm gì thì phải viết ra từng trường hợp |
| **Đầu vào có cấu trúc** | Số, chuỗi đúng định dạng, JSON, form. Đầu vào "tự do" như một câu văn thì khó xử lý |
| **Luồng điều khiển do con người quyết định** | Thứ tự các bước nằm trong code (`if`, `for`, gọi hàm) |

Điểm mạnh là nhanh, rẻ, đáng tin cậy. Điểm yếu là **cứng**: gặp tình huống chưa ai viết quy tắc cho thì chương trình bó tay. Hãy thử viết `if/else` để xử lý mọi cách một khách hàng có thể phàn nàn về đơn hàng, bạn sẽ thấy ngay giới hạn đó.

---

## 1.2. LLM: "bộ não" mới

**LLM (Large Language Model, mô hình ngôn ngữ lớn)** là mô hình được huấn luyện trên lượng văn bản khổng lồ để dự đoán đoạn văn tiếp theo hợp lý. Claude, GPT, Gemini đều là LLM.

Từ góc nhìn của lập trình viên, hãy coi LLM như **một hàm đặc biệt**:

```
văn bản vào  →  [ LLM ]  →  văn bản ra
```

Điểm khác với hàm thông thường:

- **Hiểu ngôn ngữ tự nhiên**: bạn đưa vào một câu tiếng Việt tự do, không cần định dạng cố định.
- **Không xác định hoàn toàn**: hỏi hai lần có thể nhận hai câu trả lời khác nhau về cách diễn đạt.
- **Có thể sai mà vẫn nói rất tự tin** (gọi là hallucination, "ảo giác").
- **Chỉ biết những gì nằm trong dữ liệu huấn luyện và trong đoạn văn bạn đưa vào.** Nó không biết hôm nay là ngày mấy, không biết file nào trên máy bạn.
- **Chỉ "nói", không "làm".** LLM tự nó không đọc được file, không gọi được API, không gửi được email. Nó chỉ sinh ra văn bản.

Điểm cuối cùng là chìa khóa để hiểu agent. Hãy nhớ nó.

---

## 1.3. Ba cấp độ: Chatbot, Workflow, Agent

Khi đưa LLM vào ứng dụng, có ba mức phổ biến. Điểm phân biệt quan trọng nhất là **ai quyết định bước tiếp theo**.

| | Chatbot | Workflow | Agent |
|---|---|---|---|
| Mô tả | Hỏi một câu, đáp một câu | Chuỗi bước **do lập trình viên định sẵn**, có bước gọi LLM | LLM **tự quyết định** bước tiếp theo để đạt mục tiêu |
| Ai quyết định luồng? | Không có luồng | Code | LLM |
| Số bước | 1 | Cố định | Không biết trước |
| Dùng công cụ bên ngoài? | Không | Có, theo thứ tự cố định | Có, tự chọn công cụ nào, khi nào |
| Ví dụ | Hỏi "thủ đô Pháp là gì?" | Nhận email → LLM tóm tắt → LLM phân loại → lưu DB | "Tìm lỗi trong repo này và sửa" |
| Độ dự đoán | Cao | Cao | Thấp hơn |

Ví dụ cùng một bài toán "xử lý yêu cầu hoàn tiền":

- **Chatbot:** trả lời "Chính sách hoàn tiền của chúng tôi là…". Hết.
- **Workflow:** code luôn chạy đúng trình tự *đọc email → LLM trích mã đơn → tra DB → LLM soạn thư trả lời → gửi*. Mỗi bước LLM chỉ làm một việc nhỏ, đường đi cố định.
- **Agent:** bạn đưa mục tiêu "xử lý yêu cầu hoàn tiền này". LLM tự quyết: tra đơn hàng trước, thấy thiếu thông tin thì hỏi lại khách, rồi mới kiểm tra điều kiện hoàn tiền, và dừng khi thấy xong.

> **Lời khuyên thực tế:** workflow thường là lựa chọn tốt hơn nếu bạn đã biết rõ các bước. Chỉ dùng agent khi **không thể biết trước cần bao nhiêu bước hoặc bước nào**.

---

## 1.4. Agent là gì?

> **Agent = LLM + công cụ (tools) + vòng lặp (loop), hoạt động để đạt một mục tiêu.**

Từng thành phần:

### a) LLM: bộ não
Đọc tình huống hiện tại và quyết định làm gì tiếp.

### b) Tools: đôi tay
Vì LLM chỉ sinh văn bản, ta cho nó "tay chân" bằng cách định nghĩa các **tool** (còn gọi là *function calling*): những hàm do bạn viết, ví dụ `doc_file(duong_dan)`, `tim_kiem_web(tu_khoa)`, `gui_email(...)`.

Cơ chế quan trọng, hãy đọc kỹ vì nhiều người hiểu nhầm:

1. Bạn mô tả cho LLM biết có những tool nào (tên, công dụng, tham số).
2. LLM **không tự chạy tool**. Nó chỉ trả về một yêu cầu có cấu trúc, kiểu: *"Hãy gọi `doc_file` với `duong_dan="a.txt"`"*.
3. **Code của bạn** thực sự chạy hàm đó, rồi đưa kết quả trở lại cho LLM.

Tức là LLM đề xuất, còn chương trình của bạn thực thi. Điều này có ý nghĩa lớn về an toàn: bạn luôn nắm quyền quyết định cái gì được chạy thật.

### c) Vòng lặp: nhịp hoạt động

```
        ┌────────────────────────────────────────┐
        │                                        │
        ▼                                        │
  ┌───────────┐   cần dùng tool    ┌──────────┐  │
  │   LLM     │ ─────────────────► │ Code của │  │
  │ (suy nghĩ │                    │ bạn chạy │  │
  │ & quyết   │ ◄───────────────── │  tool    │  │
  │  định)    │   kết quả tool     └──────────┘  │
  └───────────┘                                  │
        │                                        │
        │ "đã xong"                              │
        ▼                                        │
   Trả lời cuối cùng                (lặp lại ────┘
                                  nếu chưa xong)
```

Mỗi vòng gồm: **quan sát** (đọc tình huống và kết quả tool trước đó) → **suy nghĩ** (quyết định) → **hành động** (gọi tool) → quay lại quan sát. Vòng lặp kết thúc khi LLM cho rằng đã đạt mục tiêu, hoặc khi chạm giới hạn do bạn đặt.

### Ví dụ minh họa

Yêu cầu: *"Trong thư mục này có bao nhiêu file Python?"*

```
Vòng 1: LLM nghĩ "cần xem thư mục"      → gọi tool liet_ke_file(".")
        Code chạy tool, trả: ["a.py", "b.py", "README.md"]
Vòng 2: LLM nghĩ "có 2 file .py"         → không gọi tool nữa
        Trả lời: "Có 2 file Python: a.py và b.py."
```

Không có dòng `if` nào của lập trình viên quyết định "gọi liet_ke_file trước". LLM tự chọn. Đó là điểm làm agent khác workflow.

---

## 1.5. Các khái niệm liên quan

Các thuật ngữ này sẽ xuất hiện liên tục từ Phần 2.

| Thuật ngữ | Giải thích ngắn |
|---|---|
| **Prompt** | Văn bản bạn gửi cho LLM |
| **System prompt** | Chỉ dẫn nền do lập trình viên đặt: vai trò, quy tắc, giọng điệu. Người dùng thường không thấy |
| **Message / hội thoại** | LLM không "nhớ" gì giữa các lần gọi. Mỗi lần gọi bạn phải gửi lại **toàn bộ lịch sử** các lượt `user` và `assistant` |
| **Token** | Đơn vị văn bản mà LLM xử lý (khoảng một âm tiết hoặc một mảnh từ). Tính phí và giới hạn đều theo token |
| **Context window** | Tổng lượng token tối đa LLM xử lý được trong một lần gọi (cả vào lẫn ra). Hội thoại và kết quả tool dài quá sẽ chạm trần |
| **Tool / function calling** | Cơ chế để LLM yêu cầu code của bạn chạy hàm (mục 1.4b) |
| **Memory (bộ nhớ)** | Cách agent giữ thông tin: ngắn hạn là lịch sử hội thoại trong context, dài hạn là lưu ra file hoặc DB rồi nạp lại khi cần |
| **Planning** | Agent chia mục tiêu lớn thành các bước nhỏ trước khi hành động |
| **Điều kiện dừng** | Khi nào vòng lặp kết thúc: LLM báo xong, hoặc chạm giới hạn số bước. Thiếu điều kiện này agent có thể lặp vô hạn và đốt tiền |
| **Guardrails** | Các rào chắn an toàn: giới hạn tool nào được dùng, hành động nào cần con người xác nhận |
| **Human-in-the-loop** | Con người duyệt các bước quan trọng (xóa dữ liệu, gửi tiền, gửi email) |
| **RAG** | Tìm tài liệu liên quan rồi nhét vào prompt để LLM trả lời dựa trên đó |
| **MCP (Model Context Protocol)** | Chuẩn mở để các tool/nguồn dữ liệu cắm vào agent theo cùng một kiểu, khỏi viết tích hợp riêng cho từng ứng dụng |
| **Multi-agent** | Nhiều agent phối hợp, mỗi agent một vai trò. Chủ đề nâng cao, ngoài phạm vi bài này |

---

## 1.6. Khi nào nên và không nên dùng agent?

Agent không phải lúc nào cũng tốt hơn. Đổi lại sự linh hoạt, bạn trả giá:

| Chi phí | Giải thích |
|---|---|
| **Tiền** | Mỗi vòng lặp là một lần gọi LLM, và lịch sử càng dài càng tốn token |
| **Thời gian** | Nhiều vòng lặp nghĩa là chậm hơn nhiều so với một hàm thường |
| **Độ tin cậy** | Có thể chọn sai tool, đi vòng, hoặc dừng sớm. Khó dự đoán và khó kiểm thử hơn |
| **Rủi ro** | Có tool thật nghĩa là có thể gây hậu quả thật |

Dùng bảng này để quyết định:

| Tình huống | Nên dùng |
|---|---|
| Bài toán có quy tắc rõ, đầu vào có cấu trúc | **Phần mềm truyền thống** |
| Cần hiểu hoặc sinh văn bản, nhưng các bước cố định | **Workflow** |
| Mục tiêu mở, không biết trước cần bao nhiêu bước hay tool nào | **Agent** |

Nguyên tắc: **bắt đầu từ giải pháp đơn giản nhất** và chỉ tăng độ phức tạp khi thật sự cần.

---

## 1.7. Tóm tắt phần 1

- Phần mềm truyền thống: quy tắc do người viết, kết quả xác định, nhưng cứng.
- LLM: hiểu ngôn ngữ tự nhiên và linh hoạt, nhưng chỉ sinh văn bản, không xác định hoàn toàn.
- Chatbot trả lời một lượt. Workflow đi theo đường định sẵn. Agent tự quyết đường đi.
- **Agent = LLM + tools + vòng lặp.** LLM đề xuất hành động, code của bạn thực thi và trả kết quả về.
- Agent linh hoạt nhưng tốn kém và khó đoán hơn, nên chỉ dùng khi bài toán thật sự mở.

### Câu hỏi tự kiểm tra

1. Vì sao nói LLM "chỉ nói, không làm"? Điều gì biến nó thành agent?
2. Trong ví dụ hoàn tiền, đâu là điểm khác nhau căn bản giữa workflow và agent?
3. Ai thực sự chạy tool: LLM hay code của bạn? Vì sao điều này quan trọng với an toàn?
4. Cho ba bài toán: (a) tính thuế thu nhập, (b) tóm tắt mỗi email đến rồi gắn nhãn, (c) "tìm và sửa lỗi test đang fail trong repo". Bài nào hợp với phần mềm thường, workflow, agent?

> Gợi ý đáp án câu 4: (a) phần mềm thường, (b) workflow, (c) agent.

**Tiếp theo:** Phần 2, tự tay xây một agent từ con số không.
