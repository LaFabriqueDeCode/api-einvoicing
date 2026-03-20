from __future__ import annotations

from einvoicing.auth.jwt_token import JwtToken
from einvoicing.auth.jwt_token_provider import JwtTokenProvider


class StaticJwtTokenProvider(JwtTokenProvider):
	def __init__(self, token: str = "dummy-token") -> None:
		super().__init__()
		self._token = token

	def _fetch_token(self) -> JwtToken:
		return JwtToken(
			access_token=self._token,
			expires_at=None,
		)