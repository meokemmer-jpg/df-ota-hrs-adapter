from pathlib import Path
from src.canonical_pms_ota_contract import CanonicalPmsOtaContract, ContractEvent, payload_hash
from src.adapter_orchestrator import HrsAdapterOrchestrator

SEQ = ("pms_quote_accepted","ota_hold_received","payment_auth_started",
       "payment_auth_confirmed","pms_inventory_committed","guest_notice_sent")

def apply(contract, tenant, event, rid, payload=None):
    base = {"hotel_id": tenant, "amount": 128, "currency": "EUR"}
    if payload:
        base.update(payload)
    return contract.apply(ContractEvent(tenant, event, rid, base))

def test_chaos_replay_rejects_bad_order_unknown_event_and_payload_drift():
    c = CanonicalPmsOtaContract()
    try:
        apply(c, "hildesheim", "ota_hold_received", "R-029")
        raise AssertionError("bad order accepted")
    except ValueError as e:
        assert str(e).startswith("invalid_transition:ota_hold_received")
    try:
        apply(c, "hildesheim", "partner_cancelled_without_contract", "R-029")
        raise AssertionError("unknown event accepted")
    except ValueError as e:
        assert str(e) == "unknown_event:partner_cancelled_without_contract"
    apply(c, "hildesheim", "pms_quote_accepted", "R-029", {"amount": 128})
    try:
        apply(c, "hildesheim", "pms_quote_accepted", "R-029", {"amount": 129})
        raise AssertionError("payload drift accepted")
    except ValueError as e:
        assert str(e).startswith("duplicate_payload_drift:hildesheim:pms_quote_accepted:R-029")

def test_tenant_isolation_and_canonical_payload_hash_are_deterministic():
    c = CanonicalPmsOtaContract()
    a = {"currency": "EUR", "amount": 128, "hotel_id": "hildesheim"}
    b = {"hotel_id": "hildesheim", "amount": 128, "currency": "EUR"}
    assert payload_hash(a) == payload_hash(b)
    row_a = apply(c, "hildesheim", "pms_quote_accepted", "SHARED")
    row_b = apply(c, "karlsruhe", "pms_quote_accepted", "SHARED")
    assert row_a["to_state"] == row_b["to_state"] == "HOLD_PLACED"
    assert c.state_by_key[("hildesheim","SHARED")] == "HOLD_PLACED"
    assert c.state_by_key[("karlsruhe","SHARED")] == "HOLD_PLACED"

def test_runtime_audit_signature_survives_replay_gate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    orch = HrsAdapterOrchestrator(tenant_id="hildesheim")
    report = orch.run(hotel_id="hildesheim", dry_run=True)
    assert report.final_status in ("complete", "partial")
    rows = [r for r in orch.audit.read_recent(limit=30) if r.event_type == "canonical_contract_event"]
    assert len(rows) == 1 and rows[0].verify_signature()
    assert rows[0].payload["source_event"] == "pms_quote_accepted"
    assert Path("runs/loop-reports").is_dir()
