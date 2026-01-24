from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CategoriaBase(BaseModel):
    nombre: str


class CategoriaCreate(CategoriaBase):
    """Schema para crear categoría."""
    pass


class CategoriaUpdate(BaseModel):
    """Schema para actualizar categoría."""
    nombre: Optional[str] = None


class CategoriaResponse(CategoriaBase):
    """Schema para respuesta de categoría."""
    id: int
    estado: str
    fecha_creacion: datetime
    fecha_edicion: datetime

    class Config:
        from_attributes = True
