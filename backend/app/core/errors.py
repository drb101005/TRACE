"""Custom exceptions and error handlers."""
from typing import Any, Optional
from fastapi import HTTPException, status


class TraceException(Exception):
    """Base exception for TRACE application."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InsufficientDataException(TraceException):
    """Raised when data is insufficient for audit procedures."""
    pass


class ValidationException(TraceException):
    """Raised when data validation fails."""
    pass


class AuthorizationException(TraceException):
    """Raised when authorization check fails."""
    pass


class EngagementNotFoundException(TraceException):
    """Raised when engagement is not found."""
    pass


class FileProcessingException(TraceException):
    """Raised when file processing fails."""
    pass


class SamplingException(TraceException):
    """Raised when sampling fails."""
    pass


class AuditCheckException(TraceException):
    """Raised when audit check execution fails."""
    pass


def raise_403(detail: str = "Access forbidden") -> None:
    """Raise a 403 Forbidden HTTP exception."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def raise_404(detail: str = "Resource not found") -> None:
    """Raise a 404 Not Found HTTP exception."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_400(detail: str = "Bad request") -> None:
    """Raise a 400 Bad Request HTTP exception."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_401(detail: str = "Unauthorized") -> None:
    """Raise a 401 Unauthorized HTTP exception."""
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
