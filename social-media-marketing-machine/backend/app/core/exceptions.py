"""Custom exception hierarchy + FastAPI exception handlers.

Routers/services raise these typed exceptions instead of calling
``raise HTTPException(...)`` directly. This keeps the service/repository
layer framework-agnostic (they don't import FastAPI) while still producing
consistent, well-shaped HTTP error responses once the exception bubbles up
to ``create_app()``'s registered handlers.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for all typed application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: Optional[str] = None, *, details: Optional[dict[str, Any]] = None) -> None:
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "The requested resource was not found."


class ValidationAppError(AppError):
    status_code = 422
    default_message = "Validation failed."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    default_message = "The request conflicts with existing state."


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "Authentication is required."


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "You do not have permission to perform this action."


class InvalidTransitionError(AppError):
    """Raised by the approval state machine (task #8) on illegal transitions."""

    status_code = status.HTTP_409_CONFLICT
    default_message = "The requested state transition is not allowed."


class ExternalServiceError(AppError):
    """Raised when a downstream integration (AI provider, social platform,
    S3, etc.) fails in a way we can't recover from inline."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_message = "An upstream service call failed."


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Uniform error envelope for all typed AppError subclasses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler so unexpected exceptions never leak a stack
    trace to the client in a non-debug environment."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred.",
            "details": {},
        },
    )
