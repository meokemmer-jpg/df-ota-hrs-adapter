
# K12+K13+K16 Trinity-CONTRARIAN 2026-05-17 (Cross-LLM-validated)
def k12_provenance(payload: bytes, key: bytes = b"df-trinity-contrarian-v1") -> dict:
    import hashlib, hmac
    return {
        "payload_hash": hashlib.sha256(payload).hexdigest(),
        "hmac_sha256": hmac.new(key, payload, hashlib.sha256).hexdigest(),
    }

def k13_anchor(payload_hash: str) -> dict:
    from datetime import datetime, timezone
    return {
        "anchor_type": "rfc3161-mock",
        "iso_ts": datetime.now(timezone.utc).isoformat(),
        "payload_hash": payload_hash,
    }

def k16_lock_or_exit(df_name: str):
    import fcntl, os, sys
    lock_path = f"/tmp/df-trinity-{df_name}.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        sys.exit(3)

from src.canonical_pms_ota_contract import CanonicalPmsOtaContract, ContractEvent, REQUIRED_AUDIT_FIELDS

def ev(name, amount=120):
    return ContractEvent("hildesheim", name, "R-025", {"amount": amount, "currency": "EUR"})

def test_canonical_happy_path_audit_fields():
    c = CanonicalPmsOtaContract()
    for name in ("pms_quote_accepted","ota_hold_received","payment_auth_started",
                 "payment_auth_confirmed","pms_inventory_committed","guest_notice_sent"):
        row = c.apply(ev(name))
        assert set(REQUIRED_AUDIT_FIELDS) <= set(row)
    assert c.state_by_key[("hildesheim","R-025")] == "COMPLETED"

def test_rejects_unknown_skip_and_payload_drift():
    c = CanonicalPmsOtaContract()
    try:
        c.apply(ev("ota_freeform_note"))
    except ValueError as e:
        assert str(e).startswith("unknown_event:")
    c.apply(ev("pms_quote_accepted", 120))
    try:
        c.apply(ev("payment_auth_started", 120))
    except ValueError as e:
        assert str(e).startswith("invalid_transition:")
    try:
        c.apply(ev("pms_quote_accepted", 999))
    except ValueError as e:
        assert str(e).startswith("duplicate_payload_drift:")
