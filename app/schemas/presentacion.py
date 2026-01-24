from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProductoInfo(BaseModel):
    """Información básica del producto para presentaciones."""
    codigo: str
    nombre: str
    
    class Config:
        from_attributes = True


class PresentacionBase(BaseModel):
    id_producto: int
    nombre: str
    cantidad_base: int
    precio: float


class PresentacionCreate(PresentacionBase):
    """Schema para crear presentación."""
    pass


class PresentacionUpdate(BaseModel):
    """Schema para actualizar presentación."""
    nombre: Optional[str] = None
    cantidad_base: Optional[int] = None
    precio: Optional[float] = None
    estado: Optional[str] = None


class PresentacionResponse(PresentacionBase):
    """Schema para respuesta de presentación con información del producto."""
    id: int
    estado: str
    fecha_creacion: datetime
    producto: Optional[ProductoInfo] = None
    
    # Propiedades computadas para compatibilidad
    @property
    def producto_codigo(self) -> Optional[str]:
        return self.producto.codigo if self.producto else None
    
    @property
    def producto_nombre(self) -> Optional[str]:
        return self.producto.nombre if self.producto else None

    class Config:
        from_attributes = True

