from __future__ import annotations

import threading
from abc import ABC, abstractmethod

from einvoicing.auth.jwt_token import JwtToken


class JwtTokenProvider(ABC):
	def __init__(self) -> None:
		self._cached_token: JwtToken | None = None
		self._lock = threading.Lock()

	def get_token(self) -> str:

		if self._cached_token is not None and not self._cached_token.is_expired():
			return self._cached_token.access_token

		with self._lock:
			if self._cached_token is None or self._cached_token.is_expired():
				self._cached_token = self._fetch_token()

		return self._cached_token.access_token

	@abstractmethod
	def _fetch_token(self) -> JwtToken:
		pass