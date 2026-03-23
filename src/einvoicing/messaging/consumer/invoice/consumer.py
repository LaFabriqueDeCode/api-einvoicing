from __future__ import annotations

import logging

import httpx

from einvoicing.config import load_config
from einvoicing.context.request_context import RequestContext
from einvoicing.provider.provider_client_factory import ProviderClientFactory
from einvoicing.repositories.invoice_history_repository import InvoiceHistoryRepository
from einvoicing.repositories.invoice_repository import InvoiceRepository
from einvoicing.messaging.kafka import build_consumer

logger = logging.getLogger(__name__)


class InvoiceConsumer:
	def __init__(
		self,
		bootstrap_servers: list[str],
		topic: str,
		group_id: str,
		history_repository: InvoiceHistoryRepository,
		invoice_repository: InvoiceRepository,
		ok_app_status_id: int | None = None,
		error_app_status_id: int | None = None,
	) -> None:
		self._consumer = build_consumer(
			bootstrap_servers=bootstrap_servers,
			topic=topic,
			group_id=group_id,
		)
		self._config = load_config()
		self._provider_factory = ProviderClientFactory(self._config)
		self._history_repository = history_repository
		self._invoice_repository = invoice_repository
		self._ok_app_status_id = ok_app_status_id
		self._error_app_status_id = error_app_status_id

	def consume_forever(self) -> None:
		logger.info("Consumer started")

		try:
			for message in self._consumer:
				payload = message.value

				logger.info(
					"Received message topic=%s partition=%s offset=%s global_request_id=%s provider=%s filename=%s full_path=%s invoice_id=%s",
					message.topic,
					message.partition,
					message.offset,
					payload.get("request_id"),
					payload.get("provider"),
					payload.get("filename"),
					payload.get("full_path"),
					payload.get("invoice_id"),
				)

				if not self._is_valid_payload(payload):
					logger.error(
						"Skipping invalid payload topic=%s partition=%s offset=%s payload=%s",
						message.topic,
						message.partition,
						message.offset,
						payload,
					)
					continue

				provider = payload["provider"]
				invoice_id = payload["invoice_id"]
				context = RequestContext(global_request_id=payload["request_id"])
				client = self._provider_factory.create(provider)

				try:
					response, provider_context = client.submit(payload, context)

					logger.info(
						"Provider submission succeeded global_request_id=%s provider_request_id=%s invoice_id=%s provider=%s response=%s",
						provider_context.global_request_id,
						provider_context.provider_request_id,
						invoice_id,
						provider,
						response,
					)

					event = client.map_success(
						invoice_id=invoice_id,
						response=response,
						app_status_id=self._ok_app_status_id,
					)

					self._history_repository.save(event)
					self._update_ok_status(invoice_id)

				except httpx.HTTPStatusError as exc:
					logger.exception(
						"Provider submission failed invoice_id=%s provider=%s error=%s",
						invoice_id,
						provider,
						exc,
					)

					try:
						error_payload = exc.response.json()
					except Exception:
						error_payload = {"body": exc.response.text}

					event = client.map_error(
						invoice_id=invoice_id,
						error=f"HTTP {exc.response.status_code}",
						payload=error_payload,
						app_status_id=self._error_app_status_id,
					)

					self._history_repository.save(event)
					self._update_error_status(invoice_id)

				except Exception as exc:
					logger.exception(
						"Provider submission failed invoice_id=%s provider=%s error=%s",
						invoice_id,
						provider,
						exc,
					)

					event = client.map_error(
						invoice_id=invoice_id,
						error=str(exc),
						payload=None,
						app_status_id=self._error_app_status_id,
					)

					self._history_repository.save(event)
					self._update_error_status(invoice_id)

				finally:
					client.close()

				logger.info(
					"Invoice history event saved topic=%s partition=%s offset=%s invoice_id=%s",
					message.topic,
					message.partition,
					message.offset,
					invoice_id,
				)

		finally:
			self._consumer.close()

	def _is_valid_payload(self, payload: dict) -> bool:
		if not payload.get("provider"):
			return False

		if payload.get("invoice_id") is None:
			return False

		if not payload.get("request_id"):
			return False

		if not payload.get("filename"):
			return False

		if not payload.get("full_path"):
			return False

		return True

	def _update_ok_status(self, invoice_id: int) -> None:
		if self._ok_app_status_id is None:
			return

		self._invoice_repository.update_app_status(
			invoice_id=invoice_id,
			app_status_id=self._ok_app_status_id,
		)

	def _update_error_status(self, invoice_id: int) -> None:
		if self._error_app_status_id is None:
			return

		self._invoice_repository.update_app_status(
			invoice_id=invoice_id,
			app_status_id=self._error_app_status_id,
		)