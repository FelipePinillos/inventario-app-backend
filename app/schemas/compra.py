from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# Schema para EstadoPago
class EstadoPagoBase(BaseModel):
    nombre: str

class EstadoPagoResponse(EstadoPagoBase):
    id: int
    
    class Config:
        from_attributes = True

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

# Schema para Presentacion simplificado
class PresentacionSimple(BaseModel):
    id: int
    nombre: Optional[str]
    
    class Config:
        from_attributes = True

# Schemas para DetalleCompra
class DetalleCompraCreate(BaseModel):
    id_presentacion: int
    cantidad: int
    precio_compra: Decimal = Field(..., decimal_places=2)
    subtotal: Decimal = Field(..., decimal_places=2)

class DetalleCompraUpdate(BaseModel):
    id_presentacion: Optional[int] = None
    cantidad: Optional[int] = None
    precio_compra: Optional[Decimal] = Field(None, decimal_places=2)
    subtotal: Optional[Decimal] = Field(None, decimal_places=2)

class DetalleCompraResponse(BaseModel):
    id: int
    id_compra: int
    id_presentacion: int
    cantidad: int
    subtotal: Decimal
    precio_compra: Decimal
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime]
    presentacion: Optional[PresentacionSimple] = None
    
    class Config:
        from_attributes = True

# Schemas para Compra
class CompraCreate(BaseModel):
    fecha_compra: Optional[date] = None
    fecha_entrega: Optional[date] = None
    totalcondescuento: Optional[Decimal] = Field(None, decimal_places=2)
    descuento: Decimal = Field(default=0.00, decimal_places=2)
    totalsindescuento: Decimal = Field(..., decimal_places=2)
    id_usuario: Optional[int] = None
    id_proveedor: Optional[int] = None
    detalles: Optional[List[DetalleCompraCreate]] = []

class CompraUpdate(BaseModel):
    fecha_compra: Optional[date] = None
    fecha_entrega: Optional[date] = None
    totalcondescuento: Optional[Decimal] = Field(None, decimal_places=2)
    descuento: Optional[Decimal] = Field(None, decimal_places=2)
    totalsindescuento: Optional[Decimal] = Field(None, decimal_places=2)
    id_usuario: Optional[int] = None
    id_proveedor: Optional[int] = None

class CompraResponse(BaseModel):
    id: int
    fecha_compra: Optional[date]
    fecha_entrega: Optional[date]
    totalcondescuento: Optional[Decimal]
    descuento: Decimal
    totalsindescuento: Decimal
    id_usuario: Optional[int]
    id_proveedor: Optional[int]
    fecha_creacion: datetime
    fecha_edicion: Optional[datetime]
    usuario: Optional[UsuarioSimple] = None
    proveedor: Optional[ProveedorSimple] = None
    detalles: Optional[List[DetalleCompraResponse]] = []
    
    class Config:
        from_attributes = True
