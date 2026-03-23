from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from einvoicing.auth.jwt_token import JwtToken
from einvoicing.auth.jwt_token_provider import JwtTokenProvider


class HttpJwtTokenProvider(JwtTokenProvider):
	def __init__(
		self,
		token_url: str,
		client_id: str,
		client_secret: str,
		timeout: int = 10,
	) -> None:
		super().__init__()
		self._token_url = token_url
		self._client_id = client_id
		self._client_secret = client_secret
		self._client = httpx.Client(timeout=timeout)

	def _fetch_token(self) -> JwtToken:
		response = self._client.post(
			self._token_url,
			data={
				"client_id": self._client_id,
				"client_secret": self._client_secret,
				"grant_type": "client_credentials",
			},
		)
		response.raise_for_status()

		payload = response.json()

		expires_in = int(payload.get("expires_in", 3600))

		return JwtToken(
			access_token=payload["access_token"],
			expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
		)

	def close(self) -> None:
		self._client.close()