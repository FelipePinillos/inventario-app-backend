from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MarcaBase(BaseModel):
    nombre: str


class MarcaCreate(MarcaBase):
    """Schema para crear marca."""
    pass


class MarcaUpdate(BaseModel):
    """Schema para actualizar marca."""
    nombre: Optional[str] = None


class MarcaResponse(MarcaBase):
    """Schema para respuesta de marca."""
    id: int
    estado: str
    fecha_creacion: datetime
    fecha_edicion: datetime

    class Config:
        from_attributes = True
