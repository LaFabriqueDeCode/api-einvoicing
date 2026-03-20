from __future__ import annotations

from einvoicing.auth.static_jwt_token_provider import StaticJwtTokenProvider
from einvoicing.provider.doxallia_client import DoxalliaClient
from einvoicing.provider.exceptions import UnsupportedProviderError
from einvoicing.provider.interfaces import ProviderClientInterface


class ProviderClientFactory:
	def __init__(self, config: dict) -> None:
		self._config = config

	def create(self, provider: str) -> ProviderClientInterface:
		normalized_provider = provider.strip().lower()

		if normalized_provider == "doxallia":
			return self._build_doxallia_client()

		raise UnsupportedProviderError(f"Unsupported provider: {provider}")

	def create_from_payload(self, payload: dict) -> ProviderClientInterface:
		provider = payload.get("provider")

		if not provider:
			raise ValueError("Missing 'provider' in payload")

		return self.create(provider)

	def _build_doxallia_client(self) -> DoxalliaClient:
		provider_config = self._config["providers"]["doxallia"]
		auth_config = provider_config.get("auth", {})

		token_provider = StaticJwtTokenProvider(
			token=auth_config.get("bearer_token", "dummy-token")
		)

		return DoxalliaClient(
			base_url=provider_config["base_url"],
			token_provider=token_provider,
			timeout=provider_config.get("timeout", 10),
		)