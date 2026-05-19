import json
from pathlib import Path
from src.canonical_pms_ota_contract import CanonicalPmsOtaContract, ContractEvent, REQUIRED_AUDIT_FIELDS
from src.adapter_orchestrator import HrsAdapterOrchestrator

SEQ = ("pms_quote_accepted","ota_hold_received","payment_auth_started",
       "payment_auth_confirmed","pms_inventory_committed","guest_notice_sent")

def test_full_eventstream_hash_parity_and_drift_rejection():
    c = CanonicalPmsOtaContract()
    rows = [c.apply(ContractEvent("hildesheim", name, "R-028",
            {"amount": 128, "currency": "EUR", "hotel_id": "hildesheim"})) for name in SEQ]
    assert c.state_by_key[("hildesheim","R-028")] == "COMPLETED"
    assert [r["to_state"] for r in rows] == ["HOLD_PLACED","PAYMENT_INITIATED","PAYMENT_CONFIRMED",
                                             "RESERVATION_LOCKED","CONFIRMATION_SENT","COMPLETED"]
    assert all(set(REQUIRED_AUDIT_FIELDS) <= set(r) and len(r["payload_hash"]) == 64 for r in rows)
    try:
        c.apply(ContractEvent("hildesheim", "guest_notice_sent", "R-028", {"amount": 999}))
    except ValueError as e:
        assert str(e).startswith("duplicate_payload_drift:")

def test_orchestrator_records_contract_quote_before_runtime_audit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    orch = HrsAdapterOrchestrator(tenant_id="hildesheim")
    report = orch.run(hotel_id="hildesheim", dry_run=True)
    assert "contract_quote" in report.phases_passed
    rows = orch.audit.read_recent(limit=20)
    contract_rows = [r for r in rows if r.event_type == "canonical_contract_event"]
    assert contract_rows and contract_rows[-1].verify_signature()
    payload = contract_rows[-1].payload
    assert payload["source_event"] == "pms_quote_accepted"
    assert payload["to_state"] == "HOLD_PLACED"
    assert Path("runs/loop-reports").exists()
