"""Commission-Tracker fuer Hrs [CRUX-MK].

Trackt 13%-Kommission pro Booking + Aggregat-Reports.

Welle-37.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommissionRecord:
    """Single commission-record pro Booking."""
    booking_id: str
    hotel_id: str
    rate_eur: float
    commission_pct: float
    commission_eur: float
    booking_date_iso: str
    vendor: str = "hrs"


class CommissionTracker:
    """Tracker fuer OTA-Kommission pro Booking + Periodic-Aggregation.

    Public API:
    - record_booking(booking) -> CommissionRecord
    - aggregate_period(hotel_id, period) -> dict
    - export_jsonl(target_path) -> int
    """

    COMMISSION_PCT_DEFAULT = 0.13

    def __init__(self, df_id: str = "df-ota-hrs-adapter", storage_dir: str = "audit"):
        self.df_id = df_id
        self.storage_dir = Path(storage_dir)
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.storage_dir = Path(".")
        self._records: list = []

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def record_booking(self, booking: dict) -> CommissionRecord:
        """Record commission fuer Booking.

        booking: {"booking_id": str, "hotel_id": str, "rate_eur": float, "commission_pct"?: float}
        """
        try:
            rate_eur = float(booking.get("rate_eur", 0.0))
            commission_pct = float(booking.get("commission_pct", self.COMMISSION_PCT_DEFAULT))
            commission_eur = round(rate_eur * commission_pct, 2)
            record = CommissionRecord(
                booking_id=booking.get("booking_id", ""),
                hotel_id=booking.get("hotel_id", ""),
                rate_eur=rate_eur,
                commission_pct=commission_pct,
                commission_eur=commission_eur,
                booking_date_iso=booking.get("booking_date_iso", self._now_iso()),
                vendor=booking.get("vendor", "hrs"),
            )
            self._records.append(record)
            return record
        except Exception as e:
            logger.error(f"[commission-tracker] record_booking failed: {e}")
            return CommissionRecord(
                booking_id="", hotel_id="", rate_eur=0.0,
                commission_pct=0.0, commission_eur=0.0,
                booking_date_iso=self._now_iso(),
            )

    def aggregate_period(self, hotel_id: str, period: str = "monthly") -> dict:
        """Aggregate commission fuer Hotel + Period.

        Returns: {"hotel_id": str, "period": str, "bookings_count": int,
                  "total_rate_eur": float, "total_commission_eur": float}
        """
        try:
            filtered = [r for r in self._records if r.hotel_id == hotel_id]
            count = len(filtered)
            total_rate = sum(r.rate_eur for r in filtered)
            total_commission = sum(r.commission_eur for r in filtered)
            return {
                "hotel_id": hotel_id,
                "period": period,
                "bookings_count": count,
                "total_rate_eur": round(total_rate, 2),
                "total_commission_eur": round(total_commission, 2),
                "avg_commission_pct": (
                    round(total_commission / total_rate, 4) if total_rate > 0 else 0.0
                ),
                "vendor": "hrs",
            }
        except Exception as e:
            logger.error(f"[commission-tracker] aggregate_period failed: {e}")
            return {"hotel_id": hotel_id, "period": period, "error": str(e)[:200]}

    def export_jsonl(self, target_path: Optional[str] = None) -> int:
        """Export records as JSONL. Returns count written."""
        try:
            if target_path is None:
                target_path = str(self.storage_dir / f"commission-{self.df_id}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl")
            with open(target_path, "a", encoding="utf-8") as f:
                for record in self._records:
                    f.write(json.dumps(asdict(record), default=str) + "\n")
            return len(self._records)
        except Exception as e:
            logger.error(f"[commission-tracker] export_jsonl failed: {e}")
            return 0
