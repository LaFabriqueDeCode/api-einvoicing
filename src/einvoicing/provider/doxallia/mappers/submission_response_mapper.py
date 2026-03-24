from __future__ import annotations

from datetime import datetime

from einvoicing.domain.invoice_history_event import InvoiceHistoryEvent


class DoxalliaSubmissionResponseMapper:
	@staticmethod
	def from_response(
		invoice_id: int,
		payload: dict,
		app_status_id: int | None = None,
		global_request_id: str | None = None,
		provider_request_id: str | None = None,
	) -> InvoiceHistoryEvent:
		submitted_at = payload.get("submittedAt")

		event_at = None
		if submitted_at:
			event_at = datetime.fromisoformat(submitted_at)

		return InvoiceHistoryEvent(
			invoice_id=invoice_id,
			source="doxallia",
			event_type="PROVIDER_SUBMISSION_ACCEPTED",
			event_at=event_at,
			provider_status_id=None,
			app_status_id=app_status_id,
			global_request_id=global_request_id,
			provider_request_id=provider_request_id,
			raw_payload=payload,
			details=f"Doxallia submission accepted for flowId={payload.get('flowId')}",
		)

	@staticmethod
	def from_error(
		invoice_id: int,
		error: str,
		payload: dict | None = None,
		app_status_id: int | None = None,
		global_request_id: str | None = None,
		provider_request_id: str | None = None,
	) -> InvoiceHistoryEvent:
		return InvoiceHistoryEvent(
			invoice_id=invoice_id,
			source="doxallia",
			event_type="PROVIDER_SUBMISSION_FAILED",
			event_at=None,
			provider_status_id=None,
			app_status_id=app_status_id,
			global_request_id=global_request_id,
			provider_request_id=provider_request_id,
			raw_payload=payload,
			details=error,
		)