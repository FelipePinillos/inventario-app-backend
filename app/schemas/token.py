
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Respuesta de autenticación."""
    access_token: str
    token_type: str = "bearer"


# Alias para compatibilidad
token = TokenResponse
