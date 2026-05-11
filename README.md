# df-ota-hrs-adapter [CRUX-MK]

**Welle-37 HeyLou-Mosaic-Adapter fuer HRS OTA (DACH-Geschaeftsreise-Spezialist).**

16. Foundation-DF im Kemmer-System (NEU Welle-37).

## Zweck

Connector fuer HRS-Connect-API:
- Inventory-Query (Verfuegbarkeit)
- Rate-Push (Tarif-Updates) + Tarif-Verhandlung-Engine
- Booking-Pull + Webhook (Notifications)
- 13%-Kommission-Tracker pro Booking

## Vendor-API-Pattern

- HRS-Connect-API (Inventory + Bookings + Rate-Verhandlung)
- Hotelier-Login + Token-Service (statt Direktes API-Key)
- Webhook (Notifications mit HMAC-SHA256 Verification)
- Token-Service-basiertes Refresh-Pattern

## Default-Mode: Sandbox

ENV-Var `DF_OTA_HRS_REAL_ENABLED=false` (default) → Mock-Daten.

Real-Mode erfordert:
- `DF_OTA_HRS_REAL_ENABLED=true`
- `HRS_HOTELIER_ID` + `HRS_API_KEY` (Token vom Token-Service)
- `DF_OTA_HRS_PHRONESIS_TICKET` (fuer Push-Operations + Rate-Verhandlung)

## Module

- `src/hrs_adapter.py` — HRS-Connect-API + Tarif-Verhandlung-Engine + 13% Commission-Tracker
- `src/hrs_auth.py` — Hotelier-Login + Token-Service-Pattern, ENV-Var-gated
- `src/hrs_webhook.py` — Booking-Notification-Receiver + HMAC-SHA256
- `src/commission_tracker.py` — Pro-Booking Commission-Records + Aggregat-Reports
- `src/adapter_orchestrator.py` — LaunchAgent-Entry-Point
- `src/audit_logger.py` — HMAC-SHA256-signed audit-entries (JSONL append-only)

## Tests

`tests/test_hrs_adapter.py` — 27+ Tests (Adapter + Auth + Webhook + Tracker + Orchestrator + AuditLogger).

```bash
cd df-ota-hrs-adapter
PYTHONPATH=. python -m pytest tests/ -v
```

## Run via LaunchAgent

```bash
cp scripts/com.kemmer.df-ota-hrs-adapter.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.kemmer.df-ota-hrs-adapter.plist
```

LaunchAgent: `RunAtLoad=true` + `StartInterval=7200` (2h).

## K11-K16 Compliance

- **K11:** Cascade-Containment via try/except + LC4 idempotent
- **K12:** Provenance via frozen dataclass + source-tracking
- **K13:** PAV via env_tag + vendor_api anchor
- **K14:** Override via single_command + martin_review weekly
- **K15:** Entropy ~700 LOC mit rho-Justifikation 40k EUR/J
- **K16:** Concurrent-Spawn-Mutex via mkdir-lock + pgrep

## LC1-LC5 Compliance

- **LC1:** 3 degradation_modes (full / degraded_no_real_api / standalone_mock)
- **LC2:** direct_mode_capability 0.5 (Mock-Daten ohne Real-API)
- **LC3:** Circuit-Breaker (30s timeout, 3 fails, 300s half-open)
- **LC4:** Failure-Isolation via state_externalization + idempotent_operations
- **LC5:** Health-Check standalone (keine Cross-DF-Dependencies)

## Promotion-Pfad

- **SKELETON** (jetzt) → **PRE-PRODUCTION-CONDITIONAL** (Welle-38)
- Pflicht fuer Promotion: Cross-LLM-Wargame + Failure-Injection-Pack + Real-Sandbox-Pilot

## CRUX-Bindung

- **K_0:** Sandbox-Default schuetzt vor Real-Bookings-Kosten
- **Q_0:** Cross-LLM-Wargame Pflicht vor Promotion
- **W_0:** Skeleton-Pattern aus Welle-36 PMS-Adapter wiederverwendet
- **L_Martin:** klare Mosaic-Roadmap W37→W40+

[CRUX-MK]
