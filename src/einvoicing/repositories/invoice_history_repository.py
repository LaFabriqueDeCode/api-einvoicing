from __future__ import annotations

from abc import ABC, abstractmethod

from einvoicing.domain.invoice_history_event import InvoiceHistoryEvent


class InvoiceHistoryRepository(ABC):
	@abstractmethod
	def save(self, event: InvoiceHistoryEvent) -> None:
		pass