from dataclasses import dataclass
from hashlib import sha256
import json

STATES = ("QUOTE_CREATED","HOLD_PLACED","PAYMENT_INITIATED","PAYMENT_CONFIRMED","RESERVATION_LOCKED","CONFIRMATION_SENT","COMPLETED")
EVENT_TO_TRANSITION = {
    "pms_quote_accepted": ("QUOTE_CREATED","HOLD_PLACED"),
    "ota_hold_received": ("HOLD_PLACED","PAYMENT_INITIATED"),
    "payment_auth_started": ("PAYMENT_INITIATED","PAYMENT_CONFIRMED"),
    "payment_auth_confirmed": ("PAYMENT_CONFIRMED","RESERVATION_LOCKED"),
    "pms_inventory_committed": ("RESERVATION_LOCKED","CONFIRMATION_SENT"),
    "guest_notice_sent": ("CONFIRMATION_SENT","COMPLETED"),
}
REQUIRED_AUDIT_FIELDS = ("tenant_id","source_event","external_reservation_id","to_state","payload_hash")

@dataclass(frozen=True)
class ContractEvent:
    tenant_id: str
    source_event: str
    external_reservation_id: str
    payload: dict

def payload_hash(payload):
    raw = json.dumps(payload, sort_keys=True, separators=(",",":"))
    return sha256(raw.encode("utf-8")).hexdigest()

class CanonicalPmsOtaContract:
    def __init__(self):
        self.state_by_key = {}
        self.hash_by_event_key = {}
        self.audit_rows = []

    def apply(self, event):
        if event.source_event not in EVENT_TO_TRANSITION:
            raise ValueError(f"unknown_event:{event.source_event}")
        key = (event.tenant_id, event.external_reservation_id)
        expected, target = EVENT_TO_TRANSITION[event.source_event]
        h = payload_hash(event.payload)
        event_key = key + (event.source_event,)
        previous = self.hash_by_event_key.get(event_key)
        if previous and previous != h:
            raise ValueError(f"duplicate_payload_drift:{event.tenant_id}:{event.source_event}:{event.external_reservation_id}")
        actual = self.state_by_key.get(key, "QUOTE_CREATED")
        if actual != expected:
            raise ValueError(f"invalid_transition:{event.source_event}:{actual}!={expected}")
        self.hash_by_event_key[event_key] = h
        self.state_by_key[key] = target
        row = {"tenant_id": event.tenant_id, "source_event": event.source_event,
               "external_reservation_id": event.external_reservation_id,
               "to_state": target, "payload_hash": h}
        self.audit_rows.append(row)
        return row
