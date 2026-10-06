from common.config import app_dir, config_path
from common.payos_client import PayOSClient, sign
from common.store import Store


def test_dev_paths_live_under_local() -> None:
    assert app_dir(dev=True).name == ".local"
    assert config_path(dev=True).parent == app_dir(dev=True)


def test_webhook_signature_roundtrip() -> None:
    client = PayOSClient("mock")
    payload = client.build_webhook(1001, 100000)
    assert client.verify_webhook(payload)
    payload["data"]["amount"] = 1
    assert not client.verify_webhook(payload)


def test_sign_is_order_independent() -> None:
    assert sign({"a": 1, "b": 2}, "k") == sign({"b": 2, "a": 1}, "k")


def test_store_balance_and_orders() -> None:
    store = Store()
    store.seed()
    store.add_txn("alice", "topup", 10)
    assert store.balance("alice") == 110
    assert store.next_order_code() == 1001
