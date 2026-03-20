from __future__ import annotations

from dataclasses import asdict, dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class PdfMessage:
	message_id: str
	invoice_id: int
	provider: str
	tracking_id: str
	filename: str
	full_path: str
	batch_id: str | None = None
	batch_type: str | None = None
	processing_rule: str | None = None
	flow_syntax: str | None = None
	flow_profile: str | None = None

	@staticmethod
	def create(
		invoice_id: int,
		provider: str,
		filename: str,
		full_path: str,
		tracking_id: str,
		batch_id: str | None = None,
		batch_type: str | None = None,
		processing_rule: str | None = None,
		flow_syntax: str | None = None,
		flow_profile: str | None = None,
	) -> "PdfMessage":
		return PdfMessage(
			message_id=str(uuid4()),
			invoice_id=invoice_id,
			provider=provider,
			tracking_id=tracking_id,
			filename=filename,
			full_path=full_path,
			batch_id=batch_id,
			batch_type=batch_type,
			processing_rule=processing_rule,
			flow_syntax=flow_syntax,
			flow_profile=flow_profile,
		)

	def to_dict(self) -> dict:
		return asdict(self)