from __future__ import annotations

from abc import ABC, abstractmethod


class AppStatusRepository(ABC):
	@abstractmethod
	def get_id_by_code(self, code: str) -> int:
		pass