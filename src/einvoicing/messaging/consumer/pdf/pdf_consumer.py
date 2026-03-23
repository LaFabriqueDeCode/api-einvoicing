from __future__ import annotations

import logging

import httpx

from einvoicing.provider.doxallia.flow_info_builder import DoxalliaFlowInfoBuilder
from einvoicing.application.request_context import RequestContext
from einvoicing.config import load_config
from einvoicing.provider.doxallia.mappers.submission_response_mapper import (
	DoxalliaSubmissionResponseMapper,
)
from einvoicing.provider.factory import ProviderClientFactory
from einvoicing.repositories.invoice_history_repository import (
	InvoiceHistoryRepository,
)
from einvoicing.repositories.invoice_repository import InvoiceRepository
from einvoicing.utils.kafka import build_consumer

logger = logging.getLogger(__name__)


class PdfConsumer:
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
		self._doxallia_flow_info_builder = DoxalliaFlowInfoBuilder()

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

				provider = payload.get("provider")
				if not provider:
					logger.error(
						"Skipping message without provider topic=%s partition=%s offset=%s payload=%s",
						message.topic,
						message.partition,
						message.offset,
						payload,
					)
					continue

				invoice_id = payload.get("invoice_id")
				if invoice_id is None:
					logger.error(
						"Skipping message without invoice_id topic=%s partition=%s offset=%s payload=%s",
						message.topic,
						message.partition,
						message.offset,
						payload,
					)
					continue

				client = self._provider_factory.create(provider)

				try:
					if provider == "doxallia":
						context = RequestContext(
							global_request_id=payload["request_id"],
						).with_new_provider_request()

						flow_info = self._doxallia_flow_info_builder.build(
							filename=payload["filename"],
							full_path=payload["full_path"],
							tracking_id=payload.get("tracking_id"),
						)

						response = client.submit_document(
							payload=payload,
							flow_info=flow_info,
							context=context,
						)
					else:
						logger.error(
							"Unsupported provider topic=%s partition=%s offset=%s provider=%s",
							message.topic,
							message.partition,
							message.offset,
							provider,
						)
						continue

					logger.info(
						"Provider submission succeeded global_request_id=%s provider_request_id=%s invoice_id=%s provider=%s response=%s",
						context.global_request_id,
						context.provider_request_id,
						invoice_id,
						provider,
						response,
					)

					event = DoxalliaSubmissionResponseMapper.from_response(
						invoice_id=invoice_id,
						payload=response,
						app_status_id=self._ok_app_status_id,
					)

					self._history_repository.save(event)

					if self._ok_app_status_id is not None:
						self._invoice_repository.update_app_status(
							invoice_id=invoice_id,
							app_status_id=self._ok_app_status_id,
						)

				except httpx.HTTPStatusError as exc:
					logger.exception(
						"Provider submission failed invoice_id=%s provider=%s error=%s",
						invoice_id,
						provider,
						exc,
					)

					error_payload = None
					try:
						error_payload = exc.response.json()
					except Exception:
						error_payload = {"body": exc.response.text}

					event = DoxalliaSubmissionResponseMapper.from_error(
						invoice_id=invoice_id,
						error=f"Doxallia HTTP error {exc.response.status_code}",
						payload=error_payload,
						app_status_id=self._error_app_status_id,
					)

					self._history_repository.save(event)

					if self._error_app_status_id is not None:
						self._invoice_repository.update_app_status(
							invoice_id=invoice_id,
							app_status_id=self._error_app_status_id,
						)

				except Exception as exc:
					logger.exception(
						"Provider submission failed invoice_id=%s provider=%s error=%s",
						invoice_id,
						provider,
						exc,
					)

					event = DoxalliaSubmissionResponseMapper.from_error(
						invoice_id=invoice_id,
						error=str(exc),
						payload=None,
						app_status_id=self._error_app_status_id,
					)

					self._history_repository.save(event)

					if self._error_app_status_id is not None:
						self._invoice_repository.update_app_status(
							invoice_id=invoice_id,
							app_status_id=self._error_app_status_id,
						)

				logger.info(
					"Invoice history event saved topic=%s partition=%s offset=%s invoice_id=%s",
					message.topic,
					message.partition,
					message.offset,
					invoice_id,
				)

		finally:
			self._consumer.close()