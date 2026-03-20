#!/usr/bin/env python3

from __future__ import annotations

import argparse
import uuid
from pathlib import Path

from einvoicing.application.pdf_scan_publisher_service import PdfScanPublisherService
from einvoicing.config import load_config
from einvoicing.logger import configure_logging
from einvoicing.messaging.producer.pdf.pdf_producer import PdfProducer


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Scan a directory and publish one Kafka message per PDF file."
	)
	parser.add_argument("directory", help="Directory to scan")
	parser.add_argument("--provider", required=True, help="Provider name")
	parser.add_argument("--batch-type", required=True, help="Batch type, for example XPR or PRO")
	parser.add_argument("--batch-id", required=False, help="Optional batch id")
	return parser.parse_args()


def main() -> int:
	configure_logging()

	args = parse_args()
	config = load_config()

	kafka_config = config["kafka"]
	scanner_config = config["scanner"]

	producer = PdfProducer(
		bootstrap_servers=kafka_config["bootstrap_servers"],
		topic=kafka_config["topic"],
	)

	service = PdfScanPublisherService(
		producer=producer,
		recursive=scanner_config.get("recursive", True),
	)

	batch_id = args.batch_id or str(uuid.uuid4())

	published_count = service.scan_and_publish(
		directory=Path(args.directory),
		provider=args.provider,
		batch_type=args.batch_type,
		batch_id=batch_id,
	)

	print(
		f"Batch accepted: batch_id={batch_id} "
		f"provider={args.provider} "
		f"batch_type={args.batch_type} "
		f"published_count={published_count}"
	)

	return 0


if __name__ == "__main__":
	raise SystemExit(main())