"""Hrs-Webhook-Handler [CRUX-MK].

Booking-Notification-Webhook-Receiver mit HMAC-SHA256-Verification
(per _df_common.stripe_hmac_verifier-Pattern).

Welle-37.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookVerificationResult:
    """Resultat der Webhook-HMAC-Verifikation."""
    valid: bool
    event_type: str
    booking_id: str
    error: Optional[str] = None


class HrsWebhookHandler:
    """HMAC-SHA256-verifizierter Booking-Notification-Receiver.

    Public API:
    - verify_signature(body, signature, timestamp) -> bool
    - parse_event(body) -> dict
    - handle_webhook(body, signature, timestamp) -> WebhookVerificationResult
    """

    REPLAY_WINDOW_S = 300  # 5 min anti-replay

    def __init__(self, secret: Optional[str] = None, sandbox_mode: Optional[bool] = None):
        if sandbox_mode is None:
            self.sandbox_mode = os.environ.get("DF_OTA_HRS_REAL_ENABLED", "false") != "true"
        else:
            self.sandbox_mode = sandbox_mode
        self.secret = secret or os.environ.get(
            "DF_OTA_HRS_WEBHOOK_SECRET", "df-ota-hrs-mock-webhook-secret"
        )

    def verify_signature(self, body: bytes, signature: str, timestamp: Optional[float] = None) -> bool:
        """HMAC-SHA256-Verify mit Constant-Time-Compare + Replay-Protection."""
        try:
            if not signature:
                return False
            # Replay-Protection
            if timestamp is not None:
                age = time.time() - timestamp
                if age > self.REPLAY_WINDOW_S:
                    logger.warning(f"[hrs-webhook] replay window exceeded: {age:.0f}s")
                    return False
            expected = hmac.new(
                self.secret.encode("utf-8"),
                body,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"[hrs-webhook] verify_signature failed: {e}")
            return False

    def parse_event(self, body: bytes) -> dict:
        """Parse Hrs-Notification Body (JSON)."""
        import json
        try:
            return json.loads(body.decode("utf-8"))
        except Exception as e:
            logger.error(f"[hrs-webhook] parse_event failed: {e}")
            return {}

    def handle_webhook(
        self,
        body: bytes,
        signature: str,
        timestamp: Optional[float] = None,
    ) -> WebhookVerificationResult:
        """End-to-End-Webhook-Handling.

        Returns WebhookVerificationResult mit valid-flag.
        """
        try:
            if not self.verify_signature(body, signature, timestamp):
                return WebhookVerificationResult(
                    valid=False, event_type="", booking_id="",
                    error="signature_invalid_or_replay",
                )
            event = self.parse_event(body)
            return WebhookVerificationResult(
                valid=True,
                event_type=event.get("event_type", "unknown"),
                booking_id=event.get("booking_id", ""),
            )
        except Exception as e:
            return WebhookVerificationResult(
                valid=False, event_type="", booking_id="", error=str(e)[:200]
            )
