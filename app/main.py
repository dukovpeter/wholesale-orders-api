import logging

from fastapi import FastAPI

from app.api import api_router
from app.config import get_settings
from app.errors import register_error_handlers


def create_app() -> FastAPI:
    logging.basicConfig(level=get_settings().log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    app = FastAPI(
        title="Wholesale Orders API",
        description="Orders for a fruit & vegetable wholesaler: products, customers, stock reservation.",
        version="0.2.0",
    )
    register_error_handlers(app)
    app.include_router(api_router)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
