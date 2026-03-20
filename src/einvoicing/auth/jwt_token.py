from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class JwtToken:
	access_token: str
	expires_at: datetime | None = None

	def is_expired(self, leeway_seconds: int = 30) -> bool:
		if self.expires_at is None:
			return False

		return datetime.utcnow() >= (self.expires_at - timedelta(seconds=leeway_seconds))