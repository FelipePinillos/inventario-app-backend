from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal

# Schema para EstadoPago
class EstadoPagoBase(BaseModel):
    nombre: str

class EstadoPagoResponse(EstadoPagoBase):
    id: int
    
    class Config:
        from_attributes = True

# Schemas para Compra
class CompraCreate(BaseModel):
    fecha_compra: Optional[date] = None
    fecha_entrega: Optional[date] = None
    TotalConDescuento: Optional[Decimal] = Field(None, decimal_places=2)
    descuento: Decimal = Field(..., decimal_places=2)
    TotalSinDescuento: Decimal = Field(..., decimal_places=2)
    id_estado: Optional[int] = None
    id_usuario: Optional[int] = None
    id_proveedor: Optional[int] = None

class CompraUpdate(BaseModel):
    fecha_compra: Optional[date] = None
    fecha_entrega: Optional[date] = None
    TotalConDescuento: Optional[Decimal] = Field(None, decimal_places=2)
    descuento: Optional[Decimal] = Field(None, decimal_places=2)
    TotalSinDescuento: Optional[Decimal] = Field(None, decimal_places=2)
    id_estado: Optional[int] = None
    id_usuario: Optional[int] = None
    id_proveedor: Optional[int] = None

# Schema para Proveedor simplificado
class ProveedorSimple(BaseModel):
    id: int
    razon_social: Optional[str]
    ruc: int
    
    class Config:
        from_attributes = True

# Schema para Usuario simplificado
class UsuarioSimple(BaseModel):
    id: int
    nombre: Optional[str]
    apellido: Optional[str]
    
    class Config:
        from_attributes = True

class CompraResponse(BaseModel):
    id: int
    fecha_compra: Optional[date]
    fecha_entrega: Optional[date]
    TotalConDescuento: Optional[Decimal]
    descuento: Decimal
    TotalSinDescuento: Decimal
    id_estado: Optional[int]
    id_usuario: Optional[int]
    id_proveedor: Optional[int]
    estado_pago: Optional[EstadoPagoResponse] = None
    usuario: Optional[UsuarioSimple] = None
    proveedor: Optional[ProveedorSimple] = None
    
    class Config:
        from_attributes = True
