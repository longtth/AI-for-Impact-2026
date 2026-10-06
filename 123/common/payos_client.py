"""Client payOS. `mock` giả lập đúng dạng request/webhook/chữ ký; `live` gọi payOS thật.

Chữ ký payOS: HMAC-SHA256 (checksum key) trên chuỗi `key=value` nối bằng `&`,
các key sắp xếp theo alphabet. Đối chiếu lại tài liệu payOS hiện hành trước khi
dùng `live` (chế độ live chưa được kiểm thử với tài khoản payOS thật).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

import httpx

log = logging.getLogger(__name__)

PAYOS_URL = "https://api-merchant.payos.vn/v2/payment-requests"
MOCK_CHECKSUM_KEY = "mock-checksum-key"


def sign(data: dict[str, Any], checksum_key: str) -> str:
    raw = "&".join(f"{k}={'' if data[k] is None else data[k]}" for k in sorted(data))
    return hmac.new(checksum_key.encode(), raw.encode(), hashlib.sha256).hexdigest()


class PayOSClient:
    def __init__(self, mode: str = "mock") -> None:
        if mode not in ("mock", "live"):
            raise ValueError(f"payos.mode không hợp lệ: {mode}")
        self.mode = mode
        self.checksum_key = (
            MOCK_CHECKSUM_KEY if mode == "mock" else os.environ.get("PAYOS_CHECKSUM_KEY", "")
        )

    def create_payment_link(
        self, order_code: int, amount_vnd: int, description: str
    ) -> dict[str, Any]:
        if self.mode == "mock":
            return {
                "code": "00",
                "desc": "success",
                "data": {
                    "orderCode": order_code,
                    "amount": amount_vnd,
                    "status": "PENDING",
                    "checkoutUrl": f"https://pay.payos.vn/web/mock-{order_code}",
                    "qrCode": f"mock-vietqr-{order_code}",
                },
            }
        body: dict[str, Any] = {
            "orderCode": order_code,
            "amount": amount_vnd,
            "description": description[:25],
            "cancelUrl": os.environ.get("PAYOS_CANCEL_URL", "http://localhost/cancel"),
            "returnUrl": os.environ.get("PAYOS_RETURN_URL", "http://localhost/return"),
        }
        body["signature"] = sign(
            {k: body[k] for k in ("amount", "cancelUrl", "description", "orderCode", "returnUrl")},
            self.checksum_key,
        )
        headers = {
            "x-client-id": os.environ["PAYOS_CLIENT_ID"],
            "x-api-key": os.environ["PAYOS_API_KEY"],
        }
        resp = httpx.post(PAYOS_URL, json=body, headers=headers, timeout=10)
        resp.raise_for_status()
        log.info("payOS tạo link cho order %s (live)", order_code)
        return dict(resp.json())

    def build_webhook(self, order_code: int, amount_vnd: int) -> dict[str, Any]:
        """Tạo payload webhook "đã thanh toán" có chữ ký (dùng cho mock và test)."""
        data = {"orderCode": order_code, "amount": amount_vnd, "code": "00", "desc": "success"}
        return {
            "code": "00",
            "desc": "success",
            "success": True,
            "data": data,
            "signature": sign(data, self.checksum_key),
        }

    def verify_webhook(self, payload: dict[str, Any]) -> bool:
        data = payload.get("data")
        signature = payload.get("signature")
        if not isinstance(data, dict) or not isinstance(signature, str):
            return False
        return hmac.compare_digest(sign(data, self.checksum_key), signature)
