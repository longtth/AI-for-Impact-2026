# Phần 2b. Xây cùng agent đó bằng Ollama (LLM chạy trên máy bạn)

Phần 2 dùng Claude API: gọi qua mạng, trả tiền theo token. Phần này xây **đúng agent hoàn tiền đó**, nhưng thay Claude bằng một model mã nguồn mở chạy local qua [Ollama](https://ollama.com). Không API key, không tốn tiền token, dữ liệu không rời máy.

Code nằm trong `refund-agent-ollama/`. Đây là bản sao của `refund-agent/` với **chỉ phần giao tiếp với LLM được viết lại**. Nếu bạn đã làm Phần 2 thì đây là bài tập rất tốt để thấy phần nào của agent là *bản chất*, phần nào chỉ là *chi tiết của một nhà cung cấp*.

## 2b.1. Cái gì giữ nguyên, cái gì đổi

| File | So với `refund-agent/` | Ghi chú |
|---|---|---|
| `shop.py` | **Giữ nguyên** | Cửa hàng giả lập + chính sách. Không dính LLM |
| `logger.py` | **Giữ nguyên** | |
| `tests/test_shop.py` | **Giữ nguyên** | |
| `tools.py` | Đổi định dạng schema, thêm 1 guardrail | Logic `ToolExecutor` vẫn là của bạn |
| `agent.py` | **Viết lại vòng lặp** | Cùng ý tưởng, khác giao diện API |
| `cli.py`, `config.py` | Đổi nhỏ | Bỏ API key, thêm `host`, `num_ctx` |
| `tests/fakes.py` | Viết lại | LLM giả theo định dạng của Ollama |

Đây cũng là lý do ta tách `shop.py`, `ToolExecutor` ra khỏi vòng lặp ở Phần 2: đổi LLM không động đến luật nghiệp vụ và guardrail.

## 2b.2. Chuẩn bị môi trường

**1. Cài Ollama** từ [ollama.com/download](https://ollama.com/download). Sau khi cài, server tự chạy ở `http://localhost:11434` (nếu không, chạy `ollama serve`).

**2. Tải một model có hỗ trợ tool calling.** Không phải model nào cũng biết gọi tool. Xem danh sách có nhãn *tools* tại [ollama.com/search?c=tools](https://ollama.com/search?c=tools).

```powershell
ollama pull qwen3:8b
```

`qwen3:8b` cần khoảng 5–6 GB RAM/VRAM. Máy yếu hơn có thể thử `qwen3:4b` hoặc `llama3.2:3b`, nhưng model càng nhỏ càng hay gọi sai tool (xem 2b.6).

**3. Cài thư viện Python:**

```powershell
cd refund-agent-ollama
uv sync
uv run pytest -q          # 18 passed, chưa cần Ollama
```

## 2b.3. Khác biệt giữa Claude API và Ollama API

Vòng lặp vẫn là *gọi LLM, chạy tool, đưa kết quả về, lặp*. Chỉ có hình dạng dữ liệu đổi:

| | Claude (`client.messages.create`) | Ollama (`client.chat`) |
|---|---|---|
| System prompt | tham số `system=` | message `{"role": "system", ...}` đầu danh sách |
| Giới hạn độ dài trả lời | `max_tokens=` | `options={"num_predict": ...}` |
| Mô tả tool | `{"name", "description", "input_schema"}` | `{"type": "function", "function": {"name", "description", "parameters"}}` |
| Biết LLM đòi gọi tool | `stop_reason == "tool_use"` | `message.tool_calls` không rỗng |
| Tham số tool | `block.input` | `call.function.arguments` |
| Id của lời gọi tool | có (`tool_use_id`, phải khớp) | **không có**, ghép theo thứ tự |
| Gửi kết quả tool | message `user` chứa block `tool_result` | message `{"role": "tool", "tool_name": ..., "content": ...}` |
| Cờ lỗi tool | `is_error` | không có, lỗi nằm trong nội dung JSON (`{"error": ...}`) |
| Đếm token | `usage.input_tokens / output_tokens` | `prompt_eval_count / eval_count` |

## 2b.4. Vòng lặp với Ollama

Đọc `refund-agent-ollama/src/refund_agent/agent.py`. Phần lõi:

```python
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_message},
]

for step in range(1, max_steps + 1):
    response = client.chat(
        model=model,
        messages=messages,
        tools=TOOL_SCHEMAS,
        options={"num_predict": max_tokens, "num_ctx": num_ctx},
    )
    message = response.message
    messages.append(message)                  # PHẢI lưu lượt của LLM vào lịch sử

    if not message.tool_calls:                # không đòi tool -> nói xong rồi
        return AgentResult(message.content.strip(), ...)

    for call in message.tool_calls:           # có thể có NHIỀU lời gọi trong một lượt
        result = executor.execute(call.function.name, dict(call.function.arguments))
        messages.append({"role": "tool", "tool_name": call.function.name,
                         "content": json.dumps(result, ensure_ascii=False)})
```

So với 2.5, ba điều đáng để ý:

1. **Điều kiện thoát đổi từ `stop_reason` sang `tool_calls`.** Ollama không có `stop_reason = "tool_use"`. Nó chỉ cho biết có lời gọi tool hay không.
2. **Không có `tool_use_id`.** Vì vậy kết quả tool được ghép với lời gọi theo thứ tự, kèm `tool_name`. Khi LLM gọi hai tool trong một lượt, hãy gửi kết quả theo đúng thứ tự đó.
3. **`MAX_STEPS` còn quan trọng hơn.** Model local nhỏ dễ lặp đi lặp lại một lời gọi tool hơn Claude. Điều kiện dừng vẫn do code của bạn đảm bảo.

Cũng như bản Claude, `run_agent` nhận `client` (đối tượng có hàm `chat`) thay vì tự tạo, nên test truyền vào một `FakeOllama` đọc kịch bản có sẵn. Test chạy trong vài mili giây mà không cần Ollama.

## 2b.5. Chạy thử

```powershell
uv run refund-agent-ollama --dev init       # tạo .local\config.toml
uv run refund-agent-ollama --dev run "Chào shop, tôi muốn hoàn tiền đơn DH1001, email an@example.com. Tai nghe bị hỏng."
```

Config (`.local\config.toml`) khác bản Claude ở chỗ không còn API key mà có các mục của Ollama:

```toml
model = "qwen3:8b"                 # model đã `ollama pull`
host = "http://localhost:11434"    # địa chỉ server Ollama
num_ctx = 8192                     # context window (token)
```

**`num_ctx` là cái bẫy lớn nhất.** Ollama dùng context window khá nhỏ theo mặc định. System prompt + 4 mô tả tool + lịch sử hội thoại có thể vượt ngưỡng đó, và khi đó Ollama **âm thầm cắt phần đầu** (đúng chỗ chứa system prompt và quy tắc!), nên agent bỗng "quên" quy trình mà không hề báo lỗi. Hãy đặt `num_ctx` đủ lớn, và nhớ nó tốn thêm RAM. Đây là hệ quả của điều đã nói ở 2.3: lịch sử gửi lại mỗi vòng.

Hãy thử lại các tình huống ở bảng trong mục 2.6 và so sánh với Claude. Chương trình cũng báo lỗi dễ hiểu khi hạ tầng có vấn đề:

| Tình huống | Thông báo |
|---|---|
| Ollama chưa chạy | `Không kết nối được Ollama tại http://localhost:11434. Đã cài và chạy ollama serve chưa?` |
| Chưa tải model | `Ollama báo lỗi (404) ... Hãy chạy ollama pull qwen3:8b.` |
| Model không hỗ trợ tool | `Ollama báo lỗi (400) ... does not support tools` |

## 2b.6. Model local khác Claude ở đâu: lý do guardrail càng quan trọng

Chạy cùng một kịch bản, bạn sẽ thấy model local nhỏ thường:

- **Gọi sai tham số**, ví dụ `amount` là chuỗi `"890000"` thay vì số nguyên.
- **Bỏ qua bước** (gọi `issue_refund` mà chưa `check_refund_policy`).
- **Bịa lời gọi tool** hoặc bịa dữ liệu thay vì gọi tool.
- Dễ **bị prompt injection** hơn.
- Chậm hơn nhiều nếu không có GPU.

Đó là lý do ở 2.6.3 ta nói *"prompt chỉ là lời đề nghị, code mới là luật"*. Với model mạnh, guardrail là lưới an toàn. Với model local nhỏ, guardrail là thứ giữ cho hệ thống đúng. Bản Ollama có thêm một chi tiết nhỏ minh họa điều này, trong `_tool_issue_refund`:

```python
# Model local nhỏ hay trả số dưới dạng chuỗi ("890000"): chuẩn hóa trước khi so sánh.
try:
    amount = int(amount)
except (TypeError, ValueError):
    return {"error": "amount phải là số nguyên (VND)."}
```

Ta **khoan dung ở đầu vào** (chấp nhận `"890000"`), nhưng **nghiêm khắc ở luật** (vẫn so với `refundable_amount`, vẫn chặn quá hạn, vẫn bắt duyệt số tiền lớn). Khi gặp giá trị vô nghĩa, trả `{"error": ...}` để LLM nhìn thấy và tự sửa, thay vì để chương trình crash. Test tương ứng: `test_amount_given_as_string_is_normalized`, `test_amount_not_a_number_returns_error`.

## 2b.7. Khi nào chọn Ollama, khi nào chọn Claude

| | Ollama (local) | Claude API |
|---|---|---|
| Chi phí | Miễn phí (tốn điện, phần cứng) | Trả theo token |
| Dữ liệu | Không rời máy | Gửi lên server của nhà cung cấp |
| Chất lượng gọi tool, tiếng Việt | Phụ thuộc model, thường kém hơn | Cao, ổn định |
| Tốc độ | Phụ thuộc phần cứng | Nhanh, ổn định |
| Phù hợp | Học, thử nghiệm, dữ liệu nhạy cảm, chạy offline | Production cần độ tin cậy |

Không có lựa chọn "đúng" tuyệt đối. Vì kiến trúc đã tách LLM ra sau một giao diện nhỏ, bạn có thể chạy **cả hai** và đo trên cùng một bộ tình huống, nội dung của Phần 3.

## 2b.8. Tóm tắt phần 2b

- Đổi từ Claude sang Ollama chỉ phải viết lại **lớp giao tiếp LLM** (`agent.py`, định dạng schema trong `tools.py`). Cửa hàng, chính sách, guardrail, test của chúng đều dùng lại.
- Khác biệt chính: không có `stop_reason` (nhìn `tool_calls`), không có `tool_use_id`, system prompt là một message, kết quả tool là message `role="tool"`.
- Cẩn thận `num_ctx`: context quá nhỏ làm Ollama âm thầm cắt mất system prompt.
- Model local nhỏ sai nhiều hơn, nên **guardrail trong code** càng không thể thiếu.

### Bài tập

1. **Dễ:** chạy 6 đơn DH1001 đến DH1006 với `qwen3:8b`, ghi lại đơn nào model làm đúng, đơn nào sai.
2. **Dễ:** đặt `num_ctx = 512` rồi chạy lại. Điều gì xảy ra, và log cho bạn thấy dấu hiệu gì (gợi ý: số token vào)?
3. **Vừa:** thử một model khác (`llama3.2:3b`) và so sánh số bước, số lần gọi sai tham số trong log.
4. **Vừa:** thêm chế độ `--stream` để in câu trả lời cuối từng chữ một (`client.chat(..., stream=True)`).
5. **Khó:** viết một lớp `LLMClient` dùng chung, có hai bản cài đặt (Claude và Ollama), để cùng một `run_agent` chạy được với cả hai. Cái gì khó gộp nhất?
