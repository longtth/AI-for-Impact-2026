from refund_agent.shop import Shop
from refund_agent.tools import ToolExecutor


def make(approve: bool = True) -> tuple[ToolExecutor, Shop, list[str]]:
    shop = Shop()
    asked: list[str] = []

    def approver(q: str) -> bool:
        asked.append(q)
        return approve

    return ToolExecutor(shop, 2_000_000, approver), shop, asked


def test_small_refund_needs_no_approval() -> None:
    ex, shop, asked = make()
    r = ex.execute(
        "issue_refund",
        {
            "order_id": "DH1001",
            "customer_email": "an@example.com",
            "amount": 890_000,
            "reason": "lỗi",
        },
    )
    assert r["status"] == "refunded"
    assert asked == []
    assert len(shop.refunds) == 1


def test_large_refund_requires_approval_and_can_be_rejected() -> None:
    ex, shop, asked = make(approve=False)
    r = ex.execute(
        "issue_refund",
        {
            "order_id": "DH1004",
            "customer_email": "dung@example.com",
            "amount": 25_000_000,
            "reason": "lỗi",
        },
    )
    assert r["status"] == "rejected_by_human"
    assert len(asked) == 1
    assert shop.refunds == []


def test_llm_cannot_bypass_policy() -> None:
    # LLM "quên" kiểm tra chính sách và gọi thẳng issue_refund cho đơn quá hạn.
    ex, shop, _ = make()
    r = ex.execute(
        "issue_refund",
        {
            "order_id": "DH1002",
            "customer_email": "binh@example.com",
            "amount": 1_200_000,
            "reason": "muốn trả",
        },
    )
    assert "Từ chối" in r["error"]
    assert shop.refunds == []


def test_llm_cannot_inflate_amount() -> None:
    ex, shop, _ = make()
    r = ex.execute(
        "issue_refund",
        {
            "order_id": "DH1001",
            "customer_email": "an@example.com",
            "amount": 9_999_999,
            "reason": "x",
        },
    )
    assert "error" in r
    assert shop.refunds == []


def test_double_refund_blocked() -> None:
    ex, shop, _ = make()
    args = {
        "order_id": "DH1001",
        "customer_email": "an@example.com",
        "amount": 890_000,
        "reason": "x",
    }
    assert ex.execute("issue_refund", args)["status"] == "refunded"
    assert "error" in ex.execute("issue_refund", args)
    assert len(shop.refunds) == 1


def test_unknown_tool_and_bad_args_return_errors() -> None:
    ex, _, _ = make()
    assert "error" in ex.execute("delete_everything", {})
    assert "error" in ex.execute("get_order", {"order_id": "DH1001"})


def test_escalate_creates_ticket() -> None:
    ex, shop, _ = make()
    r = ex.execute("escalate_to_human", {"summary": "khách gay gắt"})
    assert r["status"] == "ticket_created"
    assert len(shop.tickets) == 1


def test_amount_given_as_string_is_normalized() -> None:
    # Model local nhỏ hay trả số dưới dạng chuỗi.
    ex, shop, _ = make()
    r = ex.execute(
        "issue_refund",
        {
            "order_id": "DH1001",
            "customer_email": "an@example.com",
            "amount": "890000",
            "reason": "x",
        },
    )
    assert r["status"] == "refunded"
    assert len(shop.refunds) == 1


def test_amount_not_a_number_returns_error() -> None:
    ex, shop, _ = make()
    r = ex.execute(
        "issue_refund",
        {
            "order_id": "DH1001",
            "customer_email": "an@example.com",
            "amount": "tám trăm",
            "reason": "x",
        },
    )
    assert "error" in r
    assert shop.refunds == []
