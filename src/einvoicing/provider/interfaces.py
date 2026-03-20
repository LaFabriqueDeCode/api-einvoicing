from __future__ import annotations

from typing import Any, Protocol


class ProviderClientInterface(Protocol):
	def fetch_document(self, document_id: str) -> dict[str, Any]:
		...