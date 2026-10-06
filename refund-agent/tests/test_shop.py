from datetime import date

from refund_agent.shop import Shop


def test_policy_eligible() -> None:
    shop = Shop(today=date(2026, 10, 5))
    order = shop.find_order("DH1001", "an@example.com")
    assert order is not None
    assert shop.evaluate_policy(order) == {
        "eligible": True,
        "reason": "Trong hạn hoàn tiền (10/30 ngày).",
        "refundable_amount": 890_000,
    }


def test_policy_rejections() -> None:
    shop = Shop()
    cases = {
        "DH1002": ("binh@example.com", "Quá hạn"),
        "DH1003": ("chi@example.com", "số"),
        "DH1005": ("em@example.com", "đã được hoàn"),
        "DH1006": ("phuc@example.com", "chưa giao"),
    }
    for order_id, (email, expected) in cases.items():
        order = shop.find_order(order_id, email)
        assert order is not None
        result = shop.evaluate_policy(order)
        assert result["eligible"] is False
        assert expected in result["reason"]


def test_wrong_email_hides_order() -> None:
    assert Shop().find_order("DH1001", "ke-xau@example.com") is None


def test_order_id_is_normalized() -> None:
    assert Shop().find_order(" dh1001 ", "AN@example.com") is not None
