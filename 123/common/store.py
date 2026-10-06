"""Ví coin lưu SQLite. Dùng chung cho agent, evaluator và (buổi 3) API server."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

SEED_USERS: dict[str, tuple[str, int]] = {
    # user_id: (role, số dư coin ban đầu)
    "alice": ("user", 100),
    "bob": ("user", 50),
    "admin": ("admin", 0),
}


@dataclass
class Order:
    order_code: int
    user_id: str
    amount_vnd: int
    promo_code: str | None
    status: str


class Store:
    def __init__(self, path: str = ":memory:") -> None:
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users(
                user_id TEXT PRIMARY KEY, role TEXT NOT NULL, balance INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS txns(
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                type TEXT NOT NULL, delta INTEGER NOT NULL, note TEXT NOT NULL DEFAULT '');
            CREATE TABLE IF NOT EXISTS orders(
                order_code INTEGER PRIMARY KEY, user_id TEXT NOT NULL, amount_vnd INTEGER NOT NULL,
                promo_code TEXT, status TEXT NOT NULL);
            """
        )

    def seed(self, overrides: dict[str, int] | None = None) -> None:
        for user_id, (role, balance) in SEED_USERS.items():
            balance = (overrides or {}).get(user_id, balance)
            self.db.execute(
                "INSERT OR IGNORE INTO users(user_id, role, balance) VALUES (?,?,?)",
                (user_id, role, balance),
            )
        self.db.commit()

    def role(self, user_id: str) -> str:
        row = self.db.execute("SELECT role FROM users WHERE user_id=?", (user_id,)).fetchone()
        return str(row["role"]) if row else "user"

    def balance(self, user_id: str) -> int:
        row = self.db.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            raise KeyError(f"Không có người dùng {user_id}")
        return int(row["balance"])

    def add_txn(self, user_id: str, type_: str, delta: int, note: str = "") -> int:
        self.db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, user_id)
        )
        cur = self.db.execute(
            "INSERT INTO txns(user_id, type, delta, note) VALUES (?,?,?,?)",
            (user_id, type_, delta, note),
        )
        self.db.commit()
        return int(cur.lastrowid or 0)

    def txns(self, user_id: str | None = None) -> list[dict[str, Any]]:
        sql, args = "SELECT * FROM txns", ()
        if user_id:
            sql, args = sql + " WHERE user_id=?", (user_id,)
        return [dict(r) for r in self.db.execute(sql + " ORDER BY id", args)]

    def create_order(self, order: Order) -> None:
        self.db.execute(
            "INSERT INTO orders(order_code, user_id, amount_vnd, promo_code, status)"
            " VALUES (?,?,?,?,?)",
            (order.order_code, order.user_id, order.amount_vnd, order.promo_code, order.status),
        )
        self.db.commit()

    def get_order(self, order_code: int) -> Order | None:
        row = self.db.execute("SELECT * FROM orders WHERE order_code=?", (order_code,)).fetchone()
        return Order(**dict(row)) if row else None

    def orders(self, status: str | None = None) -> list[Order]:
        sql, args = "SELECT * FROM orders", ()
        if status:
            sql, args = sql + " WHERE status=?", (status,)
        return [Order(**dict(r)) for r in self.db.execute(sql + " ORDER BY order_code", args)]

    def set_order_status(self, order_code: int, status: str) -> None:
        self.db.execute("UPDATE orders SET status=? WHERE order_code=?", (status, order_code))
        self.db.commit()

    def next_order_code(self) -> int:
        row = self.db.execute("SELECT MAX(order_code) AS m FROM orders").fetchone()
        return int(row["m"] or 1000) + 1
