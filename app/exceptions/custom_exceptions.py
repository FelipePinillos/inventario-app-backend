"""Definición de excepciones personalizadas."""
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Error cuando no se encuentra un recurso."""
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ValidationError(HTTPException):
    """Error de validación."""
    def __init__(self, detail: str = "Error de validación"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class AuthenticationError(HTTPException):
    """Error de autenticación."""
    def __init__(self, detail: str = "No autenticado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionError(HTTPException):
    """Error de permisos."""
    def __init__(self, detail: str = "Permisos insuficientes"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )
