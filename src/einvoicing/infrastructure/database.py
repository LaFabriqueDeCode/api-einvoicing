from __future__ import annotations
from urllib.parse import quote_plus


def build_dsn(config: dict) -> str:
	db = config.get("database", {})

	required_keys = ["user", "password", "host", "port", "dbname"]
	missing = [k for k in required_keys if k not in db]

	if missing:
		raise ValueError(f"Missing database config keys: {missing}")

	password = quote_plus(db["password"])

	return (
		f"postgresql://{db['user']}:{password}"
		f"@{db['host']}:{db['port']}/{db['dbname']}"
	)