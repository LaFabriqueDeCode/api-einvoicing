from __future__ import annotations

from typing import Protocol


class JwtTokenProviderInterface(Protocol):
	def get_token(self) -> str:
		...