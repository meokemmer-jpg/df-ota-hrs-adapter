from pathlib import Path
import hashlib, json
from src.adapter_orchestrator import HrsAdapterOrchestrator

EVIDENCE = [{"bucket": "heylou_design", "name": "03-heylou-loc-gap.md", "path": "/Users/make/Library/CloudStorage/GoogleDrive-m.e.o.kemmer@gmail.com/Meine Ablage/nlm-library/architekt-self-audit/03-heylou-loc-gap.md"}, {"bucket": "heylou_design", "name": "2660ab88_HEYLOU_DESIGN_AUDIT_REFLEXION.md", "path": "/Users/make/Library/CloudStorage/GoogleDrive-m.e.o.kemmer@gmail.com/Meine Ablage/Claude-Knowledge-System/branch-hub/nlm-nightly-chats/2026-05-18/phase-a-tagesthemen/2660ab88_HEYLOU_DESIGN_AUDIT_REFLEXION.md"}, {"bucket": "lexvance", "name": "43831c12_LexVance_14_-_Handelsrecht_Spezial_REFLEXION.md", "path": "/Users/make/Library/CloudStorage/GoogleDrive-m.e.o.kemmer@gmail.com/Meine Ablage/Claude-Knowledge-System/branch-hub/nlm-nightly-chats/2026-05-18/phase-a-tagesthemen/43831c12_LexVance_14_-_Handelsrecht_Spezial_REFLEXION.md"}, {"bucket": "lexvance", "name": "43831c12_LexVance_14_-_Handelsrecht_Spezial.md", "path": "/Users/make/Library/CloudStorage/GoogleDrive-m.e.o.kemmer@gmail.com/Meine Ablage/Claude-Knowledge-System/branch-hub/nlm-nightly-chats/2026-05-18/phase-a-tagesthemen/43831c12_LexVance_14_-_Handelsrecht_Spezial.md"}, {"bucket": "decisions_recent", "name": "DC-SELF-BOOTSTRAP-GENESIS-2026-05-18.md", "path": "/Users/make/Library/CloudStorage/GoogleDrive-m.e.o.kemmer@gmail.com/Meine Ablage/docs/decision-cards/DC-SELF-BOOTSTRAP-GENESIS-2026-05-18.md"}, {"bucket": "decisions_recent", "name": "DC-MEGA-WARGAME-3-PLAENE-2026-05-18.md", "path": "/Users/make/Library/CloudStorage/GoogleDrive-m.e.o.kemmer@gmail.com/Meine Ablage/docs/decision-cards/DC-MEGA-WARGAME-3-PLAENE-2026-05-18.md"}]
API_GATE = {"apple_developer": {"url": "https://developer.apple.com/app-store/review/guidelines/", "http_code": "200"}, "microsoft_store": {"url": "https://learn.microsoft.com/en-us/windows/apps/publish/", "http_code": "200"}, "eur_lex": {"url": "https://eur-lex.europa.eu/", "http_code": "202"}}
PATTERNS = {"wet_reproduction": "guest/partner feedback changes evidence expectations", "dry_reproduction": "same manifest schema and hash discipline across OTA adapters", "gesellschaftlich": "HeyLou trust and store-readiness proof", "zivilisatorisch": "LexVance legal/audit trace proof"}

def sha(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def test_store_legal_evidence_manifest_is_signed_complete_and_deterministic(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    orch = HrsAdapterOrchestrator(tenant_id="hildesheim")
    report = orch.run(hotel_id="hildesheim", dry_run=True)
    signed = [r for r in orch.audit.read_recent(limit=50) if r.verify_signature()]
    contract = [r for r in signed if r.event_type == "canonical_contract_event"]
    manifest = {
        "df_id": orch.DF_ID,
        "tenant_id": orch.tenant_id,
        "loop_id": report.loop_id,
        "sandbox_mode": report.sandbox_mode,
        "final_status": report.final_status,
        "required_store_surfaces": ["apple_developer", "microsoft_store"],
        "required_legal_surfaces": ["eur_lex"],
        "knowledge_buckets": sorted({e["bucket"] for e in EVIDENCE}),
        "knowledge_evidence": EVIDENCE,
        "public_api_gate": API_GATE,
        "growth_patterns": PATTERNS,
        "signed_audit_events": [r.event_type for r in signed],
        "canonical_contract_hashes": [r.payload["payload_hash"] for r in contract],
    }
    manifest["manifest_sha256"] = sha({k: v for k, v in manifest.items() if k != "manifest_sha256"})
    out = Path("runs/evidence") / f"store-legal-evidence-{report.loop_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    loaded = json.loads(out.read_text())
    assert loaded["final_status"] in ("complete", "partial")
    assert loaded["sandbox_mode"] is True
    assert loaded["knowledge_buckets"] == ["decisions_recent", "heylou_design", "lexvance"]
    assert set(loaded["growth_patterns"]) == {"wet_reproduction", "dry_reproduction", "gesellschaftlich", "zivilisatorisch"}
    assert all(v["http_code"] in ("200", "202") for v in loaded["public_api_gate"].values())
    assert loaded["signed_audit_events"].count("canonical_contract_event") == 1
    assert len(loaded["canonical_contract_hashes"]) == 1
    assert loaded["manifest_sha256"] == sha({k: v for k, v in loaded.items() if k != "manifest_sha256"})
