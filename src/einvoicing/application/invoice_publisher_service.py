from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from einvoicing.domain.exceptions import DuplicateInvoiceError
from einvoicing.domain.invoice import Invoice
from einvoicing.messaging.producer.invoice.producer import InvoiceProducer
from einvoicing.messaging.invoice.message import InvoiceMessage
from einvoicing.infrastructure.postgres.repositories.invoice_batch_repository import InvoiceBatchRepository
from einvoicing.infrastructure.postgres.repositories.invoice_repository import InvoiceRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PublishInvoiceRequest:
	request_id: str
	provider: str
	file_path: str
	external_batch_id: str | None = None
	batch_type: str | None = None
	batch_db_id: int | None = None


@dataclass(frozen=True, slots=True)
class PublishInvoiceResult:
	invoice_id: int
	message_id: str
	provider: str
	tracking_id: str
	filename: str
	full_path: str
	status: str


class InvoicePublisherService:
	def __init__(
		self,
		producer: InvoiceProducer,
		invoice_repository: InvoiceRepository,
		batch_repository: InvoiceBatchRepository,
	) -> None:
		self._producer = producer
		self._invoice_repository = invoice_repository
		self._batch_repository = batch_repository

	def publish(self, request: PublishInvoiceRequest) -> PublishInvoiceResult:
		file_path = Path(request.file_path).resolve()

		if not file_path.exists():
			raise FileNotFoundError(f"File does not exist: {file_path}")

		if not file_path.is_file():
			raise ValueError(f"Path is not a file: {file_path}")

		if file_path.suffix.lower() != ".pdf":
			raise ValueError(f"File is not a PDF: {file_path}")

		if request.external_batch_id is not None and request.batch_type is None:
			raise ValueError(
				"batch_type is required when external_batch_id is provided"
			)

		invoice = Invoice.from_file(
			provider=request.provider,
			file_path=str(file_path),
			batch_id=request.batch_db_id,
		)

		save_result = self._invoice_repository.save(invoice)

		if not save_result.created:
			raise DuplicateInvoiceError(
				f"Invoice already exists for provider={invoice.provider} "
				f"tracking_id={invoice.tracking_id} batch_id={request.external_batch_id}"
			)

		message = InvoiceMessage.create(
			request_id=request.request_id,
			invoice_id=save_result.invoice_id,
			provider=request.provider,
			filename=file_path.name,
			full_path=str(file_path),
			tracking_id=invoice.tracking_id,
		)

		logger.info(
			"Publishing invoice global_request_id=%s invoice_id=%s provider=%s tracking_id=%s external_batch_id=%s filename=%s",
			request.request_id,
			save_result.invoice_id,
			request.provider,
			invoice.tracking_id,
			request.external_batch_id,
			file_path.name,
		)

		self._producer.send(message)

		return PublishInvoiceResult(
			invoice_id=save_result.invoice_id,
			message_id=message.message_id,
			provider=request.provider,
			tracking_id=invoice.tracking_id,
			filename=file_path.name,
			full_path=str(file_path),
			status="accepted",
		)

	def flush(self) -> None:
		self._producer.flush()

	def close(self) -> None:
		self._producer.close()