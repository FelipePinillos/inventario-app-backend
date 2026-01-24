from pydantic import BaseModel
from typing import Optional


class ProveedorBase(BaseModel):
    razon_social: str
    ruc: int
    telefono: int
    correo: str
    direccion: str
    avatar: Optional[str] = None


class ProveedorCreate(ProveedorBase):
    """Schema para crear proveedor."""
    pass


class ProveedorUpdate(BaseModel):
    """Schema para actualizar proveedor."""
    razon_social: Optional[str] = None
    ruc: Optional[int] = None
    telefono: Optional[int] = None
    correo: Optional[str] = None
    direccion: Optional[str] = None
    avatar: Optional[str] = None


class ProveedorResponse(ProveedorBase):
    """Schema para respuesta de proveedor."""
    id: int
    estado: str

    class Config:
        from_attributes = True
