from __future__ import annotations

import logging

import psycopg

from einvoicing.repositories.app_status_repository import AppStatusRepository

logger = logging.getLogger(__name__)


class PostgresAppStatusRepository(AppStatusRepository):
	def __init__(self, dsn: str) -> None:
		self._dsn = dsn

	def get_id_by_code(self, code: str) -> int:
		with psycopg.connect(self._dsn) as conn:
			with conn.cursor() as cur:
				cur.execute(
					"""
					SELECT id
					FROM invoice_app_statuses
					WHERE code = %s
					""",
					(code,),
				)

				row = cur.fetchone()

		if row is None:
			raise RuntimeError(f"App status not found for code={code}")

		status_id = int(row[0])

		logger.debug(
			"App status resolved code=%s id=%s",
			code,
			status_id,
		)

		return status_id