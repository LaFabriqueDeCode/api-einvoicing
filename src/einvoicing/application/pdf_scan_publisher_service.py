from __future__ import annotations

import logging
from pathlib import Path

from einvoicing.models import PdfMessage
from einvoicing.scanner import iter_pdf_files
from einvoicing.messaging.producer.pdf.pdf_producer import PdfProducer

logger = logging.getLogger(__name__)


class PdfScanPublisherService:
	def __init__(
		self,
		producer: PdfProducer,
		recursive: bool = True,
	) -> None:
		self._producer = producer
		self._recursive = recursive

	def scan_and_publish(
		self,
		directory: Path,
		provider: str,
		batch_type: str,
		batch_id: str,
	) -> int:
		if not directory.exists():
			raise FileNotFoundError(f"Directory does not exist: {directory}")

		if not directory.is_dir():
			raise NotADirectoryError(f"Not a directory: {directory}")

		published_count = 0

		logger.info(
			"Starting PDF scan directory=%s provider=%s batch_type=%s batch_id=%s recursive=%s",
			directory,
			provider,
			batch_type,
			batch_id,
			self._recursive,
		)

		for pdf_path in iter_pdf_files(
			directory=directory,
			recursive=self._recursive,
		):
			tracking_id = pdf_path.stem

			message = PdfMessage.create(
				provider=provider,
				filename=pdf_path.name,
				full_path=str(pdf_path),
				tracking_id=tracking_id,
				batch_id=batch_id,
				batch_type=batch_type,
			)

			logger.info(
				"Publishing PDF message batch_id=%s batch_type=%s provider=%s tracking_id=%s filename=%s full_path=%s message_id=%s",
				batch_id,
				batch_type,
				provider,
				tracking_id,
				pdf_path.name,
				str(pdf_path),
				message.message_id,
			)

			self._producer.send(message)
			published_count += 1

		self._producer.flush()

		logger.info(
			"PDF scan completed directory=%s provider=%s batch_type=%s batch_id=%s published_count=%s",
			directory,
			provider,
			batch_type,
			batch_id,
			published_count,
		)

		return published_count