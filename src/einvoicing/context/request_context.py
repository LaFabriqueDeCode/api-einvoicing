from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class RequestContext:
	global_request_id: str
	provider_request_id: str | None = None

	def with_new_provider_request(self) -> "RequestContext":
		return RequestContext(
			global_request_id=self.global_request_id,
			provider_request_id=str(uuid4()),
		)