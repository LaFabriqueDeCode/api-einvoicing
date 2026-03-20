from __future__ import annotations

import logging

import psycopg

from einvoicing.domain.invoice import Invoice
from einvoicing.repositories.invoice_repository import (
	InvoiceRepository,
	SaveInvoiceResult,
)

logger = logging.getLogger(__name__)


class PostgresInvoiceRepository(InvoiceRepository):
	def __init__(self, dsn: str) -> None:
		self._dsn = dsn

	def save(self, invoice: Invoice) -> SaveInvoiceResult:
		with psycopg.connect(self._dsn) as conn:
			with conn.cursor() as cur:
				cur.execute(
					"""
					INSERT INTO public.invoices (
						tracking_id,
						batch_id,
						provider,
						name,
						file_path,
						current_provider_status_id,
						current_app_status_id,
						submitted_at
					)
					VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
					ON CONFLICT DO NOTHING
					RETURNING id
					""",
					(
						invoice.tracking_id,
						invoice.invoice_batch_id,
						invoice.provider,
						invoice.name,
						invoice.file_path,
						invoice.current_provider_status_id,
						invoice.current_app_status_id,
						invoice.submitted_at,
					),
				)

				row = cur.fetchone()

				if row is not None:
					invoice_id = int(row[0])
					conn.commit()

					logger.info(
						"Invoice inserted id=%s tracking_id=%s provider=%s",
						invoice_id,
						invoice.tracking_id,
						invoice.provider,
					)

					return SaveInvoiceResult(
						invoice_id=invoice_id,
						created=True,
					)

				cur.execute(
					"""
					SELECT id
					FROM public.invoices
					WHERE provider = %s
					  AND batch_id = %s
					  AND tracking_id = %s
					""",
					(
						invoice.provider,
						invoice.invoice_batch_id,
						invoice.tracking_id,
					),
				)

				row = cur.fetchone()
				conn.commit()

		if row is None:
			raise RuntimeError(
				f"Failed to save or retrieve invoice tracking_id={invoice.tracking_id}"
			)

		invoice_id = int(row[0])

		logger.info(
			"Invoice already exists id=%s tracking_id=%s provider=%s",
			invoice_id,
			invoice.tracking_id,
			invoice.provider,
		)

		return SaveInvoiceResult(
			invoice_id=invoice_id,
			created=False,
		)

	def update_app_status(
		self,
		invoice_id: int,
		app_status_id: int,
	) -> None:
		with psycopg.connect(self._dsn) as conn:
			with conn.cursor() as cur:
				cur.execute(
					"""
					UPDATE public.invoices
					SET current_app_status_id = %s,
					    updated_at = NOW()
					WHERE id = %s
					""",
					(
						app_status_id,
						invoice_id,
					),
				)
			conn.commit()

		logger.info(
			"Invoice app status updated invoice_id=%s app_status_id=%s",
			invoice_id,
			app_status_id,
		)

	def update_provider_and_app_status(
		self,
		invoice_id: int,
		provider_status_id: int,
		app_status_id: int,
	) -> None:
		with psycopg.connect(self._dsn) as conn:
			with conn.cursor() as cur:
				cur.execute(
					"""
					UPDATE public.invoices
					SET current_provider_status_id = %s,
					    current_app_status_id = %s,
					    updated_at = NOW()
					WHERE id = %s
					""",
					(
						provider_status_id,
						app_status_id,
						invoice_id,
					),
				)
			conn.commit()

		logger.info(
			"Invoice provider/app statuses updated invoice_id=%s provider_status_id=%s app_status_id=%s",
			invoice_id,
			provider_status_id,
			app_status_id,
		)