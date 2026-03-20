from __future__ import annotations

from pathlib import Path
from typing import Iterator


def iter_pdf_files(directory: Path, recursive: bool = True) -> Iterator[Path]:
    iterator = directory.rglob("*") if recursive else directory.glob("*")

    for path in iterator:
        if path.is_file() and path.suffix.lower() == ".pdf":
            yield path.resolve()