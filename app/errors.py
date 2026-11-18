from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST


class NotFoundError(DomainError):
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(DomainError):
    """Valid request that the current state does not allow, e.g. not enough stock."""

    status_code = status.HTTP_409_CONFLICT


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})
