from __future__ import annotations


class DuplicateInvoiceError(Exception):
	"""Raised when trying to create an invoice that already exists."""
	pass