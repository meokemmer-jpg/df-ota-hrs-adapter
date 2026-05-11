"""df-ota-hrs-adapter [CRUX-MK].

Welle-37 HeyLou-Mosaic-Adapter fuer HRS OTA (DACH-Geschaeftsreise-Spezialist).

LAZY-IMPORT-PATTERN: Module werden bei Bedarf importiert.
"""

from __future__ import annotations

__version__ = "0.1.0-SKELETON"
__df_id__ = "df-ota-hrs-adapter"
__welle__ = "welle-37"


def get_connector():
    from src.hrs_adapter import HrsConnector
    return HrsConnector


def get_auth_manager():
    from src.hrs_auth import HrsAuthManager
    return HrsAuthManager


def get_webhook_handler():
    from src.hrs_webhook import HrsWebhookHandler
    return HrsWebhookHandler


def get_commission_tracker():
    from src.commission_tracker import CommissionTracker
    return CommissionTracker


def get_orchestrator():
    from src.adapter_orchestrator import HrsAdapterOrchestrator
    return HrsAdapterOrchestrator


def get_audit_logger():
    from src.audit_logger import AuditLogger
    return AuditLogger


__all__ = [
    "__version__",
    "__df_id__",
    "__welle__",
    "get_connector",
    "get_auth_manager",
    "get_webhook_handler",
    "get_commission_tracker",
    "get_orchestrator",
    "get_audit_logger",
]
