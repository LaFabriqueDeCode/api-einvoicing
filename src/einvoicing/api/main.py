from __future__ import annotations

from fastapi import APIRouter, FastAPI

from einvoicing.api.routes.invoices import router as invoices_router

API_NAME = "api-einvoicing"
API_VERSION = "v1"
INVOICES_TAG = "invoices"

API_PREFIX = f"/{API_NAME}/{API_VERSION}"


def create_app() -> FastAPI:
	app = FastAPI(
		title="API e-Invoicing",
		version="1.0.0",
		description="Service for e-invoice submission and processing",
	)

	# Main router
	api_router = APIRouter(prefix=API_PREFIX)

	# Business routes
	api_router.include_router(invoices_router, tags=[INVOICES_TAG])

	# Health endpoint
	@api_router.get("/health")
	def health() -> dict[str, str]:
		return {"status": "ok"}

	# Root endpoint
	@app.get("/")
	def root() -> dict[str, str]:
		return {
			"service": API_NAME,
			"version": API_VERSION,
		}

	app.include_router(api_router)

	return app


app = create_app()