"""Hrs-Adapter-Orchestrator [CRUX-MK].

LaunchAgent-Entry-Point fuer Welle-37 HeyLou-Mosaic-Adapter Hrs.

Welle-37.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class LoopReport:
    loop_id: str
    df_id: str
    started_iso: str
    finished_iso: str
    sandbox_mode: bool
    final_status: str
    phases_passed: list = field(default_factory=list)
    phases_failed: list = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)
    error: Optional[str] = None


class HrsAdapterOrchestrator:
    """Orchestriert Hrs-Adapter-LaunchAgent-Run."""

    DF_ID = "df-ota-hrs-adapter"

    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id or os.environ.get("DF_OTA_HRS_TENANT_ID", "hildesheim")
        self.sandbox_mode = os.environ.get("DF_OTA_HRS_REAL_ENABLED", "false") != "true"
        from src.hrs_auth import HrsAuthManager
        from src.hrs_adapter import HrsConnector
        from src.commission_tracker import CommissionTracker
        from src.audit_logger import AuditLogger
        self.auth = HrsAuthManager(sandbox_mode=self.sandbox_mode)
        self.connector = HrsConnector(sandbox_mode=self.sandbox_mode)
        self.tracker = CommissionTracker(df_id=self.DF_ID)
        self.audit = AuditLogger(df_id=self.DF_ID)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _persist_loop_report(self, report: LoopReport) -> Optional[Path]:
        try:
            reports_dir = Path("runs/loop-reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            file_path = reports_dir / f"loop-{report.loop_id}.json"
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(asdict(report), f, indent=2, default=str)
            return file_path
        except Exception as e:
            logger.error(f"loop-report persist failed: {e}")
            return None

    def run(self, hotel_id: Optional[str] = None, dry_run: bool = False) -> LoopReport:
        loop_id = str(uuid.uuid4())[:8]
        started = self._now_iso()
        report = LoopReport(
            loop_id=loop_id, df_id=self.DF_ID, started_iso=started,
            finished_iso="", sandbox_mode=self.sandbox_mode, final_status="failed",
        )
        hotel_id = hotel_id or self.tenant_id

        try:
            # Phase 1: Auth
            creds = None
            try:
                creds = self.auth.get_credentials(self.tenant_id)
                if not self.auth.validate(creds):
                    report.phases_failed.append("auth")
                    report.error = "auth: invalid credentials"
                    self.audit.log("auth_failed", {"tenant_id": self.tenant_id, "loop_id": loop_id})
                else:
                    report.phases_passed.append("auth")
                    self.audit.log("auth_ok", {"tenant_id": self.tenant_id, "source": creds.source, "loop_id": loop_id})
            except Exception as e:
                report.phases_failed.append("auth")
                report.error = f"auth: {e}"

            if "auth" in report.phases_failed and not self.sandbox_mode:
                report.finished_iso = self._now_iso()
                report.final_status = "failed"
                self._persist_loop_report(report)
                return report

            # Phase 2: Connect
            try:
                creds_dict = {
                    "hotelier_id": creds.hotelier_id if creds else "",
                    "api_key": creds.api_key if creds else "",
                }
                if self.connector.connect(creds_dict):
                    report.phases_passed.append("connect")
                    self.audit.log("connect_ok", {"tenant_id": self.tenant_id, "loop_id": loop_id})
                else:
                    report.phases_failed.append("connect")
            except Exception as e:
                report.phases_failed.append("connect")
                logger.error(f"connect failed: {e}")

            # Phase 3: Health
            try:
                caps = self.connector.get_capabilities()
                report.artifacts["capabilities"] = caps
                report.phases_passed.append("health_check")
            except Exception as e:
                report.phases_failed.append("health_check")

            # Phase 4: Sample-Query
            if not dry_run and self.connector._connected:
                try:
                    inv = self.connector.query_inventory(hotel_id, ("2026-06-01", "2026-06-02"))
                    report.artifacts["sample_inventory_count"] = len(inv)
                    report.phases_passed.append("sample_query")
                except Exception as e:
                    report.phases_failed.append("sample_query")

            # Phase 5: Audit-Persist
            try:
                self.audit.log("loop_complete", {
                    "loop_id": loop_id,
                    "phases_passed": report.phases_passed,
                    "phases_failed": report.phases_failed,
                })
                report.phases_passed.append("audit_persist")
            except Exception as e:
                report.phases_failed.append("audit_persist")

            if not report.phases_failed:
                report.final_status = "complete"
            elif len(report.phases_passed) >= 3:
                report.final_status = "partial"
            else:
                report.final_status = "failed"
        except Exception as e:
            report.error = f"orchestrator: {e}"
            report.final_status = "failed"
        finally:
            report.finished_iso = self._now_iso()
            self._persist_loop_report(report)

        return report


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    orch = HrsAdapterOrchestrator()
    report = orch.run()
    print(f"[{orch.DF_ID}] loop_id={report.loop_id} status={report.final_status} sandbox={report.sandbox_mode}")
    sys.exit(0 if report.final_status in ("complete", "partial") else 1)


if __name__ == "__main__":
    main()
