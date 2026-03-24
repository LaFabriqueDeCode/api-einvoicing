from __future__ import annotations

import logging

import psycopg
from psycopg.types.json import Json

from einvoicing.domain.invoice_history_event import InvoiceHistoryEvent
from einvoicing.repositories.invoice_history_repository import InvoiceHistoryRepository

logger = logging.getLogger(__name__)


class PostgresInvoiceHistoryRepository(InvoiceHistoryRepository):
	def __init__(self, dsn: str) -> None:
		self._dsn = dsn

	def save(self, event: InvoiceHistoryEvent) -> None:
		with psycopg.connect(self._dsn) as conn:
			with conn.cursor() as cur:
				cur.execute(
					"""
					INSERT INTO invoice_history (
						invoice_id,
						provider_status_id,
						app_status_id,
						global_request_id,
						provider_request_id,
						source,
						event_type,
						event_at,
						raw_payload,
						details
					)
					VALUES (%s, %s, %s, %s, %s, %s, %s, COALESCE(%s, NOW()), %s, %s)
					""",
					(
						event.invoice_id,
						event.provider_status_id,
						event.app_status_id,
						event.global_request_id,
						event.provider_request_id,
						event.source,
						event.event_type,
						event.event_at,
						Json(event.raw_payload) if event.raw_payload is not None else None,
						event.details,
					),
				)
			conn.commit()

		logger.info(
			"Invoice history saved invoice_id=%s source=%s event_type=%s global_request_id=%s provider_request_id=%s",
			event.invoice_id,
			event.source,
			event.event_type,
			event.global_request_id,
			event.provider_request_id,
		)