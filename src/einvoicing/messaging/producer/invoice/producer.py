from __future__ import annotations

import logging

from einvoicing.messaging.invoice.message import InvoiceMessage
from einvoicing.messaging.kafka import build_producer

logger = logging.getLogger(__name__)


class InvoiceProducer:
	def __init__(self, bootstrap_servers: list[str], topic: str) -> None:
		self._topic = topic
		self._producer = build_producer(bootstrap_servers)

	def send(self, message: InvoiceMessage) -> None:
		future = self._producer.send(self._topic, value=message.to_dict())
		metadata = future.get(timeout=10)

		logger.info(
			"Sent message topic=%s partition=%s offset=%s filename=%s full_path=%s",
			metadata.topic,
			metadata.partition,
			metadata.offset,
			message.filename,
			message.full_path,
		)

	def flush(self) -> None:
		self._producer.flush()

	def close(self) -> None:
		self._producer.close()