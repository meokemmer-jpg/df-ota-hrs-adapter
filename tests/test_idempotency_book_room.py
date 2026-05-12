"""W41-A Idempotency-Integration-Tests fuer hrs-ota [CRUX-MK]."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from _df_common.idempotency_keys import IdempotencyStore  # noqa: E402
from _df_common.idempotency_adapter_wrapper import (  # noqa: E402
    idempotency_check,
    store_cached_response,
)
from src.hrs_adapter import HrsConnector  # noqa: E402


@pytest.fixture
def store(tmp_path):
    return IdempotencyStore(db_path=tmp_path / "idem.db")


@pytest.fixture
def adapter():
    a = HrsConnector(sandbox_mode=True)
    a.connect({"hotelier_id": "test", "api_key": "test"})
    return a


def _pull_with_idempotency(adapter, store, response_db, payload):
    result = idempotency_check(
        tenant_id=payload["hotel_id"],
        adapter_name=adapter.adapter_name,
        operation="pull_bookings",
        payload=payload,
        store=store,
        response_db=response_db,
        ttl_seconds=300,
    )
    if result.status == "duplicate" and result.cached_response is not None:
        return result.cached_response, "cached"
    bookings = adapter.pull_bookings(payload["hotel_id"], payload["since_iso"])
    response = {"bookings": bookings, "count": len(bookings)}
    store_cached_response(response_db, result.key_hash, response)
    return response, "fresh"


def test_duplicate_call_returns_cached(adapter, store, tmp_path):
    payload = {"hotel_id": "hildesheim", "since_iso": "2026-06-01T00:00:00Z"}
    response_db = tmp_path / "resp.db"
    r1, s1 = _pull_with_idempotency(adapter, store, response_db, payload)
    r2, s2 = _pull_with_idempotency(adapter, store, response_db, payload)
    assert s1 == "fresh"
    assert s2 == "cached"
    assert r1["count"] == r2["count"]


def test_different_keys_independent(adapter, store, tmp_path):
    response_db = tmp_path / "resp.db"
    p_a = {"hotel_id": "hildesheim", "since_iso": "2026-06-01T00:00:00Z"}
    p_b = {"hotel_id": "munich", "since_iso": "2026-06-01T00:00:00Z"}
    r_a, s_a = _pull_with_idempotency(adapter, store, response_db, p_a)
    r_b, s_b = _pull_with_idempotency(adapter, store, response_db, p_b)
    assert s_a == s_b == "fresh"


def test_expired_key_recomputes(adapter, store, tmp_path):
    import time as _t
    payload = {"hotel_id": "munich", "since_iso": "2026-07-01T00:00:00Z"}
    res = idempotency_check(
        tenant_id=payload["hotel_id"], adapter_name=adapter.adapter_name,
        operation="pull_bookings", payload=payload, ttl_seconds=1, store=store,
    )
    assert res.status == "fresh"
    _t.sleep(1.5)
    res2 = idempotency_check(
        tenant_id=payload["hotel_id"], adapter_name=adapter.adapter_name,
        operation="pull_bookings", payload=payload, ttl_seconds=1, store=store,
    )
    assert res2.status == "fresh"


def test_concurrent_call_safe(adapter, store, tmp_path):
    payload = {"hotel_id": "hildesheim", "since_iso": "2026-08-01T00:00:00Z"}
    statuses: list[str] = []
    lock = threading.Lock()

    def worker():
        r = idempotency_check(
            tenant_id=payload["hotel_id"], adapter_name=adapter.adapter_name,
            operation="pull_bookings", payload=payload, store=store,
        )
        with lock:
            statuses.append(r.status)

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert statuses.count("fresh") == 1
    assert statuses.count("duplicate") == 49
