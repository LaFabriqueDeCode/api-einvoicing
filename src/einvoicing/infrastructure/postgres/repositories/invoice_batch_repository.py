from __future__ import annotations

import logging

import psycopg

from einvoicing.repositories.invoice_batch_repository import (
	InvoiceBatch,
	InvoiceBatchRepository,
)

logger = logging.getLogger(__name__)


class PostgresInvoiceBatchRepository(InvoiceBatchRepository):
	def __init__(self, dsn: str) -> None:
		self._dsn = dsn

	def get_by_external_batch_id(self, external_batch_id: str) -> InvoiceBatch | None:
		with psycopg.connect(self._dsn) as conn:
			with conn.cursor() as cur:
				cur.execute(
					"""
					SELECT id, external_batch_id, provider, batch_type, directory
					FROM invoice_batches
					WHERE external_batch_id = %s
					""",
					(external_batch_id,),
				)

				row = cur.fetchone()

		if row is None:
			return None

		return InvoiceBatch(
			id=row[0],
			external_batch_id=row[1],
			provider=row[2],
			batch_type=row[3],
			directory=row[4],
		)

	def create_if_not_exists(
		self,
		external_batch_id: str,
		provider: str,
		batch_type: str,
		directory: str,
	) -> InvoiceBatch:
		existing_batch = self.get_by_external_batch_id(external_batch_id)
		if existing_batch is not None:
			if existing_batch.provider != provider:
				raise ValueError(
					f"Batch provider mismatch for external_batch_id={external_batch_id}"
				)

			if existing_batch.batch_type != batch_type:
				raise ValueError(
					f"Batch type mismatch for external_batch_id={external_batch_id}"
				)

			return existing_batch

		with psycopg.connect(self._dsn) as conn:
			with conn.cursor() as cur:
				cur.execute(
					"""
					INSERT INTO invoice_batches (
						external_batch_id,
						provider,
						batch_type,
						directory
					)
					VALUES (%s, %s, %s, %s)
					RETURNING id, external_batch_id, provider, batch_type, directory
					""",
					(
						external_batch_id,
						provider,
						batch_type,
						directory,
					),
				)

				row = cur.fetchone()
				conn.commit()

		if row is None:
			raise RuntimeError(
				f"Failed to create batch with id={external_batch_id}"
			)

		batch = InvoiceBatch(
			id=row[0],
			external_batch_id=row[1],
			provider=row[2],
			batch_type=row[3],
			directory=row[4],
		)

		logger.info(
			"Batch created external_batch_id=%s provider=%s batch_type=%s",
			batch.external_batch_id,
			batch.provider,
			batch.batch_type,
		)

		return batch