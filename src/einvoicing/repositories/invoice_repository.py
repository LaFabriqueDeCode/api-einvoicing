from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from einvoicing.domain.invoice import Invoice


@dataclass(frozen=True, slots=True)
class SaveInvoiceResult:
	invoice_id: int
	created: bool


class InvoiceRepository(ABC):
	@abstractmethod
	def save(self, invoice: Invoice) -> SaveInvoiceResult:
		pass

	@abstractmethod
	def update_app_status(
		self,
		invoice_id: int,
		app_status_id: int,
	) -> None:
		pass

	@abstractmethod
	def update_provider_and_app_status(
		self,
		invoice_id: int,
		provider_status_id: int,
		app_status_id: int,
	) -> None:
		pass