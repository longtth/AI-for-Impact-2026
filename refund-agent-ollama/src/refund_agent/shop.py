"""Backend giả lập của cửa hàng: đơn hàng, chính sách hoàn tiền, hoàn tiền.

Đây là phần mềm TRUYỀN THỐNG (xác định, không có LLM). Agent chỉ được phép
chạm vào nó thông qua các tool trong tools.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

REFUND_WINDOW_DAYS = 30


@dataclass
class Order:
    order_id: str
    customer_email: str
    item: str
    amount: int  # VND
    status: str  # "shipped" | "delivered"
    is_digital: bool
    delivered_on: date | None = None
    refunded: bool = False


@dataclass
class Shop:
    """Cửa hàng giả lập. Dữ liệu nằm trong bộ nhớ, mỗi lần chạy tạo lại từ đầu."""

    today: date = field(default_factory=date.today)
    orders: dict[str, Order] = field(default_factory=dict)
    refunds: list[dict[str, Any]] = field(default_factory=list)
    tickets: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.orders:
            self.orders = {o.order_id: o for o in self._sample_orders()}

    def _sample_orders(self) -> list[Order]:
        def ago(days: int) -> date:
            return self.today - timedelta(days=days)

        return [
            Order(
                "DH1001",
                "an@example.com",
                "Tai nghe Bluetooth",
                890_000,
                "delivered",
                False,
                ago(10),
            ),
            Order(
                "DH1002", "binh@example.com", "Giày chạy bộ", 1_200_000, "delivered", False, ago(45)
            ),
            Order(
                "DH1003",
                "chi@example.com",
                "Khóa học lập trình online",
                1_500_000,
                "delivered",
                True,
                ago(3),
            ),
            Order(
                "DH1004",
                "dung@example.com",
                "Laptop 14 inch",
                25_000_000,
                "delivered",
                False,
                ago(5),
            ),
            Order(
                "DH1005",
                "em@example.com",
                "Bàn phím cơ",
                1_800_000,
                "delivered",
                False,
                ago(7),
                refunded=True,
            ),
            Order(
                "DH1006", "phuc@example.com", "Màn hình 27 inch", 5_500_000, "shipped", False, None
            ),
        ]

    # --- tra cứu ---------------------------------------------------------
    def find_order(self, order_id: str, customer_email: str) -> Order | None:
        """Chỉ trả đơn khi email khớp. Đây là lớp bảo vệ nằm trong code, không dựa vào prompt."""
        order = self.orders.get(order_id.strip().upper())
        if order is None or order.customer_email.lower() != customer_email.strip().lower():
            return None
        return order

    # --- chính sách ------------------------------------------------------
    def evaluate_policy(self, order: Order) -> dict[str, Any]:
        """Quy tắc hoàn tiền. Là một hàm thuần, kiểm thử bằng assert được."""
        if order.refunded:
            return {"eligible": False, "reason": "Đơn hàng này đã được hoàn tiền trước đó."}
        if order.status != "delivered" or order.delivered_on is None:
            return {
                "eligible": False,
                "reason": "Đơn hàng chưa giao nên không áp dụng hoàn tiền (có thể hủy đơn).",
            }
        if order.is_digital:
            return {"eligible": False, "reason": "Sản phẩm số không được hoàn tiền."}
        days = (self.today - order.delivered_on).days
        if days > REFUND_WINDOW_DAYS:
            return {
                "eligible": False,
                "reason": f"Quá hạn hoàn tiền: đã {days} ngày kể từ lúc giao "
                f"(tối đa {REFUND_WINDOW_DAYS} ngày).",
            }
        return {
            "eligible": True,
            "reason": f"Trong hạn hoàn tiền ({days}/{REFUND_WINDOW_DAYS} ngày).",
            "refundable_amount": order.amount,
        }

    # --- hành động có tác dụng phụ --------------------------------------
    def refund(self, order: Order, amount: int, reason: str) -> dict[str, Any]:
        record = {"order_id": order.order_id, "amount": amount, "reason": reason}
        order.refunded = True
        self.refunds.append(record)
        return record

    def open_ticket(self, order_id: str, summary: str) -> dict[str, str]:
        ticket = {
            "ticket_id": f"TK{len(self.tickets) + 1:04d}",
            "order_id": order_id,
            "summary": summary,
        }
        self.tickets.append(ticket)
        return ticket
