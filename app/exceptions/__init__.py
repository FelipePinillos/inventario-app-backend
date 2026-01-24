"""Excepciones personalizadas."""
from app.exceptions.custom_exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    PermissionError as PermissionDeniedError,
)

__all__ = [
    "NotFoundError",
    "ValidationError", 
    "AuthenticationError",
    "PermissionDeniedError",
]
