from __future__ import annotations

import logging
from typing import Any

import httpx

from einvoicing.provider.doxallia.flow_info_builder import DoxalliaFlowInfo
from einvoicing.application.request_context import RequestContext
from einvoicing.auth.interfaces import JwtTokenProviderInterface

logger = logging.getLogger(__name__)


class DoxalliaClient:
	def __init__(
		self,
		base_url: str,
		token_provider: JwtTokenProviderInterface,
		timeout: int = 10,
	) -> None:
		self._url = base_url
		self._timeout = timeout
		self._token_provider = token_provider
		self._client = httpx.Client(timeout=timeout)

	def submit_document(
		self,
		payload: dict[str, Any],
		flow_info: DoxalliaFlowInfo,
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