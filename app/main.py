"""Entry point: creates the FastAPI app and plugs in the routers."""
from fastapi import FastAPI

app = FastAPI(
    title="Wholesale Orders API",
    description="Orders for a fruit & vegetable wholesaler: products, customers, stock and order reservation.",
    version="0.1.0",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness check used by Docker and monitoring."""
    return {"status": "ok"}
