from __future__ import annotations

from dataclasses import asdict, dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class PdfMessage:
	message_id: str
	request_id: str
	invoice_id: int
	provider: str
	tracking_id: str
	filename: str
	full_path: str

	@staticmethod
	def create(
		request_id: str,
		invoice_id: int,
		provider: str,
		filename: str,
		full_path: str,
		tracking_id: str,
	) -> "PdfMessage":
		return PdfMessage(
			message_id=str(uuid4()),
			request_id=request_id,
			invoice_id=invoice_id,
			provider=provider,
			tracking_id=tracking_id,
			filename=filename,
			full_path=full_path,
		)

	def to_dict(self) -> dict:
		return asdict(self)