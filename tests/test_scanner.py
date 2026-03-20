from pathlib import Path

from einvoicing.scanner import iter_pdf_files


def test_iter_pdf_files(tmp_path: Path) -> None:
    pdf_file = tmp_path / "invoice.pdf"
    txt_file = tmp_path / "notes.txt"

    pdf_file.write_text("dummy")
    txt_file.write_text("dummy")

    files = list(iter_pdf_files(tmp_path))

    assert len(files) == 1
    assert files[0].name == "invoice.pdf"