from __future__ import annotations

from datetime import datetime

from einvoicing.domain.invoice import Invoice


class DoxalliaMapper:
	@staticmethod
	def from_api(
		payload: dict,
		provider: str,
		file_path: str,
		invoice_batch_id: int | None = None,
	) -> Invoice:
		tracking_id = payload.get("trackingId")

		if tracking_id is None or not str(tracking_id).strip():
			raise ValueError("Missing trackingId in Doxallia payload")

		return Invoice(
			tracking_id=tracking_id,
			provider=provider,
			name=payload["name"],
			file_path=file_path,
			submitted_at=datetime.fromisoformat(payload["submittedAt"]),
			invoice_batch_id=invoice_batch_id,
		)