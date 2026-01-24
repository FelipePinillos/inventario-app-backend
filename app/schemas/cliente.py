from pydantic import BaseModel
from datetime import date
from typing import Optional


class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    edad: date  # Fecha de nacimiento
    telefono: int
    correo: str  # Sin validación estricta de email
    sexo: str
    adicional: Optional[str] = None
    avatar: Optional[str] = None


class ClienteCreate(ClienteBase):
    """Schema para crear cliente."""
    pass


class ClienteUpdate(BaseModel):
    """Schema para actualizar cliente."""
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    edad: Optional[date] = None
    telefono: Optional[int] = None
    correo: Optional[str] = None
    sexo: Optional[str] = None
    adicional: Optional[str] = None
    avatar: Optional[str] = None


class ClienteResponse(ClienteBase):
    """Schema para respuesta de cliente."""
    id: int
    estado: str

    class Config:
        from_attributes = True
