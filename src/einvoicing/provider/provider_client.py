from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from einvoicing.context.request_context import RequestContext
from einvoicing.domain.invoice_history_event import InvoiceHistoryEvent


class ProviderClientInterface(ABC):
	@abstractmethod
	def submit(
		self,
		payload: dict[str, Any],
		context: RequestContext,
	) -> tuple[dict[str, Any], RequestContext]:
		pass

	@abstractmethod
	def map_success(
		self,
		invoice_id: int,
		response: dict[str, Any],
		app_status_id: int | None = None,
		global_request_id: str | None = None,
		provider_request_id: str | None = None,
	) -> InvoiceHistoryEvent:
		pass

	@abstractmethod
	def map_error(
		self,
		invoice_id: int,
		error: str,
		payload: dict[str, Any] | None = None,
		app_status_id: int | None = None,
		global_request_id: str | None = None,
		provider_request_id: str | None = None,
	) -> InvoiceHistoryEvent:
		pass

	@abstractmethod
	def close(self) -> None:
		pass