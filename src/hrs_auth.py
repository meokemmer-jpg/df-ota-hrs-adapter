"""Hrs-Auth-Manager [CRUX-MK].

HRS Hotelier-Login + Token-Service-Pattern (HRS-Connect-API).

ENV-Var-gated: ohne HRS_HOTELIER_ID + HRS_API_KEY -> Mock-Mode.

Welle-37.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HrsCredentials:
    """Kanonische HRS-Credentials (Hotelier-Login + Token-Service)."""
    hotelier_id: str
    api_key: str
    source: str        # "env" | "mock" | "vault"
    fetched_iso: str


class HrsAuthManager:
    """Manager fuer HRS Hotelier-Login + Token-Service-Auth.

    Public API:
    - get_credentials(tenant_id) -> HrsCredentials | None
    - validate(creds) -> bool
    - refresh_if_expired(creds) -> HrsCredentials | None
    """

    MOCK_HOTELIER_ID = "mock-hotelier-hrs-2026"
    MOCK_API_KEY = "mock-api-key-hrs-property-001"

    def __init__(self, sandbox_mode: Optional[bool] = None):
        if sandbox_mode is None:
            self.sandbox_mode = os.environ.get("DF_OTA_HRS_REAL_ENABLED", "false") != "true"
        else:
            self.sandbox_mode = sandbox_mode

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_credentials(self, tenant_id: str = "hildesheim") -> Optional[HrsCredentials]:
        if self.sandbox_mode:
            return HrsCredentials(
                hotelier_id=self.MOCK_HOTELIER_ID,
                api_key=self.MOCK_API_KEY,
                source="mock",
                fetched_iso=self._now_iso(),
            )

        hotelier_id = os.environ.get("HRS_HOTELIER_ID", "")
        api_key = os.environ.get("HRS_API_KEY", "")
        if not hotelier_id or not api_key:
            logger.warning(f"[hrs-auth] missing credentials for tenant={tenant_id}")
            return None
        return HrsCredentials(
            hotelier_id=hotelier_id, api_key=api_key, source="env", fetched_iso=self._now_iso()
        )

    def validate(self, creds: Optional[HrsCredentials]) -> bool:
        if creds is None:
            return False
        if not creds.hotelier_id or not creds.api_key:
            return False
        if creds.source not in ("env", "mock", "vault"):
            return False
        return True

    def refresh_if_expired(self, creds: Optional[HrsCredentials]) -> Optional[HrsCredentials]:
        if not self.validate(creds):
            return self.get_credentials()
        try:
            fetched = datetime.fromisoformat(creds.fetched_iso)
            if datetime.now(timezone.utc) - fetched > timedelta(hours=24):
                return self.get_credentials()
        except (ValueError, TypeError):
            return self.get_credentials()
        return creds

    def is_real_mode(self) -> bool:
        return not self.sandbox_mode
