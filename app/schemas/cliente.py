from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional



class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    dni: str
    telefono: int
    correo: str



class ClienteCreate(ClienteBase):
    """Schema para crear cliente."""
    pass



class ClienteUpdate(BaseModel):
    """Schema para actualizar cliente."""
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[int] = None
    correo: Optional[str] = None



class ClienteResponse(ClienteBase):
    """Schema para respuesta de cliente."""

    id: int
    estado: str

    class Config:
        from_attributes = True
