from __future__ import annotations

from dataclasses import dataclass

from einvoicing.repositories.invoice_batch_repository import InvoiceBatchRepository


@dataclass(frozen=True, slots=True)
class UploadRequest:
	provider: str
	files: list[str]
	batch_id: str | None = None
	batch_type: str | None = None


@dataclass(frozen=True, slots=True)
class UploadResult:
	provider: str
	batch_id: str | None
	batch_type: str | None
	file_count: int
	status: str


class UploadOrchestrationService:
	def __init__(self, batch_repository: InvoiceBatchRepository) -> None:
		self._batch_repository = batch_repository

	def handle(self, request: UploadRequest) -> UploadResult:
		self._validate_request(request)

		if request.batch_id is not None:
			batch = self._batch_repository.get_by_batch_id(request.batch_id)

			if batch is None:
				self._batch_repository.create_if_not_exists(
					batch_id=request.batch_id,
					provider=request.provider,
					batch_type=request.batch_type,
				)
			else:
				if batch.provider != request.provider:
					raise ValueError(
						f"Batch provider mismatch for batch_id={request.batch_id}"
					)

				if batch.batch_type != request.batch_type:
					raise ValueError(
						f"Batch type mismatch for batch_id={request.batch_id}"
					)

		return UploadResult(
			provider=request.provider,
			batch_id=request.batch_id,
			batch_type=request.batch_type,
			file_count=len(request.files),
			status="accepted",
		)

	def _validate_request(self, request: UploadRequest) -> None:
		if not request.provider.strip():
			raise ValueError("provider must not be empty")

		if not request.files:
			raise ValueError("files must not be empty")

		if request.batch_id is not None and not request.batch_id.strip():
			raise ValueError("batch_id must not be empty")

		if request.batch_type is not None and not request.batch_type.strip():
			raise ValueError("batch_type must not be empty")

		if request.batch_id and not request.batch_type:
			raise ValueError("batch_type is required when batch_id is provided")

		if request.batch_type and not request.batch_id:
			raise ValueError("batch_id is required when batch_type is provided")