from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TipoProductoBase(BaseModel):
    nombre: str


class TipoProductoCreate(TipoProductoBase):
    """Schema para crear tipo de producto."""
    pass


class TipoProductoUpdate(BaseModel):
    """Schema para actualizar tipo de producto."""
    nombre: Optional[str] = None


class TipoProductoResponse(TipoProductoBase):
    """Schema para respuesta de tipo de producto."""
    id: int

    class Config:
        from_attributes = True
