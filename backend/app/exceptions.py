from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound


class AppError(Exception):
    """Application-level business logic error."""

    def __init__(self, message: str, code: str, status_code: int = 400) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def _error_response(status_code: int, detail: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "code": code},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.message, exc.code)

    @app.exception_handler(NoResultFound)
    async def no_result_handler(request: Request, exc: NoResultFound) -> JSONResponse:
        return _error_response(404, "The requested resource was not found.", "NOT_FOUND")

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        # Surface readable message — services handle specific cases before DB raises
        detail = str(exc.orig) if exc.orig else "A database integrity constraint was violated."
        return _error_response(409, detail, "INTEGRITY_ERROR")

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Don't leak stack traces in production
        return _error_response(500, "An unexpected internal error occurred.", "INTERNAL_ERROR")
