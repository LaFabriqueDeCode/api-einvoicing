from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InvoiceBatch:
	id: int
	external_batch_id: str
	provider: str
	batch_type: str
	directory: str


class InvoiceBatchRepository(ABC):
	@abstractmethod
	def get_by_external_batch_id(self, external_batch_id: str) -> InvoiceBatch | None:
		pass

	@abstractmethod
	def create_if_not_exists(
		self,
		external_batch_id: str,
		provider: str,
		batch_type: str,
		directory: str,
	) -> InvoiceBatch:
		pass