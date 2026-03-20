from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import httpx

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

	def fetch_document(self, document_id: str) -> dict[str, Any]:
		token = self._token_provider.get_token()

		params = {
			"trackingId": document_id,
		}

		headers = {
			"Authorization": f"Bearer {token}",
		}

		response = self._client.get(
			self._url,
			params=params,
			headers=headers,
		)
		response.raise_for_status()

		return response.json()

	def submit_document(self, payload: dict[str, Any]) -> dict[str, Any]:
		token = self._token_provider.get_token()

		full_path = payload["full_path"]
		filename = payload["filename"]

		file_path = Path(full_path)
		if not file_path.exists():
			raise FileNotFoundError(f"File does not exist: {file_path}")

		file_bytes = file_path.read_bytes()
		sha256 = hashlib.sha256(file_bytes).hexdigest()

		headers = {
			"Authorization": f"Bearer {token}",
		}

		multipart_fields: list[tuple[str, tuple[str | None, str | bytes, str | None]]] = [
			("flowInfo[name]", (None, filename, None)),
			("flowInfo[processingRule]", (None, payload["processing_rule"], None)),
			("flowInfo[flowSyntax]", (None, payload["flow_syntax"], None)),
			("flowInfo[trackingId]", (None, payload.get("tracking_id") or "", None)),
			("flowInfo[sha256]", (None, sha256, None)),
			("File", (filename, file_bytes, "application/pdf")),
		]

		flow_profile = payload.get("flow_profile")
		if flow_profile is not None:
			multipart_fields.append(
				("flowInfo[flowProfile]", (None, flow_profile, None))
			)

		logger.info(
			"Submitting document to Doxallia url=%s filename=%s",
			self._url,
			filename,
		)

		response = self._client.post(
			self._url,
			headers=headers,
			files=multipart_fields,
		)

		logger.info(
			"Doxallia submit response status=%s body=%s",
			response.status_code,
			response.text,
		)

		response.raise_for_status()
		return response.json()

	def close(self) -> None:
		self._client.close()