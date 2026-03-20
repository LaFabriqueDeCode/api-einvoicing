from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Invoice:
	"""
	Domain entity representing an invoice.

	Mapped to the `invoices` table in the database.
	"""

	tracking_id: str
	provider: str
	name: str
	file_path: str
	submitted_at: datetime

	invoice_batch_id: int | None = None
	current_provider_status_id: int | None = None
	current_app_status_id: int | None = None
	id: int | None = None

	@staticmethod
	def from_file(
		provider: str,
		file_path: str,
		batch_id: int | None = None,
	) -> "Invoice":
		"""
		Create an Invoice from a file path.
		Automatically extracts tracking_id and filename.
		"""
		path = Path(file_path)

		return Invoice(
			tracking_id=path.stem,
			provider=provider,
			name=path.name,
			file_path=str(path),
			submitted_at=datetime.now(timezone.utc),
			invoice_batch_id=batch_id,
		)