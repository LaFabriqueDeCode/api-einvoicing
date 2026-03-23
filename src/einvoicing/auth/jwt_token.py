from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True, slots=True)
class JwtToken:
	access_token: str
	expires_at: datetime | None = None

	def is_expired(self, leeway_seconds: int = 30) -> bool:
		if self.expires_at is None:
			return False

		now = datetime.now(timezone.utc)

		expires_at = self.expires_at
		if expires_at.tzinfo is None:
			expires_at = expires_at.replace(tzinfo=timezone.utc)

		return now >= (expires_at - timedelta(seconds=leeway_seconds))