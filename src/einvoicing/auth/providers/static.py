from __future__ import annotations

import logging

from einvoicing.auth.jwt_token import JwtToken
from einvoicing.auth.jwt_token_provider import JwtTokenProvider

logger = logging.getLogger(__name__)


class StaticJwtTokenProvider(JwtTokenProvider):
	def __init__(self, token: str = "dummy-token") -> None:
		super().__init__()
		self._cached_token = JwtToken(
			access_token=token,
			expires_at=None,
		)

	def _fetch_token(self) -> JwtToken:
		logger.debug("Using static JWT token")

		if self._cached_token is None:
			raise RuntimeError("Static JWT token is not initialized")

		return self._cached_token