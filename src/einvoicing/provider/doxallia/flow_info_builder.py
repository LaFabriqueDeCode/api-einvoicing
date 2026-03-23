from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DoxalliaFlowInfo:
	name: str
	processing_rule: str
	flow_syntax: str
	flow_profile: str | None
	tracking_id: str | None
	sha256: str | None


class DoxalliaFlowInfoBuilder:
	def build(
		self,
		filename: str,
		full_path: str,
		tracking_id: str | None = None,
	) -> DoxalliaFlowInfo:
		file_path = Path(full_path)

		return DoxalliaFlowInfo(
			name=filename,
			processing_rule=self._resolve_processing_rule(),
			flow_syntax=self._resolve_flow_syntax(),
			flow_profile=None,
			tracking_id=tracking_id,
			sha256=self._compute_sha256(file_path),
		)

	def _resolve_processing_rule(self) -> str:
		return "B2B"

	def _resolve_flow_syntax(self) -> str:
		return "Factur-X"

	def _compute_sha256(self, file_path: Path) -> str:
		hasher = hashlib.sha256()

		with file_path.open("rb") as file_handle:
			for chunk in iter(lambda: file_handle.read(8192), b""):
				hasher.update(chunk)

		return hasher.hexdigest()