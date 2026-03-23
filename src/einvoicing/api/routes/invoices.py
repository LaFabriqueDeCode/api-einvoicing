from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from einvoicing.application.invoice_publisher_service import (
	InvoicePublisherService,
	PublishInvoiceRequest,
)
from einvoicing.config import load_config
from einvoicing.domain.exceptions import DuplicateInvoiceError
from einvoicing.infrastructure.database import build_dsn
from einvoicing.infrastructure.postgres.repositories.invoice_batch_repository import PostgresInvoiceBatchRepository
from einvoicing.infrastructure.postgres.repositories.invoice_repository import PostgresInvoiceRepository
from einvoicing.messaging.producer.invoice.producer import InvoiceProducer

router = APIRouter(prefix="/invoices")


class InvoiceFilePayload(BaseModel):
	path: str = Field(
		...,
		examples=["/var/si/factures/JN/2026/03/A000000-F20260301000000.pdf"],
	)


class CreateInvoicesPayload(BaseModel):
	provider: str = Field(..., examples=["doxallia"])
	files: list[InvoiceFilePayload] = Field(..., min_length=1)
	batch_id: Optional[str] = Field(default=None, examples=["2026030207"])
	batch_type: Optional[str] = Field(default=None, examples=["XPR"])


class PublishedInvoiceResponse(BaseModel):
	invoice_id: int
	tracking_id: str
	path: str


class CreateInvoicesResponse(BaseModel):
	provider: str
	external_batch_id: str | None
	batch_type: str | None
	count: int
	invoices: list[PublishedInvoiceResponse]


@router.post(
	"",
	response_model=CreateInvoicesResponse,
	status_code=status.HTTP_202_ACCEPTED,
)
def create_invoices(
	request: Request,
	payload: CreateInvoicesPayload,
) -> CreateInvoicesResponse:
	if payload.batch_id and not payload.batch_type:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="batch_type required when batch_id is provided",
		)

	if payload.batch_type and not payload.batch_id:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail="batch_id required when batch_type is provided",
		)

	request_id = request.headers.get("X-Request-Id") or str(uuid4())

	config = load_config()
	kafka_config = config["kafka"]

	producer = InvoiceProducer(
		bootstrap_servers=kafka_config["bootstrap_servers"],
		topic=kafka_config["topic"],
	)

	dsn = build_dsn(config)

	invoice_repository = PostgresInvoiceRepository(dsn)
	batch_repository = PostgresInvoiceBatchRepository(dsn)

	batch = None

	if payload.batch_id is not None:
		first_path = Path(payload.files[0].path).resolve()
		directory = str(first_path.parent)

		try:
			batch = batch_repository.create_if_not_exists(
				external_batch_id=payload.batch_id,
				provider=payload.provider,
				batch_type=payload.batch_type,
				directory=directory,
			)
		except ValueError as exc:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail=str(exc),
			) from exc

	service = InvoicePublisherService(
		producer=producer,
		invoice_repository=invoice_repository,
		batch_repository=batch_repository,
	)

	results: list[PublishedInvoiceResponse] = []
	errors: list[str] = []

	try:
		for item in payload.files:
			try:
				result = service.publish(
					PublishInvoiceRequest(
						request_id=request_id,
						provider=payload.provider,
						file_path=item.path,
						external_batch_id=payload.batch_id,
						batch_type=payload.batch_type,
						batch_db_id=batch.id if batch is not None else None,
					)
				)

				results.append(
					PublishedInvoiceResponse(
						invoice_id=result.invoice_id,
						tracking_id=result.tracking_id,
						path=result.full_path,
					)
				)

			except DuplicateInvoiceError as exc:
				errors.append(str(exc))

			except FileNotFoundError as exc:
				errors.append(str(exc))

			except ValueError as exc:
				errors.append(str(exc))

		if results:
			service.flush()

	finally:
		service.close()

	if errors and not results:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail={"errors": errors},
			headers={"X-Request-Id": request_id},
		)

	return CreateInvoicesResponse(
		provider=payload.provider,
		external_batch_id=payload.batch_id,
		batch_type=payload.batch_type,
		count=len(results),
		invoices=results,
	)