from __future__ import annotations

import json
import sys
from pathlib import Path


def _import_kafka_python():
	project_root = Path(__file__).resolve().parents[3]
	original_sys_path = list(sys.path)

	try:
		filtered_sys_path: list[str] = []

		for entry in sys.path:
			resolved_entry = Path(entry or ".").resolve()
			if resolved_entry == project_root:
				continue
			filtered_sys_path.append(entry)

		sys.path = filtered_sys_path

		from kafka import KafkaConsumer, KafkaProducer  # type: ignore

		return KafkaConsumer, KafkaProducer
	finally:
		sys.path = original_sys_path


KafkaConsumer, KafkaProducer = _import_kafka_python()


def build_producer(bootstrap_servers: list[str]) -> KafkaProducer:
	return KafkaProducer(
		bootstrap_servers=bootstrap_servers,
		value_serializer=lambda value: json.dumps(value).encode("utf-8"),
		acks="all",
		retries=3,
	)


def build_consumer(
	bootstrap_servers: list[str],
	topic: str,
	group_id: str,
) -> KafkaConsumer:
	return KafkaConsumer(
		topic,
		bootstrap_servers=bootstrap_servers,
		group_id=group_id,
		auto_offset_reset="earliest",
		enable_auto_commit=True,
		value_deserializer=lambda message: json.loads(message.decode("utf-8")),
	)