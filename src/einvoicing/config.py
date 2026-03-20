from __future__ import annotations

import os
from pathlib import Path

import yaml


def load_config() -> dict:
    config_path = os.getenv("EINVOICING_CONFIG", "conf/config.yaml")
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)