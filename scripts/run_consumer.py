#!/usr/bin/env python3

from __future__ import annotations

from einvoicing.config import load_config
from einvoicing.infrastructure.database import build_dsn
from einvoicing.infrastructure.postgres.postgres_app_status_repository import (
	PostgresAppStatusRepository,
)
from einvoicing.infrastructure.postgres.postgres_invoice_history_repository import (
	PostgresInvoiceHistoryRepository,
)
from einvoicing.infrastructure.postgres.postgres_invoice_repository import (
	PostgresInvoiceRepository,
)
from einvoicing.logger import configure_logging
from einvoicing.messaging.consumer.pdf.pdf_consumer import PdfConsumer


def main() -> int:
	configure_logging()

	config = load_config()
	kafka_config = config["kafka"]

	dsn = build_dsn(config)

	history_repository = PostgresInvoiceHistoryRepository(dsn=dsn)
	invoice_repository = PostgresInvoiceRepository(dsn=dsn)
	app_status_repository = PostgresAppStatusRepository(dsn=dsn)

	ok_app_status_id = app_status_repository.get_id_by_code("OK")
	error_app_status_id = app_status_repository.get_id_by_code("ERROR")

	consumer = PdfConsumer(
		bootstrap_servers=kafka_config["bootstrap_servers"],
		topic=kafka_config["topic"],
		group_id=kafka_config["consumer_group_id"],
		history_repository=history_repository,
		invoice_repository=invoice_repository,
		ok_app_status_id=ok_app_status_id,
		error_app_status_id=error_app_status_id,
	)

	consumer.consume_forever()
	return 0


if __name__ == "__main__":
	raise SystemExit(main())