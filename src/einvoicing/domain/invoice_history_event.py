from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class InvoiceHistoryEvent:
	invoice_id: int
	source: str
	event_type: str
	event_at: datetime | None = None
	provider_status_id: int | None = None
	app_status_id: int | None = None
	raw_payload: dict[str, Any] | None = None
	details: str | None = None