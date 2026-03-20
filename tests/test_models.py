from einvoicing.models import PdfMessage


def test_pdf_message_to_dict() -> None:
    message = PdfMessage(
        filename="invoice.pdf",
        full_path="/tmp/invoice.pdf",
    )

    assert message.to_dict() == {
        "filename": "invoice.pdf",
        "full_path": "/tmp/invoice.pdf",
    }