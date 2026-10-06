"""Tool cho agent: phần MÔ TẢ (gửi cho LLM) và phần THỰC THI (code của bạn chạy).

LLM chỉ *đề xuất* gọi tool. Hàm `ToolExecutor.execute` mới là nơi tool thật sự chạy,
và là nơi đặt các guardrail (kiểm tra tham số, xin con người duyệt).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from refund_agent.shop import Shop

logger = logging.getLogger("refund_agent.tools")

# Hàm xin con người duyệt: nhận câu hỏi, trả True/False.
ApprovalFn = Callable[[str], bool]

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_order",
        "description": (
            "Tra cứu đơn hàng. Cần CẢ mã đơn hàng và email khách hàng đúng khớp. "
            "Trả về sản phẩm, số tiền (VND), trạng thái, ngày giao."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Mã đơn, ví dụ DH1001"},
                "customer_email": {"type": "string", "description": "Email đặt hàng"},
            },
            "required": ["order_id", "customer_email"],
        },
    },
    {
        "name": "check_refund_policy",
        "description": (
            "Kiểm tra đơn hàng có đủ điều kiện hoàn tiền theo chính sách hay không. "
            "Chỉ gọi sau khi đã tra cứu đơn thành công bằng get_order."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer_email": {"type": "string"},
            },
            "required": ["order_id", "customer_email"],
        },
    },
    {
        "name": "issue_refund",
        "description": (
            "Thực hiện hoàn tiền. CHỈ gọi khi check_refund_policy trả về eligible=true. "
            "Hành động không thể hoàn tác. Số tiền lớn có thể cần nhân viên duyệt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer_email": {"type": "string"},
                "amount": {"type": "integer", "description": "Số tiền hoàn (VND)"},
                "reason": {"type": "string", "description": "Lý do hoàn tiền của khách"},
            },
            "required": ["order_id", "customer_email", "amount", "reason"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Tạo ticket chuyển cho nhân viên khi không thể tự xử lý: thiếu thông tin sau khi "
            "đã hỏi lại, yêu cầu ngoài chính sách, hoặc khách khiếu nại gay gắt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Mã đơn nếu có, nếu không để rỗng"},
                "summary": {
                    "type": "string",
                    "description": "Tóm tắt vấn đề để nhân viên nắm nhanh",
                },
            },
            "required": ["summary"],
        },
    },
]


class ToolExecutor:
    """Thực thi tool. Mỗi kết quả trả về là dict để đưa ngược lại cho LLM dưới dạng JSON."""

    def __init__(self, shop: Shop, approval_threshold: int, approve: ApprovalFn) -> None:
        self.shop = shop
        self.approval_threshold = approval_threshold
        self.approve = approve

    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        handler = getattr(self, f"_tool_{name}", None)
        if handler is None:
            return {"error": f"Không có tool tên '{name}'."}
        try:
            result: dict[str, Any] = handler(**args)
        except TypeError as exc:  # thiếu/sai tham số
            return {"error": f"Tham số không hợp lệ: {exc}"}
        return result

    # --- các tool --------------------------------------------------------
    def _tool_get_order(self, order_id: str, customer_email: str) -> dict[str, Any]:
        order = self.shop.find_order(order_id, customer_email)
        if order is None:
            return {"error": "Không tìm thấy đơn hàng khớp mã đơn và email."}
        return {
            "order_id": order.order_id,
            "item": order.item,
            "amount": order.amount,
            "status": order.status,
            "is_digital": order.is_digital,
            "delivered_on": order.delivered_on.isoformat() if order.delivered_on else None,
            "already_refunded": order.refunded,
        }

    def _tool_check_refund_policy(self, order_id: str, customer_email: str) -> dict[str, Any]:
        order = self.shop.find_order(order_id, customer_email)
        if order is None:
            return {"error": "Không tìm thấy đơn hàng khớp mã đơn và email."}
        return self.shop.evaluate_policy(order)

    def _tool_issue_refund(
        self, order_id: str, customer_email: str, amount: int, reason: str
    ) -> dict[str, Any]:
        order = self.shop.find_order(order_id, customer_email)
        if order is None:
            return {"error": "Không tìm thấy đơn hàng khớp mã đơn và email."}

        # Guardrail 1: KHÔNG tin LLM, tự kiểm tra lại chính sách trong code.
        policy = self.shop.evaluate_policy(order)
        if not policy["eligible"]:
            return {"error": f"Từ chối hoàn tiền: {policy['reason']}"}
        if amount != policy["refundable_amount"]:
            return {"error": f"Số tiền phải bằng {policy['refundable_amount']} VND."}

        # Guardrail 2: số tiền lớn cần con người duyệt (human-in-the-loop).
        if amount > self.approval_threshold:
            question = f"Duyệt hoàn {amount:,} VND cho đơn {order.order_id} ({order.item})?"
            if not self.approve(question):
                logger.warning("Người duyệt TỪ CHỐI hoàn tiền đơn %s", order.order_id)
                return {"status": "rejected_by_human", "message": "Nhân viên từ chối hoàn tiền."}
            logger.info("Người duyệt ĐỒNG Ý hoàn tiền đơn %s", order.order_id)

        record = self.shop.refund(order, amount, reason)
        return {"status": "refunded", **record}

    def _tool_escalate_to_human(self, summary: str, order_id: str = "") -> dict[str, Any]:
        return {"status": "ticket_created", **self.shop.open_ticket(order_id, summary)}
