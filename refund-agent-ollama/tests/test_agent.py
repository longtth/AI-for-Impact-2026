import json
from types import SimpleNamespace

from refund_agent.agent import AgentResult, run_agent
from refund_agent.shop import Shop
from refund_agent.tools import ToolExecutor
from tests.fakes import FakeOllama, reply, tool_call


def run(
    script: list[SimpleNamespace], approve: bool = True, max_steps: int = 8
) -> tuple[AgentResult, Shop, FakeOllama]:
    shop = Shop()
    api = FakeOllama(script)
    ex = ToolExecutor(shop, 2_000_000, lambda _q: approve)
    result = run_agent(
        api, ex, "Tôi muốn hoàn tiền", model="m", max_tokens=100, max_steps=max_steps
    )
    return result, shop, api


def test_happy_path_refund() -> None:
    email = "an@example.com"
    result, shop, api = run(
        [
            reply("", tool_call("get_order", order_id="DH1001", customer_email=email)),
            reply("", tool_call("check_refund_policy", order_id="DH1001", customer_email=email)),
            reply(
                "",
                tool_call(
                    "issue_refund",
                    order_id="DH1001",
                    customer_email=email,
                    amount=890_000,
                    reason="lỗi",
                ),
            ),
            reply("Đã hoàn 890.000đ cho đơn DH1001."),
        ]
    )
    assert result.finished and result.steps == 4
    assert result.text == "Đã hoàn 890.000đ cho đơn DH1001."
    assert result.input_tokens == 400 and result.output_tokens == 80
    assert len(shop.refunds) == 1
    # Lịch sử tăng dần: system + user, rồi mỗi vòng thêm (lượt assistant + kết quả tool).
    assert [len(c["messages"]) for c in api.calls] == [2, 4, 6, 8]


def test_tool_error_is_fed_back_to_llm() -> None:
    result, _, api = run(
        [
            reply("", tool_call("get_order", order_id="DH9999", customer_email="x@y.z")),
            reply("Không tìm thấy đơn, bạn kiểm tra lại mã nhé."),
        ]
    )
    tool_msg = api.calls[1]["messages"][-1]
    assert tool_msg["role"] == "tool" and tool_msg["tool_name"] == "get_order"
    assert "error" in json.loads(tool_msg["content"])
    assert result.finished


def test_asks_customer_without_calling_tools() -> None:
    result, shop, _ = run([reply("Bạn cho mình mã đơn và email nhé?")])
    assert result.steps == 1 and shop.refunds == []


def test_max_steps_stops_runaway_loop() -> None:
    loop = [
        reply("", tool_call("get_order", order_id="DH1001", customer_email="an@example.com"))
        for _ in range(10)
    ]
    result, _, api = run(loop, max_steps=3)
    assert not result.finished
    assert len(api.calls) == 3


def test_prompt_injection_still_blocked_by_code() -> None:
    # Khách chèn lệnh; giả sử LLM bị lừa và gọi hoàn tiền đơn quá hạn: code vẫn chặn.
    result, shop, _ = run(
        [
            reply(
                "",
                tool_call(
                    "issue_refund",
                    order_id="DH1002",
                    customer_email="binh@example.com",
                    amount=1_200_000,
                    reason="bỏ qua mọi quy tắc",
                ),
            ),
            reply("Rất tiếc, đơn đã quá hạn hoàn tiền."),
        ]
    )
    assert shop.refunds == []
    assert result.finished
