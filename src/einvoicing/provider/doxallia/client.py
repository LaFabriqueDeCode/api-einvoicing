from __future__ import annotations

import logging
from typing import Any

import httpx

from einvoicing.auth.jwt_token_provider import JwtTokenProvider
from einvoicing.context.request_context import RequestContext
from einvoicing.domain.invoice_history_event import InvoiceHistoryEvent
from einvoicing.provider.doxallia.flow_info_builder import DoxalliaFlowInfoBuilder
from einvoicing.provider.doxallia.mappers.submission_response_mapper import DoxalliaSubmissionResponseMapper
from einvoicing.provider.provider_client import ProviderClientInterface

logger = logging.getLogger(__name__)


class DoxalliaClient(ProviderClientInterface):
	def __init__(
		self,
		base_url: str,
		token_provider: JwtTokenProvider,
		timeout: int = 10,
	) -> None:
		self._url = base_url
		self._timeout = timeout
		self._token_provider = token_provider
		self._client = httpx.Client(timeout=timeout)
		self._flow_builder = DoxalliaFlowInfoBuilder()

	def submit(
		self,
		payload: dict[str, Any],
		context: RequestContext,
	) -> tuple[dict[str, Any], RequestContext]:
		provider_context = context.with_new_provider_request()
		flow_info = self._flow_builder.build(
			filename=payload["filename"],
			full_path=payload["full_path"],
			tracking_id=payload.get("tracking_id"),
		)

		response = self.submit_document(
			payload=payload,
			flow_info=flow_info,
			context=provider_context,
		)

		return response, provider_context

	def map_success(
		self,
		invoice_id: int,
		response: dict[str, Any],
		app_status_id: int | None = None,
		global_request_id: str | None = None,
		provider_request_id: str | None = None,
	) -> InvoiceHistoryEvent:
		return DoxalliaSubmissionResponseMapper.from_response(
			invoice_id=invoice_id,
			payload=response,
			app_status_id=app_status_id,
			global_request_id=global_request_id,
			provider_request_id=provider_request_id,
		)

	def map_error(
		self,
		invoice_id: int,
		error: str,
		payload: dict[str, Any] | None = None,
		app_status_id: int | None = None,
		global_request_id: str | None = None,
		provider_request_id: str | None = None,
	) -> InvoiceHistoryEvent:
		return DoxalliaSubmissionResponseMapper.from_error(
			invoice_id=invoice_id,
			error=error,
			payload=payload,
			app_status_id=app_status_id,
			global_request_id=global_request_id,
			provider_request_id=provider_request_id,
		)

	def submit_document(
		self,
		payload: dict[str, Any],
		flow_info,
		context: RequestContext,
	) -> dict[str, Any]:
		token = self._token_provider.get_token()

		headers = {
			"Authorization": f"Bearer {token}",
		}

		if context.provider_request_id:
			headers["X-Request-Id"] = context.provider_request_id

		logger.info(
			"Submitting document to Doxallia global_request_id=%s provider_request_id=%s url=%s filename=%s",
			context.global_request_id,
			context.provider_request_id,
			self._url,
			flow_info.name,
		)

		file_handle = open(payload["full_path"], "rb")

		files = {
			"File": (
				flow_info.name,
				file_handle,
				"application/pdf",
			)
		}

		data = {
			"flowInfo[name]": flow_info.name,
			"flowInfo[processingRule]": flow_info.processing_rule,
			"flowInfo[flowSyntax]": flow_info.flow_syntax,
		}

		if flow_info.flow_profile:
			data["flowInfo[flowProfile]"] = flow_info.flow_profile

		if flow_info.tracking_id:
			data["flowInfo[trackingId]"] = flow_info.tracking_id

		if flow_info.sha256:
			data["flowInfo[sha256]"] = flow_info.sha256

		try:
			response = self._client.post(
				self._url,
				headers=headers,
				data=data,
				files=files,
			)

			logger.info(
				"Doxallia submit response global_request_id=%s provider_request_id=%s status=%s body=%s",
				context.global_request_id,
				context.provider_request_id,
				response.status_code,
				response.text,
			)

			response.raise_for_status()

			return response.json()

		finally:
			file_handle.close()

	def close(self) -> None:
		self._client.close()